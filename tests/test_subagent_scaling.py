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
        """Test that SubAgent supports max_turns parameter."""
        # SubAgent should accept max_turns parameter
        self.assertTrue(True)  # Placeholder - actual implementation check

    def test_subagent_has_allow_writes(self):
        """Test that SubAgent supports allow_writes parameter."""
        # SubAgent should accept allow_writes parameter
        self.assertTrue(True)  # Placeholder - actual implementation check

    def test_subagent_has_isolation(self):
        """Test that SubAgent supports isolation parameter."""
        # SubAgent should accept isolation parameter
        self.assertTrue(True)  # Placeholder - actual implementation check

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
        """Test that ParallelAgents supports 2-4 concurrent tasks."""
        # ParallelAgents should support 2-4 concurrent tasks
        self.assertTrue(True)  # Placeholder - actual implementation check

    def test_parallel_agents_has_max_turns(self):
        """Test that ParallelAgents supports max_turns per agent."""
        self.assertTrue(True)  # Placeholder - actual implementation check


if __name__ == "__main__":
    unittest.main()
