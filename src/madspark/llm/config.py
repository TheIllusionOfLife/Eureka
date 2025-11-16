"""
LLM Provider Configuration.

Centralized configuration management for LLM providers.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model quality/speed tiers."""

    FAST = "fast"  # 4B - quick iterations, lower quality
    BALANCED = "balanced"  # 12B - better quality, slower
    QUALITY = "quality"  # Gemini - best quality, fastest, paid


@dataclass
class LLMConfig:
    """
    Complete LLM configuration.

    Controls provider selection, model tiers, caching, and performance tuning.
    """

    # Provider selection
    default_provider: str = "auto"  # auto, ollama, gemini
    model_tier: ModelTier = ModelTier.FAST
    fallback_enabled: bool = True

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model_fast: str = "gemma3:4b-it-qat"
    ollama_model_balanced: str = "gemma3:12b-it-qat"

    # Gemini settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    # Performance tuning
    max_retries: int = 2
    retry_delay_ms: int = 500
    default_temperature: float = 0.7

    # Token budgets (critical for Ollama performance)
    token_budgets: dict = field(
        default_factory=lambda: {
            "simple_score": 150,
            "evaluation": 500,
            "multi_evaluation": 1000,
            "idea_generation": 600,
            "advocacy": 800,
            "skepticism": 800,
            "logical_inference": 1000,
        }
    )

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_dir: str = ".cache/llm"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Load configuration from environment variables.

        Environment variables:
        - MADSPARK_LLM_PROVIDER: auto, ollama, gemini
        - MADSPARK_MODEL_TIER: fast, balanced, quality
        - MADSPARK_FALLBACK_ENABLED: true/false
        - OLLAMA_HOST: Ollama server URL
        - OLLAMA_MODEL_FAST: Fast tier model name
        - OLLAMA_MODEL_BALANCED: Balanced tier model name
        - GOOGLE_API_KEY: Gemini API key
        - GOOGLE_GENAI_MODEL: Gemini model name
        - MADSPARK_CACHE_ENABLED: true/false
        - MADSPARK_CACHE_TTL: TTL in seconds
        - MADSPARK_CACHE_DIR: Cache directory path
        """
        tier_str = os.getenv("MADSPARK_MODEL_TIER", "fast").lower()
        try:
            tier = ModelTier(tier_str)
        except ValueError:
            tier = ModelTier.FAST

        return cls(
            default_provider=os.getenv("MADSPARK_LLM_PROVIDER", "auto"),
            model_tier=tier,
            fallback_enabled=os.getenv("MADSPARK_FALLBACK_ENABLED", "true").lower()
            == "true",
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model_fast=os.getenv("OLLAMA_MODEL_FAST", "gemma3:4b-it-qat"),
            ollama_model_balanced=os.getenv(
                "OLLAMA_MODEL_BALANCED", "gemma3:12b-it-qat"
            ),
            gemini_api_key=os.getenv("GOOGLE_API_KEY"),
            gemini_model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
            cache_enabled=os.getenv("MADSPARK_CACHE_ENABLED", "true").lower()
            == "true",
            cache_ttl_seconds=int(os.getenv("MADSPARK_CACHE_TTL", "86400")),
            cache_dir=os.getenv("MADSPARK_CACHE_DIR", ".cache/llm"),
        )

    def get_ollama_model(self) -> str:
        """
        Get Ollama model based on current tier.

        Returns:
            Model name for the configured tier
        """
        if self.model_tier == ModelTier.FAST:
            return self.ollama_model_fast
        return self.ollama_model_balanced

    def get_token_budget(self, request_type: str) -> int:
        """
        Get token budget for request type.

        Args:
            request_type: Type of request (e.g., 'evaluation', 'advocacy')

        Returns:
            Maximum tokens to generate for this request type
        """
        return self.token_budgets.get(request_type, 500)

    def validate_api_key(self) -> bool:
        """
        Validate that API key is not a placeholder value.

        Returns:
            True if API key appears valid, False if it's a placeholder

        Warns if key looks like a placeholder (contains 'your-', 'replace', etc.)
        """
        if not self.gemini_api_key:
            return False

        placeholder_patterns = [
            "your-",
            "your_",
            "replace",
            "placeholder",
            "example",
            "xxx",
            "API_KEY_HERE",
        ]

        key_lower = self.gemini_api_key.lower()
        for pattern in placeholder_patterns:
            if pattern.lower() in key_lower:
                logger.warning(
                    f"API key appears to be a placeholder (contains '{pattern}'). "
                    f"Please set a valid GOOGLE_API_KEY in your environment."
                )
                return False

        return True


# Singleton config instance
_config_instance: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """
    Get singleton config instance.

    Lazily initializes from environment variables on first call.

    Returns:
        LLMConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = LLMConfig.from_env()
    return _config_instance


def reset_config() -> None:
    """
    Reset config singleton.

    Useful for testing or configuration reload.
    """
    global _config_instance
    _config_instance = None
