"""
Tests for MCP server B+C security hybrid (Security Finding #1):
- DEFAULT_SAFE_TOOLS exposed only by default (read-only)
- DANGEROUS_TOOLS gated behind --mcp-server-allow
- Tool execution routed through PermissionMgr unless --mcp-server-yes
- PreToolUse / PostToolUse hooks fired
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

MCPServer = eve_coder.MCPServer


def _make_config(allow_tools=None, mcp_yes=False):
    return SimpleNamespace(
        mcp_server_allow_tools=list(allow_tools or []),
        mcp_server_yes=mcp_yes,
        model="",
        cwd=tempfile.gettempdir(),
    )


class _RecordingTool:
    def __init__(self, name="Bash", output="ok"):
        self.name = name
        self.executed = False
        self._output = output

    def execute(self, params):
        self.executed = True
        return self._output


class _StubRegistry:
    def __init__(self, tool):
        self._tool = tool

    def get(self, name):
        return self._tool if name == self._tool.name else None

    def get_schemas(self):
        return [{
            "type": "function",
            "function": {
                "name": self._tool.name,
                "description": "stub",
                "parameters": {"type": "object", "properties": {}},
            },
        }]


class _RecordingHookMgr:
    has_hooks = True

    def __init__(self, pre_decision="allow"):
        self.pre_decision = pre_decision
        self.pre_calls = []
        self.post_calls = []

    def fire_pre_tool(self, tool_name, params):
        self.pre_calls.append((tool_name, params))
        return self.pre_decision

    def fire_post_tool(self, tool_name, output, is_error):
        self.post_calls.append((tool_name, output, is_error))


class _RecordingPermissions:
    def __init__(self, allow=True, reason="denied for test"):
        self.allow = allow
        self.reason = reason
        self.checks = []

    def check(self, tool_name, params, tui=None):
        self.checks.append((tool_name, params))
        return self.allow

    def describe_last_decision(self):
        return self.reason


def _build_server(config, tool, hook_mgr=None, permissions=None):
    server = MCPServer.__new__(MCPServer)
    server.config = config
    server.registry = _StubRegistry(tool)
    server.permissions = permissions
    server.hook_mgr = hook_mgr
    server.exposed_tools = server._compute_exposed_tools()
    return server


class TestMCPExposedToolsDefault(unittest.TestCase):
    def test_default_only_safe_tools(self):
        server = _build_server(_make_config(), _RecordingTool("Read"))
        self.assertEqual(server.exposed_tools, MCPServer.DEFAULT_SAFE_TOOLS)
        self.assertNotIn("Bash", server.exposed_tools)
        self.assertNotIn("Write", server.exposed_tools)

    def test_explicit_allow_extends_set(self):
        server = _build_server(_make_config(allow_tools=["Bash", "Write"]),
                               _RecordingTool("Bash"))
        self.assertIn("Bash", server.exposed_tools)
        self.assertIn("Write", server.exposed_tools)
        # Read still kept
        self.assertIn("Read", server.exposed_tools)

    def test_unknown_tool_in_allow_is_dropped(self):
        server = _build_server(_make_config(allow_tools=["NotARealTool", "Bash"]),
                               _RecordingTool("Bash"))
        self.assertIn("Bash", server.exposed_tools)
        self.assertNotIn("NotARealTool", server.exposed_tools)


class TestMCPToolsCallGating(unittest.TestCase):
    def setUp(self):
        self.tool = _RecordingTool("Bash", output="ran ls")
        self.responses = []
        self.errors = []

    def _patch_io(self, server):
        def _send_response(req_id, result):
            self.responses.append({"id": req_id, "result": result})
        def _send_error(req_id, code, message):
            self.errors.append({"id": req_id, "code": code, "message": message})
        server._send_response = _send_response
        server._send_error = _send_error

    def test_tool_not_in_exposed_returns_error(self):
        server = _build_server(_make_config(), self.tool)  # Bash not allowed
        self._patch_io(server)
        server._handle_tools_call(1, {"name": "Bash", "arguments": {"command": "ls"}})
        self.assertFalse(self.tool.executed)
        self.assertEqual(len(self.errors), 1)
        self.assertIn("Tool not exposed", self.errors[0]["message"])

    def test_pre_tool_hook_deny_blocks_execution(self):
        hook = _RecordingHookMgr(pre_decision="deny")
        server = _build_server(_make_config(allow_tools=["Bash"]), self.tool,
                               hook_mgr=hook, permissions=_RecordingPermissions(allow=True))
        self._patch_io(server)
        server._handle_tools_call(2, {"name": "Bash", "arguments": {"command": "ls"}})
        self.assertFalse(self.tool.executed)
        self.assertEqual(hook.pre_calls, [("Bash", {"command": "ls"})])
        self.assertEqual(self.responses[-1]["result"]["isError"], True)
        self.assertIn("PreToolUse", self.responses[-1]["result"]["content"][0]["text"])

    def test_permissions_deny_blocks_execution(self):
        hook = _RecordingHookMgr()
        perms = _RecordingPermissions(allow=False, reason="deny rule matched")
        server = _build_server(_make_config(allow_tools=["Bash"]), self.tool,
                               hook_mgr=hook, permissions=perms)
        self._patch_io(server)
        server._handle_tools_call(3, {"name": "Bash", "arguments": {"command": "ls"}})
        self.assertFalse(self.tool.executed)
        self.assertEqual(perms.checks, [("Bash", {"command": "ls"})])
        self.assertIn("Permission denied", self.responses[-1]["result"]["content"][0]["text"])

    def test_mcp_server_yes_bypasses_permissions(self):
        hook = _RecordingHookMgr()
        perms = _RecordingPermissions(allow=False)  # would deny if checked
        server = _build_server(
            _make_config(allow_tools=["Bash"], mcp_yes=True),
            self.tool, hook_mgr=hook, permissions=perms,
        )
        self._patch_io(server)
        server._handle_tools_call(4, {"name": "Bash", "arguments": {"command": "ls"}})
        self.assertTrue(self.tool.executed)
        self.assertEqual(perms.checks, [], "permissions.check should not be called under --mcp-server-yes")
        self.assertEqual(hook.post_calls[0][0], "Bash")

    def test_post_tool_hook_fires_with_result_and_error_flag(self):
        hook = _RecordingHookMgr()
        perms = _RecordingPermissions(allow=True)
        server = _build_server(
            _make_config(allow_tools=["Bash"]),
            _RecordingTool("Bash", output="Error: simulated failure"),
            hook_mgr=hook, permissions=perms,
        )
        self._patch_io(server)
        server._handle_tools_call(5, {"name": "Bash", "arguments": {}})
        self.assertEqual(len(hook.post_calls), 1)
        name, output, is_error = hook.post_calls[0]
        self.assertEqual(name, "Bash")
        self.assertTrue(is_error)
        self.assertIn("simulated failure", output)


if __name__ == "__main__":
    unittest.main()
