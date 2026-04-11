"""
Comprehensive test suite for the Config class.

Covers default values, _normalize_max_agent_steps edge cases, config file parsing,
environment variable loading, CLI argument parsing, full-width space handling,
profile sections, and backward compatibility paths.
"""

import unittest
import sys
import os
import io
import tempfile
import textwrap
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


class TestConfigDefaults(unittest.TestCase):
    """Test that Config.__init__ sets correct default values."""

    def setUp(self):
        self.cfg = Config()

    def test_default_ollama_host(self):
        self.assertEqual(self.cfg.ollama_host, "http://localhost:11434")

    def test_default_model(self):
        self.assertEqual(self.cfg.model, "glm-5.1:cloud")

    def test_default_sidecar_model(self):
        self.assertEqual(self.cfg.sidecar_model, "gemma4:31b-cloud")

    def test_default_review_model(self):
        self.assertEqual(self.cfg.review_model, "")

    def test_default_rubber_duck_disabled(self):
        self.assertFalse(self.cfg.rubber_duck)

    def test_default_rubber_duck_checkpoints(self):
        self.assertEqual(self.cfg.rubber_duck_checkpoints, "plan,post-edit")

    def test_default_max_tokens(self):
        self.assertEqual(self.cfg.max_tokens, 8192)

    def test_default_temperature(self):
        self.assertAlmostEqual(self.cfg.temperature, 0.7)

    def test_default_context_window(self):
        self.assertEqual(self.cfg.context_window, 65536)

    def test_default_prompt_cost_per_mtok(self):
        self.assertEqual(self.cfg.prompt_cost_per_mtok, 0.0)

    def test_default_completion_cost_per_mtok(self):
        self.assertEqual(self.cfg.completion_cost_per_mtok, 0.0)

    def test_default_plan_mode_reasoning_effort(self):
        self.assertEqual(self.cfg.plan_mode_reasoning_effort, "")

    def test_default_shell_env_policy(self):
        self.assertEqual(self.cfg.shell_env_policy, "default")

    def test_default_hook_env_policy(self):
        self.assertEqual(self.cfg.hook_env_policy, "default")

    def test_default_notify_on(self):
        self.assertEqual(self.cfg.notify_on, ["stop"])

    def test_default_max_agent_steps(self):
        self.assertEqual(self.cfg.max_agent_steps, 100)

    def test_default_prompt_none(self):
        self.assertIsNone(self.cfg.prompt)

    def test_default_output_format(self):
        self.assertEqual(self.cfg.output_format, "text")

    def test_default_yes_mode_false(self):
        self.assertFalse(self.cfg.yes_mode)

    def test_default_debug_false(self):
        self.assertFalse(self.cfg.debug)

    def test_default_resume_false(self):
        self.assertFalse(self.cfg.resume)

    def test_default_rag_false(self):
        self.assertFalse(self.cfg.rag)

    def test_default_rag_mode(self):
        self.assertEqual(self.cfg.rag_mode, "query")

    def test_default_rag_topk(self):
        self.assertEqual(self.cfg.rag_topk, 5)

    def test_default_rag_model(self):
        self.assertEqual(self.cfg.rag_model, "nomic-embed-text")

    def test_default_loop_mode_false(self):
        self.assertFalse(self.cfg.loop_mode)

    def test_default_max_loop_iterations(self):
        self.assertEqual(self.cfg.max_loop_iterations, 5)

    def test_default_done_string(self):
        self.assertEqual(self.cfg.done_string, "DONE")

    def test_default_max_loop_hours_none(self):
        self.assertIsNone(self.cfg.max_loop_hours)

    def test_default_learn_mode_false(self):
        self.assertFalse(self.cfg.learn_mode)

    def test_default_learn_level(self):
        self.assertEqual(self.cfg.learn_level, 3)

    def test_default_ui_theme(self):
        self.assertEqual(self.cfg.ui_theme, "normal")

    def test_default_profile(self):
        self.assertEqual(self.cfg.profile, "auto")

    def test_class_constants(self):
        self.assertEqual(Config.DEFAULT_OLLAMA_HOST, "http://localhost:11434")
        self.assertEqual(Config.DEFAULT_MAX_TOKENS, 8192)
        self.assertAlmostEqual(Config.DEFAULT_TEMPERATURE, 0.7)
        self.assertEqual(Config.DEFAULT_CONTEXT_WINDOW, 65536)
        self.assertEqual(Config.DEFAULT_MAX_AGENT_STEPS, 100)
        self.assertEqual(Config.HARD_MAX_AGENT_STEPS, 200)


class TestNormalizeMaxAgentSteps(unittest.TestCase):
    """Test Config._normalize_max_agent_steps edge cases."""

    def setUp(self):
        self.cfg = Config()

    def test_valid_int(self):
        self.assertEqual(self.cfg._normalize_max_agent_steps(50), 50)

    def test_valid_string_int(self):
        self.assertEqual(self.cfg._normalize_max_agent_steps("75"), 75)

    def test_boundary_value_1(self):
        self.assertEqual(self.cfg._normalize_max_agent_steps(1), 1)

    def test_boundary_value_200(self):
        self.assertEqual(self.cfg._normalize_max_agent_steps(200), 200)

    def test_zero_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps(0))

    def test_negative_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps(-5))

    def test_non_int_string_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps("abc"))

    def test_none_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps(None))

    def test_float_string_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps("3.5"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.cfg._normalize_max_agent_steps(""))

    def test_exceeds_hard_max_caps(self):
        result = self.cfg._normalize_max_agent_steps(300)
        self.assertEqual(result, Config.HARD_MAX_AGENT_STEPS)

    def test_exceeds_hard_max_with_emit_errors_warns(self):
        with patch("builtins.print") as mock_print:
            result = self.cfg._normalize_max_agent_steps(300, emit_errors=True)
        self.assertEqual(result, Config.HARD_MAX_AGENT_STEPS)
        mock_print.assert_called_once()
        call_str = mock_print.call_args[0][0]
        self.assertIn("capped", call_str.lower())

    def test_negative_with_emit_errors_exits(self):
        with self.assertRaises(SystemExit):
            self.cfg._normalize_max_agent_steps(-1, emit_errors=True)

    def test_zero_with_emit_errors_exits(self):
        with self.assertRaises(SystemExit):
            self.cfg._normalize_max_agent_steps(0, emit_errors=True)

    def test_exactly_hard_max_returns_value(self):
        self.assertEqual(
            self.cfg._normalize_max_agent_steps(Config.HARD_MAX_AGENT_STEPS),
            Config.HARD_MAX_AGENT_STEPS,
        )

    def test_one_above_hard_max_caps(self):
        self.assertEqual(
            self.cfg._normalize_max_agent_steps(Config.HARD_MAX_AGENT_STEPS + 1),
            Config.HARD_MAX_AGENT_STEPS,
        )


