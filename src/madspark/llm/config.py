"""
LLM Provider Configuration.

Centralized configuration management for LLM providers.
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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
    # TODO: Implement retry logic in LLMRouter.generate_structured() for Phase 2
    # These settings are defined but not yet used by any provider or router code.
    max_retries: int = 2
    retry_delay_ms: int = 500
    default_temperature: float = 0.7

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_max_size_mb: int = 1000  # 1GB default - prevents unbounded disk usage
    # Default uses absolute path to avoid permission issues from arbitrary directories
    cache_dir: str = field(default_factory=lambda: str(Path.home() / ".cache" / "madspark" / "llm"))

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
        - MADSPARK_CACHE_MAX_SIZE_MB: Maximum cache size in MB
        - MADSPARK_CACHE_DIR: Cache directory path
        """
        tier_str = os.getenv("MADSPARK_MODEL_TIER", "fast").lower()
        try:
            tier = ModelTier(tier_str)
        except ValueError:
            tier = ModelTier.FAST

        # Parse cache TTL with validation
        cache_ttl = 86400  # Default: 24 hours
        cache_ttl_env = os.getenv("MADSPARK_CACHE_TTL")
        if cache_ttl_env:
            try:
                cache_ttl = int(cache_ttl_env)
                if cache_ttl < 0:
                    logger.warning(
                        f"Invalid MADSPARK_CACHE_TTL value '{cache_ttl_env}' (negative). "
                        f"Using default: 86400"
                    )
                    cache_ttl = 86400
            except ValueError:
                logger.warning(
                    f"Invalid MADSPARK_CACHE_TTL value '{cache_ttl_env}' (not an integer). "
                    f"Using default: 86400"
                )
                cache_ttl = 86400

        # Parse cache max size with validation
        cache_max_size_mb = 1000  # Default: 1GB
        cache_max_size_env = os.getenv("MADSPARK_CACHE_MAX_SIZE_MB")
        if cache_max_size_env:
            try:
                cache_max_size_mb = int(cache_max_size_env)
                if cache_max_size_mb < 0:
                    logger.warning(
                        f"Invalid MADSPARK_CACHE_MAX_SIZE_MB value '{cache_max_size_env}' (negative). "
                        f"Using default: 1000"
                    )
                    cache_max_size_mb = 1000
            except ValueError:
                logger.warning(
                    f"Invalid MADSPARK_CACHE_MAX_SIZE_MB value '{cache_max_size_env}' (not an integer). "
                    f"Using default: 1000"
                )
                cache_max_size_mb = 1000

        # Use absolute path for cache to avoid permission issues when CLI runs from arbitrary directories
        default_cache_dir = str(Path.home() / ".cache" / "madspark" / "llm")
        cache_dir = os.getenv("MADSPARK_CACHE_DIR", default_cache_dir)

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
            cache_ttl_seconds=cache_ttl,
            cache_max_size_mb=cache_max_size_mb,
            cache_dir=cache_dir,
        )

    def get_ollama_model(self) -> str:
        """
        Get Ollama model based on current tier.

        Note: QUALITY tier returns balanced model since Ollama doesn't have
        a higher tier. For true quality tier, use Gemini provider directly
        via --provider gemini flag.

        Returns:
            Model name for the configured tier
        """
        if self.model_tier == ModelTier.FAST:
            return self.ollama_model_fast
        # Both BALANCED and QUALITY use the same model
        # QUALITY tier with Ollama falls back to balanced; use Gemini for true quality
        return self.ollama_model_balanced

    def validate_api_key(self) -> bool:
        """
        Validate that API key is not a placeholder value.

        Returns:
            True if API key appears valid, False if it's a placeholder

        Warns if key looks like a placeholder (contains 'your-', 'replace', etc.)
        """
        if not self.gemini_api_key:
            return False

        # Google API keys are typically 39 characters
        # Minimum length check to catch truncated or invalid keys
        min_key_length = 20
        if len(self.gemini_api_key) < min_key_length:
            logger.warning(
                f"API key too short ({len(self.gemini_api_key)} chars, minimum {min_key_length}). "
                f"Please set a valid GOOGLE_API_KEY in your environment."
            )
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


# Singleton config instance with thread safety
_config_instance: Optional[LLMConfig] = None
_config_lock = threading.Lock()


def get_config() -> LLMConfig:
    """
    Get singleton config instance.

    Lazily initializes from environment variables on first call.
    Thread-safe via double-checked locking pattern.

    Returns:
        LLMConfig instance
    """
    global _config_instance
    if _config_instance is None:
        with _config_lock:
            if _config_instance is None:  # Double-checked locking
                _config_instance = LLMConfig.from_env()
    return _config_instance


def reset_config() -> None:
    """
    Reset config singleton.

    Useful for testing or configuration reload.
    Thread-safe via lock.
    """
    global _config_instance
    with _config_lock:
        _config_instance = None
