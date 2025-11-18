"""Shared Agent Retry Wrappers

This module consolidates the retry logic for all agent functions that was previously
duplicated between coordinator.py and async_coordinator.py. This eliminates
code duplication and provides a single source of truth for agent retry behavior.
"""
from typing import List, Optional, Union, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

from ..config.execution_constants import RetryConfig
from .utils import exponential_backoff_retry
from ..agents.idea_generator import generate_ideas, improve_idea
from ..agents.critic import evaluate_ideas
from ..agents.advocate import advocate_idea
from ..agents.skeptic import criticize_idea


class AgentRetryWrapper:
    """Centralized retry wrappers for all agent functions.

    This class provides retry-enabled versions of all agent functions
    with retry configuration from RetryConfig.
    """

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.IDEA_GENERATOR_MAX_RETRIES,
        initial_delay=RetryConfig.IDEA_GENERATOR_INITIAL_DELAY
    )
    def idea_generator(
        topic: str,
        context: str,
        temperature: float = 0.9,
        use_structured_output: bool = True,
        multimodal_files: Optional[List[Union[str, Path]]] = None,
        multimodal_urls: Optional[List[str]] = None,
        router: Optional["LLMRouter"] = None
    ) -> str:
        """Generate ideas with retry logic.

        Args:
            topic: Main topic/theme for idea generation.
            context: Context/constraints for the ideas.
            temperature: Controls randomness (0.0-1.0).
            use_structured_output: Whether to use structured JSON output.
            multimodal_files: Optional list of file paths (images, PDFs, documents).
            multimodal_urls: Optional list of URLs for context.
            router: Optional LLMRouter instance for request-scoped routing.

        Returns:
            Generated ideas as string (JSON if use_structured_output=True).
        """
        return generate_ideas(
            topic=topic,
            context=context,
            temperature=temperature,
            use_structured_output=use_structured_output,
            multimodal_files=multimodal_files,
            multimodal_urls=multimodal_urls,
            router=router
        )

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.CRITIC_MAX_RETRIES,
        initial_delay=RetryConfig.CRITIC_INITIAL_DELAY
    )
    def critic(
        ideas: str,
        topic: str,
        context: str,
        temperature: float = 0.3,
        use_structured_output: bool = True,
        router: Optional["LLMRouter"] = None
    ) -> str:
        """Evaluate ideas with retry logic.

        Args:
            ideas: Ideas to evaluate.
            topic: Main topic/theme.
            context: Context/constraints.
            temperature: Controls randomness (0.0-1.0).
            use_structured_output: Whether to use structured JSON output.
            router: Optional LLMRouter instance for request-scoped routing.

        Returns:
            Evaluation results as string.
        """
        return evaluate_ideas(
            ideas=ideas,
            topic=topic,
            context=context,
            temperature=temperature,
            use_structured_output=use_structured_output,
            router=router
        )

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.ADVOCATE_MAX_RETRIES,
        initial_delay=RetryConfig.ADVOCATE_INITIAL_DELAY
    )
    def advocate(
        idea: str,
        evaluation: str,
        topic: str,
        context: str,
        temperature: float = 0.5,
        use_structured_output: bool = True,
        router: Optional["LLMRouter"] = None
    ) -> str:
        """Advocate for an idea with retry logic.

        Args:
            idea: Idea to advocate for.
            evaluation: Evaluation/critique of the idea.
            topic: Main topic/theme.
            context: Context/constraints.
            temperature: Controls randomness (0.0-1.0).
            use_structured_output: Whether to use structured JSON output.
            router: Optional LLMRouter instance for request-scoped routing.

        Returns:
            Advocacy arguments as string.
        """
        return advocate_idea(
            idea=idea,
            evaluation=evaluation,
            topic=topic,
            context=context,
            temperature=temperature,
            use_structured_output=use_structured_output,
            router=router
        )

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.SKEPTIC_MAX_RETRIES,
        initial_delay=RetryConfig.SKEPTIC_INITIAL_DELAY
    )
    def skeptic(
        idea: str,
        advocacy: str,
        topic: str,
        context: str,
        temperature: float = 0.5,
        use_structured_output: bool = True,
        router: Optional["LLMRouter"] = None
    ) -> str:
        """Provide skeptical analysis with retry logic.

        Args:
            idea: Idea to criticize.
            advocacy: Advocacy arguments for the idea.
            topic: Main topic/theme.
            context: Context/constraints.
            temperature: Controls randomness (0.0-1.0).
            use_structured_output: Whether to use structured JSON output.
            router: Optional LLMRouter instance for request-scoped routing.

        Returns:
            Critical analysis as string.
        """
        return criticize_idea(
            idea=idea,
            advocacy=advocacy,
            topic=topic,
            context=context,
            temperature=temperature,
            use_structured_output=use_structured_output,
            router=router
        )

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.IMPROVEMENT_MAX_RETRIES,
        initial_delay=RetryConfig.IMPROVEMENT_INITIAL_DELAY
    )
    def improve_idea_agent(
        original_idea: str,
        critique: str,
        advocacy_points: str,
        skeptic_points: str,
        topic: str,
        context: str,
        temperature: float = 0.9,
        router: Optional["LLMRouter"] = None
    ) -> str:
        """Improve an idea based on feedback with retry logic.

        Args:
            original_idea: Original idea to improve.
            critique: Critic's evaluation.
            advocacy_points: Advocate's arguments.
            skeptic_points: Skeptic's concerns.
            topic: Main topic/theme.
            context: Context/constraints.
            temperature: Controls randomness (0.0-1.0).
            router: Optional LLMRouter instance for request-scoped routing.

        Returns:
            Improved idea as string.
        """
        # Note: improve_idea automatically handles structured output internally
        return improve_idea(
            original_idea=original_idea,
            critique=critique,
            advocacy_points=advocacy_points,
            skeptic_points=skeptic_points,
            topic=topic,
            context=context,
            temperature=temperature,
            router=router
        )


# Convenience aliases for backward compatibility
call_idea_generator_with_retry = AgentRetryWrapper.idea_generator
call_critic_with_retry = AgentRetryWrapper.critic
call_advocate_with_retry = AgentRetryWrapper.advocate
call_skeptic_with_retry = AgentRetryWrapper.skeptic
call_improve_idea_with_retry = AgentRetryWrapper.improve_idea_agent

# Async coordinator aliases (different naming convention)
generate_ideas_with_retry = AgentRetryWrapper.idea_generator
evaluate_ideas_with_retry = AgentRetryWrapper.critic
advocate_idea_with_retry = AgentRetryWrapper.advocate
criticize_idea_with_retry = AgentRetryWrapper.skeptic
improve_idea_with_retry = AgentRetryWrapper.improve_idea_agent