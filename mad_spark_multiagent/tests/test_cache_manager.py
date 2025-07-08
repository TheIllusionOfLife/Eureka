"""Simple tests for Redis caching system."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

try:
    from mad_spark_multiagent.cache_manager import CacheManager, CacheConfig
except ImportError:
    from cache_manager import CacheManager, CacheConfig


class TestCacheManager:
    """Simplified test suite for CacheManager."""
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        config = CacheConfig()
        manager = CacheManager(config)
        
        # Test key generation
        key1 = manager._generate_cache_key("AI", "healthcare", {"temp": 0.7})
        key2 = manager._generate_cache_key("AI", "healthcare", {"temp": 0.7})
        key3 = manager._generate_cache_key("AI", "finance", {"temp": 0.7})
        
        assert key1 == key2  # Same inputs
        assert key1 != key3  # Different theme
        assert key1.startswith("madspark:workflow:")
    
    def test_agent_key_generation(self):
        """Test agent key generation."""
        config = CacheConfig()
        manager = CacheManager(config)
        
        key1 = manager._generate_agent_key("idea_generator", "test prompt")
        key2 = manager._generate_agent_key("idea_generator", "test prompt")
        key3 = manager._generate_agent_key("critic", "test prompt")
        
        assert key1 == key2  # Same inputs
        assert key1 != key3  # Different agent
        assert "idea_generator" in key1
    
    @pytest.mark.asyncio
    async def test_cache_disabled_when_redis_unavailable(self):
        """Test cache operations when Redis is not available."""
        config = CacheConfig()
        manager = CacheManager(config)
        manager.is_connected = False  # Simulate Redis not connected
        
        # All operations should return None/False
        result = await manager.get_cached_workflow("AI", "healthcare", {})
        assert result is None
        
        cached = await manager.cache_workflow_result("AI", "healthcare", {}, {"test": "data"})
        assert cached is False
        
        agent_result = await manager.get_cached_agent_response("idea_generator", "prompt")
        assert agent_result is None
    
    @pytest.mark.asyncio
    async def test_cache_stats_format(self):
        """Test cache stats return format."""
        config = CacheConfig()
        manager = CacheManager(config)
        manager.is_connected = False
        
        stats = await manager.get_cache_stats()
        assert stats["status"] == "disconnected"
    
    def test_cache_config_defaults(self):
        """Test default configuration values."""
        config = CacheConfig()
        
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.ttl_seconds == 3600
        assert config.max_cache_size_mb == 100
        assert config.enable_agent_caching is True
        assert config.enable_workflow_caching is True
        assert config.key_prefix == "madspark"
    
    @pytest.mark.asyncio
    async def test_cache_with_mock_redis(self):
        """Test caching with mocked Redis client."""
        config = CacheConfig()
        manager = CacheManager(config)
        
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=None)
        mock_client.setex = AsyncMock(return_value=True)
        
        manager.redis_client = mock_client
        manager.is_connected = True
        
        # Test caching workflow
        result = {"candidates": ["idea1", "idea2"]}
        cached = await manager.cache_workflow_result("AI", "healthcare", {}, result)
        assert cached is True
        
        # Verify setex was called with correct TTL
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 3600  # TTL
        
        # Test getting from cache
        mock_client.get = AsyncMock(return_value=json.dumps({
            "result": result,
            "cached_at": datetime.now().isoformat()
        }))
        
        cached_result = await manager.get_cached_workflow("AI", "healthcare", {})
        assert cached_result == result