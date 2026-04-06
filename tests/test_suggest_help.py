"""
Regression tests for /suggest-help sidecar calls and chat options overrides.
"""

import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import contextlib
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class _FakeHTTPResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self, _limit=None):
        return self._payload

    def close(self):
        pass


class _CaptureSuggestHelpClient:
    def __init__(self):
        self.last_kwargs = None

    def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return {"choices": [{"message": {"content": '["foo", "bar"]'}}]}


class _EmptySuggestHelpClient:
    def chat(self, **kwargs):
        return {"choices": [{"message": {"content": ""}}]}


class _UtilitySuggestHelpClient:
    def __init__(self):
        self.last_kwargs = None
        self.reasoning_states = []

    def build_utility_options(self, model, profile, temperature):
        return {
            "temperature": temperature,
            "num_ctx": 8192,
            "num_predict": 512,
            "profile": profile,
            "model": model,
        }

    @contextlib.contextmanager
    def temporary_reasoning(self, think_mode, thinking_budget=None):
        self.reasoning_states.append((think_mode, thinking_budget))
        yield

    def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return {"choices": [{"message": {"content": '["foo", "bar"]'}}]}


class TestSuggestHelp(unittest.TestCase):
    def make_config(self):
        config = eve_coder.Config()
        config.ollama_host = "http://example.invalid"
        config.max_tokens = 2048
        config.temperature = 0.2
        config.context_window = 8192
        config.debug = False
        return config

    def test_chat_accepts_per_call_options(self):
        config = self.make_config()
        client = eve_coder.OllamaClient(config)
        seen = {}

        def fake_urlopen(req, timeout):
            seen["timeout"] = timeout
            seen["body"] = json.loads(req.data.decode("utf-8"))
            payload = json.dumps({"message": {"role": "assistant", "content": '["ok"]'}}).encode("utf-8")
            return _FakeHTTPResponse(payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            response = client.chat(
                model="sidecar-model",
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                options={"temperature": 0.7, "max_tokens": 512},
            )

        self.assertEqual(response["choices"][0]["message"]["content"], '["ok"]')
        self.assertEqual(seen["body"]["options"]["temperature"], 0.7)
        self.assertEqual(seen["body"]["options"]["num_predict"], 512)
        self.assertEqual(seen["body"]["options"]["num_ctx"], 8192)

    def test_call_sidecar_for_suggestions_uses_options(self):
        client = _CaptureSuggestHelpClient()
        config = SimpleNamespace(sidecar_model="qwen3:8b")

        suggestions = eve_coder._call_sidecar_for_suggestions(
            agent=None,
            config=config,
            client=client,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(suggestions, ["foo", "bar"])
        self.assertEqual(client.last_kwargs["options"]["temperature"], 0.7)
        self.assertEqual(client.last_kwargs["options"]["max_tokens"], 512)

    def test_call_sidecar_for_suggestions_prefers_utility_options_when_available(self):
        client = _UtilitySuggestHelpClient()
        config = SimpleNamespace(sidecar_model="gemma4:31b")

        suggestions = eve_coder._call_sidecar_for_suggestions(
            agent=None,
            config=config,
            client=client,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(suggestions, ["foo", "bar"])
        self.assertEqual(client.reasoning_states, [(False, None)])
        self.assertEqual(client.last_kwargs["options"]["profile"], "suggestions")
        self.assertEqual(client.last_kwargs["options"]["num_ctx"], 8192)
        self.assertEqual(client.last_kwargs["options"]["num_predict"], 512)

    def test_parse_suggest_help_response_reports_empty_output_clearly(self):
        with self.assertRaises(RuntimeError) as cm:
            eve_coder._parse_suggest_help_response("")
        self.assertIn("空の応答", str(cm.exception))

    def test_handle_suggest_help_falls_back_to_generic_suggestions(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        config = SimpleNamespace(cwd=temp_dir, sidecar_model="qwen3:8b")
        agent = SimpleNamespace(last_error=None)
        session = SimpleNamespace(messages=[])
        stdout = io.StringIO()

        with patch("subprocess.run", return_value=SimpleNamespace(stdout="")), \
             patch("builtins.input", return_value="1"), \
             patch("sys.stdout", stdout):
            selected = eve_coder._handle_suggest_help(
                agent=agent,
                config=config,
                client=_EmptySuggestHelpClient(),
                session=session,
            )

        output = stdout.getvalue()
        self.assertTrue(selected)
        self.assertIn("一般的な候補を表示します", output)
        self.assertIn("起動直後", output)


if __name__ == "__main__":
    unittest.main()
