"""
Test suite for FileWatcher class.
"""

import unittest
import sys
import os
import time
import tempfile
import shutil

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# Import eve-coder.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)
FileWatcher = eve_coder.FileWatcher


class TestFileWatcherInit(unittest.TestCase):
    """Tests for FileWatcher initialization."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_initial_state_not_enabled(self):
        """FileWatcher should not be enabled by default."""
        self.assertFalse(self.watcher.enabled)

    def test_initial_empty_snapshots(self):
        """Snapshots should be empty on init."""
        self.assertEqual(self.watcher._snapshots, {})

    def test_initial_empty_changes(self):
        """Changes list should be empty on init."""
        self.assertEqual(self.watcher._changes, [])

    def test_initial_no_thread(self):
        """No polling thread should be running on init."""
        self.assertIsNone(self.watcher._thread)


class TestFileWatcherConstants(unittest.TestCase):
    """Tests for FileWatcher class constants."""

    def test_max_files(self):
        """MAX_FILES should be 5000."""
        self.assertEqual(FileWatcher.MAX_FILES, 5000)

    def test_poll_interval(self):
        """POLL_INTERVAL should be 2.0 seconds."""
        self.assertEqual(FileWatcher.POLL_INTERVAL, 2.0)

    def test_watch_extensions_is_frozenset(self):
        """WATCH_EXTENSIONS should be a frozenset."""
        self.assertIsInstance(FileWatcher.WATCH_EXTENSIONS, frozenset)

    def test_skip_dirs_is_frozenset(self):
        """SKIP_DIRS should be a frozenset."""
        self.assertIsInstance(FileWatcher.SKIP_DIRS, frozenset)

    def test_common_extensions_included(self):
        """Common programming extensions should be in WATCH_EXTENSIONS."""
        for ext in [".py", ".js", ".ts", ".json", ".html", ".css"]:
            self.assertIn(ext, FileWatcher.WATCH_EXTENSIONS)

    def test_common_skip_dirs_included(self):
        """Common skip directories should be in SKIP_DIRS."""
        for d in [".git", "node_modules", "__pycache__", ".venv"]:
            self.assertIn(d, FileWatcher.SKIP_DIRS)


class TestFileWatcherScan(unittest.TestCase):
    """Tests for FileWatcher._scan method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_finds_matching_files(self):
        """_scan should find files with watched extensions."""
        filepath = os.path.join(self.tmpdir, "test.py")
        with open(filepath, "w") as f:
            f.write("print('hello')")
        result = self.watcher._scan()
        self.assertIn(filepath, result)

    def test_scan_ignores_non_matching_extensions(self):
        """_scan should ignore files without watched extensions."""
        filepath = os.path.join(self.tmpdir, "data.bin")
        with open(filepath, "w") as f:
            f.write("binary data")
        result = self.watcher._scan()
        self.assertNotIn(filepath, result)

    def test_scan_skips_skip_dirs(self):
        """_scan should skip directories in SKIP_DIRS."""
        skip_dir = os.path.join(self.tmpdir, "node_modules")
        os.makedirs(skip_dir)
        filepath = os.path.join(skip_dir, "index.js")
        with open(filepath, "w") as f:
            f.write("module.exports = {}")
        result = self.watcher._scan()
        self.assertNotIn(filepath, result)

    def test_scan_skips_hidden_dirs(self):
        """_scan should skip directories starting with '.' (except those explicitly listed)."""
        hidden_dir = os.path.join(self.tmpdir, ".hidden")
        os.makedirs(hidden_dir)
        filepath = os.path.join(hidden_dir, "secret.py")
        with open(filepath, "w") as f:
            f.write("pass")
        result = self.watcher._scan()
        self.assertNotIn(filepath, result)

    def test_scan_returns_mtime_and_size(self):
        """_scan should return (mtime, size) tuples."""
        filepath = os.path.join(self.tmpdir, "test.py")
        content = "x = 42\n"
        with open(filepath, "w") as f:
            f.write(content)
        result = self.watcher._scan()
        self.assertIn(filepath, result)
        mtime, size = result[filepath]
        self.assertIsInstance(mtime, float)
        self.assertIsInstance(size, int)

    def test_scan_respects_max_files(self):
        """_scan should not return more than MAX_FILES entries."""
        # Temporarily lower MAX_FILES for test
        original = FileWatcher.MAX_FILES
        FileWatcher.MAX_FILES = 3
        try:
            for i in range(10):
                filepath = os.path.join(self.tmpdir, f"file{i}.py")
                with open(filepath, "w") as f:
                    f.write(f"# file {i}")
            result = self.watcher._scan()
            self.assertLessEqual(len(result), 3)
        finally:
            FileWatcher.MAX_FILES = original

    def test_scan_empty_directory(self):
        """_scan on empty directory returns empty dict."""
        result = self.watcher._scan()
        self.assertEqual(result, {})


