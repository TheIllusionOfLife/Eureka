"""
Unit tests for LLM Router batch operations.

Tests batch generation, metrics accumulation, and provider fallback for batches.
Following TDD - tests written first before implementation.
"""

import pytest
from unittest.mock import Mock, patch, call
from pydantic import BaseModel, Field
from typing import List

from madspark.llm.router import LLMRouter, reset_router
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import AllProvidersFailedError, ProviderUnavailableError
from madspark.llm.config import reset_config
from madspark.llm.cache import reset_cache


class IdeaEvaluation(BaseModel):
    """Test schema for idea evaluation."""
    score: float = Field(ge=0, le=10)
    comment: str


class AdvocacyResponse(BaseModel):
    """Test schema for advocacy."""
    strengths: List[str]
    opportunities: List[str]


@pytest.fixture
def reset_all():
    """Reset all singletons after each test."""
    yield
    reset_router()
    reset_cache()
    reset_config()


@pytest.fixture
def mock_ollama_provider():
    """Create mock Ollama provider that returns different results per call."""
    provider = Mock()
    provider.provider_name = "ollama"
    provider.model_name = "gemma3:4b"
    provider.health_check.return_value = True
    provider.supports_multimodal = True

    # Return different results for each call
    call_count = [0]
    def generate_side_effect(prompt, schema, **kwargs):
        call_count[0] += 1
        if schema == IdeaEvaluation:
            return (
                IdeaEvaluation(score=7.0 + call_count[0], comment=f"Evaluation {call_count[0]}"),
                LLMResponse(
                    text=f'{{"score": {7.0 + call_count[0]}, "comment": "Evaluation {call_count[0]}"}}',
                    provider="ollama",
                    model="gemma3:4b",
                    tokens_used=50 + call_count[0] * 10,
                    latency_ms=100 * call_count[0],
                    cost=0.0,
                ),
            )
        elif schema == AdvocacyResponse:
            return (
                AdvocacyResponse(
                    strengths=[f"Strength {call_count[0]}"],
                    opportunities=[f"Opportunity {call_count[0]}"]
                ),
                LLMResponse(
                    text=f'{{"strengths": ["Strength {call_count[0]}"], "opportunities": ["Opportunity {call_count[0]}"]}}',
                    provider="ollama",
                    model="gemma3:4b",
                    tokens_used=80 + call_count[0] * 10,
                    latency_ms=150 * call_count[0],
                    cost=0.0,
                ),
            )
        else:
            raise ValueError(f"Unknown schema: {schema}")

    provider.generate_structured.side_effect = generate_side_effect
    return provider


@pytest.fixture
def mock_gemini_provider():
    """Create mock Gemini provider."""
    provider = Mock()
    provider.provider_name = "gemini"
    provider.model_name = "gemini-2.5-flash"
    provider.health_check.return_value = True
    provider.supports_multimodal = True

    call_count = [0]
    def generate_side_effect(prompt, schema, **kwargs):
        call_count[0] += 1
        if schema == IdeaEvaluation:
            return (
                IdeaEvaluation(score=6.0 + call_count[0], comment=f"Gemini eval {call_count[0]}"),
                LLMResponse(
                    text=f'{{"score": {6.0 + call_count[0]}, "comment": "Gemini eval {call_count[0]}"}}',
                    provider="gemini",
                    model="gemini-2.5-flash",
                    tokens_used=100 + call_count[0] * 10,
                    latency_ms=200 * call_count[0],
                    cost=0.00001 * call_count[0],
                ),
            )
        else:
            raise ValueError(f"Unknown schema: {schema}")

    provider.generate_structured.side_effect = generate_side_effect
    return provider


