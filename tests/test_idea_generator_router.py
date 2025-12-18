"""
TDD Tests for Idea Generator Agent LLM Router Integration.

Tests verify router routing with fallback, configuration detection, and backward compatibility.
"""

import json
from unittest.mock import patch, Mock
from .test_constants import TEST_MODEL_NAME

from madspark.schemas.generation import GeneratedIdeas
from madspark.llm.response import LLMResponse


class TestIdeaGeneratorRouterIntegration:
    """Test idea generator agent routing through LLM Router."""

    def test_generate_ideas_uses_router_when_configured(self):
        """Test that generate_ideas routes through LLM Router when env vars are set."""
        from madspark.agents.idea_generator import generate_ideas

        mock_router = Mock()
        mock_ideas = GeneratedIdeas.model_validate([
            {
                "idea_number": 1,
                "title": "AI-Powered Water Purifier",
                "description": "Smart water purification system using AI to optimize filtering process",
                "key_features": ["Real-time monitoring", "Auto-calibration", "Energy efficient"],
                "category": "Clean Water Technology"
            },
            {
                "idea_number": 2,
                "title": "Solar Desalination Plant",
                "description": "Portable solar-powered desalination unit for coastal communities",
                "key_features": ["Portable", "Solar powered", "Low maintenance"],
                "category": "Renewable Energy"
            }
        ])
        mock_response = LLMResponse(
            text='[{...}]',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=250,
            latency_ms=1100,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_ideas, mock_response)

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.idea_generator._should_use_router', return_value=True):
                    result = generate_ideas(
                        topic="Water purification",
                        context="Rural communities with limited infrastructure",
                        use_router=True
                    )

        mock_router.generate_structured.assert_called_once()
        call_kwargs = mock_router.generate_structured.call_args[1]
        assert "Water purification" in call_kwargs['prompt']
        assert call_kwargs['schema'] == GeneratedIdeas

        # Result should be JSON array of ideas
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["title"] == "AI-Powered Water Purifier"

    def test_generate_ideas_respects_use_router_false(self):
        """Test that router is bypassed when use_router=False."""
        from madspark.agents.idea_generator import generate_ideas

        mock_router = Mock()

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', True):
                result = generate_ideas(
                    topic="Test topic",
                    context="Test context",
                    use_router=False
                )

        mock_router.generate_structured.assert_not_called()
        assert result is not None

    def test_generate_ideas_falls_back_on_router_failure(self):
        """Test fallback to direct API when router fails."""
        from madspark.agents.idea_generator import generate_ideas
        from madspark.llm.exceptions import AllProvidersFailedError

        mock_router = Mock()
        mock_router.generate_structured.side_effect = AllProvidersFailedError("All providers failed", {})

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.idea_generator._should_use_router', return_value=True):
                    result = generate_ideas(
                        topic="Test",
                        context="Context"
                    )

        mock_router.generate_structured.assert_called_once()
        assert result is not None

    def test_generate_ideas_passes_temperature_to_router(self):
        """Test that temperature parameter is passed to router."""
        from madspark.agents.idea_generator import generate_ideas

        mock_router = Mock()
        mock_ideas = GeneratedIdeas.model_validate([
            {
                "idea_number": 1,
                "title": "Test Idea",
                "description": "A test idea for temperature testing",
                "key_features": ["Feature 1"],
                "category": "Test"
            }
        ])
        mock_response = LLMResponse(
            text='[]',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=600,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_ideas, mock_response)

        custom_temp = 0.95

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.idea_generator._should_use_router', return_value=True):
                    generate_ideas(
                        topic="Test",
                        context="Context",
                        temperature=custom_temp
                    )

        call_kwargs = mock_router.generate_structured.call_args[1]
        assert call_kwargs['temperature'] == custom_temp

    def test_generate_ideas_logs_router_usage(self, caplog):
        """Test that router usage is logged with provider and token info."""
        from madspark.agents.idea_generator import generate_ideas
        import logging

        mock_router = Mock()
        mock_ideas = GeneratedIdeas.model_validate([
            {
                "idea_number": 1,
                "title": "Test Idea",
                "description": "Test idea for logging verification",
                "key_features": ["Feature"],
                "category": "Test"
            }
        ])
        mock_response = LLMResponse(
            text='[]',
            provider="gemini",
            model="TEST_MODEL_NAME",
            tokens_used=300,
            latency_ms=700,
            cost=0.00006
        )
        mock_router.generate_structured.return_value = (mock_ideas, mock_response)

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.idea_generator._should_use_router', return_value=True):
                    with caplog.at_level(logging.INFO):
                        generate_ideas(
                            topic="Test",
                            context="Context"
                        )

        # Check logging includes provider and token info
        assert any("gemini" in record.message.lower() or "300" in record.message for record in caplog.records)

    def test_router_not_called_when_unavailable(self):
        """Test that direct API is used when router is not available."""
        from madspark.agents.idea_generator import generate_ideas

        mock_router = Mock()

        with patch('madspark.agents.idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.idea_generator.LLM_ROUTER_AVAILABLE', False):
                result = generate_ideas(
                    topic="Test",
                    context="Context"
                )

        mock_router.generate_structured.assert_not_called()
        assert result is not None

    def test_generate_ideas_preserves_backward_compatibility(self):
        """Test that existing callers without use_router param still work."""
        from madspark.agents.idea_generator import generate_ideas

        # Call without use_router parameter (should default to True)
        result = generate_ideas(
            topic="Innovation in healthcare",
            context="Resource-limited settings"
        )

        assert result is not None
        assert len(result) > 0


class TestIdeaGeneratorRouterConfiguration:
    """Test _should_use_router configuration detection."""

    def test_should_use_router_enabled_by_default(self, monkeypatch):
        """Test router is enabled by default (Ollama-first behavior)."""
        from madspark.agents.idea_generator import _should_use_router

        # Clean environment - router should be ON by default
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)

        assert _should_use_router() is True

    def test_should_use_router_with_provider_env_var(self, monkeypatch):
        """Test router remains enabled when MADSPARK_LLM_PROVIDER is set."""
        from madspark.agents.idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        assert _should_use_router() is True

    def test_should_use_router_with_model_tier_env_var(self, monkeypatch):
        """Test router remains enabled when MADSPARK_MODEL_TIER is set."""
        from madspark.agents.idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "quality")
        assert _should_use_router() is True

    def test_should_use_router_with_cache_disabled(self, monkeypatch):
        """Test router remains enabled when cache is explicitly disabled."""
        from madspark.agents.idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "false")
        assert _should_use_router() is True

    def test_should_use_router_false_when_explicitly_disabled(self, monkeypatch):
        """Test router disabled when MADSPARK_NO_ROUTER=true (opt-out behavior)."""
        from madspark.agents.idea_generator import _should_use_router

        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        assert _should_use_router() is False