class TestFileWatcherDetectChanges(unittest.TestCase):
    """Tests for FileWatcher._detect_changes method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detect_created(self):
        """New file in new snapshot should be detected as 'created'."""
        old = {}
        new = {"/tmp/new.py": (1000.0, 100)}
        changes = self.watcher._detect_changes(old, new)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("created", "/tmp/new.py"))

    def test_detect_modified(self):
        """Changed mtime/size should be detected as 'modified'."""
        old = {"/tmp/mod.py": (1000.0, 100)}
        new = {"/tmp/mod.py": (2000.0, 150)}
        changes = self.watcher._detect_changes(old, new)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("modified", "/tmp/mod.py"))

    def test_detect_deleted(self):
        """File in old but not in new should be detected as 'deleted'."""
        old = {"/tmp/del.py": (1000.0, 100)}
        new = {}
        changes = self.watcher._detect_changes(old, new)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("deleted", "/tmp/del.py"))

    def test_no_changes(self):
        """Identical snapshots should produce no changes."""
        snap = {"/tmp/same.py": (1000.0, 100)}
        changes = self.watcher._detect_changes(snap, dict(snap))
        self.assertEqual(changes, [])

    def test_multiple_changes(self):
        """Multiple changes should all be detected."""
        old = {"/tmp/a.py": (1000.0, 100), "/tmp/b.py": (1000.0, 200)}
        new = {"/tmp/a.py": (2000.0, 100), "/tmp/c.py": (1000.0, 50)}
        changes = self.watcher._detect_changes(old, new)
        types = {c[0] for c in changes}
        paths = {c[1] for c in changes}
        self.assertIn("modified", types)   # a.py changed mtime
        self.assertIn("created", types)    # c.py is new
        self.assertIn("deleted", types)    # b.py removed
        self.assertIn("/tmp/a.py", paths)
        self.assertIn("/tmp/b.py", paths)
        self.assertIn("/tmp/c.py", paths)


class TestFileWatcherFormatChanges(unittest.TestCase):
    """Tests for FileWatcher.format_changes method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_format_empty_returns_empty_string(self):
        """Empty changes list returns empty string."""
        result = self.watcher.format_changes([])
        self.assertEqual(result, "")

    def test_format_created_icon(self):
        """Created changes use '+' icon."""
        filepath = os.path.join(self.tmpdir, "new.py")
        result = self.watcher.format_changes([("created", filepath)])
        self.assertIn("+ ", result)
        self.assertIn("(created)", result)

    def test_format_modified_icon(self):
        """Modified changes use '~' icon."""
        filepath = os.path.join(self.tmpdir, "mod.py")
        result = self.watcher.format_changes([("modified", filepath)])
        self.assertIn("~ ", result)
        self.assertIn("(modified)", result)

    def test_format_deleted_icon(self):
        """Deleted changes use '-' icon."""
        filepath = os.path.join(self.tmpdir, "del.py")
        result = self.watcher.format_changes([("deleted", filepath)])
        self.assertIn("- ", result)
        self.assertIn("(deleted)", result)

    def test_format_header_line(self):
        """Formatted output should include a header line."""
        filepath = os.path.join(self.tmpdir, "test.py")
        result = self.watcher.format_changes([("created", filepath)])
        self.assertIn("[File Watcher]", result)

    def test_format_caps_at_20_items(self):
        """Format should cap at 20 items and show overflow message."""
        changes = [("created", os.path.join(self.tmpdir, f"f{i}.py")) for i in range(25)]
        result = self.watcher.format_changes(changes)
        self.assertIn("... and 5 more", result)

    def test_format_exactly_20_no_overflow(self):
        """Format with exactly 20 items should not show overflow message."""
        changes = [("created", os.path.join(self.tmpdir, f"f{i}.py")) for i in range(20)]
        result = self.watcher.format_changes(changes)
        self.assertNotIn("... and", result)


