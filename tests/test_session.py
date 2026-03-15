"""
Test suite for Session class: message management, token estimation,
session ID sanitization, max messages enforcement, tool pairing validation,
image marker parsing, and cwd hashing.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

Session = eve_coder.Session
ToolResult = eve_coder.ToolResult


def _make_config(tmpdir, session_id=None, context_window=32768):
    """Create a mock Config for Session tests."""
    sessions_dir = os.path.join(tmpdir, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    return SimpleNamespace(
        context_window=context_window,
        session_id=session_id,
        sessions_dir=sessions_dir,
        cwd=tmpdir,
        sidecar_model="",
    )


class TestSessionInit(unittest.TestCase):
    """Tests for Session initialization."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_empty_state(self):
        cfg = _make_config(self.tmpdir)
        sess = Session(cfg, "You are a helpful assistant.")
        self.assertEqual(sess.messages, [])
        self.assertEqual(sess.system_prompt, "You are a helpful assistant.")

    def test_session_id_generated_when_none(self):
        cfg = _make_config(self.tmpdir, session_id=None)
        sess = Session(cfg, "prompt")
        self.assertTrue(len(sess.session_id) > 0)
        # Must only contain safe characters
        import re
        self.assertRegex(sess.session_id, r'^[A-Za-z0-9_\-]+$')

    def test_session_id_from_config(self):
        cfg = _make_config(self.tmpdir, session_id="my_session_123")
        sess = Session(cfg, "prompt")
        self.assertEqual(sess.session_id, "my_session_123")

    def test_session_id_sanitization_strips_special_chars(self):
        cfg = _make_config(self.tmpdir, session_id="../../etc/passwd")
        sess = Session(cfg, "prompt")
        # Path traversal characters should be stripped
        self.assertNotIn("/", sess.session_id)
        self.assertNotIn(".", sess.session_id)

    def test_session_id_max_length(self):
        cfg = _make_config(self.tmpdir, session_id="a" * 100)
        sess = Session(cfg, "prompt")
        self.assertLessEqual(len(sess.session_id), 64)

    def test_session_id_empty_after_sanitization_gets_fallback(self):
        cfg = _make_config(self.tmpdir, session_id="///...")
        sess = Session(cfg, "prompt")
        self.assertTrue(len(sess.session_id) > 0)
        import re
        self.assertRegex(sess.session_id, r'^[A-Za-z0-9_\-]+$')


