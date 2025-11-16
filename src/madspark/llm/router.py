"""
LLM Router with Automatic Fallback.

Smart routing between providers with caching integration.
"""

import logging
import threading
import time
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.config import get_config
from madspark.llm.cache import get_cache, reset_cache
from madspark.llm.exceptions import (
    AllProvidersFailedError,
    ProviderUnavailableError,
)

# Lazy imports for providers
OLLAMA_PROVIDER = None
GEMINI_PROVIDER = None

logger = logging.getLogger(__name__)


def _get_ollama_provider():
    """Lazy load OllamaProvider."""
    global OLLAMA_PROVIDER
    if OLLAMA_PROVIDER is None:
        try:
            from madspark.llm.providers.ollama import OllamaProvider

            OLLAMA_PROVIDER = OllamaProvider
        except ImportError:
            OLLAMA_PROVIDER = False  # Mark as unavailable
    return OLLAMA_PROVIDER if OLLAMA_PROVIDER else None


def _get_gemini_provider():
    """Lazy load GeminiProvider."""
    global GEMINI_PROVIDER
    if GEMINI_PROVIDER is None:
        try:
            from madspark.llm.providers.gemini import GeminiProvider

            GEMINI_PROVIDER = GeminiProvider
        except ImportError:
            GEMINI_PROVIDER = False
    return GEMINI_PROVIDER if GEMINI_PROVIDER else None


