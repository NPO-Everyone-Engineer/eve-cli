"""
Test suite for GitChangeTracker and _git_status_path.
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
GitChangeTracker = eve_coder.GitChangeTracker
_git_status_path = eve_coder._git_status_path


class TestGitStatusPath(unittest.TestCase):
    """Tests for _git_status_path helper function."""

    def test_modified_staged(self):
        """Modified and staged: 'M  file.py' -> 'file.py'."""
        self.assertEqual(_git_status_path("M  file.py"), "file.py")

    def test_modified_unstaged(self):
        """Modified but unstaged: ' M file.py' -> 'file.py'."""
        self.assertEqual(_git_status_path(" M file.py"), "file.py")

    def test_untracked(self):
        """Untracked file: '?? newfile.py' -> 'newfile.py'."""
        self.assertEqual(_git_status_path("?? newfile.py"), "newfile.py")

    def test_renamed(self):
        """Renamed file: 'R  old -> new' -> 'old -> new'."""
        self.assertEqual(_git_status_path("R  old -> new"), "old -> new")

    def test_empty_string(self):
        """Empty string returns empty string."""
        self.assertEqual(_git_status_path(""), "")

    def test_added(self):
        """Added file: 'A  new.py' -> 'new.py'."""
        self.assertEqual(_git_status_path("A  new.py"), "new.py")

    def test_deleted(self):
        """Deleted file: 'D  removed.py' -> 'removed.py'."""
        self.assertEqual(_git_status_path("D  removed.py"), "removed.py")

    def test_path_with_directory(self):
        """File in subdirectory: 'M  src/main.py' -> 'src/main.py'."""
        self.assertEqual(_git_status_path("M  src/main.py"), "src/main.py")

    def test_both_staged_and_unstaged(self):
        """Both staged and unstaged changes: 'MM file.py' -> 'file.py'."""
        self.assertEqual(_git_status_path("MM file.py"), "file.py")


class TestGitChangeTrackerInit(unittest.TestCase):
    """Tests for GitChangeTracker initialization."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_without_git_dir(self):
        """Without .git directory, _is_git_repo is False."""
        tracker = GitChangeTracker(self.tmpdir)
        self.assertFalse(tracker._is_git_repo)
        self.assertEqual(tracker._events, [])

    def test_init_with_git_dir(self):
        """With .git directory, _is_git_repo is True."""
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        tracker = GitChangeTracker(self.tmpdir)
        self.assertTrue(tracker._is_git_repo)

    def test_max_events_constant(self):
        """MAX_EVENTS should be 100."""
        self.assertEqual(GitChangeTracker.MAX_EVENTS, 100)


class TestGitChangeTrackerRecord(unittest.TestCase):
    """Tests for GitChangeTracker.record method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_single_event(self):
        """Record a single event and verify it's stored."""
        filepath = os.path.join(self.tmpdir, "test.py")
        self.tracker.record("create", filepath)
        events = self.tracker.recent_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "create")
        self.assertEqual(events[0][1], "test.py")

    def test_record_multiple_events(self):
        """Record multiple events and retrieve them."""
        for i in range(3):
            filepath = os.path.join(self.tmpdir, f"file{i}.py")
            self.tracker.record("edit", filepath)
        events = self.tracker.recent_events(limit=10)
        self.assertEqual(len(events), 3)

    def test_record_stores_timestamp(self):
        """Each recorded event has a timestamp."""
        before = time.time()
        filepath = os.path.join(self.tmpdir, "test.py")
        self.tracker.record("create", filepath)
        after = time.time()
        events = self.tracker.recent_events(limit=10)
        self.assertGreaterEqual(events[0][2], before)
        self.assertLessEqual(events[0][2], after)


