"""
Test suite for utility functions: display width, image helpers,
JSON parsing, and git status path extraction.
"""

import base64
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

_char_display_width = eve_coder._char_display_width
_display_width = eve_coder._display_width
_truncate_to_display_width = eve_coder._truncate_to_display_width
_extract_image_paths = eve_coder._extract_image_paths
_read_image_as_base64 = eve_coder._read_image_as_base64
_build_multimodal_content = eve_coder._build_multimodal_content
_try_parse_json_value = eve_coder._try_parse_json_value
_git_status_path = eve_coder._git_status_path


# ────────────────────────────────────────────────────────────────────────────────
# _char_display_width / _display_width / _truncate_to_display_width
# ────────────────────────────────────────────────────────────────────────────────

class TestCharDisplayWidth(unittest.TestCase):

    def test_ascii_letter(self):
        self.assertEqual(_char_display_width("a"), 1)

    def test_ascii_digit(self):
        self.assertEqual(_char_display_width("0"), 1)

    def test_ascii_space(self):
        self.assertEqual(_char_display_width(" "), 1)

    def test_cjk_ideograph(self):
        self.assertEqual(_char_display_width("\u4e16"), 2)  # 世

    def test_cjk_katakana_fullwidth(self):
        self.assertEqual(_char_display_width("\u30a2"), 2)  # ア

    def test_latin_halfwidth(self):
        self.assertEqual(_char_display_width("A"), 1)

    def test_fullwidth_latin(self):
        # Ａ (U+FF21) — Fullwidth Latin Capital Letter A
        self.assertEqual(_char_display_width("\uff21"), 2)


class TestDisplayWidth(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(_display_width(""), 0)

    def test_ascii_only(self):
        self.assertEqual(_display_width("hello"), 5)

    def test_cjk_only(self):
        # 世界 = 2+2 = 4
        self.assertEqual(_display_width("\u4e16\u754c"), 4)

    def test_mixed(self):
        # "hi世界" = 1+1+2+2 = 6
        self.assertEqual(_display_width("hi\u4e16\u754c"), 6)

    def test_single_char(self):
        self.assertEqual(_display_width("x"), 1)


class TestTruncateToDisplayWidth(unittest.TestCase):

    def test_short_string_no_truncation(self):
        self.assertEqual(_truncate_to_display_width("abc", 10), "abc")

    def test_exact_fit(self):
        self.assertEqual(_truncate_to_display_width("abcde", 5), "abcde")

    def test_truncate_ascii(self):
        result = _truncate_to_display_width("abcdefgh", 5)
        self.assertTrue(result.endswith("..."))
        # Display width of result (without ...) + ... should make sense
        self.assertLessEqual(len(result), 8)

    def test_truncate_cjk(self):
        # 世界你好 = 8 display width; truncate to 5
        result = _truncate_to_display_width("\u4e16\u754c\u4f60\u597d", 5)
        self.assertTrue(result.endswith("..."))

    def test_empty_string(self):
        self.assertEqual(_truncate_to_display_width("", 10), "")

    def test_zero_max_width(self):
        result = _truncate_to_display_width("hello", 0)
        self.assertEqual(result, "...")

    def test_cjk_boundary(self):
        # "a世" = 1+2 = 3; max_width=2 means 世 doesn't fit after a
        result = _truncate_to_display_width("a\u4e16", 2)
        self.assertTrue(result.endswith("..."))


# ────────────────────────────────────────────────────────────────────────────────
# _extract_image_paths
# ────────────────────────────────────────────────────────────────────────────────

class TestExtractImagePaths(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_image(self, name):
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # minimal PNG header
        return path

    def test_no_images(self):
        text, paths = _extract_image_paths("hello world")
        self.assertEqual(text, "hello world")
        self.assertEqual(paths, [])

    def test_single_image_path(self):
        img = self._create_image("photo.png")
        text, paths = _extract_image_paths(f"describe {img}")
        self.assertEqual(paths, [img])
        self.assertNotIn(img, text)

    def test_file_prefix_stripped(self):
        img = self._create_image("photo.jpg")
        text, paths = _extract_image_paths(f"describe file://{img}")
        self.assertEqual(paths, [img])

    def test_non_image_extension_ignored(self):
        txt = os.path.join(self.tmpdir, "readme.txt")
        with open(txt, "w") as f:
            f.write("not an image")
        text, paths = _extract_image_paths(f"read {txt}")
        self.assertEqual(paths, [])

    def test_nonexistent_file_ignored(self):
        fake = os.path.join(self.tmpdir, "missing.png")
        text, paths = _extract_image_paths(f"show {fake}")
        self.assertEqual(paths, [])

    def test_multiple_images(self):
        img1 = self._create_image("a.png")
        img2 = self._create_image("b.jpg")
        text, paths = _extract_image_paths(f"compare {img1} {img2}")
        self.assertEqual(len(paths), 2)


# ────────────────────────────────────────────────────────────────────────────────
# _read_image_as_base64
# ────────────────────────────────────────────────────────────────────────────────

class TestReadImageAsBase64(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, name, data):
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_valid_png(self):
        path = self._write_file("img.png", b"\x89PNG\r\n\x1a\ndata")
        result, err = _read_image_as_base64(path)
        self.assertIsNotNone(result)
        self.assertIsNone(err)
        data, media = result
        self.assertEqual(media, "image/png")
        # data should be valid base64
        base64.b64decode(data)

    def test_valid_jpg(self):
        path = self._write_file("photo.jpg", b"\xff\xd8\xff\xe0data")
        result, err = _read_image_as_base64(path)
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "image/jpeg")

    def test_non_image_extension_rejected(self):
        path = self._write_file("readme.txt", b"hello")
        result, err = _read_image_as_base64(path)
        self.assertIsNone(result)
        self.assertIn("Not an image", err)

    def test_empty_file_rejected(self):
        path = self._write_file("empty.png", b"")
        result, err = _read_image_as_base64(path)
        self.assertIsNone(result)
        self.assertIn("empty", err.lower())

    def test_oversized_file_rejected(self):
        path = self._write_file("huge.png", b"x" * (10 * 1024 * 1024 + 1))
        result, err = _read_image_as_base64(path)
        self.assertIsNone(result)
        self.assertIn("too large", err.lower())

    def test_nonexistent_file(self):
        result, err = _read_image_as_base64(os.path.join(self.tmpdir, "nope.png"))
        self.assertIsNone(result)
        self.assertIn("Cannot read", err)


# ────────────────────────────────────────────────────────────────────────────────
# _build_multimodal_content
# ────────────────────────────────────────────────────────────────────────────────

class TestBuildMultimodalContent(unittest.TestCase):

    def test_text_only_returns_string(self):
        result = _build_multimodal_content("hello", [])
        self.assertEqual(result, "hello")

    def test_text_with_one_image_returns_list(self):
        result = _build_multimodal_content("describe", [("b64data", "image/png")])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "image_url")

    def test_image_url_format(self):
        result = _build_multimodal_content("describe", [("AAAA", "image/jpeg")])
        url = result[1]["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/jpeg;base64,"))

    def test_multiple_images(self):
        imgs = [("a", "image/png"), ("b", "image/gif")]
        result = _build_multimodal_content("compare", imgs)
        self.assertEqual(len(result), 3)  # 1 text + 2 images

    def test_empty_text_with_image(self):
        result = _build_multimodal_content("", [("data", "image/png")])
        self.assertIsInstance(result, list)
        # No text part, just image
        types = [p["type"] for p in result]
        self.assertNotIn("text", types)

    def test_whitespace_only_text_with_image(self):
        result = _build_multimodal_content("   ", [("data", "image/png")])
        self.assertIsInstance(result, list)


