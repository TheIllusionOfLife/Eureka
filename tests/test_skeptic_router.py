"""
TDD Tests for Skeptic Agent LLM Router Integration.
"""

from unittest.mock import patch, Mock

from madspark.schemas.skepticism import SkepticismResponse
from madspark.llm.response import LLMResponse


class TestSkepticRouterIntegration:
    """Test skeptic agent routing through LLM Router."""

    def test_criticize_idea_uses_router_when_configured(self):
        """Test that criticize_idea routes through LLM Router."""
        from madspark.agents.skeptic import criticize_idea

        mock_router = Mock()
        mock_skepticism = SkepticismResponse(
            critical_flaws=[{"title": "Scalability", "description": "Scaling challenges identified"}],
            risks_and_challenges=[{"title": "Market risk", "description": "Market conditions volatile"}],
            questionable_assumptions=[{"assumption": "User adoption", "concern": "May be overly optimistic"}],
            missing_considerations=[{"aspect": "Legal compliance", "importance": "Critical for launch"}]
        )
        mock_response = LLMResponse(
            text='{}', provider="ollama", model="gemma3:4b", tokens_used=180, latency_ms=850, cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_skepticism, mock_response)

        with patch('madspark.agents.skeptic.get_router', return_value=mock_router):
            with patch('madspark.agents.skeptic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.skeptic._should_use_router', return_value=True):
                    result = criticize_idea(
                        idea="AI recycling sorter", advocacy="Strong innovation potential",
                        topic="Sustainability", context="Urban waste", use_router=True
                    )

        mock_router.generate_structured.assert_called_once()
        assert "Scalability" in result or "critical_flaws" in result.lower()

    def test_criticize_idea_respects_use_router_false(self):
        """Test router bypassed when use_router=False."""
        from madspark.agents.skeptic import criticize_idea

        mock_router = Mock()
        with patch('madspark.agents.skeptic.get_router', return_value=mock_router):
            with patch('madspark.agents.skeptic.LLM_ROUTER_AVAILABLE', True):
                result = criticize_idea(
                    idea="Test", advocacy="Good", topic="Topic", context="Context", use_router=False
                )

        mock_router.generate_structured.assert_not_called()
        assert result is not None

    def test_criticize_idea_falls_back_on_router_failure(self):
        """Test fallback on router failure."""
        from madspark.agents.skeptic import criticize_idea
        from madspark.llm.exceptions import AllProvidersFailedError

        mock_router = Mock()
        mock_router.generate_structured.side_effect = AllProvidersFailedError("Failed", {})

        with patch('madspark.agents.skeptic.get_router', return_value=mock_router):
            with patch('madspark.agents.skeptic.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.skeptic._should_use_router', return_value=True):
                    result = criticize_idea(
                        idea="Test", advocacy="Advocacy", topic="Topic", context="Context"
                    )

        mock_router.generate_structured.assert_called_once()
        assert result is not None

    def test_criticize_preserves_backward_compatibility(self):
        """Test existing callers work."""
        from madspark.agents.skeptic import criticize_idea

        result = criticize_idea(idea="Test", advocacy="Good", topic="Topic", context="Context")
        assert result is not None


class TestSkepticRouterConfiguration:
    """Test _should_use_router configuration detection."""

    def test_should_use_router_enabled_by_default(self, monkeypatch):
        """Test router is enabled by default (Ollama-first behavior)."""
        from madspark.agents.skeptic import _should_use_router

        # Clean environment - router should be ON by default
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)

        assert _should_use_router() is True

    def test_should_use_router_with_provider_env_var(self, monkeypatch):
        """Test router remains enabled when MADSPARK_LLM_PROVIDER is set."""
        from madspark.agents.skeptic import _should_use_router
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        assert _should_use_router() is True

    def test_should_use_router_false_when_explicitly_disabled(self, monkeypatch):
        """Test router disabled when MADSPARK_NO_ROUTER=true (opt-out behavior)."""
        from madspark.agents.skeptic import _should_use_router
        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")
        assert _should_use_router() is False
