import importlib.util
import os
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class TestAutoTestRunner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            for root, dirs, files in os.walk(self.tmpdir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.tmpdir)
        except OSError:
            pass

    def test_retryable_timeout_reruns_once(self):
        runner = eve_coder.AutoTestRunner(self.tmpdir)
        runner.enabled = True
        runner.lint_cmd = None
        runner.test_cmd = ["python3", "-m", "unittest"]

        with mock.patch.object(
            eve_coder.subprocess,
            "run",
            side_effect=[
                eve_coder.subprocess.TimeoutExpired(cmd=runner.test_cmd, timeout=120),
                mock.Mock(returncode=0, stdout="ok", stderr=""),
            ],
        ) as patched:
            pipeline = runner.run_pipeline("notes.txt")

        self.assertTrue(pipeline["ok"])
        self.assertTrue(pipeline["retry_attempted"])
        self.assertEqual(pipeline["attempts"], 2)
        self.assertEqual(patched.call_count, 2)

    def test_non_retryable_failure_stops_after_first_attempt(self):
        runner = eve_coder.AutoTestRunner(self.tmpdir)
        runner.enabled = True
        runner.lint_cmd = None
        runner.test_cmd = ["python3", "-m", "unittest"]

        with mock.patch.object(
            eve_coder.subprocess,
            "run",
            return_value=mock.Mock(returncode=1, stdout="FAILED (failures=1)", stderr=""),
        ) as patched:
            pipeline = runner.run_pipeline("notes.txt")

        self.assertFalse(pipeline["ok"])
        self.assertFalse(pipeline["retry_attempted"])
        self.assertEqual(pipeline["attempts"], 1)
        self.assertEqual(pipeline["failure_kind"], "test")
        self.assertIn("FAILED", pipeline["error_output"])
        self.assertEqual(patched.call_count, 1)


if __name__ == "__main__":
    unittest.main()
