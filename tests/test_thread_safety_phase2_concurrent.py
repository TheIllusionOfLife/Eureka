"""Phase 2 Concurrent Request Tests - Thread Safety Verification

Tests that multiple concurrent requests with different configurations
maintain independent router state without contamination.

Key Goal: Verify request-scoped routers prevent configuration contamination,
not object identity (router instances may be cached/pooled internally).
"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import patch

from madspark.llm.router import LLMRouter
from madspark.core.async_coordinator import AsyncCoordinator


@pytest.mark.asyncio
async def test_concurrent_requests_config_isolation():
    """Test 25+ concurrent requests maintain independent configuration.

    Verifies that each request's router configuration is isolated from
    other concurrent requests, preventing race conditions and contamination.
    """
    test_configs = []
    for i in range(25):
        test_configs.append({
            "primary_provider": ["ollama", "gemini", "auto"][i % 3],
            "fallback_enabled": i % 2 == 0,
            "cache_enabled": i % 3 != 0,
        })

    async def run_request(config: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        """Simulate a request with specific configuration."""
        router = LLMRouter(
            primary_provider=config["primary_provider"],
            fallback_enabled=config["fallback_enabled"],
            cache_enabled=config["cache_enabled"]
        )

        # Small delay to increase chance of race conditions if they exist
        await asyncio.sleep(0.001 * (request_id % 5))

        # Read configuration immediately after creation
        result = {
            "request_id": request_id,
            "provider": router._primary_provider,
            "fallback": router._fallback_enabled,
            "cache": router._cache_enabled,
        }

        # Small delay before returning to test persistence
        await asyncio.sleep(0.001)

        return result

    # Run all requests concurrently
    tasks = [run_request(config, i) for i, config in enumerate(test_configs)]
    results = await asyncio.gather(*tasks)

    # Verify ZERO configuration contamination
    for i, result in enumerate(results):
        expected = test_configs[i]

        assert result["provider"] == expected["primary_provider"], \
            f"Request {i}: Provider mismatch - got {result['provider']}, expected {expected['primary_provider']}"
        assert result["fallback"] == expected["fallback_enabled"], \
            f"Request {i}: Fallback mismatch - got {result['fallback']}, expected {expected['fallback_enabled']}"
        assert result["cache"] == expected["cache_enabled"], \
            f"Request {i}: Cache mismatch - got {result['cache']}, expected {expected['cache_enabled']}"


@pytest.mark.asyncio
async def test_concurrent_coordinators_with_routers():
    """Test that multiple AsyncCoordinators with different routers work concurrently.

    This simulates real backend usage: multiple concurrent HTTP requests
    each creating their own router + coordinator.
    """
    with patch('madspark.agents.idea_generator.generate_ideas') as mock_generate, \
         patch('madspark.agents.critic.evaluate_ideas') as mock_evaluate:

        mock_generate.return_value = '{"ideas": [{"title": "Test", "description": "Test"}]}'
        mock_evaluate.return_value = '{"evaluations": [{"score": 8.5}]}'

        async def simulate_backend_request(
            provider: str,
            request_id: int
        ) -> Dict[str, Any]:
            """Simulate a single backend request."""
            # Create request-scoped router (like backend does)
            router = LLMRouter(primary_provider=provider)

            # Create request-scoped coordinator (like backend does)
            coordinator = AsyncCoordinator(
                max_concurrent_agents=2,
                router=router
            )

            # Simulate some processing
            await asyncio.sleep(0.002)

            return {
                "request_id": request_id,
                "provider": router._primary_provider,
                "coordinator_id": id(coordinator),
            }

        # Simulate 24 concurrent backend requests with mixed configs
        providers = ["ollama", "gemini", "auto"] * 8

        tasks = [
            simulate_backend_request(providers[i], i)
            for i in range(24)
        ]
        results = await asyncio.gather(*tasks)

        # Verify all coordinators are unique instances
        coordinator_ids = [r["coordinator_id"] for r in results]
        assert len(set(coordinator_ids)) == 24, \
            "Each request should have unique coordinator instance"

        # Verify configurations match expectations (no contamination)
        for i, result in enumerate(results):
            assert result["provider"] == providers[i], \
                f"Request {i}: Provider mismatch - got {result['provider']}, expected {providers[i]}"


def test_router_config_independence():
    """Test that router instances maintain independent configuration.

    This is a synchronous sanity check that creating multiple routers
    with different configs doesn't cause shared state issues.
    """
    routers = []
    configs = []

    for i in range(30):
        config = {
            "provider": ["ollama", "gemini", "auto"][i % 3],
            "cache": i % 2 == 0,
            "fallback": i % 3 == 0,
        }
        configs.append(config)

        router = LLMRouter(
            primary_provider=config["provider"],
            cache_enabled=config["cache"],
            fallback_enabled=config["fallback"]
        )
        routers.append(router)

    # Verify all configurations are preserved correctly
    for i, router in enumerate(routers):
        expected = configs[i]

        assert router._primary_provider == expected["provider"], \
            f"Router {i}: Provider mismatch"
        assert router._cache_enabled == expected["cache"], \
            f"Router {i}: Cache mismatch"
        assert router._fallback_enabled == expected["fallback"], \
            f"Router {i}: Fallback mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