class TestRouterBatchOperations:
    """Test batch generation capabilities."""

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_single_item(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch generation with single item."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        prompts = ["Evaluate idea 1"]
        results, total_response = router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
            system_instruction="Evaluate ideas",
        )

        assert len(results) == 1
        assert results[0].score == 8.0
        assert results[0].comment == "Evaluation 1"
        assert total_response.provider == "ollama"
        assert total_response.tokens_used == 60  # 50 + 10

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_multiple_items(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch generation with multiple items."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        prompts = [
            "Evaluate idea 1",
            "Evaluate idea 2",
            "Evaluate idea 3",
        ]
        results, total_response = router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
        )

        assert len(results) == 3
        # Each call increments score by 1
        assert results[0].score == 8.0  # 7.0 + 1
        assert results[1].score == 9.0  # 7.0 + 2
        assert results[2].score == 10.0  # 7.0 + 3

        # Aggregate metrics
        assert total_response.tokens_used == 60 + 70 + 80  # 210
        assert total_response.cost == 0.0  # Ollama is free

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_metrics_accumulation(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test that batch operations accumulate metrics correctly."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        prompts = ["Evaluate 1", "Evaluate 2"]
        router.generate_structured_batch(prompts=prompts, schema=IdeaEvaluation)

        metrics = router.get_metrics()
        assert metrics["total_requests"] == 2  # Each prompt counts as request
        assert metrics["ollama_calls"] == 2
        assert metrics["total_tokens"] == 60 + 70  # 130
        assert metrics["cache_hits"] == 0

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_empty_list(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch generation with empty list returns empty results."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        results, total_response = router.generate_structured_batch(
            prompts=[],
            schema=IdeaEvaluation,
        )

        assert len(results) == 0
        assert total_response.tokens_used == 0
        assert total_response.cost == 0.0
        # Provider should not be called
        assert mock_ollama_provider.generate_structured.called is False

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_with_fallback(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test batch operation falls back when primary fails mid-batch."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        # Ollama fails on second call
        call_count = [0]
        def ollama_side_effect(prompt, schema, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ProviderUnavailableError("Ollama crashed")
            return (
                IdeaEvaluation(score=8.0, comment="Ollama result"),
                LLMResponse(
                    text='{"score": 8.0, "comment": "Ollama result"}',
                    provider="ollama",
                    model="gemma3:4b",
                    tokens_used=50,
                    latency_ms=100,
                    cost=0.0,
                ),
            )

        mock_ollama_provider.generate_structured.side_effect = ollama_side_effect

        router = LLMRouter(cache_enabled=False, fallback_enabled=True)
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        prompts = ["Eval 1", "Eval 2", "Eval 3"]
        results, total_response = router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
        )

        assert len(results) == 3
        # First from Ollama, second and third from Gemini (after fallback)
        assert results[0].comment == "Ollama result"
        assert "Gemini" in results[1].comment
        assert "Gemini" in results[2].comment

        metrics = router.get_metrics()
        assert metrics["fallback_triggers"] >= 1  # At least one fallback

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_all_fail_raises_error(
        self,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
        mock_gemini_provider,
    ):
        """Test batch operation raises error when all providers fail."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = Mock(return_value=mock_gemini_provider)

        mock_ollama_provider.generate_structured.side_effect = RuntimeError("Ollama error")
        mock_gemini_provider.generate_structured.side_effect = RuntimeError("Gemini error")

        router = LLMRouter(cache_enabled=False, fallback_enabled=True)
        router._ollama = mock_ollama_provider
        router._gemini = mock_gemini_provider

        prompts = ["Eval 1", "Eval 2"]
        with pytest.raises(AllProvidersFailedError):
            router.generate_structured_batch(prompts=prompts, schema=IdeaEvaluation)

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    @patch("madspark.llm.router.get_cache")
    def test_generate_structured_batch_with_caching(
        self,
        mock_get_cache,
        mock_gemini_cls,
        mock_ollama_cls,
        reset_all,
        mock_ollama_provider,
    ):
        """Test batch operations utilize caching per prompt."""
        mock_cache = Mock()
        mock_cache.enabled = True

        # Cache hit for second prompt
        cache_keys = {}
        def make_key_side_effect(prompt, schema, temperature, **kwargs):
            key = f"key_{prompt}"
            cache_keys[prompt] = key
            return key

        def get_side_effect(key):
            if "Eval 2" in key:
                # Cache hit for second prompt
                return (
                    {"score": 9.5, "comment": "Cached result"},
                    LLMResponse(
                        text='{"score": 9.5, "comment": "Cached result"}',
                        provider="ollama",
                        model="gemma3:4b",
                        tokens_used=0,
                        latency_ms=0,
                        cached=True,
                    ),
                )
            return None  # Cache miss

        mock_cache.make_key.side_effect = make_key_side_effect
        mock_cache.get.side_effect = get_side_effect
        mock_get_cache.return_value = mock_cache

        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=True)
        router._ollama = mock_ollama_provider

        prompts = ["Eval 1", "Eval 2", "Eval 3"]
        results, total_response = router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
        )

        assert len(results) == 3
        # Second result should be from cache
        assert results[1].score == 9.5
        assert results[1].comment == "Cached result"

        metrics = router.get_metrics()
        assert metrics["cache_hits"] >= 1

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_different_schemas(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch operations work with different schemas."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        # First batch with IdeaEvaluation
        eval_prompts = ["Eval 1"]
        eval_results, _ = router.generate_structured_batch(
            prompts=eval_prompts,
            schema=IdeaEvaluation,
        )

        # Second batch with AdvocacyResponse
        advocacy_prompts = ["Advocate 1"]
        advocacy_results, _ = router.generate_structured_batch(
            prompts=advocacy_prompts,
            schema=AdvocacyResponse,
        )

        assert len(eval_results) == 1
        assert hasattr(eval_results[0], "score")
        assert len(advocacy_results) == 1
        assert hasattr(advocacy_results[0], "strengths")

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_with_system_instruction(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch operations pass system instruction to each call."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        prompts = ["Eval 1", "Eval 2"]
        router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
            system_instruction="You are a strict evaluator.",
        )

        # Verify system_instruction passed to all calls
        calls = mock_ollama_provider.generate_structured.call_args_list
        assert len(calls) == 2
        for call_args in calls:
            assert call_args.kwargs.get("system_instruction") == "You are a strict evaluator."

    @patch("madspark.llm.router._get_ollama_provider")
    @patch("madspark.llm.router._get_gemini_provider")
    def test_generate_structured_batch_with_temperature(
        self, mock_gemini_cls, mock_ollama_cls, reset_all, mock_ollama_provider
    ):
        """Test batch operations pass temperature to each call."""
        mock_ollama_cls.return_value = Mock(return_value=mock_ollama_provider)
        mock_gemini_cls.return_value = None

        router = LLMRouter(cache_enabled=False)
        router._ollama = mock_ollama_provider

        prompts = ["Eval 1"]
        router.generate_structured_batch(
            prompts=prompts,
            schema=IdeaEvaluation,
            temperature=0.8,
        )

        call_args = mock_ollama_provider.generate_structured.call_args
        assert call_args.kwargs.get("temperature") == 0.8

    def test_generate_structured_batch_invalid_prompts_type(self, reset_all):
        """Test batch generation with invalid prompts type raises error."""
        router = LLMRouter(cache_enabled=False)

        with pytest.raises((TypeError, ValueError)):
            router.generate_structured_batch(
                prompts="not a list",  # Should be a list
                schema=IdeaEvaluation,
            )

    def test_generate_structured_batch_none_prompts(self, reset_all):
        """Test batch generation with None prompts raises error."""
        router = LLMRouter(cache_enabled=False)

        with pytest.raises((TypeError, ValueError)):
            router.generate_structured_batch(
                prompts=None,
                schema=IdeaEvaluation,
            )


class TestRouterDefaultBehavior:
    """Test router is used by default (Ollama-first)."""

    @patch("madspark.llm.utils.os.getenv")
    def test_should_use_router_returns_true_by_default(self, mock_getenv, reset_all):
        """Test should_use_router returns True by default when router available."""
        from madspark.llm.utils import should_use_router

        # No environment variables set
        mock_getenv.return_value = None

        mock_get_router = Mock()
        result = should_use_router(router_available=True, get_router_func=mock_get_router)

        # Should return True by default (router-first behavior)
        assert result is True

    @patch("madspark.llm.utils.os.getenv")
    def test_should_use_router_false_when_unavailable(self, mock_getenv, reset_all):
        """Test should_use_router returns False when router not available."""
        from madspark.llm.utils import should_use_router

        mock_getenv.return_value = None

        result = should_use_router(router_available=False, get_router_func=None)
        assert result is False

    @patch("madspark.llm.utils.os.getenv")
    def test_should_use_router_respects_no_router_flag(self, mock_getenv, reset_all):
        """Test should_use_router returns False when --no-router flag is set."""
        from madspark.llm.utils import should_use_router

        # Simulate --no-router flag
        def getenv_side_effect(key, default=None):
            if key == "MADSPARK_NO_ROUTER":
                return "true"
            return default

        mock_getenv.side_effect = getenv_side_effect
        mock_get_router = Mock()

        result = should_use_router(router_available=True, get_router_func=mock_get_router)
        assert result is False
