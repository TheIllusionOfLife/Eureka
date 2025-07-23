"""Shared Google GenAI client utilities.

This module provides centralized client initialization for all agents,
following the DRY principle to avoid code duplication.
"""
import os
import logging
from typing import Optional

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False


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