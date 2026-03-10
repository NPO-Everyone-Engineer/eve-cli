"""
Test suite for loop mode functionality including time-based limits.
"""

import unittest
import sys
import os
import time
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


class TestLoopModeConfig(unittest.TestCase):
    """Test loop mode configuration parsing."""

    def test_default_loop_settings(self):
        """Test default loop mode settings."""
        config = Config()
        config.load([])
        
        self.assertFalse(config.loop_mode)
        self.assertEqual(config.max_agent_steps, Config.DEFAULT_MAX_AGENT_STEPS)
        self.assertEqual(config.max_loop_iterations, 5)
        self.assertEqual(config.done_string, "DONE")
        self.assertIsNone(config.max_loop_hours)

    def test_max_agent_steps(self):
        """Test setting max agent steps."""
        config = Config()
        config.load(["--max-agent-steps", "80"])

        self.assertEqual(config.max_agent_steps, 80)

    def test_max_agent_steps_capped(self):
        """Test that max agent steps is capped for safety."""
        config = Config()
        with patch("builtins.print") as mock_print:
            config.load(["--max-agent-steps", "500"])

        self.assertEqual(config.max_agent_steps, Config.HARD_MAX_AGENT_STEPS)
        printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        self.assertTrue(any("max-agent-steps capped" in arg for arg in printed_args))

    def test_max_agent_steps_negative(self):
        """Test that negative max agent steps raises error."""
        config = Config()
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                config.load(["--max-agent-steps", "-1"])

    def test_loop_mode_enabled(self):
        """Test enabling loop mode."""
        config = Config()
        config.load(["--loop"])
        
        self.assertTrue(config.loop_mode)

    def test_max_loop_iterations(self):
        """Test setting max loop iterations."""
        config = Config()
        config.load(["--max-loop-iterations", "10"])
        
        self.assertEqual(config.max_loop_iterations, 10)

    def test_done_string(self):
        """Test setting custom done string."""
        config = Config()
        config.load(["--done-string", "ALL_DONE"])
        
        self.assertEqual(config.done_string, "ALL_DONE")

    def test_max_loop_hours_valid(self):
        """Test setting valid max loop hours."""
        config = Config()
        config.load(["--max-loop-hours", "24"])
        
        self.assertEqual(config.max_loop_hours, 24.0)

    def test_max_loop_hours_float(self):
        """Test setting max loop hours with float value."""
        config = Config()
        config.load(["--max-loop-hours", "0.5"])
        
        self.assertEqual(config.max_loop_hours, 0.5)

    def test_max_loop_hours_capped_at_72(self):
        """Test that max loop hours is capped at 72 (3 days)."""
        config = Config()
        with patch("builtins.print") as mock_print:
            config.load(["--max-loop-hours", "100"])
        
        self.assertEqual(config.max_loop_hours, 72.0)
        # Check warning was printed
        printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        self.assertTrue(any("capped at 72 hours" in arg for arg in printed_args))

    def test_max_loop_hours_negative(self):
        """Test that negative max loop hours raises error."""
        config = Config()
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                config.load(["--max-loop-hours", "-5"])

    def test_max_loop_hours_zero(self):
        """Test setting max loop hours to zero."""
        config = Config()
        config.load(["--max-loop-hours", "0"])
        
        self.assertEqual(config.max_loop_hours, 0.0)

    def test_combined_loop_options(self):
        """Test combining multiple loop options."""
        config = Config()
        config.load([
            "--loop",
            "--max-loop-iterations", "10",
            "--done-string", "COMPLETE",
            "--max-loop-hours", "48"
        ])
        
        self.assertTrue(config.loop_mode)
        self.assertEqual(config.max_loop_iterations, 10)
        self.assertEqual(config.done_string, "COMPLETE")
        self.assertEqual(config.max_loop_hours, 48.0)


class TestLoopModeTimeCalculation(unittest.TestCase):
    """Test time-based loop limit calculations."""

    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation logic."""
        start_time = time.time()
        
        # Simulate 1 hour elapsed
        with patch("time.time", return_value=start_time + 3600):
            elapsed_hours = (time.time() - start_time) / 3600.0
            self.assertAlmostEqual(elapsed_hours, 1.0, places=2)

    def test_remaining_time_calculation(self):
        """Test remaining time calculation."""
        start_time = time.time()
        max_hours = 2.0
        
        # Simulate 30 minutes elapsed
        with patch("time.time", return_value=start_time + 1800):
            elapsed_hours = (time.time() - start_time) / 3600.0
            remaining_hours = max_hours - elapsed_hours
            self.assertAlmostEqual(remaining_hours, 1.5, places=2)

    def test_time_limit_reached(self):
        """Test time limit reached detection."""
        start_time = time.time()
        max_hours = 1.0
        
        # Simulate 1.5 hours elapsed (limit exceeded)
        with patch("time.time", return_value=start_time + 5400):
            elapsed_hours = (time.time() - start_time) / 3600.0
            self.assertGreater(elapsed_hours, max_hours)


if __name__ == "__main__":
    unittest.main()
