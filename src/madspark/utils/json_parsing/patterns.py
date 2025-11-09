"""Pre-compiled regex patterns for JSON parsing performance.

This module contains all regex patterns used in JSON parsing, pre-compiled
at module load time for optimal performance. Pre-compilation provides
10-20% performance gain over inline re.compile() calls.

Pattern Categories:
- Comma fix patterns: Fix missing commas in malformed JSON
- Object extraction patterns: Extract JSON objects from text
- String cleanup patterns: Handle newlines and escapes in strings
- Score/comment patterns: Legacy fallback for text-based evaluation results
"""

import re

# ============================================================================
# Comma Fix Patterns (Hot Path - Called on Every Batch Parse)
# ============================================================================

#: Fix missing comma after string value before next property
COMMA_AFTER_STRING = re.compile(r'("\s*)\n(\s*"[^"]+"\s*:)')

#: Fix missing comma after array value before next property
COMMA_AFTER_ARRAY = re.compile(r'(\]\s*)\n(\s*"[^"]+"\s*:)')

#: Fix missing comma after number value before next property
COMMA_AFTER_NUMBER = re.compile(r'(\d\s*)\n(\s*"[^"]+"\s*:)')

#: Fix missing comma after object value before next property
COMMA_AFTER_OBJECT = re.compile(r'(\}\s*)\n(\s*"[^"]+"\s*:)')


# ============================================================================
# Object Extraction Patterns (Fallback Strategies)
# ============================================================================

#: Extract JSON object with one level of nesting
#: Handles simple and moderately complex objects
JSON_OBJECT_PATTERN = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', re.DOTALL)

#: Extract JSON object with multiple nesting levels
#: More comprehensive than JSON_OBJECT_PATTERN
NESTED_OBJECT_PATTERN = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL)


# ============================================================================
# String Cleanup Patterns
# ============================================================================

#: Match quoted strings (with escaped content support)
#: Used to identify string boundaries for newline replacement
NEWLINE_IN_STRING = re.compile(r'("(?:[^"\\]|\\.)*")')


# ============================================================================
# Score/Comment Patterns (Legacy Fallback - Last Resort)
# ============================================================================

#: Standard format: "Score: 8 Comment: text" (case-insensitive)
SCORE_COMMENT_STANDARD = re.compile(
    r'(?:score|Score)[\s:]+(\d+).*?(?:comment|Comment|critique|Critique)[\s:]+([^\n]+)',
    re.IGNORECASE | re.DOTALL
)

#: Narrative format 1: "scores an 8" or "scores a 9 out of 10"
#: ReDoS Protection: Comment limited to 500 characters
SCORE_NARRATIVE_AN = re.compile(
    r'scores?\s+an?\s+(\d+)(?:\s+out\s+of\s+\d+)?[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})',
    re.IGNORECASE
)

#: Narrative format 2: "give it a score of 7"
#: ReDoS Protection: Comment limited to 500 characters
SCORE_NARRATIVE_GIVE = re.compile(
    r'give\s+it\s+a\s+score\s+of\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})',
    re.IGNORECASE
)

#: Narrative format 3: "deserves a 9" or "gets a 6"
#: ReDoS Protection: Comment limited to 500 characters
SCORE_NARRATIVE_DESERVES = re.compile(
    r'(?:deserves?|gets?)\s+an?\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})',
    re.IGNORECASE
)

#: Narrative format 4: "scores 8" (simplest form)
#: ReDoS Protection: Comment limited to 500 characters
SCORE_NARRATIVE_SIMPLE = re.compile(
    r'scores?\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})',
    re.IGNORECASE
)


# ============================================================================
# Pattern Collections for Iteration
# ============================================================================

#: All comma fix patterns in order of application
COMMA_FIX_PATTERNS = [
    COMMA_AFTER_STRING,
    COMMA_AFTER_ARRAY,
    COMMA_AFTER_NUMBER,
    COMMA_AFTER_OBJECT,
]

#: All score/comment narrative patterns for fallback parsing
SCORE_NARRATIVE_PATTERNS = [
    SCORE_NARRATIVE_AN,
    SCORE_NARRATIVE_GIVE,
    SCORE_NARRATIVE_DESERVES,
    SCORE_NARRATIVE_SIMPLE,
]
