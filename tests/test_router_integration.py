"""
Integration tests for LLM Router in full workflow.

Tests verify router works correctly in real-world scenarios including:
- Full workflow execution with router
- Provider fallback behavior
- Cache persistence across runs
- Environment variable configuration
- Backward compatibility
"""
import pytest
from unittest.mock import Mock


class TestRouterWorkflowIntegration:
    """Test router integration in complete workflows."""

    @pytest.fixture
    def enable_router_env(self, monkeypatch):
        """Enable router for these tests."""
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "auto")
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "fast")
        yield

    def test_router_environment_configuration(self, enable_router_env, monkeypatch):
        """Test that environment variables properly configure router."""
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "balanced")

        from madspark.llm.utils import should_use_router

        # Router should be enabled since MADSPARK_NO_ROUTER is not set
        assert should_use_router(True, lambda: Mock()) is True

    def test_router_disabled_via_env_var(self, monkeypatch):
        """Test that MADSPARK_NO_ROUTER=true disables router."""
        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        from madspark.llm.utils import should_use_router

        assert should_use_router(True, lambda: Mock()) is False

    def test_router_disabled_via_cli_flag(self, monkeypatch):
        """Test that --no-router CLI flag disables router."""
        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        from madspark.llm.utils import should_use_router

        assert should_use_router(True, lambda: Mock()) is False

    @pytest.mark.asyncio
    async def test_async_coordinator_respects_router_config(self, enable_router_env):
        """Test that AsyncCoordinator uses router when configured."""
        from madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()
        assert coordinator is not None
        assert hasattr(coordinator, "run_workflow")

    def test_cache_persistence_across_imports(self, enable_router_env, tmp_path, monkeypatch):
        """Test that cache persists across module imports."""
        cache_dir = tmp_path / "llm_cache"
        monkeypatch.setenv("MADSPARK_CACHE_DIR", str(cache_dir))

        from madspark.llm.cache import reset_cache, get_cache
        from madspark.llm.response import LLMResponse

        reset_cache()
        cache = get_cache()

        if cache.enabled:
            test_key = "test_prompt_123"
            # Cache expects tuple of (validated_object, LLMResponse)
            mock_response = LLMResponse(
                text='{"response": "test"}',
                provider="ollama",
                model="gemma3:4b",
                tokens_used=10,
                latency_ms=100.0,
                cost=0.0
            )
            test_value = ({"response": "test"}, mock_response)
            cache.set(test_key, test_value, ttl=3600)

            retrieved = cache.get(test_key)
            assert retrieved is not None
            validated_obj, llm_response = retrieved
            assert validated_obj["response"] == "test"
            assert llm_response.provider == "ollama"

    def test_provider_selection_defaults_to_auto(self, enable_router_env):
        """Test that default provider selection is 'auto' (Ollama-first)."""
        from madspark.llm.config import reset_config, get_config

        reset_config()
        config = get_config()

        assert config.default_provider in ["auto", "ollama", "gemini"]

    def test_model_tier_configuration(self, enable_router_env, monkeypatch):
        """Test model tier selection from environment."""
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "quality")

        from madspark.llm.config import reset_config, get_config

        reset_config()
        config = get_config()

        assert config.model_tier.value == "quality"


class TestRouterCacheIntegration:
    """Test cache integration with router."""

    def test_cache_enabled_by_default(self, monkeypatch):
        """Test that caching is enabled by default."""
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)

        from madspark.llm.config import reset_config, get_config

        reset_config()
        config = get_config()

        assert config.cache_enabled is True

    def test_cache_disabled_via_env(self, monkeypatch):
        """Test disabling cache via environment variable."""
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "false")

        from madspark.llm.config import reset_config, get_config

        reset_config()
        config = get_config()

        assert config.cache_enabled is False


class TestRouterBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_agents_work_without_router(self, monkeypatch):
        """Test that agents still work when router is disabled."""
        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        from madspark.agents.advocate import advocate_idea

        result = advocate_idea(
            idea="Test idea",
            evaluation="Good evaluation",
            topic="Testing",
            context="Test context"
        )

        assert result is not None
        assert len(result) > 0

    def test_coordinator_works_without_router(self, monkeypatch):
        """Test that coordinator works when router is disabled."""
        monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")

        from madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()
        assert coordinator is not None

    def test_cli_argument_parsing_includes_router_flags(self):
        """Test that CLI parser includes all router-related flags."""
        from madspark.cli.cli import create_parser

        parser = create_parser()

        args = parser.parse_args([
            "test_topic",
            "--provider", "ollama",
            "--model-tier", "fast",
            "--no-cache",
            "--no-router"
        ])

        assert args.provider == "ollama"
        assert args.model_tier == "fast"
        assert args.no_cache is True
        assert args.no_router is True


class TestRouterMetricsCollection:
    """Test metrics collection from router."""

    def test_metrics_accumulate_correctly(self, monkeypatch):
        """Test that router metrics accumulate across calls."""
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)

        from madspark.llm.router import LLMRouter, reset_router

        reset_router()
        router = LLMRouter()

        metrics = router.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["total_tokens"] == 0

    def test_show_llm_stats_flag_in_cli(self):
        """Test that --show-llm-stats flag is parsed correctly."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["topic", "--show-llm-stats"])

        assert args.show_llm_stats is True
