"""
Phase 2 Tests: Backend Request-Scoped Router Migration.

Tests that backend endpoints create request-scoped router instances
instead of manipulating global state.
"""

import os
import pytest
from madspark.llm.router import LLMRouter


class TestRequestScopedRouter:
    """Test request-scoped router pattern."""

    def test_router_instances_are_independent(self):
        """Test that multiple router instances don't share state."""
        router1 = LLMRouter(primary_provider="ollama")
        router2 = LLMRouter(primary_provider="gemini")

        # Different configurations
        assert router1._primary_provider == "ollama"
        assert router2._primary_provider == "gemini"

        # Independent metrics
        router1._metrics["total_requests"] = 5
        router2._metrics["total_requests"] = 10

        assert router1._metrics["total_requests"] == 5
        assert router2._metrics["total_requests"] == 10

    def test_concurrent_router_creation(self):
        """Test creating multiple routers concurrently."""
        configs = [
            {"primary_provider": "ollama"},
            {"primary_provider": "gemini"},
            {"primary_provider": "auto"},
        ]

        routers = [LLMRouter(**config) for config in configs]

        assert len(routers) == 3
        assert routers[0]._primary_provider == "ollama"
        assert routers[1]._primary_provider == "gemini"
        assert routers[2]._primary_provider == "auto"


class TestAsyncCoordinatorRouterIntegration:
    """Test AsyncCoordinator accepts router parameter."""

    @pytest.mark.asyncio
    async def test_coordinator_accepts_router(self):
        """Test that AsyncCoordinator can accept optional router."""
        from madspark.core.async_coordinator import AsyncCoordinator

        router = LLMRouter(primary_provider="ollama")

        # Should accept router parameter without error
        coordinator = AsyncCoordinator(
            max_concurrent_agents=5,
            router=router,
        )

        assert coordinator.router is router
        assert coordinator.router._primary_provider == "ollama"

    @pytest.mark.asyncio
    async def test_coordinator_without_router_still_works(self):
        """Test backward compatibility - coordinator without router."""
        from madspark.core.async_coordinator import AsyncCoordinator

        # Should work without router (backward compatible)
        coordinator = AsyncCoordinator(max_concurrent_agents=5)

        # Router should be None (backward compat mode)
        assert coordinator.router is None


class TestAgentFunctionsAcceptRouter:
    """Test that agent functions accept optional router parameter."""

    def test_critic_accepts_router(self):
        """Test that evaluate_ideas accepts router parameter."""
        from madspark.agents.critic import evaluate_ideas
        import inspect

        _router = LLMRouter(primary_provider="ollama")

        # Test 1: Check function signature accepts router parameter
        sig = inspect.signature(evaluate_ideas)
        assert 'router' in sig.parameters, "evaluate_ideas should have 'router' parameter"

        # Test 2: Verify parameter is Optional (has default None)
        router_param = sig.parameters['router']
        assert router_param.default is None, "router parameter should default to None"

    def test_advocate_accepts_router(self):
        """Test that advocate_idea accepts router parameter."""
        from madspark.agents.advocate import advocate_idea
        import inspect

        _router = LLMRouter(primary_provider="gemini")

        # Check function signature accepts router parameter
        sig = inspect.signature(advocate_idea)
        assert 'router' in sig.parameters, "advocate_idea should have 'router' parameter"

        router_param = sig.parameters['router']
        assert router_param.default is None, "router parameter should default to None"

    def test_skeptic_accepts_router(self):
        """Test that criticize_idea accepts router parameter."""
        from madspark.agents.skeptic import criticize_idea
        import inspect

        _router = LLMRouter(primary_provider="ollama")

        # Check function signature accepts router parameter
        sig = inspect.signature(criticize_idea)
        assert 'router' in sig.parameters, "criticize_idea should have 'router' parameter"

        router_param = sig.parameters['router']
        assert router_param.default is None, "router parameter should default to None"

    def test_idea_generator_accepts_router(self):
        """Test that generate_ideas accepts router parameter."""
        from madspark.agents.idea_generator import generate_ideas
        import inspect

        _router = LLMRouter(primary_provider="ollama")

        # Check function signature accepts router parameter
        sig = inspect.signature(generate_ideas)
        assert 'router' in sig.parameters, "generate_ideas should have 'router' parameter"

        router_param = sig.parameters['router']
        assert router_param.default is None, "router parameter should default to None"

    def test_structured_idea_generator_accepts_router(self):
        """Test that improve_idea_structured accepts router parameter."""
        from madspark.agents.structured_idea_generator import improve_idea_structured
        import inspect

        _router = LLMRouter(primary_provider="gemini")

        # Check function signature accepts router parameter
        sig = inspect.signature(improve_idea_structured)
        assert 'router' in sig.parameters, "improve_idea_structured should have 'router' parameter"

        router_param = sig.parameters['router']
        assert router_param.default is None, "router parameter should default to None"


