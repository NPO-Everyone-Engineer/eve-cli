import importlib.util
import os
import sys
import threading
import time
import unittest
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)


class TestTypeAheadQueue(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_queue_completed_and_partial_input(self):
        self.tui.queue_typeahead_bytes(b"hello\nwor")
        self.assertEqual(self.tui.dequeue_typeahead_input(), "hello")
        self.assertIsNone(self.tui.dequeue_typeahead_input())
        self.assertEqual(self.tui.consume_typeahead_prefill(), "wor")
        self.assertEqual(self.tui.consume_typeahead_prefill(), "")

    def test_queue_backspace(self):
        self.tui.queue_typeahead_bytes(b"hel\x7flo\n")
        self.assertEqual(self.tui.dequeue_typeahead_input(), "helo")


class TestReadWriteLock(unittest.TestCase):
    def test_multiple_readers_can_run_together(self):
        lock = eve_coder.ReadWriteLock()
        state = {"count": 0, "peak": 0}
        gate = threading.Event()

        def reader():
            with lock.read():
                state["count"] += 1
                state["peak"] = max(state["peak"], state["count"])
                gate.wait(0.2)
                state["count"] -= 1

        threads = [threading.Thread(target=reader) for _ in range(2)]
        for t in threads:
            t.start()
        time.sleep(0.05)
        gate.set()
        for t in threads:
            t.join()
        self.assertGreaterEqual(state["peak"], 2)

    def test_writer_waits_for_reader(self):
        lock = eve_coder.ReadWriteLock()
        events = []
        gate = threading.Event()

        def reader():
            with lock.read():
                events.append("reader-start")
                gate.wait(0.2)
                events.append("reader-end")

        def writer():
            with lock.write():
                events.append("writer")

        rt = threading.Thread(target=reader)
        wt = threading.Thread(target=writer)
        rt.start()
        time.sleep(0.05)
        wt.start()
        time.sleep(0.05)
        gate.set()
        rt.join()
        wt.join()
        self.assertEqual(events, ["reader-start", "reader-end", "writer"])


class TestThinkingDisplay(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_show_sync_response_renders_native_thinking_without_polluting_text(self):
        data = {
            "choices": [{
                "message": {
                    "thinking": "inspect files\ncompare outputs",
                    "content": "Visible answer",
                }
            }]
        }

        with patch.object(self.tui, "_scroll_print") as mock_print, \
             patch.object(self.tui, "_render_markdown") as mock_render:
            text, tool_calls, had_thinking = self.tui.show_sync_response(data)

        printed = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
        self.assertTrue(had_thinking)
        self.assertEqual(text, "Visible answer")
        self.assertEqual(tool_calls, [])
        self.assertIn("Thinking", printed)
        self.assertIn("inspect files", printed)
        mock_render.assert_called_once_with("Visible answer")


class TestInputPrompts(unittest.TestCase):
    def setUp(self):
        self.tui = eve_coder.TUI(eve_coder.Config())

    def test_multiline_continuation_prompts_avoid_ansi_sequences(self):
        prompts = []
        responses = iter(["first line", "second line", ""])

        def fake_input(prompt=""):
            prompts.append(prompt)
            return next(responses)

        with patch.object(self.tui, "show_input_separator"), \
             patch("builtins.input", side_effect=fake_input):
            result = self.tui.get_multiline_input()

        self.assertEqual(result, "first line\nsecond line")
        self.assertEqual(prompts, ["> ", "... ", "... "])
        self.assertTrue(all("\x1b" not in prompt for prompt in prompts))

    def test_stream_response_renders_native_thinking_without_polluting_text(self):
        chunks = iter([
            {"choices": [{"delta": {"thinking": "inspect files\ncompare outputs"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": "Visible answer"}, "finish_reason": None}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
        ])

        with patch.object(self.tui, "_scroll_print") as mock_print:
            text, tool_calls, had_thinking = self.tui.stream_response(chunks)

        printed = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
        self.assertTrue(had_thinking)
        self.assertEqual(text, "Visible answer")
        self.assertEqual(tool_calls, [])
        self.assertIn("Thinking", printed)
        self.assertIn("inspect files", printed)


if __name__ == "__main__":
    unittest.main()
