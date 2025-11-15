"""
Agent Adapter for LLM Router.

Provides a seamless interface for agents to use LLMRouter
while maintaining backward compatibility with direct GenAI calls.
"""

import logging
from typing import Any, Optional, Type
from pathlib import Path
from pydantic import BaseModel

from madspark.llm.router import get_router
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import AllProvidersFailedError

logger = logging.getLogger(__name__)


def generate_structured_via_router(
    prompt: str,
    schema: Type[BaseModel],
    system_instruction: str = "",
    temperature: float = 0.7,
    images: Optional[list] = None,
    files: Optional[list[Path]] = None,
    urls: Optional[list[str]] = None,
    force_provider: Optional[str] = None,
) -> tuple[Any, int]:
    """
    Generate structured output through LLM router.

    This function provides a simple interface for agents to use the router
    without needing to manage provider selection, caching, or fallback logic.

    Args:
        prompt: User prompt text
        schema: Pydantic model for validation
        system_instruction: System instruction for the model
        temperature: Sampling temperature
        images: Optional image paths for multimodal input
        files: Optional file paths (PDF, documents)
        urls: Optional URLs for context
        force_provider: Force specific provider (None = auto)

    Returns:
        tuple: (validated_response_text, token_count)
               Returns JSON string of validated object and token count

    Raises:
        AllProvidersFailedError: If all providers fail
    """
    router = get_router()

    try:
        validated, response = router.generate_structured(
            prompt=prompt,
            schema=schema,
            system_instruction=system_instruction,
            temperature=temperature,
            images=images,
            files=files,
            urls=urls,
            force_provider=force_provider,
        )

        # Convert validated Pydantic object back to JSON string
        # (agents expect JSON string for parsing)
        if hasattr(validated, "model_dump_json"):
            response_text = validated.model_dump_json()
        else:
            import json
            response_text = json.dumps(validated)

        return response_text, response.tokens_used

    except AllProvidersFailedError as e:
        logger.error(f"All LLM providers failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Router generation failed: {e}")
        raise


def check_router_health() -> dict:
    """
    Check health status of LLM providers via router.

    Returns:
        Dictionary with provider health information
    """
    try:
        router = get_router()
        return router.health_status()
    except Exception as e:
        logger.warning(f"Router health check failed: {e}")
        return {"error": str(e)}


def get_router_metrics() -> dict:
    """
    Get usage metrics from router.

    Returns:
        Dictionary with usage statistics
    """
    try:
        router = get_router()
        return router.get_metrics()
    except Exception as e:
        logger.warning(f"Failed to get router metrics: {e}")
        return {"error": str(e)}


def is_router_available() -> bool:
    """
    Check if LLM router is available and has at least one healthy provider.

    Returns:
        True if at least one provider is available
    """
    try:
        router = get_router()
        health = router.health_status()

        ollama_healthy = health.get("ollama", {}).get("healthy", False)
        gemini_available = health.get("gemini", {}).get("available", False)

        return ollama_healthy or gemini_available
    except Exception as e:
        logger.warning(f"Router availability check failed: {e}")
        return False
