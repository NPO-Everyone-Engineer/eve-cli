"""
Test suite for ActionExecutor.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class _FakeStateStore:
    def __init__(self):
        self.saved = {}

    def load_aux_json(self, name, default):
        return {}

    def save_aux_json(self, name, data):
        self.saved[name] = dict(data)


class _FakePermissions:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []

    def check(self, tool_name, params, tui=None):
        self.calls.append((tool_name, params, tui))
        return self.allowed


class _FakeTool:
    def __init__(self):
        self.calls = []

    def execute(self, params):
        self.calls.append(dict(params))
        return {"ok": True, "params": dict(params)}


class _FakeRegistry:
    def __init__(self, tools):
        self.tools = tools

    def get(self, name):
        return self.tools.get(name)


class TestActionExecutor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = SimpleNamespace(cwd=self.test_dir, config_dir=self.test_dir)
        self.state_store = _FakeStateStore()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_can_execute_checks_permissions_with_action_params(self):
        permissions = _FakePermissions(allowed=True)
        executor = eve_coder.ActionExecutor(
            self.config,
            registry=_FakeRegistry({}),
            permissions=permissions,
            state_store=self.state_store,
        )
        executor.allowlist = {"Write"}
        action = {"tool": "Write", "params": {"file_path": "/tmp/demo.txt"}}

        allowed, reason = executor.can_execute(action)

        self.assertTrue(allowed)
        self.assertEqual(reason, "OK")
        self.assertEqual(
            permissions.calls,
            [("Write", {"file_path": "/tmp/demo.txt"}, None)],
        )

    def test_execute_batch_records_dedupe_and_blocks_duplicates(self):
        tool = _FakeTool()
        executor = eve_coder.ActionExecutor(
            self.config,
            registry=_FakeRegistry({"Write": tool}),
            permissions=_FakePermissions(allowed=True),
            state_store=self.state_store,
        )
        executor.allowlist = {"Write"}
        action = {"tool": "Write", "params": {"file_path": "/tmp/demo.txt"}}

        first = executor.execute_batch([action], heartbeat_id="hb-1")
        second = executor.execute_batch([action], heartbeat_id="hb-2")

        self.assertTrue(first[0]["success"])
        self.assertEqual(tool.calls, [{"file_path": "/tmp/demo.txt"}])
        self.assertFalse(second[0]["success"])
        self.assertIn("Duplicate action", second[0]["error"])
        self.assertIn("dedupe.json", self.state_store.saved)


if __name__ == "__main__":
    unittest.main()