class TestFileWatcherGetPendingChanges(unittest.TestCase):
    """Tests for FileWatcher.get_pending_changes method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_pending_changes_returns_and_clears(self):
        """get_pending_changes should return changes and clear the list."""
        self.watcher._changes = [("created", "/tmp/a.py"), ("modified", "/tmp/b.py")]
        result = self.watcher.get_pending_changes()
        self.assertEqual(len(result), 2)
        # After get, internal list should be empty
        self.assertEqual(self.watcher._changes, [])

    def test_get_pending_changes_empty(self):
        """get_pending_changes with no changes returns empty list."""
        result = self.watcher.get_pending_changes()
        self.assertEqual(result, [])

    def test_get_pending_changes_returns_copy(self):
        """Returned list should be independent of internal state."""
        self.watcher._changes = [("created", "/tmp/a.py")]
        result = self.watcher.get_pending_changes()
        result.append(("deleted", "/tmp/b.py"))
        # Internal list should still be empty (cleared)
        self.assertEqual(self.watcher._changes, [])


class TestFileWatcherLifecycle(unittest.TestCase):
    """Tests for FileWatcher start/stop lifecycle."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        self.watcher.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_start_enables_watcher(self):
        """start() should set enabled to True."""
        self.watcher.start()
        self.assertTrue(self.watcher.enabled)

    def test_start_creates_thread(self):
        """start() should create a polling thread."""
        self.watcher.start()
        self.assertIsNotNone(self.watcher._thread)
        self.assertTrue(self.watcher._thread.is_alive())

    def test_stop_disables_watcher(self):
        """stop() should set enabled to False."""
        self.watcher.start()
        self.watcher.stop()
        self.assertFalse(self.watcher.enabled)

    def test_stop_clears_thread(self):
        """stop() should terminate and clear the thread."""
        self.watcher.start()
        self.watcher.stop()
        self.assertIsNone(self.watcher._thread)


class TestFileWatcherRefreshSnapshot(unittest.TestCase):
    """Tests for FileWatcher.refresh_snapshot method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = FileWatcher(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_refresh_updates_snapshot(self):
        """refresh_snapshot should update internal snapshot with current files."""
        # Initially empty
        self.assertEqual(self.watcher._snapshots, {})
        # Create a file
        filepath = os.path.join(self.tmpdir, "new.py")
        with open(filepath, "w") as f:
            f.write("pass")
        # Refresh and verify
        self.watcher.refresh_snapshot()
        self.assertIn(filepath, self.watcher._snapshots)

    def test_refresh_reflects_removed_files(self):
        """refresh_snapshot should reflect file removals."""
        filepath = os.path.join(self.tmpdir, "temp.py")
        with open(filepath, "w") as f:
            f.write("pass")
        self.watcher.refresh_snapshot()
        self.assertIn(filepath, self.watcher._snapshots)
        # Remove the file and refresh
        os.remove(filepath)
        self.watcher.refresh_snapshot()
        self.assertNotIn(filepath, self.watcher._snapshots)


if __name__ == "__main__":
    unittest.main()
