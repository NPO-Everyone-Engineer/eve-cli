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


def _make_config(tmpdir, yes_mode=False, rules=None, auto_mode=False, approval_mode=None):
    """Create a mock Config with a temporary permissions file."""
    perm_file = os.path.join(tmpdir, "permissions.json")
    if rules is not None:
        with open(perm_file, "w", encoding="utf-8") as f:
            json.dump(rules, f)
    if approval_mode is None:
        approval_mode = "full-auto" if yes_mode else "auto-run" if auto_mode else "suggest"
    else:
        approval_mode = eve_coder.Config.normalize_approval_mode(approval_mode) or approval_mode
        yes_mode = approval_mode == "full-auto"
        auto_mode = approval_mode == "auto-run"
    return SimpleNamespace(
        approval_mode=approval_mode,
        yes_mode=yes_mode,
        auto_mode=auto_mode,
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

    def test_parallel_agents_always_allowed(self):
        # Regression: ParallelAgents was missing from SAFE_TOOLS so full-auto
        # would still raise an interactive prompt for it (and InputMonitor was
        # eating the user's "y" key, leaving the user stuck).
        self.assertTrue(self.mgr.check("ParallelAgents", {"tasks": []}))

    def test_parallel_agents_allowed_in_full_auto(self):
        cfg = _make_config(self.tmpdir, approval_mode="full-auto")
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("ParallelAgents", {"tasks": []}))

    def test_ask_user_question_always_allowed(self):
        self.assertTrue(self.mgr.check("AskUserQuestion", {}))

    def test_task_tools_always_allowed(self):
        for tool in ("TaskCreate", "TaskList", "TaskGet", "TaskUpdate"):
            with self.subTest(tool=tool):
                self.assertTrue(self.mgr.check(tool, {}))

    def test_safe_tools_match_class_constant(self):
        expected = {"Read", "Glob", "Grep", "SubAgent", "ParallelAgents", "AskUserQuestion",
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


class TestPermissionMgrApprovalModes(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_auto_edit_allows_write_without_prompt(self):
        cfg = _make_config(self.tmpdir, approval_mode="auto-edit")
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("Write", {"file_path": os.path.join(self.tmpdir, "note.txt")}))

    def test_auto_edit_prompts_shell_without_tui(self):
        cfg = _make_config(self.tmpdir, approval_mode="auto-edit")
        mgr = PermissionMgr(cfg)
        self.assertFalse(mgr.check("Bash", {"command": "ls"}))

    def test_auto_run_prompts_push_without_tui(self):
        cfg = _make_config(self.tmpdir, approval_mode="auto-run")
        mgr = PermissionMgr(cfg)
        self.assertFalse(mgr.check("Bash", {"command": "git push origin main"}))

    def test_full_auto_allows_push_without_prompt(self):
        cfg = _make_config(self.tmpdir, approval_mode="full-auto")
        mgr = PermissionMgr(cfg)
        self.assertTrue(mgr.check("Bash", {"command": "git push origin main"}))

    def test_audit_blocks_write_even_when_session_allowed(self):
        cfg = _make_config(self.tmpdir, approval_mode="audit")
        mgr = PermissionMgr(cfg)
        mgr.session_allow("Write")
        self.assertFalse(mgr.check("Write", {"file_path": os.path.join(self.tmpdir, "note.txt")}))
        self.assertIn("audit mode blocks write actions", mgr.describe_last_decision())

    def test_policy_precedence_reports_current_approval_mode(self):
        cfg = _make_config(self.tmpdir, approval_mode="audit")
        mgr = PermissionMgr(cfg)
        self.assertIn("approval-mode(audit)", mgr.policy_precedence())


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

    def test_project_tool_prompt_rule_overrides_yes_mode(self):
        project_dir = os.path.join(self.tmpdir, ".eve-cli")
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump({"tools": {"WebFetch": "prompt"}}, f)
        cfg = _make_config(self.tmpdir, yes_mode=True)
        _trust_project_permissions(cfg)
        mgr = PermissionMgr(cfg)

        tui = SimpleNamespace(ask_permission=lambda *args, **kwargs: False)
        allowed = mgr.check("WebFetch", {"url": "https://example.com"}, tui=tui)
        self.assertFalse(allowed)
        self.assertIn("denied", mgr.describe_last_decision())

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

    def test_session_allow_does_not_persist_for_apply_patch(self):
        self.mgr.session_allow("ApplyPatch")
        self.assertNotIn("ApplyPatch", self.mgr.rules)

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
        expected = {"Bash", "Write", "Edit", "ApplyPatch", "MultiEdit", "NotebookEdit"}
        self.assertEqual(PermissionMgr.ASK_TOOLS, expected)

    def test_network_tools(self):
        expected = {"WebFetch", "WebSearch"}
        self.assertEqual(PermissionMgr.NETWORK_TOOLS, expected)

    def test_no_persist_allow(self):
        expected = {"Bash", "Write", "Edit", "ApplyPatch", "MultiEdit", "NotebookEdit"}
        self.assertEqual(PermissionMgr._NO_PERSIST_ALLOW, expected)


class TestPermissionMgrGuardian(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_auto_mode_low_risk_allows_without_prompt(self):
        cfg = _make_config(self.tmpdir, auto_mode=True)
        mgr = PermissionMgr(cfg)
        mgr._sidecar_client = object()
        mgr._sidecar_model = "sidecar"
        mgr._classify_with_sidecar = lambda tool, params: {"level": "low", "score": 0.1, "reason": "safe", "source": "guardian"}
        self.assertTrue(mgr.check("WebFetch", {"url": "https://example.com"}))

    def test_auto_mode_medium_risk_allows_without_prompt(self):
        cfg = _make_config(self.tmpdir, auto_mode=True)
        mgr = PermissionMgr(cfg)
        mgr._sidecar_client = object()
        mgr._sidecar_model = "sidecar"
        mgr._classify_with_sidecar = lambda tool, params: {"level": "medium", "score": 0.5, "reason": "review", "source": "guardian"}
        self.assertTrue(mgr.check("WebFetch", {"url": "https://example.com"}))

    def test_auto_mode_high_risk_denies(self):
        cfg = _make_config(self.tmpdir, auto_mode=True)
        mgr = PermissionMgr(cfg)
        mgr._sidecar_client = object()
        mgr._sidecar_model = "sidecar"
        mgr._classify_with_sidecar = lambda tool, params: {"level": "high", "score": 0.9, "reason": "danger", "source": "guardian"}
        self.assertFalse(mgr.check("WebFetch", {"url": "https://example.com"}))

    def test_auto_mode_high_risk_prompts_with_tui(self):
        cfg = _make_config(self.tmpdir, auto_mode=True)
        mgr = PermissionMgr(cfg)
        mgr._sidecar_client = object()
        mgr._sidecar_model = "sidecar"
        mgr._classify_with_sidecar = lambda tool, params: {"level": "high", "score": 0.9, "reason": "danger", "source": "guardian"}
        prompted_modes = []
        tui = SimpleNamespace(
            ask_permission=lambda *args, **kwargs: prompted_modes.append(kwargs.get("approval_mode")) or True
        )
        self.assertTrue(mgr.check("WebFetch", {"url": "https://example.com"}, tui=tui))
        self.assertEqual(prompted_modes, ["auto-run"])


class _ScriptedSidecarClient:
    """Sidecar client stub that returns successive scripted chat() responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def chat(self, *, model, messages, tools, stream, options):
        self.calls += 1
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    def build_utility_options(self, model, role, temperature):
        return {"temperature": temperature, "max_tokens": 64}


class TestSidecarClassifierRetry(unittest.TestCase):
    """Sidecar classifier should validate verdicts and retry once on transient failure."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir, auto_mode=True)
        self.mgr = PermissionMgr(cfg)
        self.mgr._sidecar_model = "sidecar"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @staticmethod
    def _resp(text):
        return {"choices": [{"message": {"content": text}}]}

    def test_clean_low_verdict_returns_low(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([self._resp("LOW\nread-only")])
        risk = self.mgr._classify_with_sidecar("Read", {"file_path": "/tmp/x"})
        self.assertIsNotNone(risk)
        self.assertEqual(risk["level"], "low")
        self.assertEqual(self.mgr._sidecar_client.calls, 1)

    def test_exception_then_success_uses_retry(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([
            RuntimeError("transient network error"),
            self._resp("HIGH\ndelete repo"),
        ])
        risk = self.mgr._classify_with_sidecar("Bash", {"command": "rm -rf ~"})
        self.assertIsNotNone(risk)
        self.assertEqual(risk["level"], "high")
        self.assertEqual(self.mgr._sidecar_client.calls, 2)

    def test_two_exceptions_returns_none(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([
            RuntimeError("err 1"),
            RuntimeError("err 2"),
        ])
        risk = self.mgr._classify_with_sidecar("Bash", {"command": "ls"})
        self.assertIsNone(risk)
        self.assertEqual(self.mgr._sidecar_client.calls, 2)

    def test_ambiguous_then_clean_uses_retry(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([
            self._resp("LOW or HIGH\nunclear"),
            self._resp("MEDIUM\nfile edit"),
        ])
        risk = self.mgr._classify_with_sidecar("Edit", {"file_path": "x.py"})
        self.assertIsNotNone(risk)
        self.assertEqual(risk["level"], "medium")
        self.assertEqual(self.mgr._sidecar_client.calls, 2)

    def test_two_ambiguous_returns_none(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([
            self._resp("MAYBE\nnot sure"),
            self._resp("LOW or HIGH\nunclear"),
        ])
        risk = self.mgr._classify_with_sidecar("Bash", {"command": "ls"})
        self.assertIsNone(risk)
        self.assertEqual(self.mgr._sidecar_client.calls, 2)

    def test_empty_content_then_success_uses_retry(self):
        self.mgr._sidecar_client = _ScriptedSidecarClient([
            self._resp(""),
            self._resp("LOW\nclean"),
        ])
        risk = self.mgr._classify_with_sidecar("Read", {"file_path": "x"})
        self.assertIsNotNone(risk)
        self.assertEqual(risk["level"], "low")
        self.assertEqual(self.mgr._sidecar_client.calls, 2)


if __name__ == "__main__":
    unittest.main()
