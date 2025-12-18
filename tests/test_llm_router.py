"""
Unit tests for LLM Router with fallback logic.

Tests provider selection, fallback behavior, caching integration, and metrics.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from pydantic import BaseModel, Field

from madspark.llm.router import LLMRouter, get_router, reset_router
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import AllProvidersFailedError, ProviderUnavailableError
from madspark.llm.config import reset_config
from madspark.llm.cache import reset_cache


class SimpleSchema(BaseModel):
    """Simple test schema."""

    score: float = Field(ge=0, le=10)
    comment: str


@pytest.fixture
def reset_all():
    """Reset all singletons after each test."""
    yield
    reset_router()
    reset_cache()
    reset_config()


@pytest.fixture
def mock_ollama_provider():
    """Create mock Ollama provider."""
    provider = Mock()
    provider.provider_name = "ollama"
    provider.model_name = "gemma3:4b"
    provider.health_check.return_value = True
    provider.supports_multimodal = True
    provider.generate_structured.return_value = (
        SimpleSchema(score=8.5, comment="Great idea"),
        LLMResponse(
            text='{"score": 8.5, "comment": "Great idea"}',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=50,
            latency_ms=1000,
            cost=0.0,
        ),
    )
    return provider


@pytest.fixture
def mock_gemini_provider():
    """Create mock Gemini provider."""
    from .test_constants import TEST_MODEL_NAME
    provider = Mock()
    provider.provider_name = "gemini"
    provider.model_name = TEST_MODEL_NAME
    provider.health_check.return_value = True
    provider.supports_multimodal = True
    provider.generate_structured.return_value = (
        SimpleSchema(score=7.0, comment="Good from Gemini"),
        LLMResponse(
            text='{"score": 7.0, "comment": "Good from Gemini"}',
            provider="gemini",
            model=TEST_MODEL_NAME,
            tokens_used=100,
            latency_ms=500,
            cost=0.00002,
        ),
    )
    return provider


class TestLLMRouter:
    """Test LLMRouter functionality."""

    def test_router_creation(self, reset_all):
        """Test router creation with defaults."""
        router = LLMRouter()
        assert router._primary_provider == "auto"
        assert router._fallback_enabled is True
        assert router._cache_enabled is True

    def test_router_custom_config(self, reset_all):
        """Test router with custom configuration."""
        router = LLMRouter(
            primary_provider="ollama", fallback_enabled=False, cache_enabled=False
        )
        assert router._primary_provider == "ollama"
        assert router._fallback_enabled is False
        assert router._cache_enabled is False

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_select_provider_auto_prefers_ollama(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test auto mode prefers Ollama."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(primary_provider="auto")
        router._ollama = mock_ollama_provider

        provider, name = router._select_provider()
        assert name == "ollama"

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_select_provider_files_require_gemini(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_gemini_provider
    ):
        """Test files route to Gemini."""
        mock_ollama_cls.return_value = None
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        router = LLMRouter()
        router._gemini = mock_gemini_provider

        files = [Path("test.pdf")]
        provider, name = router._select_provider(files=files)
        assert name == "gemini"

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_select_provider_urls_require_gemini(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_gemini_provider
    ):
        """Test URLs route to Gemini."""
        mock_ollama_cls.return_value = None
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        router = LLMRouter()
        router._gemini = mock_gemini_provider

        urls = ["https://example.com"]
        provider, name = router._select_provider(urls=urls)
        assert name == "gemini"

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_select_provider_force_ollama(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test forcing Ollama provider."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter()
        router._ollama = mock_ollama_provider

        provider, name = router._select_provider(force_provider="ollama")
        assert name == "ollama"

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_select_provider_force_gemini(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_gemini_provider
    ):
        """Test forcing Gemini provider."""
        mock_ollama_cls.return_value = None
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        router = LLMRouter()
        router._gemini = mock_gemini_provider

        provider, name = router._select_provider(force_provider="gemini")
        assert name == "gemini"

    def test_select_provider_unknown_force(self, reset_all):
        """Test forcing unknown provider raises error."""
        router = LLMRouter()
        with pytest.raises(ValueError, match="Unknown provider"):
            router._select_provider(force_provider="unknown")

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_success(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test successful structured generation."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        validated, response = router.generate_structured(
            prompt="Test prompt", schema=SimpleSchema
        )

        assert validated.score == 8.5
        assert validated.comment == "Great idea"
        assert response.provider == "ollama"

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_with_fallback(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test fallback when primary fails."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        # Make Ollama fail
        mock_ollama_provider.generate_structured.side_effect = ProviderUnavailableError(
            "Ollama down"
        )

        router = LLMRouter(cache_enabled=False, fallback_enabled=True)
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        validated, response = router.generate_structured(
            prompt="Test", schema=SimpleSchema
        )

        # Should fallback to Gemini
        assert response.provider == "gemini"
        assert router._metrics["fallback_triggers"] == 1

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_all_fail(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test error when all providers fail."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        mock_ollama_provider.generate_structured.side_effect = RuntimeError("Ollama error")
        mock_gemini_provider.generate_structured.side_effect = RuntimeError("Gemini error")

        router = LLMRouter(cache_enabled=False, fallback_enabled=True)
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        with pytest.raises(AllProvidersFailedError):
            router.generate_structured(prompt="Test", schema=SimpleSchema)

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_metrics_tracking(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test metrics are tracked correctly."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        # Make 3 requests
        for _ in range(3):
            router.generate_structured(prompt="Test", schema=SimpleSchema)

        metrics = router.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["ollama_calls"] == 3
        assert metrics["total_tokens"] == 150  # 50 * 3
        assert metrics["total_cost"] == 0.0
        # Latency is now measured in real time (time.time() measurement),
        # not from mock response.latency_ms, so it will be very small in tests
        assert metrics["avg_latency_ms"] >= 0  # Should be a valid positive number
        assert metrics["total_latency_ms"] >= 0  # Total latency tracked

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_reset_metrics(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test metrics reset."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        router.generate_structured(prompt="Test", schema=SimpleSchema)
        assert router._metrics["total_requests"] == 1

        router.reset_metrics()
        assert router._metrics["total_requests"] == 0

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_health_status(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test health status reporting."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        router = LLMRouter()
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        status = router.health_status()

        from .test_constants import TEST_MODEL_NAME
        assert status["ollama"]["available"] is True
        assert status["ollama"]["healthy"] is True
        assert status["ollama"]["model"] == "gemma3:4b"
        assert status["gemini"]["available"] is True
        assert status["gemini"]["model"] == TEST_MODEL_NAME
        assert "cache" in status

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_fallback_disabled(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test no fallback when disabled."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        mock_ollama_provider.generate_structured.side_effect = RuntimeError("Ollama error")

        router = LLMRouter(cache_enabled=False, fallback_enabled=False)
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        with pytest.raises(AllProvidersFailedError):
            router.generate_structured(prompt="Test", schema=SimpleSchema)

        # Gemini should not have been called
        assert mock_gemini_provider.generate_structured.called is False


class TestRouterSingleton:
    """Test router singleton behavior."""

    def test_get_router_returns_singleton(self, reset_all):
        """Test get_router returns same instance."""
        router1 = get_router()
        router2 = get_router()
        assert router1 is router2

    def test_reset_router_clears_singleton(self, reset_all):
        """Test reset_router clears singleton."""
        router1 = get_router()
        reset_router()
        router2 = get_router()
        assert router1 is not router2


class TestRouterCacheIntegration:
    """Test router with cache integration."""

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    @patch("madspark.llm.router.get_cache")
    def test_cache_hit_returns_cached(
        self,
        mock_get_cache,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
    ):
        """Test cache hit returns cached value."""
        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.make_key.return_value = "test_key"
        mock_cache.get.return_value = (
            {"score": 9.0, "comment": "Cached"},
            LLMResponse(
                text="cached",
                provider="ollama",
                model="gemma3:4b",
                tokens_used=0,
                latency_ms=0,
                cached=True,
            ),
        )
        mock_get_cache.return_value = mock_cache

        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=True)
        router._ollama = mock_ollama_provider

        validated, response = router.generate_structured(
            prompt="Test", schema=SimpleSchema
        )

        assert validated.score == 9.0
        assert validated.comment == "Cached"
        assert response.cached is True
        # Provider should not have been called
        assert mock_ollama_provider.generate_structured.called is False

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    @patch("madspark.llm.router.get_cache")
    def test_cache_miss_calls_provider(
        self,
        mock_get_cache,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
    ):
        """Test cache miss calls provider and caches result."""
        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.make_key.return_value = "test_key"
        mock_cache.get.return_value = None  # Cache miss
        mock_get_cache.return_value = mock_cache

        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=True)
        router._ollama = mock_ollama_provider

        validated, response = router.generate_structured(
            prompt="Test", schema=SimpleSchema
        )

        assert validated.score == 8.5
        assert mock_cache.set.called  # Result should be cached

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    @patch("madspark.llm.router.get_cache")
    def test_cache_disabled_skips_cache(
        self,
        mock_get_cache,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
    ):
        """Test disabled cache skips caching."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        router.generate_structured(prompt="Test", schema=SimpleSchema)

        # get_cache should not be called when cache is disabled
        assert mock_get_cache.called is False


