"""Mad Spark Multi-Agent Definitions.

This package exports the core agent functions used in the multi-agent workflow.
Each function is specialized for a specific task in the idea generation and
refinement process.
"""

# Try to import agent functions with graceful fallback
try:
    from .idea_generator import generate_ideas, improve_idea
    from .critic import evaluate_ideas
    from .advocate import advocate_idea
    from .skeptic import criticize_idea
except ImportError as e:
    # Fallback for local development when dependencies aren't available
    import logging
    logging.warning(f"Could not import agents: {e}")
    generate_ideas = None
    improve_idea = None
    evaluate_ideas = None
    advocate_idea = None
    criticize_idea = None
