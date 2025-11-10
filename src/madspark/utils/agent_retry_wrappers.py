"""Shared Agent Retry Wrappers

This module consolidates the retry logic for all agent functions that was previously
duplicated between coordinator.py and async_coordinator.py. This eliminates
code duplication and provides a single source of truth for agent retry behavior.
"""
from typing import List, Optional, Union
from pathlib import Path

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
        multimodal_urls: Optional[List[str]] = None
    ) -> str:
        """Generate ideas with retry logic.

        Args:
            topic: Main topic/theme for idea generation.
            context: Context/constraints for the ideas.
            temperature: Controls randomness (0.0-1.0).
            use_structured_output: Whether to use structured JSON output.
            multimodal_files: Optional list of file paths (images, PDFs, documents).
            multimodal_urls: Optional list of URLs for context.

        Returns:
            Generated ideas as string (JSON if use_structured_output=True).
        """
        return generate_ideas(
            topic=topic,
            context=context,
            temperature=temperature,
            use_structured_output=use_structured_output,
            multimodal_files=multimodal_files,
            multimodal_urls=multimodal_urls
        )

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.CRITIC_MAX_RETRIES,
        initial_delay=RetryConfig.CRITIC_INITIAL_DELAY
    )
    def critic(ideas: str, topic: str, context: str, temperature: float = 0.3, use_structured_output: bool = True) -> str:
        """Evaluate ideas with retry logic."""
        return evaluate_ideas(ideas=ideas, topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.ADVOCATE_MAX_RETRIES,
        initial_delay=RetryConfig.ADVOCATE_INITIAL_DELAY
    )
    def advocate(idea: str, evaluation: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
        """Advocate for an idea with retry logic."""
        return advocate_idea(idea=idea, evaluation=evaluation, topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.SKEPTIC_MAX_RETRIES,
        initial_delay=RetryConfig.SKEPTIC_INITIAL_DELAY
    )
    def skeptic(idea: str, advocacy: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
        """Provide skeptical analysis with retry logic."""
        return criticize_idea(idea=idea, advocacy=advocacy, topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)

    @staticmethod
    @exponential_backoff_retry(
        max_retries=RetryConfig.IMPROVEMENT_MAX_RETRIES,
        initial_delay=RetryConfig.IMPROVEMENT_INITIAL_DELAY
    )
    def improve_idea_agent(original_idea: str, critique: str, advocacy_points: str, skeptic_points: str, topic: str, context: str, temperature: float = 0.9) -> str:
        """Improve an idea based on feedback with retry logic."""
        # Note: improve_idea automatically handles structured output internally
        return improve_idea(
            original_idea=original_idea,
            critique=critique,
            advocacy_points=advocacy_points,
            skeptic_points=skeptic_points,
            topic=topic,
            context=context,
            temperature=temperature
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