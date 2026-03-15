"""
Test suite for _extract_tool_calls_from_text and _try_parse_json_value.
"""

import unittest
import json
import sys
import os

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# Import eve-coder.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)
_extract_tool_calls_from_text = eve_coder._extract_tool_calls_from_text
_try_parse_json_value = eve_coder._try_parse_json_value


class TestTryParseJsonValue(unittest.TestCase):
    """Tests for _try_parse_json_value helper."""

    def test_true(self):
        """'true' should parse to Python True."""
        self.assertIs(_try_parse_json_value("true"), True)

    def test_false(self):
        """'false' should parse to Python False."""
        self.assertIs(_try_parse_json_value("false"), False)

    def test_null(self):
        """'null' should parse to Python None."""
        self.assertIsNone(_try_parse_json_value("null"))

    def test_integer(self):
        """'42' should parse to int 42."""
        self.assertEqual(_try_parse_json_value("42"), 42)

    def test_negative_integer(self):
        """'-7' should parse to int -7."""
        self.assertEqual(_try_parse_json_value("-7"), -7)

    def test_float(self):
        """'3.14' should parse to float 3.14."""
        self.assertAlmostEqual(_try_parse_json_value("3.14"), 3.14)

    def test_array(self):
        """JSON array string should parse to Python list."""
        result = _try_parse_json_value('["a", "b"]')
        self.assertEqual(result, ["a", "b"])

    def test_object(self):
        """JSON object string should parse to Python dict."""
        result = _try_parse_json_value('{"key": "val"}')
        self.assertEqual(result, {"key": "val"})

    def test_plain_string(self):
        """Plain string should be returned unchanged."""
        self.assertEqual(_try_parse_json_value("hello"), "hello")

    def test_empty_string(self):
        """Empty string should be returned unchanged."""
        self.assertEqual(_try_parse_json_value(""), "")

    def test_string_with_spaces(self):
        """String with spaces that is not JSON should be returned unchanged."""
        self.assertEqual(_try_parse_json_value("hello world"), "hello world")

    def test_zero(self):
        """'0' should parse to int 0."""
        self.assertEqual(_try_parse_json_value("0"), 0)


class TestExtractToolCallsPlainText(unittest.TestCase):
    """Tests for _extract_tool_calls_from_text with non-tool text."""

    def test_no_tool_calls_in_plain_text(self):
        """Plain text without XML should return no tool calls."""
        calls, cleaned = _extract_tool_calls_from_text("Hello, this is normal text.")
        self.assertEqual(calls, [])
        self.assertEqual(cleaned, "Hello, this is normal text.")

    def test_empty_text(self):
        """Empty text should return no tool calls."""
        calls, cleaned = _extract_tool_calls_from_text("")
        self.assertEqual(calls, [])
        self.assertEqual(cleaned, "")

    def test_quick_bail_out_no_closing_tags(self):
        """Text without '</' should bail out quickly."""
        calls, cleaned = _extract_tool_calls_from_text("Some <open> tag but no closing tag")
        self.assertEqual(calls, [])

    def test_no_tool_calls_in_code_blocks(self):
        """Tool call XML inside code blocks should NOT be extracted."""
        text = '```xml\n<invoke name="Bash"><parameter name="command">ls</parameter></invoke>\n```'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(calls, [])


class TestExtractToolCallsPattern1(unittest.TestCase):
    """Tests for Pattern 1: <invoke name="ToolName"> format."""

    def test_basic_invoke(self):
        """Basic invoke pattern should be parsed correctly."""
        text = '<invoke name="Bash"><parameter name="command">ls -la</parameter></invoke>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "Bash")
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["command"], "ls -la")

    def test_invoke_multiple_params(self):
        """Invoke with multiple parameters."""
        text = '<invoke name="Edit"><parameter name="file">test.py</parameter><parameter name="content">hello</parameter></invoke>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["file"], "test.py")
        self.assertEqual(args["content"], "hello")

    def test_invoke_id_format(self):
        """Tool call ID should start with 'call_' and be a hex string."""
        text = '<invoke name="Bash"><parameter name="command">pwd</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        self.assertTrue(calls[0]["id"].startswith("call_"))
        # uuid4.hex is 32 hex chars
        hex_part = calls[0]["id"][5:]
        self.assertEqual(len(hex_part), 32)

    def test_invoke_type_is_function(self):
        """Tool call type should be 'function'."""
        text = '<invoke name="Bash"><parameter name="command">pwd</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        self.assertEqual(calls[0]["type"], "function")


