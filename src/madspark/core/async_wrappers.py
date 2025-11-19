"""Async wrappers for agent functions.

This module provides async execution capabilities for concurrent agent processing,
improving performance by running multiple agent calls in parallel.
"""

import asyncio
import atexit
import concurrent.futures
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

from ..utils.cache_manager import CacheManager
from ..config.execution_constants import ConcurrencyConfig
from ..utils.compat_imports import import_agent_retry_wrappers

logger = logging.getLogger(__name__)

_retry_wrappers = import_agent_retry_wrappers()
generate_ideas_with_retry = _retry_wrappers["generate_ideas_with_retry"]
evaluate_ideas_with_retry = _retry_wrappers["evaluate_ideas_with_retry"]
advocate_idea_with_retry = _retry_wrappers["advocate_idea_with_retry"]
criticize_idea_with_retry = _retry_wrappers["criticize_idea_with_retry"]
improve_idea_with_retry = _retry_wrappers["improve_idea_with_retry"]

# Create a shared thread pool executor for all async functions
# This avoids the overhead of creating/destroying executors repeatedly
_SHARED_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=ConcurrencyConfig.MAX_ASYNC_WORKERS)


# Ensure threads are cleaned up on interpreter exit
def _shutdown_shared_executor():
    _SHARED_EXECUTOR.shutdown(wait=False)


atexit.register(_shutdown_shared_executor)


async def async_generate_ideas(
    topic: str,
    context: str,
    temperature: float = 0.9,
    cache_manager: Optional[CacheManager] = None,
    use_structured_output: bool = True,
    router: Optional["LLMRouter"] = None,
) -> str:
    """Async wrapper for idea generation with retry logic.

    Runs the synchronous generate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.

    Args:
        topic: The main topic for idea generation
        context: Context or constraints for the ideas
        temperature: Controls randomness (0.0-1.0)
        cache_manager: Optional cache manager for result caching
        use_structured_output: Whether to use structured JSON output (default: True)
        router: Optional LLMRouter instance for request-scoped routing

    Returns:
        Generated ideas as JSON string (if structured) or newline-separated text
    """
    # Check cache first
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        cached = await cache_manager.get_cached_agent_response("idea_generator", prompt)
        if cached:
            logger.debug("Using cached idea generation response")
            return cached

    loop = asyncio.get_running_loop()
    # Use shared executor to avoid hanging issues in some environments
    result = await loop.run_in_executor(
        _SHARED_EXECUTOR,
        generate_ideas_with_retry,
        topic,
        context,
        temperature,
        use_structured_output,
        None,  # multimodal_files
        None,  # multimodal_urls
        router,  # router parameter
    )

    # Cache the result
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        await cache_manager.cache_agent_response("idea_generator", prompt, result)

    return result


async def async_evaluate_ideas(
    ideas: str,
    topic: str,
    context: str,
    temperature: float = 0.3,
    use_structured_output: bool = True,
    router: Optional["LLMRouter"] = None,
) -> str:
    """Async wrapper for idea evaluation with retry logic.

    Runs the synchronous evaluate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.

    Args:
        ideas: Ideas to evaluate
        topic: Main topic/theme
        context: Context/constraints
        temperature: Controls randomness (0.0-1.0)
        use_structured_output: Whether to use structured JSON output
        router: Optional LLMRouter instance for request-scoped routing

    Returns:
        Evaluation results as string
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        evaluate_ideas_with_retry,
        ideas,
        topic,
        context,
        temperature,
        use_structured_output,
        router,  # router parameter
    )


async def async_advocate_idea(
    idea: str,
    evaluation: str,
    topic: str,
    context: str,
    temperature: float = 0.5,
    use_structured_output: bool = True,
    router: Optional["LLMRouter"] = None,
) -> str:
    """Async wrapper for idea advocacy with retry logic.

    Runs the synchronous advocate_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.

    Args:
        idea: Idea to advocate for
        evaluation: Evaluation/critique of the idea
        topic: Main topic/theme
        context: Context/constraints
        temperature: Controls randomness (0.0-1.0)
        use_structured_output: Whether to use structured JSON output
        router: Optional LLMRouter instance for request-scoped routing

    Returns:
        Advocacy arguments as string
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        advocate_idea_with_retry,
        idea,
        evaluation,
        topic,
        context,
        temperature,
        use_structured_output,
        router,  # router parameter
    )


async def async_criticize_idea(
    idea: str,
    advocacy: str,
    topic: str,
    context: str,
    temperature: float = 0.5,
    use_structured_output: bool = True,
    router: Optional["LLMRouter"] = None,
) -> str:
    """Async wrapper for idea criticism/skepticism with retry logic.

    Runs the synchronous criticize_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.

    Args:
        idea: Idea to criticize
        advocacy: Advocacy arguments for the idea
        topic: Main topic/theme
        context: Context/constraints
        temperature: Controls randomness (0.0-1.0)
        use_structured_output: Whether to use structured JSON output
        router: Optional LLMRouter instance for request-scoped routing

    Returns:
        Critical analysis as string
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        criticize_idea_with_retry,
        idea,
        advocacy,
        topic,
        context,
        temperature,
        use_structured_output,
        router,  # router parameter
    )


async def async_improve_idea(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    topic: str,
    context: str,
    temperature: float = 0.9,
    router: Optional["LLMRouter"] = None,
) -> str:
    """Async wrapper for idea improvement with retry logic.

    Runs the synchronous improve_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.

    Args:
        original_idea: Original idea to improve
        critique: Critic's evaluation
        advocacy_points: Advocate's arguments
        skeptic_points: Skeptic's concerns
        topic: Main topic/theme
        context: Context/constraints
        temperature: Controls randomness (0.0-1.0)
        router: Optional LLMRouter instance for request-scoped routing

    Returns:
        Improved idea as string
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        improve_idea_with_retry,
        original_idea,
        critique,
        advocacy_points,
        skeptic_points,
        topic,
        context,
        temperature,
        router,  # router parameter
    )
