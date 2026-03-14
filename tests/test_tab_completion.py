"""
Regression tests for interactive readline tab completion.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class TestTabCompletion(unittest.TestCase):
    """Test readline completion behavior for commands and file paths."""

    def setUp(self):
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        with open(os.path.join(self.test_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write("# test\n")
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "docs"), exist_ok=True)
        with open(os.path.join(self.test_dir, "docs", "troubleshooting.md"), "w", encoding="utf-8") as f:
            f.write("troubleshooting\n")
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_slash_command_completion_still_works(self):
        options = eve_coder._readline_completion_options("/he", ["/help", "/exit"])
        self.assertEqual(options, ["/help"])

    def test_at_file_completion_still_works(self):
        options = eve_coder._readline_completion_options("@REA", [])
        self.assertEqual(options, ["@README.md"])

    def test_bare_relative_path_completion_works(self):
        options = eve_coder._readline_completion_options("REA", [])
        self.assertEqual(options, ["README.md"])

    def test_nested_path_completion_still_works(self):
        options = eve_coder._readline_completion_options("docs/tr", [])
        self.assertEqual(options, ["docs/troubleshooting.md"])


if __name__ == "__main__":
    unittest.main()