class TestSessionMessages(unittest.TestCase):
    """Tests for add_user_message, add_assistant_message, and get_messages."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "System prompt here.")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_user_message(self):
        self.sess.add_user_message("Hello")
        self.assertEqual(len(self.sess.messages), 1)
        self.assertEqual(self.sess.messages[0]["role"], "user")
        self.assertEqual(self.sess.messages[0]["content"], "Hello")

    def test_add_assistant_message(self):
        self.sess.add_assistant_message("Hi there")
        self.assertEqual(len(self.sess.messages), 1)
        self.assertEqual(self.sess.messages[0]["role"], "assistant")
        self.assertEqual(self.sess.messages[0]["content"], "Hi there")

    def test_add_assistant_message_with_tool_calls(self):
        tool_calls = [{"id": "call_1", "function": {"name": "Bash", "arguments": "{}"}}]
        self.sess.add_assistant_message("", tool_calls=tool_calls)
        msg = self.sess.messages[0]
        self.assertEqual(msg["role"], "assistant")
        self.assertEqual(msg["tool_calls"], tool_calls)

    def test_add_assistant_message_without_tool_calls(self):
        self.sess.add_assistant_message("Just text")
        msg = self.sess.messages[0]
        self.assertNotIn("tool_calls", msg)

    def test_get_messages_includes_system_prompt(self):
        self.sess.add_user_message("Hi")
        messages = self.sess.get_messages()
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "System prompt here.")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Hi")

    def test_get_messages_empty_session(self):
        messages = self.sess.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")

    def test_message_order_preserved(self):
        self.sess.add_user_message("User 1")
        self.sess.add_assistant_message("Asst 1")
        self.sess.add_user_message("User 2")
        messages = self.sess.get_messages()
        self.assertEqual(len(messages), 4)  # system + 3
        self.assertEqual(messages[1]["content"], "User 1")
        self.assertEqual(messages[2]["content"], "Asst 1")
        self.assertEqual(messages[3]["content"], "User 2")


class TestSessionTokenEstimation(unittest.TestCase):
    """Tests for _estimate_tokens and get_token_estimate."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "short prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_estimate_tokens_empty(self):
        self.assertEqual(Session._estimate_tokens(""), 0)

    def test_estimate_tokens_none(self):
        self.assertEqual(Session._estimate_tokens(None), 0)

    def test_estimate_tokens_ascii(self):
        # "hello world" is 11 chars -> 11 / 4 = 2 (integer division)
        result = Session._estimate_tokens("hello world")
        self.assertEqual(result, 11 // 4)

    def test_estimate_tokens_cjk_japanese(self):
        # Each CJK character counts as 1 token
        text = "日本語テスト"  # 6 chars, all CJK (kanji + katakana)
        result = Session._estimate_tokens(text)
        self.assertEqual(result, 6)

    def test_estimate_tokens_cjk_korean(self):
        text = "한국어"  # 3 Korean chars
        result = Session._estimate_tokens(text)
        self.assertEqual(result, 3)

    def test_estimate_tokens_mixed(self):
        # "Hello日本" -> 5 ASCII chars + 2 CJK chars = 5//4 + 2 = 1 + 2 = 3
        text = "Hello日本"
        result = Session._estimate_tokens(text)
        cjk = 2
        non_cjk = 5
        expected = cjk + non_cjk // 4
        self.assertEqual(result, expected)

    def test_get_token_estimate_includes_system_prompt(self):
        estimate = self.sess.get_token_estimate()
        # Should at least include the system prompt tokens
        sys_tokens = Session._estimate_tokens("short prompt")
        self.assertGreaterEqual(estimate, sys_tokens)

    def test_get_token_estimate_increases_with_messages(self):
        before = self.sess.get_token_estimate()
        self.sess.add_user_message("This is a test message with some content")
        after = self.sess.get_token_estimate()
        self.assertGreater(after, before)

    def test_get_token_estimate_includes_tool_calls(self):
        before = self.sess.get_token_estimate()
        tool_calls = [{"id": "tc1", "function": {"name": "Bash", "arguments": '{"command": "ls -la"}'}}]
        self.sess.add_assistant_message("", tool_calls=tool_calls)
        after = self.sess.get_token_estimate()
        self.assertGreater(after, before)


class TestSessionEnforceMaxMessages(unittest.TestCase):
    """Tests for _enforce_max_messages."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_trimming_under_limit(self):
        for i in range(10):
            self.sess.add_user_message(f"msg {i}")
        self.assertEqual(len(self.sess.messages), 10)

    def test_trimming_at_limit(self):
        # Add more than MAX_MESSAGES
        for i in range(Session.MAX_MESSAGES + 50):
            self.sess.messages.append({"role": "user", "content": f"msg {i}"})
        self.sess._enforce_max_messages()
        self.assertLessEqual(len(self.sess.messages), Session.MAX_MESSAGES)

    def test_preserves_tool_pairings(self):
        """Messages should not be cut in the middle of a tool result sequence."""
        # Create a large message history with tool call/result pairs at the boundary
        for i in range(Session.MAX_MESSAGES - 5):
            self.sess.messages.append({"role": "user", "content": f"msg {i}"})
        # Add tool call + results near the cut point
        self.sess.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "tc1"}, {"id": "tc2"}],
        })
        self.sess.messages.append({"role": "tool", "tool_call_id": "tc1", "content": "result1"})
        self.sess.messages.append({"role": "tool", "tool_call_id": "tc2", "content": "result2"})
        self.sess.messages.append({"role": "user", "content": "follow up"})
        self.sess.messages.append({"role": "assistant", "content": "response"})
        # Trigger enforcement
        self.sess._enforce_max_messages()
        # The resulting list should not start with orphaned tool results
        if self.sess.messages:
            self.assertNotEqual(self.sess.messages[0].get("role"), "tool")

    def test_never_erases_all(self):
        """Even aggressive trimming should not leave messages empty."""
        for i in range(Session.MAX_MESSAGES + 100):
            self.sess.messages.append({"role": "user", "content": f"msg {i}"})
        self.sess._enforce_max_messages()
        self.assertGreater(len(self.sess.messages), 0)


class TestSessionRecalculateTokens(unittest.TestCase):
    """Tests for _recalculate_tokens."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_recalculate_matches_estimate(self):
        self.sess.add_user_message("Hello world")
        self.sess.add_assistant_message("Hi there")
        expected = self.sess._token_estimate
        self.sess._recalculate_tokens()
        self.assertEqual(self.sess._token_estimate, expected)

    def test_recalculate_from_zero(self):
        self.sess.messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"},
        ]
        self.sess._token_estimate = 0
        self.sess._recalculate_tokens()
        self.assertGreater(self.sess._token_estimate, 0)