class TestParseConfigFile(unittest.TestCase):
    """Test Config._parse_config_file with temporary config files."""

    def setUp(self):
        self.cfg = Config()

    def _write_config(self, content):
        """Write config content to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".cfg")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(content))
        return path

    def test_basic_model_setting(self):
        path = self._write_config("MODEL = qwen3:8b\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "qwen3:8b")
        finally:
            os.unlink(path)

    def test_sidecar_model(self):
        path = self._write_config("SIDECAR_MODEL = llama3:latest\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.sidecar_model, "llama3:latest")
        finally:
            os.unlink(path)

    def test_role_specific_models(self):
        path = self._write_config("""
            UTILITY_MODEL = qwen3:8b
            COMPACTION_MODEL = gemma4:31b
            SUBAGENT_MODEL = qwen3.5:32b
            REVIEW_MODEL = gemma4:31b-cloud
            RUBBER_DUCK = true
            RUBBER_DUCK_CHECKPOINTS = plan
        """)
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.utility_model, "qwen3:8b")
            self.assertEqual(self.cfg.compaction_model, "gemma4:31b")
            self.assertEqual(self.cfg.subagent_model, "qwen3.5:32b")
            self.assertEqual(self.cfg.review_model, "gemma4:31b-cloud")
            self.assertTrue(self.cfg.rubber_duck)
            self.assertEqual(self.cfg.rubber_duck_checkpoints, "plan")
        finally:
            os.unlink(path)

    def test_ollama_host(self):
        path = self._write_config("OLLAMA_HOST = http://192.168.1.100:11434\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.ollama_host, "http://192.168.1.100:11434")
        finally:
            os.unlink(path)

    def test_ollama_api_key(self):
        path = self._write_config("OLLAMA_API_KEY = secret-token\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.ollama_api_key, "secret-token")
        finally:
            os.unlink(path)

    def test_pricing_fields(self):
        path = self._write_config("PROMPT_COST_PER_MTOK = 0.12\nCOMPLETION_COST_PER_MTOK = 0.34\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.prompt_cost_per_mtok, 0.12)
            self.assertEqual(self.cfg.completion_cost_per_mtok, 0.34)
        finally:
            os.unlink(path)

    def test_advanced_runtime_fields(self):
        path = self._write_config(
            "PLAN_MODE_REASONING_EFFORT = high\n"
            "SHELL_ENV_POLICY = inherit\n"
            "SHELL_ENV_INCLUDE = CI,HTTPS_PROXY\n"
            "SHELL_ENV_EXCLUDE = PATH\n"
            "SHELL_ENV_SET = FOO=bar,HELLO=world\n"
            "HOOK_ENV_POLICY = inherit\n"
            "NOTIFY_COMMAND = python3 notify.py\n"
            "NOTIFY_ON = stop,error\n"
            "SKILLS_ENABLE = design*,review\n"
            "SKILLS_DISABLE = bugfix\n"
        )
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.plan_mode_reasoning_effort, "high")
            self.assertEqual(self.cfg.shell_env_policy, "inherit")
            self.assertEqual(self.cfg.shell_env_include, ["CI", "HTTPS_PROXY"])
            self.assertEqual(self.cfg.shell_env_exclude, ["PATH"])
            self.assertEqual(self.cfg.shell_env_set["FOO"], "bar")
            self.assertEqual(self.cfg.hook_env_policy, "inherit")
            self.assertEqual(self.cfg.notify_command, "python3 notify.py")
            self.assertEqual(self.cfg.notify_on, ["stop", "error"])
            self.assertEqual(self.cfg.skill_enable_patterns, ["design*", "review"])
            self.assertEqual(self.cfg.skill_disable_patterns, ["bugfix"])
        finally:
            os.unlink(path)

    def test_max_tokens(self):
        path = self._write_config("MAX_TOKENS = 4096\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.max_tokens, 4096)
        finally:
            os.unlink(path)

    def test_temperature(self):
        path = self._write_config("TEMPERATURE = 0.3\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertAlmostEqual(self.cfg.temperature, 0.3)
        finally:
            os.unlink(path)

    def test_context_window(self):
        path = self._write_config("CONTEXT_WINDOW = 65536\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.context_window, 65536)
        finally:
            os.unlink(path)

    def test_max_agent_steps(self):
        path = self._write_config("MAX_AGENT_STEPS = 80\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.max_agent_steps, 80)
        finally:
            os.unlink(path)

    def test_max_agent_steps_invalid_ignored(self):
        path = self._write_config("MAX_AGENT_STEPS = notanumber\n")
        try:
            self.cfg._parse_config_file(path)
            # Should remain at default since invalid value is ignored
            self.assertEqual(self.cfg.max_agent_steps, Config.DEFAULT_MAX_AGENT_STEPS)
        finally:
            os.unlink(path)

    def test_comments_and_blank_lines_skipped(self):
        content = """\
        # This is a comment

        MODEL = test-model
        # Another comment
        TEMPERATURE = 0.5
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "test-model")
            self.assertAlmostEqual(self.cfg.temperature, 0.5)
        finally:
            os.unlink(path)

    def test_quoted_values_stripped(self):
        path = self._write_config('MODEL = "qwen3:8b"\n')
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "qwen3:8b")
        finally:
            os.unlink(path)

    def test_single_quoted_values_stripped(self):
        path = self._write_config("MODEL = 'qwen3:8b'\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "qwen3:8b")
        finally:
            os.unlink(path)

    def test_profile_setting(self):
        path = self._write_config("PROFILE = offline\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.profile, "offline")
        finally:
            os.unlink(path)

    def test_markdown_renderer(self):
        path = self._write_config("MARKDOWN_RENDERER = simple\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.markdown_renderer, "simple")
        finally:
            os.unlink(path)

    def test_ui_theme(self):
        path = self._write_config("UI_THEME = gal\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.ui_theme, "gal")
        finally:
            os.unlink(path)

    def test_lines_without_equals_skipped(self):
        content = """\
        MODEL = test-model
        this line has no equals sign
        TEMPERATURE = 0.9
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "test-model")
            self.assertAlmostEqual(self.cfg.temperature, 0.9)
        finally:
            os.unlink(path)

    def test_invalid_max_tokens_ignored(self):
        path = self._write_config("MAX_TOKENS = not_a_number\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.max_tokens, Config.DEFAULT_MAX_TOKENS)
        finally:
            os.unlink(path)

    def test_invalid_temperature_ignored(self):
        path = self._write_config("TEMPERATURE = warm\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertAlmostEqual(self.cfg.temperature, Config.DEFAULT_TEMPERATURE)
        finally:
            os.unlink(path)

    def test_invalid_context_window_ignored(self):
        path = self._write_config("CONTEXT_WINDOW = big\n")
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.context_window, Config.DEFAULT_CONTEXT_WINDOW)
        finally:
            os.unlink(path)

    def test_empty_value_ignored(self):
        path = self._write_config("MODEL = \n")
        try:
            original = self.cfg.model
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, original)
        finally:
            os.unlink(path)


class TestProfileSections(unittest.TestCase):
    """Test profile section parsing in config files."""

    def setUp(self):
        self.cfg = Config()

    def _write_config(self, content):
        fd, path = tempfile.mkstemp(suffix=".cfg")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(content))
        return path

    def test_profile_section_parsed(self):
        content = """\
        MODEL = default-model

        [profile:online]
        MODEL = cloud-model
        OLLAMA_HOST = http://cloud:11434
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            self.assertEqual(self.cfg.model, "default-model")
            self.assertIn("online", self.cfg._profiles)
            self.assertEqual(self.cfg._profiles["online"]["MODEL"], "cloud-model")
            self.assertEqual(self.cfg._profiles["online"]["OLLAMA_HOST"], "http://cloud:11434")
        finally:
            os.unlink(path)

    def test_multiple_profiles(self):
        content = """\
        [profile:online]
        MODEL = cloud-model

        [profile:offline]
        MODEL = local-model
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            self.assertIn("online", self.cfg._profiles)
            self.assertIn("offline", self.cfg._profiles)
            self.assertEqual(self.cfg._profiles["online"]["MODEL"], "cloud-model")
            self.assertEqual(self.cfg._profiles["offline"]["MODEL"], "local-model")
        finally:
            os.unlink(path)

    def test_profile_values_do_not_affect_globals(self):
        content = """\
        MODEL = global-model

        [profile:custom]
        MODEL = custom-model
        MAX_TOKENS = 2048
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            # Global model should remain unchanged by profile section
            self.assertEqual(self.cfg.model, "global-model")
            self.assertEqual(self.cfg.max_tokens, Config.DEFAULT_MAX_TOKENS)
        finally:
            os.unlink(path)

    def test_non_profile_section_resets_to_global(self):
        content = """\
        [profile:myprofile]
        MODEL = profile-model

        [other]
        MODEL = should-be-global
        """
        path = self._write_config(content)
        try:
            self.cfg._parse_config_file(path)
            # After [other] (not a profile section), parsing should go back to global
            self.assertEqual(self.cfg.model, "should-be-global")
        finally:
            os.unlink(path)


class TestLoadEnv(unittest.TestCase):
    """Test Config._load_env with environment variable patching."""

    def setUp(self):
        self.cfg = Config()

    def _clean_env(self):
        """Return a dict of env vars to remove for clean testing."""
        keys = [
            "OLLAMA_HOST", "EVE_CODER_MODEL", "EVE_CLI_MODEL",
            "OLLAMA_API_KEY", "EVE_CLI_OLLAMA_API_KEY",
            "EVE_CLI_PROMPT_COST_PER_MTOK", "EVE_CLI_COMPLETION_COST_PER_MTOK",
            "EVE_CLI_PLAN_MODE_REASONING_EFFORT",
            "EVE_CLI_SHELL_ENV_POLICY", "EVE_CLI_SHELL_ENV_INCLUDE", "EVE_CLI_SHELL_ENV_EXCLUDE", "EVE_CLI_SHELL_ENV_SET",
            "EVE_CLI_HOOK_ENV_POLICY", "EVE_CLI_HOOK_ENV_INCLUDE", "EVE_CLI_HOOK_ENV_EXCLUDE", "EVE_CLI_HOOK_ENV_SET",
            "EVE_CLI_NOTIFY_COMMAND", "EVE_CLI_NOTIFY_ON",
            "EVE_CLI_SKILLS_ENABLE", "EVE_CLI_SKILLS_DISABLE",
            "EVE_CODER_SIDECAR", "EVE_CLI_SIDECAR_MODEL",
            "EVE_CODER_MAX_AGENT_STEPS", "EVE_CLI_MAX_AGENT_STEPS",
            "EVE_CLI_PROFILE", "EVE_CODER_DEBUG", "EVE_CLI_DEBUG",
            "EVE_CLI_MARKDOWN_RENDERER",
        ]
        return {k: None for k in keys}

    def _make_env(self, **kwargs):
        """Build a clean env dict with only the specified keys set."""
        env = os.environ.copy()
        for k in self._clean_env():
            env.pop(k, None)
        env.update(kwargs)
        return env

    def test_ollama_host_from_env(self):
        with patch.dict(os.environ, self._make_env(OLLAMA_HOST="http://remote:11434"), clear=True):
            # Restore PATH so subprocesses work
            pass
        env = self._make_env(OLLAMA_HOST="http://remote:11434")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.ollama_host, "http://remote:11434")

    def test_eve_coder_model_legacy(self):
        env = self._make_env(EVE_CODER_MODEL="legacy-model")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.model, "legacy-model")

    def test_ollama_api_key_from_env(self):
        env = self._make_env(OLLAMA_API_KEY="env-secret")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.ollama_api_key, "env-secret")

    def test_eve_cli_ollama_api_key_overrides_env(self):
        env = self._make_env(OLLAMA_API_KEY="env-secret", EVE_CLI_OLLAMA_API_KEY="cli-secret")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.ollama_api_key, "cli-secret")

    def test_pricing_from_env(self):
        env = self._make_env(EVE_CLI_PROMPT_COST_PER_MTOK="0.25", EVE_CLI_COMPLETION_COST_PER_MTOK="0.75")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.prompt_cost_per_mtok, 0.25)
        self.assertEqual(self.cfg.completion_cost_per_mtok, 0.75)

    def test_advanced_runtime_fields_from_env(self):
        env = self._make_env(
            EVE_CLI_PLAN_MODE_REASONING_EFFORT="medium",
            EVE_CLI_SHELL_ENV_POLICY="inherit",
            EVE_CLI_SHELL_ENV_INCLUDE="CI,HTTPS_PROXY",
            EVE_CLI_HOOK_ENV_POLICY="inherit",
            EVE_CLI_NOTIFY_COMMAND="python3 notify.py",
            EVE_CLI_NOTIFY_ON="stop,error",
            EVE_CLI_SKILLS_ENABLE="design*",
            EVE_CLI_SKILLS_DISABLE="bugfix",
        )
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.plan_mode_reasoning_effort, "medium")
        self.assertEqual(self.cfg.shell_env_policy, "inherit")
        self.assertEqual(self.cfg.shell_env_include, ["CI", "HTTPS_PROXY"])
        self.assertEqual(self.cfg.hook_env_policy, "inherit")
        self.assertEqual(self.cfg.notify_command, "python3 notify.py")
        self.assertEqual(self.cfg.notify_on, ["stop", "error"])
        self.assertEqual(self.cfg.skill_enable_patterns, ["design*"])
        self.assertEqual(self.cfg.skill_disable_patterns, ["bugfix"])

    def test_eve_cli_model_overrides_legacy(self):
        env = self._make_env(EVE_CODER_MODEL="legacy-model", EVE_CLI_MODEL="new-model")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.model, "new-model")

    def test_eve_cli_model_alone(self):
        env = self._make_env(EVE_CLI_MODEL="cli-model")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.model, "cli-model")

    def test_sidecar_model_from_env(self):
        env = self._make_env(EVE_CLI_SIDECAR_MODEL="sidecar-v2")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.sidecar_model, "sidecar-v2")

    def test_legacy_sidecar_from_env(self):
        env = self._make_env(EVE_CODER_SIDECAR="old-sidecar")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.sidecar_model, "old-sidecar")

    def test_role_specific_models_from_env(self):
        env = self._make_env(
            EVE_CLI_UTILITY_MODEL="util-v1",
            EVE_CLI_COMPACTION_MODEL="compact-v1",
            EVE_CLI_SUBAGENT_MODEL="sub-v1",
            EVE_CLI_REVIEW_MODEL="review-v1",
            EVE_CLI_RUBBER_DUCK="1",
            EVE_CLI_RUBBER_DUCK_CHECKPOINTS="post-edit",
        )
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.utility_model, "util-v1")
        self.assertEqual(self.cfg.compaction_model, "compact-v1")
        self.assertEqual(self.cfg.subagent_model, "sub-v1")
        self.assertEqual(self.cfg.review_model, "review-v1")
        self.assertTrue(self.cfg.rubber_duck)
        self.assertEqual(self.cfg.rubber_duck_checkpoints, "post-edit")

    def test_max_agent_steps_from_env(self):
        env = self._make_env(EVE_CLI_MAX_AGENT_STEPS="150")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.max_agent_steps, 150)

    def test_max_agent_steps_legacy_env(self):
        env = self._make_env(EVE_CODER_MAX_AGENT_STEPS="80")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.max_agent_steps, 80)

    def test_max_agent_steps_cli_overrides_legacy_env(self):
        env = self._make_env(
            EVE_CODER_MAX_AGENT_STEPS="80",
            EVE_CLI_MAX_AGENT_STEPS="120",
        )
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.max_agent_steps, 120)

    def test_profile_from_env(self):
        env = self._make_env(EVE_CLI_PROFILE="offline")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.profile, "offline")

    def test_debug_from_eve_cli_debug(self):
        env = self._make_env(EVE_CLI_DEBUG="1")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertTrue(self.cfg.debug)

    def test_debug_from_eve_coder_debug(self):
        env = self._make_env(EVE_CODER_DEBUG="1")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertTrue(self.cfg.debug)

    def test_debug_not_set(self):
        env = self._make_env()
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertFalse(self.cfg.debug)

    def test_markdown_renderer_from_env(self):
        env = self._make_env(EVE_CLI_MARKDOWN_RENDERER="simple")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.markdown_renderer, "simple")

    def test_markdown_renderer_invalid_ignored(self):
        env = self._make_env(EVE_CLI_MARKDOWN_RENDERER="fancy")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        # Should remain at default
        self.assertEqual(self.cfg.markdown_renderer, "glow")

    def test_invalid_max_agent_steps_env_ignored(self):
        env = self._make_env(EVE_CLI_MAX_AGENT_STEPS="notanumber")
        with patch.dict(os.environ, env):
            self.cfg._load_env()
        self.assertEqual(self.cfg.max_agent_steps, Config.DEFAULT_MAX_AGENT_STEPS)


