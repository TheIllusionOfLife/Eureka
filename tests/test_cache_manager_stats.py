"""Tests for CacheManager.get_cache_stats."""

import pytest
from unittest.mock import AsyncMock
from madspark.utils.cache_manager import CacheManager, CacheConfig, RedisConnectionError

class TestCacheManagerStats:
    """Test get_cache_stats method in CacheManager."""

    @pytest.mark.asyncio
    async def test_get_cache_stats_disconnected(self):
        """Verify get_cache_stats returns disconnected status when not connected."""
        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = False

        stats = await cache_manager.get_cache_stats()

        assert stats == {"status": "disconnected"}

    @pytest.mark.asyncio
    async def test_get_cache_stats_success(self):
        """Verify get_cache_stats returns correct statistics when connected."""
        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()

        # Mock info
        cache_manager.redis_client.info.return_value = {
            "used_memory_human": "100M",
            "connected_clients": 5,
            "keyspace_hits": 80,
            "keyspace_misses": 20
        }

        # Mock dbsize
        cache_manager.redis_client.dbsize.return_value = 1000

        # Mock scan_iter for workflow and agent keys
        async def mock_scan_iter(match=None):
            if "workflow" in match:
                for i in range(10):
                    yield f"workflow:{i}"
            elif "agent" in match:
                for i in range(5):
                    yield f"agent:{i}"
            else:
                return

        cache_manager.redis_client.scan_iter = mock_scan_iter

        stats = await cache_manager.get_cache_stats()

        assert stats["status"] == "connected"
        assert stats["memory_used"] == "100M"
        assert stats["total_keys"] == 1000
        assert stats["workflow_keys"] == 10
        assert stats["agent_keys"] == 5
        assert stats["connected_clients"] == 5
        assert stats["hit_rate"] == 80.0  # (80 / (80 + 20)) * 100
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_get_cache_stats_error(self):
        """Verify get_cache_stats handles redis errors gracefully."""
        cache_manager = CacheManager(CacheConfig())
        cache_manager.is_connected = True
        cache_manager.redis_client = AsyncMock()

        # Mock info to raise RedisConnectionError
        cache_manager.redis_client.info.side_effect = RedisConnectionError("Connection refused")

        stats = await cache_manager.get_cache_stats()

        assert stats["status"] == "error"
        assert "Connection refused" in stats["error"]
