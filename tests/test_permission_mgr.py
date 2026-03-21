"""
Test suite for PermissionMgr: safe tools, yes mode, dangerous commands,
persistent rules, session allows/denies.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

PermissionMgr = eve_coder.PermissionMgr


def _make_config(tmpdir, yes_mode=False, rules=None):
    """Create a mock Config with a temporary permissions file."""
    perm_file = os.path.join(tmpdir, "permissions.json")
    if rules is not None:
        with open(perm_file, "w", encoding="utf-8") as f:
            json.dump(rules, f)
    return SimpleNamespace(
        yes_mode=yes_mode,
        permissions_file=perm_file,
        cwd=tmpdir,
        config_dir=tmpdir,
    )


def _trust_project_permissions(cfg):
    project_path = os.path.join(cfg.cwd, ".eve-cli", "permissions.json")
    hash_value = eve_coder._compute_file_hash(project_path)
    eve_coder._remember_repo_scope_trust(
        cfg,
        "permissions",
        {os.path.join(".eve-cli", "permissions.json"): hash_value},
    )


class TestPermissionMgrInit(unittest.TestCase):
    """Tests for initialization and rule loading."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_no_file(self):
        cfg = _make_config(self.tmpdir)
        mgr = PermissionMgr(cfg)
        self.assertEqual(mgr.rules, {})

    def test_init_loads_rules(self):
        cfg = _make_config(self.tmpdir, rules={"WebFetch": "allow"})
        mgr = PermissionMgr(cfg)
        self.assertEqual(mgr.rules.get("WebFetch"), "allow")

    def test_init_ignores_invalid_values(self):
        cfg = _make_config(self.tmpdir, rules={"Foo": "maybe", "Bar": 42})
        mgr = PermissionMgr(cfg)
        self.assertNotIn("Foo", mgr.rules)
        self.assertNotIn("Bar", mgr.rules)

    def test_init_bash_allow_not_loaded(self):
        """Persistently allowing Bash is never loaded from disk."""
        cfg = _make_config(self.tmpdir, rules={"Bash": "allow"})
        mgr = PermissionMgr(cfg)
        self.assertNotIn("Bash", mgr.rules)

    def test_init_bash_deny_loaded(self):
        """Bash deny rule IS loaded."""
        cfg = _make_config(self.tmpdir, rules={"Bash": "deny"})
        mgr = PermissionMgr(cfg)
        self.assertEqual(mgr.rules.get("Bash"), "deny")

    def test_init_symlink_file_skipped(self):
        """Symlink permissions file is skipped for security."""
        real_file = os.path.join(self.tmpdir, "real.json")
        with open(real_file, "w", encoding="utf-8") as f:
            json.dump({"WebFetch": "allow"}, f)
        link_file = os.path.join(self.tmpdir, "permissions.json")
        os.symlink(real_file, link_file)
        cfg = SimpleNamespace(yes_mode=False, permissions_file=link_file)
        mgr = PermissionMgr(cfg)
        self.assertEqual(mgr.rules, {})


class TestPermissionMgrSafeTools(unittest.TestCase):
    """Tests for SAFE_TOOLS always being allowed."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir, yes_mode=False)
        self.mgr = PermissionMgr(cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_read_always_allowed(self):
        self.assertTrue(self.mgr.check("Read", {}))

    def test_glob_always_allowed(self):
        self.assertTrue(self.mgr.check("Glob", {}))

    def test_grep_always_allowed(self):
        self.assertTrue(self.mgr.check("Grep", {}))

    def test_subagent_always_allowed(self):
        self.assertTrue(self.mgr.check("SubAgent", {}))

    def test_ask_user_question_always_allowed(self):
        self.assertTrue(self.mgr.check("AskUserQuestion", {}))

    def test_task_tools_always_allowed(self):
        for tool in ("TaskCreate", "TaskList", "TaskGet", "TaskUpdate"):
            with self.subTest(tool=tool):
                self.assertTrue(self.mgr.check(tool, {}))

    def test_safe_tools_match_class_constant(self):
        expected = {"Read", "Glob", "Grep", "SubAgent", "AskUserQuestion",
                    "TaskCreate", "TaskList", "TaskGet", "TaskUpdate"}
        self.assertEqual(PermissionMgr.SAFE_TOOLS, expected)


class TestPermissionMgrYesMode(unittest.TestCase):
    """Tests for yes_mode behavior."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_yes_mode_allows_bash(self):
        cfg = _make_config(self.tmpdir, yes_mode=True)
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("Bash", {"command": "ls"}))

    def test_yes_mode_allows_write(self):
        cfg = _make_config(self.tmpdir, yes_mode=True)
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("Write", {"file_path": "/tmp/test.txt"}))

    def test_yes_mode_allows_edit(self):
        cfg = _make_config(self.tmpdir, yes_mode=True)
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("Edit", {}))

    def test_yes_mode_allows_network(self):
        cfg = _make_config(self.tmpdir, yes_mode=True)
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("WebFetch", {"url": "https://example.com"}))


