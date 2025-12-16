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

    def __init__(
        self,
        message: str = "All providers failed",
        errors: dict[str, str] | None = None,
        prompt: str | None = None,
    ) -> None:
        """
        Initialize with optional error details.

        Args:
            message: Error message
            errors: Dict mapping provider names to error messages
            prompt: Truncated prompt that caused the failure (for debugging)
        """
        self.errors = errors or {}
        self.prompt = prompt
        # Build detailed message if errors provided
        if errors:
            details = ", ".join(f"{p}: {e}" for p, e in errors.items())
            message = f"{message}: {details}"
        super().__init__(message)


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
