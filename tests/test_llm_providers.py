"""
Unit tests for LLM Provider implementations.

Tests configuration, Ollama provider, Gemini provider, and response handling.
"""
import os

# Explicit mock-mode guard - prevent accidental real API calls
# This check runs at import time to fail fast if conftest changes
assert os.environ.get("MADSPARK_MODE") == "mock", (
    "MADSPARK_MODE must be 'mock' for LLM provider tests. "
    "This prevents accidental real API calls in CI. "
    "Check tests/conftest.py pytest_configure()."
)

import pytest  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from datetime import datetime  # noqa: E402
from .test_constants import TEST_MODEL_NAME  # noqa: E402

from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE  # noqa: E402
from madspark.llm.providers.gemini import GeminiProvider, GENAI_AVAILABLE  # noqa: E402
from madspark.llm.response import LLMResponse  # noqa: E402
from madspark.llm.config import LLMConfig, ModelTier, get_config, reset_config  # noqa: E402
from madspark.llm.exceptions import ProviderUnavailableError, SchemaValidationError  # noqa: E402


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
        assert config.model_tier == ModelTier.BALANCED  # Default changed from FAST to BALANCED
        assert config.fallback_enabled is True
        assert config.cache_enabled is True
        assert config.default_provider == "auto"

    def test_get_ollama_model_fast(self, reset_config_fixture):
        """Test fast tier returns 4B model."""
        config = LLMConfig(model_tier=ModelTier.FAST)
        assert config.get_ollama_model() == "gemma3:4b"

    def test_get_ollama_model_balanced(self, reset_config_fixture):
        """Test balanced tier returns 12B model."""
        config = LLMConfig(model_tier=ModelTier.BALANCED)
        assert config.get_ollama_model() == "gemma3:12b"

    def test_get_ollama_model_quality(self, reset_config_fixture):
        """Test quality tier still returns balanced Ollama model."""
        config = LLMConfig(model_tier=ModelTier.QUALITY)
        assert config.get_ollama_model() == "gemma3:12b"

    def test_from_env_defaults(self, reset_config_fixture, monkeypatch):
        """Test from_env uses defaults when no env vars set."""
        # Clear relevant env vars
        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        config = LLMConfig.from_env()
        assert config.default_provider == "auto"
        assert config.model_tier == ModelTier.BALANCED  # Default changed from FAST to BALANCED
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

    def test_from_env_invalid_tier_defaults_to_balanced(
        self, reset_config_fixture, monkeypatch
    ):
        """Test invalid tier falls back to BALANCED."""
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "invalid")

        config = LLMConfig.from_env()
        assert config.model_tier == ModelTier.BALANCED  # Default changed from FAST to BALANCED

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

    def test_validate_api_key_valid(self, reset_config_fixture):
        """Test validate_api_key returns True for valid keys."""
        # Use obviously fake key to avoid triggering secret scanners
        config = LLMConfig(gemini_api_key="valid_gemini_key_1234567890")
        assert config.validate_api_key() is True

    def test_validate_api_key_none(self, reset_config_fixture):
        """Test validate_api_key returns False when key is None."""
        config = LLMConfig(gemini_api_key=None)
        assert config.validate_api_key() is False

    def test_validate_api_key_placeholder_patterns(self, reset_config_fixture):
        """Test validate_api_key detects placeholder patterns."""
        placeholder_keys = [
            "your-api-key-here",
            "YOUR_API_KEY",
            "replace-this",
            "placeholder",
            "example-key",
            "xxx",
            "API_KEY_HERE",
        ]
        for key in placeholder_keys:
            config = LLMConfig(gemini_api_key=key)
            assert config.validate_api_key() is False, f"Failed for key: {key}"

    def test_from_env_invalid_cache_ttl(self, reset_config_fixture, monkeypatch):
        """Test from_env handles invalid MADSPARK_CACHE_TTL gracefully."""
        monkeypatch.setenv("MADSPARK_CACHE_TTL", "not-a-number")

        config = LLMConfig.from_env()
        assert config.cache_ttl_seconds == 86400  # Default value

    def test_from_env_negative_cache_ttl(self, reset_config_fixture, monkeypatch):
        """Test from_env handles negative MADSPARK_CACHE_TTL."""
        monkeypatch.setenv("MADSPARK_CACHE_TTL", "-100")

        config = LLMConfig.from_env()
        assert config.cache_ttl_seconds == 86400  # Default value

    def test_from_env_valid_cache_ttl(self, reset_config_fixture, monkeypatch):
        """Test from_env accepts valid MADSPARK_CACHE_TTL."""
        monkeypatch.setenv("MADSPARK_CACHE_TTL", "7200")

        config = LLMConfig.from_env()
        assert config.cache_ttl_seconds == 7200

    def test_from_env_default_ollama_timeout(self, reset_config_fixture, monkeypatch):
        """Test from_env uses default OLLAMA_REQUEST_TIMEOUT."""
        monkeypatch.delenv("OLLAMA_REQUEST_TIMEOUT", raising=False)

        config = LLMConfig.from_env()
        assert config.ollama_timeout == 600.0  # Default: 10 minutes

    def test_from_env_valid_ollama_timeout(self, reset_config_fixture, monkeypatch):
        """Test from_env accepts valid OLLAMA_REQUEST_TIMEOUT."""
        monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "300")

        config = LLMConfig.from_env()
        assert config.ollama_timeout == 300.0

    def test_from_env_invalid_ollama_timeout(self, reset_config_fixture, monkeypatch):
        """Test from_env handles invalid OLLAMA_REQUEST_TIMEOUT gracefully."""
        monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "not-a-number")

        config = LLMConfig.from_env()
        assert config.ollama_timeout == 600.0  # Default value

    def test_from_env_negative_ollama_timeout(self, reset_config_fixture, monkeypatch):
        """Test from_env handles negative OLLAMA_REQUEST_TIMEOUT."""
        monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "-100")

        config = LLMConfig.from_env()
        assert config.ollama_timeout == 600.0  # Default value

    def test_from_env_zero_ollama_timeout(self, reset_config_fixture, monkeypatch):
        """Test from_env handles zero OLLAMA_REQUEST_TIMEOUT."""
        monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "0")

        config = LLMConfig.from_env()
        assert config.ollama_timeout == 600.0  # Default value


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
            model=TEST_MODEL_NAME,
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
    def test_init_with_custom_timeout(self, mock_ollama):
        """Test initialization with custom timeout."""
        provider = OllamaProvider(timeout=300.0)
        assert provider._timeout == 300.0

    @patch("madspark.llm.providers.ollama.ollama")
    def test_init_timeout_from_config(self, mock_ollama, reset_config_fixture, monkeypatch):
        """Test initialization uses timeout from config when not specified."""
        monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "450")
        reset_config()  # Force config reload
        provider = OllamaProvider()
        assert provider._timeout == 450.0

    @patch("madspark.llm.providers.ollama.ollama")
    def test_client_receives_timeout(self, mock_ollama):
        """Test that timeout is passed to ollama.Client."""
        mock_client_class = Mock()
        mock_ollama.Client = mock_client_class

        provider = OllamaProvider(timeout=300.0)
        _ = provider.client  # Trigger lazy initialization

        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs.get("timeout") == 300.0

    @patch("madspark.llm.providers.ollama.ollama")
    def test_gemma3_supports_multimodal(self, mock_ollama):
        """Test gemma3 models support images."""
        provider = OllamaProvider(model="gemma3:4b")
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
        mock_client.list.return_value = {"models": [{"model": "gemma3:4b"}]}

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        assert provider.health_check() is True

    @patch("madspark.llm.providers.ollama.ollama")
    def test_health_check_model_not_found(self, mock_ollama):
        """Test health check when model not pulled."""
        mock_client = Mock()
        mock_client.list.return_value = {"models": [{"model": "llama3:8b"}]}

        provider = OllamaProvider(model="gemma3:4b")
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
        mock_response.eval_count = 50  # Use attribute, not dict-like .get()

        mock_client = Mock()
        mock_client.chat.return_value = mock_response
        mock_client.list.return_value = {"models": [{"model": "gemma3:4b"}]}

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
        mock_client.list.return_value = {"models": [{"model": "gemma3:4b"}]}

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        with pytest.raises(SchemaValidationError):
            provider.generate_structured(prompt="Test", schema=SimpleSchema)

    @patch("madspark.llm.providers.ollama.ollama")
    def test_generate_structured_server_error(self, mock_ollama):
        """Test server error handling."""
        mock_client = Mock()
        mock_client.list.return_value = {"models": [{"model": "gemma3:4b"}]}
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

        # Should be 1000 + (2 * 400) = 1800 (increased for Japanese text support)
        assert budget == 1800

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
        # API key is stored as SecretStr for memory safety
        assert provider._api_key.get_secret_value() == "test-key"

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

    @patch("madspark.llm.providers.gemini.genai")
    def test_gemini_3_flash_pricing(self, mock_genai, monkeypatch):
        """Test Gemini 3 Flash returns correct weighted cost.

        Pricing: $0.50/1M input, $3.00/1M output
        With DEFAULT_OUTPUT_RATIO=0.3:
        Weighted = $0.50 * 0.7 + $3.00 * 0.3 = $1.25/1M = $0.00000125/token
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider(model="gemini-3-flash-preview")
        cost = provider.get_cost_per_token()

        # Expected: $1.25 per 1M tokens = 0.00000125 per token
        assert cost == pytest.approx(0.00000125, rel=0.01)

    @patch("madspark.llm.providers.gemini.genai")
    def test_unknown_model_fallback_pricing(self, mock_genai, monkeypatch):
        """Test unknown model falls back to default pricing."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider(model="unknown-future-model")
        cost = provider.get_cost_per_token()

        # Should fall back to Gemini 3 Flash pricing
        assert cost == pytest.approx(0.00000125, rel=0.01)

    @patch("madspark.llm.providers.gemini.genai")
    def test_default_model_initialization(self, mock_genai, monkeypatch, reset_config_fixture):
        """Test GeminiProvider uses GEMINI_MODEL_DEFAULT when no model specified."""
        from madspark.llm.models import GEMINI_MODEL_DEFAULT

        # Clear any existing model env var and reset config singleton
        monkeypatch.delenv("GOOGLE_GENAI_MODEL", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        reset_config()  # Force config to re-read defaults

        provider = GeminiProvider()
        assert provider.model_name == GEMINI_MODEL_DEFAULT

    @patch("madspark.llm.providers.gemini.genai")
    def test_legacy_model_pricing(self, mock_genai, monkeypatch):
        """Test legacy Gemini 2.5 Flash pricing is preserved."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        provider = GeminiProvider(model="gemini-2.5-flash")
        cost = provider.get_cost_per_token()

        # Gemini 2.5 Flash: $0.075*0.7 + $0.30*0.3 = $0.1425/1M = $0.0000001425/token
        assert cost == pytest.approx(0.0000001425, rel=0.01)


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests with real Ollama server."""

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not installed")
    def test_real_ollama_health_check(self):
        """Test health check with real Ollama server."""
        try:
            provider = OllamaProvider(model="gemma3:4b")
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
            provider = OllamaProvider(model="gemma3:4b")

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