class TestNoEnvironmentManipulationInBackend:
    """Test that backend endpoints don't manipulate environment variables."""

    def test_router_creation_preserves_environment(self):
        """Test that creating routers doesn't modify os.environ."""
        original_provider = os.environ.get("MADSPARK_LLM_PROVIDER")
        original_tier = os.environ.get("MADSPARK_MODEL_TIER")

        # Create multiple routers with different configs
        _router1 = LLMRouter(primary_provider="ollama")
        _router2 = LLMRouter(primary_provider="gemini")

        # Environment should be unchanged
        assert os.environ.get("MADSPARK_LLM_PROVIDER") == original_provider
        assert os.environ.get("MADSPARK_MODEL_TIER") == original_tier

    @pytest.mark.asyncio
    async def test_coordinator_workflow_preserves_environment(self):
        """Test that running coordinator doesn't modify environment."""
        from madspark.core.async_coordinator import AsyncCoordinator

        original_env = dict(os.environ)

        router = LLMRouter(primary_provider="ollama")
        _coordinator = AsyncCoordinator(router=router)

        # Environment should remain unchanged after coordinator creation
        assert dict(os.environ) == original_env


class TestMetricsIsolation:
    """Test that router metrics are properly isolated per instance."""

    def test_metrics_isolated_between_instances(self):
        """Test that each router instance has independent metrics."""
        router1 = LLMRouter(primary_provider="ollama")
        router2 = LLMRouter(primary_provider="gemini")

        # Modify router1 metrics
        router1._metrics["total_requests"] = 100
        router1._metrics["cache_hits"] = 50
        router1._metrics["total_cost"] = 0.25

        # router2 metrics should be untouched
        assert router2._metrics["total_requests"] == 0
        assert router2._metrics["cache_hits"] == 0
        assert router2._metrics["total_cost"] == 0.0

    def test_metrics_aggregation(self):
        """Test that metrics can be aggregated from multiple router instances."""
        routers = [
            LLMRouter(primary_provider="ollama"),
            LLMRouter(primary_provider="gemini"),
            LLMRouter(primary_provider="auto"),
        ]

        # Simulate different usage
        for i, router in enumerate(routers):
            router._metrics["total_requests"] = (i + 1) * 10
            router._metrics["total_tokens"] = (i + 1) * 1000

        # Aggregate metrics
        total_requests = sum(r._metrics["total_requests"] for r in routers)
        total_tokens = sum(r._metrics["total_tokens"] for r in routers)

        assert total_requests == 60  # 10 + 20 + 30
        assert total_tokens == 6000  # 1000 + 2000 + 3000


class TestBackwardCompatibility:
    """Test that existing code patterns still work during migration."""

    def test_singleton_get_router_still_works(self):
        """Test that get_router() singleton still functions."""
        from madspark.llm.router import get_router

        router = get_router()
        assert router is not None

    @pytest.mark.asyncio
    async def test_coordinator_without_router_backwards_compat(self):
        """Test coordinator works without router (legacy mode)."""
        from madspark.core.async_coordinator import AsyncCoordinator

        # Old code that doesn't pass router should still work
        coordinator = AsyncCoordinator(max_concurrent_agents=3)

        assert hasattr(coordinator, 'router')
        # Router may be None (legacy mode) or auto-created
