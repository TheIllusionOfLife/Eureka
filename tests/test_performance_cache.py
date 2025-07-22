"""Comprehensive tests for performance caching utilities."""
import pytest
import time
import asyncio
import threading
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from madspark.utils.performance_cache import (
    LRUCache,
    memoize,
    async_memoize,
    cache_key_generator,
    PerformanceMetrics,
    CacheWarmer,
    clear_all_caches
)


class TestLRUCache:
    """Test cases for LRU cache implementation."""
    
    def test_lru_cache_initialization(self):
        """Test LRU cache initialization."""
        cache = LRUCache(max_size=100, ttl=3600)
        assert cache.max_size == 100
        assert cache.ttl == 3600
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
    
    def test_lru_cache_get_set(self):
        """Test basic get/set operations."""
        cache = LRUCache(max_size=10, ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.hits == 1
        assert cache.misses == 0
        
        # Test miss
        assert cache.get("key2") is None
        assert cache.hits == 1
        assert cache.misses == 1
    
    def test_lru_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3, ttl=3600)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new item, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still present
        assert cache.get("key4") == "value4"  # New item
    
    def test_lru_cache_ttl_expiration(self):
        """Test TTL expiration."""
        cache = LRUCache(max_size=10, ttl=0.1)  # 100ms TTL
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.15)
        assert cache.get("key1") is None  # Expired
    
    def test_lru_cache_clear(self):
        """Test cache clearing."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Clear cache
        cache.clear()
        
        assert len(cache.cache) == 0
        assert len(cache.expiry_times) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_lru_cache_delete(self):
        """Test item deletion."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
        
        # Delete non-existent key should not raise error
        cache.delete("non_existent")
    
    def test_lru_cache_contains(self):
        """Test contains operation."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        cache.set("key1", "value1")
        assert cache.contains("key1") == True
        assert cache.contains("key2") == False
        
        # Test expired item
        cache = LRUCache(max_size=10, ttl=0.1)
        cache.set("key3", "value3")
        time.sleep(0.15)
        assert cache.contains("key3") == False
    
    def test_lru_cache_get_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        # Generate some hits and misses
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["max_size"] == 10
    
    def test_lru_cache_thread_safety(self):
        """Test thread-safe operations."""
        cache = LRUCache(max_size=100, ttl=3600)
        results = []
        
        def worker(thread_id):
            for i in range(100):
                key = f"key_{thread_id}_{i}"
                cache.set(key, f"value_{thread_id}_{i}")
                value = cache.get(key)
                results.append(value is not None)
        
        # Run multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 1000
    
    def test_lru_cache_periodic_cleanup(self):
        """Test periodic cleanup of expired items."""
        cache = LRUCache(max_size=100, ttl=0.1)
        
        # Add items
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # Force cleanup by accessing after expiration
        time.sleep(0.15)
        cache._cleanup_if_needed()
        
        # All items should be expired and cleaned
        assert len(cache.cache) == 0
        assert len(cache.expiry_times) == 0


class TestCacheKeyGenerator:
    """Test cache key generation."""
    
    def test_cache_key_simple_args(self):
        """Test key generation with simple arguments."""
        key = cache_key_generator("func", (1, 2, 3), {})
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex digest length
        
        # Same args should generate same key
        key2 = cache_key_generator("func", (1, 2, 3), {})
        assert key == key2
        
        # Different args should generate different key
        key3 = cache_key_generator("func", (1, 2, 4), {})
        assert key != key3
    
    def test_cache_key_with_kwargs(self):
        """Test key generation with keyword arguments."""
        key1 = cache_key_generator("func", (), {"a": 1, "b": 2})
        key2 = cache_key_generator("func", (), {"b": 2, "a": 1})
        assert key1 == key2  # Order shouldn't matter
        
        key3 = cache_key_generator("func", (), {"a": 1, "b": 3})
        assert key1 != key3
    
    def test_cache_key_complex_types(self):
        """Test key generation with complex types."""
        # Lists
        key1 = cache_key_generator("func", ([1, 2, 3],), {})
        key2 = cache_key_generator("func", ([1, 2, 3],), {})
        assert key1 == key2
        
        # Dicts
        key1 = cache_key_generator("func", ({"x": 1, "y": 2},), {})
        key2 = cache_key_generator("func", ({"y": 2, "x": 1},), {})
        assert key1 == key2
        
        # Nested structures
        complex_obj = {
            "list": [1, 2, {"nested": True}],
            "tuple": (1, 2, 3),
            "str": "test"
        }
        key1 = cache_key_generator("func", (complex_obj,), {})
        key2 = cache_key_generator("func", (complex_obj,), {})
        assert key1 == key2
    
    def test_cache_key_unhashable_types(self):
        """Test key generation with unhashable types."""
        # Should handle sets by converting to sorted list
        key1 = cache_key_generator("func", ({1, 2, 3},), {})
        key2 = cache_key_generator("func", ({3, 2, 1},), {})
        assert key1 == key2
        
        # Should handle custom objects
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __str__(self):
                return f"CustomObj({self.value})"
        
        obj = CustomObj(42)
        key = cache_key_generator("func", (obj,), {})
        assert isinstance(key, str)


class TestMemoizeDecorator:
    """Test memoize decorator."""
    
    def test_memoize_basic(self):
        """Test basic memoization."""
        call_count = 0
        
        @memoize(max_size=10, ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call
        result = expensive_function(1, 2)
        assert result == 3
        assert call_count == 1
        
        # Second call with same args should use cache
        result = expensive_function(1, 2)
        assert result == 3
        assert call_count == 1  # Not incremented
        
        # Different args should trigger new call
        result = expensive_function(2, 3)
        assert result == 5
        assert call_count == 2
    
    def test_memoize_with_kwargs(self):
        """Test memoization with keyword arguments."""
        call_count = 0
        
        @memoize()
        def func(a, b=10, c=20):
            nonlocal call_count
            call_count += 1
            return a + b + c
        
        assert func(1) == 31
        assert call_count == 1
        
        assert func(1, b=10) == 31
        assert call_count == 1  # Should use cache
        
        assert func(1, b=20) == 41
        assert call_count == 2  # Different kwargs
    
    def test_memoize_expiration(self):
        """Test cache expiration."""
        call_count = 0
        
        @memoize(ttl=0.1)  # 100ms TTL
        def func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        assert func(5) == 10
        assert call_count == 1
        
        # Should use cache
        assert func(5) == 10
        assert call_count == 1
        
        # Wait for expiration
        time.sleep(0.15)
        assert func(5) == 10
        assert call_count == 2  # Called again after expiration
    
    def test_memoize_clear_cache(self):
        """Test clearing memoize cache."""
        @memoize()
        def func(x):
            return x * 2
        
        assert func(5) == 10
        assert func(5) == 10  # From cache
        
        # Clear cache
        func.clear_cache()
        
        # Should recompute
        assert func(5) == 10
    
    def test_memoize_cache_info(self):
        """Test cache info access."""
        @memoize(max_size=10)
        def func(x):
            return x * 2
        
        # Generate some cache activity
        for i in range(5):
            func(i)
        func(0)  # Hit
        func(10)  # Miss
        
        info = func.cache_info()
        assert info["hits"] == 1
        assert info["misses"] == 6
        assert info["size"] == 5


class TestAsyncMemoize:
    """Test async memoize decorator."""
    
    @pytest.mark.asyncio
    async def test_async_memoize_basic(self):
        """Test basic async memoization."""
        call_count = 0
        
        @async_memoize(max_size=10, ttl=60)
        async def async_expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate async work
            return x + y
        
        # First call
        result = await async_expensive_function(1, 2)
        assert result == 3
        assert call_count == 1
        
        # Second call should use cache
        result = await async_expensive_function(1, 2)
        assert result == 3
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_memoize_concurrent(self):
        """Test async memoization with concurrent calls."""
        call_count = 0
        
        @async_memoize()
        async def slow_function(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return x * 2
        
        # Launch multiple concurrent calls with same argument
        tasks = [slow_function(5) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should return same result
        assert all(r == 10 for r in results)
        # But function should only be called once
        assert call_count == 1


class TestPerformanceMetrics:
    """Test performance metrics tracking."""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.call_count == 0
        assert metrics.total_time == 0
        assert metrics.min_time is None
        assert metrics.max_time is None
        assert metrics.average_time == 0
    
    def test_performance_metrics_record(self):
        """Test recording performance metrics."""
        metrics = PerformanceMetrics()
        
        metrics.record_call(0.1)
        metrics.record_call(0.2)
        metrics.record_call(0.15)
        
        assert metrics.call_count == 3
        assert metrics.total_time == 0.45
        assert metrics.min_time == 0.1
        assert metrics.max_time == 0.2
        assert abs(metrics.average_time - 0.15) < 0.001
    
    def test_performance_metrics_decorator(self):
        """Test performance tracking decorator."""
        metrics = PerformanceMetrics()
        
        @metrics.track_performance
        def func(x):
            time.sleep(0.01)
            return x * 2
        
        # Call function multiple times
        for i in range(5):
            func(i)
        
        assert metrics.call_count == 5
        assert metrics.total_time > 0.05  # At least 5 * 0.01
        assert metrics.min_time > 0.01
        assert metrics.max_time < 0.1  # Reasonable upper bound
    
    def test_performance_metrics_async_decorator(self):
        """Test async performance tracking."""
        metrics = PerformanceMetrics()
        
        @metrics.track_performance
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        # Run async function
        async def run_test():
            for i in range(3):
                await async_func(i)
        
        asyncio.run(run_test())
        
        assert metrics.call_count == 3
        assert metrics.total_time > 0.03


class TestCacheWarmer:
    """Test cache warming functionality."""
    
    def test_cache_warmer_basic(self):
        """Test basic cache warming."""
        cache = LRUCache(max_size=10, ttl=3600)
        warmer = CacheWarmer(cache)
        
        # Define data to warm
        warm_data = [
            ("key1", "value1"),
            ("key2", "value2"),
            ("key3", "value3")
        ]
        
        warmer.warm_cache(warm_data)
        
        # Verify all data is in cache
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_cache_warmer_with_generator(self):
        """Test cache warming with generator function."""
        cache = LRUCache(max_size=10, ttl=3600)
        warmer = CacheWarmer(cache)
        
        def data_generator():
            for i in range(5):
                yield (f"key{i}", f"value{i}")
        
        warmer.warm_cache_from_generator(data_generator)
        
        # Verify all data is in cache
        for i in range(5):
            assert cache.get(f"key{i}") == f"value{i}"
    
    @pytest.mark.asyncio
    async def test_cache_warmer_async(self):
        """Test async cache warming."""
        cache = LRUCache(max_size=10, ttl=3600)
        warmer = CacheWarmer(cache)
        
        async def async_data_generator():
            for i in range(5):
                await asyncio.sleep(0.001)  # Simulate async data fetching
                yield (f"async_key{i}", f"async_value{i}")
        
        await warmer.warm_cache_async(async_data_generator)
        
        # Verify all data is in cache
        for i in range(5):
            assert cache.get(f"async_key{i}") == f"async_value{i}"


class TestClearAllCaches:
    """Test clearing all caches."""
    
    def test_clear_all_caches(self):
        """Test clearing all registered caches."""
        # Create some cached functions
        @memoize()
        def func1(x):
            return x * 2
        
        @memoize()
        def func2(x):
            return x * 3
        
        # Populate caches
        func1(5)
        func2(5)
        
        # Clear all caches
        clear_all_caches()
        
        # Verify caches are empty
        assert func1.cache_info()["size"] == 0
        assert func2.cache_info()["size"] == 0


class TestCacheEdgeCases:
    """Test edge cases for caching utilities."""
    
    def test_cache_with_none_values(self):
        """Test caching None values."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        cache.set("key1", None)
        assert cache.get("key1") is None
        assert cache.contains("key1") == True
    
    def test_cache_with_large_values(self):
        """Test caching large values."""
        cache = LRUCache(max_size=10, ttl=3600)
        
        # Large string (1MB)
        large_value = "x" * (1024 * 1024)
        cache.set("large_key", large_value)
        
        retrieved = cache.get("large_key")
        assert retrieved == large_value
    
    def test_memoize_with_exceptions(self):
        """Test memoization when function raises exceptions."""
        call_count = 0
        
        @memoize()
        def func(x):
            nonlocal call_count
            call_count += 1
            if x < 0:
                raise ValueError("Negative input")
            return x * 2
        
        # Normal call
        assert func(5) == 10
        assert call_count == 1
        
        # Exception should not be cached
        with pytest.raises(ValueError):
            func(-1)
        assert call_count == 2
        
        # Calling again should re-execute (exception not cached)
        with pytest.raises(ValueError):
            func(-1)
        assert call_count == 3
    
    def test_cache_key_with_mutable_args(self):
        """Test cache key generation with mutable arguments."""
        @memoize()
        def func(lst):
            return sum(lst)
        
        # Lists are mutable but should work
        lst1 = [1, 2, 3]
        result1 = func(lst1)
        assert result1 == 6
        
        # Same content should hit cache
        lst2 = [1, 2, 3]
        result2 = func(lst2)
        assert result2 == 6
        
        # Modifying original list shouldn't affect cache
        lst1.append(4)
        result3 = func([1, 2, 3])
        assert result3 == 6  # Still from cache