#!/usr/bin/env python3
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
import urllib.parse
from unittest import mock


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(ROOT_DIR, "eve-coder.py")

spec = importlib.util.spec_from_file_location("eve_coder", MODULE_PATH)
eve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve)


class TestConfigBehavior(unittest.TestCase):
    def test_parse_config_file_reads_supported_values(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "# comment\n"
                    "MODEL=qwen3:8b\n"
                    "SIDECAR_MODEL=qwen3:4b\n"
                    "OLLAMA_HOST=http://localhost:11435/\n"
                    "MAX_TOKENS=4096\n"
                    "TEMPERATURE=0.25\n"
                    "CONTEXT_WINDOW=65536\n"
                )
            config = eve.Config()
            config._parse_config_file(path)
            self.assertEqual(config.model, "qwen3:8b")
            self.assertEqual(config.sidecar_model, "qwen3:4b")
            self.assertEqual(config.ollama_host, "http://localhost:11435/")
            self.assertEqual(config.max_tokens, 4096)
            self.assertEqual(config.temperature, 0.25)
            self.assertEqual(config.context_window, 65536)
        finally:
            os.unlink(path)

    def test_load_cli_args_handles_full_width_spaces(self):
        config = eve.Config()
        config._load_cli_args(["--model　qwen3:8b", "-y　", "--rag-topk", "7"])
        self.assertEqual(config.model, "qwen3:8b")
        self.assertTrue(config.yes_mode)
        self.assertEqual(config.rag_topk, 7)

    def test_pick_best_model_prefers_highest_supported_tier(self):
        config = eve.Config()
        installed = ["qwen3:1.7b", "qwen3:8b", "qwen3-coder:30b"]
        self.assertEqual(config._pick_best_model(installed, 32), "qwen3-coder:30b")

    def test_pick_sidecar_avoids_main_model(self):
        config = eve.Config()
        config._pick_sidecar(["qwen3:8b", "qwen3:4b"], "qwen3:8b", 16)
        self.assertEqual(config.sidecar_model, "qwen3:4b")

    def test_validate_ollama_host_sanitizes_values(self):
        config = eve.Config()
        config.ollama_host = "http://user:pass@localhost:11434/"
        config.context_window = -5
        config.max_tokens = 999999999
        config.temperature = 3
        config.model = "bad;model"
        config.sidecar_model = "bad model"
        config._validate_ollama_host()
        self.assertEqual(config.ollama_host, "http://localhost:11434")
        self.assertEqual(config.context_window, config.DEFAULT_CONTEXT_WINDOW)
        self.assertEqual(config.max_tokens, config.DEFAULT_MAX_TOKENS)
        self.assertEqual(config.temperature, config.DEFAULT_TEMPERATURE)
        self.assertEqual(config.model, config.DEFAULT_MODEL)
        self.assertEqual(config.sidecar_model, "")

    def test_validate_ollama_host_rejects_non_localhost(self):
        config = eve.Config()
        config.ollama_host = "https://example.com:443"
        config._validate_ollama_host()
        self.assertEqual(config.ollama_host, config.DEFAULT_OLLAMA_HOST)


