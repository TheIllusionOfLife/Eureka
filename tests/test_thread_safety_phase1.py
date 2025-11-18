"""
Phase 1 Tests: Immutable Configuration - No Environment Variable Manipulation.

Tests that LLMConfig and LLMRouter can be initialized with explicit parameters
without requiring environment variable manipulation.
"""

import os
import pytest
from unittest.mock import patch

# Import after setting up test environment
from madspark.llm.config import LLMConfig, ModelTier
from madspark.llm.router import LLMRouter


class TestLLMConfigImmutable:
    """Test that LLMConfig accepts constructor parameters and doesn't require env manipulation."""

    def test_config_with_explicit_parameters(self):
        """Test LLMConfig initialization with explicit parameters."""
        config = LLMConfig(
            default_provider="ollama",
            model_tier=ModelTier.FAST,
            fallback_enabled=False,
            cache_enabled=True,
        )

        assert config.default_provider == "ollama"
        assert config.model_tier == ModelTier.FAST
        assert config.fallback_enabled is False
        assert config.cache_enabled is True

    def test_config_parameter_override_of_env(self):
        """Test that explicit parameters override environment variables."""
        with patch.dict(os.environ, {
            "MADSPARK_LLM_PROVIDER": "gemini",
            "MADSPARK_MODEL_TIER": "quality",
            "MADSPARK_FALLBACK_ENABLED": "true",
        }):
            # from_env should read environment
            env_config = LLMConfig.from_env()
            assert env_config.default_provider == "gemini"
            assert env_config.model_tier == ModelTier.QUALITY

            # Direct initialization should override
            override_config = LLMConfig(
                default_provider="ollama",
                model_tier=ModelTier.FAST,
                fallback_enabled=False,
            )
            assert override_config.default_provider == "ollama"
            assert override_config.model_tier == ModelTier.FAST
            assert override_config.fallback_enabled is False

    def test_config_defaults_fallback_to_env(self):
        """Test that config falls back to env when parameters not provided."""
        with patch.dict(os.environ, {
            "MADSPARK_LLM_PROVIDER": "gemini",
            "MADSPARK_MODEL_TIER": "balanced",
        }):
            config = LLMConfig.from_env()
            assert config.default_provider == "gemini"
            assert config.model_tier == ModelTier.BALANCED


class TestLLMRouterImmutable:
    """Test that LLMRouter accepts constructor parameters and doesn't modify env."""

    def test_router_with_explicit_config(self):
        """Test LLMRouter initialization with explicit config object."""
        config = LLMConfig(
            default_provider="ollama",
            model_tier=ModelTier.FAST,
            fallback_enabled=True,
            cache_enabled=False,
        )

        router = LLMRouter(config=config)

        assert router._primary_provider == "ollama"
        assert router._fallback_enabled is True
        assert router._cache_enabled is False

    def test_router_with_parameter_overrides(self):
        """Test LLMRouter parameter overrides."""
        config = LLMConfig(default_provider="auto", model_tier=ModelTier.FAST)

        router = LLMRouter(
            primary_provider="ollama",
            fallback_enabled=False,
            config=config,
        )

        # Overrides should take precedence
        assert router._primary_provider == "ollama"
        assert router._fallback_enabled is False

    def test_router_without_config_uses_env(self):
        """Test that router falls back to env-based config when no config provided."""
        with patch.dict(os.environ, {
            "MADSPARK_LLM_PROVIDER": "gemini",
            "MADSPARK_MODEL_TIER": "quality",
        }):
            router = LLMRouter()

            # Should have read from environment via get_config()
            assert router._primary_provider == "gemini"

    def test_multiple_router_instances_independent(self):
        """Test that multiple router instances don't interfere with each other."""
        config1 = LLMConfig(default_provider="ollama", model_tier=ModelTier.FAST)
        config2 = LLMConfig(default_provider="gemini", model_tier=ModelTier.QUALITY)

        router1 = LLMRouter(config=config1)
        router2 = LLMRouter(config=config2)

        # Each router should have its own configuration
        assert router1._primary_provider == "ollama"
        assert router2._primary_provider == "gemini"

        # Modifying one router's metrics shouldn't affect the other
        router1._metrics["total_requests"] = 10
        assert router2._metrics["total_requests"] == 0


class TestNoEnvironmentManipulation:
    """Test that code doesn't write to os.environ."""

    def test_router_creation_does_not_modify_env(self):
        """Test that creating router doesn't modify environment variables."""
        original_env = dict(os.environ)

        # Create router with custom config
        router = LLMRouter(
            primary_provider="ollama",
            fallback_enabled=False,
        )

        # Environment should be unchanged
        assert os.environ == original_env
        assert router._primary_provider == "ollama"

    def test_config_creation_does_not_modify_env(self):
        """Test that creating config doesn't modify environment variables."""
        original_env = dict(os.environ)

        config = LLMConfig(
            default_provider="gemini",
            model_tier=ModelTier.QUALITY,
        )

        # Environment should be unchanged
        assert os.environ == original_env
        assert config.default_provider == "gemini"


class TestBackwardCompatibility:
    """Test that existing patterns still work during migration."""

    def test_get_router_still_works(self):
        """Test that singleton get_router() still functions."""
        from madspark.llm.router import get_router

        router = get_router()
        assert router is not None
        assert hasattr(router, '_primary_provider')

    def test_config_from_env_still_works(self):
        """Test that LLMConfig.from_env() still functions."""
        with patch.dict(os.environ, {
            "MADSPARK_LLM_PROVIDER": "ollama",
            "MADSPARK_MODEL_TIER": "fast",
        }):
            config = LLMConfig.from_env()
            assert config.default_provider == "ollama"
            assert config.model_tier == ModelTier.FAST
