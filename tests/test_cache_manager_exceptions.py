"""Tests for cache_manager exception handling.

These tests verify that CacheManager properly handles various error scenarios
including connection errors, serialization failures, and redis unavailability.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json


class TestCacheManagerExceptionHandling:
    """Test exception handling in CacheManager."""

    @pytest.mark.asyncio
    async def test_initialize_handles_connection_error(self):
        """Verify CacheManager gracefully handles Redis connection failures."""
        # Import here to avoid issues if redis is not installed
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())

        # Mock redis client to raise connection error
        with patch('src.madspark.utils.cache_manager.redis') as mock_redis_module:
            mock_redis_module.from_url = Mock(side_effect=ConnectionError("Connection refused"))

            result = await cache_manager.initialize()

            assert result is False
            assert cache_manager.is_connected is False

    @pytest.mark.asyncio
    async def test_cache_workflow_handles_serialization_error(self):
        """Verify CacheManager handles non-serializable objects."""
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()

        # Create a result with a non-serializable object
        non_serializable_result = {
            "data": lambda x: x,  # Functions can't be JSON-serialized
            "timestamp": "2024-01-01"
        }

        # The method should handle this gracefully with fallback to default=str
        result = await cache_manager.cache_workflow_result(
            topic="test",
            context="test",
            options={},
            result=non_serializable_result
        )

        # With the fallback, it should succeed
        # (The fallback converts non-serializable objects to strings)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_cached_workflow_handles_deserialization_error(self):
        """Verify CacheManager handles malformed JSON data."""
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True

        # Mock redis client to return invalid JSON
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value='{"invalid": json}')  # Malformed JSON
        cache_manager.redis_client = mock_client

        result = await cache_manager.get_cached_workflow(
            topic="test",
            context="test",
            options={}
        )

        # Should handle the JSONDecodeError gracefully
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_manager_works_without_redis_installed(self):
        """Verify CacheManager imports successfully when redis is not available."""
        # This test verifies the fix for the AttributeError bug
        # When redis is not installed, fallback exception types are used

        # Import should succeed without AttributeError
        from src.madspark.utils.cache_manager import (
            CacheManager,
            RedisConnectionError,
            RedisTimeoutError
        )

        # Fallback exception types should be defined
        assert RedisConnectionError is not None
        assert RedisTimeoutError is not None

        # Should be able to create CacheManager instance
        cache_manager = CacheManager()
        assert cache_manager is not None

    @pytest.mark.asyncio
    async def test_redis_unavailable_returns_false(self):
        """Verify operations return False/None when redis is unavailable."""
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = False  # Redis not available

        # All cache operations should handle unavailability gracefully
        result = await cache_manager.cache_workflow_result(
            topic="test",
            context="test",
            options={},
            result={}
        )
        assert result is False

        cached = await cache_manager.get_cached_workflow(
            topic="test",
            context="test",
            options={}
        )
        assert cached is None

    @pytest.mark.asyncio
    async def test_warm_cache_uses_correct_parameters(self):
        """Verify warm_cache uses topic/context parameters correctly."""
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()

        # Mock cache_workflow_result to track calls
        cache_manager.cache_workflow_result = AsyncMock(return_value=True)

        # Call warm_cache with test queries
        common_queries = [
            ("AI in healthcare", "Budget-friendly solutions"),
            ("Sustainable farming", "Urban environments")
        ]

        warmed_count = await cache_manager.warm_cache(common_queries)

        # Verify correct number of entries warmed
        assert warmed_count == 2
        assert cache_manager.cache_workflow_result.call_count == 2

        # Verify first call used correct parameters (topic, context)
        first_call = cache_manager.cache_workflow_result.call_args_list[0]
        assert first_call[0][0] == "AI in healthcare"  # topic
        assert first_call[0][1] == "Budget-friendly solutions"  # context

        # Verify second call used correct parameters
        second_call = cache_manager.cache_workflow_result.call_args_list[1]
        assert second_call[0][0] == "Sustainable farming"  # topic
        assert second_call[0][1] == "Urban environments"  # context


class TestCacheManagerExceptionTypes:
    """Test that correct exception types are caught."""

    def test_exception_imports_are_correct(self):
        """Verify that RedisConnectionError and RedisTimeoutError are properly defined."""
        from src.madspark.utils.cache_manager import (
            RedisConnectionError,
            RedisTimeoutError,
            REDIS_AVAILABLE
        )

        # Exception types should always be defined (either real or fallback)
        assert RedisConnectionError is not None
        assert RedisTimeoutError is not None

        # Both should be subclasses of Exception
        assert issubclass(RedisConnectionError, Exception)
        assert issubclass(RedisTimeoutError, Exception)

        # REDIS_AVAILABLE flag should be set
        assert isinstance(REDIS_AVAILABLE, bool)
