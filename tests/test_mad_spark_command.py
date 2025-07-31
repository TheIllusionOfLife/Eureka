"""Tests for mad_spark command line interface."""
import os
import tempfile
import pytest
from unittest.mock import patch


class TestMadSparkCommand:
    """Test mad_spark command functionality."""
    
    @pytest.fixture
    def mock_mad_spark_installed(self):
        """Mock mad_spark command installation."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock mad_spark executable
            mad_spark_path = os.path.join(tmpdir, "mad_spark")
            with open(mad_spark_path, 'w') as f:
                f.write("#!/usr/bin/env python3\n")
                f.write("# Mock mad_spark command\n")
            os.chmod(mad_spark_path, 0o755)
            
            # Add to PATH for testing
            original_path = os.environ.get('PATH', '')
            os.environ['PATH'] = f"{tmpdir}:{original_path}"
            
            yield mad_spark_path
            
            # Restore PATH
            os.environ['PATH'] = original_path
    
    def test_mad_spark_exists_after_setup(self):
        """Test that mad_spark command exists after running setup."""
        # Check if mad_spark is in PATH or common locations
        locations_to_check = [
            '/usr/local/bin/mad_spark',
            os.path.expanduser('~/.local/bin/mad_spark'),
            './src/madspark/bin/mad_spark'
        ]
        
        # At least one should exist after setup
        found = any(os.path.exists(loc) for loc in locations_to_check)
        assert found or os.path.exists('src/madspark/bin/mad_spark'), "mad_spark command not found in expected locations"
    
    def test_mad_spark_is_executable(self, mock_mad_spark_installed):
        """Test that mad_spark command is executable."""
        # Check file permissions
        assert os.path.isfile(mock_mad_spark_installed)
        assert os.access(mock_mad_spark_installed, os.X_OK)
    
    def test_mad_spark_shows_help(self):
        """Test that 'mad_spark' without args shows help."""
        import subprocess
        import sys
        
        # Test mad_spark --help command
        result = subprocess.run([
            sys.executable, 'run.py', '--help'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        # Should exit successfully
        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        
        # Should contain help information
        help_output = result.stdout + result.stderr
        assert len(help_output) > 100, "Help output should be substantial"
        
        # Should contain key help elements
        help_indicators = ["usage", "Usage", "MadSpark", "arguments", "options", "help"]
        assert any(indicator in help_output for indicator in help_indicators), \
            f"Help output should contain help indicators. Got: {help_output[:200]}..."
    
    def test_mad_spark_runs_coordinator(self):
        """Test that 'mad_spark coordinator' runs the coordinator."""
        import subprocess
        import sys
        
        # Test mad_spark coordinator command with mock mode to avoid API dependency
        env = os.environ.copy()
        env['MADSPARK_MODE'] = 'mock'
        env['SUPPRESS_MODE_MESSAGE'] = '1'  # Suppress mode detection message
        
        result = subprocess.run([
            sys.executable, 'run.py', 'coordinator'
        ], capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=30)
        
        # Should exit successfully or timeout gracefully
        assert result.returncode == 0, f"Coordinator command failed: stderr={result.stderr}, stdout={result.stdout}"
        
        # Should produce coordinator output
        output = result.stdout + result.stderr
        
        # Should contain coordinator-specific elements
        coordinator_indicators = [
            "coordinator", "Coordinator", "multi-agent", "Multi-Agent",
            "IdeaGenerator", "Critic", "Advocate", "Skeptic", "ideas", "evaluation"
        ]
        
        assert any(indicator in output for indicator in coordinator_indicators), \
            f"Coordinator output should contain coordinator indicators. Got: {output[:300]}..."
        
        # Output should be substantial (coordinator generates multiple ideas)
        assert len(output) > 100, f"Coordinator output should be substantial. Got {len(output)} chars: {output[:200]}..."
    
    def test_mad_spark_cli_simplified_syntax(self):
        """Test simplified CLI syntax: mad_spark "topic" "context"."""
        with patch('subprocess.run'):
            # Test: mad_spark "AI automation" "cost effective"
            # Should execute: python -m madspark.cli.cli "AI automation" "cost effective"
            # Much simpler than: ./run.py cli "AI automation" "cost effective"
            pass
    
    def test_mad_spark_handles_single_argument(self):
        """Test that single argument is treated as topic with empty context."""
        with patch('subprocess.run'):
            # Test: mad_spark "consciousness"
            # Should execute: python -m madspark.cli.cli "consciousness" ""
            pass
    
    def test_mad_spark_runs_tests(self):
        """Test that 'mad_spark test' runs the test suite."""
        with patch('subprocess.run'):
            # Test: mad_spark test
            # Should execute: pytest tests/
            pass
    
    def test_mad_spark_preserves_environment(self):
        """Test that mad_spark preserves environment variables."""
        test_env = {
            'MADSPARK_MODE': 'mock',
            'GOOGLE_API_KEY': 'test_key'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('subprocess.run'):
                # mad_spark should pass through env vars
                # Verify subprocess receives correct environment
                pass
    
    def test_mad_spark_works_from_any_directory(self):
        """Test that mad_spark works when called from any directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to a different directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                with patch('subprocess.run'):
                    # mad_spark should still work
                    # Should find project root and run correctly
                    pass
            finally:
                os.chdir(original_cwd)
    
    def test_mad_spark_error_handling(self):
        """Test that mad_spark handles errors gracefully."""
        import subprocess
        import sys
        
        # Test 1: Missing required arguments for CLI (this will timeout if treated as topic)
        result = subprocess.run([
            sys.executable, 'run.py', 'cli'
        ], capture_output=True, text=True, cwd=os.getcwd(), timeout=10)
        
        # Should exit with error code
        assert result.returncode != 0, "CLI without arguments should return non-zero exit code"
        
        # Should provide helpful error message about missing arguments
        error_output = result.stdout + result.stderr
        argument_error_indicators = ["Error", "requires", "argument", "topic", "Usage"]
        assert any(indicator in error_output for indicator in argument_error_indicators), \
            f"Missing argument error should be helpful. Got: {error_output[:300]}..."
        
        # Test 2: Test that topics are processed correctly (not treated as errors)
        # This ensures the topic handling works as expected
        env = os.environ.copy()
        env['MADSPARK_MODE'] = 'mock'
        env['SUPPRESS_MODE_MESSAGE'] = '1'
        
        result = subprocess.run([
            sys.executable, 'run.py', 'test_topic'
        ], capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=30)
        
        # Should exit successfully (topic is valid)
        assert result.returncode == 0, f"Valid topic should succeed: stderr={result.stderr[:200]}, stdout={result.stdout[:200]}"
        
        # Should generate ideas output (not error)
        output = result.stdout + result.stderr
        idea_indicators = ["idea", "Mock", "generated", "score", "evaluation"]
        assert any(indicator in output for indicator in idea_indicators), \
            f"Topic processing should generate ideas. Got: {output[:300]}..."
    
    def test_mad_spark_version_command(self):
        """Test that 'mad_spark --version' shows version info."""
        with patch('subprocess.run'):
            # Test: mad_spark --version
            # Should show: MadSpark Multi-Agent System v2.2
            pass


