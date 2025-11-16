"""
Response Caching for LLM Providers.

Disk-based caching to reduce redundant LLM calls.
Estimated 30-50% reduction in API calls.
"""

import hashlib
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Type
from pydantic import BaseModel

from madspark.llm.response import LLMResponse
from madspark.llm.config import get_config

try:
    import diskcache

    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    diskcache = None  # type: ignore

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Disk-based cache for LLM responses.

    Features:
    - Prompt-based cache keys (hash of prompt + schema + params)
    - TTL-based expiration
    - Automatic disk cleanup
    - Thread-safe operations

    Usage:
        cache = ResponseCache()
        key = cache.make_key(prompt, schema, temperature)

        # Check cache
        cached = cache.get(key)
        if cached:
            return cached

        # Generate and cache
        result = provider.generate_structured(...)
        cache.set(key, result)
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """
        Initialize response cache.

        Args:
            cache_dir: Directory for cache storage (default from config)
            ttl_seconds: Time-to-live for cache entries (default from config)
            enabled: Whether caching is enabled (default from config)
        """
        config = get_config()
        self._enabled = enabled if enabled is not None else config.cache_enabled
        self._ttl = ttl_seconds if ttl_seconds is not None else config.cache_ttl_seconds
        self._cache_dir = cache_dir or config.cache_dir
        self._cache = None

        if self._enabled:
            if not DISKCACHE_AVAILABLE:
                logger.warning("diskcache not installed. Caching disabled.")
                self._enabled = False
            else:
                self._init_cache()

    def _init_cache(self) -> None:
        """Initialize disk cache."""
        cache_path = Path(self._cache_dir)
        # WARNING: Cache stores prompts and responses in plaintext on disk.
        # Do not use for sensitive data without additional encryption.
        # Restrictive permissions (0o700) limit access to current user only.
        cache_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._cache = diskcache.Cache(str(cache_path))
        logger.info(f"Initialized cache at {cache_path}")

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    def make_key(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.0,
        provider: str = "",
        model: str = "",
        **kwargs,
    ) -> str:
        """
        Generate cache key from request parameters.

        Args:
            prompt: The prompt text
            schema: Pydantic schema class
            temperature: Sampling temperature
            provider: Provider name (optional, for provider-specific caching)
            model: Model name (optional)
            **kwargs: Additional parameters to include in key

        Returns:
            SHA256 hash as cache key
        """
        # Create deterministic representation
        key_data = {
            "prompt": prompt,
            "schema_name": f"{schema.__module__}.{schema.__name__}",  # Full path to avoid collisions
            "schema_hash": hashlib.sha256(
                json.dumps(schema.model_json_schema(), sort_keys=True).encode()
            ).hexdigest()[:64],  # Use 64 chars to minimize collision risk
            "temperature": temperature,
            "provider": provider,
            "model": model,
            **kwargs,
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[tuple[Any, LLMResponse]]:
        """
        Get cached response.

        Args:
            key: Cache key from make_key()

        Returns:
            Tuple of (validated_object, LLMResponse) or None if not cached
        """
        if not self._enabled or self._cache is None:
            return None

        try:
            cached_data = self._cache.get(key, default=None)
            if cached_data is None:
                logger.debug(f"Cache miss: {key[:16]}...")
                return None

            # Deserialize
            validated_dict, response_dict = cached_data
            # Convert timestamp string back to datetime if needed
            if "timestamp" in response_dict and isinstance(response_dict["timestamp"], str):
                response_dict["timestamp"] = datetime.fromisoformat(response_dict["timestamp"])
            response = LLMResponse(**response_dict)
            response.cached = True

            logger.debug(f"Cache hit: {key[:16]}...")
            return validated_dict, response

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None

    def set(
        self,
        key: str,
        value: tuple[Any, LLMResponse],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store response in cache.

        Args:
            key: Cache key from make_key()
            value: Tuple of (validated_object, LLMResponse)
            ttl: Optional TTL override in seconds

        Returns:
            True if cached successfully or cache is disabled (no-op success),
            False only on actual storage failure
        """
        if not self._enabled or self._cache is None:
            return True  # Not a failure, just no-op when disabled

        try:
            validated_obj, response = value

            # Serialize to cacheable format with explicit type checking
            if isinstance(validated_obj, BaseModel):
                validated_dict = validated_obj.model_dump()
            elif isinstance(validated_obj, dict):
                validated_dict = validated_obj
            else:
                raise TypeError(
                    f"Cannot cache object of type {type(validated_obj).__name__}. "
                    f"Expected BaseModel or dict."
                )

            response_dict = response.to_dict()

            # Store with TTL
            expire = ttl if ttl is not None else self._ttl
            self._cache.set(key, (validated_dict, response_dict), expire=expire)

            logger.debug(f"Cached: {key[:16]}... (TTL: {expire}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """
        Remove specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if removed successfully
        """
        if not self._enabled or self._cache is None:
            return False

        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated: {key[:16]}...")
                return True
            return False
        except Exception as e:
            logger.warning(f"Cache invalidate failed: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if cleared successfully
        """
        if not self._enabled or self._cache is None:
            return False

        try:
            self._cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
            return False

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self._enabled or self._cache is None:
            return {"enabled": False}

        try:
            return {
                "enabled": True,
                "size": len(self._cache),
                "volume": self._cache.volume(),
                "cache_dir": self._cache_dir,
                "ttl_seconds": self._ttl,
            }
        except Exception as e:
            logger.warning(f"Cache stats failed: {e}")
            return {"enabled": True, "error": str(e)}

    def close(self) -> None:
        """Close cache connection."""
        if self._cache is not None:
            self._cache.close()
            logger.debug("Cache closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - close cache."""
        self.close()


# Singleton cache instance with thread safety
_cache_instance: Optional[ResponseCache] = None
_cache_lock = threading.Lock()


def get_cache() -> ResponseCache:
    """
    Get singleton cache instance.

    Thread-safe via double-checked locking pattern.

    Returns:
        ResponseCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:  # Double-checked locking
                _cache_instance = ResponseCache()
    return _cache_instance


def reset_cache() -> None:
    """Reset cache singleton (for testing). Thread-safe."""
    global _cache_instance
    with _cache_lock:
        if _cache_instance is not None:
            _cache_instance.close()
        _cache_instance = None
