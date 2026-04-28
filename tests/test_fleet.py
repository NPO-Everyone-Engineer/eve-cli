"""
Test suite for FleetOrchestrator: decompose response parsing,
blockedBy index translation, dependency-aware dispatch, synthesis on/off,
and end-to-end run flow with a fake client + fake SubAgentTool.
"""

import importlib.util
import json
import os
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

FleetOrchestrator = eve_coder.FleetOrchestrator


def _reset_task_store():
    with eve_coder._task_store_lock:
        eve_coder._task_store["next_id"] = 1
        eve_coder._task_store["tasks"] = {}


class TestParseDecomposeResponse(unittest.TestCase):
    def test_array_inside_prose(self):
        content = (
            "Here are the tasks:\n"
            '[{"subject":"a","description":"do a","blockedBy":[]},'
            '{"subject":"b","description":"do b","blockedBy":[1]}]\n'
            "End of array."
        )
        out = FleetOrchestrator._parse_decompose_response(content)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[1]["blockedBy"], [1])

    def test_drops_entries_without_subject(self):
        content = '[{"subject":""},{"subject":"ok","description":"d"}]'
        out = FleetOrchestrator._parse_decompose_response(content)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["subject"], "ok")

    def test_coerces_non_int_blocked_by(self):
        content = '[{"subject":"a","blockedBy":["x",2,"3"]}]'
        out = FleetOrchestrator._parse_decompose_response(content)
        self.assertEqual(out[0]["blockedBy"], [2, 3])

    def test_returns_empty_on_garbage(self):
        self.assertEqual(FleetOrchestrator._parse_decompose_response("totally not json"), [])
        self.assertEqual(FleetOrchestrator._parse_decompose_response(""), [])
        self.assertEqual(FleetOrchestrator._parse_decompose_response("{}"), [])


class TestTranslateBlockedByIndices(unittest.TestCase):
    def test_one_indexed_to_task_ids(self):
        tasks_data = [
            {"subject": "a", "description": "", "blockedBy": []},
            {"subject": "b", "description": "", "blockedBy": [1]},
            {"subject": "c", "description": "", "blockedBy": [1, 2]},
        ]
        task_ids = ["10", "11", "12"]
        out = FleetOrchestrator._translate_blockedby_indices(tasks_data, task_ids)
        self.assertEqual(out[0]["blockedBy_ids"], [])
        self.assertEqual(out[1]["blockedBy_ids"], ["10"])
        self.assertEqual(out[2]["blockedBy_ids"], ["10", "11"])

    def test_self_reference_dropped(self):
        tasks_data = [{"subject": "a", "description": "", "blockedBy": [1]}]
        out = FleetOrchestrator._translate_blockedby_indices(tasks_data, ["7"])
        self.assertEqual(out[0]["blockedBy_ids"], [])

    def test_out_of_range_dropped(self):
        tasks_data = [
            {"subject": "a", "description": "", "blockedBy": [99]},
            {"subject": "b", "description": "", "blockedBy": [0, 1]},  # 0 is invalid 1-indexed
        ]
        task_ids = ["1", "2"]
        out = FleetOrchestrator._translate_blockedby_indices(tasks_data, task_ids)
        self.assertEqual(out[0]["blockedBy_ids"], [])
        self.assertEqual(out[1]["blockedBy_ids"], ["1"])


class _FakeClient:
    """Captures chat_sync calls and returns canned responses by call order."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self._lock = threading.Lock()

    def chat_sync(self, model, messages, tools=None):
        with self._lock:
            self.calls.append({"model": model, "messages": messages})
            if not self._responses:
                return {"content": ""}
            return self._responses.pop(0)


class _FakeSubAgentTool:
    """Drop-in replacement for SubAgentTool that returns scripted results."""

    by_subject = {}  # populated per-test

    def __init__(self, *args, **kwargs):
        pass

    def execute(self, params):
        prompt = params.get("prompt", "")
        for subject, payload in self.by_subject.items():
            if subject in prompt:
                return payload
        return {"ok": True, "result": "default", "summary": "default"}


class TestFleetRunEndToEnd(unittest.TestCase):
    def setUp(self):
        _reset_task_store()
        self.config = SimpleNamespace(
            model="test-model:cloud",
            cwd="/tmp/fake_cwd",
        )

    def tearDown(self):
        _reset_task_store()

    def _build_decompose_response(self):
        return {
            "content": json.dumps([
                {"subject": "task-alpha", "description": "do alpha", "blockedBy": []},
                {"subject": "task-beta", "description": "do beta", "blockedBy": [1]},
            ])
        }

    def test_run_with_synthesis_emits_unified_answer(self):
        client = _FakeClient([
            self._build_decompose_response(),
            {"content": "UNIFIED_SYNTH_ANSWER"},
        ])
        _FakeSubAgentTool.by_subject = {
            "task-alpha": {"ok": True, "result": "alpha-done", "summary": "alpha-done"},
            "task-beta": {"ok": True, "result": "beta-done", "summary": "beta-done"},
        }
        fleet = FleetOrchestrator(self.config, client, registry=None, permissions=None)
        with patch.object(eve_coder, "SubAgentTool", _FakeSubAgentTool):
            output = fleet.run("test goal", num_teammates=2)
        self.assertIn("UNIFIED_SYNTH_ANSWER", output)
        self.assertIn("Task #1", output)
        self.assertIn("Task #2", output)
        # synth call is the 2nd chat_sync invocation
        self.assertEqual(len(client.calls), 2)

    def test_run_with_skip_synthesis_omits_synth_call(self):
        client = _FakeClient([self._build_decompose_response()])
        _FakeSubAgentTool.by_subject = {
            "task-alpha": {"ok": True, "result": "a", "summary": "a"},
            "task-beta": {"ok": True, "result": "b", "summary": "b"},
        }
        fleet = FleetOrchestrator(self.config, client, registry=None, permissions=None)
        with patch.object(eve_coder, "SubAgentTool", _FakeSubAgentTool):
            output = fleet.run("test goal", num_teammates=2, skip_synthesis=True)
        # only the decompose call should have happened
        self.assertEqual(len(client.calls), 1)
        self.assertIn("synthesis skipped", output)

    def test_run_returns_error_when_decompose_unparseable(self):
        client = _FakeClient([{"content": "not json"}])
        fleet = FleetOrchestrator(self.config, client, registry=None, permissions=None)
        output = fleet.run("test goal", num_teammates=2)
        self.assertIn("Failed to decompose goal", output)


if __name__ == "__main__":
    unittest.main()
