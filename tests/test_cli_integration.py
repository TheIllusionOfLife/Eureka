"""Integration tests for CLI automatic bookmarking and optional context."""
import pytest
import tempfile
import json
import os
import subprocess
import sys


class TestCLIIntegration:
    """Test CLI integration for new features."""
    
    @pytest.fixture
    def temp_bookmark_file(self):
        """Create a temporary bookmark file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def run_cli_command(self, args, env=None):
        """Run CLI command and return result."""
        cmd = [sys.executable, "-m", "madspark.cli.cli"] + args
        
        # Set up environment
        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = "src"
        test_env["MADSPARK_MODE"] = "mock"  # Use mock mode for tests
        if env:
            test_env.update(env)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=test_env
        )
        return result
    
    def test_cli_works_without_context(self):
        """Test that 'ms topic' works without providing context."""
        # This should work after implementation
        result = self.run_cli_command(["test topic"])
        
        # Currently this fails, but should succeed after implementation
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Solution" in result.stdout  # Brief mode shows the solution directly
    
    def test_cli_works_with_empty_context(self):
        """Test that 'ms topic ""' works with empty context."""
        # This should work after implementation
        result = self.run_cli_command(["test topic", ""])
        
        # Currently this fails, but should succeed after implementation
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Solution" in result.stdout  # Brief mode shows the solution directly
    
    def test_automatic_bookmarking(self, temp_bookmark_file):
        """Test that results are automatically bookmarked without flag."""
        # Run command without --bookmark-results flag
        result = self.run_cli_command([
            "test topic",
            "test context",
            "--bookmark-file", temp_bookmark_file
        ])
        
        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # After implementation, bookmark file should contain the result
        with open(temp_bookmark_file, 'r') as f:
            bookmarks = json.load(f)
            # Currently this will fail because automatic bookmarking isn't implemented
            assert len(bookmarks) > 0, "No bookmarks were saved automatically"
    
    def test_no_bookmark_flag_prevents_bookmarking(self, temp_bookmark_file):
        """Test that --no-bookmark flag prevents bookmarking."""
        # Run command with --no-bookmark flag (doesn't exist yet)
        result = self.run_cli_command([
            "test topic",
            "test context",
            "--no-bookmark",
            "--bookmark-file", temp_bookmark_file
        ])
        
        # After implementation, this should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Bookmark file should remain empty
        with open(temp_bookmark_file, 'r') as f:
            bookmarks = json.load(f)
            assert len(bookmarks) == 0, "Bookmarks were saved despite --no-bookmark flag"
    
    def test_ms_command_with_real_workflow(self):
        """Test the ms command through run.py (simulating real usage)."""
        # Test using the run.py script
        cmd = [sys.executable, "run.py", "test topic"]
        
        test_env = os.environ.copy()
        test_env["MADSPARK_MODE"] = "mock"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=test_env
        )
        
        # Should work after implementation
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Mock idea generated" in result.stdout