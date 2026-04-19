"""
Test suite for SubAgent dynamic scaling functionality.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# Import eve-coder.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

Config = eve_coder.Config


class TestSubAgentScaling(unittest.TestCase):
    """Test SubAgent dynamic scaling functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        eve_coder._set_active_runtime_state(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_subagent_tool_exists(self):
        """Test that SubAgentTool class exists."""
        self.assertTrue(hasattr(eve_coder, 'SubAgentTool'))

    def test_subagent_has_max_turns(self):
        """SubAgent schema should expose max_turns with the configured default."""
        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
            default_subagent_max_turns=13,
        )
        tool = eve_coder.SubAgentTool(cfg, object(), MagicMock())

        max_turns = tool.parameters["properties"]["max_turns"]

        self.assertEqual(max_turns["type"], "integer")
        self.assertIn("default 13", max_turns["description"])
        self.assertIn(str(tool.HARD_MAX_TURNS), max_turns["description"])

    def test_subagent_has_allow_writes(self):
        """SubAgent schema should expose allow_writes."""
        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
        )
        tool = eve_coder.SubAgentTool(cfg, object(), MagicMock())

        allow_writes = tool.parameters["properties"]["allow_writes"]

        self.assertEqual(allow_writes["type"], "boolean")
        self.assertIn("Allow write tools", allow_writes["description"])

    def test_subagent_has_isolation(self):
        """SubAgent schema should expose isolation modes."""
        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
        )
        tool = eve_coder.SubAgentTool(cfg, object(), MagicMock())

        isolation = tool.parameters["properties"]["isolation"]

        self.assertEqual(isolation["type"], "string")
        self.assertEqual(isolation["enum"], ["none", "worktree"])

    def test_subagent_disallows_allow_writes_in_plan_mode(self):
        """Plan mode should block write-capable sub-agents."""
        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
            sessions_dir=os.path.join(self.test_dir, "sessions"),
        )
        os.makedirs(cfg.sessions_dir, exist_ok=True)
        runtime = eve_coder.SessionRuntimeStore(cfg, "plan-mode-subagent")
        runtime.update_runtime(plan_mode=True)
        eve_coder._set_active_runtime_state(runtime)
        subagent = eve_coder.SubAgentTool(cfg, object(), MagicMock())

        result = subagent.execute({"prompt": "edit a file", "allow_writes": True})

        self.assertIn("plan mode", result.lower())
        self.assertIn("allow_writes", result.lower())

    def test_subagent_can_return_structured_result(self):
        """Internal structured result mode should expose status and summary."""
        class _FakeClient:
            def chat_sync(self, **kwargs):
                return {"content": "done", "tool_calls": []}

        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
            sessions_dir=os.path.join(self.test_dir, "sessions"),
        )
        os.makedirs(cfg.sessions_dir, exist_ok=True)
        eve_coder._set_active_runtime_state(None)
        subagent = eve_coder.SubAgentTool(cfg, _FakeClient(), MagicMock())

        result = subagent.execute({"prompt": "summarize", "_structured_result": True})

        self.assertIsInstance(result, dict)
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], "done")
        self.assertIn("summary", result)

    def test_subagent_uses_configured_default_max_turns(self):
        """Omitted max_turns should use the config default instead of hardcoded 10."""
        class _FakeClient:
            def __init__(self, finish_after):
                self.calls = 0
                self.finish_after = finish_after

            def chat_sync(self, **kwargs):
                self.calls += 1
                if self.calls >= self.finish_after:
                    return {"content": "done", "tool_calls": []}
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": f"call_{self.calls}",
                        "name": "Glob",
                        "arguments": {"pattern": "*.py"},
                    }],
                }

        cfg = SimpleNamespace(
            cwd=self.test_dir,
            model="test-model",
            sidecar_model="",
            sessions_dir=os.path.join(self.test_dir, "sessions"),
            default_subagent_max_turns=15,
        )
        os.makedirs(cfg.sessions_dir, exist_ok=True)
        eve_coder._set_active_runtime_state(None)
        client = _FakeClient(finish_after=12)
        subagent = eve_coder.SubAgentTool(cfg, client, MagicMock())

        result = subagent.execute({"prompt": "keep going until done"})

        self.assertEqual(result, "done")
        self.assertEqual(client.calls, 12)

    def test_parse_subagent_default_max_turns_is_capped(self):
        """Config parsing should clamp configured default max turns to the hard cap."""
        cfg_path = os.path.join(self.test_dir, "config")
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("SUBAGENT_DEFAULT_MAX_TURNS=25\n")

        cfg = Config()
        cfg._parse_config_file(cfg_path)

        self.assertEqual(cfg.default_subagent_max_turns, eve_coder.HARD_MAX_SUBAGENT_TURNS)


