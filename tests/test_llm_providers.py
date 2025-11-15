"""
Unit tests for LLM Provider implementations.

Tests configuration, Ollama provider, Gemini provider, and response handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field
from datetime import datetime

from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE
from madspark.llm.providers.gemini import GeminiProvider, GENAI_AVAILABLE
from madspark.llm.response import LLMResponse
from madspark.llm.config import LLMConfig, ModelTier, get_config, reset_config
from madspark.llm.exceptions import ProviderUnavailableError, SchemaValidationError


class SimpleSchema(BaseModel):
    """Simple test schema."""

    score: float = Field(ge=0, le=10)
    comment: str


class NestedSchema(BaseModel):
    """Nested test schema."""

    title: str
    evaluation: SimpleSchema
    tags: list[str]


@pytest.fixture
def reset_config_fixture():
    """Reset config singleton after each test."""
    yield
    reset_config()


class TestLLMConfig:
    """Test LLM configuration."""

    def test_default_config(self, reset_config_fixture):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.model_tier == ModelTier.FAST
        assert config.fallback_enabled is True
        assert config.cache_enabled is True
        assert config.default_provider == "auto"

    def test_get_ollama_model_fast(self, reset_config_fixture):
        """Test fast tier returns 4B model."""
        config = LLMConfig(model_tier=ModelTier.FAST)
        assert config.get_ollama_model() == "gemma3:4b-it-qat"

    def test_get_ollama_model_balanced(self, reset_config_fixture):
        """Test balanced tier returns 12B model."""
        config = LLMConfig(model_tier=ModelTier.BALANCED)
        assert config.get_ollama_model() == "gemma3:12b-it-qat"

    def test_get_ollama_model_quality(self, reset_config_fixture):
        """Test quality tier still returns balanced Ollama model."""
        config = LLMConfig(model_tier=ModelTier.QUALITY)
        assert config.get_ollama_model() == "gemma3:12b-it-qat"

    def test_token_budget_known_type(self, reset_config_fixture):
        """Test known request types return correct budgets."""
        config = LLMConfig()
        assert config.get_token_budget("simple_score") == 150
        assert config.get_token_budget("evaluation") == 500
        assert config.get_token_budget("advocacy") == 800

    def test_token_budget_unknown_type(self, reset_config_fixture):
        """Test unknown request type returns default."""
        config = LLMConfig()
        assert config.get_token_budget("unknown_type") == 500

    def test_from_env_defaults(self, reset_config_fixture, monkeypatch):
        """Test from_env uses defaults when no env vars set."""
        # Clear relevant env vars
        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        config = LLMConfig.from_env()
        assert config.default_provider == "auto"
        assert config.model_tier == ModelTier.FAST
        assert config.ollama_host == "http://localhost:11434"

    def test_from_env_custom_values(self, reset_config_fixture, monkeypatch):
        """Test from_env reads custom env vars."""
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "balanced")
        monkeypatch.setenv("MADSPARK_FALLBACK_ENABLED", "false")
        monkeypatch.setenv("OLLAMA_HOST", "http://custom:11434")

        config = LLMConfig.from_env()
        assert config.default_provider == "ollama"
        assert config.model_tier == ModelTier.BALANCED
        assert config.fallback_enabled is False
        assert config.ollama_host == "http://custom:11434"

    def test_from_env_invalid_tier_defaults_to_fast(
        self, reset_config_fixture, monkeypatch
    ):
        """Test invalid tier falls back to FAST."""
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "invalid")

        config = LLMConfig.from_env()
        assert config.model_tier == ModelTier.FAST

    def test_singleton_get_config(self, reset_config_fixture):
        """Test get_config returns singleton."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_singleton(self, reset_config_fixture):
        """Test reset_config clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2


class TestLLMResponse:
    """Test LLM response metadata."""

    def test_response_creation(self):
        """Test basic response creation."""
        response = LLMResponse(
            text="test",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=5000,
        )
        assert response.text == "test"
        assert response.provider == "ollama"
        assert response.cost == 0.0
        assert response.cached is False
        assert isinstance(response.timestamp, datetime)

    def test_to_dict(self):
        """Test response serialization."""
        response = LLMResponse(
            text="test",
            provider="gemini",
            model="gemini-2.5-flash",
            tokens_used=100,
            latency_ms=500,
            cost=0.00002,
        )
        d = response.to_dict()
        assert d["provider"] == "gemini"
        assert d["cost"] == 0.00002
        assert d["cached"] is False
        assert "timestamp" in d

    def test_repr(self):
        """Test string representation."""
        response = LLMResponse(
            text="test",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=5000,
        )
        repr_str = repr(response)
        assert "ollama" in repr_str
        assert "gemma3:4b" in repr_str
        assert "100" in repr_str
        assert "5000" in repr_str


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not installed")
class TestOllamaProvider:
    """Test Ollama provider implementation."""

    @patch("madspark.llm.providers.ollama.ollama")
    def test_init_with_defaults(self, mock_ollama, reset_config_fixture):
        """Test initialization with default config."""
        provider = OllamaProvider()
        assert provider.provider_name == "ollama"
        assert "gemma3" in provider.model_name

    @patch("madspark.llm.providers.ollama.ollama")
    def test_init_with_custom_model(self, mock_ollama):
        """Test initialization with custom model."""
        provider = OllamaProvider(
            model="custom-model", host="http://custom:11434"
        )
        assert provider.model_name == "custom-model"
        assert provider._host == "http://custom:11434"

    @patch("madspark.llm.providers.ollama.ollama")
    def test_gemma3_supports_multimodal(self, mock_ollama):
        """Test gemma3 models support images."""
        provider = OllamaProvider(model="gemma3:4b-it-qat")
        assert provider.supports_multimodal is True

    @patch("madspark.llm.providers.ollama.ollama")
    def test_non_gemma_no_multimodal(self, mock_ollama):
        """Test non-gemma models don't support images."""
        provider = OllamaProvider(model="llama3:8b")
        assert provider.supports_multimodal is False

    @patch("madspark.llm.providers.ollama.ollama")
    def test_health_check_success(self, mock_ollama):
        """Test health check when server is running and model available."""
        mock_client = Mock()
        mock_client.list.return_value = {"models": [{"name": "gemma3:4b-it-qat"}]}

        provider = OllamaProvider(model="gemma3:4b-it-qat")
        provider._client = mock_client

        assert provider.health_check() is True

    @patch("madspark.llm.providers.ollama.ollama")
    def test_health_check_model_not_found(self, mock_ollama):
        """Test health check when model not pulled."""
        mock_client = Mock()
        mock_client.list.return_value = {"models": [{"name": "llama3:8b"}]}

        provider = OllamaProvider(model="gemma3:4b-it-qat")
        provider._client = mock_client

        assert provider.health_check() is False

    @patch("madspark.llm.providers.ollama.ollama")
    def test_health_check_server_down(self, mock_ollama):
        """Test health check when server not running."""
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        provider._client = mock_client

        assert provider.health_check() is False

    @patch("madspark.llm.providers.ollama.ollama")
    def test_generate_structured_success(self, mock_ollama):
        """Test successful structured output generation."""
        mock_response = Mock()
        mock_response.message.content = '{"score": 8.5, "comment": "Great idea"}'
        mock_response.get.return_value = 50

        mock_client = Mock()
        mock_client.chat.return_value = mock_response
        mock_client.list.return_value = {"models": [{"name": "gemma3:4b"}]}

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        validated, response = provider.generate_structured(
            prompt="Rate this idea", schema=SimpleSchema
        )

        assert validated.score == 8.5
        assert validated.comment == "Great idea"
        assert response.provider == "ollama"
        assert response.cost == 0.0
        assert response.tokens_used == 50

    @patch("madspark.llm.providers.ollama.ollama")
    def test_generate_structured_validation_error(self, mock_ollama):
        """Test schema validation error handling."""
        mock_response = Mock()
        mock_response.message.content = '{"score": "invalid", "comment": "test"}'
        mock_response.get.return_value = 50

        mock_client = Mock()
        mock_client.chat.return_value = mock_response
        mock_client.list.return_value = {"models": [{"name": "gemma3:4b"}]}

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        with pytest.raises(SchemaValidationError):
            provider.generate_structured(prompt="Test", schema=SimpleSchema)

    @patch("madspark.llm.providers.ollama.ollama")
    def test_generate_structured_server_error(self, mock_ollama):
        """Test server error handling."""
        mock_client = Mock()
        mock_client.list.return_value = {"models": [{"name": "gemma3:4b"}]}
        mock_client.chat.side_effect = Exception("Server error")

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        with pytest.raises(ProviderUnavailableError):
            provider.generate_structured(prompt="Test", schema=SimpleSchema)

    @patch("madspark.llm.providers.ollama.ollama")
    def test_estimate_token_budget_simple(self, mock_ollama):
        """Test token budget estimation for simple schema."""
        provider = OllamaProvider()

        # SimpleSchema has 2 fields
        budget = provider._estimate_token_budget(SimpleSchema.model_json_schema())

        # Should be 100 + (2 * 80) = 260
        assert budget == 260

    @patch("madspark.llm.providers.ollama.ollama")
    def test_estimate_token_budget_nested(self, mock_ollama):
        """Test token budget estimation for nested schema."""
        provider = OllamaProvider()

        budget = provider._estimate_token_budget(NestedSchema.model_json_schema())

        # Should account for nested structure
        assert budget > 260  # More than simple schema

    @patch("madspark.llm.providers.ollama.ollama")
    def test_cost_is_zero(self, mock_ollama):
        """Test local inference has zero cost."""
        provider = OllamaProvider()
        assert provider.get_cost_per_token() == 0.0


