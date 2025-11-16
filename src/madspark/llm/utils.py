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

    The router is used BY DEFAULT when available (Ollama-first behavior).
    Use MADSPARK_NO_ROUTER=true to bypass the router.

    Args:
        router_available: Whether the LLM Router module is available
        get_router_func: The get_router function (None if unavailable)

    Returns:
        True if:
        - LLM Router is available and importable
        - MADSPARK_NO_ROUTER is not set to "true"
        False if:
        - Router not available
        - MADSPARK_NO_ROUTER is set to "true" (--no-router flag)
    """
    if not router_available or get_router_func is None:
        return False

    # Check if user explicitly disabled router via --no-router flag
    no_router = os.getenv("MADSPARK_NO_ROUTER", "").lower() in ("true", "1", "yes")
    if no_router:
        logger.info("Router disabled via MADSPARK_NO_ROUTER environment variable")
        return False

    # Router is enabled by default when available (Ollama-first behavior)
    logger.debug("Router enabled by default (Ollama-first behavior)")
    return True
