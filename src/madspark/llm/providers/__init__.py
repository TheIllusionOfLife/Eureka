"""
LLM Provider Implementations.

This package contains concrete implementations of the LLMProvider interface.
"""

__all__ = []

# Conditionally export OllamaProvider if available
try:
    from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE  # noqa: F401

    __all__.extend(["OllamaProvider", "OLLAMA_AVAILABLE"])
except ImportError:
    # ollama Python package not installed
    OLLAMA_AVAILABLE = False
    __all__.append("OLLAMA_AVAILABLE")

# Conditionally export GeminiProvider if available
try:
    from madspark.llm.providers.gemini import (  # noqa: F401
        GENAI_AVAILABLE,
        GeminiProvider,
    )

    __all__.extend(["GeminiProvider", "GENAI_AVAILABLE"])
except ImportError:
    # google-genai package not installed
    GENAI_AVAILABLE = False
    __all__.append("GENAI_AVAILABLE")