class TestLoadCliArgs(unittest.TestCase):
    """Test Config._load_cli_args with various argument combinations."""

    def setUp(self):
        self.cfg = Config()

    def test_prompt_short_flag(self):
        self.cfg._load_cli_args(["-p", "hello world"])
        self.assertEqual(self.cfg.prompt, "hello world")

    def test_prompt_long_flag(self):
        self.cfg._load_cli_args(["--prompt", "test prompt"])
        self.assertEqual(self.cfg.prompt, "test prompt")

    def test_model_flag(self):
        self.cfg._load_cli_args(["-m", "qwen3:8b"])
        self.assertEqual(self.cfg.model, "qwen3:8b")
        self.assertTrue(self.cfg._cli_model_set)

    def test_review_model_flag(self):
        self.cfg._load_cli_args(["--review-model", "gemma4:31b"])
        self.assertEqual(self.cfg.review_model, "gemma4:31b")
        self.assertTrue(self.cfg._cli_review_model_set)

    def test_rubber_duck_flag(self):
        self.cfg._load_cli_args(["--rubber-duck"])
        self.assertTrue(self.cfg.rubber_duck)

    def test_rubber_duck_checkpoints_flag(self):
        self.cfg._load_cli_args(["--rubber-duck-checkpoints", "plan"])
        self.assertEqual(self.cfg.rubber_duck_checkpoints, "plan")

    def test_yes_flag(self):
        self.cfg._load_cli_args(["-y"])
        self.assertTrue(self.cfg.yes_mode)

    def test_dangerously_skip_permissions_flag(self):
        self.cfg._load_cli_args(["--dangerously-skip-permissions"])
        self.assertTrue(self.cfg.yes_mode)

    def test_debug_flag(self):
        self.cfg._load_cli_args(["--debug"])
        self.assertTrue(self.cfg.debug)

    def test_resume_flag(self):
        self.cfg._load_cli_args(["--resume"])
        self.assertTrue(self.cfg.resume)

    def test_session_id_sets_resume(self):
        self.cfg._load_cli_args(["--session-id", "abc123"])
        self.assertEqual(self.cfg.session_id, "abc123")
        self.assertTrue(self.cfg.resume)

    def test_ollama_host_flag(self):
        self.cfg._load_cli_args(["--ollama-host", "http://remote:11434"])
        self.assertEqual(self.cfg.ollama_host, "http://remote:11434")
        self.assertTrue(self.cfg._cli_ollama_host_set)

    def test_max_tokens_flag(self):
        self.cfg._load_cli_args(["--max-tokens", "4096"])
        self.assertEqual(self.cfg.max_tokens, 4096)
        self.assertTrue(self.cfg._cli_max_tokens_set)

    def test_temperature_flag(self):
        self.cfg._load_cli_args(["--temperature", "0.3"])
        self.assertAlmostEqual(self.cfg.temperature, 0.3)
        self.assertTrue(self.cfg._cli_temperature_set)

    def test_context_window_flag(self):
        self.cfg._load_cli_args(["--context-window", "65536"])
        self.assertEqual(self.cfg.context_window, 65536)
        self.assertTrue(self.cfg._cli_context_window_set)

    def test_max_agent_steps_flag(self):
        self.cfg._load_cli_args(["--max-agent-steps", "80"])
        self.assertEqual(self.cfg.max_agent_steps, 80)

    def test_max_agent_steps_capped_at_hard_max(self):
        with patch("builtins.print"):
            self.cfg._load_cli_args(["--max-agent-steps", "500"])
        self.assertEqual(self.cfg.max_agent_steps, Config.HARD_MAX_AGENT_STEPS)

    def test_profile_flag(self):
        self.cfg._load_cli_args(["--profile", "offline"])
        self.assertEqual(self.cfg.profile, "offline")

    def test_loop_flag(self):
        self.cfg._load_cli_args(["--loop"])
        self.assertTrue(self.cfg.loop_mode)

    def test_max_loop_iterations_flag(self):
        self.cfg._load_cli_args(["--max-loop-iterations", "10"])
        self.assertEqual(self.cfg.max_loop_iterations, 10)

    def test_done_string_flag(self):
        self.cfg._load_cli_args(["--done-string", "FINISHED"])
        self.assertEqual(self.cfg.done_string, "FINISHED")

    def test_max_loop_hours_flag(self):
        self.cfg._load_cli_args(["--max-loop-hours", "2.5"])
        self.assertAlmostEqual(self.cfg.max_loop_hours, 2.5)

    def test_max_loop_hours_capped_at_72(self):
        with patch("builtins.print"):
            self.cfg._load_cli_args(["--max-loop-hours", "100"])
        self.assertAlmostEqual(self.cfg.max_loop_hours, 72.0)

    def test_max_loop_hours_negative_exits(self):
        with self.assertRaises(SystemExit):
            self.cfg._load_cli_args(["--max-loop-hours", "-1"])

    def test_output_format_json(self):
        self.cfg._load_cli_args(["--output-format", "json"])
        self.assertEqual(self.cfg.output_format, "json")

    def test_output_format_stream_json(self):
        self.cfg._load_cli_args(["--output-format", "stream-json"])
        self.assertEqual(self.cfg.output_format, "stream-json")

    def test_markdown_renderer_simple(self):
        self.cfg._load_cli_args(["--markdown-renderer", "simple"])
        self.assertEqual(self.cfg.markdown_renderer, "simple")

    def test_rag_flag(self):
        self.cfg._load_cli_args(["--rag"])
        self.assertTrue(self.cfg.rag)

    def test_rag_path_flag(self):
        self.cfg._load_cli_args(["--rag-path", "/tmp/docs"])
        self.assertEqual(self.cfg.rag_path, "/tmp/docs")

    def test_rag_topk_flag(self):
        self.cfg._load_cli_args(["--rag-topk", "10"])
        self.assertEqual(self.cfg.rag_topk, 10)

    def test_rag_model_flag(self):
        self.cfg._load_cli_args(["--rag-model", "mxbai-embed-large"])
        self.assertEqual(self.cfg.rag_model, "mxbai-embed-large")

    def test_learn_flag(self):
        self.cfg._load_cli_args(["--learn"])
        self.assertTrue(self.cfg.learn_mode)

    def test_learn_level_flag(self):
        self.cfg._load_cli_args(["--level", "5"])
        self.assertEqual(self.cfg.learn_level, 5)

    def test_theme_flag(self):
        with patch.object(eve_coder.C, "apply_theme"):
            self.cfg._load_cli_args(["--theme", "gal"])
        self.assertEqual(self.cfg.ui_theme, "gal")

    def test_list_sessions_flag(self):
        self.cfg._load_cli_args(["--list-sessions"])
        self.assertTrue(self.cfg.list_sessions)

    def test_empty_args(self):
        self.cfg._load_cli_args([])
        self.assertIsNone(self.cfg.prompt)
        self.assertFalse(self.cfg.yes_mode)
        self.assertFalse(self.cfg.debug)

    def test_combined_flags(self):
        with patch.object(eve_coder.C, "apply_theme"):
            self.cfg._load_cli_args([
                "-p", "do something",
                "-m", "llama3:latest",
                "-y",
                "--debug",
                "--theme", "dandy",
                "--loop",
                "--max-loop-iterations", "3",
            ])
        self.assertEqual(self.cfg.prompt, "do something")
        self.assertEqual(self.cfg.model, "llama3:latest")
        self.assertTrue(self.cfg.yes_mode)
        self.assertTrue(self.cfg.debug)
        self.assertEqual(self.cfg.ui_theme, "dandy")
        self.assertTrue(self.cfg.loop_mode)
        self.assertEqual(self.cfg.max_loop_iterations, 3)


