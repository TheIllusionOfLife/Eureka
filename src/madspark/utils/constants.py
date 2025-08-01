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
DIMENSION_SCORES_KEY = "dimension_scores"  # Key for storing dimension scores in evaluation results
FEASIBILITY_KEY = "feasibility"
INNOVATION_KEY = "innovation"
IMPACT_KEY = "impact"
COST_EFFECTIVENESS_KEY = "cost_effectiveness"
SCALABILITY_KEY = "scalability"
RISK_ASSESSMENT_KEY = "risk_assessment"
TIMELINE_KEY = "timeline"

# Agent prompt constants
LANGUAGE_CONSISTENCY_INSTRUCTION = "Please respond in the same language as this prompt.\n\n"
IDEA_GENERATION_INSTRUCTION = "generate a list of diverse and creative ideas"
IDEA_GENERATOR_SYSTEM_INSTRUCTION = f"""You are an expert idea generator and improver. Given a topic and some context, {IDEA_GENERATION_INSTRUCTION}. 

CRITICAL OUTPUT REQUIREMENTS:
- Start directly with the content requested
- Do NOT include meta-commentary like "Here's the improved version", "Enhanced concept:", etc.
- Do NOT reference the original idea or improvement process
- Write as if this is the first and only version
- Be concise and direct
- Always respond in the same language as the input provided."""

# Agent system instructions
CRITIC_SYSTEM_INSTRUCTION = (
    "You are an expert critic. Evaluate the given ideas based on the"
    " provided criteria and context. Provide constructive feedback and"
    " identify potential weaknesses. Always respond in the same language"
    " as the input provided."
)

ADVOCATE_SYSTEM_INSTRUCTION = (
    "You are a persuasive advocate. Given an idea, its evaluation, and"
    " context, build a strong case for the idea. List key strengths and"
    " benefits as bullet points. Be direct and concise. Focus on specific"
    " advantages and opportunities. Always respond in the same language"
    " as the input provided."
)

SKEPTIC_SYSTEM_INSTRUCTION = (
    "You are a devil's advocate. Given an idea, the arguments for it, and"
    " context, critically analyze the idea. List specific concerns, risks,"
    " and flaws as bullet points. Be direct and critical. Focus on concrete"
    " problems and potential failures. Always respond in the same language"
    " as the input provided."
)

# Default model configuration
DEFAULT_GOOGLE_GENAI_MODEL = "gemini-2.5-flash"

# Temperature defaults for specific agents/functions
DEFAULT_CRITIC_TEMPERATURE = 0.3
DEBUG_DEFAULT_TEMPERATURE = 0.9

# Timeout constants
DEFAULT_REQUEST_TIMEOUT = 600  # 10 minutes in seconds
MIN_REQUEST_TIMEOUT = 60  # 1 minute minimum
MAX_REQUEST_TIMEOUT = 3600  # 1 hour maximum

# Idea cleaner constants - patterns for cleaning improved idea text
CLEANER_META_HEADERS = [
    'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
    'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
]

CLEANER_META_PHRASES = [
    'Addresses Evaluation Criteria', 'Enhancing Impact Through',
    'Preserving & Amplifying Strengths', 'Addressing Concerns',
    'Score:', 'from Score', 'Building on Score', '↑↑ from', '↑ from'
]

