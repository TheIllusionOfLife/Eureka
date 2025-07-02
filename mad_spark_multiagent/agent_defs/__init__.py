"""Mad Spark Multi-Agent Definitions.

This package exports the core agent instances used in the multi-agent workflow.
Each agent is specialized for a specific task in the idea generation and
refinement process.
"""
from .idea_generator import idea_generator_agent
from .critic import critic_agent
from .advocate import advocate_agent
from .skeptic import skeptic_agent
