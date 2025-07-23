"""Configuration module for MadSpark with mock-first approach."""
import os
import logging
from typing import Literal, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Mode types
ModeType = Literal["mock", "direct", "adk"]

# Default to mock mode for safety
DEFAULT_MODE = "mock"

def get_mode() -> ModeType:
    """
    Get the current operation mode with mock as default.
    
    Mock mode is the default to ensure:
    1. CI/CD can run without API keys
    2. Development doesn't accidentally use API credits
    3. Tests are reproducible
    
    To use real API, explicitly set MADSPARK_MODE=direct
    """
    mode = os.getenv("MADSPARK_MODE", DEFAULT_MODE).lower()
    
    if mode not in ["mock", "direct", "adk"]:
        logger.warning(f"Invalid MADSPARK_MODE '{mode}', defaulting to 'mock'")
        return "mock"
    
    # Additional safety check for direct mode
    if mode == "direct":
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key or api_key.startswith("mock-") or api_key == "your-api-key-here":
            logger.warning("Direct mode requested but no valid API key found, falling back to mock")
            return "mock"
    
    return mode

def validate_environment() -> dict:
    """
    Validate environment configuration and return status.
    
    Returns:
        dict: Configuration status including mode, API availability, etc.
    """
    mode = get_mode()
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    # Check if API key looks valid (without exposing it)
    api_key_status = "not_set"
    if api_key:
        if api_key.startswith("mock-") or api_key == "your-api-key-here":
            api_key_status = "mock"
        else:
            api_key_status = "configured"
    
    return {
        "mode": mode,
        "api_key_status": api_key_status,
        "safe_for_ci": mode == "mock" or api_key_status == "mock",
        "warnings": []
    }

def require_api_key() -> str:
    """
    Get API key with validation, raising error if not in mock mode.
    
    Returns:
        str: The API key
        
    Raises:
        ValueError: If no valid API key in direct mode
    """
    mode = get_mode()
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    if mode == "mock":
        return "mock-api-key"
    
    if not api_key or api_key.startswith("mock-") or api_key == "your-api-key-here":
        raise ValueError(
            "Direct mode requires a valid GOOGLE_API_KEY. "
            "Either set the API key or use MADSPARK_MODE=mock"
        )
    
    return api_key

# Export key functions
__all__ = ["get_mode", "validate_environment", "require_api_key", "DEFAULT_MODE"]