class TestExtractToolCallsPattern2(unittest.TestCase):
    """Tests for Pattern 2: Qwen <function=ToolName> format."""

    def test_qwen_basic(self):
        """Basic Qwen function format should be parsed."""
        text = '<function=Bash><parameter=command>echo hello</parameter></function>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "Bash")
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["command"], "echo hello")

    def test_qwen_multiple_params(self):
        """Qwen format with multiple parameters."""
        text = '<function=Write><parameter=path>out.txt</parameter><parameter=content>data</parameter></function>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["path"], "out.txt")
        self.assertEqual(args["content"], "data")


class TestExtractToolCallsPattern3(unittest.TestCase):
    """Tests for Pattern 3: <ToolName> simple XML format (requires known_tools)."""

    def test_simple_xml_with_known_tools(self):
        """Simple XML format should work when tool is in known_tools."""
        text = '<Bash><command>ls</command></Bash>'
        known = {"Bash", "Read", "Write"}
        calls, cleaned = _extract_tool_calls_from_text(text, known_tools=known)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "Bash")
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["command"], "ls")

    def test_simple_xml_without_known_tools(self):
        """Simple XML format without known_tools should NOT be parsed (pattern 3 requires it)."""
        text = '<Bash><command>ls</command></Bash>'
        calls, cleaned = _extract_tool_calls_from_text(text, known_tools=None)
        # Pattern 3 only runs if known_tools is provided
        # Patterns 1 and 2 won't match this format
        self.assertEqual(calls, [])

    def test_simple_xml_unknown_tool_filtered(self):
        """Tool not in known_tools should be filtered out."""
        text = '<Unknown><param>val</param></Unknown>'
        known = {"Bash", "Read"}
        calls, cleaned = _extract_tool_calls_from_text(text, known_tools=known)
        self.assertEqual(calls, [])


class TestExtractToolCallsXmlEntities(unittest.TestCase):
    """Tests for XML entity decoding in parameter values."""

    def test_lt_entity(self):
        """&lt; should be decoded to '<'."""
        text = '<invoke name="Bash"><parameter name="command">echo &lt;hello&gt;</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertIn("<hello>", args["command"])

    def test_amp_entity(self):
        """&amp; should be decoded to '&'."""
        text = '<invoke name="Bash"><parameter name="command">a &amp; b</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["command"], "a & b")

    def test_gt_entity(self):
        """&gt; should be decoded to '>'."""
        text = '<invoke name="Bash"><parameter name="command">x &gt; y</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["command"], "x > y")


class TestExtractToolCallsJsonParams(unittest.TestCase):
    """Tests for JSON value auto-parsing in parameters."""

    def test_boolean_param(self):
        """Boolean parameter values should be auto-parsed."""
        text = '<invoke name="Read"><parameter name="path">file.py</parameter><parameter name="binary">true</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertIs(args["binary"], True)

    def test_number_param(self):
        """Numeric parameter values should be auto-parsed."""
        text = '<invoke name="Read"><parameter name="path">file.py</parameter><parameter name="limit">100</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["limit"], 100)

    def test_array_param(self):
        """Array parameter values should be auto-parsed."""
        text = '<invoke name="Tool"><parameter name="items">["a","b","c"]</parameter></invoke>'
        calls, _ = _extract_tool_calls_from_text(text)
        args = json.loads(calls[0]["function"]["arguments"])
        self.assertEqual(args["items"], ["a", "b", "c"])


