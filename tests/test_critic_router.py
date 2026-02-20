"""
TDD Tests for Critic Agent LLM Router Integration.

These tests verify that the critic agent correctly routes through the LLM Router
when configured, with proper fallback to direct API when router fails.
"""

import json
import pytest
from unittest.mock import patch, Mock
from .test_constants import TEST_MODEL_NAME

from madspark.schemas.evaluation import CriticEvaluations
from madspark.llm.response import LLMResponse


class TestCriticRouterIntegration:
    """Test critic agent routing through LLM Router."""

    def test_evaluate_ideas_uses_router_when_configured(self):
        """Test that evaluate_ideas routes through LLM Router when env vars are set."""
        from madspark.agents.critic import evaluate_ideas

        # Create mock router
        mock_router = Mock()
        # CriticEvaluations is a RootModel of list[CriticEvaluation]
        mock_evaluations = CriticEvaluations.model_validate([
            {
                "idea_index": 0,
                "score": 9,
                "comment": "Excellent idea with strong implementation potential",
                "dimensions": {
                    "feasibility": 9.0,
                    "innovation": 8.5,
                    "impact": 9.5
                }
            }
        ])
        mock_response = LLMResponse(
            text='[{"idea_index": 0, "score": 9, "comment": "..."}]',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=150,
            latency_ms=800,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_evaluations, mock_response)

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    result, _ = evaluate_ideas(
                        ideas="1. AI-powered recycling sorter",
                        topic="Sustainability",
                        context="Urban waste management",
                        use_router=True
                    )

        # Verify router was called
        mock_router.generate_structured.assert_called_once()
        call_kwargs = mock_router.generate_structured.call_args[1]
        assert "Sustainability" in call_kwargs['prompt']
        assert "Urban waste management" in call_kwargs['prompt']
        assert call_kwargs['schema'] == CriticEvaluations

        # Verify result is valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["score"] == 9

    def test_evaluate_ideas_respects_use_router_false(self):
        """Test that router is bypassed when use_router=False."""
        from madspark.agents.critic import evaluate_ideas

        mock_router = Mock()

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic.GENAI_AVAILABLE', False):
                    # use_router=False should skip router entirely
                    result, _ = evaluate_ideas(
                        ideas="Test idea",
                        topic="Topic",
                        context="Context",
                        use_router=False
                    )

        # Router should NOT have been called
        mock_router.generate_structured.assert_not_called()
        # Should return mock structured output (GENAI_AVAILABLE=False)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert "score" in parsed[0]
        assert "comment" in parsed[0]

    def test_evaluate_ideas_falls_back_on_router_failure(self):
        """Test fallback to direct API when router fails."""
        from madspark.agents.critic import evaluate_ideas
        from madspark.llm.exceptions import AllProvidersFailedError

        mock_router = Mock()
        mock_router.generate_structured.side_effect = AllProvidersFailedError(
            "Both Ollama and Gemini failed", {}
        )

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    # Should fall back to mock response (no critic_client available in tests)
                    result, _ = evaluate_ideas(
                        ideas="Test idea",
                        topic="Topic",
                        context="Context"
                    )

        # Router was called but failed
        mock_router.generate_structured.assert_called_once()
        # Should get fallback response (mock mode in tests)
        assert "score" in result.lower() or "mock" in result.lower()

    def test_evaluate_ideas_logs_router_usage(self, caplog):
        """Test that router usage is logged with provider and token info."""
        from madspark.agents.critic import evaluate_ideas
        import logging

        mock_router = Mock()
        mock_evaluations = CriticEvaluations.model_validate([
            {"idea_index": 0, "score": 8, "comment": "Good idea with solid implementation potential", "dimensions": {"feasibility": 8.0}}
        ])
        mock_response = LLMResponse(
            text='[]',
            provider="gemini",
            model=TEST_MODEL_NAME,
            tokens_used=200,
            latency_ms=500,
            cost=0.00004
        )
        mock_router.generate_structured.return_value = (mock_evaluations, mock_response)

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    with caplog.at_level(logging.INFO):
                        evaluate_ideas(
                            ideas="Test idea",
                            topic="Topic",
                            context="Context"
                        )

        # Check logging includes provider and token info
        assert any("gemini" in record.message.lower() or "200" in record.message for record in caplog.records)

    def test_evaluate_ideas_passes_temperature_to_router(self):
        """Test that temperature parameter is passed to router."""
        from madspark.agents.critic import evaluate_ideas

        mock_router = Mock()
        mock_evaluations = CriticEvaluations.model_validate([
            {"idea_index": 0, "score": 7, "comment": "Decent idea with room for improvement", "dimensions": {}}
        ])
        mock_response = LLMResponse(
            text='[]',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=600,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_evaluations, mock_response)

        custom_temp = 0.3

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    evaluate_ideas(
                        ideas="Test idea",
                        topic="Topic",
                        context="Context",
                        temperature=custom_temp
                    )

        call_kwargs = mock_router.generate_structured.call_args[1]
        assert call_kwargs['temperature'] == custom_temp

    def test_evaluate_ideas_with_multiple_ideas_via_router(self):
        """Test routing multiple ideas through router."""
        from madspark.agents.critic import evaluate_ideas

        mock_router = Mock()
        mock_evaluations = CriticEvaluations.model_validate([
            {"idea_index": 0, "score": 9, "comment": "First idea excellent", "dimensions": {"innovation": 9.0}},
            {"idea_index": 1, "score": 7, "comment": "Second idea good", "dimensions": {"innovation": 7.0}},
            {"idea_index": 2, "score": 5, "comment": "Third idea average", "dimensions": {"innovation": 5.0}}
        ])
        mock_response = LLMResponse(
            text='[]',
            provider="ollama",
            model="gemma3:12b",
            tokens_used=350,
            latency_ms=1200,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_evaluations, mock_response)

        ideas_text = "1. First idea\n2. Second idea\n3. Third idea"

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    result, _ = evaluate_ideas(
                        ideas=ideas_text,
                        topic="Multi-idea test",
                        context="Testing multiple ideas"
                    )

        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["score"] == 9
        assert parsed[1]["score"] == 7
        assert parsed[2]["score"] == 5

    def test_router_not_called_when_unavailable(self):
        """Test that direct API is used when router is not available."""
        from madspark.agents.critic import evaluate_ideas

        mock_router = Mock()

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', False):
                result, _ = evaluate_ideas(
                    ideas="Test",
                    topic="Topic",
                    context="Context"
                )

        # Router should not be called when unavailable
        mock_router.generate_structured.assert_not_called()
        # Should still return valid result (mock mode)
        assert result is not None

    def test_evaluate_ideas_preserves_backward_compatibility(self):
        """Test that existing callers without use_router param still work."""
        from madspark.agents.critic import evaluate_ideas

        # Call without use_router parameter (should default to True)
        result, _ = evaluate_ideas(
            ideas="Test idea",
            topic="Topic",
            context="Context"
        )

        # Should work and return valid result
        assert result is not None
        assert len(result) > 0


