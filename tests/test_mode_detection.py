"""Test mode detection behavior to ensure mock mode is default."""
import os
import sys
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.agents.genai_client import get_mode, is_api_key_configured


class TestModeDetection:
    """Test that mode detection respects explicit MADSPARK_MODE settings."""
    
    def test_explicit_mock_mode_overrides_api_key(self):
        """When MADSPARK_MODE=mock, should use mock even with API key."""
        with patch.dict(os.environ, {
            'MADSPARK_MODE': 'mock',
            'GOOGLE_API_KEY': 'AIza1234567890123456789012345678901234567'
        }):
            assert get_mode() == 'mock'
    
    def test_explicit_api_mode_without_key_still_api(self):
        """When MADSPARK_MODE=api, should return api even without key."""
        with patch.dict(os.environ, {
            'MADSPARK_MODE': 'api'
        }, clear=True):
            assert get_mode() == 'api'
    
    def test_no_mode_with_api_key_uses_api(self):
        """Without explicit mode but with API key, should use api."""
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'AIza1234567890123456789012345678901234567'
        }):
            if 'MADSPARK_MODE' in os.environ:
                del os.environ['MADSPARK_MODE']
            assert get_mode() == 'api'
    
    def test_no_mode_no_key_uses_mock(self):
        """Without explicit mode and no API key, should use mock."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_mode() == 'mock'
    
    def test_setup_sh_mock_mode_respected(self):
        """Simulate setup.sh creating .env with MADSPARK_MODE=mock."""
        # This tests that when setup.sh sets MADSPARK_MODE=mock in .env,
        # it should be respected even if API key exists
        with patch.dict(os.environ, {
            'MADSPARK_MODE': 'mock',
            'GOOGLE_API_KEY': 'AIza1234567890123456789012345678901234567'
        }):
            # The mode should be mock despite having an API key
            assert get_mode() == 'mock'
            
            # Verify that is_api_key_configured still returns True
            # (the key exists, we just chose not to use it)
            assert is_api_key_configured() is True