"""Tests for automatic mock mode detection when no API key is present."""
import os
import pytest
from unittest.mock import patch, Mock
import tempfile
import shutil


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
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIza_test_key_123'}):
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
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, '.env')
            
            # Write test .env file
            with open(env_file, 'w') as f:
                f.write('GOOGLE_API_KEY="AIza_test_key_from_env"\n')
                f.write('GOOGLE_GENAI_MODEL="gemini-2.5-flash"\n')
            
            # Mock the .env file location
            with patch('madspark.agents.genai_client.find_dotenv', return_value=env_file):
                with patch.dict(os.environ, {}, clear=True):
                    from madspark.agents.genai_client import load_env_file, is_api_key_configured
                    
                    # Load the env file
                    load_env_file()
                    
                    # Should detect API key from file
                    assert is_api_key_configured()
                    assert os.getenv('GOOGLE_API_KEY') == 'AIza_test_key_from_env'
    
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
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIza_test'}, clear=True):
            from madspark.agents.genai_client import get_mode
            assert get_mode() == 'api'
        
        # Test 3: API key present, MADSPARK_MODE=mock -> mock mode
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'AIza_test',
            'MADSPARK_MODE': 'mock'
        }):
            from madspark.agents.genai_client import get_mode
            assert get_mode() == 'mock'
    
    def test_run_py_auto_mock_mode(self):
        """Test that run.py automatically sets mock mode when no API key."""
        # This will test the run.py script's ability to detect and set mode
        # We'll implement this after updating run.py
        pass


class TestMockModeMessages:
    """Test user-facing messages in mock mode."""
    
    def test_mock_mode_startup_message(self):
        """Test that appropriate message is shown when starting in mock mode."""
        # This will test that run.py shows a message like:
        # "No API key found. Running in mock mode..."
        pass
    
    def test_api_mode_startup_message(self):
        """Test that appropriate message is shown when starting in API mode."""
        # This will test that run.py shows a message like:
        # "API key found. Running with Google Gemini API..."
        pass