@pytest.mark.skipif(not GENAI_AVAILABLE, reason="google-genai not installed")
class TestGeminiProvider:
    """Test Gemini provider implementation."""

    @patch("madspark.llm.providers.gemini.genai")
    def test_init_requires_api_key(self, mock_genai, reset_config_fixture, monkeypatch):
        """Test initialization requires API key."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        reset_config()

        with pytest.raises(ProviderUnavailableError):
            GeminiProvider()

    @patch("madspark.llm.providers.gemini.genai")
    def test_init_with_api_key(self, mock_genai, monkeypatch):
        """Test initialization with API key."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider()
        assert provider.provider_name == "gemini"
        assert provider._api_key == "test-key"

    @patch("madspark.llm.providers.gemini.genai")
    def test_supports_multimodal(self, mock_genai, monkeypatch):
        """Test Gemini always supports multimodal."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider()
        assert provider.supports_multimodal is True

    @patch("madspark.llm.providers.gemini.genai")
    def test_cost_per_token(self, mock_genai, monkeypatch):
        """Test cost calculation."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider()
        cost = provider.get_cost_per_token()

        assert cost > 0
        assert cost < 0.001  # Less than $1 per 1000 tokens


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests with real Ollama server."""

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not installed")
    def test_real_ollama_health_check(self):
        """Test health check with real Ollama server."""
        try:
            provider = OllamaProvider(model="gemma3:4b-it-qat")
            is_healthy = provider.health_check()

            # If Ollama is running and model is pulled, should be True
            # If not running, should be False (not raise exception)
            assert isinstance(is_healthy, bool)
        except ImportError:
            pytest.skip("Ollama not installed")

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not installed")
    def test_real_ollama_structured_output(self):
        """Test structured output with real Ollama server."""
        try:
            provider = OllamaProvider(model="gemma3:4b-it-qat")

            if not provider.health_check():
                pytest.skip("Ollama server not running or model not available")

            validated, response = provider.generate_structured(
                prompt="Rate this idea (0-10): AI-powered recycling sorter",
                schema=SimpleSchema,
                temperature=0,
            )

            # Validate response structure
            assert 0 <= validated.score <= 10
            assert len(validated.comment) > 0
            assert response.provider == "ollama"
            assert response.tokens_used > 0
            assert response.latency_ms > 0
            assert response.cost == 0.0

        except ImportError:
            pytest.skip("Ollama not installed")
