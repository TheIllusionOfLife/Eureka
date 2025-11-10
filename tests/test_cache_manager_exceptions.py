"""Tests for cache_manager exception handling.

These tests verify that CacheManager properly handles various error scenarios
including connection errors, serialization failures, and redis unavailability.
"""

import pytest
from unittest.mock import AsyncMock


class TestCacheManagerExceptionHandling:
    """Test exception handling in CacheManager."""

    def test_cache_manager_works_without_redis_installed(self):
        """Verify CacheManager imports successfully when redis is not available."""
        # This test verifies the fix for the AttributeError bug
        # When redis is not installed, fallback exception types are used

        # Import should succeed without AttributeError
        from madspark.utils.cache_manager import (
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
        from madspark.utils.cache_manager import CacheManager, CacheConfig

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
        from madspark.utils.cache_manager import CacheManager, CacheConfig

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

    @pytest.mark.asyncio
    async def test_cache_workflow_connection_error_returns_false(self):
        """Redis connection errors should be handled gracefully."""
        from madspark.utils.cache_manager import (
            CacheManager,
            CacheConfig,
            RedisConnectionError,
        )

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()
        cache_manager.redis_client.setex = AsyncMock(
            side_effect=RedisConnectionError("boom")
        )
        cache_manager._enforce_size_limit = AsyncMock()

        success = await cache_manager.cache_workflow_result(
            topic="t",
            context="c",
            options={},
            result={"ok": True},
        )

        assert success is False
        cache_manager.redis_client.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_workflow_oserror_bubbles_up(self):
        """System-level OSErrors should not be swallowed by cache manager."""
        from madspark.utils.cache_manager import CacheManager, CacheConfig

        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()
        cache_manager.redis_client.setex = AsyncMock(
            side_effect=OSError("disk error")
        )
        cache_manager._enforce_size_limit = AsyncMock()

        with pytest.raises(OSError):
            await cache_manager.cache_workflow_result(
                topic="t",
                context="c",
                options={},
                result={"ok": True},
            )


class TestCacheManagerExceptionTypes:
    """Test that correct exception types are caught."""

    def test_exception_imports_are_correct(self):
        """Verify that RedisConnectionError and RedisTimeoutError are properly defined."""
        from madspark.utils.cache_manager import (
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
