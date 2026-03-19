"""
Test suite for cmux notification hooks functionality.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# Import eve-coder.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

from tests import HookFixtureMixin

Config = eve_coder.Config
HookManager = eve_coder.HookManager


class TestCmuxHooksConfig(HookFixtureMixin, unittest.TestCase):
    """Test cmux hooks configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hooks_file_exists(self):
        """Test that global hooks.json exists."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        self.assertTrue(os.path.exists(hooks_path), "hooks.json should exist")

    def test_hooks_file_valid_json(self):
        """Test that hooks.json is valid JSON."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        self.assertIn("hooks", data)
        self.assertIsInstance(data["hooks"], list)

    def test_hooks_have_required_events(self):
        """Test that hooks include PostToolUse and Stop events."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        
        events = [hook.get("event") for hook in data.get("hooks", [])]
        self.assertIn("PostToolUse", events, "Should have PostToolUse hook")
        self.assertIn("Stop", events, "Should have Stop hook")

    def test_hooks_have_cmux_notify(self):
        """Test that hooks include cmux notify command."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        
        found_cmux = False
        for hook in data.get("hooks", []):
            command = hook.get("command", [])
            if isinstance(command, list):
                cmd_str = " ".join(str(c) for c in command)
            else:
                cmd_str = str(command)
            
            if "cmux notify" in cmd_str:
                found_cmux = True
                break
        
        self.assertTrue(found_cmux, "Should have cmux notify command")

    def test_hooks_have_socket_check(self):
        """Test that hooks check for cmux socket existence."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        
        found_socket_check = False
        for hook in data.get("hooks", []):
            command = hook.get("command", [])
            if isinstance(command, list):
                cmd_str = " ".join(str(c) for c in command)
            else:
                cmd_str = str(command)
            
            if "/tmp/cmux.sock" in cmd_str or "-S /tmp/cmux.sock" in cmd_str:
                found_socket_check = True
                break
        
        self.assertTrue(found_socket_check, "Should check for cmux socket existence")

    def test_trusted_hooks_file_exists(self):
        """Test that trusted_hooks.json exists."""
        trusted_path = os.path.expanduser("~/.config/eve-cli/trusted_hooks.json")
        self.assertTrue(os.path.exists(trusted_path), "trusted_hooks.json should exist")

    def test_trusted_hooks_valid_json(self):
        """Test that trusted_hooks.json is valid JSON."""
        trusted_path = os.path.expanduser("~/.config/eve-cli/trusted_hooks.json")
        with open(trusted_path, 'r') as f:
            data = json.load(f)
        self.assertIn("global", data)


class TestHookManagerCmux(HookFixtureMixin, unittest.TestCase):
    """Test HookManager with cmux hooks."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Create a mock config
        self.config = Config()
        self.config.config_dir = self.config_dir
        self.config.cwd = self.test_dir
        
        # Copy global hooks to test config dir
        global_hooks = os.path.expanduser("~/.config/eve-cli/hooks.json")
        if os.path.exists(global_hooks):
            test_hooks = os.path.join(self.config_dir, "hooks.json")
            shutil.copy(global_hooks, test_hooks)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hook_manager_loads_hooks(self):
        """Test that HookManager loads hooks from config."""
        hook_mgr = HookManager(self.config)
        self.assertTrue(len(hook_mgr._hooks) > 0, "Should load hooks")

    def test_hook_manager_has_hooks(self):
        """Test that HookManager reports has_hooks."""
        hook_mgr = HookManager(self.config)
        self.assertTrue(hook_mgr.has_hooks, "Should have hooks")

    def test_hook_events_are_valid(self):
        """Test that hook events are in valid event set."""
        hook_mgr = HookManager(self.config)
        valid_events = HookManager.VALID_EVENTS
        
        for hook in hook_mgr._hooks:
            event = hook.get("event")
            self.assertIn(event, valid_events, f"Invalid event: {event}")


class TestCmuxEnvironment(unittest.TestCase):
    """Test cmux environment availability."""

    def test_cmux_command_exists(self):
        """Test that cmux command is available."""
        result = shutil.which("cmux")
        self.assertIsNotNone(result, "cmux command should be available")

    def test_cmux_socket_exists(self):
        """Test that cmux socket exists."""
        socket_path = "/tmp/cmux.sock"
        self.assertTrue(os.path.exists(socket_path), "cmux socket should exist")
        # Check if it's a socket using stat
        import stat
        st = os.stat(socket_path)
        self.assertTrue(stat.S_ISSOCK(st.st_mode), "cmux socket should be a socket file")


if __name__ == "__main__":
    unittest.main()
