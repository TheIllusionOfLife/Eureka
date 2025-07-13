"""Constants used throughout the MadSpark multi-agent system.

This module contains shared constants to avoid magic strings and improve
maintainability across the codebase.
"""

# Empty response placeholders for agents
ADVOCATE_EMPTY_RESPONSE = "Advocate agent returned no content."
SKEPTIC_EMPTY_RESPONSE = "Skeptic agent returned no content."

# Bookmark system constants
HIGH_SCORE_THRESHOLD = 7  # Score threshold for highlighting high-rated ideas
MAX_REMIX_BOOKMARKS = 10  # Maximum number of bookmarks to use for remix context

# Temperature defaults
DEFAULT_IDEA_TEMPERATURE = 0.9
DEFAULT_EVALUATION_TEMPERATURE = 0.3
DEFAULT_ADVOCACY_TEMPERATURE = 0.5
DEFAULT_SKEPTICISM_TEMPERATURE = 0.5

# Workflow defaults
DEFAULT_NUM_TOP_CANDIDATES = 3  # Default to 3 top ideas for richer results
DEFAULT_NOVELTY_THRESHOLD = 0.8

# Enhanced reasoning constants
LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for logical inference conclusions

# Multi-dimensional evaluation constants
DIMENSION_SCORES_KEY = "dimension_scores"
FEASIBILITY_KEY = "feasibility"
INNOVATION_KEY = "innovation"
IMPACT_KEY = "impact"
COST_EFFECTIVENESS_KEY = "cost_effectiveness"
SCALABILITY_KEY = "scalability"
RISK_ASSESSMENT_KEY = "risk_assessment"
TIMELINE_KEY = "timeline"

# Agent prompt constants
IDEA_GENERATION_INSTRUCTION = "generate a list of diverse and creative ideas"
IDEA_GENERATOR_SYSTEM_INSTRUCTION = f"You are an expert idea generator. Given a topic and some context, {IDEA_GENERATION_INSTRUCTION}."