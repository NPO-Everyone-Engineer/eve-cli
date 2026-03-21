"""
Test suite for parallel file editing functionality.
Tests MultiEditTool parallel execution, progress indicators, and configuration.
"""

import os
import sys
import tempfile
import shutil
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from eve-coder.py (note: hyphen in filename)
import importlib.util
spec = importlib.util.spec_from_file_location("eve_coder", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)

MultiEditTool = eve_coder.MultiEditTool
_MAX_PARALLEL_FILES = eve_coder._MAX_PARALLEL_FILES
_SHOW_PROGRESS = eve_coder._SHOW_PROGRESS


class TestParallelFileEditing:
    """Test parallel file editing functionality."""

    def setup_method(self):
        """Create temporary directory and test files."""
        self.test_dir = tempfile.mkdtemp()
        self.tool = MultiEditTool(cwd=self.test_dir)
        
        # Create test files
        self.test_files = []
        for i in range(5):
            fpath = os.path.join(self.test_dir, f"file{i}.txt")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"Hello World {i}\nLine 2\nLine 3\n")
            self.test_files.append(fpath)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_single_edit(self):
        """Test single file edit works correctly."""
        edits = [{
            "file_path": self.test_files[0],
            "old_string": "Hello World 0",
            "new_string": "Goodbye World 0"
        }]
        
        result = self.tool.execute({"edits": edits})
        
        assert "OK: file0.txt" in result
        assert "1/1 edits applied" in result
        
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        assert "Goodbye World 0" in content
        assert "Hello World 0" not in content

    def test_multiple_edits_parallel(self):
        """Test multiple files are edited in parallel."""
        edits = []
        for i in range(5):
            edits.append({
                "file_path": self.test_files[i],
                "old_string": f"Hello World {i}",
                "new_string": f"Modified {i}"
            })
        
        start_time = time.time()
        result = self.tool.execute({"edits": edits})
        elapsed = time.time() - start_time
        
        # All edits should succeed
        assert "5/5 edits applied" in result
        
        # Verify all files were modified
        for i in range(5):
            with open(self.test_files[i], "r", encoding="utf-8") as f:
                content = f.read()
            assert f"Modified {i}" in content
            assert f"Hello World {i}" not in content
        
        # Parallel execution should be faster than sequential
        # (each edit has small delay, so 5 parallel should be < 5x sequential)
        assert elapsed < 2.0  # Should complete quickly

    def test_partial_failure(self):
        """Test that partial failures don't stop other edits."""
        edits = [
            {
                "file_path": self.test_files[0],
                "old_string": "Hello World 0",
                "new_string": "Modified 0"
            },
            {
                "file_path": self.test_files[1],
                "old_string": "NonExistent String",  # Will fail
                "new_string": "Modified 1"
            },
            {
                "file_path": self.test_files[2],
                "old_string": "Hello World 2",
                "new_string": "Modified 2"
            }
        ]
        
        result = self.tool.execute({"edits": edits})
        
        # Should have 2 successes, 1 failure
        assert "2/3 edits applied" in result
        assert "Error: old_string not found" in result
        
        # Verify successful edits
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            assert "Modified 0" in f.read()
        with open(self.test_files[2], "r", encoding="utf-8") as f:
            assert "Modified 2" in f.read()
        # File 1 should be unchanged
        with open(self.test_files[1], "r", encoding="utf-8") as f:
            assert "Hello World 1" in f.read()

    def test_invalid_path(self):
        """Test invalid path handling."""
        edits = [{
            "file_path": "/nonexistent/path/file.txt",
            "old_string": "test",
            "new_string": "test"
        }]
        
        result = self.tool.execute({"edits": edits})
        assert "Error: invalid path" in result or "file not found" in result

    def test_protected_path(self):
        """Test protected path rejection."""
        # Try to edit a file in system directory
        edits = [{
            "file_path": "/etc/hosts",
            "old_string": "test",
            "new_string": "test"
        }]
        
        result = self.tool.execute({"edits": edits})
        assert "Error:" in result

    def test_symlink_rejection(self):
        """Test that symlinks are rejected."""
        # Create a symlink
        original = os.path.join(self.test_dir, "original.txt")
        link = os.path.join(self.test_dir, "link.txt")
        
        with open(original, "w", encoding="utf-8") as f:
            f.write("Original content\n")
        
        os.symlink(original, link)
        
        edits = [{
            "file_path": link,
            "old_string": "Original content",
            "new_string": "Modified content"
        }]
        
        result = self.tool.execute({"edits": edits})
        assert "symlink not allowed" in result

    def test_outside_repo_rejected(self):
        """MultiEdit rejects files outside its configured workspace."""
        outside_dir = tempfile.mkdtemp()
        try:
            outside_file = os.path.join(outside_dir, "outside.txt")
            with open(outside_file, "w", encoding="utf-8") as f:
                f.write("secret\n")
            edits = [{
                "file_path": outside_file,
                "old_string": "secret",
                "new_string": "public"
            }]
            result = self.tool.execute({"edits": edits})
            assert "outside repository" in result
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_parent_symlink_escape_rejected(self):
        """Symlinked parent directories cannot escape the workspace."""
        outside_dir = tempfile.mkdtemp()
        try:
            outside_file = os.path.join(outside_dir, "outside.txt")
            with open(outside_file, "w", encoding="utf-8") as f:
                f.write("secret\n")
            link_dir = os.path.join(self.test_dir, "linked")
            os.symlink(outside_dir, link_dir)
            edits = [{
                "file_path": os.path.join(link_dir, "outside.txt"),
                "old_string": "secret",
                "new_string": "public"
            }]
            result = self.tool.execute({"edits": edits})
            assert "outside repository" in result
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_multiple_edits_same_file(self):
        """Test multiple edits to the same file."""
        edits = [
            {
                "file_path": self.test_files[0],
                "old_string": "Line 2",
                "new_string": "Modified Line 2"
            },
            {
                "file_path": self.test_files[0],
                "old_string": "Line 3",
                "new_string": "Modified Line 3"
            }
        ]
        
        result = self.tool.execute({"edits": edits})
        
        # Both edits should succeed
        assert "2/2 edits applied" in result
        
        with open(self.test_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        assert "Modified Line 2" in content
        assert "Modified Line 3" in content

    def test_file_lock_prevents_corruption(self):
        """Test that file locks prevent concurrent write corruption."""
        # Create a file with known content
        test_file = os.path.join(self.test_dir, "concurrent.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Line 0\nLine 1\nLine 2\nLine 3\nLine 4\n")
        
        # Create multiple edits to the same file
        edits = []
        for i in range(5):
            edits.append({
                "file_path": test_file,
                "old_string": f"Line {i}",
                "new_string": f"Modified {i}"
            })
        
        result = self.tool.execute({"edits": edits})
        
        # All edits should succeed
        assert "5/5 edits applied" in result
        
        # Verify file integrity
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        for i in range(5):
            assert f"Modified {i}" in content
            assert f"Line {i}\n" not in content or f"Modified {i}" in content

    def test_max_edits_limit(self):
        """Test that max edits limit is enforced."""
        edits = []
        for i in range(25):
            edits.append({
                "file_path": self.test_files[0],
                "old_string": f"test{i}",
                "new_string": f"modified{i}"
            })
        
        result = self.tool.execute({"edits": edits})
        assert "too many edits (max 20)" in result

    def test_empty_edits(self):
        """Test empty edits list handling."""
        result = self.tool.execute({"edits": []})
        assert "no edits provided" in result


class TestParallelConfiguration:
    """Test configuration for parallel file operations."""

    def test_max_parallel_files_range(self):
        """Test that MAX_PARALLEL_FILES is within valid range."""
        assert 1 <= _MAX_PARALLEL_FILES <= 10

    def test_show_progress_default(self):
        """Test that SHOW_PROGRESS defaults to True."""
        assert _SHOW_PROGRESS is True


class TestThreadSafety:
    """Test thread safety of parallel file operations."""

    def setup_method(self):
        """Create temporary directory and test files."""
        self.test_dir = tempfile.mkdtemp()
        self.tool = MultiEditTool()
        
        # Create test files
        self.test_files = []
        for i in range(10):
            fpath = os.path.join(self.test_dir, f"file{i}.txt")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"Content {i}\n")
            self.test_files.append(fpath)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_execution(self):
        """Test that concurrent executions don't interfere."""
        results = []
        errors = []
        
        def run_edit(file_idx):
            try:
                edits = [{
                    "file_path": self.test_files[file_idx],
                    "old_string": f"Content {file_idx}",
                    "new_string": f"Modified {file_idx}"
                }]
                result = self.tool.execute({"edits": edits})
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Run multiple edits concurrently
        threads = []
        for i in range(10):
            t = threading.Thread(target=run_edit, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All should succeed
        assert len(errors) == 0
        assert len(results) == 10
        
        # Verify all files were modified
        for i in range(10):
            with open(self.test_files[i], "r", encoding="utf-8") as f:
                content = f.read()
            assert f"Modified {i}" in content


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
