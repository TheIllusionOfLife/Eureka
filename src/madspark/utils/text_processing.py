"""Text processing utilities.

This module provides generic text processing functions used across the application.
"""

def truncate_text_intelligently(text: str, max_length: int = 300) -> str:
    """Truncate text at a sensible boundary (sentence or word).

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    # Find a good breaking point (end of sentence or word) within the limit
    truncation_candidate = text[:max_length]

    last_period = truncation_candidate.rfind('.')
    last_space = truncation_candidate.rfind(' ')

    # Prefer to break at sentence end if it's reasonably close to the end (last 50 chars)
    if last_period > max_length - 50 and last_period != -1:
        final_text = truncation_candidate[:last_period + 1]
    elif last_space > 0:
        # Break at space
        final_text = truncation_candidate[:last_space]
    else:
        # No good break point, just hard truncate
        final_text = truncation_candidate

    return f"{final_text}..."