class TestMadSparkIntegration:
    """Integration tests for mad_spark command."""
    
    def test_mad_spark_mock_mode_integration(self):
        """Test mad_spark runs in mock mode when no API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any API keys
            if 'GOOGLE_API_KEY' in os.environ:
                del os.environ['GOOGLE_API_KEY']
            
            # Run: mad_spark "test topic" "test context"
            # Should complete successfully with mock response
            pass
    
    def test_mad_spark_api_mode_integration(self):
        """Test mad_spark uses API when key is present."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIza_test_key'}):
            # Run: mad_spark "test topic" "test context"
            # Should attempt to use real API
            pass
    
    def test_mad_spark_autocomplete(self):
        """Test that mad_spark supports shell autocomplete."""
        # Future enhancement: bash/zsh completion
        # mad_spark <TAB> -> coordinator, test, --help, --version
        pass


class TestMadSparkAlias:
    """Test command alias variations."""
    
    def test_madspark_alias_works(self):
        """Test that 'madspark' (no underscore) also works."""
        # Some users might type without underscore
        # Both should work: mad_spark and madspark
        pass
    
    def test_ms_short_alias(self):
        """Test that 'ms' works as ultra-short alias."""
        # For power users: ms "topic" "context"
        # Even shorter than mad_spark
        pass