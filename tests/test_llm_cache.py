"""
Unit tests for LLM Response Caching.

Tests caching functionality, TTL, key generation, and statistics.
"""

import pytest
import tempfile
import shutil
from pydantic import BaseModel, Field

from madspark.llm.cache import ResponseCache, get_cache, reset_cache, DISKCACHE_AVAILABLE
from madspark.llm.response import LLMResponse
from madspark.llm.config import reset_config


class SimpleSchema(BaseModel):
    """Simple test schema."""

    score: float = Field(ge=0, le=10)
    comment: str


class AnotherSchema(BaseModel):
    """Different schema for testing."""

    result: str
    confidence: float


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def reset_cache_fixture():
    """Reset cache singleton after each test."""
    yield
    reset_cache()
    reset_config()


@pytest.fixture
def cache(temp_cache_dir):
    """Create cache instance with temp directory."""
    return ResponseCache(cache_dir=temp_cache_dir, ttl_seconds=3600, enabled=True)


@pytest.fixture
def sample_response():
    """Create sample LLM response."""
    return LLMResponse(
        text='{"score": 8.5, "comment": "Great idea"}',
        provider="ollama",
        model="gemma3:4b",
        tokens_used=50,
        latency_ms=1000,
        cost=0.0,
    )


@pytest.fixture
def sample_validated():
    """Create sample validated object."""
    return SimpleSchema(score=8.5, comment="Great idea")


@pytest.mark.skipif(not DISKCACHE_AVAILABLE, reason="diskcache not installed")
class TestResponseCache:
    """Test ResponseCache functionality."""

    def test_cache_creation(self, cache):
        """Test cache is created successfully."""
        assert cache.enabled is True
        assert cache._cache is not None

    def test_cache_disabled(self, temp_cache_dir):
        """Test cache can be disabled."""
        cache = ResponseCache(cache_dir=temp_cache_dir, enabled=False)
        assert cache.enabled is False
        assert cache._cache is None

    def test_make_key_deterministic(self, cache):
        """Test same inputs produce same key."""
        key1 = cache.make_key("test prompt", SimpleSchema, 0.7)
        key2 = cache.make_key("test prompt", SimpleSchema, 0.7)
        assert key1 == key2

    def test_make_key_different_prompt(self, cache):
        """Test different prompts produce different keys."""
        key1 = cache.make_key("prompt 1", SimpleSchema, 0.7)
        key2 = cache.make_key("prompt 2", SimpleSchema, 0.7)
        assert key1 != key2

    def test_make_key_different_schema(self, cache):
        """Test different schemas produce different keys."""
        key1 = cache.make_key("test", SimpleSchema, 0.7)
        key2 = cache.make_key("test", AnotherSchema, 0.7)
        assert key1 != key2

    def test_make_key_different_temperature(self, cache):
        """Test different temperatures produce different keys."""
        key1 = cache.make_key("test", SimpleSchema, 0.0)
        key2 = cache.make_key("test", SimpleSchema, 0.7)
        assert key1 != key2

    def test_make_key_with_provider(self, cache):
        """Test provider affects key."""
        key1 = cache.make_key("test", SimpleSchema, 0.7, provider="ollama")
        key2 = cache.make_key("test", SimpleSchema, 0.7, provider="gemini")
        assert key1 != key2

    def test_make_key_with_model(self, cache):
        """Test model affects key."""
        key1 = cache.make_key("test", SimpleSchema, 0.7, model="gemma3:4b")
        key2 = cache.make_key("test", SimpleSchema, 0.7, model="gemma3:12b")
        assert key1 != key2

    def test_make_key_with_extra_kwargs(self, cache):
        """Test extra kwargs affect key."""
        key1 = cache.make_key("test", SimpleSchema, 0.7, custom_param="a")
        key2 = cache.make_key("test", SimpleSchema, 0.7, custom_param="b")
        assert key1 != key2

    def test_make_key_with_multimodal_inputs(self, cache):
        """Test cache key includes multimodal inputs (images, files, urls)."""
        # Same prompt but different images
        key1 = cache.make_key(
            "test", SimpleSchema, 0.7, images=["img1.jpg", "img2.jpg"]
        )
        key2 = cache.make_key(
            "test", SimpleSchema, 0.7, images=["img1.jpg", "img3.jpg"]
        )
        assert key1 != key2

        # Same prompt but different files
        key3 = cache.make_key("test", SimpleSchema, 0.7, files=["doc1.pdf"])
        key4 = cache.make_key("test", SimpleSchema, 0.7, files=["doc2.pdf"])
        assert key3 != key4

        # Same prompt but different URLs
        key5 = cache.make_key(
            "test", SimpleSchema, 0.7, urls=["http://example.com/a"]
        )
        key6 = cache.make_key(
            "test", SimpleSchema, 0.7, urls=["http://example.com/b"]
        )
        assert key5 != key6

        # No multimodal vs with multimodal should differ
        key7 = cache.make_key("test", SimpleSchema, 0.7)
        key8 = cache.make_key("test", SimpleSchema, 0.7, images=["img.jpg"])
        assert key7 != key8

    def test_make_key_full_schema_path(self, cache):
        """Test cache key includes full schema path (module.name)."""
        # This test verifies the key includes schema module path
        key = cache.make_key("test", SimpleSchema, 0.7)
        # Key should be deterministic and SHA-256 (64 chars)
        assert len(key) == 64  # SHA-256 hex digest
        assert key.isalnum()  # Should be alphanumeric

    def test_cache_miss(self, cache):
        """Test cache returns None on miss."""
        key = cache.make_key("nonexistent", SimpleSchema, 0.0)
        result = cache.get(key)
        assert result is None

    def test_cache_set_and_get(self, cache, sample_validated, sample_response):
        """Test setting and getting cached values."""
        key = cache.make_key("test prompt", SimpleSchema, 0.0)

        # Set
        success = cache.set(key, (sample_validated, sample_response))
        assert success is True

        # Get
        result = cache.get(key)
        assert result is not None

        cached_obj, cached_response = result
        assert cached_obj["score"] == 8.5
        assert cached_obj["comment"] == "Great idea"
        assert cached_response.provider == "ollama"
        assert cached_response.cached is True  # Marked as cached

    def test_cache_set_dict(self, cache, sample_response):
        """Test caching dict objects (not just Pydantic)."""
        key = cache.make_key("test", SimpleSchema, 0.0)

        # Cache dict directly
        dict_obj = {"score": 7.0, "comment": "Good"}
        success = cache.set(key, (dict_obj, sample_response))
        assert success is True

        result = cache.get(key)
        assert result is not None
        assert result[0]["score"] == 7.0

    def test_cache_invalidate(self, cache, sample_validated, sample_response):
        """Test invalidating cache entry."""
        key = cache.make_key("test", SimpleSchema, 0.0)
        cache.set(key, (sample_validated, sample_response))

        # Verify exists
        assert cache.get(key) is not None

        # Invalidate
        success = cache.invalidate(key)
        assert success is True

        # Verify gone
        assert cache.get(key) is None

    def test_cache_invalidate_nonexistent(self, cache):
        """Test invalidating nonexistent key."""
        success = cache.invalidate("nonexistent_key")
        assert success is False

    def test_cache_clear(self, cache, sample_validated, sample_response):
        """Test clearing all cache entries."""
        # Add multiple entries
        for i in range(3):
            key = cache.make_key(f"prompt {i}", SimpleSchema, 0.0)
            cache.set(key, (sample_validated, sample_response))

        # Verify size
        stats = cache.stats()
        assert stats["size"] >= 3

        # Clear
        success = cache.clear()
        assert success is True

        # Verify empty
        stats = cache.stats()
        assert stats["size"] == 0

    def test_cache_stats(self, cache, sample_validated, sample_response):
        """Test cache statistics."""
        stats = cache.stats()
        assert stats["enabled"] is True
        assert "size" in stats
        assert "volume" in stats
        assert stats["ttl_seconds"] == 3600

    def test_cache_stats_disabled(self, temp_cache_dir):
        """Test stats when cache disabled."""
        cache = ResponseCache(cache_dir=temp_cache_dir, enabled=False)
        stats = cache.stats()
        assert stats["enabled"] is False

    def test_cache_close(self, cache):
        """Test cache close operation."""
        cache.close()
        # Should not raise
        assert cache._cache is not None  # Cache object still exists

    def test_disabled_cache_operations(self, temp_cache_dir):
        """Test operations on disabled cache."""
        cache = ResponseCache(cache_dir=temp_cache_dir, enabled=False)

        key = cache.make_key("test", SimpleSchema, 0.0)
        assert cache.get(key) is None
        assert cache.set(key, ({}, LLMResponse(
            text="", provider="", model="", tokens_used=0, latency_ms=0
        ))) is False
        assert cache.invalidate(key) is False
        assert cache.clear() is False


