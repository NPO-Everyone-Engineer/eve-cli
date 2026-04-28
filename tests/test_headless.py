"""
Test suite for HeadlessOutputCollector: session_start / done events,
token usage accumulation, stop_reason propagation, and stream-json line emission.
"""

import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

HeadlessOutputCollector = eve_coder.HeadlessOutputCollector


class TestHeadlessOutputCollectorJsonMode(unittest.TestCase):
    def setUp(self):
        self.collector = HeadlessOutputCollector(
            output_format="json",
            model="test-model:cloud",
            session_id="sess123",
        )

    def test_session_start_is_idempotent(self):
        self.collector.session_start(prompt="hello world")
        self.collector.session_start(prompt="should be ignored")
        starts = [e for e in self.collector._events if e["type"] == "session_start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0]["prompt"], "hello world")
        self.assertEqual(starts[0]["model"], "test-model:cloud")
        self.assertEqual(starts[0]["session_id"], "sess123")

    def test_record_usage_accumulates(self):
        self.collector.record_usage(100, 50)
        self.collector.record_usage(20, 10)
        self.collector.record_usage(None, "garbage")  # ignored cleanly
        self.assertEqual(self.collector._prompt_tokens, 120)
        self.assertEqual(self.collector._completion_tokens, 60)

    def test_done_records_stop_reason_and_token_usage(self):
        self.collector.record_usage(200, 80)
        self.collector.done(stop_reason="max_iterations", stop_detail="80 turns", exit_code=2)
        summary = self.collector.get_summary()
        self.assertEqual(summary["stop_reason"], "max_iterations")
        self.assertEqual(summary["stop_detail"], "80 turns")
        self.assertEqual(summary["token_usage"]["input"], 200)
        self.assertEqual(summary["token_usage"]["output"], 80)
        self.assertEqual(summary["token_usage"]["total"], 280)
        self.assertGreaterEqual(summary["duration_ms"], 0)
        self.assertEqual(summary["events"][-1]["type"], "done")

    def test_get_summary_default_stop_reason_is_completed(self):
        summary = self.collector.get_summary()
        self.assertEqual(summary["stop_reason"], "completed")
        self.assertEqual(summary["token_usage"]["total"], 0)

    def test_json_mode_does_not_emit_per_event_lines(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.collector.session_start(prompt="hi")
            self.collector.tool_call("Bash", {"command": "ls"})
            self.collector.tool_result("Bash", "file.txt", is_error=False)
            self.collector.assistant_text("done")
            self.collector.done(stop_reason="completed", exit_code=0)
        # In json mode, events accumulate but nothing is flushed mid-run.
        self.assertEqual(buf.getvalue(), "")


class TestHeadlessOutputCollectorStreamMode(unittest.TestCase):
    def setUp(self):
        self.collector = HeadlessOutputCollector(
            output_format="stream-json",
            model="test-model:cloud",
            session_id="streamsess",
        )

    def test_stream_mode_emits_session_start_and_done_lines(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.collector.session_start(prompt="run me")
            self.collector.tool_call("Read", {"path": "file.py"})
            self.collector.tool_result("Read", "contents", is_error=False)
            self.collector.assistant_text("ok")
            self.collector.done(stop_reason="completed", exit_code=0)

        lines = [json.loads(line) for line in buf.getvalue().strip().splitlines()]
        types = [e["type"] for e in lines]
        self.assertEqual(types[0], "session_start")
        self.assertEqual(types[-1], "done")
        self.assertIn("tool_call", types)
        self.assertIn("tool_result", types)
        self.assertIn("assistant", types)

        done_event = lines[-1]
        self.assertEqual(done_event["stop_reason"], "completed")
        self.assertEqual(done_event["exit_code"], 0)
        self.assertIn("token_usage", done_event)
        self.assertIn("duration_ms", done_event)


if __name__ == "__main__":
    unittest.main()
