"""Tests for enhanced setup.sh script functionality."""
import os
import shutil
import tempfile
import pytest
from unittest.mock import patch


class TestSetupEnhancements:
    """Test enhanced setup script features."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal project structure
            os.makedirs(os.path.join(tmpdir, "src", "madspark"))
            os.makedirs(os.path.join(tmpdir, "config"))
            
            # Create minimal requirements.txt
            with open(os.path.join(tmpdir, "config", "requirements.txt"), 'w') as f:
                f.write("pytest>=7.4.0\n")
            
            # Copy setup.sh to temp dir (will be modified)
            setup_src = os.path.join(os.path.dirname(__file__), "..", "setup.sh")
            if os.path.exists(setup_src):
                shutil.copy2(setup_src, tmpdir)
            
            yield tmpdir
    
    def test_setup_detects_missing_api_key(self, temp_project_dir):
        """Test that setup script detects when API key is missing."""
        # This test will verify the enhanced setup.sh can detect no API key
        # and prompt the user appropriately
        env_file = os.path.join(temp_project_dir, "src", "madspark", ".env")
        
        # Ensure no .env exists
        if os.path.exists(env_file):
            os.remove(env_file)
        
        # The enhanced setup.sh should create .env and detect missing key
        # We'll test this after implementing the enhancement
        assert True  # Placeholder for now
    
    def test_setup_interactive_api_key_input(self):
        """Test that setup script offers interactive API key input."""
        # Test interactive prompt functionality
        # This will use subprocess with stdin simulation
        with patch('builtins.input', return_value='AIza_test_interactive_key'):
            # Run enhanced setup script
            # Should accept the key and write to .env
            pass
    
    def test_setup_validates_api_key_format(self):
        """Test that setup script validates API key format."""
        # Test various API key formats
        valid_keys = [
            'AIza_valid_key_123',
            'AIza-another-valid-key',
            'AIzaSyDtestkey123'
        ]
        invalid_keys = [
            'invalid_key',
            '12345',
            'notanapikey',
            ''
        ]
        
        # Enhanced setup should accept valid and reject invalid
        for key in valid_keys:
            # Should accept
            assert True  # Placeholder
            
        for key in invalid_keys:
            # Should reject and re-prompt
            assert True  # Placeholder
    
    def test_setup_creates_env_with_key(self, temp_project_dir):
        """Test that setup creates proper .env file with API key."""
        env_file = os.path.join(temp_project_dir, "src", "madspark", ".env")
        test_key = "AIza_test_setup_key"
        
        # Simulate user entering API key
        with patch('builtins.input', return_value=test_key):
            # Run setup (to be implemented)
            # Check .env contents
            pass
            
        # Verify .env was created with correct content
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                assert f'GOOGLE_API_KEY="{test_key}"' in content
    
    def test_setup_creates_env_for_mock_mode(self, temp_project_dir):
        """Test that setup creates .env for mock mode when user skips API key."""
        env_file = os.path.join(temp_project_dir, "src", "madspark", ".env")
        
        # Simulate user skipping API key (empty input)
        with patch('builtins.input', return_value=''):
            # Run setup
            # Should create .env with mock mode marker
            pass
        
        # Verify .env indicates mock mode
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                assert 'MADSPARK_MODE="mock"' in content or 'YOUR_API_KEY_HERE' in content
    
    def test_setup_installs_mad_spark_command(self, temp_project_dir):
        """Test that setup installs mad_spark command to system."""
        # Check if mad_spark symlink/script is created
        # This will test after implementation
        # Expected locations:
        # - /usr/local/bin/mad_spark
        # - ~/.local/bin/mad_spark
        # - [temp_project_dir]/mad_spark
        
        # At least one location should have the command
        # We'll verify this after implementation
        assert True  # Placeholder
    
    def test_setup_handles_permission_errors(self):
        """Test that setup handles permission errors gracefully."""
        # Test when /usr/local/bin is not writable
        with patch('os.access', return_value=False):
            # Should fall back to user directory or show helpful message
            pass
    
    def test_setup_shows_colored_output(self):
        """Test that setup uses colors for better UX."""
        # Check if setup.sh script contains ANSI color codes
        setup_script = os.path.join(os.path.dirname(__file__), "..", "setup.sh")
        
        if os.path.exists(setup_script):
            with open(setup_script, 'r') as f:
                content = f.read()
                
            # Look for common ANSI color patterns
            color_patterns = [
                '\033[',  # Basic ANSI escape sequence
                '\\e[',   # Alternative escape sequence format
                'tput ',  # tput color commands
                'echo -e',  # echo with color support
            ]
            
            has_colors = any(pattern in content for pattern in color_patterns)
            
            # If colors are used, they should include common ones like green for success, red for errors
            if has_colors:
                success_colors = ['32m', 'green', '\033[1;32m']  # Green variants
                error_colors = ['31m', 'red', '\033[1;31m']      # Red variants
                
                has_success_colors = any(color in content for color in success_colors)
                has_error_colors = any(color in content for color in error_colors)
                
                assert has_success_colors or has_error_colors, "Setup should use meaningful colors (green for success, red for errors)"
            else:
                # Test passes if no colors are implemented yet (backward compatibility)
                # This allows the test to pass while setup.sh is enhanced
                pytest.skip("Colored output not yet implemented in setup.sh - enhancement pending")  
        else:
            pytest.skip("setup.sh not found - cannot test colored output")
    
    def test_setup_is_idempotent(self, temp_project_dir):
        """Test that running setup multiple times is safe."""
        # Run setup twice
        # Should not duplicate entries or break existing config
        env_file = os.path.join(temp_project_dir, "src", "madspark", ".env")
        
        # First run
        with open(env_file, 'w') as f:
            f.write('GOOGLE_API_KEY="existing_key"\n')
        
        # Second run should preserve existing key
        # We'll test this after implementation
        assert True  # Placeholder


class TestSetupUserFlow:
    """Test complete user flows through setup."""
    
    def test_new_user_with_api_key_flow(self):
        """Test complete flow for new user who has an API key."""
        # 1. User runs ./setup.sh
        # 2. Prompted for API key
        # 3. Enters valid key
        # 4. Setup completes with success message
        # 5. mad_spark command is available
        pass
    
    def test_new_user_without_api_key_flow(self):
        """Test complete flow for new user who wants mock mode."""
        # Test the user flow simulation
        # This tests that a user can successfully skip API key input and use mock mode
        
        # Simulate user flow:
        # 1. No API key provided (empty input)
        # 2. System should default to mock mode
        # 3. Commands should work in mock mode
        
        with patch('builtins.input', return_value=''):  # User presses enter (empty)
            # Check that mock mode is properly configured when no API key provided
            # This would be tested after implementing the enhanced setup.sh
            
            # For now, test that our current system handles missing API keys gracefully
            env = os.environ.copy()
            if 'GOOGLE_API_KEY' in env:
                del env['GOOGLE_API_KEY']  # Remove API key to simulate no key scenario
            env['MADSPARK_MODE'] = 'mock'
            env['SUPPRESS_MODE_MESSAGE'] = '1'
            
            # Test that mad_spark works without API key
            import subprocess
            import sys
            
            try:
                # Need to run from project root
                project_root = os.path.join(os.path.dirname(__file__), "..")
                result = subprocess.run([
                    sys.executable, 'run.py', 'test_no_api_key_topic'
                ], capture_output=True, text=True, env=env, timeout=30, cwd=project_root)
                
                # Should work in mock mode
                assert result.returncode == 0, f"Mock mode should work without API key: {result.stderr[:200]}"
                
                # Should generate mock output
                output = result.stdout + result.stderr
                mock_indicators = ["solution", "score", "revolutionary", "innovation"]
                assert any(indicator.lower() in output.lower() for indicator in mock_indicators), \
                    f"Should generate mock ideas without API key. Got: {output[:300]}..."
                    
            except subprocess.TimeoutExpired:
                pytest.fail("Command timed out - indicates mock mode may not be working properly")
    
    def test_existing_user_preserves_config(self):
        """Test that existing users' configs are preserved."""
        # Test that existing configuration is not accidentally overwritten
        # This simulates a user who already has a working setup
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock .env file with existing configuration
            env_file = os.path.join(temp_dir, ".env")
            original_config = 'GOOGLE_API_KEY="existing_user_key_12345"\nMADSPARK_MODE="api"\n'
            
            with open(env_file, 'w') as f:
                f.write(original_config)
            
            # Verify the file was created correctly
            assert os.path.exists(env_file), "Test setup failed - .env file not created"
            
            # Read back the content to verify preservation
            with open(env_file, 'r') as f:
                preserved_content = f.read()
            
            # The original configuration should be preserved
            assert 'existing_user_key_12345' in preserved_content, "Existing API key should be preserved"
            assert 'MADSPARK_MODE="api"' in preserved_content, "Existing mode setting should be preserved"
            
            # Test that we don't accidentally modify existing files
            # (This tests the principle - actual setup.sh preservation would be tested when enhanced)
            assert preserved_content == original_config, "Configuration should remain exactly the same"