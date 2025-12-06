"""
Centralized Model Definitions - Single Source of Truth.

This module contains all model name constants used across MadSpark.
When updating models, only this file needs to be changed (plus documentation).

Usage:
    from madspark.llm.models import OLLAMA_MODEL_FAST, GEMINI_MODEL_DEFAULT
"""

# =============================================================================
# Ollama Models (Local Inference)
# =============================================================================

# Fast tier - quick iterations, lower quality
OLLAMA_MODEL_FAST: str = "gemma3:4b-it-qat"

# Balanced tier - better quality, slower (DEFAULT)
OLLAMA_MODEL_BALANCED: str = "gemma3:12b-it-qat"

# =============================================================================
# Gemini Models (Cloud Inference)
# =============================================================================

# Default Gemini model
GEMINI_MODEL_DEFAULT: str = "gemini-2.5-flash"

# =============================================================================
# Default Configuration
# =============================================================================

# Default model tier (balanced for better quality by default)
DEFAULT_MODEL_TIER: str = "balanced"

# Legacy alias for backward compatibility
DEFAULT_MODEL: str = GEMINI_MODEL_DEFAULT
