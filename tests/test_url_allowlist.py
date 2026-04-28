"""
Tests for URL allowlist / denylist (P2-4):
- _host_matches_pattern (exact, *.subdomain)
- check_url_allowed semantics (deny precedence, allowlist mode, default open)
- WebFetchTool integration via _active_permissions global
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

PermissionMgr = eve_coder.PermissionMgr
WebFetchTool = eve_coder.WebFetchTool


class TestHostMatchesPattern(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(PermissionMgr._host_matches_pattern("github.com", "github.com"))
        self.assertFalse(PermissionMgr._host_matches_pattern("api.github.com", "github.com"))

    def test_subdomain_wildcard(self):
        self.assertTrue(PermissionMgr._host_matches_pattern("api.github.com", "*.github.com"))
        self.assertTrue(PermissionMgr._host_matches_pattern("a.b.github.com", "*.github.com"))
        # Wildcard does NOT match the apex domain (Copilot CLI semantic)
        self.assertFalse(PermissionMgr._host_matches_pattern("github.com", "*.github.com"))

    def test_case_insensitive(self):
        self.assertTrue(PermissionMgr._host_matches_pattern("API.GitHub.COM", "*.github.com"))

    def test_trailing_dot_normalized(self):
        # FQDN trailing dot should not break matching.
        self.assertTrue(PermissionMgr._host_matches_pattern("github.com.", "github.com"))

    def test_empty_inputs(self):
        self.assertFalse(PermissionMgr._host_matches_pattern("", "github.com"))
        self.assertFalse(PermissionMgr._host_matches_pattern("github.com", ""))
        self.assertFalse(PermissionMgr._host_matches_pattern("github.com", "*."))


def _make_config(tmpdir, permissions_path=None):
    cfg = SimpleNamespace(
        cwd=os.path.join(tmpdir, "project"),
        config_dir=os.path.join(tmpdir, "config"),
        permissions_file=permissions_path or os.path.join(tmpdir, "config", "permissions.json"),
        yes_mode=False,
        auto_mode=False,
    )
    os.makedirs(cfg.cwd, exist_ok=True)
    os.makedirs(cfg.config_dir, exist_ok=True)
    return cfg


class TestCheckUrlAllowed(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _build_pm(self, allowed=None, denied=None):
        perms_path = os.path.join(self.tmpdir, "permissions.json")
        payload = {}
        if allowed is not None:
            payload["allowed_urls"] = allowed
        if denied is not None:
            payload["denied_urls"] = denied
        with open(perms_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        cfg = _make_config(self.tmpdir, permissions_path=perms_path)
        return PermissionMgr(cfg)

    def test_default_open_when_no_lists(self):
        pm = self._build_pm()
        ok, _ = pm.check_url_allowed("https://example.com/x")
        self.assertTrue(ok)

    def test_allowlist_mode_blocks_unlisted(self):
        pm = self._build_pm(allowed=["github.com", "*.github.com"])
        ok1, _ = pm.check_url_allowed("https://github.com/x")
        ok2, _ = pm.check_url_allowed("https://api.github.com/x")
        ok3, reason = pm.check_url_allowed("https://example.com/x")
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertFalse(ok3)
        self.assertIn("not in allowed_urls", reason)

    def test_denylist_blocks_matching(self):
        pm = self._build_pm(denied=["*.internal.example.com"])
        ok1, reason = pm.check_url_allowed("https://api.internal.example.com/x")
        ok2, _ = pm.check_url_allowed("https://example.com/x")
        self.assertFalse(ok1)
        self.assertIn("denied", reason)
        self.assertTrue(ok2)

    def test_deny_takes_precedence_over_allow(self):
        pm = self._build_pm(
            allowed=["*.example.com"],
            denied=["api.example.com"],
        )
        # api.example.com matches both → deny wins
        ok, reason = pm.check_url_allowed("https://api.example.com/x")
        self.assertFalse(ok)
        self.assertIn("denied", reason)
        # other.example.com is in allow only → allowed
        ok2, _ = pm.check_url_allowed("https://other.example.com/x")
        self.assertTrue(ok2)

    def test_url_without_scheme_or_host_is_blocked(self):
        pm = self._build_pm()
        ok, reason = pm.check_url_allowed("not a url")
        self.assertFalse(ok)


class TestWebFetchToolIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._original_active = eve_coder._active_permissions

    def tearDown(self):
        eve_coder._active_permissions = self._original_active
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _build_pm(self, allowed=None, denied=None):
        perms_path = os.path.join(self.tmpdir, "permissions.json")
        with open(perms_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v for k, v in (("allowed_urls", allowed), ("denied_urls", denied)) if v is not None},
                f,
            )
        cfg = _make_config(self.tmpdir, permissions_path=perms_path)
        return PermissionMgr(cfg)

    def test_webfetch_blocks_when_url_not_allowed(self):
        eve_coder._active_permissions = self._build_pm(allowed=["github.com"])
        tool = WebFetchTool()
        # SSRF guard would normally trigger first for example.com, but we patch
        # _is_private_ip to return False so that the allowlist check runs.
        with unittest.mock.patch.object(WebFetchTool, "_is_private_ip", return_value=False):
            out = tool.execute({"url": "https://example.com/x"})
        self.assertTrue(out.startswith("Error: URL blocked by permissions"))

    def test_webfetch_passes_allowlist_check_then_proceeds_to_fetch(self):
        # Allowed → should NOT short-circuit on the permissions error path.
        # We make _fetch_pinned raise so we can assert we got past the
        # allowlist gate and into the actual fetch path.
        eve_coder._active_permissions = self._build_pm(allowed=["example.com"])
        tool = WebFetchTool()
        with unittest.mock.patch.object(WebFetchTool, "_is_private_ip", return_value=False), \
             unittest.mock.patch.object(WebFetchTool, "_fetch_pinned", side_effect=RuntimeError("network mocked")):
            out = tool.execute({"url": "https://example.com/x"})
        self.assertIn("Error fetching URL", out)
        self.assertNotIn("blocked by permissions", out)


if __name__ == "__main__":
    unittest.main()