class LLMRouter:
    """
    Smart router for LLM providers with fallback and caching.

    Features:
    - Automatic provider selection based on input type
    - Fallback from primary to secondary provider
    - Response caching integration
    - Provider health monitoring
    - Usage metrics tracking

    Usage:
        router = LLMRouter()
        validated, response = router.generate_structured(
            prompt="Rate this idea",
            schema=MySchema,
            images=["photo.jpg"]  # Automatically routes to Ollama
        )
    """

    def __init__(
        self,
        primary_provider: Optional[str] = None,
        fallback_enabled: Optional[bool] = None,
        cache_enabled: Optional[bool] = None,
    ) -> None:
        """
        Initialize router.

        Args:
            primary_provider: Primary provider name (auto, ollama, gemini)
            fallback_enabled: Enable fallback to secondary provider
            cache_enabled: Enable response caching
        """
        config = get_config()

        self._primary_provider = primary_provider or config.default_provider
        self._fallback_enabled = (
            fallback_enabled if fallback_enabled is not None else config.fallback_enabled
        )
        self._cache_enabled = cache_enabled if cache_enabled is not None else config.cache_enabled

        # Lazy-loaded provider instances
        self._ollama: Optional[LLMProvider] = None
        self._gemini: Optional[LLMProvider] = None

        # Metrics tracking
        self._metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "ollama_calls": 0,
            "gemini_calls": 0,
            "fallback_triggers": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0,
        }

        logger.info(
            f"Router initialized: primary={self._primary_provider}, "
            f"fallback={self._fallback_enabled}, cache={self._cache_enabled}"
        )

    @property
    def ollama(self) -> Optional[LLMProvider]:
        """Lazy load Ollama provider."""
        if self._ollama is None:
            OllamaProvider = _get_ollama_provider()
            if OllamaProvider:
                try:
                    self._ollama = OllamaProvider()
                    logger.debug("Ollama provider initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Ollama: {e}")
        return self._ollama

    @property
    def gemini(self) -> Optional[LLMProvider]:
        """Lazy load Gemini provider."""
        if self._gemini is None:
            GeminiProvider = _get_gemini_provider()
            if GeminiProvider:
                try:
                    self._gemini = GeminiProvider()
                    logger.debug("Gemini provider initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini: {e}")
        return self._gemini

    def _select_provider(
        self,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        images: Optional[list[Union[str, Path]]] = None,
        force_provider: Optional[str] = None,
    ) -> tuple[LLMProvider, str]:
        """
        Select appropriate provider based on inputs.

        Args:
            files: PDF/document files (requires Gemini)
            urls: URLs to process (requires Gemini)
            images: Image files (Ollama or Gemini)
            force_provider: Force specific provider

        Returns:
            Tuple of (provider_instance, provider_name)

        Raises:
            ProviderUnavailableError: If no suitable provider available
        """
        if force_provider:
            if force_provider == "ollama":
                if self.ollama and self.ollama.health_check():
                    return self.ollama, "ollama"
                raise ProviderUnavailableError("Ollama requested but not available")
            elif force_provider == "gemini":
                if self.gemini and self.gemini.health_check():
                    return self.gemini, "gemini"
                raise ProviderUnavailableError("Gemini requested but not available")
            else:
                raise ValueError(f"Unknown provider: {force_provider}")

        # If files or URLs, use Gemini (native support)
        if files or urls:
            if self.gemini:
                return self.gemini, "gemini"
            raise ProviderUnavailableError("Gemini required for file/URL processing but not available")

        # For text/images, prefer Ollama (free)
        if self._primary_provider == "auto" or self._primary_provider == "ollama":
            if self.ollama and self.ollama.health_check():
                return self.ollama, "ollama"

        # Fallback to Gemini
        if self._primary_provider == "gemini" or self._fallback_enabled:
            if self.gemini:
                return self.gemini, "gemini"

        raise ProviderUnavailableError("No LLM providers available")

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        images: Optional[list[Union[str, Path]]] = None,
        force_provider: Optional[str] = None,
        use_cache: Optional[bool] = None,
        **kwargs,
    ) -> tuple[Any, LLMResponse]:
        """
        Generate structured output with automatic provider selection.

        Args:
            prompt: User prompt
            schema: Pydantic model for validation
            system_instruction: System instruction
            temperature: Sampling temperature
            files: PDF/document files (routes to Gemini)
            urls: URLs to process (routes to Gemini)
            images: Image files
            force_provider: Force specific provider
            use_cache: Override cache setting
            **kwargs: Additional provider-specific args

        Returns:
            tuple: (validated_pydantic_object, response_metadata)

        Raises:
            AllProvidersFailedError: If all providers fail
        """
        self._metrics["total_requests"] += 1

        # Check cache first
        should_use_cache = use_cache if use_cache is not None else self._cache_enabled
        cache = get_cache() if should_use_cache else None
        cache_key = None  # Initialize to avoid unbound variable in fallback

        if cache and cache.enabled:
            # Build cache key with all inputs that affect output
            cache_key_kwargs = {
                "provider": force_provider or "",
                "system_instruction": system_instruction,
            }
            # Include multimodal inputs to avoid incorrect cache hits
            # Normalize paths with resolve() for consistent caching
            if images:
                cache_key_kwargs["images"] = sorted(
                    [str(Path(p).resolve()) for p in images]
                )
            if files:
                cache_key_kwargs["files"] = sorted(
                    [str(Path(p).resolve()) for p in files]
                )
            if urls:
                cache_key_kwargs["urls"] = sorted(urls)

            cache_key = cache.make_key(
                prompt,
                schema,
                temperature,
                **cache_key_kwargs,
                **kwargs  # Include all other dynamic arguments
            )
            cached = cache.get(cache_key)
            if cached:
                self._metrics["cache_hits"] += 1
                # Reconstruct validated object from dict
                validated_dict, response = cached
                validated = schema.model_validate(validated_dict)
                logger.info("Cache hit - returning cached response")
                return validated, response

        # Select provider
        errors = []
        providers_tried = []

        try:
            provider, provider_name = self._select_provider(
                files=files, urls=urls, images=images, force_provider=force_provider
            )
            providers_tried.append(provider_name)

            # Generate structured output
            start = time.time()
            validated, response = provider.generate_structured(
                prompt=prompt,
                schema=schema,
                system_instruction=system_instruction,
                temperature=temperature,
                images=images,
                files=files,
                urls=urls,
                **kwargs,
            )
            latency = (time.time() - start) * 1000

            # Update metrics
            self._update_metrics(provider_name, response)

            # Cache result
            if cache and cache.enabled:
                cache.set(cache_key, (validated, response))

            logger.info(
                f"Generated via {provider_name} in {latency:.0f}ms "
                f"({response.tokens_used} tokens)"
            )
            return validated, response

        except (ProviderUnavailableError, Exception) as e:
            errors.append((providers_tried[-1] if providers_tried else "unknown", str(e)))
            logger.warning(f"Primary provider failed: {e}")

            # Try fallback if enabled
            if self._fallback_enabled and not force_provider:
                try:
                    fallback_provider = self._get_fallback_provider(providers_tried)
                    if fallback_provider:
                        provider_name = fallback_provider.provider_name
                        providers_tried.append(provider_name)
                        self._metrics["fallback_triggers"] += 1

                        logger.info(f"Attempting fallback to {provider_name}")

                        validated, response = fallback_provider.generate_structured(
                            prompt=prompt,
                            schema=schema,
                            system_instruction=system_instruction,
                            temperature=temperature,
                            images=images,
                            files=files,
                            urls=urls,
                            **kwargs,
                        )

                        self._update_metrics(provider_name, response)

                        if cache and cache.enabled and cache_key is not None:
                            cache.set(cache_key, (validated, response))

                        return validated, response

                except Exception as fallback_error:
                    errors.append((providers_tried[-1], str(fallback_error)))
                    logger.error(f"Fallback also failed: {fallback_error}")

        raise AllProvidersFailedError(f"All providers failed: {errors}")

    def _get_fallback_provider(
        self, already_tried: list[str]
    ) -> Optional[LLMProvider]:
        """
        Get fallback provider that hasn't been tried.

        Attempts to find an available provider that hasn't been used yet,
        performing health checks before returning.

        Args:
            already_tried: List of provider names already attempted

        Returns:
            Healthy fallback provider instance, or None if no fallback available
        """
        if "ollama" not in already_tried and self.ollama:
            try:
                if self.ollama.health_check():
                    return self.ollama
            except Exception as e:
                logger.warning(f"Ollama health check failed during fallback: {e}")

        if "gemini" not in already_tried and self.gemini:
            # Note: Gemini health check is less critical than Ollama since it's cloud-based,
            # but we check for consistency and to avoid returning an uninitialized provider
            if self.gemini.health_check():
                return self.gemini

        return None

    def _update_metrics(self, provider_name: str, response: LLMResponse) -> None:
        """
        Update usage metrics from a provider response.

        Args:
            provider_name: Name of the provider ("ollama" or "gemini")
            response: LLMResponse containing usage data
        """
        if provider_name == "ollama":
            self._metrics["ollama_calls"] += 1
        elif provider_name == "gemini":
            self._metrics["gemini_calls"] += 1

        self._metrics["total_tokens"] += response.tokens_used
        self._metrics["total_cost"] += response.cost
        self._metrics["total_latency_ms"] += response.latency_ms

    def get_metrics(self) -> dict:
        """
        Get router usage metrics.

        Returns:
            Dictionary with usage statistics
        """
        metrics = self._metrics.copy()
        if metrics["total_requests"] > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / metrics["total_requests"]
            metrics["avg_latency_ms"] = metrics["total_latency_ms"] / metrics["total_requests"]
        else:
            metrics["cache_hit_rate"] = 0.0
            metrics["avg_latency_ms"] = 0.0

        return metrics

    def reset_metrics(self) -> None:
        """Reset usage metrics."""
        for key in self._metrics:
            if isinstance(self._metrics[key], float):
                self._metrics[key] = 0.0
            else:
                self._metrics[key] = 0

    def health_status(self) -> dict:
        """
        Get health status of all providers.

        Returns:
            Dictionary with provider health status
        """
        return {
            "ollama": {
                "available": self.ollama is not None,
                "healthy": self.ollama.health_check() if self.ollama else False,
                "model": self.ollama.model_name if self.ollama else None,
            },
            "gemini": {
                "available": self.gemini is not None,
                "healthy": self.gemini.health_check() if self.gemini else False,
                "model": self.gemini.model_name if self.gemini else None,
            },
            "cache": {
                "enabled": get_cache().enabled,
                "stats": get_cache().stats(),
            },
        }


# Singleton router instance with thread safety
_router_instance: Optional[LLMRouter] = None
_router_lock = threading.Lock()


def get_router() -> LLMRouter:
    """
    Get singleton router instance.

    Thread-safe via double-checked locking pattern.

    Returns:
        LLMRouter instance
    """
    global _router_instance
    if _router_instance is None:
        with _router_lock:
            if _router_instance is None:  # Double-checked locking
                _router_instance = LLMRouter()
    return _router_instance


def reset_router() -> None:
    """Reset router singleton (for testing). Thread-safe."""
    global _router_instance
    with _router_lock:
        if _router_instance is not None:
            # Close associated cache to prevent resource leaks
            reset_cache()
        _router_instance = None
