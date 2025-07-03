"""Mad Spark Multi-Agent Definitions.

This package exports the core agent functions used in the multi-agent workflow.
Each function is specialized for a specific task in the idea generation and
refinement process.
"""
from .idea_generator import generate_ideas
from .critic import evaluate_ideas
from .advocate import advocate_idea
from .skeptic import criticize_idea