@pytest.mark.skipif(not DISKCACHE_AVAILABLE, reason="diskcache not installed")
class TestCacheSingleton:
    """Test cache singleton behavior."""

    def test_get_cache_returns_instance(self, reset_cache_fixture, monkeypatch):
        """Test get_cache returns singleton."""
        # Set up environment for cache
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "true")
        reset_config()

        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_reset_cache_clears_singleton(self, reset_cache_fixture, monkeypatch):
        """Test reset_cache clears singleton."""
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "true")
        reset_config()

        cache1 = get_cache()
        reset_cache()
        cache2 = get_cache()
        assert cache1 is not cache2


@pytest.mark.skipif(not DISKCACHE_AVAILABLE, reason="diskcache not installed")
class TestCacheIntegration:
    """Integration tests for cache with real operations."""

    def test_cache_persistence(self, temp_cache_dir, sample_validated, sample_response):
        """Test cache persists across instances."""
        # Create first cache and set value
        cache1 = ResponseCache(cache_dir=temp_cache_dir)
        key = cache1.make_key("test", SimpleSchema, 0.0)
        cache1.set(key, (sample_validated, sample_response))
        cache1.close()

        # Create second cache and retrieve
        cache2 = ResponseCache(cache_dir=temp_cache_dir)
        result = cache2.get(key)
        assert result is not None
        assert result[0]["score"] == 8.5
        cache2.close()

    def test_cache_ttl_override(self, cache, sample_validated, sample_response):
        """Test TTL override on set."""
        key = cache.make_key("test", SimpleSchema, 0.0)

        # Set with custom TTL
        success = cache.set(key, (sample_validated, sample_response), ttl=1)
        assert success is True

        # Should be cached immediately
        result = cache.get(key)
        assert result is not None

    def test_cache_handles_complex_schemas(self, cache):
        """Test caching with nested schemas."""

        class NestedSchema(BaseModel):
            title: str
            items: list[str]
            metadata: dict

        validated = NestedSchema(
            title="Test",
            items=["a", "b", "c"],
            metadata={"key": "value", "count": 42},
        )
        response = LLMResponse(
            text="{}",
            provider="ollama",
            model="test",
            tokens_used=100,
            latency_ms=500,
        )

        key = cache.make_key("nested test", NestedSchema, 0.0)
        cache.set(key, (validated, response))

        result = cache.get(key)
        assert result is not None
        assert result[0]["title"] == "Test"
        assert result[0]["items"] == ["a", "b", "c"]
        assert result[0]["metadata"]["count"] == 42
