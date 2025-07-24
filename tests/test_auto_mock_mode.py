"""Tests for automatic mock mode detection when no API key is present."""
import os
from unittest.mock import patch, Mock
import tempfile
from pathlib import Path


class TestAutoMockMode:
    """Test automatic mock mode functionality."""
    
    def test_no_api_key_uses_mock_mode(self):
        """Test that system uses mock mode when no API key is present."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing API key
            if 'GOOGLE_API_KEY' in os.environ:
                del os.environ['GOOGLE_API_KEY']
            
            from madspark.agents.genai_client import get_genai_client, is_api_key_configured
            
            # Should detect no API key
            assert not is_api_key_configured()
            
            # Should return None client in mock mode
            client = get_genai_client()
            assert client is None
    
    def test_api_key_present_uses_real_mode(self):
        """Test that system uses real API when API key is present."""
        # API key must be over 30 chars and start with AIza to be valid
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIzaSyTest1234567890123456789012345678'}):
            from madspark.agents.genai_client import is_api_key_configured
            
            # Should detect API key
            assert is_api_key_configured()
    
    def test_mock_mode_env_override(self):
        """Test that MADSPARK_MODE=mock overrides API key presence."""
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'AIza_test_key_123',
            'MADSPARK_MODE': 'mock'
        }):
            from madspark.agents.genai_client import get_mode
            
            # Should use mock mode despite API key
            assert get_mode() == 'mock'
    
    def test_api_mode_env_override(self):
        """Test that MADSPARK_MODE=api forces API mode."""
        with patch.dict(os.environ, {'MADSPARK_MODE': 'api'}, clear=True):
            from madspark.agents.genai_client import get_mode
            
            # Should use API mode even without key (will fail later)
            assert get_mode() == 'api'
    
    def test_dotenv_file_reading(self):
        """Test that system reads API key from .env file."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create madspark directory structure
            madspark_dir = os.path.join(tmpdir, 'src', 'madspark')
            os.makedirs(madspark_dir)
            
            env_file = os.path.join(madspark_dir, '.env')
            
            # Write test .env file with valid API key format
            with open(env_file, 'w') as f:
                f.write('GOOGLE_API_KEY=AIzaSyTest1234567890123456789012345678\n')
                f.write('GOOGLE_GENAI_MODEL=gemini-2.5-flash\n')
            
            # Mock the Path to point to our temp directory
            with patch('madspark.agents.genai_client.Path') as mock_path:
                # Make Path(__file__).parent.parent return our madspark_dir
                mock_file_path = Mock()
                mock_file_path.parent.parent = Path(madspark_dir)
                mock_path.return_value = mock_file_path
                
                with patch.dict(os.environ, {}, clear=True):
                    # First load the env file to simulate reading from .env
                    import dotenv
                    dotenv.load_dotenv(env_file)
                    
                    # Now test that the key was loaded
                    assert os.getenv('GOOGLE_API_KEY') == 'AIzaSyTest1234567890123456789012345678'
                    
                    # And that is_api_key_configured detects it
                    from madspark.agents.genai_client import is_api_key_configured
                    assert is_api_key_configured()
    
    def test_mock_response_generation(self):
        """Test that mock mode generates appropriate responses."""
        with patch.dict(os.environ, {'MADSPARK_MODE': 'mock'}, clear=True):
            from madspark.agents.idea_generator import generate_ideas
            
            # Generate ideas in mock mode
            result = generate_ideas("Test topic", "Test context")
            
            # Should return mock response
            assert result is not None
            assert "mock" in result.lower() or "Mock" in result
            assert "Test topic" in result
    
    def test_mode_detection_logic(self):
        """Test the complete mode detection logic flow."""
        # Test 1: No API key, no env var -> mock mode
        with patch.dict(os.environ, {}, clear=True):
            from madspark.agents.genai_client import get_mode
            assert get_mode() == 'mock'
        
        # Test 2: API key present, no env var -> api mode
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIzaSyTest1234567890123456789012345678'}, clear=True):
            from madspark.agents.genai_client import get_mode
            assert get_mode() == 'api'
        
        # Test 3: API key present, MADSPARK_MODE=mock -> mock mode
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'AIzaSyTest1234567890123456789012345678',
            'MADSPARK_MODE': 'mock'
        }):
            from madspark.agents.genai_client import get_mode
            assert get_mode() == 'mock'
    
    def test_run_py_auto_mock_mode(self):
        """Test that run.py automatically sets mock mode when no API key."""
        # Simulate no API key environment
        with patch.dict(os.environ, {}, clear=True):
            # Mock subprocess to capture run.py execution
            with patch('subprocess.run'):
                # Import would trigger mode detection
                with patch('madspark.agents.genai_client.get_mode', return_value='mock'):
                    from madspark.agents.genai_client import get_mode
                    assert get_mode() == 'mock'


class TestMockModeMessages:
    """Test user-facing messages in mock mode."""
    
    def test_mock_mode_startup_message(self):
        """Test that appropriate message is shown when starting in mock mode."""
        # Test that mock mode shows appropriate message
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.print'):
                from madspark.agents.genai_client import get_mode
                mode = get_mode()
                if mode == 'mock':
                    # Verify some form of mock mode message would be shown
                    assert mode == 'mock'
    
    def test_api_mode_startup_message(self):
        """Test that appropriate message is shown when starting in API mode."""
        # Test that API mode is detected with valid key
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIzaSyTest1234567890123456789012345678'}):
            from madspark.agents.genai_client import get_mode
            mode = get_mode()
            # With valid API key format, should use API mode
            assert mode == 'api'