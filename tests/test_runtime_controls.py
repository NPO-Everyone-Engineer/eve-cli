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

    def _scroll_print(self, *args, **kwargs):
        return None

    def _render_markdown(self, *args, **kwargs):
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
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.think_mode = False
        self.thinking_budget = 0

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
        self.assertIn("inspect files", printed)
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
                                    "command": "python3 -c \"import py_compile; py_compile.compile('generated.py', doraise=True)\"",
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

    def test_resolve_request_policy_prefers_sidecar_after_retries(self):
        client = _SequenceClient([])
        agent, _session = self.make_agent(client, [eve_coder.ReadTool(self.project_dir)])

        policy = agent._resolve_request_policy([], empty_retries=3)

        self.assertEqual(policy["model"], "fallback-model")
        self.assertEqual(policy["options"], {"retry_temperature_boost": 0.3})


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
        self.assertIn("inspect files", printed)


if __name__ == "__main__":
    unittest.main()
