"""Expose agent instances for easy import."""

from .idea_generator import idea_generator_agent
from .critic import critic_agent
from .advocate import advocate_agent
from .skeptic import skeptic_agent

__all__ = [
    "idea_generator_agent",
    "critic_agent",
    "advocate_agent",
    "skeptic_agent",
]
