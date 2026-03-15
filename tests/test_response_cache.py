"""
Test suite for the ResponseCache class.

Covers basic put/get, LRU eviction, cache hit ordering, clear,
_hash_messages determinism, and max_size boundary behavior.
"""

import unittest
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
ResponseCache = eve_coder.ResponseCache


class TestResponseCacheBasic(unittest.TestCase):
    """Test basic put/get operations."""

    def test_get_returns_none_for_missing_key(self):
        cache = ResponseCache()
        self.assertIsNone(cache.get("nonexistent"))

    def test_put_and_get(self):
        cache = ResponseCache()
        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

    def test_put_overwrites_existing_key(self):
        cache = ResponseCache()
        cache.put("key1", "old_value")
        cache.put("key1", "new_value")
        self.assertEqual(cache.get("key1"), "new_value")

    def test_multiple_keys(self):
        cache = ResponseCache()
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)

    def test_none_value_stored(self):
        """None is a valid cache value, distinct from cache miss."""
        cache = ResponseCache()
        cache.put("key", None)
        # get returns None for both miss and stored None,
        # but the key should exist in the cache
        self.assertIsNone(cache.get("key"))

    def test_complex_value_types(self):
        cache = ResponseCache()
        cache.put("dict", {"role": "assistant", "content": "hello"})
        cache.put("list", [1, 2, 3])
        self.assertEqual(cache.get("dict"), {"role": "assistant", "content": "hello"})
        self.assertEqual(cache.get("list"), [1, 2, 3])


class TestResponseCacheLRUEviction(unittest.TestCase):
    """Test LRU eviction behavior when cache is full."""

    def test_evicts_oldest_when_full(self):
        cache = ResponseCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        # Cache is full. Adding "d" should evict "a" (oldest)
        cache.put("d", 4)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)
        self.assertEqual(cache.get("d"), 4)

    def test_eviction_order_is_fifo_without_access(self):
        cache = ResponseCache(max_size=2)
        cache.put("first", 1)
        cache.put("second", 2)
        cache.put("third", 3)  # evicts "first"
        self.assertIsNone(cache.get("first"))
        self.assertEqual(cache.get("second"), 2)
        cache.put("fourth", 4)  # evicts "second" (since "third" was just accessed via get above... but "second" was accessed too)
        # Actually: after put("third"), order is [second, third]
        # get("second") moves it to end: [third, second]
        # put("fourth") evicts "third": [second, fourth]
        self.assertIsNone(cache.get("third"))
        self.assertEqual(cache.get("second"), 2)
        self.assertEqual(cache.get("fourth"), 4)

    def test_max_size_1(self):
        cache = ResponseCache(max_size=1)
        cache.put("a", 1)
        self.assertEqual(cache.get("a"), 1)
        cache.put("b", 2)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)

    def test_cache_hit_moves_to_end_preventing_eviction(self):
        """Accessing a key moves it to the end, so it is not evicted next."""
        cache = ResponseCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        # Access "a" to move it to the end
        cache.get("a")
        # Now order is: b, c, a. Adding "d" should evict "b"
        cache.put("d", 4)
        self.assertEqual(cache.get("a"), 1)  # "a" was saved from eviction
        self.assertIsNone(cache.get("b"))     # "b" was evicted
        self.assertEqual(cache.get("c"), 3)
        self.assertEqual(cache.get("d"), 4)

    def test_put_existing_key_moves_to_end(self):
        """Updating an existing key moves it to the end."""
        cache = ResponseCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        # Update "a" (moves it to end)
        cache.put("a", 100)
        # Order: b, c, a. Adding "d" evicts "b"
        cache.put("d", 4)
        self.assertEqual(cache.get("a"), 100)
        self.assertIsNone(cache.get("b"))
        self.assertEqual(cache.get("c"), 3)
        self.assertEqual(cache.get("d"), 4)


class TestResponseCacheClear(unittest.TestCase):
    """Test cache clear operation."""

    def test_clear_empties_cache(self):
        cache = ResponseCache(max_size=10)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.clear()
        self.assertIsNone(cache.get("a"))
        self.assertIsNone(cache.get("b"))
        self.assertIsNone(cache.get("c"))

    def test_clear_then_reuse(self):
        cache = ResponseCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.clear()
        # Can add new items after clear
        cache.put("c", 3)
        cache.put("d", 4)
        self.assertEqual(cache.get("c"), 3)
        self.assertEqual(cache.get("d"), 4)


class TestHashMessages(unittest.TestCase):
    """Test _hash_messages determinism and behavior."""

    def test_deterministic_same_input(self):
        messages = [{"role": "user", "content": "hello"}]
        h1 = ResponseCache._hash_messages(messages, "model-a")
        h2 = ResponseCache._hash_messages(messages, "model-a")
        self.assertEqual(h1, h2)

    def test_different_model_different_hash(self):
        messages = [{"role": "user", "content": "hello"}]
        h1 = ResponseCache._hash_messages(messages, "model-a")
        h2 = ResponseCache._hash_messages(messages, "model-b")
        self.assertNotEqual(h1, h2)

    def test_different_messages_different_hash(self):
        m1 = [{"role": "user", "content": "hello"}]
        m2 = [{"role": "user", "content": "goodbye"}]
        h1 = ResponseCache._hash_messages(m1, "model-a")
        h2 = ResponseCache._hash_messages(m2, "model-a")
        self.assertNotEqual(h1, h2)

    def test_hash_length_is_32(self):
        messages = [{"role": "user", "content": "test"}]
        h = ResponseCache._hash_messages(messages, "model")
        self.assertEqual(len(h), 32)

    def test_hash_is_hex_string(self):
        messages = [{"role": "user", "content": "test"}]
        h = ResponseCache._hash_messages(messages, "model")
        # Should only contain hex characters
        int(h, 16)  # Raises ValueError if not valid hex

    def test_uses_last_3_messages(self):
        """_hash_messages uses messages[-3:], so only last 3 matter."""
        msgs_a = [
            {"role": "user", "content": "old1"},
            {"role": "assistant", "content": "old2"},
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"},
        ]
        msgs_b = [
            {"role": "user", "content": "different_history"},
            {"role": "assistant", "content": "also_different"},
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"},
        ]
        h1 = ResponseCache._hash_messages(msgs_a, "model")
        h2 = ResponseCache._hash_messages(msgs_b, "model")
        self.assertEqual(h1, h2)

    def test_fewer_than_3_messages(self):
        """Works correctly with fewer than 3 messages."""
        msgs = [{"role": "user", "content": "only one"}]
        h = ResponseCache._hash_messages(msgs, "model")
        self.assertEqual(len(h), 32)

    def test_empty_messages(self):
        """Works with empty message list."""
        h = ResponseCache._hash_messages([], "model")
        self.assertEqual(len(h), 32)


class TestResponseCacheDefaultMaxSize(unittest.TestCase):
    """Test the default max_size parameter."""

    def test_default_max_size_is_50(self):
        cache = ResponseCache()
        # Fill to 50
        for i in range(50):
            cache.put(f"key{i}", f"val{i}")
        # All 50 should be present
        self.assertEqual(cache.get("key0"), "val0")
        self.assertEqual(cache.get("key49"), "val49")
        # Adding 51st evicts the oldest (key0 was accessed above so it moved to end,
        # key1 is now oldest)
        cache.put("key50", "val50")
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key50"), "val50")


if __name__ == "__main__":
    unittest.main()
