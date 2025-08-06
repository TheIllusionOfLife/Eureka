"""Shared Agent Retry Wrappers

This module consolidates the retry logic for all agent functions that was previously
duplicated between coordinator.py and async_coordinator.py. This eliminates
code duplication and provides a single source of truth for agent retry behavior.
"""

from .utils import exponential_backoff_retry
from ..agents.idea_generator import generate_ideas, improve_idea
from ..agents.critic import evaluate_ideas
from ..agents.advocate import advocate_idea
from ..agents.skeptic import criticize_idea


class AgentRetryWrapper:
    """Centralized retry wrappers for all agent functions.
    
    This class provides retry-enabled versions of all agent functions
    with consistent retry configuration (max_retries=3, initial_delay=2.0).
    """
    
    @staticmethod
    @exponential_backoff_retry(max_retries=3, initial_delay=2.0)
    def idea_generator(topic: str, context: str, temperature: float = 0.9, use_structured_output: bool = True) -> str:
        """Generate ideas with retry logic."""
        return generate_ideas(topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)
    
    @staticmethod
    @exponential_backoff_retry(max_retries=3, initial_delay=2.0)
    def critic(ideas: str, criteria: str, context: str, temperature: float = 0.3, use_structured_output: bool = True) -> str:
        """Evaluate ideas with retry logic."""
        return evaluate_ideas(ideas=ideas, criteria=criteria, context=context, temperature=temperature, use_structured_output=use_structured_output)
    
    @staticmethod
    @exponential_backoff_retry(max_retries=2, initial_delay=1.0)
    def advocate(idea: str, evaluation: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
        """Advocate for an idea with retry logic."""
        return advocate_idea(idea=idea, evaluation=evaluation, topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)
    
    @staticmethod
    @exponential_backoff_retry(max_retries=2, initial_delay=1.0)
    def skeptic(idea: str, advocacy: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
        """Provide skeptical analysis with retry logic."""
        return criticize_idea(idea=idea, advocacy=advocacy, topic=topic, context=context, temperature=temperature, use_structured_output=use_structured_output)
    
    @staticmethod
    @exponential_backoff_retry(max_retries=3, initial_delay=2.0)
    def improve_idea_agent(original_idea: str, critique: str, advocacy_points: str, skeptic_points: str, context: str, temperature: float = 0.9) -> str:
        """Improve an idea based on feedback with retry logic."""
        # Note: improve_idea automatically handles structured output internally
        return improve_idea(
            original_idea=original_idea,
            critique=critique,
            advocacy_points=advocacy_points,
            skeptic_points=skeptic_points,
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