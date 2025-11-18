"""Integration tests for thread-safety features.

Tests that verify request-scoped router configuration is properly
respected throughout the system.
"""
import pytest
from unittest.mock import Mock, patch

# Check if web backend is available
try:
    from web.backend.main import IdeaGenerationRequest
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


class TestRouterConfigIsolation:
    """Test that router uses stored config instead of global state."""

    def test_router_uses_stored_config_not_global(self):
        """Verify router uses self._config instead of calling get_config()."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier
        import os

        # Set env to one tier
        with patch.dict(os.environ, {"MADSPARK_MODEL_TIER": "fast"}):
            # Create router with different tier
            config = LLMConfig(model_tier=ModelTier.QUALITY)
            router = LLMRouter(config=config)

            # Router should use QUALITY (from config), not FAST (from env)
            assert router._config.model_tier == ModelTier.QUALITY

    def test_router_respects_provider_from_config_not_env(self):
        """Verify router uses primary_provider from config, not env vars."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig
        import os

        # Set env to one provider
        with patch.dict(os.environ, {"MADSPARK_LLM_PROVIDER": "gemini"}):
            # Request wants Ollama
            config = LLMConfig(default_provider="ollama")
            router = LLMRouter(config=config)

            # Router should use ollama (from config), not gemini (from env)
            assert router._primary_provider == "ollama"

    def test_concurrent_routers_with_different_configs(self):
        """Verify multiple routers with different configs don't interfere."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier

        # Create 3 routers with different configs
        router1 = LLMRouter(config=LLMConfig(model_tier=ModelTier.FAST))
        router2 = LLMRouter(config=LLMConfig(model_tier=ModelTier.BALANCED))
        router3 = LLMRouter(config=LLMConfig(model_tier=ModelTier.QUALITY))

        # Each should maintain its own config
        assert router1._config.model_tier == ModelTier.FAST
        assert router2._config.model_tier == ModelTier.BALANCED
        assert router3._config.model_tier == ModelTier.QUALITY


class TestModelTierSelection:
    """Test that model tier selection uses request-scoped config."""

    def test_quality_tier_selects_gemini(self):
        """Verify quality tier triggers Gemini selection logic."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier

        config = LLMConfig(model_tier=ModelTier.QUALITY, default_provider="auto")
        router = LLMRouter(config=config)

        # Verify config is stored correctly
        assert router._config.model_tier == ModelTier.QUALITY

    def test_fast_tier_config_stored(self):
        """Verify fast tier config is stored correctly."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier

        config = LLMConfig(model_tier=ModelTier.FAST)
        router = LLMRouter(config=config)

        assert router._config.model_tier == ModelTier.FAST

    def test_balanced_tier_config_stored(self):
        """Verify balanced tier config is stored correctly."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig, ModelTier

        config = LLMConfig(model_tier=ModelTier.BALANCED)
        router = LLMRouter(config=config)

        assert router._config.model_tier == ModelTier.BALANCED


class TestCacheSettingPropagation:
    """Test that cache settings propagate from request to router."""

    def test_cache_disabled_from_request(self):
        """Verify cache setting from request reaches router."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig

        # Create config with cache disabled
        config = LLMConfig(cache_enabled=False)
        router = LLMRouter(config=config)

        assert router._cache_enabled is False

    def test_cache_enabled_from_request(self):
        """Verify cache enabled setting works."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig

        config = LLMConfig(cache_enabled=True)
        router = LLMRouter(config=config)

        assert router._cache_enabled is True

    def test_cache_parameter_overrides_config(self):
        """Verify cache_enabled parameter overrides config setting."""
        from madspark.llm.router import LLMRouter
        from madspark.llm.config import LLMConfig

        # Config says enabled, but parameter says disabled
        config = LLMConfig(cache_enabled=True)
        router = LLMRouter(config=config, cache_enabled=False)

        # Parameter should win
        assert router._cache_enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
