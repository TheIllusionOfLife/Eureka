"""
TDD Tests for Advocate Agent LLM Router Integration.

Tests verify router routing with fallback, configuration detection, and backward compatibility.
"""
import json

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

        # Result should be valid JSON with expected structure
        parsed = json.loads(result)
        assert "strengths" in parsed
        assert len(parsed["strengths"]) == 1
        assert parsed["strengths"][0]["title"] == "Innovation"

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
                    with patch('madspark.agents.advocate.GENAI_AVAILABLE', False):
                        result = advocate_idea(
                            idea="Test",
                            evaluation="Eval",
                            topic="Topic",
                            context="Context"
                        )

        mock_router.generate_structured.assert_called_once()
        assert result is not None

    def test_advocate_idea_skips_router_when_structured_output_false(self):
        """Test that router is bypassed when use_structured_output=False."""
        from madspark.agents.advocate import advocate_idea

        mock_router = Mock()

        with patch('madspark.agents.advocate.get_router', return_value=mock_router):
            with patch('madspark.agents.advocate.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.advocate._should_use_router', return_value=True):
                    with patch('madspark.agents.advocate.GENAI_AVAILABLE', False):
                        result = advocate_idea(
                            idea="Test idea",
                            evaluation="Good evaluation",
                            topic="Topic",
                            context="Context",
                            use_structured_output=False,  # Legacy text mode
                            use_router=True  # Router enabled but should be skipped
                        )

        # Router should NOT have been called when use_structured_output=False
        mock_router.generate_structured.assert_not_called()
        # Result should be plaintext, not JSON
        assert result is not None
        assert "STRENGTHS:" in result or "Mock" in result

    def test_advocate_ideas_batch_returns_results(self):
        """Test that batch advocacy returns expected results in mock mode."""
        from madspark.agents.advocate import advocate_ideas_batch

        # Batch uses different pattern - single API call for all ideas
        # Router integration for batch would require per-idea calls, less efficient
        # For now, batch continues to use direct API
        ideas_with_evals = [
            {"idea": "Idea 1", "evaluation": "Eval 1"},
            {"idea": "Idea 2", "evaluation": "Eval 2"}
        ]

        results, tokens = advocate_ideas_batch(
            ideas_with_evaluations=ideas_with_evals,
            topic="Topic",
            context="Context"
        )

        # Should return results for each idea
        assert len(results) == 2
        assert results[0]["idea_index"] == 0
        assert results[1]["idea_index"] == 1
        assert "strengths" in results[0]

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
