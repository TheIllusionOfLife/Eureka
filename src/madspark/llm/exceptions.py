"""
LLM Provider Exceptions.

Custom exceptions for LLM provider operations.
"""

__all__ = [
    "LLMProviderError",
    "ProviderUnavailableError",
    "AllProvidersFailedError",
    "SchemaValidationError",
    "RateLimitError",
    "AuthorizationError",
]


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    pass


class ProviderUnavailableError(LLMProviderError):
    """Provider is not available (server down, no API key, etc.)."""

    pass


class AllProvidersFailedError(LLMProviderError):
    """All providers failed after retries."""

    pass


class SchemaValidationError(LLMProviderError):
    """LLM output doesn't match expected schema."""

    pass


class RateLimitError(LLMProviderError):
    """
    API rate limit exceeded.

    Reserved for future retry logic with exponential backoff.
    """

    pass


class AuthorizationError(LLMProviderError):
    """
    User not authorized for this feature.

    Reserved for future premium/tiered features.
    """

    pass
