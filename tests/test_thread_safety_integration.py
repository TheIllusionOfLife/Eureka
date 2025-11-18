"""Integration tests for thread-safety features.

Tests that verify request-scoped router configuration is properly
respected throughout the system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

# Check if web backend is available
try:
    from web.backend.main import IdeaGenerationRequest, create_request_router
    from madspark.llm.config import ModelTier
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False


@pytest.mark.skipif(not BACKEND_AVAILABLE, reason="Web backend not available")
class TestRequestScopedRouting:
    """Test that request-scoped router configuration is respected."""

    def test_create_request_router_passes_model_tier(self):
        """Test that create_request_router creates config with requested model_tier."""
        from web.backend.main import create_request_router

        # Create request with quality tier
        request = IdeaGenerationRequest(
            topic="test topic",
            model_tier="quality",
            llm_provider="auto"
        )

        router = create_request_router(request)

        # Verify router was created with correct tier
        assert router is not None
        assert router._config.model_tier == ModelTier.QUALITY

    def test_create_request_router_respects_all_tiers(self):
        """Test that all model tiers are correctly mapped."""
        from web.backend.main import create_request_router

        tier_mappings = {
            "fast": ModelTier.FAST,
            "balanced": ModelTier.BALANCED,
            "quality": ModelTier.QUALITY,
        }

        for tier_str, tier_enum in tier_mappings.items():
            request = IdeaGenerationRequest(
                topic="test topic",
                model_tier=tier_str
            )
            router = create_request_router(request)

            assert router._config.model_tier == tier_enum, \
                f"Tier {tier_str} should map to {tier_enum}"

    def test_create_request_router_respects_provider_selection(self):
        """Test that provider selection is respected."""
        from web.backend.main import create_request_router

        providers = ["auto", "ollama", "gemini"]

        for provider in providers:
            request = IdeaGenerationRequest(
                topic="test topic",
                llm_provider=provider
            )
            router = create_request_router(request)

            assert router._primary_provider == provider, \
                f"Provider should be {provider}"

    def test_create_request_router_respects_cache_setting(self):
        """Test that cache settings are respected."""
        from web.backend.main import create_request_router

        # Test with cache enabled
        request_with_cache = IdeaGenerationRequest(
            topic="test topic",
            use_llm_cache=True
        )
        router_with_cache = create_request_router(request_with_cache)
        assert router_with_cache._cache_enabled is True

        # Test with cache disabled
        request_no_cache = IdeaGenerationRequest(
            topic="test topic",
            use_llm_cache=False
        )
        router_no_cache = create_request_router(request_no_cache)
        assert router_no_cache._cache_enabled is False


class TestStructuredGeneratorWithRouter:
    """Test that structured idea generator uses provided router."""

    def test_improve_idea_structured_uses_provided_router(self):
        """Test that improve_idea_structured uses provided router parameter."""
        from madspark.agents.structured_idea_generator import improve_idea_structured
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier

        # Create a mock router
        mock_router = Mock(spec=LLMRouter)
        mock_router.generate_structured = Mock(
            return_value=(
                Mock(improved_title="Better Idea", improved_description="Better description"),
                Mock(provider="ollama", tokens_used=100)
            )
        )

        # Patch LLM_ROUTER_AVAILABLE to True
        with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
            result = improve_idea_structured(
                original_idea="Original idea",
                critique="Needs improvement",
                advocacy_points="Strong potential",
                skeptic_points="Some risks",
                topic="test topic",
                context="test context",
                temperature=0.9,
                router=mock_router  # Provide router directly
            )

            # Verify the provided router was used
            mock_router.generate_structured.assert_called_once()
            assert "Better Idea" in result
            assert "Better description" in result

    def test_improve_idea_structured_respects_router_over_env(self):
        """Test that provided router takes precedence over env vars."""
        from madspark.agents.structured_idea_generator import improve_idea_structured
        from madspark.llm.router import LLMRouter
        import os

        # Create mock router
        mock_router = Mock(spec=LLMRouter)
        mock_router.generate_structured = Mock(
            return_value=(
                Mock(improved_title="Router Used", improved_description="Via router"),
                Mock(provider="ollama", tokens_used=50)
            )
        )

        # Even with no env vars set, provided router should be used
        with patch.dict(os.environ, {}, clear=False):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                result = improve_idea_structured(
                    original_idea="Original",
                    critique="Critique",
                    advocacy_points="Advocacy",
                    skeptic_points="Skeptic",
                    topic="topic",
                    context="context",
                    router=mock_router
                )

                # Verify router was called despite no env vars
                mock_router.generate_structured.assert_called_once()
                assert "Router Used" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