class TestExtractToolCallsDeduplication(unittest.TestCase):
    """Tests for deduplication of tool calls."""

    def test_duplicate_invoke_calls_deduped(self):
        """Identical tool calls appearing twice should be deduplicated."""
        single = '<invoke name="Bash"><parameter name="command">ls</parameter></invoke>'
        text = single + "\n" + single
        calls, _ = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)

    def test_different_args_not_deduped(self):
        """Tool calls with different arguments should NOT be deduplicated."""
        text = (
            '<invoke name="Bash"><parameter name="command">ls</parameter></invoke>'
            '<invoke name="Bash"><parameter name="command">pwd</parameter></invoke>'
        )
        calls, _ = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 2)


class TestExtractToolCallsMultiple(unittest.TestCase):
    """Tests for extracting multiple tool calls."""

    def test_multiple_different_tools(self):
        """Multiple different tool calls should all be extracted."""
        text = (
            '<invoke name="Bash"><parameter name="command">ls</parameter></invoke>'
            '<invoke name="Read"><parameter name="path">file.py</parameter></invoke>'
        )
        calls, _ = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 2)
        names = {c["function"]["name"] for c in calls}
        self.assertEqual(names, {"Bash", "Read"})


class TestExtractToolCallsKnownToolsFiltering(unittest.TestCase):
    """Tests for known_tools filtering across all patterns."""

    def test_invoke_filtered_by_known_tools(self):
        """Pattern 1 (invoke) should filter by known_tools."""
        text = '<invoke name="ForbiddenTool"><parameter name="x">1</parameter></invoke>'
        known = {"Bash", "Read"}
        calls, _ = _extract_tool_calls_from_text(text, known_tools=known)
        self.assertEqual(calls, [])

    def test_invoke_allowed_by_known_tools(self):
        """Pattern 1 (invoke) should allow tools in known_tools."""
        text = '<invoke name="Bash"><parameter name="command">ls</parameter></invoke>'
        known = {"Bash", "Read"}
        calls, _ = _extract_tool_calls_from_text(text, known_tools=known)
        self.assertEqual(len(calls), 1)

    def test_qwen_filtered_by_known_tools(self):
        """Pattern 2 (Qwen) should filter by known_tools."""
        text = '<function=Unknown><parameter=x>1</parameter></function>'
        known = {"Bash"}
        calls, _ = _extract_tool_calls_from_text(text, known_tools=known)
        self.assertEqual(calls, [])


class TestExtractToolCallsCleanedText(unittest.TestCase):
    """Tests for cleaned text output."""

    def test_tool_xml_removed_from_cleaned_text(self):
        """Tool call XML should be removed from the cleaned text."""
        text = 'Before <invoke name="Bash"><parameter name="command">ls</parameter></invoke> After'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("<invoke", cleaned)
        self.assertIn("Before", cleaned)
        self.assertIn("After", cleaned)

    def test_wrapper_tags_cleaned(self):
        """Wrapper tags (function_calls, action, tool_call) should be stripped."""
        text = '<function_calls><invoke name="Bash"><parameter name="command">ls</parameter></invoke></function_calls>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("function_calls", cleaned)

    def test_action_wrapper_cleaned(self):
        """<action> wrapper tag should be stripped."""
        text = '<action><invoke name="Bash"><parameter name="command">ls</parameter></invoke></action>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("<action>", cleaned)
        self.assertNotIn("</action>", cleaned)

    def test_tool_call_wrapper_cleaned(self):
        """<tool_call> wrapper tag should be stripped."""
        text = '<tool_call><invoke name="Bash"><parameter name="command">ls</parameter></invoke></tool_call>'
        calls, cleaned = _extract_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("<tool_call>", cleaned)
        self.assertNotIn("</tool_call>", cleaned)


if __name__ == "__main__":
    unittest.main()