class TestSessionValidateMessageOrder(unittest.TestCase):
    """Tests for validate_message_order."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_simple_conversation(self):
        self.sess.messages = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        valid, err = self.sess.validate_message_order()
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_with_tool_calls(self):
        self.sess.messages = [
            {"role": "user", "content": "read file"},
            {"role": "assistant", "content": None,
             "tool_calls": [{"id": "tc1", "function": {"name": "Read", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "tc1", "content": "file content"},
            {"role": "assistant", "content": "Here is the file."},
        ]
        valid, err = self.sess.validate_message_order()
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_invalid_missing_tool_result(self):
        self.sess.messages = [
            {"role": "user", "content": "read file"},
            {"role": "assistant", "content": None,
             "tool_calls": [{"id": "tc1", "function": {"name": "Read", "arguments": "{}"}}]},
            {"role": "user", "content": "another message"},  # missing tool result
        ]
        valid, err = self.sess.validate_message_order()
        self.assertFalse(valid)
        self.assertIsNotNone(err)

    def test_valid_multiple_tool_calls(self):
        self.sess.messages = [
            {"role": "user", "content": "do things"},
            {"role": "assistant", "content": None,
             "tool_calls": [
                 {"id": "tc1", "function": {"name": "Read", "arguments": "{}"}},
                 {"id": "tc2", "function": {"name": "Glob", "arguments": "{}"}},
             ]},
            {"role": "tool", "tool_call_id": "tc1", "content": "result1"},
            {"role": "tool", "tool_call_id": "tc2", "content": "result2"},
            {"role": "assistant", "content": "Done."},
        ]
        valid, err = self.sess.validate_message_order()
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_empty_messages(self):
        valid, err = self.sess.validate_message_order()
        self.assertTrue(valid)
        self.assertIsNone(err)


class TestSessionCwdHash(unittest.TestCase):
    """Tests for _cwd_hash."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_deterministic(self):
        cfg = _make_config(self.tmpdir)
        h1 = Session._cwd_hash(cfg)
        h2 = Session._cwd_hash(cfg)
        self.assertEqual(h1, h2)

    def test_different_dirs_different_hash(self):
        tmpdir2 = tempfile.mkdtemp()
        try:
            cfg1 = _make_config(self.tmpdir)
            cfg2 = _make_config(tmpdir2)
            self.assertNotEqual(Session._cwd_hash(cfg1), Session._cwd_hash(cfg2))
        finally:
            shutil.rmtree(tmpdir2, ignore_errors=True)

    def test_hash_length(self):
        cfg = _make_config(self.tmpdir)
        h = Session._cwd_hash(cfg)
        self.assertEqual(len(h), 16)


