"""
Test suite for persistent memory compatibility and prompt formatting.
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


class TestMemoryCompatibility(unittest.TestCase):
    """Test loading legacy memory data without crashing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.memory_dir = os.path.join(self.test_dir, "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.memory_file = os.path.join(self.memory_dir, "memory.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def write_memory(self, payload):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def test_legacy_text_entries_are_migrated(self):
        self.write_memory([
            {
                "id": "legacy-1",
                "text": "Legacy memory entry",
                "category": "notes",
                "created_at": "2026-03-09T01:00:00",
            }
        ])

        memory = Memory(self.test_dir)

        self.assertEqual(
            memory.list_all(),
            [
                {
                    "content": "Legacy memory entry",
                    "category": "notes",
                    "created": "2026-03-09T01:00:00",
                }
            ],
        )
        with open(self.memory_file, encoding="utf-8") as f:
            stored = json.load(f)
        self.assertEqual(stored, memory.list_all())

    def test_format_for_prompt_skips_invalid_entries(self):
        self.write_memory([
            {"category": "broken"},
            {"text": "Legacy text memory", "category": "compat"},
            "String memory entry",
        ])

        memory = Memory(self.test_dir)
        prompt = memory.format_for_prompt()

        self.assertIn("- [compat] Legacy text memory", prompt)
        self.assertIn("- [general] String memory entry", prompt)
        self.assertNotIn("broken", prompt)


if __name__ == "__main__":
    unittest.main()