class TestCriticRouterConfiguration:
    """Test _should_use_router configuration detection."""

    def test_should_use_router_enabled_by_default(self, monkeypatch):
        """Test router is enabled by default (Ollama-first behavior)."""
        from madspark.agents.critic import _should_use_router

        # Clean environment - router should be ON by default
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)

        assert _should_use_router() is True

    def test_should_use_router_with_provider_env_var(self, monkeypatch):
        """Test router remains enabled when MADSPARK_LLM_PROVIDER is set."""
        from madspark.agents.critic import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        assert _should_use_router() is True

    def test_should_use_router_with_model_tier_env_var(self, monkeypatch):
        """Test router remains enabled when MADSPARK_MODEL_TIER is set."""
        from madspark.agents.critic import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "balanced")
        assert _should_use_router() is True

    def test_should_use_router_with_cache_disabled(self, monkeypatch):
        """Test router remains enabled when cache is explicitly disabled."""
        from madspark.agents.critic import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "false")
        assert _should_use_router() is True

    def test_should_use_router_false_when_explicitly_disabled(self, monkeypatch):
        """Test router disabled when MADSPARK_NO_ROUTER=true (opt-out behavior)."""
        from madspark.agents.critic import _should_use_router

        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        assert _should_use_router() is False

    def test_should_use_router_false_when_unavailable(self, monkeypatch):
        """Test _should_use_router returns False when router not available."""
        # This tests the guard condition at the start of _should_use_router
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")

        with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', False):
            from madspark.agents.critic import _should_use_router
            # Even with env var set, should return False if router unavailable
            result = _should_use_router()
            assert result is False


class TestCriticRouterErrorHandling:
    """Test error handling during router operations."""

    def test_router_generic_exception_fallback(self):
        """Test fallback on generic router exceptions."""
        from madspark.agents.critic import evaluate_ideas

        mock_router = Mock()
        mock_router.generate_structured.side_effect = RuntimeError("Unexpected error")

        with patch('madspark.agents.critic.get_router', return_value=mock_router):
            with patch('madspark.agents.critic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.critic._should_use_router', return_value=True):
                    # Should not raise, should fall back
                    result, _ = evaluate_ideas(
                        ideas="Test",
                        topic="Topic",
                        context="Context"
                    )

        # Should get fallback result
        assert result is not None

    def test_invalid_input_still_raises_before_router(self):
        """Test that input validation still raises ValueError before router call."""
        from madspark.agents.critic import evaluate_ideas

        with pytest.raises(ValueError, match="ideas"):
            evaluate_ideas(
                ideas="",  # Invalid empty string
                topic="Topic",
                context="Context"
            )

        with pytest.raises(ValueError, match="topic"):
            evaluate_ideas(
                ideas="Valid idea",
                topic="",  # Invalid empty string
                context="Context"
            )

        with pytest.raises(ValueError, match="context"):
            evaluate_ideas(
                ideas="Valid idea",
                topic="Topic",
                context=""  # Invalid empty string
            )
