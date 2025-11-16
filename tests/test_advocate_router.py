"""
TDD Tests for Advocate Agent LLM Router Integration.

Tests verify router routing with fallback, configuration detection, and backward compatibility.
"""

import json
import pytest
from unittest.mock import patch, Mock

from madspark.schemas.advocacy import AdvocacyResponse
from madspark.llm.response import LLMResponse


class TestAdvocateRouterIntegration:
    """Test advocate agent routing through LLM Router."""

    def test_advocate_idea_uses_router_when_configured(self):
        """Test that advocate_idea routes through LLM Router when env vars are set."""
        from madspark.agents.advocate import advocate_idea

        mock_router = Mock()
        mock_advocacy = AdvocacyResponse(
            strengths=[{"title": "Innovation", "description": "Highly innovative approach to the problem"}],
            opportunities=[{"title": "Market gap", "description": "Addresses unmet market need"}],
            addressing_concerns=[{"concern": "High cost", "response": "Phased rollout reduces initial investment"}]
        )
        mock_response = LLMResponse(
            text='{}',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=200,
            latency_ms=900,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_advocacy, mock_response)

        with patch('madspark.agents.advocate.get_router', return_value=mock_router):
            with patch('madspark.agents.advocate.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.advocate._should_use_router', return_value=True):
                    result = advocate_idea(
                        idea="AI-powered recycling sorter",
                        evaluation="Score: 8/10, Good innovation",
                        topic="Sustainability",
                        context="Urban waste management",
                        use_router=True
                    )

        mock_router.generate_structured.assert_called_once()
        call_kwargs = mock_router.generate_structured.call_args[1]
        assert "Sustainability" in call_kwargs['prompt']
        assert call_kwargs['schema'] == AdvocacyResponse

        # Result should be formatted JSON or text
        assert "Innovation" in result or "strengths" in result.lower()

    def test_advocate_idea_respects_use_router_false(self):
        """Test that router is bypassed when use_router=False."""
        from madspark.agents.advocate import advocate_idea

        mock_router = Mock()

        with patch('madspark.agents.advocate.get_router', return_value=mock_router):
            with patch('madspark.agents.advocate.LLM_ROUTER_AVAILABLE', True):
                result = advocate_idea(
                    idea="Test idea",
                    evaluation="Good evaluation",
                    topic="Topic",
                    context="Context",
                    use_router=False
                )

        mock_router.generate_structured.assert_not_called()
        assert result is not None

    def test_advocate_idea_falls_back_on_router_failure(self):
        """Test fallback to direct API when router fails."""
        from madspark.agents.advocate import advocate_idea
        from madspark.llm.exceptions import AllProvidersFailedError

        mock_router = Mock()
        mock_router.generate_structured.side_effect = AllProvidersFailedError("Failed", {})

        with patch('madspark.agents.advocate.get_router', return_value=mock_router):
            with patch('madspark.agents.advocate.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.advocate._should_use_router', return_value=True):
                    result = advocate_idea(
                        idea="Test",
                        evaluation="Eval",
                        topic="Topic",
                        context="Context"
                    )

        mock_router.generate_structured.assert_called_once()
        assert result is not None

    def test_advocate_ideas_batch_uses_router(self):
        """Test that batch advocacy uses router."""
        from madspark.agents.advocate import advocate_ideas_batch

        mock_router = Mock()
        mock_advocacy = AdvocacyResponse(
            strengths=[{"title": "Strength", "description": "Strong point here"}],
            opportunities=[{"title": "Opportunity", "description": "Market opportunity"}],
            addressing_concerns=[{"concern": "Risk", "response": "Mitigated through testing"}]
        )
        mock_response = LLMResponse(
            text='{}',
            provider="gemini",
            model="gemini-2.5-flash",
            tokens_used=500,
            latency_ms=1200,
            cost=0.0001
        )
        mock_router.generate_structured.return_value = (mock_advocacy, mock_response)

        ideas = ["Idea 1", "Idea 2"]
        evaluations = ["Eval 1", "Eval 2"]

        with patch('madspark.agents.advocate.get_router', return_value=mock_router):
            with patch('madspark.agents.advocate.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.advocate._should_use_router', return_value=True):
                    results, tokens = advocate_ideas_batch(
                        ideas=ideas,
                        evaluations=evaluations,
                        topic="Topic",
                        context="Context"
                    )

        # Should call router for each idea
        assert mock_router.generate_structured.call_count == 2
        assert len(results) == 2
        assert tokens > 0

    def test_advocate_preserves_backward_compatibility(self):
        """Test that existing callers without use_router param still work."""
        from madspark.agents.advocate import advocate_idea

        result = advocate_idea(
            idea="Test idea",
            evaluation="Good",
            topic="Topic",
            context="Context"
        )

        assert result is not None
        assert len(result) > 0


class TestAdvocateRouterConfiguration:
    """Test _should_use_router configuration detection."""

    def test_should_use_router_with_provider_env_var(self, monkeypatch):
        """Test router used when MADSPARK_LLM_PROVIDER is set."""
        from madspark.agents.advocate import _should_use_router

        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        assert _should_use_router() is True

    def test_should_use_router_false_when_no_env_vars(self, monkeypatch):
        """Test router not used when no router env vars are set."""
        from madspark.agents.advocate import _should_use_router

        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_FALLBACK_ENABLED", raising=False)

        assert _should_use_router() is False
