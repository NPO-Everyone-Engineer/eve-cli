"""
Test suite for ToolRegistry: registration, retrieval, schema caching, and defaults.
"""

import importlib.util
import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

ToolRegistry = eve_coder.ToolRegistry
Tool = eve_coder.Tool


class _DummyTool(Tool):
    """Minimal concrete Tool for testing the registry."""
    name = "DummyTool"
    description = "A dummy tool for testing"
    parameters = {"type": "object", "properties": {"x": {"type": "string"}}}

    def execute(self, params):
        return "dummy"


class _AnotherTool(Tool):
    name = "AnotherTool"
    description = "Another dummy tool"
    parameters = {"type": "object", "properties": {}}

    def execute(self, params):
        return "another"


class TestToolRegistryInit(unittest.TestCase):
    """Tests for ToolRegistry initialization."""

    def test_empty_registry(self):
        reg = ToolRegistry()
        self.assertEqual(reg.names(), [])

    def test_internal_tools_dict_empty(self):
        reg = ToolRegistry()
        self.assertEqual(len(reg._tools), 0)


class TestToolRegistryRegisterAndGet(unittest.TestCase):
    """Tests for register() and get()."""

    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = _DummyTool()
        reg.register(tool)
        self.assertIs(reg.get("DummyTool"), tool)

    def test_get_nonexistent_returns_none(self):
        reg = ToolRegistry()
        self.assertIsNone(reg.get("NoSuchTool"))

    def test_register_multiple(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        reg.register(_AnotherTool())
        self.assertEqual(set(reg.names()), {"DummyTool", "AnotherTool"})

    def test_register_overwrites_existing(self):
        reg = ToolRegistry()
        tool1 = _DummyTool()
        tool2 = _DummyTool()
        reg.register(tool1)
        reg.register(tool2)
        self.assertIs(reg.get("DummyTool"), tool2)
        self.assertEqual(len(reg.names()), 1)


class TestToolRegistryNames(unittest.TestCase):
    """Tests for names()."""

    def test_names_empty(self):
        reg = ToolRegistry()
        self.assertEqual(reg.names(), [])

    def test_names_returns_list(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        result = reg.names()
        self.assertIsInstance(result, list)
        self.assertEqual(result, ["DummyTool"])

    def test_names_order_matches_insertion(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        reg.register(_AnotherTool())
        self.assertEqual(reg.names(), ["DummyTool", "AnotherTool"])


class TestToolRegistrySchemas(unittest.TestCase):
    """Tests for get_schemas() and schema caching."""

    def test_schemas_empty_registry(self):
        reg = ToolRegistry()
        self.assertEqual(reg.get_schemas(), [])

    def test_schemas_format(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        schemas = reg.get_schemas()
        self.assertEqual(len(schemas), 1)
        schema = schemas[0]
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "DummyTool")
        self.assertEqual(schema["function"]["description"], "A dummy tool for testing")
        self.assertIn("properties", schema["function"]["parameters"])

    def test_schemas_cached_returns_same_object(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        first = reg.get_schemas()
        second = reg.get_schemas()
        self.assertIs(first, second)

    def test_cache_invalidated_on_new_registration(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        first = reg.get_schemas()
        self.assertEqual(len(first), 1)
        reg.register(_AnotherTool())
        second = reg.get_schemas()
        self.assertIsNot(first, second)
        self.assertEqual(len(second), 2)

    def test_schemas_multiple_tools(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        reg.register(_AnotherTool())
        schemas = reg.get_schemas()
        names_in_schemas = {s["function"]["name"] for s in schemas}
        self.assertEqual(names_in_schemas, {"DummyTool", "AnotherTool"})


class TestToolRegistryDefaults(unittest.TestCase):
    """Tests for register_defaults()."""

    EXPECTED_TOOL_NAMES = {
        "Bash", "Read", "Write", "Edit", "ApplyPatch", "MultiEdit", "Glob", "Grep",
        "WebFetch", "WebSearch", "NotebookEdit",
        "TaskCreate", "TaskList", "TaskGet", "TaskUpdate",
        "AskUserQuestion", "AskUserQuestionBatch",
    }

    def test_register_defaults_returns_self(self):
        reg = ToolRegistry()
        result = reg.register_defaults()
        self.assertIs(result, reg)

    def test_register_defaults_tool_count(self):
        reg = ToolRegistry()
        reg.register_defaults()
        self.assertEqual(len(reg.names()), len(self.EXPECTED_TOOL_NAMES))

    def test_register_defaults_tool_names(self):
        reg = ToolRegistry()
        reg.register_defaults()
        self.assertEqual(set(reg.names()), self.EXPECTED_TOOL_NAMES)

    def test_register_defaults_all_have_schemas(self):
        reg = ToolRegistry()
        reg.register_defaults()
        schemas = reg.get_schemas()
        self.assertEqual(len(schemas), len(self.EXPECTED_TOOL_NAMES))
        for schema in schemas:
            self.assertIn("type", schema)
            self.assertEqual(schema["type"], "function")
            self.assertIn("function", schema)
            self.assertIn("name", schema["function"])
            self.assertIn("description", schema["function"])

    def test_register_defaults_all_tools_are_tool_instances(self):
        reg = ToolRegistry()
        reg.register_defaults()
        for name in reg.names():
            tool = reg.get(name)
            self.assertIsInstance(tool, Tool)

    def test_register_defaults_idempotent(self):
        """Calling register_defaults twice should not duplicate tools."""
        reg = ToolRegistry()
        reg.register_defaults()
        reg.register_defaults()
        self.assertEqual(len(reg.names()), len(self.EXPECTED_TOOL_NAMES))


if __name__ == "__main__":
    unittest.main()
