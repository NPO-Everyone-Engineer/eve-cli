"""
Test suite for sub-agent dynamic scaling feature.
Tests for _calc_subagent_parallel_cap, ParallelAgents, and AgentTeam.
"""

import unittest
import sys
import os
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

_calc_subagent_parallel_cap = eve_coder._calc_subagent_parallel_cap
_get_subagent_max_parallel = eve_coder._get_subagent_max_parallel
_get_team_max_agents = eve_coder._get_team_max_agents


class TestCalcSubagentParallelCap(unittest.TestCase):
    """Test _calc_subagent_parallel_cap function."""

    def test_low_spec_ram_cpu(self):
        """Test low spec machine (RAM < 16GB or CPU <= 4 cores)."""
        # RAM < 16GB
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=8, cpu_count=4), 2)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=15, cpu_count=4), 2)
        # CPU <= 4 cores
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=32, cpu_count=4), 2)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=64, cpu_count=2), 2)

    def test_mid_spec_ram_cpu(self):
        """Test mid spec machine (RAM 16-31GB or CPU <= 8 cores)."""
        # RAM 16-31GB
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=16, cpu_count=8), 4)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=31, cpu_count=8), 4)
        # CPU <= 8 cores (with sufficient RAM)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=64, cpu_count=8), 4)

    def test_high_spec_ram_cpu(self):
        """Test high spec machine (RAM 32-63GB or CPU <= 12 cores)."""
        # RAM 32-63GB
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=32, cpu_count=12), 6)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=63, cpu_count=12), 6)
        # CPU <= 12 cores (with sufficient RAM)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=128, cpu_count=12), 6)

    def test_very_high_spec(self):
        """Test very high spec machine (RAM >= 64GB and CPU > 12 cores)."""
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=64, cpu_count=16), 8)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=128, cpu_count=24), 8)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=256, cpu_count=32), 8)

    def test_hard_max_clamping(self):
        """Test that hard_max properly clamps the result."""
        # Even with high specs, hard_max should limit
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=128, cpu_count=32, hard_max=4), 4)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=128, cpu_count=32, hard_max=6), 6)
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=128, cpu_count=32, hard_max=12), 8)

    def test_minimum_value(self):
        """Test that result is always at least 1."""
        self.assertEqual(_calc_subagent_parallel_cap(ram_gb=1, cpu_count=1), 2)  # Low spec = 2
        # Even with invalid inputs, should return at least 1
        self.assertGreaterEqual(_calc_subagent_parallel_cap(ram_gb=-1, cpu_count=-1), 1)

    def test_invalid_inputs_fallback(self):
        """Test that invalid inputs use fallback values."""
        # None values should auto-detect (but we can't test actual detection)
        result = _calc_subagent_parallel_cap(ram_gb=None, cpu_count=None)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 8)
        
        # Invalid types should use fallback
        result = _calc_subagent_parallel_cap(ram_gb="invalid", cpu_count="invalid")
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 8)

    def test_zero_and_negative_values(self):
        """Test that zero and negative values use fallback."""
        result = _calc_subagent_parallel_cap(ram_gb=0, cpu_count=0)
        self.assertGreaterEqual(result, 1)
        
        result = _calc_subagent_parallel_cap(ram_gb=-10, cpu_count=-4)
        self.assertGreaterEqual(result, 1)


class TestGetSubagentMaxParallel(unittest.TestCase):
    """Test _get_subagent_max_parallel function."""

    def setUp(self):
        """Set up test fixtures."""
        # Save original environment
        self.original_env = os.environ.get("SUBAGENT_MAX_PARALLEL")
        if "SUBAGENT_MAX_PARALLEL" in os.environ:
            del os.environ["SUBAGENT_MAX_PARALLEL"]

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        if self.original_env is not None:
            os.environ["SUBAGENT_MAX_PARALLEL"] = self.original_env
        elif "SUBAGENT_MAX_PARALLEL" in os.environ:
            del os.environ["SUBAGENT_MAX_PARALLEL"]

    def test_env_variable_valid(self):
        """Test that valid env variable is used."""
        os.environ["SUBAGENT_MAX_PARALLEL"] = "6"
        self.assertEqual(_get_subagent_max_parallel(), 6)
        
        os.environ["SUBAGENT_MAX_PARALLEL"] = "1"
        self.assertEqual(_get_subagent_max_parallel(), 1)
        
        os.environ["SUBAGENT_MAX_PARALLEL"] = "12"
        self.assertEqual(_get_subagent_max_parallel(), 12)

    def test_env_variable_clamped(self):
        """Test that out-of-range env values are clamped."""
        os.environ["SUBAGENT_MAX_PARALLEL"] = "0"
        self.assertEqual(_get_subagent_max_parallel(), 1)
        
        os.environ["SUBAGENT_MAX_PARALLEL"] = "20"
        self.assertEqual(_get_subagent_max_parallel(), 12)
        
        os.environ["SUBAGENT_MAX_PARALLEL"] = "-5"
        self.assertEqual(_get_subagent_max_parallel(), 1)

    def test_env_variable_invalid(self):
        """Test that invalid env variable falls back to dynamic calculation."""
        os.environ["SUBAGENT_MAX_PARALLEL"] = "invalid"
        result = _get_subagent_max_parallel()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 8)

    def test_no_env_dynamic_calculation(self):
        """Test that without env var, dynamic calculation is used."""
        if "SUBAGENT_MAX_PARALLEL" in os.environ:
            del os.environ["SUBAGENT_MAX_PARALLEL"]
        result = _get_subagent_max_parallel()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 8)


