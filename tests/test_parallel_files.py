"""
Test suite for parallel file editing functionality.

These tests are written with unittest so they are collected by the default
`python -m unittest discover` harness used in this repository.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location(
    "eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py")
)
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

MultiEditTool = eve_coder.MultiEditTool


class ParallelFileEditingTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tool = MultiEditTool(cwd=self.test_dir)
        self.test_files = []
        for i in range(5):
            fpath = os.path.join(self.test_dir, f"file{i}.txt")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"Hello World {i}\nLine 2\nLine 3\n")
            self.test_files.append(fpath)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)


class TestParallelFileEditing(ParallelFileEditingTestCase):
    """Tests for parallel file editing functionality."""

    def test_single_edit(self):
        edits = [{
            "file_path": self.test_files[0],
            "old_string": "Hello World 0",
            "new_string": "Goodbye World 0",
        }]

        result = self.tool.execute({"edits": edits})

        self.assertIn("OK: file0.txt", result)
        self.assertIn("1/1 edits applied", result)
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Goodbye World 0", content)
        self.assertNotIn("Hello World 0", content)

    def test_multiple_edits_parallel(self):
        edits = []
        for i in range(5):
            edits.append({
                "file_path": self.test_files[i],
                "old_string": f"Hello World {i}",
                "new_string": f"Modified {i}",
            })

        start_time = time.time()
        result = self.tool.execute({"edits": edits})
        elapsed = time.time() - start_time

        self.assertIn("5/5 edits applied", result)
        for i in range(5):
            with open(self.test_files[i], "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(f"Modified {i}", content)
            self.assertNotIn(f"Hello World {i}", content)
        self.assertLess(elapsed, 2.0)

    def test_partial_failure_aborts_atomically(self):
        """Security Finding #4: MultiEdit must abort the whole batch if any
        single edit fails validation. Previously this test asserted partial
        success (`2/3 edits applied`); the atomic contract reverses that."""
        edits = [
            {
                "file_path": self.test_files[0],
                "old_string": "Hello World 0",
                "new_string": "Modified 0",
            },
            {
                "file_path": self.test_files[1],
                "old_string": "NonExistent String",
                "new_string": "Modified 1",
            },
            {
                "file_path": self.test_files[2],
                "old_string": "Hello World 2",
                "new_string": "Modified 2",
            },
        ]

        result = self.tool.execute({"edits": edits})

        self.assertIn("0/3 edits applied", result)
        self.assertIn("aborted at validation", result)
        self.assertIn("Error: old_string not found", result)
        # All three files MUST remain at their original content.
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            self.assertIn("Hello World 0", f.read())
        with open(self.test_files[1], "r", encoding="utf-8") as f:
            self.assertIn("Hello World 1", f.read())
        with open(self.test_files[2], "r", encoding="utf-8") as f:
            self.assertIn("Hello World 2", f.read())

    def test_invalid_path(self):
        edits = [{
            "file_path": "/nonexistent/path/file.txt",
            "old_string": "test",
            "new_string": "test",
        }]

        result = self.tool.execute({"edits": edits})
        self.assertTrue(
            "Error: invalid path" in result or "file not found" in result,
            msg=result,
        )

    def test_protected_path(self):
        edits = [{
            "file_path": "/etc/hosts",
            "old_string": "test",
            "new_string": "test",
        }]

        result = self.tool.execute({"edits": edits})
        self.assertIn("Error:", result)

    def test_symlink_rejection(self):
        original = os.path.join(self.test_dir, "original.txt")
        link = os.path.join(self.test_dir, "link.txt")

        with open(original, "w", encoding="utf-8") as f:
            f.write("Original content\n")

        os.symlink(original, link)
        edits = [{
            "file_path": link,
            "old_string": "Original content",
            "new_string": "Modified content",
        }]

        result = self.tool.execute({"edits": edits})
        self.assertIn("symlink not allowed", result)

    def test_outside_repo_rejected(self):
        outside_dir = tempfile.mkdtemp()
        try:
            outside_file = os.path.join(outside_dir, "outside.txt")
            with open(outside_file, "w", encoding="utf-8") as f:
                f.write("secret\n")
            edits = [{
                "file_path": outside_file,
                "old_string": "secret",
                "new_string": "public",
            }]
            result = self.tool.execute({"edits": edits})
            self.assertIn("outside repository", result)
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_parent_symlink_escape_rejected(self):
        outside_dir = tempfile.mkdtemp()
        try:
            outside_file = os.path.join(outside_dir, "outside.txt")
            with open(outside_file, "w", encoding="utf-8") as f:
                f.write("secret\n")
            link_dir = os.path.join(self.test_dir, "linked")
            os.symlink(outside_dir, link_dir)
            edits = [{
                "file_path": os.path.join(link_dir, "outside.txt"),
                "old_string": "secret",
                "new_string": "public",
            }]
            result = self.tool.execute({"edits": edits})
            self.assertIn("outside repository", result)
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_multiple_edits_same_file(self):
        edits = [
            {
                "file_path": self.test_files[0],
                "old_string": "Line 2",
                "new_string": "Modified Line 2",
            },
            {
                "file_path": self.test_files[0],
                "old_string": "Line 3",
                "new_string": "Modified Line 3",
            },
        ]

        result = self.tool.execute({"edits": edits})

        self.assertIn("2/2 edits applied", result)
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Modified Line 2", content)
        self.assertIn("Modified Line 3", content)

    def test_file_lock_prevents_corruption(self):
        test_file = os.path.join(self.test_dir, "concurrent.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Line 0\nLine 1\nLine 2\nLine 3\nLine 4\n")

        edits = []
        for i in range(5):
            edits.append({
                "file_path": test_file,
                "old_string": f"Line {i}",
                "new_string": f"Modified {i}",
            })

        result = self.tool.execute({"edits": edits})

        self.assertIn("5/5 edits applied", result)
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        for i in range(5):
            self.assertIn(f"Modified {i}", content)

    def test_max_edits_limit(self):
        edits = []
        for i in range(25):
            edits.append({
                "file_path": self.test_files[0],
                "old_string": f"test{i}",
                "new_string": f"modified{i}",
            })

        result = self.tool.execute({"edits": edits})
        self.assertIn("too many edits (max 20)", result)

    def test_empty_edits(self):
        result = self.tool.execute({"edits": []})
        self.assertIn("no edits provided", result)

    def test_apply_phase_rollback(self):
        """If a write fails after some files have been written, MultiEdit
        must roll back the already-written files to their originals."""
        edits = [
            {
                "file_path": self.test_files[0],
                "old_string": "Hello World 0",
                "new_string": "Modified 0",
            },
            {
                "file_path": self.test_files[1],
                "old_string": "Hello World 1",
                "new_string": "Modified 1",
            },
            {
                "file_path": self.test_files[2],
                "old_string": "Hello World 2",
                "new_string": "Modified 2",
            },
        ]
        # Validation will pass for all three; force the second write to fail.
        original_write = self.tool._write_atomic
        call_count = {"n": 0}

        def flaky_write(path, content):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise OSError("simulated disk failure")
            return original_write(path, content)

        self.tool._write_atomic = flaky_write
        try:
            result = self.tool.execute({"edits": edits})
        finally:
            self.tool._write_atomic = original_write

        self.assertIn("0/3 edits applied", result)
        self.assertIn("write failed, rolled back", result)
        # All three originals must be restored.
        for i in range(3):
            with open(self.test_files[i], "r", encoding="utf-8") as f:
                self.assertIn(f"Hello World {i}", f.read())


class TestParallelConfiguration(unittest.TestCase):
    def test_max_parallel_files_range(self):
        self.assertGreaterEqual(eve_coder._MAX_PARALLEL_FILES, 1)
        self.assertLessEqual(eve_coder._MAX_PARALLEL_FILES, 10)

    def test_show_progress_default(self):
        self.assertTrue(eve_coder._SHOW_PROGRESS)


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of parallel file operations."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tool = MultiEditTool(cwd=self.test_dir)
        self.test_files = []
        for i in range(10):
            fpath = os.path.join(self.test_dir, f"file{i}.txt")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"Content {i}\n")
            self.test_files.append(fpath)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_execution(self):
        results = []
        errors = []
        results_lock = threading.Lock()

        def run_edit(file_idx):
            try:
                edits = [{
                    "file_path": self.test_files[file_idx],
                    "old_string": f"Content {file_idx}",
                    "new_string": f"Modified {file_idx}",
                }]
                result = self.tool.execute({"edits": edits})
                with results_lock:
                    results.append(result)
            except Exception as exc:
                with results_lock:
                    errors.append(str(exc))

        threads = []
        for i in range(10):
            thread = threading.Thread(target=run_edit, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 10)
        for i in range(10):
            with open(self.test_files[i], "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(f"Modified {i}", content)


if __name__ == "__main__":
    unittest.main()