class TestImageHelpers(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_extract_image_paths_handles_file_urls(self):
        image_path = os.path.join(self.tmpdir, "sample image.png")
        with open(image_path, "wb") as handle:
            handle.write(b"\x89PNG\r\n\x1a\nfake")
        encoded_path = "file://" + urllib.parse.quote(image_path)
        cleaned_text, image_paths = eve._extract_image_paths(
            'please inspect "{0}" now'.format(encoded_path)
        )
        self.assertEqual(cleaned_text, "please inspect now")
        self.assertEqual(image_paths, [image_path])

    def test_read_image_as_base64_accepts_existing_image_extension(self):
        image_path = os.path.join(self.tmpdir, "sample.png")
        with open(image_path, "wb") as handle:
            handle.write(b"png-bytes")
        result, error = eve._read_image_as_base64(image_path)
        self.assertIsNone(error)
        self.assertEqual(result[1], "image/png")
        self.assertTrue(result[0])

    def test_read_image_as_base64_rejects_empty_file(self):
        image_path = os.path.join(self.tmpdir, "empty.png")
        open(image_path, "wb").close()
        result, error = eve._read_image_as_base64(image_path)
        self.assertIsNone(result)
        self.assertIn("empty", error.lower())

    def test_build_multimodal_content_handles_text_and_images(self):
        text_only = eve._build_multimodal_content("hello", [])
        mixed = eve._build_multimodal_content("hello", [("YWJj", "image/png")])
        self.assertEqual(text_only, "hello")
        self.assertEqual(mixed[0], {"type": "text", "text": "hello"})
        self.assertEqual(mixed[1]["image_url"]["url"], "data:image/png;base64,YWJj")


class TestProtectedPathAndSkills(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_is_protected_path_blocks_config_dir_and_permissions_file(self):
        protected_dir = os.path.join(self.tmpdir, ".config", "eve-cli")
        os.makedirs(protected_dir)
        protected_file = os.path.join(protected_dir, "config")
        permissions_file = os.path.join(self.tmpdir, "permissions.json")
        safe_file = os.path.join(self.tmpdir, "project", "main.py")
        os.makedirs(os.path.dirname(safe_file))

        with mock.patch.object(eve.os.path, "expanduser", return_value=self.tmpdir):
            self.assertTrue(eve._is_protected_path(protected_file))
            self.assertTrue(eve._is_protected_path(permissions_file))
            self.assertFalse(eve._is_protected_path(safe_file))

    def test_load_skills_reads_standard_locations_and_skips_invalid_entries(self):
        config = eve.Config()
        config.config_dir = os.path.join(self.tmpdir, "config-home")
        config.cwd = os.path.join(self.tmpdir, "workspace")
        os.makedirs(os.path.join(config.config_dir, "skills"))
        os.makedirs(os.path.join(config.cwd, ".eve-cli", "skills"))
        os.makedirs(os.path.join(config.cwd, "skills"))

        with open(os.path.join(config.config_dir, "skills", "global.md"), "w", encoding="utf-8") as handle:
            handle.write("global skill")
        with open(os.path.join(config.cwd, ".eve-cli", "skills", "team.md"), "w", encoding="utf-8") as handle:
            handle.write("team skill")
        with open(os.path.join(config.cwd, "skills", "repo.md"), "w", encoding="utf-8") as handle:
            handle.write("repo skill")
        with open(os.path.join(config.cwd, "skills", "oversized.md"), "w", encoding="utf-8") as handle:
            handle.write("x" * 50001)

        source = os.path.join(config.cwd, "skills", "repo.md")
        symlink = os.path.join(config.cwd, "skills", "link.md")
        if hasattr(os, "symlink"):
            os.symlink(source, symlink)

        skills = eve._load_skills(config)
        self.assertEqual(skills["global"], "global skill")
        self.assertEqual(skills["team"], "team skill")
        self.assertEqual(skills["repo"], "repo skill")
        self.assertNotIn("oversized", skills)
        self.assertNotIn("link", skills)


class TestToolCallParsing(unittest.TestCase):
    def test_try_parse_json_value_converts_json_literals(self):
        self.assertIs(eve._try_parse_json_value("true"), True)
        self.assertEqual(eve._try_parse_json_value("12"), 12)
        self.assertEqual(eve._try_parse_json_value('{"a": 1}'), {"a": 1})
        self.assertEqual(eve._try_parse_json_value("plain"), "plain")

    def test_extract_tool_calls_parses_xml_and_decodes_entities(self):
        text = (
            'Before <function_calls><invoke name="Bash">'
            '<parameter name="command">echo &quot;hi&quot;</parameter>'
            '<parameter name="options">{"dry_run": true}</parameter>'
            "</invoke></function_calls> After"
        )
        calls, cleaned = eve._extract_tool_calls_from_text(text, {"Bash"})
        self.assertEqual(len(calls), 1)
        payload = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(payload["command"], 'echo "hi"')
        self.assertEqual(payload["options"], {"dry_run": True})
        self.assertIn("Before", cleaned)
        self.assertIn("After", cleaned)
        self.assertNotIn("function_calls", cleaned)

    def test_extract_tool_calls_ignores_code_blocks_and_deduplicates(self):
        text = (
            "```xml\n<invoke name=\"Bash\"><parameter name=\"command\">ignored</parameter></invoke>\n```\n"
            "<Bash><command>ls</command></Bash>\n"
            "<Bash><command>ls</command></Bash>"
        )
        calls, cleaned = eve._extract_tool_calls_from_text(text, {"Bash"})
        self.assertEqual(len(calls), 1)
        payload = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(payload, {"command": "ls"})
        self.assertNotIn("<Bash>", cleaned)
        self.assertIn("```xml", cleaned)


class TestSessionHelpers(unittest.TestCase):
    def test_estimate_tokens_counts_ascii_and_cjk(self):
        self.assertEqual(eve.Session._estimate_tokens("abcd"), 1)
        self.assertEqual(eve.Session._estimate_tokens("日本語"), 3)

    def test_parse_image_marker_accepts_valid_json(self):
        marker = json.dumps({"type": "image", "media_type": "image/png", "data": "abc"})
        self.assertEqual(eve.Session._parse_image_marker(marker), ("image/png", "abc"))
        self.assertIsNone(eve.Session._parse_image_marker("not-json"))

    def test_cwd_hash_uses_absolute_path(self):
        config = eve.Config()
        config.cwd = "."
        self.assertEqual(len(eve.Session._cwd_hash(config)), 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
