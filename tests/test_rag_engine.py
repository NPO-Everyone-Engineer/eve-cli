"""
Test suite for RAGEngine class — SQLite + embeddings-based local RAG.
All tests use tempdir for file/DB operations and mock embedding calls.
"""

import unittest
import sys
import os
import struct
import tempfile
import shutil
import sqlite3
import hashlib

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# Import eve-coder.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)
RAGEngine = eve_coder.RAGEngine
Config = eve_coder.Config


def _make_config(cwd):
    """Create a minimal Config whose cwd points at the given directory."""
    cfg = Config.__new__(Config)
    cfg.cwd = cwd
    cfg.rag_model = "nomic-embed-text"
    cfg.ollama_host = "http://localhost:11434"
    cfg.rag_topk = 5
    return cfg


class TestSerializeDeserialize(unittest.TestCase):
    """Tests for _serialize_embedding / _deserialize_embedding roundtrip."""

    def test_roundtrip_simple(self):
        vec = [1.0, 2.0, 3.0]
        blob = RAGEngine._serialize_embedding(vec)
        result = RAGEngine._deserialize_embedding(blob)
        self.assertEqual(len(result), 3)
        for a, b in zip(vec, result):
            self.assertAlmostEqual(a, b, places=5)

    def test_roundtrip_negative_values(self):
        vec = [-1.5, 0.0, 3.14, -0.001]
        blob = RAGEngine._serialize_embedding(vec)
        result = RAGEngine._deserialize_embedding(blob)
        self.assertEqual(len(result), len(vec))
        for a, b in zip(vec, result):
            self.assertAlmostEqual(a, b, places=4)

    def test_roundtrip_empty(self):
        vec = []
        blob = RAGEngine._serialize_embedding(vec)
        result = RAGEngine._deserialize_embedding(blob)
        self.assertEqual(len(result), 0)

    def test_blob_size_matches_float32(self):
        vec = [0.0] * 128
        blob = RAGEngine._serialize_embedding(vec)
        self.assertEqual(len(blob), 128 * 4)  # float32 = 4 bytes each

    def test_roundtrip_large_vector(self):
        vec = [float(i) / 100.0 for i in range(768)]
        blob = RAGEngine._serialize_embedding(vec)
        result = RAGEngine._deserialize_embedding(blob)
        self.assertEqual(len(result), 768)
        for a, b in zip(vec, result):
            self.assertAlmostEqual(a, b, places=4)


