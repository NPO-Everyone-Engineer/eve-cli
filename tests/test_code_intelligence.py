"""
Test suite for CodeIntelligence class — lightweight regex-based symbol indexing.
All tests use tempdir for file operations.
"""

import unittest
import sys
import os
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
CodeIntelligence = eve_coder.CodeIntelligence


class TestPythonPatterns(unittest.TestCase):
    """Test Python function/class/variable detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_function(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("def hello_world():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("hello_world")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_detect_async_function(self):
        fpath = os.path.join(self.tmpdir, "async_mod.py")
        with open(fpath, "w") as f:
            f.write("async def fetch_data():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("fetch_data")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_detect_class(self):
        fpath = os.path.join(self.tmpdir, "models.py")
        with open(fpath, "w") as f:
            f.write("class MyModel:\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("MyModel")
        self.assertTrue(any(d["kind"] == "class" for d in defs))

    def test_detect_variable(self):
        fpath = os.path.join(self.tmpdir, "config.py")
        with open(fpath, "w") as f:
            f.write("MAX_SIZE = 1024\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("MAX_SIZE")
        self.assertTrue(any(d["kind"] == "variable" for d in defs))

    def test_skips_single_char_variable(self):
        fpath = os.path.join(self.tmpdir, "short.py")
        with open(fpath, "w") as f:
            f.write("x = 1\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("x")
        self.assertEqual(len(defs), 0)


class TestJavaScriptPatterns(unittest.TestCase):
    """Test JavaScript function/class detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_named_function(self):
        fpath = os.path.join(self.tmpdir, "utils.js")
        with open(fpath, "w") as f:
            f.write("function processData(items) {\n  return items;\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("processData")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_detect_class(self):
        fpath = os.path.join(self.tmpdir, "app.js")
        with open(fpath, "w") as f:
            f.write("class AppController {\n  constructor() {}\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("AppController")
        self.assertTrue(any(d["kind"] == "class" for d in defs))

    def test_detect_const_variable(self):
        fpath = os.path.join(self.tmpdir, "constants.js")
        with open(fpath, "w") as f:
            f.write("const API_URL = 'https://example.com';\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("API_URL")
        self.assertTrue(len(defs) > 0)


class TestTypeScriptPatterns(unittest.TestCase):
    """Test TypeScript interface/type detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_interface(self):
        fpath = os.path.join(self.tmpdir, "types.ts")
        with open(fpath, "w") as f:
            f.write("export interface UserConfig {\n  name: string;\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("UserConfig")
        self.assertTrue(any(d["kind"] == "interface" for d in defs))

    def test_detect_type_alias(self):
        fpath = os.path.join(self.tmpdir, "types.ts")
        with open(fpath, "w") as f:
            f.write("export type ResponseType = 'json' | 'text';\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("ResponseType")
        self.assertTrue(any(d["kind"] == "type" for d in defs))

    def test_detect_abstract_class(self):
        fpath = os.path.join(self.tmpdir, "base.ts")
        with open(fpath, "w") as f:
            f.write("export abstract class BaseService {\n  abstract run(): void;\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("BaseService")
        self.assertTrue(any(d["kind"] == "class" for d in defs))


class TestGoPatterns(unittest.TestCase):
    """Test Go function/struct detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_function(self):
        fpath = os.path.join(self.tmpdir, "main.go")
        with open(fpath, "w") as f:
            f.write("func HandleRequest(w http.ResponseWriter, r *http.Request) {\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("HandleRequest")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_detect_struct(self):
        fpath = os.path.join(self.tmpdir, "models.go")
        with open(fpath, "w") as f:
            f.write("type ServerConfig struct {\n  Port int\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("ServerConfig")
        self.assertTrue(any(d["kind"] == "struct" for d in defs))

    def test_detect_method(self):
        fpath = os.path.join(self.tmpdir, "server.go")
        with open(fpath, "w") as f:
            f.write("func (s *Server) StartListening(port int) error {\n  return nil\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("StartListening")
        self.assertTrue(any(d["kind"] == "function" for d in defs))


class TestRustPatterns(unittest.TestCase):
    """Test Rust fn/struct/trait/enum detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_function(self):
        fpath = os.path.join(self.tmpdir, "lib.rs")
        with open(fpath, "w") as f:
            f.write("pub fn calculate_total(items: &[Item]) -> f64 {\n    0.0\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("calculate_total")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_detect_struct(self):
        fpath = os.path.join(self.tmpdir, "types.rs")
        with open(fpath, "w") as f:
            f.write("pub struct Configuration {\n    pub name: String,\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Configuration")
        self.assertTrue(any(d["kind"] == "struct" for d in defs))

    def test_detect_trait(self):
        fpath = os.path.join(self.tmpdir, "traits.rs")
        with open(fpath, "w") as f:
            f.write("pub trait Drawable {\n    fn draw(&self);\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Drawable")
        self.assertTrue(any(d["kind"] == "trait" for d in defs))

    def test_detect_enum(self):
        fpath = os.path.join(self.tmpdir, "enums.rs")
        with open(fpath, "w") as f:
            f.write("pub enum Direction {\n    North,\n    South,\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Direction")
        self.assertTrue(any(d["kind"] == "enum" for d in defs))


class TestRubyPatterns(unittest.TestCase):
    """Test Ruby method/class/module detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_method(self):
        fpath = os.path.join(self.tmpdir, "helper.rb")
        with open(fpath, "w") as f:
            f.write("  def process_items\n    # do stuff\n  end\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("process_items")
        self.assertTrue(any(d["kind"] == "method" for d in defs))

    def test_detect_class(self):
        fpath = os.path.join(self.tmpdir, "user.rb")
        with open(fpath, "w") as f:
            f.write("class UserService\n  def initialize\n  end\nend\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("UserService")
        self.assertTrue(any(d["kind"] == "class" for d in defs))

    def test_detect_module(self):
        fpath = os.path.join(self.tmpdir, "helpers.rb")
        with open(fpath, "w") as f:
            f.write("module Authentication\nend\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Authentication")
        self.assertTrue(any(d["kind"] == "module" for d in defs))


class TestJavaPatterns(unittest.TestCase):
    """Test Java method/class/interface detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_class(self):
        fpath = os.path.join(self.tmpdir, "App.java")
        with open(fpath, "w") as f:
            f.write("public class Application {\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Application")
        self.assertTrue(any(d["kind"] == "class" for d in defs))

    def test_detect_interface(self):
        fpath = os.path.join(self.tmpdir, "Service.java")
        with open(fpath, "w") as f:
            f.write("public interface DataService {\n  void process();\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("DataService")
        self.assertTrue(any(d["kind"] == "interface" for d in defs))

    def test_detect_method(self):
        fpath = os.path.join(self.tmpdir, "Utils.java")
        with open(fpath, "w") as f:
            f.write("public class Utils {\n  public static String formatDate(Date dt) {\n    return \"\";\n  }\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("formatDate")
        self.assertTrue(any(d["kind"] == "method" for d in defs))


class TestExtensionMapping(unittest.TestCase):
    """Test _EXT_MAP: .jsx -> .js, .tsx -> .ts, etc."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_jsx_maps_to_js(self):
        self.assertEqual(CodeIntelligence._EXT_MAP.get(".jsx"), ".js")

    def test_tsx_maps_to_ts(self):
        self.assertEqual(CodeIntelligence._EXT_MAP.get(".tsx"), ".ts")

    def test_mjs_maps_to_js(self):
        self.assertEqual(CodeIntelligence._EXT_MAP.get(".mjs"), ".js")

    def test_jsx_file_indexed_with_js_patterns(self):
        fpath = os.path.join(self.tmpdir, "component.jsx")
        with open(fpath, "w") as f:
            f.write("function RenderButton(props) {\n  return null;\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("RenderButton")
        self.assertTrue(any(d["kind"] == "function" for d in defs))

    def test_tsx_file_indexed_with_ts_patterns(self):
        fpath = os.path.join(self.tmpdir, "types.tsx")
        with open(fpath, "w") as f:
            f.write("interface ComponentProps {\n  name: string;\n}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("ComponentProps")
        self.assertTrue(any(d["kind"] == "interface" for d in defs))


class TestBuildIndex(unittest.TestCase):
    """Test build_index on temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_returns_symbol_count(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("def alpha():\n    pass\ndef beta():\n    pass\nclass Gamma:\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        count = ci.build_index()
        self.assertGreaterEqual(count, 3)

    def test_empty_directory(self):
        ci = CodeIntelligence(self.tmpdir)
        count = ci.build_index()
        self.assertEqual(count, 0)

    def test_clears_previous_index(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("def first_pass():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        # Overwrite with different content
        with open(fpath, "w") as f:
            f.write("def second_pass():\n    pass\n")
        ci.build_index()
        self.assertEqual(len(ci.find_definition("first_pass")), 0)
        self.assertTrue(len(ci.find_definition("second_pass")) > 0)


class TestFindDefinitionPriority(unittest.TestCase):
    """Test find_definition priority ordering."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_class_before_function(self):
        # Create a file where both class and function share a name pattern
        f1 = os.path.join(self.tmpdir, "a.py")
        with open(f1, "w") as f:
            f.write("def Worker():\n    pass\n")
        f2 = os.path.join(self.tmpdir, "b.py")
        with open(f2, "w") as f:
            f.write("class Worker:\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("Worker")
        self.assertGreaterEqual(len(defs), 2)
        self.assertEqual(defs[0]["kind"], "class")

    def test_function_before_variable(self):
        f1 = os.path.join(self.tmpdir, "a.py")
        with open(f1, "w") as f:
            f.write("handler = lambda: None\n")
        f2 = os.path.join(self.tmpdir, "b.py")
        with open(f2, "w") as f:
            f.write("def handler():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("handler")
        self.assertGreaterEqual(len(defs), 2)
        self.assertEqual(defs[0]["kind"], "function")


class TestSearchSymbols(unittest.TestCase):
    """Test search_symbols substring match."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_substring_match(self):
        fpath = os.path.join(self.tmpdir, "handlers.py")
        with open(fpath, "w") as f:
            f.write("def handle_request():\n    pass\ndef handle_response():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        results = ci.search_symbols("handle")
        names = [r["name"] for r in results]
        self.assertIn("handle_request", names)
        self.assertIn("handle_response", names)

    def test_case_insensitive(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("class MyParser:\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        results = ci.search_symbols("myparser")
        self.assertTrue(len(results) > 0)

    def test_max_results(self):
        fpath = os.path.join(self.tmpdir, "many.py")
        with open(fpath, "w") as f:
            for i in range(30):
                f.write(f"def item_{i:03d}():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        results = ci.search_symbols("item", max_results=5)
        self.assertLessEqual(len(results), 5)

    def test_no_match(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("def alpha():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        results = ci.search_symbols("zzz_nonexistent")
        self.assertEqual(len(results), 0)


class TestSymbolCount(unittest.TestCase):
    """Test symbol_count property."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty(self):
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        self.assertEqual(ci.symbol_count, 0)

    def test_counts_all_entries(self):
        fpath = os.path.join(self.tmpdir, "mod.py")
        with open(fpath, "w") as f:
            f.write("def func_a():\n    pass\ndef func_b():\n    pass\nclass ClassC:\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        self.assertGreaterEqual(ci.symbol_count, 3)


class TestSkipDirs(unittest.TestCase):
    """Test _SKIP_DIRS respected during indexing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_skips_node_modules(self):
        nm_dir = os.path.join(self.tmpdir, "node_modules", "pkg")
        os.makedirs(nm_dir)
        fpath = os.path.join(nm_dir, "index.js")
        with open(fpath, "w") as f:
            f.write("function hiddenFunc() {}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("hiddenFunc")
        self.assertEqual(len(defs), 0)

    def test_skips_pycache(self):
        cache_dir = os.path.join(self.tmpdir, "__pycache__")
        os.makedirs(cache_dir)
        fpath = os.path.join(cache_dir, "cached.py")
        with open(fpath, "w") as f:
            f.write("def cached_fn():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("cached_fn")
        self.assertEqual(len(defs), 0)

    def test_skips_dot_git(self):
        git_dir = os.path.join(self.tmpdir, ".git", "hooks")
        os.makedirs(git_dir)
        fpath = os.path.join(git_dir, "pre-commit.py")
        with open(fpath, "w") as f:
            f.write("def hook_func():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        defs = ci.find_definition("hook_func")
        self.assertEqual(len(defs), 0)


class TestMaxFiles(unittest.TestCase):
    """Test max_files limit."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_respects_max_files(self):
        # Create more files than the limit
        for i in range(10):
            fpath = os.path.join(self.tmpdir, f"mod_{i}.py")
            with open(fpath, "w") as f:
                f.write(f"def func_{i}():\n    pass\n")
        ci = CodeIntelligence(self.tmpdir, max_files=3)
        ci.build_index()
        # We can't easily check which 3 were picked (os.walk order varies),
        # but symbol_count should be limited
        self.assertLessEqual(ci.symbol_count, 3)


class TestFindReferences(unittest.TestCase):
    """Test find_references."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_finds_usage(self):
        f1 = os.path.join(self.tmpdir, "defs.py")
        with open(f1, "w") as f:
            f.write("def compute_total(items):\n    return sum(items)\n")
        f2 = os.path.join(self.tmpdir, "main.py")
        with open(f2, "w") as f:
            f.write("from defs import compute_total\nresult = compute_total([1, 2, 3])\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        refs = ci.find_references("compute_total")
        self.assertGreaterEqual(len(refs), 2)

    def test_max_results_limit(self):
        fpath = os.path.join(self.tmpdir, "repeat.py")
        with open(fpath, "w") as f:
            for i in range(100):
                f.write(f"use_symbol = {i}\n")
        ci = CodeIntelligence(self.tmpdir)
        ci.build_index()
        refs = ci.find_references("use_symbol", max_results=5)
        self.assertLessEqual(len(refs), 5)

    def test_skips_node_modules_in_refs(self):
        nm_dir = os.path.join(self.tmpdir, "node_modules", "pkg")
        os.makedirs(nm_dir)
        fpath = os.path.join(nm_dir, "index.js")
        with open(fpath, "w") as f:
            f.write("function targetSymbol() {}\n")
        ci = CodeIntelligence(self.tmpdir)
        refs = ci.find_references("targetSymbol")
        ref_files = [r["file"] for r in refs]
        for rf in ref_files:
            self.assertNotIn("node_modules", rf)


class TestCodeIntelligenceConstants(unittest.TestCase):
    """Test class-level constants."""

    def test_skip_dirs_contains_expected(self):
        for d in [".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"]:
            self.assertIn(d, CodeIntelligence._SKIP_DIRS)

    def test_ext_map_completeness(self):
        self.assertIn(".jsx", CodeIntelligence._EXT_MAP)
        self.assertIn(".tsx", CodeIntelligence._EXT_MAP)
        self.assertIn(".mjs", CodeIntelligence._EXT_MAP)
        self.assertIn(".cjs", CodeIntelligence._EXT_MAP)
        self.assertIn(".mts", CodeIntelligence._EXT_MAP)

    def test_patterns_cover_all_languages(self):
        for ext in [".py", ".js", ".ts", ".go", ".rs", ".rb", ".java"]:
            self.assertIn(ext, CodeIntelligence._PATTERNS, f"Missing patterns for {ext}")


if __name__ == "__main__":
    unittest.main()