class TestParallelAgents(unittest.TestCase):
    """Test ParallelAgents functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parallel_agents_tool_exists(self):
        """Test that ParallelAgentTool class exists."""
        self.assertTrue(hasattr(eve_coder, 'ParallelAgentTool'))

    def test_parallel_agents_supports_2_4_tasks(self):
        """ParallelAgents schema should advertise prompt-driven task items and system max."""
        coordinator = SimpleNamespace(_config=SimpleNamespace(default_subagent_max_turns=15))
        tool = eve_coder.ParallelAgentTool(coordinator)

        tasks = tool.parameters["properties"]["tasks"]

        self.assertEqual(tasks["type"], "array")
        self.assertGreaterEqual(tasks["maxItems"], 1)
        self.assertEqual(tasks["items"]["required"], ["prompt"])
        self.assertIn("max", tasks["description"])

    def test_parallel_agents_has_max_turns(self):
        """ParallelAgents schema should expose per-agent max_turns."""
        coordinator = SimpleNamespace(_config=SimpleNamespace(default_subagent_max_turns=17))
        tool = eve_coder.ParallelAgentTool(coordinator)

        max_turns = tool.parameters["properties"]["tasks"]["items"]["properties"]["max_turns"]

        self.assertEqual(max_turns["type"], "integer")
        self.assertIn("default 17", max_turns["description"])

    def test_auto_parallel_uses_configured_default_max_turns(self):
        """Auto-parallel should pass the configured sub-agent turn budget to each task."""
        class _StopParallel(Exception):
            pass

        class _FakeParallelTool:
            def __init__(self):
                self.payload = None

            def execute(self, payload):
                self.payload = payload
                raise _StopParallel()

        class _FakeRegistry:
            def __init__(self, parallel_tool):
                self.parallel_tool = parallel_tool

            def get(self, name):
                if name == "ParallelAgents":
                    return self.parallel_tool
                return None

        class _FakeSession:
            def __init__(self):
                self.runtime_state = None
                self.user_messages = []

            def get_resume_summary(self):
                return {}

            def add_user_message(self, message):
                self.user_messages.append(message)

            def add_assistant_message(self, *args, **kwargs):
                pass

        tui = SimpleNamespace(
            _scroll_print=lambda *args, **kwargs: None,
            _render_markdown=lambda *args, **kwargs: None,
        )
        cfg = SimpleNamespace(
            cwd=self.test_dir,
            config_dir=self.config_dir,
            autotest_on_start=False,
            max_agent_steps=20,
            max_turns=None,
            rag=False,
            default_subagent_max_turns=17,
            model="test-model",
            sidecar_model="",
        )
        parallel_tool = _FakeParallelTool()
        session = _FakeSession()
        agent = eve_coder.Agent(
            cfg,
            client=object(),
            registry=_FakeRegistry(parallel_tool),
            permissions=None,
            session=session,
            tui=tui,
        )

        with patch.object(eve_coder.Agent, "_detect_parallel_tasks", return_value=["task A", "task B"]):
            with self.assertRaises(_StopParallel):
                agent._run_impl("parallel tasks please")

        self.assertIsNotNone(parallel_tool.payload)
        self.assertEqual(
            [task["max_turns"] for task in parallel_tool.payload["tasks"]],
            [17, 17],
        )


if __name__ == "__main__":
    unittest.main()
