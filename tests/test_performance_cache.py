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
    PerformanceCache,
    cached_result,
    cache_key_for_workflow,
    cache_key_for_agent,
    AsyncBatchProcessor,
    PerformanceOptimizer,
    initialize_performance_optimizations
)


class TestLRUCache:
    """Test cases for LRU cache implementation."""
    
    def test_lru_cache_initialization(self):
        """Test LRU cache initialization."""
        cache = LRUCache(max_size=100, ttl=3600)
        assert cache.max_size == 100
        assert cache.ttl == 3600
        assert len(cache.cache) == 0
    
    def test_lru_cache_get_set(self):
        """Test basic get/set operations."""
        cache = LRUCache(max_size=10, ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test miss
        assert cache.get("key2") is None
    
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
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_lru_cache_thread_safety(self):
        """Test thread-safe operations."""
        cache = LRUCache(max_size=100, ttl=3600)
        results = []
        
        def worker(thread_id):
            for i in range(10):
                key = f"key_{thread_id}_{i}"
                cache.set(key, f"value_{thread_id}_{i}")
                value = cache.get(key)
                results.append(value is not None)
        
        # Run multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 50


class TestPerformanceCache:
    """Test cases for PerformanceCache."""
    
    def test_performance_cache_initialization(self):
        """Test PerformanceCache initialization."""
        perf_cache = PerformanceCache()
        assert perf_cache.workflow_cache is not None
        assert perf_cache.agent_cache is not None
        assert perf_cache.enabled == True
    
    def test_cache_workflow_result(self):
        """Test caching workflow results."""
        perf_cache = PerformanceCache()
        
        result = {"ideas": ["idea1", "idea2"], "score": 8.5}
        perf_cache.cache_workflow_result("AI Theme", "Scalable", result)
        
        # Retrieve cached result
        cached = perf_cache.get_cached_workflow("AI Theme", "Scalable")
        assert cached == result
    
    def test_cache_agent_result(self):
        """Test caching agent results."""
        perf_cache = PerformanceCache()
        
        result = "Generated ideas for testing"
        perf_cache.cache_agent_result("IdeaGenerator", "test input", result)
        
        # Retrieve cached result
        cached = perf_cache.get_cached_agent_result("IdeaGenerator", "test input")
        assert cached == result
    
    def test_cache_stats(self):
        """Test cache statistics."""
        perf_cache = PerformanceCache()
        
        # Add some data
        perf_cache.cache_workflow_result("Theme1", "Constraints1", {"result": 1})
        perf_cache.get_cached_workflow("Theme1", "Constraints1")  # Hit
        perf_cache.get_cached_workflow("Theme2", "Constraints2")  # Miss
        
        stats = perf_cache.get_cache_stats()
        assert "workflow_cache" in stats
        assert "agent_cache" in stats


class TestCachedResult:
    """Test cases for cached_result decorator."""
    
    def test_cached_result_basic(self):
        """Test basic caching with decorator."""
        call_count = 0
        
        @cached_result(ttl=60)
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
    
    def test_cached_result_expiration(self):
        """Test cache expiration."""
        call_count = 0
        
        @cached_result(ttl=0.1)  # 100ms TTL
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


class TestCacheKeyFunctions:
    """Test cache key generation functions."""
    
    def test_cache_key_for_workflow(self):
        """Test workflow cache key generation."""
        key1 = cache_key_for_workflow("AI Theme", "Budget constraints")
        key2 = cache_key_for_workflow("AI Theme", "Budget constraints")
        key3 = cache_key_for_workflow("Different Theme", "Budget constraints")
        
        assert key1 == key2  # Same inputs
        assert key1 != key3  # Different theme
    
    def test_cache_key_for_agent(self):
        """Test agent cache key generation."""
        key1 = cache_key_for_agent("IdeaGenerator", {"theme": "AI", "temp": 0.9})
        key2 = cache_key_for_agent("IdeaGenerator", {"theme": "AI", "temp": 0.9})
        key3 = cache_key_for_agent("Critic", {"theme": "AI", "temp": 0.9})
        
        assert key1 == key2  # Same inputs
        assert key1 != key3  # Different agent
    
    def test_cache_key_complex_data(self):
        """Test cache key with complex data structures."""
        complex_data = {
            "list": [1, 2, {"nested": True}],
            "dict": {"a": 1, "b": 2},
            "tuple": (1, 2, 3)
        }
        
        key1 = cache_key_for_agent("Test", complex_data)
        key2 = cache_key_for_agent("Test", complex_data)
        
        assert key1 == key2


class TestAsyncBatchProcessor:
    """Test cases for AsyncBatchProcessor."""
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_basic(self):
        """Test basic async batch processing."""
        processor = AsyncBatchProcessor(batch_size=3, max_concurrent=2)
        
        # Mock async function
        async def process_item(item):
            await asyncio.sleep(0.01)
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)
        
        assert results == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_error_handling(self):
        """Test error handling in batch processing."""
        processor = AsyncBatchProcessor(batch_size=2, max_concurrent=2)
        
        # Mock function that fails for specific items
        async def process_item(item):
            if item == 3:
                raise ValueError("Test error")
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)
        
        # Should handle errors gracefully
        assert len(results) == 5
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] is None  # Failed item
        assert results[3] == 8
        assert results[4] == 10


class TestPerformanceOptimizer:
    """Test cases for PerformanceOptimizer."""
    
    def test_performance_optimizer_initialization(self):
        """Test PerformanceOptimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert optimizer.cache is not None
        assert optimizer.enable_caching == True
        assert optimizer.enable_batching == True
    
    @patch('madspark.utils.performance_cache.PerformanceCache')
    def test_optimize_workflow(self, mock_cache_class):
        """Test workflow optimization."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        optimizer = PerformanceOptimizer()
        
        # Mock workflow function
        def workflow_func(theme, constraints):
            return {"result": "success"}
        
        # Optimize the workflow
        optimized = optimizer.optimize_workflow(workflow_func)
        
        # Call optimized function
        result = optimized("AI Theme", "Constraints")
        assert result == {"result": "success"}
    
    def test_optimize_agent(self):
        """Test agent optimization."""
        optimizer = PerformanceOptimizer()
        
        call_count = 0
        
        # Mock agent function
        def agent_func(input_data):
            nonlocal call_count
            call_count += 1
            return f"Result for {input_data}"
        
        # Optimize the agent
        optimized = optimizer.optimize_agent("TestAgent", agent_func)
        
        # Call optimized function multiple times
        result1 = optimized("test1")
        result2 = optimized("test1")  # Should use cache
        result3 = optimized("test2")
        
        assert result1 == "Result for test1"
        assert result2 == "Result for test1"
        assert result3 == "Result for test2"
        assert call_count == 2  # Only called twice (cache hit for second call)


class TestInitializePerformanceOptimizations:
    """Test performance initialization function."""
    
    @patch('madspark.utils.performance_cache.PerformanceOptimizer')
    def test_initialize_performance_optimizations(self, mock_optimizer_class):
        """Test initialization function."""
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer
        
        result = initialize_performance_optimizations()
        
        assert result == mock_optimizer
        mock_optimizer_class.assert_called_once()