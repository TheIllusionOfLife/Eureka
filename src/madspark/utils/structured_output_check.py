"""Utility to check if structured output is available and functional."""

import logging
import importlib.util
from typing import Optional, Any

_structured_output_available: Optional[bool] = None


def is_structured_output_available(genai_client: Optional[Any] = None) -> bool:
    """Check if structured output is available and functional.
    
    This function checks if:
    1. The structured_idea_generator module can be imported
    2. The genai client is available (not in mock mode)
    3. The genai library supports structured output features
    
    Args:
        genai_client: Optional GenAI client to check
        
    Returns:
        True if structured output is available and functional, False otherwise
    """
    global _structured_output_available
    
    # Return cached result if available
    if _structured_output_available is not None:
        return _structured_output_available
    
    try:
        # Check if structured module can be imported using importlib
        spec = importlib.util.find_spec('madspark.agents.structured_idea_generator')
        if spec is None:
            _structured_output_available = False
            return False
        
        # Check if we're in mock mode
        if genai_client is None:
            _structured_output_available = False
            return False
            
        # Check if genai has required features using importlib
        genai_spec = importlib.util.find_spec('google.genai')
        if genai_spec is None:
            _structured_output_available = False
            return False
        
        try:
            from google.genai import types
            
            # Check for response_mime_type support (indicates structured output capability)
            if not hasattr(types.GenerateContentConfig, '__annotations__'):
                _structured_output_available = False
                return False
                
            config_annotations = types.GenerateContentConfig.__annotations__
            if 'response_mime_type' not in config_annotations:
                _structured_output_available = False
                return False
        except ImportError:
            # Failed to import types from google.genai
            _structured_output_available = False
            return False
            
        # All checks passed
        _structured_output_available = True
        return True
        
    except (ImportError, AttributeError) as e:
        logging.debug(f"Structured output not available: {e}")
        _structured_output_available = False
        return False
    except Exception as e:
        logging.warning(f"Error checking structured output availability: {e}")
        _structured_output_available = False
        return False


def reset_structured_output_cache():
    """Reset the cached availability check. Useful for testing."""
    global _structured_output_available
    _structured_output_available = None