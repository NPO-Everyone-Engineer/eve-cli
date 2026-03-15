"""
Test suite for Memory class: add, remove, search, format, normalization,
persistence, limits, and deduplication.
"""

import importlib.util
import json
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

Memory = eve_coder.Memory


class TestMemoryInit(unittest.TestCase):
    """Tests for Memory creation and directory setup."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_memory_directory(self):
        mem = Memory(self.tmpdir)
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, "memory")))

    def test_empty_on_creation(self):
        mem = Memory(self.tmpdir)
        self.assertEqual(mem.list_all(), [])

    def test_memory_file_path(self):
        mem = Memory(self.tmpdir)
        expected = os.path.join(self.tmpdir, "memory", "memory.json")
        self.assertEqual(mem._file, expected)


class TestMemoryAddAndList(unittest.TestCase):
    """Tests for add() and list_all()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_single_entry(self):
        self.mem.add("test entry")
        entries = self.mem.list_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"], "test entry")
        self.assertEqual(entries[0]["category"], "general")
        self.assertIn("created", entries[0])

    def test_add_with_category(self):
        self.mem.add("project note", category="project")
        entries = self.mem.list_all()
        self.assertEqual(entries[0]["category"], "project")

    def test_add_multiple_entries(self):
        self.mem.add("first")
        self.mem.add("second")
        self.mem.add("third")
        entries = self.mem.list_all()
        self.assertEqual(len(entries), 3)

    def test_duplicate_prevention(self):
        self.mem.add("same content")
        self.mem.add("same content")
        entries = self.mem.list_all()
        self.assertEqual(len(entries), 1)

    def test_duplicate_prevention_different_category(self):
        """Same content with different category is still deduplicated."""
        self.mem.add("same content", category="a")
        self.mem.add("same content", category="b")
        entries = self.mem.list_all()
        self.assertEqual(len(entries), 1)


class TestMemoryRemove(unittest.TestCase):
    """Tests for remove()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_remove_valid_index(self):
        self.mem.add("entry0")
        self.mem.add("entry1")
        result = self.mem.remove(0)
        self.assertTrue(result)
        entries = self.mem.list_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"], "entry1")

    def test_remove_invalid_negative_index(self):
        self.mem.add("entry")
        result = self.mem.remove(-1)
        self.assertFalse(result)
        self.assertEqual(len(self.mem.list_all()), 1)

    def test_remove_invalid_too_large_index(self):
        self.mem.add("entry")
        result = self.mem.remove(5)
        self.assertFalse(result)
        self.assertEqual(len(self.mem.list_all()), 1)

    def test_remove_from_empty(self):
        result = self.mem.remove(0)
        self.assertFalse(result)


class TestMemorySearch(unittest.TestCase):
    """Tests for search()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mem = Memory(self.tmpdir)
        self.mem.add("Python project setup")
        self.mem.add("JavaScript frontend")
        self.mem.add("python testing guide")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_search_finds_matching(self):
        results = self.mem.search("python")
        self.assertEqual(len(results), 2)

    def test_search_case_insensitive(self):
        results = self.mem.search("PYTHON")
        self.assertEqual(len(results), 2)

    def test_search_no_match(self):
        results = self.mem.search("Rust")
        self.assertEqual(len(results), 0)

    def test_search_partial_match(self):
        results = self.mem.search("front")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "JavaScript frontend")


class TestMemoryFormatForPrompt(unittest.TestCase):
    """Tests for format_for_prompt()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_returns_empty_string(self):
        self.assertEqual(self.mem.format_for_prompt(), "")

    def test_format_contains_header(self):
        self.mem.add("test entry")
        output = self.mem.format_for_prompt()
        self.assertIn("# Persistent Memory", output)

    def test_format_contains_entry(self):
        self.mem.add("my project note", category="project")
        output = self.mem.format_for_prompt()
        self.assertIn("[project]", output)
        self.assertIn("my project note", output)

    def test_format_truncation_by_max_chars(self):
        for i in range(50):
            self.mem.add(f"entry number {i} with some filler text to make it long enough")
        output = self.mem.format_for_prompt(max_chars=200)
        # Output should be truncated to roughly max_chars
        # It includes the header, so we give some slack
        self.assertLess(len(output), 400)

    def test_format_most_recent_first(self):
        """format_for_prompt iterates in reverse but reverses back, so most
        recent entries should still appear (they are checked first for budget)."""
        self.mem.add("old entry")
        self.mem.add("new entry")
        output = self.mem.format_for_prompt(max_chars=5000)
        self.assertIn("old entry", output)
        self.assertIn("new entry", output)


class TestMemoryLimits(unittest.TestCase):
    """Tests for MAX_ENTRIES and MAX_ENTRY_SIZE."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_max_entries_limit(self):
        for i in range(Memory.MAX_ENTRIES + 20):
            self.mem.add(f"entry {i}")
        entries = self.mem.list_all()
        self.assertLessEqual(len(entries), Memory.MAX_ENTRIES)

    def test_max_entry_size_truncation(self):
        long_content = "x" * (Memory.MAX_ENTRY_SIZE + 100)
        self.mem.add(long_content)
        entries = self.mem.list_all()
        self.assertLessEqual(len(entries[0]["content"]), Memory.MAX_ENTRY_SIZE)


