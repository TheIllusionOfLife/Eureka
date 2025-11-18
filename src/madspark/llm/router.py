"""
LLM Router with Automatic Fallback.

Smart routing between providers with caching integration.
"""

import hashlib
import json
import logging
import threading
import time
from typing import Any, Optional, Type, Union, TYPE_CHECKING
from typing_extensions import TypedDict
from pathlib import Path
from pydantic import BaseModel, ValidationError

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.config import get_config, ModelTier
from madspark.llm.cache import get_cache, reset_cache
from madspark.llm.exceptions import (
    AllProvidersFailedError,
    ProviderUnavailableError,
    SchemaValidationError,
)

if TYPE_CHECKING:
    from madspark.llm.config import LLMConfig

# Security constants
MAX_PROMPT_LENGTH = 100_000  # Characters - prevents resource exhaustion
MAX_FILE_SIZE_MB = 50  # Maximum file size in MB for multimodal inputs


def _compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file contents for cache invalidation.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file contents (first 16 chars for brevity)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file exceeds size limit
        PermissionError: If file is not readable
    """
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file size before reading
    try:
        file_size = file_path.stat().st_size
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File {file_path.name} ({file_size / 1024 / 1024:.1f}MB) "
                f"exceeds maximum size of {MAX_FILE_SIZE_MB}MB"
            )
    except (OSError, PermissionError) as e:
        raise PermissionError(f"Cannot access file {file_path}: {e}")

    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    except (IOError, OSError) as e:
        raise PermissionError(f"Cannot read file {file_path}: {e}")

    # Use first 16 chars of hash for reasonable cache key length
    return hasher.hexdigest()[:16]

# Shared metrics key constants - prevents key mismatch bugs between router and CLI
METRIC_TOTAL_REQUESTS = "total_requests"
METRIC_CACHE_HITS = "cache_hits"
METRIC_OLLAMA_CALLS = "ollama_calls"
METRIC_GEMINI_CALLS = "gemini_calls"
METRIC_FALLBACK_TRIGGERS = "fallback_triggers"
METRIC_TOTAL_TOKENS = "total_tokens"
METRIC_TOTAL_COST = "total_cost"
METRIC_TOTAL_LATENCY_MS = "total_latency_ms"
METRIC_CACHE_HIT_RATE = "cache_hit_rate"
METRIC_AVG_LATENCY_MS = "avg_latency_ms"


class RouterMetrics(TypedDict):
    """Type-safe metrics dictionary for router usage tracking."""

    total_requests: int
    cache_hits: int
    ollama_calls: int
    gemini_calls: int
    fallback_triggers: int
    total_tokens: int
    total_cost: float
    total_latency_ms: float

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
        except ImportError as e:
            logger.debug(f"OllamaProvider not available: {e}")
            OLLAMA_PROVIDER = False  # Mark as unavailable
    return OLLAMA_PROVIDER if OLLAMA_PROVIDER else None


def _get_gemini_provider():
    """Lazy load GeminiProvider."""
    global GEMINI_PROVIDER
    if GEMINI_PROVIDER is None:
        try:
            from madspark.llm.providers.gemini import GeminiProvider

            GEMINI_PROVIDER = GeminiProvider
        except ImportError as e:
            logger.debug(f"GeminiProvider not available: {e}")
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
        config: Optional["LLMConfig"] = None,
    ) -> None:
        """
        Initialize router with optional explicit configuration.

        Args:
            primary_provider: Primary provider name (auto, ollama, gemini) - overrides config
            fallback_enabled: Enable fallback to secondary provider - overrides config
            cache_enabled: Enable response caching - overrides config
            config: Pre-initialized LLMConfig object (optional). If not provided,
                   creates config from environment variables via get_config().

        Example:
            # Explicit configuration (thread-safe, recommended for concurrent use)
            custom_config = LLMConfig(default_provider="ollama", model_tier=ModelTier.FAST)
            router = LLMRouter(config=custom_config)

            # Parameter overrides with config
            router = LLMRouter(primary_provider="gemini", config=custom_config)

            # Environment-based (backward compatible)
            router = LLMRouter()  # Reads from env vars via get_config()
        """
        # Use provided config or get singleton config from environment
        if config is None:
            config = get_config()

        # Store config for later use (thread-safe)
        self._config = config

        # Apply parameter overrides (parameters take precedence over config)
        self._primary_provider = primary_provider or config.default_provider
        self._fallback_enabled = (
            fallback_enabled if fallback_enabled is not None else config.fallback_enabled
        )
        self._cache_enabled = cache_enabled if cache_enabled is not None else config.cache_enabled

        # Lazy-loaded provider instances
        self._ollama: Optional[LLMProvider] = None
        self._gemini: Optional[LLMProvider] = None

        # Metrics tracking with thread safety (TypedDict for type safety)
        self._metrics: RouterMetrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "ollama_calls": 0,
            "gemini_calls": 0,
            "fallback_triggers": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0.0,
        }
        self._metrics_lock = threading.Lock()  # Thread-safe metrics updates

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

        # If quality tier requested, prefer Gemini for best results
        if self._config.model_tier == ModelTier.QUALITY and not force_provider:
            if self.gemini and self.gemini.health_check():
                logger.info("Quality tier requested, using Gemini for best results")
                return self.gemini, "gemini"
            # If Gemini unavailable, fallback to Ollama with warning
            logger.warning("Quality tier requested but Gemini unavailable, falling back to Ollama balanced model")

        # For text/images, prefer Ollama (free) but check multimodal support for images
        if self._primary_provider == "auto" or self._primary_provider == "ollama":
            if self.ollama and self.ollama.health_check():
                # Check if Ollama supports multimodal when images are provided
                if images and not self.ollama.supports_multimodal:
                    logger.info("Ollama model doesn't support images, falling back to Gemini")
                else:
                    return self.ollama, "ollama"

        # Fallback to Gemini
        if self._primary_provider == "gemini" or self._fallback_enabled:
            if self.gemini and self.gemini.health_check():
                return self.gemini, "gemini"

        raise ProviderUnavailableError("No LLM providers available")

    def generate_structured_batch(
        self,
        prompts: list[str],
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        images: Optional[list[Union[str, Path]]] = None,
        force_provider: Optional[str] = None,
        use_cache: Optional[bool] = None,
        **kwargs,
    ) -> tuple[list[Any], LLMResponse]:
        """
        Generate structured output for multiple prompts (batch operation).

        Processes each prompt through the router with caching and fallback support.
        Aggregates metrics and returns combined response metadata.

        Args:
            prompts: List of user prompts to process
            schema: Pydantic model for validation
            system_instruction: System instruction (shared across all prompts)
            temperature: Sampling temperature
            files: PDF/document files (routes to Gemini)
            urls: URLs to process (routes to Gemini)
            images: Image files (shared across all prompts)
            force_provider: Force specific provider
            use_cache: Override cache setting
            **kwargs: Additional provider-specific args

        Returns:
            tuple: (list of validated_pydantic_objects, aggregated response_metadata)

        Raises:
            TypeError: If prompts is None or not a list, or if individual prompts are not strings
            ValueError: If individual prompts exceed MAX_PROMPT_LENGTH
            AllProvidersFailedError: If all providers fail for any prompt.
                **Fail-fast behavior**: Processing stops immediately on first failure.
                Previously processed results are lost. This ensures consistent error
                reporting but does not support partial success

        Note:
            Sequential Processing: Prompts are processed one at a time (O(N) API calls).
            This is intentional to maintain consistent error handling and avoid
            complexity of managing concurrent provider state. For async batch processing,
            consider using AsyncCoordinator with gather() instead.
        """
        # Input validation
        if prompts is None:
            raise TypeError("Prompts cannot be None")

        if not isinstance(prompts, list):
            raise TypeError(f"Prompts must be a list, got {type(prompts).__name__}")

        # Validate individual prompts
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, str):
                raise TypeError(
                    f"Prompt {i} must be str, got {type(prompt).__name__}"
                )
            if len(prompt) > MAX_PROMPT_LENGTH:
                raise ValueError(
                    f"Prompt {i} exceeds max length ({len(prompt)} > {MAX_PROMPT_LENGTH})"
                )

        # Handle empty list case
        if not prompts:
            return [], LLMResponse(
                text="",
                provider="none",
                model="none",
                tokens_used=0,
                latency_ms=0.0,
                cost=0.0,
            )

        # Process each prompt
        results = []
        total_tokens = 0
        total_cost = 0.0
        total_latency = 0.0
        provider_counts: dict[str, int] = {}  # Track count of each provider used

        for prompt in prompts:
            validated, response = self.generate_structured(
                prompt=prompt,
                schema=schema,
                system_instruction=system_instruction,
                temperature=temperature,
                files=files,
                urls=urls,
                images=images,
                force_provider=force_provider,
                use_cache=use_cache,
                **kwargs,
            )
            results.append(validated)
            total_tokens += response.tokens_used
            total_cost += response.cost
            total_latency += response.latency_ms
            # Track provider usage counts (not just unique providers)
            provider_counts[response.provider] = provider_counts.get(response.provider, 0) + 1

        # Determine primary provider used
        # If multiple providers used (due to fallback), report the one used most frequently
        primary_provider = max(provider_counts.keys(), key=lambda p: provider_counts[p])

        # Create aggregated response
        aggregated_response = LLMResponse(
            text=f"Batch of {len(prompts)} items processed",
            provider=primary_provider,
            model="batch",
            tokens_used=total_tokens,
            latency_ms=total_latency,
            cost=total_cost,
        )

        return results, aggregated_response

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
            ValueError: If prompt is empty or schema is invalid
        """
        # Input validation
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Security: prevent resource exhaustion via extremely long prompts
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt length ({len(prompt)}) exceeds maximum allowed ({MAX_PROMPT_LENGTH})"
            )

        if schema is None:
            raise ValueError("Schema cannot be None")

        try:
            if not issubclass(schema, BaseModel):
                raise ValueError("Schema must be a Pydantic BaseModel subclass")
        except TypeError:
            # issubclass raises TypeError if schema is not a class
            raise ValueError("Schema must be a Pydantic BaseModel subclass")

        with self._metrics_lock:
            self._metrics["total_requests"] += 1

        # Check cache first
        should_use_cache = use_cache if use_cache is not None else self._cache_enabled
        cache = get_cache() if should_use_cache else None

        # Early validation of file inputs (fail fast before provider call)
        if images:
            for img in images:
                path = Path(img).resolve()
                if not path.exists():
                    raise ValueError(f"Image file not found: {path}")
                if not path.is_file():
                    raise ValueError(f"Image path is not a file: {path}")
                # Enforce file size limit to prevent resource exhaustion
                file_size_mb = path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    raise ValueError(
                        f"Image file too large: {path} ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                    )
        if files:
            for file_path in files:
                path = Path(file_path).resolve()
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {path}")
                if not path.is_file():
                    raise ValueError(f"Path is not a file: {path}")
                # Enforce file size limit to prevent resource exhaustion
                file_size_mb = path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    raise ValueError(
                        f"File too large: {path} ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                    )

        # Build base cache key kwargs (shared between lookup and storage)
        base_cache_kwargs = {
            "system_instruction": system_instruction,
        }
        # Include multimodal inputs to avoid incorrect cache hits
        # For files, include content hash to detect changes (not just path)
        if images:
            base_cache_kwargs["images"] = sorted(
                [f"{Path(p).resolve()}:{_compute_file_hash(Path(p))}" for p in images]
            )
        if files:
            base_cache_kwargs["files"] = sorted(
                [f"{Path(p).resolve()}:{_compute_file_hash(Path(p))}" for p in files]
            )
        if urls:
            base_cache_kwargs["urls"] = sorted(urls)

        # Cache lookup: try to find cached response
        # Key includes actual provider name to prevent cache poisoning
        if cache and cache.enabled:
            if force_provider:
                # User requested specific provider, only check that provider's cache
                cache_key = cache.make_key(
                    prompt, schema, temperature,
                    provider=force_provider,
                    **base_cache_kwargs,
                    **kwargs
                )
                cached = cache.get(cache_key)
                if cached:
                    try:
                        validated_dict, response = cached
                        validated = schema.model_validate(validated_dict)
                        with self._metrics_lock:
                            self._metrics["cache_hits"] += 1
                        logger.info(f"Cache hit - returning cached {force_provider} response")
                        return validated, response
                    except (ValidationError, json.JSONDecodeError, TypeError, KeyError) as e:
                        # Cache entry corrupted/invalid - treat as miss
                        logger.warning(f"Cache entry invalid, treating as miss: {e}")
                        cache.invalidate(cache_key)
            else:
                # Auto mode: respect provider preference
                # Only use cache if preferred provider is unavailable OR cache matches preferred
                ollama_available = self.ollama and self.ollama.health_check()

                if ollama_available:
                    # Ollama is primary and available - only use Ollama cache
                    cache_key = cache.make_key(
                        prompt, schema, temperature,
                        provider="ollama",
                        **base_cache_kwargs,
                        **kwargs
                    )
                    cached = cache.get(cache_key)
                    if cached:
                        try:
                            validated_dict, response = cached
                            validated = schema.model_validate(validated_dict)
                            with self._metrics_lock:
                                self._metrics["cache_hits"] += 1
                            logger.info("Cache hit - returning cached ollama response")
                            return validated, response
                        except (ValidationError, json.JSONDecodeError, TypeError, KeyError) as e:
                            logger.warning(f"Cache entry invalid, treating as miss: {e}")
                            cache.invalidate(cache_key)
                else:
                    # Ollama unavailable - check Gemini cache as fallback
                    cache_key = cache.make_key(
                        prompt, schema, temperature,
                        provider="gemini",
                        **base_cache_kwargs,
                        **kwargs
                    )
                    cached = cache.get(cache_key)
                    if cached:
                        try:
                            validated_dict, response = cached
                            validated = schema.model_validate(validated_dict)
                            with self._metrics_lock:
                                self._metrics["cache_hits"] += 1
                            logger.info("Cache hit - returning cached gemini response (ollama unavailable)")
                            return validated, response
                        except (ValidationError, json.JSONDecodeError, TypeError, KeyError) as e:
                            logger.warning(f"Cache entry invalid, treating as miss: {e}")
                            cache.invalidate(cache_key)

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

            # Update metrics (pass measured latency for accurate tracking)
            self._update_metrics(provider_name, response, latency_ms=latency)

            # Cache result with actual provider name (prevents cache poisoning)
            if cache and cache.enabled:
                actual_cache_key = cache.make_key(
                    prompt, schema, temperature,
                    provider=provider_name,  # Use ACTUAL provider, not force_provider
                    **base_cache_kwargs,
                    **kwargs
                )
                # Explicitly serialize Pydantic model to dict for cache storage
                # This makes the serialization explicit rather than relying on cache.set() internals
                validated_dict = validated.model_dump() if hasattr(validated, 'model_dump') else validated
                cache.set(actual_cache_key, (validated_dict, response))

            logger.info(
                f"Generated via {provider_name} in {latency:.0f}ms "
                f"({response.tokens_used} tokens)"
            )
            return validated, response

        except (
            ProviderUnavailableError,
            SchemaValidationError,
            ValidationError,  # Pydantic validation
            json.JSONDecodeError,  # JSON parsing errors
            RuntimeError,
            OSError,
            ConnectionError,
            TimeoutError,
            # Note: TypeError and KeyError are NOT caught here - they indicate
            # programming bugs that should fail fast during development
        ) as e:
            # Catch specific exceptions, not KeyboardInterrupt/SystemExit
            errors.append((providers_tried[-1] if providers_tried else "unknown", str(e)))
            logger.warning(f"Primary provider failed: {type(e).__name__}: {e}")

            # Try fallback if enabled
            if self._fallback_enabled and not force_provider:
                try:
                    fallback_provider = self._get_fallback_provider(providers_tried)
                    if fallback_provider:
                        # Check multimodal support for fallback provider
                        if images and not fallback_provider.supports_multimodal:
                            logger.warning(
                                f"Fallback provider {fallback_provider.provider_name} "
                                f"doesn't support multimodal input"
                            )
                            raise ProviderUnavailableError(
                                "No provider supports multimodal input for images"
                            )

                        provider_name = fallback_provider.provider_name
                        providers_tried.append(provider_name)
                        with self._metrics_lock:
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

                        # Cache fallback result with actual provider name
                        if cache and cache.enabled:
                            actual_cache_key = cache.make_key(
                                prompt, schema, temperature,
                                provider=provider_name,  # Use ACTUAL provider
                                **base_cache_kwargs,
                                **kwargs
                            )
                            # Explicitly serialize Pydantic model for cache storage
                            validated_dict = validated.model_dump() if hasattr(validated, 'model_dump') else validated
                            cache.set(actual_cache_key, (validated_dict, response))

                        return validated, response

                except (
                    ProviderUnavailableError,
                    SchemaValidationError,
                    ValidationError,
                    json.JSONDecodeError,
                    RuntimeError,
                    OSError,
                    ConnectionError,
                    TimeoutError,
                    # Note: TypeError and KeyError are intentionally caught in fallback
                    # to give fallback a chance even if primary has a bug
                ) as fallback_error:
                    errors.append((providers_tried[-1], str(fallback_error)))
                    logger.error(f"Fallback also failed: {type(fallback_error).__name__}: {fallback_error}")

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
            try:
                if self.gemini.health_check():
                    return self.gemini
            except Exception as e:
                logger.warning(f"Gemini health check failed during fallback: {e}")

        return None

    def _update_metrics(
        self,
        provider_name: str,
        response: LLMResponse,
        latency_ms: Optional[float] = None,
    ) -> None:
        """
        Update usage metrics from a provider response.

        Thread-safe via metrics lock.

        Args:
            provider_name: Name of the provider ("ollama" or "gemini")
            response: LLMResponse containing usage data
            latency_ms: Optional measured latency (overrides response.latency_ms if provided)
        """
        with self._metrics_lock:
            if provider_name == "ollama":
                self._metrics["ollama_calls"] += 1
            elif provider_name == "gemini":
                self._metrics["gemini_calls"] += 1

            self._metrics["total_tokens"] += response.tokens_used
            self._metrics["total_cost"] += response.cost
            # Use measured latency if provided, otherwise fall back to response latency
            self._metrics["total_latency_ms"] += (
                latency_ms if latency_ms is not None else response.latency_ms
            )

    def get_metrics(self) -> dict:
        """
        Get router usage metrics.

        Returns:
            Dictionary with usage statistics
        """
        # Thread-safe metrics copy to prevent race conditions
        with self._metrics_lock:
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
        # Wrap health checks in try/except to prevent crashes
        ollama_healthy = False
        if self.ollama:
            try:
                ollama_healthy = self.ollama.health_check()
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")

        gemini_healthy = False
        if self.gemini:
            try:
                gemini_healthy = self.gemini.health_check()
            except Exception as e:
                logger.warning(f"Gemini health check failed: {e}")

        return {
            "ollama": {
                "available": self.ollama is not None,
                "healthy": ollama_healthy,
                "model": self.ollama.model_name if self.ollama else None,
            },
            "gemini": {
                "available": self.gemini is not None,
                "healthy": gemini_healthy,
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
    global _router_instance, OLLAMA_PROVIDER, GEMINI_PROVIDER
    with _router_lock:
        if _router_instance is not None:
            # Close associated cache to prevent resource leaks
            reset_cache()
        _router_instance = None
        # Reset lazy-loaded provider classes to allow re-initialization
        OLLAMA_PROVIDER = None
        GEMINI_PROVIDER = None