class TestCosineSimilarity(unittest.TestCase):
    """Tests for _cosine_similarity."""

    def test_identical_vectors(self):
        a = [1.0, 2.0, 3.0]
        sim = RAGEngine._cosine_similarity(a, a)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertAlmostEqual(sim, 0.0, places=5)

    def test_opposite_vectors(self):
        a = [1.0, 2.0, 3.0]
        b = [-1.0, -2.0, -3.0]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertAlmostEqual(sim, -1.0, places=5)

    def test_zero_vector_a(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertEqual(sim, 0.0)

    def test_zero_vector_b(self):
        a = [1.0, 2.0, 3.0]
        b = [0.0, 0.0, 0.0]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertEqual(sim, 0.0)

    def test_both_zero_vectors(self):
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertEqual(sim, 0.0)

    def test_similar_vectors(self):
        a = [1.0, 2.0, 3.0]
        b = [1.1, 2.1, 3.1]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertGreater(sim, 0.99)

    def test_unit_vectors(self):
        a = [1.0, 0.0]
        b = [0.707, 0.707]
        sim = RAGEngine._cosine_similarity(a, b)
        self.assertAlmostEqual(sim, 0.707, places=2)


class TestChunkText(unittest.TestCase):
    """Tests for _chunk_text."""

    def test_short_text_single_chunk(self):
        text = "Hello world"
        chunks = RAGEngine._chunk_text(text, chunk_size=1000, overlap=200)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_empty_text(self):
        text = ""
        chunks = RAGEngine._chunk_text(text, chunk_size=100, overlap=20)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_long_text_multiple_chunks(self):
        # Create text with many lines that exceed chunk_size
        lines = [f"line {i}: " + "x" * 40 for i in range(100)]
        text = "\n".join(lines)
        chunks = RAGEngine._chunk_text(text, chunk_size=200, overlap=50)
        self.assertGreater(len(chunks), 1)

    def test_chunks_contain_all_content(self):
        lines = [f"unique_line_{i}" for i in range(50)]
        text = "\n".join(lines)
        chunks = RAGEngine._chunk_text(text, chunk_size=100, overlap=20)
        # Every original line should appear in at least one chunk
        combined = "\n".join(chunks)
        for line in lines:
            self.assertIn(line, combined)

    def test_overlap_present(self):
        # Build text where we can verify overlap behavior
        lines = [f"L{i:03d}" for i in range(100)]
        text = "\n".join(lines)
        chunks = RAGEngine._chunk_text(text, chunk_size=30, overlap=10)
        if len(chunks) >= 2:
            # Last part of chunk N should appear in beginning of chunk N+1
            last_lines_0 = chunks[0].split("\n")[-2:]
            first_lines_1 = chunks[1].split("\n")[:3]
            # At least one line from the end of chunk 0 should be in chunk 1
            overlap_found = any(line in first_lines_1 for line in last_lines_0)
            self.assertTrue(overlap_found, "Expected overlap between consecutive chunks")

    def test_default_parameters(self):
        text = "short"
        chunks = RAGEngine._chunk_text(text)
        self.assertEqual(len(chunks), 1)


class TestFileHash(unittest.TestCase):
    """Tests for _file_hash."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_consistent_hash(self):
        fpath = os.path.join(self.tmpdir, "test.txt")
        with open(fpath, "w") as f:
            f.write("hello world")
        h1 = RAGEngine._file_hash(fpath)
        h2 = RAGEngine._file_hash(fpath)
        self.assertEqual(h1, h2)

    def test_sha256_format(self):
        fpath = os.path.join(self.tmpdir, "test.txt")
        with open(fpath, "w") as f:
            f.write("content")
        h = RAGEngine._file_hash(fpath)
        self.assertEqual(len(h), 64)  # SHA-256 hex digest = 64 chars
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_different_content_different_hash(self):
        f1 = os.path.join(self.tmpdir, "a.txt")
        f2 = os.path.join(self.tmpdir, "b.txt")
        with open(f1, "w") as f:
            f.write("content A")
        with open(f2, "w") as f:
            f.write("content B")
        self.assertNotEqual(RAGEngine._file_hash(f1), RAGEngine._file_hash(f2))

    def test_matches_hashlib_directly(self):
        fpath = os.path.join(self.tmpdir, "verify.txt")
        data = "verify this hash"
        with open(fpath, "w") as f:
            f.write(data)
        with open(fpath, "rb") as f:
            expected = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(RAGEngine._file_hash(fpath), expected)


class TestCollectFiles(unittest.TestCase):
    """Tests for _collect_files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = _make_config(self.tmpdir)
        self.engine = RAGEngine.__new__(RAGEngine)
        self.engine.config = self.config
        self.engine.db_path = os.path.join(self.tmpdir, ".eve", "rag", "index.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_collects_python_files(self):
        fpath = os.path.join(self.tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("print('hello')")
        files = self.engine._collect_files(self.tmpdir)
        self.assertIn(fpath, files)

    def test_collects_js_files(self):
        fpath = os.path.join(self.tmpdir, "index.js")
        with open(fpath, "w") as f:
            f.write("console.log('hi');")
        files = self.engine._collect_files(self.tmpdir)
        self.assertIn(fpath, files)

    def test_collects_markdown_files(self):
        fpath = os.path.join(self.tmpdir, "readme.md")
        with open(fpath, "w") as f:
            f.write("# Title")
        files = self.engine._collect_files(self.tmpdir)
        self.assertIn(fpath, files)

    def test_skips_git_directory(self):
        git_dir = os.path.join(self.tmpdir, ".git")
        os.makedirs(git_dir)
        fpath = os.path.join(git_dir, "config.py")
        with open(fpath, "w") as f:
            f.write("secret")
        files = self.engine._collect_files(self.tmpdir)
        self.assertNotIn(fpath, files)

    def test_skips_node_modules(self):
        nm_dir = os.path.join(self.tmpdir, "node_modules", "pkg")
        os.makedirs(nm_dir)
        fpath = os.path.join(nm_dir, "index.js")
        with open(fpath, "w") as f:
            f.write("module.exports = {}")
        files = self.engine._collect_files(self.tmpdir)
        self.assertNotIn(fpath, files)

    def test_skips_pycache(self):
        cache_dir = os.path.join(self.tmpdir, "__pycache__")
        os.makedirs(cache_dir)
        fpath = os.path.join(cache_dir, "mod.cpython-39.pyc")
        with open(fpath, "w") as f:
            f.write("bytecode")
        files = self.engine._collect_files(self.tmpdir)
        self.assertNotIn(fpath, files)

    def test_skips_large_files(self):
        fpath = os.path.join(self.tmpdir, "big.py")
        with open(fpath, "w") as f:
            f.write("x" * (RAGEngine.MAX_FILE_SIZE + 1))
        files = self.engine._collect_files(self.tmpdir)
        self.assertNotIn(fpath, files)

    def test_skips_unknown_extensions(self):
        fpath = os.path.join(self.tmpdir, "data.xyz")
        with open(fpath, "w") as f:
            f.write("unknown format")
        files = self.engine._collect_files(self.tmpdir)
        self.assertNotIn(fpath, files)

    def test_collects_bare_filenames(self):
        for name in ["Makefile", "Dockerfile", "README", "LICENSE"]:
            fpath = os.path.join(self.tmpdir, name)
            with open(fpath, "w") as f:
                f.write("content")
        files = self.engine._collect_files(self.tmpdir)
        basenames = [os.path.basename(fp) for fp in files]
        for name in ["Makefile", "Dockerfile", "README", "LICENSE"]:
            self.assertIn(name, basenames)

    def test_single_file_target(self):
        fpath = os.path.join(self.tmpdir, "single.py")
        with open(fpath, "w") as f:
            f.write("x = 1")
        files = self.engine._collect_files(fpath)
        self.assertEqual(files, [fpath])

    def test_respects_text_extensions(self):
        """Verify several expected extensions are collected."""
        extensions = [".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".html", ".css"]
        for ext in extensions:
            fpath = os.path.join(self.tmpdir, f"file{ext}")
            with open(fpath, "w") as f:
                f.write("content")
        files = self.engine._collect_files(self.tmpdir)
        collected_exts = {os.path.splitext(fp)[1] for fp in files}
        for ext in extensions:
            self.assertIn(ext, collected_exts, f"Extension {ext} should be collected")


class TestEnsureDb(unittest.TestCase):
    """Tests for _ensure_db creating valid SQLite schema."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_db_file(self):
        cfg = _make_config(self.tmpdir)
        engine = RAGEngine(cfg)
        self.assertTrue(os.path.exists(engine.db_path))

    def test_creates_documents_table(self):
        cfg = _make_config(self.tmpdir)
        engine = RAGEngine(cfg)
        conn = sqlite3.connect(engine.db_path)
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            tables = cursor.fetchall()
            self.assertEqual(len(tables), 1)
        finally:
            conn.close()

    def test_documents_table_columns(self):
        cfg = _make_config(self.tmpdir)
        engine = RAGEngine(cfg)
        conn = sqlite3.connect(engine.db_path)
        try:
            cursor = conn.execute("PRAGMA table_info(documents)")
            columns = {row[1] for row in cursor.fetchall()}
            expected = {"id", "path", "chunk_index", "content", "embedding", "file_hash", "created_at"}
            self.assertEqual(columns, expected)
        finally:
            conn.close()

    def test_indexes_created(self):
        cfg = _make_config(self.tmpdir)
        engine = RAGEngine(cfg)
        conn = sqlite3.connect(engine.db_path)
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            index_names = {row[0] for row in cursor.fetchall()}
            self.assertIn("idx_doc_path", index_names)
            self.assertIn("idx_doc_hash", index_names)
        finally:
            conn.close()

    def test_idempotent(self):
        """Calling _ensure_db twice should not error."""
        cfg = _make_config(self.tmpdir)
        engine = RAGEngine(cfg)
        engine._ensure_db()  # second call
        self.assertTrue(os.path.exists(engine.db_path))


class TestFormatContext(unittest.TestCase):
    """Tests for format_context."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = _make_config(self.tmpdir)
        self.engine = RAGEngine(self.config)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_results(self):
        result = self.engine.format_context([])
        self.assertEqual(result, "")

    def test_single_result(self):
        results = [("src/main.py", "print('hello')", 0.95)]
        ctx = self.engine.format_context(results)
        self.assertIn("[LOCAL CONTEXT START]", ctx)
        self.assertIn("[LOCAL CONTEXT END]", ctx)
        self.assertIn("src/main.py", ctx)
        self.assertIn("0.950", ctx)
        self.assertIn("print('hello')", ctx)

    def test_multiple_results(self):
        results = [
            ("file_a.py", "content_a", 0.9),
            ("file_b.py", "content_b", 0.8),
        ]
        ctx = self.engine.format_context(results)
        self.assertIn("file_a.py", ctx)
        self.assertIn("file_b.py", ctx)
        self.assertIn("content_a", ctx)
        self.assertIn("content_b", ctx)

    def test_truncates_long_content(self):
        long_content = "x" * 3000
        results = [("long.py", long_content, 0.5)]
        ctx = self.engine.format_context(results)
        self.assertIn("... (truncated)", ctx)
        # The truncated content should be 2000 chars + truncation marker
        self.assertNotIn("x" * 2500, ctx)


class TestGetStats(unittest.TestCase):
    """Tests for get_stats."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = _make_config(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_db(self):
        engine = RAGEngine(self.config)
        stats = engine.get_stats()
        self.assertEqual(stats["chunks"], 0)
        self.assertEqual(stats["files"], 0)
        self.assertGreater(stats["db_size"], 0)  # SQLite file has header even when empty

    def test_no_db_file(self):
        engine = RAGEngine.__new__(RAGEngine)
        engine.config = self.config
        engine.db_path = os.path.join(self.tmpdir, "nonexistent", "index.sqlite")
        stats = engine.get_stats()
        self.assertEqual(stats, {"chunks": 0, "files": 0, "db_size": 0})

    def test_populated_db(self):
        engine = RAGEngine(self.config)
        # Manually insert some data
        conn = sqlite3.connect(engine.db_path)
        try:
            vec = RAGEngine._serialize_embedding([1.0, 2.0, 3.0])
            conn.execute(
                "INSERT INTO documents (path, chunk_index, content, embedding, file_hash) VALUES (?, ?, ?, ?, ?)",
                ("a.py", 0, "chunk1", vec, "hash1"),
            )
            conn.execute(
                "INSERT INTO documents (path, chunk_index, content, embedding, file_hash) VALUES (?, ?, ?, ?, ?)",
                ("a.py", 1, "chunk2", vec, "hash1"),
            )
            conn.execute(
                "INSERT INTO documents (path, chunk_index, content, embedding, file_hash) VALUES (?, ?, ?, ?, ?)",
                ("b.py", 0, "chunk3", vec, "hash2"),
            )
            conn.commit()
        finally:
            conn.close()
        stats = engine.get_stats()
        self.assertEqual(stats["chunks"], 3)
        self.assertEqual(stats["files"], 2)
        self.assertGreater(stats["db_size"], 0)


class TestRAGEngineConstants(unittest.TestCase):
    """Tests for RAGEngine class-level constants."""

    def test_text_extensions_contains_common(self):
        for ext in [".py", ".js", ".ts", ".md", ".txt", ".json", ".go", ".rs"]:
            self.assertIn(ext, RAGEngine.TEXT_EXTENSIONS)

    def test_bare_filenames(self):
        for name in ["makefile", "dockerfile", "readme", "license"]:
            self.assertIn(name, RAGEngine.BARE_FILENAMES)

    def test_skip_dirs(self):
        for d in [".git", "node_modules", "__pycache__", "venv"]:
            self.assertIn(d, RAGEngine.SKIP_DIRS)

    def test_max_file_size(self):
        self.assertEqual(RAGEngine.MAX_FILE_SIZE, 256 * 1024)


if __name__ == "__main__":
    unittest.main()
