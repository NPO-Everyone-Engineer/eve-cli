import os
import sys
import tempfile
import unittest
import importlib.util
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class TestRoutingHeuristics(unittest.TestCase):
    def test_latest_query_prefers_web_search(self):
        scored = eve_coder._score_tool_candidates("最新の OpenAI ニュースを調べて", allowed_tool_names={"WebSearch", "Read", "Grep"})
        self.assertTrue(scored)
        self.assertEqual(scored[0]["name"], "WebSearch")

    def test_direct_url_prefers_web_fetch(self):
        scored = eve_coder._score_tool_candidates("https://example.com/docs を読んで要約して", allowed_tool_names={"WebFetch", "WebSearch"})
        self.assertTrue(scored)
        self.assertEqual(scored[0]["name"], "WebFetch")

    def test_edit_request_adds_read_and_grep_dependencies(self):
        scored = eve_coder._score_tool_candidates(
            "ログイン処理のバグを修正して",
            allowed_tool_names={"Edit", "Read", "Grep"},
        )
        names = {item["name"] for item in scored}
        self.assertIn("Edit", names)
        self.assertIn("Read", names)
        self.assertIn("Grep", names)

    def test_prefilter_selects_strong_candidates(self):
        scored = eve_coder._score_tool_candidates(
            "最新情報を検索して https://example.com を読んで",
            allowed_tool_names={"WebSearch", "WebFetch", "Read"},
        )
        names = eve_coder._derive_route_prefilter(scored, {"WebSearch", "WebFetch", "Read"})
        self.assertIn("WebSearch", names)
        self.assertIn("WebFetch", names)


class TestEvolutionUsage(unittest.TestCase):
    def test_usage_tracking_accumulates_tokens_and_cost(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evo = eve_coder.EvolutionEngine(tmpdir)
            cost = evo.record_usage("qwen3.5:397b-cloud", 1000, 500, 1.0, 2.0)
            self.assertGreater(cost, 0.0)
            summary = evo.usage_summary()
            self.assertEqual(summary["prompt_tokens"], 1000)
            self.assertEqual(summary["completion_tokens"], 500)
            self.assertAlmostEqual(summary["estimated_cost_usd"], cost)
            self.assertEqual(summary["top_models"][0][0], "qwen3.5:397b-cloud")

    def test_usage_report_lines_include_cost_and_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evo = eve_coder.EvolutionEngine(tmpdir)
            evo.record_usage("qwen3-coder-next:cloud", 2000, 1000, 0.5, 1.5)
            cfg = eve_coder.Config()
            cfg.prompt_cost_per_mtok = 0.5
            cfg.completion_cost_per_mtok = 1.5
            session = SimpleNamespace(get_token_estimate=lambda: 1234)
            lines = eve_coder._build_usage_report_lines(cfg, evo, session=session)
            text = "\n".join(lines)
            self.assertIn("estimated cost", text)
            self.assertIn("qwen3-coder-next:cloud", text)


class TestDiagnosticsFormatting(unittest.TestCase):
    def test_tool_pool_lists_builtin_tools(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = eve_coder.ToolRegistry().register_defaults()
            permissions = eve_coder.PermissionMgr(SimpleNamespace(
                yes_mode=False,
                auto_mode=False,
                permissions_file=os.path.join(tmpdir, "permissions.json"),
                cwd=tmpdir,
                config_dir=tmpdir,
            ))
            lines = eve_coder._build_tool_pool_lines(registry, permissions, allowed_names={"Read", "Grep"})
            joined = "\n".join(lines)
            self.assertIn("Read", joined)
            self.assertIn("Grep", joined)

    def test_command_graph_uses_last_route_when_no_prompt(self):
        agent = SimpleNamespace(
            _plan_mode=False,
            _last_route_report={
                "plan_mode": False,
                "prefilter_active": True,
                "parallel_tasks": [],
                "candidates": [{"name": "Read", "score": 4, "reasons": ["file reference"]}],
            },
        )
        registry = eve_coder.ToolRegistry().register_defaults()
        lines = eve_coder._build_command_graph_lines(eve_coder.Config(), agent, registry)
        joined = "\n".join(lines)
        self.assertIn("last_route", joined)
        self.assertIn("Read", joined)

    def test_reasoning_settings_for_plan_mode(self):
        cfg = eve_coder.Config()
        cfg.think_mode = None
        cfg.thinking_budget = None
        cfg.plan_mode_reasoning_effort = "high"
        think_mode, budget, effort = eve_coder._resolve_reasoning_settings(cfg, plan_mode=True)
        self.assertTrue(think_mode)
        self.assertEqual(budget, 24576)
        self.assertEqual(effort, "high")

    def test_notification_manager_runs_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "notify.json")
            cfg = eve_coder.Config()
            cfg.cwd = tmpdir
            cfg.notify_command = f"python3 -c \"import pathlib,sys; pathlib.Path(r'{out_path}').write_text(sys.stdin.read(), encoding='utf-8')\""
            cfg.notify_on = ["stop"]
            mgr = eve_coder.NotificationManager(cfg)
            self.assertTrue(mgr.notify("stop", {"event": "stop", "ok": True}))
            with open(out_path, encoding="utf-8") as fh:
                payload = fh.read()
            self.assertIn('"event": "stop"', payload)

    def test_init_mcp_clients_filters_tools_and_honors_required(self):
        class FakeMCPClient:
            def __init__(self, name, command, args=None, env=None, startup_timeout=30, tool_timeout=30):
                self.name = name
                self.command = command
                self.args = args or []
                self.env = env or {}
                self.startup_timeout = startup_timeout
                self.tool_timeout = tool_timeout

            def start(self):
                return None

            def initialize(self):
                return None

            def list_tools(self):
                return [
                    {"name": "read_doc", "description": "read", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "write_doc", "description": "write", "inputSchema": {"type": "object", "properties": {}}},
                ]

        with tempfile.TemporaryDirectory() as tmpdir:
            registry = eve_coder.ToolRegistry().register_defaults()
            permissions = eve_coder.PermissionMgr(SimpleNamespace(
                yes_mode=False,
                auto_mode=False,
                permissions_file=os.path.join(tmpdir, "permissions.json"),
                cwd=tmpdir,
                config_dir=tmpdir,
            ))
            server_cfg = {
                "docs": {
                    "name": "docs",
                    "command": "python3",
                    "args": ["fake_mcp.py"],
                    "env": {},
                    "env_vars": [],
                    "enabled": True,
                    "required": False,
                    "enabled_tools": ["read_doc"],
                    "disabled_tools": ["write_doc"],
                    "startup_timeout_sec": 12,
                    "tool_timeout_sec": 34,
                }
            }
            with patch.object(eve_coder, "_load_mcp_servers", return_value=server_cfg), \
                 patch.object(eve_coder, "MCPClient", FakeMCPClient):
                clients = eve_coder._init_mcp_clients(eve_coder.Config(), registry, permissions)
            self.assertEqual(len(clients), 1)
            self.assertEqual(clients[0].startup_timeout, 12)
            self.assertEqual(clients[0].tool_timeout, 34)
            self.assertIn("mcp_docs_read_doc", registry.names())
            self.assertNotIn("mcp_docs_write_doc", registry.names())


if __name__ == "__main__":
    unittest.main()