class TestGitChangeTrackerRecentEvents(unittest.TestCase):
    """Tests for GitChangeTracker.recent_events method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_recent_events_deduplicates_by_path(self):
        """Duplicate paths should be deduplicated, keeping newest."""
        filepath = os.path.join(self.tmpdir, "test.py")
        self.tracker.record("create", filepath)
        time.sleep(0.01)
        self.tracker.record("edit", filepath)
        events = self.tracker.recent_events(limit=10)
        self.assertEqual(len(events), 1)
        # Newest action should win
        self.assertEqual(events[0][0], "edit")

    def test_recent_events_respects_limit(self):
        """Limit parameter should cap the returned events."""
        for i in range(10):
            filepath = os.path.join(self.tmpdir, f"file{i}.py")
            self.tracker.record("edit", filepath)
        events = self.tracker.recent_events(limit=3)
        self.assertEqual(len(events), 3)

    def test_recent_events_newest_first(self):
        """Events should be returned newest first."""
        for i in range(3):
            filepath = os.path.join(self.tmpdir, f"file{i}.py")
            self.tracker.record("edit", filepath)
            time.sleep(0.01)
        events = self.tracker.recent_events(limit=10)
        self.assertEqual(events[0][1], "file2.py")
        self.assertEqual(events[1][1], "file1.py")
        self.assertEqual(events[2][1], "file0.py")

    def test_recent_events_empty(self):
        """No events recorded should return empty list."""
        events = self.tracker.recent_events()
        self.assertEqual(events, [])

    def test_default_limit_is_five(self):
        """Default limit should be 5."""
        for i in range(10):
            filepath = os.path.join(self.tmpdir, f"file{i}.py")
            self.tracker.record("edit", filepath)
        events = self.tracker.recent_events()
        self.assertEqual(len(events), 5)


class TestGitChangeTrackerMaxEvents(unittest.TestCase):
    """Tests for MAX_EVENTS cap on GitChangeTracker."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_max_events_cap(self):
        """Events list is trimmed when exceeding MAX_EVENTS (100)."""
        for i in range(150):
            filepath = os.path.join(self.tmpdir, f"file{i}.py")
            self.tracker.record("edit", filepath)
        # Internal events list should not exceed MAX_EVENTS
        self.assertLessEqual(len(self.tracker._events), GitChangeTracker.MAX_EVENTS)

    def test_max_events_keeps_newest(self):
        """After trimming, the newest events are preserved."""
        for i in range(150):
            filepath = os.path.join(self.tmpdir, f"file{i:04d}.py")
            self.tracker.record("edit", filepath)
        # The last recorded file should be in events
        events = self.tracker.recent_events(limit=1)
        self.assertEqual(events[0][1], "file0149.py")


class TestGitChangeTrackerFormatRecent(unittest.TestCase):
    """Tests for GitChangeTracker.format_recent method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_format_create_icon(self):
        """Create action should use '+' icon."""
        filepath = os.path.join(self.tmpdir, "new.py")
        self.tracker.record("create", filepath)
        lines = self.tracker.format_recent()
        self.assertTrue(lines[0].startswith("+ "))
        self.assertIn("(create)", lines[0])

    def test_format_write_icon(self):
        """Write action should use '~' icon."""
        filepath = os.path.join(self.tmpdir, "mod.py")
        self.tracker.record("write", filepath)
        lines = self.tracker.format_recent()
        self.assertTrue(lines[0].startswith("~ "))
        self.assertIn("(write)", lines[0])

    def test_format_edit_icon(self):
        """Edit action should use '~' icon."""
        filepath = os.path.join(self.tmpdir, "edit.py")
        self.tracker.record("edit", filepath)
        lines = self.tracker.format_recent()
        self.assertTrue(lines[0].startswith("~ "))
        self.assertIn("(edit)", lines[0])

    def test_format_delete_icon(self):
        """Delete action should use '-' icon."""
        filepath = os.path.join(self.tmpdir, "del.py")
        self.tracker.record("delete", filepath)
        lines = self.tracker.format_recent()
        self.assertTrue(lines[0].startswith("- "))
        self.assertIn("(delete)", lines[0])

    def test_format_unknown_action_defaults_to_tilde(self):
        """Unknown action should default to '~' icon."""
        filepath = os.path.join(self.tmpdir, "unk.py")
        self.tracker.record("unknown_action", filepath)
        lines = self.tracker.format_recent()
        self.assertTrue(lines[0].startswith("~ "))

    def test_format_empty(self):
        """No events should return empty list."""
        lines = self.tracker.format_recent()
        self.assertEqual(lines, [])


class TestGitChangeTrackerRelpath(unittest.TestCase):
    """Tests for GitChangeTracker._relpath method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_relpath_within_cwd(self):
        """File inside cwd returns relative path."""
        filepath = os.path.join(self.tmpdir, "subdir", "file.py")
        relpath = self.tracker._relpath(filepath)
        expected = os.path.join("subdir", "file.py")
        self.assertEqual(relpath, expected)

    def test_relpath_outside_cwd(self):
        """File outside cwd returns original path."""
        filepath = "/some/other/path/file.py"
        relpath = self.tracker._relpath(filepath)
        self.assertEqual(relpath, filepath)


class TestGitChangeTrackerGitDirtySummary(unittest.TestCase):
    """Tests for GitChangeTracker.git_dirty_summary method."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # No .git directory — not a real git repo
        self.tracker = GitChangeTracker(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_git_dirty_summary_not_git_repo(self):
        """Returns None if not a git repo (no .git dir)."""
        result = self.tracker.git_dirty_summary()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