class TestOllamaHostValidation(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()

    def test_allows_localhost(self):
        self.cfg.ollama_host = "http://localhost:11434"
        self.cfg._validate_ollama_host()
        self.assertEqual(self.cfg.ollama_host, "http://localhost:11434")
        self.assertTrue(self.cfg.uses_local_ollama())

    def test_allows_ollama_cloud_and_strips_api_path(self):
        self.cfg.ollama_host = "https://ollama.com/api"
        self.cfg._validate_ollama_host()
        self.assertEqual(self.cfg.ollama_host, "https://ollama.com")
        self.assertFalse(self.cfg.uses_local_ollama())

    def test_allows_ollama_cloud_and_strips_v1_path(self):
        self.cfg.ollama_host = "https://ollama.com/v1"
        self.cfg._validate_ollama_host()
        self.assertEqual(self.cfg.ollama_host, "https://ollama.com")

    def test_rejects_untrusted_remote_host(self):
        self.cfg.ollama_host = "https://evil.example/api"
        with patch("builtins.print"):
            self.cfg._validate_ollama_host()
        self.assertEqual(self.cfg.ollama_host, Config.DEFAULT_OLLAMA_HOST)


class TestOllamaClientHeaders(unittest.TestCase):
    def test_check_connection_sends_auth_header(self):
        cfg = Config()
        cfg.ollama_host = "https://ollama.com"
        cfg.ollama_api_key = "secret-token"
        client = eve_coder.OllamaClient(cfg)

        fake_resp = MagicMock()
        fake_resp.read.return_value = b'{"models":[]}'

        with patch("urllib.request.urlopen", return_value=fake_resp) as mock_urlopen:
            ok, models = client.check_connection(retries=1)

        self.assertTrue(ok)
        self.assertEqual(models, [])
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer secret-token")

    def test_query_installed_models_sends_auth_header(self):
        cfg = Config()
        cfg.ollama_host = "https://ollama.com/api"
        cfg.ollama_api_key = "secret-token"

        fake_resp = MagicMock()
        fake_resp.read.return_value = b'{"models":[{"name":"glm-5.1:cloud"}]}'

        with patch("urllib.request.urlopen", return_value=fake_resp) as mock_urlopen:
            models = cfg._query_installed_models()

        self.assertEqual(models, ["glm-5.1:cloud"])
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer secret-token")


class TestGemma4CloudAndSampling(unittest.TestCase):
    def test_gemma31b_alias_is_treated_as_cloud(self):
        self.assertTrue(eve_coder._is_cloud_model("gemma4:31b"))
        self.assertTrue(eve_coder._is_cloud_model("gemma4:31b-cloud"))

    def test_glm5_cloud_is_treated_as_cloud(self):
        self.assertTrue(eve_coder._is_cloud_model("glm-5.1:cloud"))

    def test_qwen397_alias_is_treated_as_cloud(self):
        self.assertTrue(eve_coder._is_cloud_model("qwen3.5:397b"))
        self.assertTrue(eve_coder._is_cloud_model("qwen3.5:397b-cloud"))

    def test_glm5_cloud_uses_explicit_context_window(self):
        cfg = Config()
        cfg._apply_context_window("glm-5.1:cloud")
        self.assertEqual(cfg.context_window, 204800)

    def test_gemma_defaults_to_google_temperature(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        opts = client._merge_chat_options("gemma4:31b", 0.7)

        self.assertEqual(opts["temperature"], 1.0)
        self.assertEqual(opts["top_p"], 0.95)
        self.assertEqual(opts["top_k"], 64)

    def test_gemma_preserves_lower_tool_temperature(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        opts = client._merge_chat_options("gemma4:31b", 0.3)

        self.assertEqual(opts["temperature"], 0.3)

    def test_gemma_preserves_explicit_temperature_override(self):
        cfg = Config()
        cfg.temperature = 0.9
        client = eve_coder.OllamaClient(cfg)

        opts = client._merge_chat_options("gemma4:31b", 0.9)

        self.assertEqual(opts["temperature"], 0.9)

    def test_request_temperature_prefers_explicit_option(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        temp = client._resolve_request_temperature(
            "gemma4:31b",
            tools=True,
            options={"temperature": 0.2, "retry_temperature_boost": 0.3},
        )

        self.assertEqual(temp, 0.2)

    def test_gemma_uses_stricter_tool_temperature(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        temp = client._resolve_request_temperature("gemma4:31b", tools=True)

        self.assertEqual(temp, 0.25)

    def test_glm5_uses_stricter_tool_temperature(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        temp = client._resolve_request_temperature("glm-5.1:cloud", tools=True)

        self.assertEqual(temp, 0.25)

    def test_request_temperature_applies_retry_boost_without_mutating_client(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        temp = client._resolve_request_temperature(
            "test-model",
            tools=True,
            options={"retry_temperature_boost": 0.3},
        )

        self.assertEqual(temp, 0.6)
        self.assertEqual(client.temperature, cfg.temperature)

    def test_merge_chat_options_drops_retry_temperature_meta(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)

        opts = client._merge_chat_options(
            "test-model",
            0.6,
            {"retry_temperature_boost": 0.3, "max_tokens": 512},
        )

        self.assertEqual(opts["temperature"], 0.6)
        self.assertEqual(opts["num_predict"], 512)
        self.assertNotIn("retry_temperature_boost", opts)

    def test_build_utility_options_caps_context_and_tokens(self):
        cfg = Config()
        cfg.context_window = 262144
        cfg.max_tokens = 32768
        client = eve_coder.OllamaClient(cfg)

        opts = client.build_utility_options("gemma4:31b", "classifier", 0.2)

        self.assertEqual(opts["num_ctx"], 4096)
        self.assertEqual(opts["num_predict"], 64)
        self.assertEqual(opts["temperature"], 0.2)

    def test_tool_mode_caps_large_model_num_predict(self):
        cfg = Config()
        cfg.context_window = 262144
        cfg.max_tokens = 32768
        client = eve_coder.OllamaClient(cfg)

        opts = client._merge_chat_options("qwen3.5:397b", 0.4, {"tool_mode": True})

        self.assertEqual(opts["num_predict"], 4096)
        self.assertEqual(opts["num_ctx"], 262144)
        self.assertNotIn("tool_mode", opts)

    def test_temporary_reasoning_restores_client_settings(self):
        cfg = Config()
        cfg.think_mode = True
        cfg.thinking_budget = 8000
        client = eve_coder.OllamaClient(cfg)

        with client.temporary_reasoning(False, None):
            self.assertFalse(client.think_mode)
            self.assertIsNone(client.thinking_budget)

        self.assertTrue(client.think_mode)
        self.assertEqual(client.thinking_budget, 8000)

    def test_refresh_from_config_updates_runtime_settings(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)
        cfg.ollama_host = "https://ollama.com"
        cfg.max_tokens = 1234
        cfg.temperature = 0.2
        cfg.context_window = 262144
        cfg.debug = True

        client.refresh_from_config(cfg)

        self.assertEqual(client.base_url, "https://ollama.com")
        self.assertEqual(client.max_tokens, 1234)
        self.assertEqual(client.temperature, 0.2)
        self.assertEqual(client.context_window, 262144)
        self.assertTrue(client.debug)


class TestOllamaThinkingAdapters(unittest.TestCase):
    def test_native_response_preserves_thinking_field(self):
        adapted = eve_coder.OllamaClient._native_to_openai_response({
            "message": {
                "role": "assistant",
                "thinking": "step 1\nstep 2",
                "content": "final answer",
            },
            "prompt_eval_count": 11,
            "eval_count": 5,
        })

        message = adapted["choices"][0]["message"]
        self.assertEqual(message["thinking"], "step 1\nstep 2")
        self.assertEqual(message["content"], "final answer")

    def test_iter_ndjson_preserves_thinking_delta(self):
        cfg = Config()
        client = eve_coder.OllamaClient(cfg)
        payload = (
            b'{"message":{"thinking":"pondering"},"done":false}\n'
            b'{"message":{"content":"answer"},"done":true,"prompt_eval_count":7,"eval_count":3}\n'
        )

        chunks = list(client._iter_ndjson(io.BytesIO(payload)))

        self.assertEqual(chunks[0]["choices"][0]["delta"]["thinking"], "pondering")
        self.assertEqual(chunks[1]["choices"][0]["delta"]["content"], "answer")
        self.assertEqual(chunks[1]["usage"]["prompt_tokens"], 7)
        self.assertEqual(chunks[1]["usage"]["completion_tokens"], 3)


class TestFullWidthSpaceHandling(unittest.TestCase):
    """Test that full-width spaces (\u3000) in CLI args are handled correctly."""

    def setUp(self):
        self.cfg = Config()

    def test_fullwidth_space_in_flag(self):
        """Full-width space between flag and value should be split correctly."""
        self.cfg._load_cli_args(["-m\u3000qwen3:8b"])
        self.assertEqual(self.cfg.model, "qwen3:8b")

    def test_fullwidth_space_in_long_flag(self):
        self.cfg._load_cli_args(["--model\u3000llama3:latest"])
        self.assertEqual(self.cfg.model, "llama3:latest")

    def test_fullwidth_space_trailing_on_flag(self):
        """Trailing full-width space on a boolean flag should be stripped."""
        self.cfg._load_cli_args(["-y\u3000"])
        self.assertTrue(self.cfg.yes_mode)

    def test_mixed_normal_and_fullwidth(self):
        self.cfg._load_cli_args(["-p", "hello", "-m\u3000qwen3:8b"])
        self.assertEqual(self.cfg.prompt, "hello")
        self.assertEqual(self.cfg.model, "qwen3:8b")


class TestLoadConfigFile(unittest.TestCase):
    """Test Config._load_config_file security and backward compatibility."""

    def test_symlink_config_skipped(self):
        """Symlinked config files should be skipped for security."""
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            real_file = os.path.join(tmpdir, "real_config")
            with open(real_file, "w") as f:
                f.write("MODEL = dangerous-model\n")
            link_file = os.path.join(tmpdir, "config")
            os.symlink(real_file, link_file)
            cfg.config_file = link_file
            cfg._old_config_dir = os.path.join(tmpdir, "nonexistent_old")
            cfg._load_config_file()
            # Model should remain at default because symlink was skipped
            self.assertEqual(cfg.model, Config.DEFAULT_MODEL)

    def test_oversized_config_skipped(self):
        """Config files > 64KB should be skipped for security."""
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            big_file = os.path.join(tmpdir, "config")
            with open(big_file, "w") as f:
                f.write("MODEL = should-not-load\n")
                # Write > 64KB of padding
                f.write("#" * 70000 + "\n")
            cfg.config_file = big_file
            cfg._old_config_dir = os.path.join(tmpdir, "nonexistent_old")
            cfg._load_config_file()
            self.assertEqual(cfg.model, Config.DEFAULT_MODEL)

    def test_normal_config_loaded(self):
        """A normal config file should be loaded successfully."""
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "config")
            with open(config_file, "w") as f:
                f.write("MODEL = test-model\n")
            cfg.config_file = config_file
            cfg._old_config_dir = os.path.join(tmpdir, "nonexistent_old")
            cfg._load_config_file()
            self.assertEqual(cfg.model, "test-model")

    def test_old_config_dir_backward_compat(self):
        """Old eve-coder config dir should be checked for backward compat."""
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "eve-coder")
            os.makedirs(old_dir)
            old_config = os.path.join(old_dir, "config")
            with open(old_config, "w") as f:
                f.write("MODEL = old-model\n")
            cfg._old_config_dir = old_dir
            cfg.config_file = os.path.join(tmpdir, "nonexistent_new_config")
            cfg._load_config_file()
            self.assertEqual(cfg.model, "old-model")

    def test_new_config_overrides_old(self):
        """New eve-cli config should override old eve-coder config."""
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "eve-coder")
            os.makedirs(old_dir)
            old_config = os.path.join(old_dir, "config")
            with open(old_config, "w") as f:
                f.write("MODEL = old-model\n")
            new_config = os.path.join(tmpdir, "config")
            with open(new_config, "w") as f:
                f.write("MODEL = new-model\n")
            cfg._old_config_dir = old_dir
            cfg.config_file = new_config
            cfg._load_config_file()
            self.assertEqual(cfg.model, "new-model")

    def test_nonexistent_config_no_error(self):
        """Missing config files should be silently ignored."""
        cfg = Config()
        cfg.config_file = "/nonexistent/path/config"
        cfg._old_config_dir = "/nonexistent/old"
        # Should not raise
        cfg._load_config_file()
        self.assertEqual(cfg.model, Config.DEFAULT_MODEL)

    def test_load_validates_ollama_host_before_auto_detect(self):
        """Config.load must sanitize OLLAMA_HOST before model auto-detection runs."""
        cfg = Config()
        validation_hosts = []
        auto_detect_hosts = []

        def fake_load_env(self):
            self.ollama_host = "http://evil.example:11434"

        def fake_apply_profile(self):
            self.ollama_host = "http://profile-evil.example:11434"

        def fake_validate(self):
            validation_hosts.append(self.ollama_host)
            self.ollama_host = self.DEFAULT_OLLAMA_HOST

        def fake_auto_detect(self):
            auto_detect_hosts.append(self.ollama_host)

        with patch.object(Config, "_load_config_file", autospec=True, return_value=None), \
             patch.object(Config, "_load_env", autospec=True, side_effect=fake_load_env), \
             patch.object(Config, "_load_cli_args", autospec=True, return_value=None), \
             patch.object(Config, "_validate_ollama_host", autospec=True, side_effect=fake_validate), \
             patch.object(Config, "_detect_network", autospec=True, return_value=None), \
             patch.object(Config, "_apply_profile", autospec=True, side_effect=fake_apply_profile), \
             patch.object(Config, "_auto_detect_model", autospec=True, side_effect=fake_auto_detect), \
             patch.object(Config, "_ensure_dirs", autospec=True, return_value=None), \
             patch.object(Config, "load_custom_commands", autospec=True, return_value=None):
            cfg.load([])

        self.assertEqual(
            validation_hosts,
            ["http://evil.example:11434", "http://profile-evil.example:11434"],
        )
        self.assertEqual(auto_detect_hosts, [Config.DEFAULT_OLLAMA_HOST])

    def test_apply_profile_respects_cli_sidecar_override(self):
        cfg = Config()
        cfg.profile = "online"
        cfg.network_status = "online"
        cfg.sidecar_model = "cli-sidecar"
        cfg._cli_sidecar_set = True
        cfg._profiles = {"online": {"SIDECAR_MODEL": "profile-sidecar"}}

        cfg._apply_profile()

        self.assertEqual(cfg.sidecar_model, "cli-sidecar")

    def test_apply_profile_respects_role_specific_overrides(self):
        cfg = Config()
        cfg.profile = "online"
        cfg.network_status = "online"
        cfg.utility_model = "cli-utility"
        cfg.compaction_model = "cli-compaction"
        cfg.subagent_model = "cli-subagent"
        cfg.review_model = "cli-review"
        cfg._cli_utility_model_set = True
        cfg._cli_compaction_model_set = True
        cfg._cli_subagent_model_set = True
        cfg._cli_review_model_set = True
        cfg._profiles = {
            "online": {
                "UTILITY_MODEL": "profile-utility",
                "COMPACTION_MODEL": "profile-compaction",
                "SUBAGENT_MODEL": "profile-subagent",
                "REVIEW_MODEL": "profile-review",
                "RUBBER_DUCK": "true",
                "RUBBER_DUCK_CHECKPOINTS": "post-edit",
            }
        }

        cfg._apply_profile()

        self.assertEqual(cfg.utility_model, "cli-utility")
        self.assertEqual(cfg.compaction_model, "cli-compaction")
        self.assertEqual(cfg.subagent_model, "cli-subagent")
        self.assertEqual(cfg.review_model, "cli-review")
        self.assertTrue(cfg.rubber_duck)
        self.assertEqual(cfg.rubber_duck_checkpoints, "post-edit")


class TestModelRoleResolution(unittest.TestCase):
    def test_utility_model_falls_back_to_sidecar(self):
        cfg = Config()
        cfg.sidecar_model = "gemma4:31b"
        self.assertEqual(eve_coder._resolve_utility_model(cfg), "gemma4:31b")

    def test_compaction_model_prefers_explicit_override(self):
        cfg = Config()
        cfg.sidecar_model = "gemma4:31b"
        cfg.compaction_model = "gemma4:31b-cloud"
        self.assertEqual(eve_coder._resolve_compaction_model(cfg), "gemma4:31b-cloud")

    def test_subagent_model_prefers_specific_then_primary_model(self):
        cfg = Config()
        cfg.model = "glm-5.1:cloud"
        cfg.sidecar_model = "gemma4:31b"
        cfg.utility_model = "qwen3:8b"
        self.assertEqual(eve_coder._resolve_subagent_model(cfg), "glm-5.1:cloud")
        cfg.subagent_model = "qwen3.5:32b"
        self.assertEqual(eve_coder._resolve_subagent_model(cfg), "qwen3.5:32b")

    def test_review_model_prefers_explicit_then_utility(self):
        cfg = Config()
        cfg.sidecar_model = "gemma4:31b"
        cfg.utility_model = "qwen3:8b"
        self.assertEqual(eve_coder._resolve_review_model(cfg), "qwen3:8b")
        cfg.review_model = "gemma4:31b-cloud"
        self.assertEqual(eve_coder._resolve_review_model(cfg), "gemma4:31b-cloud")


if __name__ == "__main__":
    unittest.main()
