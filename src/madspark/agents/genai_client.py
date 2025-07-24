"""Shared Google GenAI client utilities.

This module provides centralized client initialization for all agents,
following the DRY principle to avoid code duplication.
"""
import os
import logging
from typing import Optional
from pathlib import Path

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv, find_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    
    def load_dotenv(*args, **kwargs):
        """Dummy function when python-dotenv is not available."""
        pass
    
    def find_dotenv(*args, **kwargs):
        """Dummy function when python-dotenv is not available."""
        return None


def get_genai_client() -> Optional['genai.Client']:
    """Get a configured Google GenAI client instance.
    
    Returns:
        A configured genai.Client instance if API key is available,
        None otherwise.
        
    Note:
        The client reads GOOGLE_API_KEY from environment directly.
        This is the expected behavior for the new google-genai SDK.
    """
    if not GENAI_AVAILABLE:
        return None
    
    # Check if we should use mock mode
    if get_mode() == "mock":
        return None
        
    api_key = os.getenv("GOOGLE_API_KEY")  # Environment variable lookup (test-safe)
    
    if api_key:  # test: Check environment variable
        # Create the client instance - it will read GOOGLE_API_KEY from environment
        return genai.Client()
    else:
        logging.warning("GOOGLE_API_KEY not found in environment")
        return None


def get_model_name() -> str:
    """Get the configured model name from environment.
    
    Returns:
        The model name from environment or default "gemini-2.5-flash".
    """
    return os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")


def load_env_file():
    """Load environment variables from .env file if it exists."""
    if DOTENV_AVAILABLE:
        # Try to find .env in the madspark directory
        current_dir = Path(__file__).parent.parent  # Go up to madspark dir
        env_path = current_dir / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try to find .env using find_dotenv
            env_file = find_dotenv()
            if env_file:
                load_dotenv(env_file)


def is_api_key_configured() -> bool:
    """Check if a valid API key is configured.
    
    Returns:
        True if API key is present and appears valid, False otherwise.
    """
    # First try to load from .env file
    load_env_file()
    
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    # Check if key exists and has a valid format
    # Google API keys typically start with "AIza"
    if api_key and api_key != "YOUR_API_KEY_HERE":
        # Basic validation - Google API keys start with AIza
        return api_key.startswith("AIza") or len(api_key) > 20
    
    return False


def get_mode() -> str:
    """Determine the operating mode (api or mock).
    
    Returns:
        'api' if API mode should be used, 'mock' otherwise.
        
    Priority:
    1. MADSPARK_MODE environment variable (explicit override)
    2. API key presence (auto-detection)
    3. Default to mock mode
    """
    # Check for explicit mode override
    explicit_mode = os.getenv("MADSPARK_MODE", "").lower()
    if explicit_mode in ["api", "mock"]:
        return explicit_mode
    
    # Auto-detect based on API key presence
    if is_api_key_configured():
        return "api"
    else:
        return "mock"