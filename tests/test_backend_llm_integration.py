"""
Tests for backend API LLM Router integration.

Tests verify that backend endpoints properly configure and use the LLM router.
"""
import pytest
from unittest.mock import patch, Mock


class TestBackendLLMEndpoints:
    """Test LLM-specific API endpoints."""

    @pytest.fixture
    def mock_router(self):
        """Create mock router for testing."""
        router = Mock()
        router.health_status.return_value = {
            "ollama": {"available": True, "latency_ms": 10.5},
            "gemini": {"available": False, "error": "No API key"}
        }
        router.get_metrics.return_value = {
            "total_requests": 100,
            "cache_hits": 25,
            "ollama_calls": 60,
            "gemini_calls": 15,
            "total_tokens": 5000,
            "total_cost": 0.05,
            "cache_hit_rate": 0.25,
            "avg_latency_ms": 150.0
        }
        return router

    def test_llm_health_endpoint_returns_provider_status(self, mock_router):
        """Test /api/llm/health returns provider availability."""
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', True):
            with patch('web.backend.main.get_router', return_value=mock_router):
                # Import after patching
                from web.backend.main import app
                from fastapi.testclient import TestClient

                client = TestClient(app)
                response = client.get("/api/llm/health")

                assert response.status_code == 200
                data = response.json()
                assert "ollama" in data
                assert "gemini" in data
                assert data["ollama"]["available"] is True
                assert data["gemini"]["available"] is False

    def test_llm_metrics_endpoint_returns_usage_stats(self, mock_router):
        """Test /api/llm/metrics returns usage statistics."""
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', True):
            with patch('web.backend.main.get_router', return_value=mock_router):
                from web.backend.main import app
                from fastapi.testclient import TestClient

                client = TestClient(app)
                response = client.get("/api/llm/metrics")

                assert response.status_code == 200
                data = response.json()
                assert data["total_requests"] == 100
                assert data["cache_hits"] == 25
                assert data["ollama_calls"] == 60
                assert data["gemini_calls"] == 15
                assert data["cache_hit_rate"] == 0.25

    def test_llm_cache_clear_endpoint_resets_cache(self):
        """Test /api/llm/cache/clear resets the LLM cache."""
        mock_reset = Mock()
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', True):
            with patch('web.backend.main.reset_llm_cache', mock_reset):
                from web.backend.main import app
                from fastapi.testclient import TestClient

                client = TestClient(app)
                response = client.post("/api/llm/cache/clear")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                mock_reset.assert_called_once()

    def test_llm_providers_endpoint_returns_available_options(self):
        """Test /api/llm/providers returns available providers and tiers."""
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', True):
            from web.backend.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.get("/api/llm/providers")

            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert "auto" in data["providers"]
            assert "ollama" in data["providers"]
            assert "gemini" in data["providers"]
            assert "tiers" in data
            assert "fast" in data["tiers"]
            assert "balanced" in data["tiers"]
            assert "quality" in data["tiers"]


