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
    from madspark.llm.providers.gemini import GeminiProvider, GENAI_AVAILABLE

    __all__.extend(["GeminiProvider", "GENAI_AVAILABLE"])
except ImportError:
    pass