class TestMemoryNormalizeEntry(unittest.TestCase):
    """Tests for _normalize_entry()."""

    def test_normalize_from_string(self):
        result = Memory._normalize_entry("hello world")
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "hello world")
        self.assertEqual(result["category"], "general")

    def test_normalize_from_dict_with_content(self):
        result = Memory._normalize_entry({"content": "test", "category": "notes"})
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "test")
        self.assertEqual(result["category"], "notes")

    def test_normalize_from_dict_with_text_fallback(self):
        result = Memory._normalize_entry({"text": "legacy entry"})
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "legacy entry")

    def test_normalize_from_dict_missing_content_and_text(self):
        result = Memory._normalize_entry({"category": "notes"})
        self.assertIsNone(result)

    def test_normalize_from_non_string_non_dict(self):
        result = Memory._normalize_entry(42)
        self.assertIsNone(result)

    def test_normalize_from_list(self):
        result = Memory._normalize_entry(["a", "b"])
        self.assertIsNone(result)

    def test_normalize_truncates_long_content(self):
        long_str = "z" * (Memory.MAX_ENTRY_SIZE + 50)
        result = Memory._normalize_entry(long_str)
        self.assertEqual(len(result["content"]), Memory.MAX_ENTRY_SIZE)

    def test_normalize_preserves_created(self):
        result = Memory._normalize_entry({
            "content": "test",
            "created": "2026-01-01T00:00:00",
        })
        self.assertEqual(result["created"], "2026-01-01T00:00:00")

    def test_normalize_created_at_fallback(self):
        result = Memory._normalize_entry({
            "content": "test",
            "created_at": "2026-02-01T00:00:00",
        })
        self.assertEqual(result.get("created"), "2026-02-01T00:00:00")


class TestMemoryPersistence(unittest.TestCase):
    """Tests for save/load cycle across Memory instances."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_persistence_across_instances(self):
        mem1 = Memory(self.tmpdir)
        mem1.add("persisted entry")
        # Create a new instance pointing to the same directory
        mem2 = Memory(self.tmpdir)
        entries = mem2.list_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"], "persisted entry")

    def test_persistence_after_remove(self):
        mem1 = Memory(self.tmpdir)
        mem1.add("keep")
        mem1.add("remove")
        mem1.remove(1)
        mem2 = Memory(self.tmpdir)
        entries = mem2.list_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"], "keep")

    def test_symlink_memory_file_skipped(self):
        """If memory.json is a symlink, it should not be loaded."""
        mem_dir = os.path.join(self.tmpdir, "memory")
        os.makedirs(mem_dir, exist_ok=True)
        real_file = os.path.join(self.tmpdir, "real_memory.json")
        with open(real_file, "w", encoding="utf-8") as f:
            json.dump([{"content": "should not load", "category": "general"}], f)
        link_file = os.path.join(mem_dir, "memory.json")
        os.symlink(real_file, link_file)
        mem = Memory(self.tmpdir)
        self.assertEqual(mem.list_all(), [])

    def test_corrupted_file_handled_gracefully(self):
        mem_dir = os.path.join(self.tmpdir, "memory")
        os.makedirs(mem_dir, exist_ok=True)
        mem_file = os.path.join(mem_dir, "memory.json")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("{invalid json[")
        mem = Memory(self.tmpdir)
        self.assertEqual(mem.list_all(), [])


if __name__ == "__main__":
    unittest.main()