class TestFileHashComputation:
    """Test file content hashing for cache invalidation."""

    def test_compute_file_hash_consistent(self, tmp_path):
        """Hash should be consistent for same file content."""
        from madspark.llm.router import _compute_file_hash
        
        file = tmp_path / "test.txt"
        file.write_text("content")
        hash1 = _compute_file_hash(file)
        hash2 = _compute_file_hash(file)
        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of hex digest

    def test_compute_file_hash_detects_changes(self, tmp_path):
        """Hash should change when file content changes."""
        from madspark.llm.router import _compute_file_hash
        
        file = tmp_path / "test.txt"
        file.write_text("content1")
        hash1 = _compute_file_hash(file)
        file.write_text("content2")
        hash2 = _compute_file_hash(file)
        assert hash1 != hash2

    def test_compute_file_hash_missing_file(self):
        """Should raise clear error for missing file."""
        from madspark.llm.router import _compute_file_hash
        
        with pytest.raises(FileNotFoundError):
            _compute_file_hash(Path("/nonexistent/file.txt"))

    def test_compute_file_hash_binary_files(self, tmp_path):
        """Hash should work with binary files."""
        from madspark.llm.router import _compute_file_hash

        file = tmp_path / "test.bin"
        file.write_bytes(b"\x00\x01\x02\x03\x04")
        hash1 = _compute_file_hash(file)
        assert len(hash1) == 16

        # Modify binary content
        file.write_bytes(b"\x00\x01\x02\x03\x05")
        hash2 = _compute_file_hash(file)
        assert hash1 != hash2

    def test_compute_file_hash_rejects_oversized_files(self, tmp_path):
        """Should raise ValueError for files exceeding MAX_FILE_SIZE_MB."""
        from madspark.llm.router import _compute_file_hash, MAX_FILE_SIZE_MB

        # Create file larger than limit (51MB)
        large_file = tmp_path / "large.bin"
        # Write 51MB of data
        large_file.write_bytes(b"x" * (MAX_FILE_SIZE_MB + 1) * 1024 * 1024)

        with pytest.raises(ValueError, match="exceeds maximum size"):
            _compute_file_hash(large_file)