# Regex replacement patterns for idea cleaner (pattern, replacement tuples)
CLEANER_REPLACEMENT_PATTERNS = [
    # Remove AI response prefixes and meta-commentary
    (r'^[Hh]ere\'s the\s+(?:improved\s+)?version\s+(?:of\s+)?(?:your\s+)?(?:idea)?.*?[:.]?\s*', ''),
    (r'^[Hh]ere\'s an?\s+(?:improved|enhanced|better)\s+version.*?[:.]?\s*', ''),
    (r'^[Hh]ere\'s\s+your\s+(?:improved|enhanced)\s+idea\s+(?:with\s+)?(?:better\s+)?(?:focus\s*[:.]?\s*)?', ''),
    (r'^[Hh]ere\'s the\s+(?:refined|polished|optimized)\s+(?:version|idea).*?[:.]?\s*', ''),
    (r'^Based on.*?feedback.*?here\s+(?:is\s+)?(?:the\s+)?(?:refined\s+)?(?:concept\s*[:.]?\s*)?', ''),
    (r'^Taking into account.*?here\s+(?:is\s+)?(?:the\s+)?(?:refined\s+)?[:.]?\s*', ''),
    (r'^Incorporating.*?feedback.*?[:.]?\s*', ''),
    (r'^\s*\*\*Updated\s+(?:version|idea)\*\*[:.]?\s*', ''),
    (r'^\s*\*\*(?:Improved|Enhanced|Refined)\s+(?:concept|idea|version)\*\*[:.]?\s*', ''),
    
    # Remove mock-generated phrases and headers
    (r'^[Ii]mproved version of:\s*', ''),  # Remove "Improved version of:" at start
    (r'^[Ee]nhanced version of:\s*', ''),  # Remove "Enhanced version of:" at start  
    (r'^[Vv]ersion of:\s*', ''),  # Remove "version of:" at start
    (r'\n\nEnhancements based on feedback:\s*.*', ''),  # Remove enhancement lists
    (r'- Addressed critique points\s*\n?', ''),
    (r'- Incorporated advocacy strengths\s*\n?', ''),
    (r'- Resolved skeptical concerns\s*\n?', ''),
    
    # Remove improvement references
    (r'Our enhanced approach', 'This approach'),
    (r'The enhanced concept', 'The concept'),
    (r'This enhanced version', 'This version'),
    (r'The revised approach', 'The approach'),
    (r'enhanced ', ''),
    (r'improved ', ''),
    (r'revised ', ''),
    (r'Building upon the original.*?\.', ''),
    (r'Improving upon.*?\.', ''),
    (r'addresses the previous.*?\.', ''),
    (r'directly addresses.*?\.', ''),
    (r'The previous concern about.*?is', 'This'),
    
    # Simplify transition language
    (r'shifts from.*?to\s+', ''),
    (r'moves beyond.*?to\s+', ''),
    (r'transforms.*?into\s+', 'is '),
    (r'We shift from.*?to\s+', ''),
    (r'We\'re moving from.*?to\s+', 'It\'s '),
    (r'is evolving into\s+', 'is '),
    
    # Clean up headers
    (r'### \d+\.\s*', '## '),
    (r'## The "([^"]+)".*', r'# \1'),
    
    # Remove score references
    (r'\s*\(Score:?\s*\d+\.?\d*\)', ''),
    (r'\s*\(Addressing Score\s*\d+\.?\d*\)', ''),
    (r'Score\s*\d+\.?\d*\s*→\s*', ''),
    
    # Clean up separators
    (r'---+\n+', '\n'),
    (r'\n\n\n+', '\n\n'),
]

# Additional cleaner patterns for final cleanup
CLEANER_FRAMEWORK_CLEANUP_PATTERN = r'^[:\s]*(?:a\s+)?more\s+robust.*?system\s+'
CLEANER_TITLE_EXTRACTION_PATTERN = r'"([^"]+)"'
CLEANER_TITLE_REPLACEMENT_PATTERN = r'^.*?"[^"]+".*?\n+'
CLEANER_TITLE_KEYWORDS = ['Framework', 'System', 'Engine']

# Temperature Configuration Note:
# Temperature presets are defined in temperature_control.py as TemperatureConfig objects
# with different temperature values for each agent stage (idea_generation, evaluation, etc.)
# The web interface uses TemperatureManager.PRESETS from temperature_control.py
# Do NOT define simple temperature values here - the system uses complex configurations

# UX and Processing Constants
MEANINGFUL_IMPROVEMENT_SCORE_DELTA = 0.3  # Minimum score improvement to consider meaningful
MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD = 0.9  # Jaccard similarity threshold for duplicate detection
MIN_TIMEOUT_FOR_MULTIPLE_IDEAS_SECONDS = 300  # Minimum timeout when processing multiple ideas

# Batch Metrics Cost Analysis Constants
INDIVIDUAL_CALL_OVERHEAD_MULTIPLIER = 1.3  # Individual calls cost ~30% more due to overhead
ORIGINAL_CALLS_PER_ITEM = 7  # Estimated original API calls per item in non-batch system

# Timeout Constants
DEFAULT_TIMEOUT_SECONDS = 600  # Default timeout (10 minutes)
MAX_TIMEOUT_SECONDS = 3600  # Maximum timeout (1 hour)
MIN_TIMEOUT_SECONDS = 60  # Minimum timeout (1 minute)

# API and Scoring Constants
DEFAULT_NOVELTY_THRESHOLD = 0.8  # Default similarity threshold for novelty filtering
PERCENTAGE_CONVERSION_FACTOR = 100  # For converting to percentage
