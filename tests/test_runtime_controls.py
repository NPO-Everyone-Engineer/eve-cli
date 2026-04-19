import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class _FakeInputMonitor:
    def __init__(self):
        self.pressed = False

    def start(self):
        return None

    def stop(self):
        return None


class _FakePermissions:
    auto_mode = False
    _last_decision = None

    def check(self, tool_name, tool_params, tui):
        return True

    def describe_last_decision(self):
        return ""


class _FakeRegistry:
    def __init__(self, tools):
        self._tools = {tool.name: tool for tool in tools}

    def names(self):
        return list(self._tools.keys())

    def get(self, name):
        return self._tools.get(name)

    def get_schemas(self):
        return [tool.get_schema() for tool in self._tools.values()]


class _FakeTUI:
    def __init__(self):
        self.scroll_region = SimpleNamespace(_active=False, update_mode_display=lambda *args, **kwargs: None)
        self.printed = []
        self.rendered = []

    def _scroll_print(self, *args, **kwargs):
        if args:
            self.printed.append(args[0])
        return None

    def _render_markdown(self, *args, **kwargs):
        if args:
            self.rendered.append(args[0])
        return None

    def start_spinner(self, *args, **kwargs):
        return None

    def stop_spinner(self, *args, **kwargs):
        return None

    def start_tool_status(self, *args, **kwargs):
        return None

    def show_tool_call(self, *args, **kwargs):
        return None

    def show_tool_result(self, *args, **kwargs):
        return None

    def show_sync_response(self, data, known_tools=None):
        message = data["choices"][0]["message"]
        return message.get("content", ""), message.get("tool_calls", []), False


class _SequenceClient:
    def __init__(self, responses, vision_support=None):
        self.responses = list(responses)
        self.calls = []
        self.think_mode = False
        self.thinking_budget = 0
        self.vision_support = dict(vision_support or {})

    def chat(self, model, messages, tools=None, stream=True, options=None):
        self.calls.append({
            "model": model,
            "messages": messages,
            "tools": tools,
            "options": options,
        })
        if not self.responses:
            raise AssertionError("No fake response queued")
        return self.responses.pop(0)

    def check_vision_support(self, model, assume_if_unknown=True):
        return self.vision_support.get(model, assume_if_unknown)


class _FakeCodeIntel:
    def __init__(self, repo_map_text):
        self.repo_map_text = repo_map_text
        self.calls = 0

    def build_index(self):
        self.calls += 1
        return 2

    def repo_map(self, max_lines=120):
        return self.repo_map_text