class TestBackendLLMRequestParameters:
    """Test LLM configuration in request parameters."""

    def test_idea_generation_request_includes_llm_fields(self):
        """Test IdeaGenerationRequest model has LLM configuration fields."""
        from web.backend.main import IdeaGenerationRequest

        request = IdeaGenerationRequest(
            topic="AI Ethics",
            context="Tech industry",
            llm_provider="ollama",
            model_tier="fast",
            use_llm_cache=False
        )

        assert request.llm_provider == "ollama"
        assert request.model_tier == "fast"
        assert request.use_llm_cache is False

    def test_idea_generation_request_has_defaults(self):
        """Test LLM fields have sensible defaults."""
        from web.backend.main import IdeaGenerationRequest

        request = IdeaGenerationRequest(
            topic="Testing",
            context="QA"
        )

        assert request.llm_provider == "auto"
        assert request.model_tier == "fast"
        assert request.use_llm_cache is True

    def test_idea_generation_response_includes_llm_metrics(self):
        """Test IdeaGenerationResponse can contain LLM metrics."""
        from web.backend.main import IdeaGenerationResponse, LLMMetrics

        metrics = LLMMetrics(
            total_requests=10,
            cache_hits=2,
            ollama_calls=8,
            gemini_calls=0,
            total_tokens=500,
            total_cost=0.0,
            cache_hit_rate=0.2,
            avg_latency_ms=100.0
        )

        response = IdeaGenerationResponse(
            status="success",
            message="Generated ideas",
            results=[],
            processing_time=5.0,
            timestamp="2025-01-01T00:00:00",
            llm_metrics=metrics
        )

        assert response.llm_metrics is not None
        assert response.llm_metrics.total_requests == 10
        assert response.llm_metrics.ollama_calls == 8
        assert response.llm_metrics.total_cost == 0.0

    def test_idea_generation_response_without_metrics(self):
        """Test response works without LLM metrics (backward compatibility)."""
        from web.backend.main import IdeaGenerationResponse

        response = IdeaGenerationResponse(
            status="success",
            message="Generated ideas",
            results=[],
            processing_time=5.0,
            timestamp="2025-01-01T00:00:00"
        )

        assert response.llm_metrics is None


class TestBackendLLMConfigIntegration:
    """Test LLM config integration in workflow."""

    def test_create_success_response_includes_metrics(self):
        """Test _create_success_response properly includes LLM metrics."""
        from web.backend.main import _create_success_response, LLMMetrics
        from datetime import datetime

        metrics = LLMMetrics(
            total_requests=5,
            cache_hits=1,
            ollama_calls=4,
            gemini_calls=0,
            total_tokens=200,
            total_cost=0.0,
            cache_hit_rate=0.2,
            avg_latency_ms=50.0
        )

        response = _create_success_response(
            results=[],
            start_time=datetime.now(),
            message="Test",
            llm_metrics=metrics
        )

        assert response.llm_metrics is not None
        assert response.llm_metrics.total_requests == 5
        assert response.llm_metrics.ollama_calls == 4

    def test_create_success_response_without_metrics(self):
        """Test _create_success_response works without metrics."""
        from web.backend.main import _create_success_response
        from datetime import datetime

        response = _create_success_response(
            results=[],
            start_time=datetime.now(),
            message="Test"
        )

        assert response.llm_metrics is None

    def test_llm_metrics_model_validation(self):
        """Test LLMMetrics validates field constraints."""
        from web.backend.main import LLMMetrics

        # Valid metrics
        metrics = LLMMetrics(
            total_requests=100,
            cache_hits=50,
            ollama_calls=30,
            gemini_calls=20,
            total_tokens=10000,
            total_cost=1.50,
            cache_hit_rate=0.5,
            avg_latency_ms=200.0
        )

        assert metrics.total_requests == 100
        assert metrics.cache_hit_rate == 0.5
        assert metrics.total_cost == 1.50


class TestBackendLLMRouterAvailability:
    """Test behavior when LLM router is not available."""

    @pytest.mark.skip(reason="Requires FastAPI/backend server environment (Docker)")
    def test_endpoints_disabled_when_router_unavailable(self):
        """Test LLM endpoints return 503 when router not available."""
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', False):
            from web.backend.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            # Health endpoint
            response = client.get("/api/llm/health")
            assert response.status_code == 503

            # Metrics endpoint
            response = client.get("/api/llm/metrics")
            assert response.status_code == 503

            # Cache clear endpoint
            response = client.post("/api/llm/cache/clear")
            assert response.status_code == 503

    @pytest.mark.skip(reason="Requires FastAPI/backend server environment (Docker)")
    def test_providers_endpoint_works_without_router(self):
        """Test providers endpoint still returns static info."""
        with patch('web.backend.main.LLM_ROUTER_AVAILABLE', False):
            from web.backend.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.get("/api/llm/providers")

            # Should still work as it returns static info
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
