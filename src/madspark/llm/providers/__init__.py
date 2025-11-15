"""
LLM Provider Implementations.

This package contains concrete implementations of the LLMProvider interface.
"""

from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE

__all__ = [
    "OllamaProvider",
    "OLLAMA_AVAILABLE",
]

# Conditionally export GeminiProvider if available
try:
    from madspark.llm.providers.gemini import GeminiProvider as _GeminiProvider
    from madspark.llm.providers.gemini import GENAI_AVAILABLE as _GENAI_AVAILABLE

    # Re-export with original names
    GeminiProvider = _GeminiProvider  # noqa: F841
    GENAI_AVAILABLE = _GENAI_AVAILABLE  # noqa: F841
    __all__.extend(["GeminiProvider", "GENAI_AVAILABLE"])
except ImportError:
    pass