class TestPermissionMgrDangerousCommands(unittest.TestCase):
    """Tests for _ALWAYS_CONFIRM_PATTERNS: dangerous Bash commands that need
    confirmation even in yes_mode."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir, yes_mode=True)
        self.mgr = PermissionMgr(cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_rm_rf_root_blocked_without_tui(self):
        result = self.mgr.check("Bash", {"command": "rm -rf /"})
        self.assertFalse(result)

    def test_sudo_blocked_without_tui(self):
        result = self.mgr.check("Bash", {"command": "sudo apt-get install foo"})
        self.assertFalse(result)

    def test_mkfs_blocked_without_tui(self):
        result = self.mgr.check("Bash", {"command": "mkfs.ext4 /dev/sda1"})
        self.assertFalse(result)

    def test_dd_to_dev_blocked_without_tui(self):
        result = self.mgr.check("Bash", {"command": "dd if=/dev/zero of=/dev/sda bs=512"})
        self.assertFalse(result)

    def test_safe_bash_allowed_in_yes_mode(self):
        result = self.mgr.check("Bash", {"command": "echo hello"})
        self.assertTrue(result)

    def test_rm_safe_dir_allowed_in_yes_mode(self):
        result = self.mgr.check("Bash", {"command": "rm -rf ./build"})
        self.assertTrue(result)


class TestPermissionMgrPersistentRules(unittest.TestCase):
    """Tests for persistent rule checks (allow/deny loaded from file)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_persistent_allow(self):
        cfg = _make_config(self.tmpdir, rules={"WebFetch": "allow"})
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("WebFetch", {}))

    def test_persistent_deny(self):
        cfg = _make_config(self.tmpdir, rules={"WebFetch": "deny"})
        mgr = PermissionMgr(cfg)
        self.assertFalse(mgr.check("WebFetch", {}))