class TestTypeAheadQueue(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_queue_completed_and_partial_input(self):
        self.tui.queue_typeahead_bytes(b"hello\nwor")
        self.assertEqual(self.tui.dequeue_typeahead_input(), "hello")
        self.assertIsNone(self.tui.dequeue_typeahead_input())
        self.assertEqual(self.tui.consume_typeahead_prefill(), "wor")
        self.assertEqual(self.tui.consume_typeahead_prefill(), "")

    def test_queue_backspace(self):
        self.tui.queue_typeahead_bytes(b"hel\x7flo\n")
        self.assertEqual(self.tui.dequeue_typeahead_input(), "helo")


class TestReadWriteLock(unittest.TestCase):
    def test_multiple_readers_can_run_together(self):
        lock = eve_coder.ReadWriteLock()
        state = {"count": 0, "peak": 0}
        gate = threading.Event()

        def reader():
            with lock.read():
                state["count"] += 1
                state["peak"] = max(state["peak"], state["count"])
                gate.wait(0.2)
                state["count"] -= 1

        threads = [threading.Thread(target=reader) for _ in range(2)]
        for t in threads:
            t.start()
        time.sleep(0.05)
        gate.set()
        for t in threads:
            t.join()
        self.assertGreaterEqual(state["peak"], 2)

    def test_writer_waits_for_reader(self):
        lock = eve_coder.ReadWriteLock()
        events = []
        gate = threading.Event()

        def reader():
            with lock.read():
                events.append("reader-start")
                gate.wait(0.2)
                events.append("reader-end")

        def writer():
            with lock.write():
                events.append("writer")

        rt = threading.Thread(target=reader)
        wt = threading.Thread(target=writer)
        rt.start()
        time.sleep(0.05)
        wt.start()
        time.sleep(0.05)
        gate.set()
        rt.join()
        wt.join()
        self.assertEqual(events, ["reader-start", "reader-end", "writer"])


class TestThinkingDisplay(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_show_sync_response_renders_native_thinking_without_polluting_text(self):
        data = {
            "choices": [{
                "message": {
                    "thinking": "inspect files\ncompare outputs",
                    "content": "Visible answer",
                }
            }]
        }

        with patch.object(self.tui, "_scroll_print") as mock_print, \
             patch.object(self.tui, "_render_markdown") as mock_render:
            text, tool_calls, had_thinking = self.tui.show_sync_response(data)

        printed = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
        self.assertTrue(had_thinking)
        self.assertEqual(text, "Visible answer")
        self.assertEqual(tool_calls, [])
        self.assertIn("Thinking", printed)
        self.assertIn("collapsed", printed)
        self.assertIn("inspect files", printed)
        self.assertIn("Final answer continues below", printed)
        mock_render.assert_called_once_with("Visible answer")


class TestAgentRuntimeControls(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.test_dir, "project")
        self.config_dir = os.path.join(self.test_dir, "config")
        self.sessions_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def make_config(self):
        config = eve_coder.Config()
        config.cwd = self.project_dir
        config.config_dir = self.config_dir
        config.sessions_dir = self.sessions_dir
        config.permissions_file = os.path.join(self.config_dir, "permissions.json")
        config.model = "test-model"
        config.sidecar_model = "fallback-model"
        config.autotest_on_start = False
        config.max_agent_steps = 8
        config.max_turns = None
        config.rag = False
        config.learn_mode = False
        config.learn_auto_explain = False
        config.prompt_cost_per_mtok = 0
        config.completion_cost_per_mtok = 0
        config.session_id = "runtime-controls"
        return config

    def make_agent(self, client, tools, code_intel=None):
        config = self.make_config()
        session = eve_coder.Session(config, "test system prompt")
        agent = eve_coder.Agent(
            config,
            client=client,
            registry=_FakeRegistry(tools),
            permissions=_FakePermissions(),
            session=session,
            tui=_FakeTUI(),
            code_intel=code_intel,
        )
        return agent, session

    @patch.object(eve_coder, "InputMonitor", _FakeInputMonitor)
    def test_agent_blocks_edit_without_prior_read(self):
        target = os.path.join(self.project_dir, "sample.py")
        with open(target, "w", encoding="utf-8") as f:
            f.write("print('hello')\n")

        client = _SequenceClient([
            {
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "id": "call_edit",
                            "function": {
                                "name": "Edit",
                                "arguments": json.dumps({
                                    "file_path": "sample.py",
                                    "old_string": "hello",
                                    "new_string": "bye",
                                }),
                            },
                        }],
                    }
                }]
            },
            {"choices": [{"message": {"content": "done", "tool_calls": []}}]},
        ])
        agent, session = self.make_agent(client, [eve_coder.EditTool(self.project_dir)])

        agent._run_impl("Fix sample.py")

        with open(target, encoding="utf-8") as f:
            self.assertEqual(f.read(), "print('hello')\n")
        tool_messages = [m["content"] for m in session.messages if m.get("role") == "tool"]
        self.assertTrue(any("Read the existing file first" in msg for msg in tool_messages))

    @patch.object(eve_coder, "InputMonitor", _FakeInputMonitor)
    def test_agent_requires_verification_before_finishing(self):
        client = _SequenceClient([
            {
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "id": "call_write",
                            "function": {
                                "name": "Write",
                                "arguments": json.dumps({
                                    "file_path": "generated.py",
                                    "content": "print('ok')\n",
                                }),
                            },
                        }],
                    }
                }]
            },
            {"choices": [{"message": {"content": "looks done", "tool_calls": []}}]},
            {
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "id": "call_verify",
                            "function": {
                                "name": "Bash",
                                "arguments": json.dumps({
                                    "command": "python3 -c \"import py_compile; py_compile.compile('generated.py', cfile='generated.pyc', doraise=True)\"",
                                }),
                            },
                        }],
                    }
                }]
            },
            {"choices": [{"message": {"content": "verified", "tool_calls": []}}]},
        ])
        bash_config = self.make_config()
        agent, session = self.make_agent(
            client,
            [
                eve_coder.WriteTool(self.project_dir),
                eve_coder.BashTool(self.project_dir, config=bash_config),
            ],
        )

        agent._run_impl("Create generated.py and finish")

        self.assertEqual(agent.get_last_output(), "verified")
        runtime = session.runtime_state.load_runtime()
        self.assertFalse(runtime.get("verification_required"))
        self.assertEqual(runtime.get("last_verification_status"), "passed")
        reminder_messages = [
            m["content"] for m in session.messages
            if m.get("role") == "user" and "verification step" in str(m.get("content", ""))
        ]
        self.assertTrue(reminder_messages)

    @patch.object(eve_coder, "InputMonitor", _FakeInputMonitor)
    def test_agent_injects_repo_map_on_code_routing(self):
        client = _SequenceClient([
            {"choices": [{"message": {"content": "done", "tool_calls": []}}]},
        ])
        code_intel = _FakeCodeIntel("foo.py:10 Foo\nbar.py:5 Bar")
        agent, _session = self.make_agent(
            client,
            [eve_coder.ReadTool(self.project_dir)],
            code_intel=code_intel,
        )

        agent._run_impl("Search foo.py and explain the definition")

        first_call_messages = client.calls[0]["messages"]
        self.assertTrue(any("[Repo Map]" in str(msg.get("content", "")) for msg in first_call_messages))
        self.assertEqual(code_intel.calls, 1)

    def test_resolve_request_policy_keeps_primary_model_after_retries(self):
        client = _SequenceClient([])
        agent, _session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])

        policy = agent._resolve_request_policy([], empty_retries=3)

        self.assertEqual(policy["model"], "test-model")
        self.assertEqual(policy["options"], {"retry_temperature_boost": 0.3})

    def test_resolve_request_policy_ignores_utility_model_after_retries(self):
        client = _SequenceClient([])
        agent, _session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        agent.config.utility_model = "utility-fallback"

        policy = agent._resolve_request_policy([], empty_retries=3)

        self.assertEqual(policy["model"], "test-model")
        self.assertEqual(policy["options"], {"retry_temperature_boost": 0.3})

    def test_resolve_request_policy_routes_images_to_vision_model(self):
        client = _SequenceClient([], vision_support={
            "test-model": False,
            "vision-helper": True,
        })
        agent, session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        agent.config.vision_model = "vision-helper"
        session.add_multimodal_user_message([
            {"type": "text", "text": "Explain this screenshot"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
        ])

        policy = agent._resolve_request_policy([], empty_retries=0)

        self.assertEqual(policy["model"], "vision-helper")
        self.assertTrue(policy["vision_route"])

    def test_resolve_request_policy_keeps_primary_for_vision_capable_main_model(self):
        client = _SequenceClient([], vision_support={"test-model": True})
        agent, session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        session.add_multimodal_user_message([
            {"type": "text", "text": "Explain this screenshot"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
        ])

        policy = agent._resolve_request_policy([], empty_retries=0)

        self.assertEqual(policy["model"], "test-model")
        self.assertFalse(policy["vision_route"])

    def test_rubber_duck_review_uses_review_model_and_records_note(self):
        client = _SequenceClient([
            {"choices": [{"message": {"content": "## Findings\n- [blocking] Missing verification for edge case\n- [non-blocking] Consider a clearer variable name\n## Follow-up Checks\n- Run unit tests for the changed branch"}}]},
        ])
        agent, session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        agent.config.rubber_duck = True
        agent.config.review_model = "review-model"

        review_text = eve_coder._run_rubber_duck_review(
            agent.config,
            client,
            session,
            agent.tui,
            trigger="post_edit",
            source_kind="diff",
            source_desc="uncommitted changes",
            content="diff --git a/foo.py b/foo.py\n+print('hello')\n",
            force=False,
        )

        self.assertIn("Missing verification", review_text)
        self.assertEqual(client.calls[0]["model"], "review-model")
        runtime = session.runtime_state.load_runtime()
        self.assertEqual(runtime.get("last_rubber_duck_model"), "review-model")
        self.assertEqual(runtime.get("last_rubber_duck_trigger"), "post_edit")
        self.assertEqual(runtime.get("rubber_duck_checkpoints"), "plan, post-edit")
        self.assertTrue(any("Rubber Duck Review" in str(m.get("content", "")) for m in session.messages))
        self.assertIn("- Missing verification for edge case", agent.tui.rendered[0])
        self.assertIn("- Consider a clearer variable name", agent.tui.rendered[1])
        self.assertIn("- Run unit tests for the changed branch", agent.tui.rendered[2])
        printed = "\n".join(agent.tui.printed)
        self.assertIn("Blocking Findings", printed)
        self.assertIn("Non-blocking Findings", printed)

    def test_rubber_duck_review_respects_checkpoint_filter(self):
        client = _SequenceClient([
            {"choices": [{"message": {"content": "## Findings\n- Should not run\n## Follow-up Checks\n- None."}}]},
        ])
        agent, session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        agent.config.rubber_duck = True
        agent.config.review_model = "review-model"
        agent.config.rubber_duck_checkpoints = "plan"

        review_text = eve_coder._run_rubber_duck_review(
            agent.config,
            client,
            session,
            agent.tui,
            trigger="post_edit",
            source_kind="diff",
            source_desc="uncommitted changes",
            content="diff --git a/foo.py b/foo.py\n+print('hello')\n",
            force=False,
        )

        self.assertEqual(review_text, "")
        self.assertEqual(client.calls, [])

    def test_accept_rubber_duck_review_can_limit_to_blocking_items(self):
        client = _SequenceClient([
            {"choices": [{"message": {"content": "## Findings\n- [blocking] Fix failing syntax path\n- [non-blocking] Consider renaming helper\n## Follow-up Checks\n- Run smoke tests"}}]},
        ])
        agent, session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])
        agent.config.rubber_duck = True
        agent.config.review_model = "review-model"

        eve_coder._run_rubber_duck_review(
            agent.config,
            client,
            session,
            agent.tui,
            trigger="post_edit",
            source_kind="diff",
            source_desc="uncommitted changes",
            content="diff --git a/foo.py b/foo.py\n+print('hello')\n",
            force=False,
        )
        ok, message = eve_coder._accept_rubber_duck_review(session, "blocking")

        self.assertTrue(ok)
        self.assertIn("Accepted 1 finding", message)
        self.assertIn("Fix failing syntax path", session.messages[-1]["content"])
        self.assertNotIn("Consider renaming helper", session.messages[-1]["content"])
        self.assertNotIn("Run smoke tests", session.messages[-1]["content"])


