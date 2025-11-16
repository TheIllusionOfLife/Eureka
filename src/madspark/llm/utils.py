"""
Shared utility functions for LLM Router integration.

This module centralizes common router configuration logic used across agents.

Note on Import Pattern:
Each agent module has its own try/except block for importing router components
(get_router, AllProvidersFailedError, etc.). This is intentional:
- Standard Python pattern for optional dependencies
- Allows module-level availability detection (LLM_ROUTER_AVAILABLE)
- Each agent can independently handle missing router package

The configuration LOGIC (should_use_router) is centralized here to avoid
duplication of the env var detection code (~20 lines per agent).
"""
import os
import logging

logger = logging.getLogger(__name__)


def should_use_router(router_available: bool = False, get_router_func=None) -> bool:
    """
    Check if router should be used based on configuration.

    This function centralizes the router availability detection logic used
    by all agents (critic, advocate, skeptic, idea_generator).

    Args:
        router_available: Whether the LLM Router module is available
        get_router_func: The get_router function (None if unavailable)

    Returns:
        True if:
        - LLM Router is available and importable
        - User explicitly configured provider via env var (e.g., --provider flag)
        - Any router-related flag is set (cache, fallback, model tier)
    """
    if not router_available or get_router_func is None:
        return False

    # Check if user explicitly set provider (indicating they want router control)
    explicit_provider = os.getenv("MADSPARK_LLM_PROVIDER")

    # Also check for other router-related flags
    cache_disabled = os.getenv("MADSPARK_CACHE_ENABLED") == "false"
    fallback_disabled = os.getenv("MADSPARK_FALLBACK_ENABLED") == "false"
    model_tier_set = os.getenv("MADSPARK_MODEL_TIER") is not None

    # Use router if any router-related flag was explicitly set
    return bool(explicit_provider or cache_disabled or fallback_disabled or model_tier_set)
