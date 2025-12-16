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


def batch_generate_with_router(
    router,
    prompt: str,
    schema,
    system_instruction: str,
    temperature: float,
    batch_type: str,
    item_count: int,
):
    """
    Execute batch generation through LLM router with standard error handling.

    This helper centralizes the common pattern used by batch operations across
    agents (advocate, skeptic, idea_generator) for router-based generation.

    Only catches expected, recoverable failures and returns (None, 0) for fallback.
    Programming errors (AttributeError, TypeError, etc.) are re-raised to aid debugging.

    Args:
        router: LLMRouter instance for request-scoped routing
        prompt: The prompt to send to the LLM
        schema: Pydantic model class for response validation
        system_instruction: System instruction for the LLM
        temperature: Generation temperature
        batch_type: Type identifier for logging (e.g., "advocacy", "skepticism")
        item_count: Number of items being processed (for logging)

    Returns:
        Tuple of (validated_response, tokens_used) on success.
        Returns (None, 0) only for expected, recoverable failures.

    Raises:
        AttributeError, TypeError, KeyError: Programming errors (re-raised)
    """
    import json
    from pydantic import ValidationError

    # Import expected router exceptions
    try:
        from madspark.llm.exceptions import (
            AllProvidersFailedError,
            SchemaValidationError,
            ProviderUnavailableError,
        )
        router_exceptions = (AllProvidersFailedError, SchemaValidationError, ProviderUnavailableError)
    except ImportError:
        router_exceptions = ()

    # Expected recoverable exceptions
    recoverable_exceptions = (
        *router_exceptions,
        ValidationError,
        json.JSONDecodeError,
        OSError,
        ConnectionError,
        TimeoutError,
    )

    try:
        logger.info(f"Using LLM router for batch {batch_type} of {item_count} ideas")

        validated, response = router.generate_structured(
            prompt=prompt,
            schema=schema,
            system_instruction=system_instruction,
            temperature=temperature,
        )

        logger.info(f"Router batch {batch_type} completed: {len(validated.root)} items, {response.tokens_used} tokens")
        return validated, response.tokens_used

    except recoverable_exceptions as e:
        logger.warning(f"Router failed for batch {batch_type}, falling back to direct API: {type(e).__name__}: {e}")
        return None, 0