class TestPermissionMgrStructuredPolicies(unittest.TestCase):
    """Tests for project/global structured policy loading."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_project_path_rule_allows_write_without_prompt(self):
        project_dir = os.path.join(self.tmpdir, ".eve-cli")
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump({
                "paths": [
                    {"tool": "Write", "path": "docs/**", "decision": "allow"}
                ]
            }, f)
        cfg = _make_config(self.tmpdir, yes_mode=False)
        _trust_project_permissions(cfg)
        mgr = PermissionMgr(cfg)

        allowed = mgr.check("Write", {"file_path": os.path.join(self.tmpdir, "docs", "note.txt")})
        self.assertTrue(allowed)
        self.assertIn("path rule allow", mgr.describe_last_decision())

    def test_project_category_rule_denies_network(self):
        project_dir = os.path.join(self.tmpdir, ".eve-cli")
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump({"categories": {"network": "deny"}}, f)
        cfg = _make_config(self.tmpdir, yes_mode=False)
        _trust_project_permissions(cfg)
        mgr = PermissionMgr(cfg)

        allowed = mgr.check("WebFetch", {"url": "https://example.com"})
        self.assertFalse(allowed)
        self.assertIn("category rule deny", mgr.describe_last_decision())

    def test_policy_summary_counts_project_rules(self):
        project_dir = os.path.join(self.tmpdir, ".eve-cli")
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump({
                "tools": {"WebFetch": "deny"},
                "categories": {"network": "deny"},
                "paths": [{"tool": "Write", "path": "docs/**", "decision": "allow"}],
            }, f)
        cfg = _make_config(self.tmpdir, yes_mode=False)
        _trust_project_permissions(cfg)
        mgr = PermissionMgr(cfg)

        summary = mgr.policy_summary()
        self.assertEqual(summary["project_tool_rules"], 1)
        self.assertEqual(summary["project_category_rules"], 1)
        self.assertEqual(summary["project_path_rules"], 1)

    @patch("sys.stdin.isatty", return_value=False)
    def test_untrusted_project_permissions_are_ignored(self, _mock_isatty):
        project_dir = os.path.join(self.tmpdir, ".eve-cli")
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump({"categories": {"network": "deny"}}, f)
        cfg = _make_config(self.tmpdir, yes_mode=False)
        mgr = PermissionMgr(cfg)

        self.assertEqual(mgr.policy_summary()["project_category_rules"], 0)


class TestPermissionMgrSessionAllowDeny(unittest.TestCase):
    """Tests for session-level allow/deny decisions."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir, yes_mode=False)
        self.mgr = PermissionMgr(cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_session_deny_takes_priority(self):
        self.mgr._session_denies.add("WebFetch")
        self.assertFalse(self.mgr.check("WebFetch", {}))

    def test_session_deny_overrides_persistent_allow(self):
        self.mgr.rules["WebFetch"] = "allow"
        self.mgr._session_denies.add("WebFetch")
        self.assertFalse(self.mgr.check("WebFetch", {}))

    def test_session_allow_works(self):
        self.mgr.session_allow("WebFetch")
        self.assertTrue(self.mgr.check("WebFetch", {}))

    def test_session_allow_persists_for_network_tools(self):
        self.mgr.session_allow("WebFetch")
        self.assertEqual(self.mgr.rules.get("WebFetch"), "allow")

    def test_session_allow_does_not_persist_for_bash(self):
        self.mgr.session_allow("Bash")
        self.assertNotIn("Bash", self.mgr.rules)
        self.assertIn("Bash", self.mgr._session_allows)

    def test_session_allow_does_not_persist_for_write(self):
        self.mgr.session_allow("Write")
        self.assertNotIn("Write", self.mgr.rules)

    def test_session_allow_does_not_persist_for_edit(self):
        self.mgr.session_allow("Edit")
        self.assertNotIn("Edit", self.mgr.rules)

    def test_session_allow_does_not_persist_for_multiedit(self):
        self.mgr.session_allow("MultiEdit")
        self.assertNotIn("MultiEdit", self.mgr.rules)

    def test_session_allow_does_not_persist_for_notebook_edit(self):
        self.mgr.session_allow("NotebookEdit")
        self.assertNotIn("NotebookEdit", self.mgr.rules)


class TestPermissionMgrSaveRules(unittest.TestCase):
    """Tests for _save_rules() and persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_reload(self):
        cfg = _make_config(self.tmpdir)
        mgr = PermissionMgr(cfg)
        mgr.session_allow("WebSearch")
        # WebSearch is not in _NO_PERSIST_ALLOW, so it should be persisted
        perm_file = cfg.permissions_file
        self.assertTrue(os.path.isfile(perm_file))
        with open(perm_file, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("WebSearch"), "allow")

    def test_unknown_tool_denied_without_tui(self):
        cfg = _make_config(self.tmpdir, yes_mode=False)
        mgr = PermissionMgr(cfg)
        self.assertFalse(mgr.check("SomeUnknownTool", {}))


class TestPermissionMgrClassConstants(unittest.TestCase):
    """Tests for class-level constants."""

    def test_ask_tools(self):
        expected = {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"}
        self.assertEqual(PermissionMgr.ASK_TOOLS, expected)

    def test_network_tools(self):
        expected = {"WebFetch", "WebSearch"}
        self.assertEqual(PermissionMgr.NETWORK_TOOLS, expected)

    def test_no_persist_allow(self):
        expected = {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"}
        self.assertEqual(PermissionMgr._NO_PERSIST_ALLOW, expected)


if __name__ == "__main__":
    unittest.main()