class TestSessionParseImageMarker(unittest.TestCase):
    """Tests for _parse_image_marker."""

    def test_valid_image_marker(self):
        marker = json.dumps({
            "type": "image",
            "media_type": "image/png",
            "data": "iVBORw0KGgo=",
        })
        result = Session._parse_image_marker(marker)
        self.assertIsNotNone(result)
        media_type, data = result
        self.assertEqual(media_type, "image/png")
        self.assertEqual(data, "iVBORw0KGgo=")

    def test_non_image_json(self):
        marker = json.dumps({"type": "text", "content": "hello"})
        result = Session._parse_image_marker(marker)
        self.assertIsNone(result)

    def test_non_json_string(self):
        result = Session._parse_image_marker("just plain text")
        self.assertIsNone(result)

    def test_empty_string(self):
        result = Session._parse_image_marker("")
        self.assertIsNone(result)

    def test_none_input(self):
        result = Session._parse_image_marker(None)
        self.assertIsNone(result)

    def test_missing_data_field(self):
        marker = json.dumps({"type": "image", "media_type": "image/png"})
        result = Session._parse_image_marker(marker)
        self.assertIsNone(result)

    def test_missing_media_type_field(self):
        marker = json.dumps({"type": "image", "data": "abc123"})
        result = Session._parse_image_marker(marker)
        self.assertIsNone(result)


class TestSessionAddToolResults(unittest.TestCase):
    """Tests for add_tool_results."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_basic_tool_result(self):
        results = [ToolResult("tc1", "output text")]
        self.sess.add_tool_results(results)
        self.assertEqual(len(self.sess.messages), 1)
        msg = self.sess.messages[0]
        self.assertEqual(msg["role"], "tool")
        self.assertEqual(msg["tool_call_id"], "tc1")
        self.assertEqual(msg["content"], "output text")

    def test_multiple_tool_results(self):
        results = [
            ToolResult("tc1", "result1"),
            ToolResult("tc2", "result2"),
        ]
        self.sess.add_tool_results(results)
        self.assertEqual(len(self.sess.messages), 2)

    def test_none_output_becomes_empty_string(self):
        results = [ToolResult("tc1", None)]
        self.sess.add_tool_results(results)
        self.assertEqual(self.sess.messages[0]["content"], "")

    def test_image_tool_result(self):
        """Image results should produce both a tool message and a user image message."""
        image_marker = json.dumps({
            "type": "image",
            "media_type": "image/png",
            "data": "iVBORw0KGgo=",
        })
        results = [ToolResult("tc1", image_marker)]
        self.sess.add_tool_results(results)
        # Should have 2 messages: tool result + user image message
        self.assertEqual(len(self.sess.messages), 2)
        self.assertEqual(self.sess.messages[0]["role"], "tool")
        self.assertEqual(self.sess.messages[1]["role"], "user")
        # User message should have multipart content
        content = self.sess.messages[1]["content"]
        self.assertIsInstance(content, list)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]["type"], "text")
        self.assertEqual(content[1]["type"], "image_url")


class TestSessionMaxMessagesEnforcement(unittest.TestCase):
    """Tests that MAX_MESSAGES is enforced via add_user_message."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cfg = _make_config(self.tmpdir)
        self.sess = Session(cfg, "prompt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_max_messages_constant(self):
        self.assertEqual(Session.MAX_MESSAGES, 500)

    def test_enforcement_via_add_user_message(self):
        # Pre-fill messages just under the limit, then add more
        for i in range(Session.MAX_MESSAGES + 10):
            self.sess.messages.append({"role": "user", "content": f"m{i}"})
        # Trigger enforcement
        self.sess.add_user_message("trigger trim")
        self.assertLessEqual(len(self.sess.messages), Session.MAX_MESSAGES + 1)


if __name__ == "__main__":
    unittest.main()
