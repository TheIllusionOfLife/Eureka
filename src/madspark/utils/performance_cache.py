"""Performance-optimized caching utilities for MadSpark."""

import asyncio
import functools
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Callable
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache implementation for performance optimization."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.expiry_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self._last_cleanup = 0
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.expiry_times:
            return True
        return time.time() > self.expiry_times[key]
    
    def _evict_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.expiry_times.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.expiry_times.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                # Clean up if expired
                if key in self.cache:
                    self.cache.pop(key, None)
                    self.expiry_times.pop(key, None)
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self.lock:
            # Remove expired entries periodically (more robust approach)
            if not hasattr(self, '_last_cleanup') or time.time() - self._last_cleanup > 300:  # 5 minutes
                self._evict_expired()
                self._last_cleanup = time.time()
            
            # Remove oldest entries if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.expiry_times.pop(oldest_key, None)
            
            self.cache[key] = value
            self.expiry_times[key] = time.time() + self.ttl
            self.cache.move_to_end(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.expiry_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'ttl': self.ttl
            }


class PerformanceCache:
    """High-performance cache for MadSpark operations."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize performance cache."""
        self.cache = LRUCache(max_size, ttl)
        self.logger = logging.getLogger(__name__)
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create a stable hash from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with logging."""
        result = self.cache.get(key)
        if result is not None:
            self.logger.debug(f"Cache hit for key: {key[:8]}...")
        else:
            self.logger.debug(f"Cache miss for key: {key[:8]}...")
        return result
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with logging."""
        self.cache.set(key, value)
        self.logger.debug(f"Cache set for key: {key[:8]}...")
    
    def cached_function(self, ttl: int = 3600):
        """Decorator to cache function results."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result)
                return result
            
            return wrapper
        return decorator
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.logger.info("Performance cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


# Global performance cache instance
performance_cache = PerformanceCache()


def cached_result(ttl: int = 3600):
    """Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
    
    Usage:
        @cached_result(ttl=1800)
        def expensive_function(arg1, arg2):
            # ... expensive computation
            return result
    """
    return performance_cache.cached_function(ttl)


def cache_key_for_workflow(theme: str, constraints: str, **kwargs) -> str:
    """Generate cache key for workflow results."""
    return performance_cache.generate_cache_key(
        'workflow', theme, constraints, **kwargs
    )


def cache_key_for_agent(agent_name: str, input_data: Any, **kwargs) -> str:
    """Generate cache key for agent results."""
    return performance_cache.generate_cache_key(
        'agent', agent_name, input_data, **kwargs
    )


class AsyncBatchProcessor:
    """Asynchronous batch processor for performance optimization."""
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = None
    
    async def process_batch(self, items: list, processor_func: Callable) -> list:
        """Process items in batches with concurrency control."""
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_item(item):
            async with self.semaphore:
                return await processor_func(item)
        
        # Process items in batches
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [process_item(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results


class PerformanceOptimizer:
    """Performance optimization utilities."""
    
    @staticmethod
    def optimize_json_parsing(json_str: str) -> Any:
        """Optimized JSON parsing with caching."""
        cache_key = hashlib.md5(json_str.encode(), usedforsecurity=False).hexdigest()
        
        cached_result = performance_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            result = json.loads(json_str)
            performance_cache.set(cache_key, result)
            return result
        except json.JSONDecodeError:
            # Cache the error to avoid repeated parsing attempts
            performance_cache.set(cache_key, None)
            return None
    
    @staticmethod
    def batch_operations(operations: list, batch_size: int = 5) -> list:
        """Group operations into batches for processing."""
        groups = []
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            groups.append(batch)
        
        return groups
    
    @staticmethod
    def precompile_regex_patterns():
        """Precompile frequently used regex patterns."""
        import re
        
        # Common patterns used in idea cleaning and processing
        patterns = {
            'meta_headers': re.compile(r'##\s*(ENHANCED|IMPROVED|REVISED|ORIGINAL).*?:', re.IGNORECASE),
            'improvement_refs': re.compile(r'\b(enhanced|improved|revised|building upon)\b', re.IGNORECASE),
            'score_refs': re.compile(r'\bscore[ds]?\s*[:=]\s*\d+', re.IGNORECASE),
            'section_headers': re.compile(r'^#+\s*.*?:', re.MULTILINE),
        }
        
        # Cache compiled patterns
        for name, pattern in patterns.items():
            performance_cache.set(f'regex_{name}', pattern)
        
        return patterns


# Initialize performance optimizations
def initialize_performance_optimizations():
    """Initialize performance optimizations."""
    try:
        # Set up performance cache
        performance_cache.clear()
        
        # Pre-compile regex patterns
        PerformanceOptimizer.precompile_regex_patterns()
        
        logger.info("Performance optimizations initialized")
    except Exception as e:
        logger.warning(f"Performance optimization initialization failed: {e}")


# Initialize on module load
initialize_performance_optimizations()