class TestInputPrompts(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_multiline_continuation_prompts_avoid_ansi_sequences(self):
        prompts = []
        responses = iter(["first line", "second line", ""])

        def fake_input(prompt=""):
            prompts.append(prompt)
            return next(responses)

        with patch.object(self.tui, "show_input_separator"), \
             patch("builtins.input", side_effect=fake_input):
            result = self.tui.get_multiline_input()

        self.assertEqual(result, "first line\nsecond line")
        self.assertEqual(prompts, ["> ", "... ", "... "])
        self.assertTrue(all("\x1b" not in prompt for prompt in prompts))

    def test_ask_user_question_prompt_avoids_ansi_sequences(self):
        prompts = []
        tool = eve_coder.AskUserQuestionTool()

        def fake_input(prompt=""):
            prompts.append(prompt)
            return "1"

        with patch.object(eve_coder, "_active_tui", None), \
             patch.object(eve_coder, "_active_scroll_region", None), \
             patch("builtins.input", side_effect=fake_input):
            result = tool.execute({
                "question": "Choose one",
                "options": ["alpha", "beta"],
            })

        self.assertEqual(result, "User chose: alpha")
        self.assertEqual(prompts, ["  > "])
        self.assertTrue(all("\x1b" not in prompt for prompt in prompts))

    def test_ask_user_question_batch_prompt_avoids_ansi_sequences(self):
        prompts = []
        tool = eve_coder.AskUserQuestionBatchTool()

        def fake_input(prompt=""):
            prompts.append(prompt)
            return "A, B"

        with patch.object(eve_coder, "_active_tui", None), \
             patch.object(eve_coder, "_active_scroll_region", None), \
             patch("builtins.input", side_effect=fake_input):
            result = tool.execute({
                "questions": [
                    {"question": "Q1", "options": ["alpha", "beta"]},
                    {"question": "Q2", "options": ["gamma", "delta"]},
                ],
            })

        self.assertIn("Q1: alpha", result)
        self.assertIn("Q2: delta", result)
        self.assertEqual(prompts, ["  > "])
        self.assertTrue(all("\x1b" not in prompt for prompt in prompts))

    def test_stream_response_renders_native_thinking_without_polluting_text(self):
        chunks = iter([
            {"choices": [{"delta": {"thinking": "inspect files\ncompare outputs"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": "Visible answer"}, "finish_reason": None}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
        ])

        with patch.object(self.tui, "_scroll_print") as mock_print:
            text, tool_calls, had_thinking = self.tui.stream_response(chunks)

        printed = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
        self.assertTrue(had_thinking)
        self.assertEqual(text, "Visible answer")
        self.assertEqual(tool_calls, [])
        self.assertIn("Thinking", printed)
        self.assertIn("collapsed", printed)
        self.assertIn("inspect files", printed)
        self.assertIn("Final answer continues below", printed)


# ---------------------------------------------------------------------------
# FIX-1: verification 判定ロジックのテスト
# ---------------------------------------------------------------------------

class TestVerificationJudgment(unittest.TestCase):
    """Tests for the improved _mark_verification_status / passed computation (FIX-1)."""

    def _compute_passed(self, is_error, output):
        return eve_coder._manual_verification_passed(is_error, output)

    def test_passed_on_clean_output(self):
        """Clean pytest output with 'OK' should yield passed=True."""
        self.assertTrue(self._compute_passed(False, "Ran 5 tests in 0.1s\nOK"))

    def test_passed_on_empty_output_no_error(self):
        """Empty output with no error flag should yield passed=True."""
        self.assertTrue(self._compute_passed(False, ""))

    def test_passed_on_none_output(self):
        """None output with no error flag should yield passed=True."""
        self.assertTrue(self._compute_passed(False, None))

    def test_failed_on_is_error(self):
        """is_error=True should always yield passed=False."""
        self.assertFalse(self._compute_passed(True, "Ran 5 tests in 0.1s\nOK"))

    def test_failed_on_exit_code_in_output(self):
        """Output containing '(exit code: 1)' should yield passed=False."""
        self.assertFalse(self._compute_passed(False, "Something went wrong\n(exit code: 1)"))

    def test_failed_on_FAILED_in_output(self):
        """Output containing 'FAILED' (uppercase) should yield passed=False."""
        self.assertFalse(self._compute_passed(False, "FAILED (failures=1)"))

    def test_failed_on_errors_count(self):
        """Output containing 'errors: 2' should yield passed=False."""
        self.assertFalse(self._compute_passed(False, "errors: 2"))

    def test_failed_on_errors_count_uppercase(self):
        """Output containing 'Errors: 3' (mixed case) should yield passed=False."""
        self.assertFalse(self._compute_passed(False, "Errors: 3"))

    def test_failed_on_pytest_summary_with_suppressed_exit_code(self):
        self.assertFalse(self._compute_passed(False, "1 failed, 9 passed in 0.42s"))

    def test_failed_on_found_errors_summary(self):
        self.assertFalse(self._compute_passed(False, "Found 2 errors."))

    def test_passed_when_failed_is_substring_not_word(self):
        """'FAILEDOVER' without word boundary should NOT trigger failed=True."""
        # 'FAILED' must be a whole word; 'FAILEDOVER' should not match
        self.assertTrue(self._compute_passed(False, "FAILEDOVER some other text"))

    def test_passed_when_errors_zero(self):
        """'errors: 0' should NOT mark as failed (only 1-9 triggers failure)."""
        self.assertTrue(self._compute_passed(False, "errors: 0"))

    def test_passed_when_failures_zero(self):
        self.assertTrue(self._compute_passed(False, "0 failed, 12 passed in 0.15s"))


# ---------------------------------------------------------------------------
# FIX-2: resume 時の _pending_verification リセットのテスト
# ---------------------------------------------------------------------------

class TestPendingVerificationReset(unittest.TestCase):
    """Tests that resume does not carry forward stale verification_required (FIX-2)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.test_dir, "project")
        self.config_dir = os.path.join(self.test_dir, "config")
        self.sessions_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def make_config(self, session_id="verify-reset-test"):
        config = eve_coder.Config()
        config.cwd = self.project_dir
        config.config_dir = self.config_dir
        config.sessions_dir = self.sessions_dir
        config.permissions_file = os.path.join(self.config_dir, "permissions.json")
        config.model = "test-model"
        config.sidecar_model = "fallback-model"
        config.autotest_on_start = False
        config.max_agent_steps = 4
        config.max_turns = None
        config.rag = False
        config.learn_mode = False
        config.learn_auto_explain = False
        config.prompt_cost_per_mtok = 0
        config.completion_cost_per_mtok = 0
        config.session_id = session_id
        return config

    def make_agent(self, config):
        session = eve_coder.Session(config, "test system prompt")
        agent = eve_coder.Agent(
            config,
            client=_SequenceClient([]),
            registry=_FakeRegistry([]),
            permissions=_FakePermissions(),
            session=session,
            tui=_FakeTUI(),
        )
        return agent, session

    def test_pending_verification_false_on_fresh_init(self):
        """A fresh agent (no prior runtime state) must start with _pending_verification=False."""
        config = self.make_config("fresh-init-test")
        agent, _session = self.make_agent(config)
        self.assertFalse(agent._pending_verification)

    def test_pending_verification_false_on_resume_with_stale_flag(self):
        """After resume where runtime has verification_required=True but no pending files,
        _pending_verification must be False (stale flag is discarded)."""
        config = self.make_config("resume-stale-test")
        # First, create a session and manually persist a stale verification_required flag
        session = eve_coder.Session(config, "test system prompt")
        if session.runtime_state:
            session.runtime_state.update_runtime(
                verification_required=True,
                pending_verification=[],  # no files pending
            )
        # Now create a new agent that resumes this session
        agent2 = eve_coder.Agent(
            config,
            client=_SequenceClient([]),
            registry=_FakeRegistry([]),
            permissions=_FakePermissions(),
            session=session,
            tui=_FakeTUI(),
        )
        # The stale flag must NOT be carried forward
        self.assertFalse(agent2._pending_verification)


# ---------------------------------------------------------------------------
# Gemma / large-context policy tests
# ---------------------------------------------------------------------------

class TestSessionContextPolicy(unittest.TestCase):
    def test_default_context_policy_stays_conservative(self):
        config = eve_coder.Config()
        config.model = "test-model"
        config.context_window = eve_coder.Config.DEFAULT_CONTEXT_WINDOW

        policy = eve_coder.Session.context_policy_for(config)

        self.assertEqual(policy["compact_threshold"], 0.80)
        self.assertEqual(policy["keep_recent_messages"], 4)
        self.assertEqual(policy["max_messages"], eve_coder.Session.MAX_MESSAGES)

    def test_gemma_context_policy_keeps_more_history(self):
        config = eve_coder.Config()
        config.model = "gemma4:31b"
        config.context_window = 262144

        policy = eve_coder.Session.context_policy_for(config)

        self.assertEqual(policy["compact_threshold"], 0.87)
        self.assertEqual(policy["keep_recent_messages"], 8)
        self.assertEqual(policy["summary_chars"], 12000)
        self.assertGreater(policy["max_messages"], eve_coder.Session.MAX_MESSAGES)


# ---------------------------------------------------------------------------
# FIX-4: _known_file_paths ターン間引き継ぎのテスト
# ---------------------------------------------------------------------------

class TestKnownFilePaths(unittest.TestCase):
    """Tests that _known_file_paths persists across turns within a session (FIX-4)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.test_dir, "project")
        self.config_dir = os.path.join(self.test_dir, "config")
        self.sessions_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def make_config(self):
        config = eve_coder.Config()
        config.cwd = self.project_dir
        config.config_dir = self.config_dir
        config.sessions_dir = self.sessions_dir
        config.permissions_file = os.path.join(self.config_dir, "permissions.json")
        config.model = "test-model"
        config.sidecar_model = "fallback-model"
        config.autotest_on_start = False
        config.max_agent_steps = 4
        config.max_turns = None
        config.rag = False
        config.learn_mode = False
        config.learn_auto_explain = False
        config.prompt_cost_per_mtok = 0
        config.completion_cost_per_mtok = 0
        config.session_id = "known-paths-test"
        return config

    @patch.object(eve_coder, "InputMonitor", _FakeInputMonitor)
    def test_known_paths_persist_across_turns(self):
        """Files read in turn 1 remain in _known_file_paths for turn 2."""
        target = os.path.join(self.project_dir, "sample.py")
        with open(target, "w", encoding="utf-8") as f:
            f.write("x = 1\n")

        config = self.make_config()
        # Turn 1: read the file
        client = _SequenceClient([
            {"choices": [{"message": {"content": "read it", "tool_calls": [{
                "id": "call_read",
                "function": {
                    "name": "Read",
                    "arguments": json.dumps({"file_path": "sample.py"}),
                },
            }]}}]},
            {"choices": [{"message": {"content": "done", "tool_calls": []}}]},
        ])
        session = eve_coder.Session(config, "test system prompt")
        agent = eve_coder.Agent(
            config,
            client=client,
            registry=_FakeRegistry([eve_coder.ReadTool(self.project_dir)]),
            permissions=_FakePermissions(),
            session=session,
            tui=_FakeTUI(),
        )
        agent._run_impl("Read sample.py")
        paths_after_turn1 = set(agent._known_file_paths)

        # _known_file_paths must not be empty after reading
        self.assertTrue(len(paths_after_turn1) > 0,
                        "_known_file_paths should contain the read file after turn 1")

        # Turn 2: run another prompt — _known_file_paths must still contain turn-1 paths
        client2 = _SequenceClient([
            {"choices": [{"message": {"content": "ok", "tool_calls": []}}]},
        ])
        agent.client = client2
        agent._run_impl("What did we read?")

        # Paths from turn 1 must be preserved
        self.assertTrue(paths_after_turn1.issubset(agent._known_file_paths),
                        "_known_file_paths from turn 1 must persist into turn 2")


# ---------------------------------------------------------------------------
# Audio read behavior
# ---------------------------------------------------------------------------

class TestAudioReadBehavior(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.test_dir, "project")
        os.makedirs(self.project_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_read_tool_explains_audio_transport_limit(self):
        audio_path = os.path.join(self.project_dir, "sample.wav")
        with open(audio_path, "wb") as f:
            f.write(b"RIFFdemoWAVEfmt ")

        result = eve_coder.ReadTool(self.project_dir).execute({"file_path": "sample.wav"})

        self.assertIn("Audio file detected", result)
        self.assertIn("does not accept audio attachments yet", result)


# ---------------------------------------------------------------------------
# FIX-6: TOCTOU テスト (エージェントファイル symlink チェック)
# ---------------------------------------------------------------------------

class TestAgentFileTOCTOU(unittest.TestCase):
    """Tests that symlinks in agent dirs are skipped (FIX-6 TOCTOU guard)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.test_dir, "project")
        self.config_dir = os.path.join(self.test_dir, "config")
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def make_config(self):
        config = eve_coder.Config()
        config.cwd = self.project_dir
        config.config_dir = self.config_dir
        config.model = "test-model"
        config.debug = False
        return config

    def trust_agents(self, config, *paths):
        eve_coder._remember_repo_scope_trust(
            config,
            "agents",
            eve_coder._compute_repo_hashes(config, [str(path) for path in paths]),
        )

    @patch("sys.stdin.isatty", return_value=False)
    def test_symlink_skipped_in_agent_dir(self, _mock_isatty):
        """A symlink to a .md file in the agents dir must not appear in the prompt."""
        agents_dir = os.path.join(self.project_dir, ".eve-cli", "agents")
        os.makedirs(agents_dir, exist_ok=True)

        # Create a real agent file
        real_agent = os.path.join(agents_dir, "real-agent.md")
        with open(real_agent, "w", encoding="utf-8") as f:
            f.write("---\ndescription: Real agent\n---\nDo things.\n")

        # Create a symlink pointing to the real agent file
        link_agent = os.path.join(agents_dir, "symlink-agent.md")
        try:
            os.symlink(real_agent, link_agent)
        except OSError:
            self.skipTest("Symlink creation not supported on this platform")

        config = self.make_config()
        self.trust_agents(config, real_agent)
        prompt = eve_coder._build_runtime_system_prompt(config)

        # The real agent must appear; the symlink must NOT generate a separate entry
        # (symlink-agent should not appear as its own agent persona)
        self.assertNotIn("symlink-agent", prompt)
        # The real agent should still appear
        self.assertIn("real-agent", prompt)

    @patch("sys.stdin.isatty", return_value=False)
    def test_normal_agent_file_included(self, _mock_isatty):
        """A normal (non-symlink) .md file in agents dir must appear in the prompt."""
        agents_dir = os.path.join(self.project_dir, ".eve-cli", "agents")
        os.makedirs(agents_dir, exist_ok=True)

        agent_file = os.path.join(agents_dir, "my-agent.md")
        with open(agent_file, "w", encoding="utf-8") as f:
            f.write("---\ndescription: My special agent\n---\nDoes special things.\n")

        config = self.make_config()
        self.trust_agents(config, agent_file)
        prompt = eve_coder._build_runtime_system_prompt(config)

        self.assertIn("my-agent", prompt)


if __name__ == "__main__":
    unittest.main()
