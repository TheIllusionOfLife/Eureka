"""
MadSpark LLM Provider Abstraction Layer.

This package provides a unified interface for multiple LLM providers
(Ollama, Gemini) with automatic fallback, response caching, and metrics.

Key Components:
- LLMProvider: Abstract base class for all providers
- LLMRouter: Smart routing with fallback logic
- LLMConfig: Configuration management
- LLMResponse: Unified response metadata
"""

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.config import LLMConfig, ModelTier, get_config, reset_config
from madspark.llm.exceptions import (
    LLMProviderError,
    ProviderUnavailableError,
    AllProvidersFailedError,
    SchemaValidationError,
)
from madspark.llm.cache import ResponseCache, get_cache, reset_cache
from madspark.llm.router import LLMRouter, get_router, reset_router
from madspark.llm.utils import should_use_router

__all__ = [
    # Base classes
    "LLMProvider",
    "LLMResponse",
    # Configuration
    "LLMConfig",
    "ModelTier",
    "get_config",
    "reset_config",
    # Caching
    "ResponseCache",
    "get_cache",
    "reset_cache",
    # Router
    "LLMRouter",
    "get_router",
    "reset_router",
    # Exceptions
    "LLMProviderError",
    "ProviderUnavailableError",
    "AllProvidersFailedError",
    "SchemaValidationError",
    # Utilities
    "should_use_router",
]
