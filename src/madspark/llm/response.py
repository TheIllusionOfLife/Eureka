"""
Unified LLM Response Metadata.

Provides a standardized response format for all LLM providers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LLMResponse:
    """
    Unified response metadata from any LLM provider.

    Attributes:
        text: Raw text response from the LLM
        provider: Name of the provider (e.g., 'ollama', 'gemini')
        model: Model used (e.g., 'gemma3:4b', 'gemma3:12b', 'gemini-2.5-flash')
        tokens_used: Total tokens consumed
        latency_ms: Response time in milliseconds
        cost: Estimated cost in USD
        cached: Whether this response was from cache
        timestamp: When the response was generated
    """

    text: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        """Concise string representation."""
        return (
            f"LLMResponse(provider={self.provider!r}, model={self.model!r}, "
            f"tokens={self.tokens_used}, latency={self.latency_ms:.0f}ms, "
            f"cost=${self.cost:.6f}, cached={self.cached})"
        )
