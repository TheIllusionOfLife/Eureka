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

# Agent system instructions
CRITIC_SYSTEM_INSTRUCTION = (
    "You are an expert critic. Evaluate the given ideas based on the"
    " provided criteria and context. Provide constructive feedback and"
    " identify potential weaknesses."
)

ADVOCATE_SYSTEM_INSTRUCTION = (
    "You are a persuasive advocate. Given an idea, its evaluation, and"
    " context, build a strong case for the idea. List key strengths and"
    " benefits as bullet points. Be direct and concise. Focus on specific"
    " advantages and opportunities."
)

SKEPTIC_SYSTEM_INSTRUCTION = (
    "You are a devil's advocate. Given an idea, the arguments for it, and"
    " context, critically analyze the idea. List specific concerns, risks,"
    " and flaws as bullet points. Be direct and critical. Focus on concrete"
    " problems and potential failures."
)

# Default model configuration
DEFAULT_GOOGLE_GENAI_MODEL = "gemini-2.5-flash"

# Temperature defaults for specific agents/functions
DEFAULT_CRITIC_TEMPERATURE = 0.3
DEBUG_DEFAULT_TEMPERATURE = 0.9