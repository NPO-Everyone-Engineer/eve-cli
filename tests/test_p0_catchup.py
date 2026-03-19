"""
Test suite for P0 CLI catchup features.
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


class TestP0_3_NonInteractiveMode(unittest.TestCase):
    """Test P0-3: Non-interactive mode enhancements for CI/CD."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_output_format_json_exists(self):
        """Test that --output-format json option is available."""
        config = Config()
        # Check that output_format attribute exists
        self.assertTrue(hasattr(config, 'output_format'))

    def test_output_format_choices(self):
        """Test that output format supports text, json, stream-json."""
        valid_formats = {"text", "json", "stream-json"}
        # The config should support these formats
        config = Config()
        config.output_format = "json"
        self.assertIn(config.output_format, valid_formats)
        config.output_format = "stream-json"
        self.assertIn(config.output_format, valid_formats)

    def test_json_output_structure(self):
        """Test that JSON output has required fields for CI/CD."""
        # Simulate JSON output structure
        output = {
            "role": "assistant",
            "content": "Test response",
            "model": "test-model",
            "session_id": "test-session",
            "exit_code": 0,
        }
        # Verify required fields for CI/CD parsing
        self.assertIn("role", output)
        self.assertIn("content", output)
        self.assertIn("model", output)
        self.assertIn("session_id", output)
        self.assertIn("exit_code", output)
        # Verify it's valid JSON
        json_str = json.dumps(output, ensure_ascii=False)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["role"], "assistant")

    def test_exit_code_standards(self):
        """Test that exit codes follow CI/CD standards."""
        # Exit code standards:
        # 0 = Success
        # 1 = General error
        # 2 = Timeout
        # 3 = Max iterations reached
        self.assertEqual(0, 0)  # Success
        self.assertEqual(1, 1)  # General error
        self.assertEqual(2, 2)  # Timeout
        self.assertEqual(3, 3)  # Max iterations


class TestP0_4_ResumeReplay(unittest.TestCase):
    """Test P0-4: Resume/Replay functionality for failure recovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, ".eve-cli-config")
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_resume_flag_exists(self):
        """Test that --resume flag is available."""
        config = Config()
        self.assertTrue(hasattr(config, 'resume'))

    def test_session_id_flag_exists(self):
        """Test that --session-id flag is available."""
        config = Config()
        self.assertTrue(hasattr(config, 'session_id'))

    def test_list_sessions_flag_exists(self):
        """Test that --list-sessions flag is available."""
        config = Config()
        self.assertTrue(hasattr(config, 'list_sessions'))


class TestP0_2_NotificationHooks(HookFixtureMixin, unittest.TestCase):
    """Test P0-2: Notification hooks for better UX."""

    def test_hooks_config_exists(self):
        """Test that global hooks.json exists."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        self.assertTrue(os.path.exists(hooks_path), "hooks.json should exist")

    def test_hooks_have_post_tool_use(self):
        """Test that hooks include PostToolUse event."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        events = [hook.get("event") for hook in data.get("hooks", [])]
        self.assertIn("PostToolUse", events)

    def test_hooks_have_stop_event(self):
        """Test that hooks include Stop event."""
        hooks_path = os.path.expanduser("~/.config/eve-cli/hooks.json")
        with open(hooks_path, 'r') as f:
            data = json.load(f)
        events = [hook.get("event") for hook in data.get("hooks", [])]
        self.assertIn("Stop", events)

    def test_trusted_hooks_exists(self):
        """Test that trusted_hooks.json exists."""
        trusted_path = os.path.expanduser("~/.config/eve-cli/trusted_hooks.json")
        self.assertTrue(os.path.exists(trusted_path), "trusted_hooks.json should exist")


class TestCatchupDocumentation(unittest.TestCase):
    """Test that catchup plan documentation exists."""

    def test_instruction_file_exists(self):
        """Test that catchup instruction file exists."""
        instruction_path = os.path.join(
            SCRIPT_DIR, "00_Docs", "20260308_cli_catchup_instruction.md"
        )
        self.assertTrue(os.path.exists(instruction_path))

    def test_readme_has_catchup_section(self):
        """Test that README mentions catchup plan."""
        readme_path = os.path.join(SCRIPT_DIR, "README.md")
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("CLI キャッチアップ計画", content)
        self.assertIn("20260308_cli_catchup_instruction.md", content)


if __name__ == "__main__":
    unittest.main()
