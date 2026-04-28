"""
Tests for HookManager extensions added in P2-2:
- new VALID_EVENTS (UserPromptSubmit, SubagentStop, PreCompact, Notification)
- regex matcher (re:, ~ prefixes)
- fire_user_prompt / fire_pre_compact deny semantics
"""

import importlib.util
import json
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

HookManager = eve_coder.HookManager


class TestHookValidEvents(unittest.TestCase):
    def test_valid_events_includes_p22_additions(self):
        for evt in ("UserPromptSubmit", "SubagentStop", "PreCompact", "Notification"):
            self.assertIn(evt, HookManager.VALID_EVENTS)

    def test_deny_capable_events(self):
        self.assertIn("PreToolUse", HookManager.DENY_CAPABLE_EVENTS)
        self.assertIn("PreCompact", HookManager.DENY_CAPABLE_EVENTS)
        self.assertIn("UserPromptSubmit", HookManager.DENY_CAPABLE_EVENTS)
        # PostToolUse / Stop / Notification cannot deny
        self.assertNotIn("PostToolUse", HookManager.DENY_CAPABLE_EVENTS)
        self.assertNotIn("Notification", HookManager.DENY_CAPABLE_EVENTS)


class TestMatcherRegex(unittest.TestCase):
    def test_re_prefix_matches_alternation(self):
        self.assertTrue(HookManager._matcher_value_matches("re:Bash|Read|Write", "Bash"))
        self.assertTrue(HookManager._matcher_value_matches("re:Bash|Read|Write", "Read"))
        self.assertFalse(HookManager._matcher_value_matches("re:Bash|Read|Write", "WebFetch"))

    def test_tilde_prefix_alias(self):
        self.assertTrue(HookManager._matcher_value_matches("~^Edit", "Edit"))
        self.assertFalse(HookManager._matcher_value_matches("~^Edit", "MultiEdit"))  # fullmatch — anchored

    def test_plain_string_is_exact_match(self):
        self.assertTrue(HookManager._matcher_value_matches("Bash", "Bash"))
        self.assertFalse(HookManager._matcher_value_matches("Bash", "BashTool"))

    def test_invalid_regex_falls_back_to_no_match(self):
        # An unbalanced regex pattern should not crash; just no match.
        self.assertFalse(HookManager._matcher_value_matches("re:[unbalanced", "anything"))


class TestHookFireWithNewEvents(unittest.TestCase):
    """End-to-end: load a hooks.json with new events, fire, verify deny semantics."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.tmpdir, "config")
        self.cwd = os.path.join(self.tmpdir, "project")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.cwd, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _build_config(self):
        # Minimal Config-like object satisfying HookManager + sanitized env.
        return SimpleNamespace(
            cwd=self.cwd,
            config_dir=self.config_dir,
            shell_env_policy="default",
            hook_env_policy="default",
            debug=False,
        )

    def _write_global_hooks(self, hooks):
        path = os.path.join(self.config_dir, "hooks.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"hooks": hooks}, f)

    def test_user_prompt_submit_deny_returns_deny(self):
        # Hook exits with code 1 → deny
        self._write_global_hooks([{
            "event": "UserPromptSubmit",
            "command": ["sh", "-lc", "exit 1"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        self.assertTrue(hm.has_hooks)
        self.assertEqual(hm.fire_user_prompt("hello world"), "deny")

    def test_user_prompt_submit_allow_when_hook_exits_zero(self):
        self._write_global_hooks([{
            "event": "UserPromptSubmit",
            "command": ["sh", "-lc", "exit 0"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        self.assertEqual(hm.fire_user_prompt("hi"), "allow")

    def test_pre_compact_deny_blocks(self):
        self._write_global_hooks([{
            "event": "PreCompact",
            "command": ["sh", "-lc", "exit 1"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        self.assertEqual(hm.fire_pre_compact(50000, 80), "deny")

    def test_subagent_stop_fires_without_denial_capability(self):
        # SubagentStop is not deny-capable; fire_subagent_stop returns None
        self._write_global_hooks([{
            "event": "SubagentStop",
            "command": ["sh", "-lc", "echo subagent-stopped"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        # Should not raise; return value is None (fire returns list, fire_subagent_stop discards)
        hm.fire_subagent_stop("Task", stop_reason="completed")

    def test_notification_hook_fires(self):
        self._write_global_hooks([{
            "event": "Notification",
            "command": ["sh", "-lc", "echo notified"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        hm.fire_notification("error", "boom")

    def test_pre_tool_matcher_regex_matches_multiple_tools(self):
        # Single regex hook covering Bash + Read.
        self._write_global_hooks([{
            "event": "PreToolUse",
            "matcher": {"tool_name": "re:Bash|Read"},
            "command": ["sh", "-lc", "exit 1"],
            "timeout": 5,
        }])
        cfg = self._build_config()
        hm = HookManager(cfg)
        self.assertEqual(hm.fire_pre_tool("Bash", {"command": "ls"}), "deny")
        self.assertEqual(hm.fire_pre_tool("Read", {"file_path": "/tmp/x"}), "deny")
        # WebFetch should not match — hook exits 1 only when matcher matches
        self.assertEqual(hm.fire_pre_tool("WebFetch", {"url": "https://example.com"}), "allow")


if __name__ == "__main__":
    unittest.main()
