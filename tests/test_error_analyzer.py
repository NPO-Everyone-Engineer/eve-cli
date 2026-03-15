"""
Test suite for ErrorAnalyzer, ErrorFixStrategy, and ErrorLogger classes.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

ErrorAnalyzer = eve_coder.ErrorAnalyzer
ErrorFixStrategy = eve_coder.ErrorFixStrategy
ErrorLogger = eve_coder.ErrorLogger


# ────────────────────────────────────────────────────────────────────────────────
# ErrorAnalyzer.parse tests
# ────────────────────────────────────────────────────────────────────────────────

class TestErrorAnalyzerSyntax(unittest.TestCase):
    """Test detection of syntax errors."""

    def test_syntax_error_keyword(self):
        result = ErrorAnalyzer.parse("SyntaxError: invalid syntax at line 42")
        self.assertEqual(result["type"], "syntax")
        self.assertEqual(result["confidence"], 0.8)

    def test_indentation_error(self):
        result = ErrorAnalyzer.parse("IndentationError: unexpected indent")
        self.assertEqual(result["type"], "syntax")

    def test_unexpected_eof(self):
        result = ErrorAnalyzer.parse("unexpected EOF while parsing")
        self.assertEqual(result["type"], "syntax")

    def test_invalid_syntax(self):
        result = ErrorAnalyzer.parse("File 'test.py', line 10: invalid syntax")
        self.assertEqual(result["type"], "syntax")

    def test_syntax_suggested_fix(self):
        result = ErrorAnalyzer.parse("SyntaxError: invalid syntax")
        self.assertIn("構文", result["suggested_fix"])


class TestErrorAnalyzerFileNotFound(unittest.TestCase):
    """Test detection of file-not-found errors."""

    def test_no_such_file_or_directory(self):
        result = ErrorAnalyzer.parse("bash: /usr/bin/foo: No such file or directory")
        self.assertEqual(result["type"], "file_not_found")

    def test_file_not_found_error(self):
        result = ErrorAnalyzer.parse("FileNotFoundError: [Errno 2] No such file")
        self.assertEqual(result["type"], "file_not_found")

    def test_cannot_access(self):
        result = ErrorAnalyzer.parse("ls: cannot access '/nonexistent': No such file")
        self.assertEqual(result["type"], "file_not_found")

    def test_file_not_found_suggested_fix(self):
        result = ErrorAnalyzer.parse("FileNotFoundError: missing.txt")
        self.assertIn("ファイルパス", result["suggested_fix"])


class TestErrorAnalyzerPermission(unittest.TestCase):
    """Test detection of permission errors."""

    def test_permission_denied(self):
        result = ErrorAnalyzer.parse("bash: /etc/shadow: Permission denied")
        self.assertEqual(result["type"], "permission")

    def test_operation_not_permitted(self):
        result = ErrorAnalyzer.parse("OSError: Operation not permitted")
        self.assertEqual(result["type"], "permission")

    def test_sudo_keyword(self):
        result = ErrorAnalyzer.parse("Try running with sudo")
        self.assertEqual(result["type"], "permission")

    def test_permission_suggested_fix(self):
        result = ErrorAnalyzer.parse("Permission denied")
        self.assertIn("権限", result["suggested_fix"])


class TestErrorAnalyzerCommandNotFound(unittest.TestCase):
    """Test detection of command-not-found errors."""

    def test_command_not_found(self):
        result = ErrorAnalyzer.parse("bash: foo: command not found")
        self.assertEqual(result["type"], "command_not_found")

    def test_is_not_recognized(self):
        result = ErrorAnalyzer.parse("'foo' is not recognized as an internal command")
        self.assertEqual(result["type"], "command_not_found")

    def test_no_module_named(self):
        result = ErrorAnalyzer.parse("No module named 'requests'")
        self.assertEqual(result["type"], "command_not_found")


class TestErrorAnalyzerImportError(unittest.TestCase):
    """Test detection of import errors."""

    def test_import_error(self):
        result = ErrorAnalyzer.parse("ImportError: cannot import name 'foo' from 'bar'")
        self.assertEqual(result["type"], "import_error")

    def test_module_not_found_error(self):
        # "No module named" is in command_not_found patterns (checked before import_error)
        # so text containing both will match command_not_found first.
        # Pure "ModuleNotFoundError" without "No module named" matches import_error.
        result = ErrorAnalyzer.parse("ModuleNotFoundError: cannot import 'numpy'")
        self.assertEqual(result["type"], "import_error")

    def test_module_not_found_matches_command_not_found_first(self):
        # "No module named" pattern is in command_not_found, which is checked before import_error
        result = ErrorAnalyzer.parse("ModuleNotFoundError: No module named 'numpy'")
        self.assertEqual(result["type"], "command_not_found")

    def test_import_error_suggested_fix(self):
        result = ErrorAnalyzer.parse("ImportError: cannot import name 'foo'")
        self.assertIn("pip install", result["suggested_fix"])


class TestErrorAnalyzerTimeout(unittest.TestCase):
    """Test detection of timeout errors."""

    def test_timeout_keyword(self):
        result = ErrorAnalyzer.parse("Connection timeout after 30s")
        self.assertEqual(result["type"], "timeout")

    def test_timed_out(self):
        result = ErrorAnalyzer.parse("Request timed out")
        self.assertEqual(result["type"], "timeout")

    def test_deadlock(self):
        result = ErrorAnalyzer.parse("Process deadlock detected")
        self.assertEqual(result["type"], "timeout")

    def test_timeout_suggested_fix(self):
        result = ErrorAnalyzer.parse("Connection timed out")
        self.assertIn("タイムアウト", result["suggested_fix"])


class TestErrorAnalyzerUnknown(unittest.TestCase):
    """Test fallback to unknown for unrecognised errors."""

    def test_unknown_error(self):
        result = ErrorAnalyzer.parse("Something went terribly wrong in 42 dimensions")
        self.assertEqual(result["type"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["suggested_fix"], "")

    def test_empty_error(self):
        result = ErrorAnalyzer.parse("")
        self.assertEqual(result["type"], "unknown")
        self.assertEqual(result["confidence"], 0.0)

    def test_raw_error_preserved(self):
        text = "Some random error text 12345"
        result = ErrorAnalyzer.parse(text)
        self.assertEqual(result["raw_error"], text)


class TestErrorAnalyzerCaseInsensitive(unittest.TestCase):
    """Verify case insensitive matching (re.IGNORECASE)."""

    def test_syntaxerror_lowercase(self):
        result = ErrorAnalyzer.parse("syntaxerror: oops")
        self.assertEqual(result["type"], "syntax")

    def test_permission_denied_mixed_case(self):
        result = ErrorAnalyzer.parse("PERMISSION DENIED for /etc/shadow")
        self.assertEqual(result["type"], "permission")

    def test_timed_out_uppercase(self):
        result = ErrorAnalyzer.parse("REQUEST TIMED OUT")
        self.assertEqual(result["type"], "timeout")

    def test_command_not_found_uppercase(self):
        result = ErrorAnalyzer.parse("COMMAND NOT FOUND: xyz")
        self.assertEqual(result["type"], "command_not_found")


class TestErrorAnalyzerReturnStructure(unittest.TestCase):
    """Verify the dict structure returned by parse()."""

    def test_keys_present(self):
        result = ErrorAnalyzer.parse("anything")
        self.assertIn("type", result)
        self.assertIn("confidence", result)
        self.assertIn("suggested_fix", result)
        self.assertIn("raw_error", result)

    def test_raw_error_is_original_text(self):
        text = "FileNotFoundError: path/to/file"
        result = ErrorAnalyzer.parse(text)
        self.assertEqual(result["raw_error"], text)


# ────────────────────────────────────────────────────────────────────────────────
# ErrorFixStrategy.select tests
# ────────────────────────────────────────────────────────────────────────────────

class TestErrorFixStrategy(unittest.TestCase):
    """Test ErrorFixStrategy.select returns appropriate prompts."""

    def test_syntax_strategy(self):
        prompt = ErrorFixStrategy.select("syntax", {})
        self.assertIn("構文", prompt)

    def test_file_not_found_strategy(self):
        prompt = ErrorFixStrategy.select("file_not_found", {})
        self.assertIn("ファイル", prompt)

    def test_permission_strategy(self):
        prompt = ErrorFixStrategy.select("permission", {})
        self.assertIn("権限", prompt)

    def test_command_not_found_strategy(self):
        prompt = ErrorFixStrategy.select("command_not_found", {})
        self.assertIn("コマンド", prompt)

    def test_import_error_strategy(self):
        prompt = ErrorFixStrategy.select("import_error", {})
        self.assertIn("モジュール", prompt)

    def test_timeout_strategy(self):
        prompt = ErrorFixStrategy.select("timeout", {})
        self.assertIn("タイムアウト", prompt)

    def test_unknown_type_returns_default(self):
        prompt = ErrorFixStrategy.select("totally_unknown", {})
        self.assertIn("修正", prompt)

    def test_context_param_accepted(self):
        """Ensure context parameter does not cause an error."""
        prompt = ErrorFixStrategy.select("syntax", {"file": "test.py"})
        self.assertIsInstance(prompt, str)


# ────────────────────────────────────────────────────────────────────────────────
# ErrorLogger.append tests
# ────────────────────────────────────────────────────────────────────────────────

class TestErrorLogger(unittest.TestCase):
    """Test ErrorLogger writes formatted entries to file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.tmpdir, "error-log.md")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _append_with_tmpdir(self, entry):
        """Call ErrorLogger.append but redirect LOG_FILE to tmpdir."""
        with patch.object(ErrorLogger, "LOG_FILE", self.log_file):
            ErrorLogger.append(entry)

    def test_creates_log_file(self):
        self._append_with_tmpdir({"type": "syntax", "confidence": 0.8, "raw_error": "err", "suggested_fix": "fix"})
        self.assertTrue(os.path.isfile(self.log_file))

    def test_log_contains_error_type(self):
        self._append_with_tmpdir({"type": "timeout", "confidence": 0.8, "raw_error": "err"})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("timeout", content)

    def test_log_contains_raw_error(self):
        raw = "FileNotFoundError: missing.txt"
        self._append_with_tmpdir({"type": "file_not_found", "raw_error": raw})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn(raw, content)

    def test_log_contains_confidence_formatted(self):
        self._append_with_tmpdir({"type": "syntax", "confidence": 0.8, "raw_error": "err"})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("80%", content)

    def test_multiple_appends_accumulate(self):
        self._append_with_tmpdir({"type": "syntax", "raw_error": "first"})
        self._append_with_tmpdir({"type": "timeout", "raw_error": "second"})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("first", content)
        self.assertIn("second", content)

    def test_creates_parent_directory(self):
        nested_log = os.path.join(self.tmpdir, "deep", "nested", "error-log.md")
        with patch.object(ErrorLogger, "LOG_FILE", nested_log):
            ErrorLogger.append({"type": "syntax", "raw_error": "err"})
        self.assertTrue(os.path.isfile(nested_log))

    def test_log_format_has_markdown_heading(self):
        self._append_with_tmpdir({"type": "import_error", "raw_error": "err"})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("##", content)

    def test_raw_error_truncated_to_500_chars(self):
        long_error = "x" * 1000
        self._append_with_tmpdir({"type": "syntax", "raw_error": long_error})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        # The raw_error in the file should be at most 500 chars of the original
        self.assertNotIn("x" * 501, content)

    def test_missing_keys_use_defaults(self):
        """Append with minimal dict should not crash."""
        self._append_with_tmpdir({})
        with open(self.log_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("unknown", content)


if __name__ == "__main__":
    unittest.main()