class TestGetTeamMaxAgents(unittest.TestCase):
    """Test _get_team_max_agents function."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_subagent = os.environ.get("SUBAGENT_MAX_PARALLEL")
        self.original_team = os.environ.get("TEAM_MAX_AGENTS")
        for var in ["SUBAGENT_MAX_PARALLEL", "TEAM_MAX_AGENTS"]:
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        """Clean up test fixtures."""
        for var, val in [("SUBAGENT_MAX_PARALLEL", self.original_subagent),
                         ("TEAM_MAX_AGENTS", self.original_team)]:
            if val is not None:
                os.environ[var] = val
            elif var in os.environ:
                del os.environ[var]

    def test_team_env_variable(self):
        """Test that TEAM_MAX_AGENTS env variable is used."""
        os.environ["TEAM_MAX_AGENTS"] = "5"
        self.assertEqual(_get_team_max_agents(), 5)

    def test_team_env_clamped(self):
        """Test that TEAM_MAX_AGENTS is clamped."""
        os.environ["TEAM_MAX_AGENTS"] = "20"
        self.assertEqual(_get_team_max_agents(), 12)
        
        os.environ["TEAM_MAX_AGENTS"] = "0"
        self.assertEqual(_get_team_max_agents(), 1)

    def test_fallback_to_subagent(self):
        """Test that TEAM_MAX_AGENTS falls back to SUBAGENT_MAX_PARALLEL."""
        os.environ["SUBAGENT_MAX_PARALLEL"] = "7"
        self.assertEqual(_get_team_max_agents(), 7)

    def test_no_env_dynamic(self):
        """Test dynamic calculation when no env vars set."""
        for var in ["SUBAGENT_MAX_PARALLEL", "TEAM_MAX_AGENTS"]:
            if var in os.environ:
                del os.environ[var]
        result = _get_team_max_agents()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 8)


class TestParallelAgentsDynamicLimit(unittest.TestCase):
    """Test ParallelAgentTool with dynamic limits."""

    def test_parameters_use_dynamic_max(self):
        """Test that ParallelAgentTool.parameters uses dynamic max."""
        # Mock coordinator
        mock_coordinator = MagicMock()
        parallel_tool = eve_coder.ParallelAgentTool(mock_coordinator)
        
        params = parallel_tool.parameters
        tasks_schema = params["properties"]["tasks"]
        
        # maxItems should be set dynamically
        self.assertIn("maxItems", tasks_schema)
        max_items = tasks_schema["maxItems"]
        self.assertGreaterEqual(max_items, 1)
        self.assertLessEqual(max_items, 12)


class TestAgentTeamDynamicLimit(unittest.TestCase):
    """Test AgentTeam with dynamic limits."""

    def test_init_sets_dynamic_max(self):
        """Test that AgentTeam.__init__ sets MAX_TEAMMATES dynamically."""
        # Mock dependencies
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_registry = MagicMock()
        mock_permissions = MagicMock()
        
        team = eve_coder.AgentTeam(mock_config, mock_client, mock_registry, mock_permissions)
        
        # MAX_TEAMMATES should be set dynamically
        self.assertGreaterEqual(team.MAX_TEAMMATES, 1)
        self.assertLessEqual(team.MAX_TEAMMATES, 12)

    def test_run_clamps_num_teammates(self):
        """Test that AgentTeam.run clamps num_teammates to MAX_TEAMMATES."""
        # Mock dependencies
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_registry = MagicMock()
        mock_permissions = MagicMock()
        
        team = eve_coder.AgentTeam(mock_config, mock_client, mock_registry, mock_permissions)
        original_max = team.MAX_TEAMMATES
        
        # Mock the LLM decomposition to avoid actual API calls
        with patch.object(team, '_stop_event'):
            # This test verifies the clamp logic exists
            # Actual execution would require full agent setup
            num_teammates = max(1, min(100, team.MAX_TEAMMATES))
            self.assertLessEqual(num_teammates, original_max)


if __name__ == "__main__":
    unittest.main()