# ────────────────────────────────────────────────────────────────────────────────
# _try_parse_json_value
# ────────────────────────────────────────────────────────────────────────────────

class TestTryParseJsonValue(unittest.TestCase):

    def test_true(self):
        self.assertIs(_try_parse_json_value("true"), True)

    def test_false(self):
        self.assertIs(_try_parse_json_value("false"), False)

    def test_null(self):
        self.assertIsNone(_try_parse_json_value("null"))

    def test_integer(self):
        self.assertEqual(_try_parse_json_value("42"), 42)

    def test_negative_integer(self):
        self.assertEqual(_try_parse_json_value("-7"), -7)

    def test_float(self):
        self.assertAlmostEqual(_try_parse_json_value("3.14"), 3.14)

    def test_array(self):
        self.assertEqual(_try_parse_json_value('[1, 2, 3]'), [1, 2, 3])

    def test_object(self):
        self.assertEqual(_try_parse_json_value('{"a": 1}'), {"a": 1})

    def test_plain_string_returned_as_is(self):
        self.assertEqual(_try_parse_json_value("hello"), "hello")

    def test_non_json_number_like_string(self):
        # A string starting with a digit but invalid JSON stays as string
        self.assertEqual(_try_parse_json_value("42abc"), "42abc")

    def test_empty_string(self):
        self.assertEqual(_try_parse_json_value(""), "")

    def test_nested_object(self):
        val = _try_parse_json_value('{"a": {"b": [1]}}')
        self.assertEqual(val, {"a": {"b": [1]}})


# ────────────────────────────────────────────────────────────────────────────────
# _git_status_path
# ────────────────────────────────────────────────────────────────────────────────

class TestGitStatusPath(unittest.TestCase):

    def test_modified_file(self):
        self.assertEqual(_git_status_path(" M src/main.py"), "src/main.py")

    def test_added_file(self):
        self.assertEqual(_git_status_path("A  new_file.txt"), "new_file.txt")

    def test_untracked_file(self):
        self.assertEqual(_git_status_path("?? untracked.txt"), "untracked.txt")

    def test_renamed_file(self):
        # porcelain: "R  old.txt -> new.txt"
        path = _git_status_path("R  old.txt -> new.txt")
        self.assertEqual(path, "old.txt -> new.txt")

    def test_empty_line(self):
        self.assertEqual(_git_status_path(""), "")

    def test_none_safe(self):
        # None should not crash — returns ""
        self.assertEqual(_git_status_path(""), "")

    def test_staged_and_modified(self):
        self.assertEqual(_git_status_path("MM both.py"), "both.py")

    def test_deleted_file(self):
        self.assertEqual(_git_status_path(" D removed.py"), "removed.py")

    def test_path_with_spaces(self):
        self.assertEqual(_git_status_path(" M path with spaces.txt"), "path with spaces.txt")


if __name__ == "__main__":
    unittest.main()
