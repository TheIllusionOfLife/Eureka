"""Utility functions for the Mad Spark Multi-Agent system.

This module provides common utilities like retry logic and robust JSON parsing
to improve the reliability of the multi-agent workflow.
"""
import re
import json
import time
import logging
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps

T = TypeVar('T')


def exponential_backoff_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that implements exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Factor to multiply delay by after each retry
        max_delay: Maximum delay between retries in seconds
        retryable_exceptions: Tuple of exceptions that should trigger a retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.1f} seconds..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logging.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
            
            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            else:
                # This should never happen, but just in case
                raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")
                
        return wrapper
    return decorator


def parse_batch_json_with_fallback(text: str, expected_count: int = None) -> List[Dict[str, Any]]:
    """Parse batch JSON responses with fallback strategies for problematic JSON.
    
    Specifically designed for batch responses from advocate, skeptic, and idea improvement.
    Handles missing commas, especially in Japanese content.
    
    Args:
        text: Raw text response that should contain JSON
        expected_count: Expected number of items (for validation)
        
    Returns:
        List of parsed dictionaries
    """
    results = []
    
    # Strategy 1: Try normal JSON parsing first
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Fix missing commas between array elements
    # Common issue: missing comma after closing quote or bracket
    fixed_text = text
    
    # Fix missing comma after string values (before next key)
    # e.g., "key": "value"\n    "nextkey": -> "key": "value",\n    "nextkey":
    fixed_text = re.sub(r'("\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_text)
    
    # Fix missing comma after arrays
    # e.g., ["item1", "item2"]\n    "nextkey": -> ["item1", "item2"],\n    "nextkey":
    fixed_text = re.sub(r'(\]\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_text)
    
    # Fix missing comma after numbers
    # e.g., "key": 123\n    "nextkey": -> "key": 123,\n    "nextkey":
    fixed_text = re.sub(r'(\d\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_text)
    
    # Fix missing comma after objects
    # e.g., {...}\n    "nextkey": -> {...},\n    "nextkey":
    fixed_text = re.sub(r'(\}\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_text)
    
    # Try parsing the fixed text
    try:
        obj = json.loads(fixed_text)
        if isinstance(obj, list):
            logging.info("Successfully parsed JSON after fixing missing commas")
            return obj
    except json.JSONDecodeError as e:
        logging.debug(f"Still failed after comma fixes: {e}")
    
    # Strategy 3: Extract individual JSON objects using regex
    # Look for patterns like {...} within the array
    object_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL)
    
    for match in object_pattern.findall(text):
        try:
            # Fix missing commas within this object too
            fixed_obj = match
            fixed_obj = re.sub(r'("\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_obj)
            fixed_obj = re.sub(r'(\]\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_obj)
            fixed_obj = re.sub(r'(\d\s*)\n(\s*"[^"]+"\s*:)', r'\1,\n\2', fixed_obj)
            
            obj = json.loads(fixed_obj)
            if isinstance(obj, dict):
                results.append(obj)
        except json.JSONDecodeError:
            continue
    
    if results:
        logging.info(f"Extracted {len(results)} objects using regex fallback")
        return results
    
    # Strategy 4: Create placeholder if nothing worked
    if expected_count and expected_count > 0:
        logging.warning(f"All parsing strategies failed. Creating {expected_count} empty results.")
        # Return empty list instead of placeholder to trigger proper error handling
        return []
    
    return results


def parse_json_with_fallback(
    text: str,
    expected_count: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Parse JSON data with multiple fallback strategies.

    DEPRECATED: This function is deprecated in favor of JsonParser from
    madspark.utils.json_parsing. Use that for new code.

    This function now delegates to JsonParser for consistency and better
    performance (pre-compiled patterns, telemetry tracking).

    Args:
        text: Raw text potentially containing JSON data
        expected_count: Expected number of JSON objects (optional)

    Returns:
        List of parsed dictionaries
    """
    # Emit deprecation warning to encourage migration
    import warnings
    warnings.warn(
        "parse_json_with_fallback() is deprecated. "
        "Use JsonParser from madspark.utils.json_parsing instead:\n"
        "  from madspark.utils.json_parsing import JsonParser\n"
        "  parser = JsonParser()\n"
        "  result = parser.parse(text, expected_count)",
        DeprecationWarning,
        stacklevel=2
    )

    # Handle None or empty input early
    if text is None or text == "":
        return []

    # Delegate to the new JsonParser for consistency
    from madspark.utils.json_parsing import JsonParser

    parser = JsonParser()
    result = parser.parse(text, expected_count=expected_count)

    # JsonParser returns various types, normalize to list of dicts
    if result is None:
        return []
    elif isinstance(result, list):
        # Already a list, ensure all items are dicts
        return [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        # Single dict, wrap in list
        return [result]
    else:
        # Unexpected type, return empty
        logging.warning(f"JsonParser returned unexpected type: {type(result)}")
        return []


def validate_evaluation_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize evaluation JSON data.
    
    Ensures the data contains required fields with appropriate types.
    Handles both integer and float scores from AI models.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Validated and normalized dictionary
    """
    validated = {}
    
    # Validate score
    score = data.get("score", 0)
    
    # Check for boolean type first (since bool is a subclass of int in Python)
    if isinstance(score, bool):
        logging.warning(f"Invalid score type {type(score)}, using default 0")
        score = 0
    # If score is already a valid int or float, use it directly
    elif isinstance(score, (int, float)):
        # Handle special float values (inf, -inf, nan)
        import math
        if math.isinf(score):
            logging.warning("Score is infinite, using default 0")
            score = 0
        elif math.isnan(score):
            logging.warning("Score is NaN, using default 0")
            score = 0
    else:
        # Try to convert string scores to float first
        if isinstance(score, str):
            try:
                # Handle "8.5/10" or "8/10" format by taking the numerator
                if '/' in score:
                    score = score.split('/')[0].strip()

                score = float(score)
                # Check for special float values after conversion
                import math
                if math.isinf(score):
                    logging.warning("Score is infinite, using default 0")
                    score = 0
                elif math.isnan(score):
                    logging.warning("Score is NaN, using default 0")
                    score = 0
            except ValueError:
                logging.warning(f"Could not convert score '{score}' to number, using default 0")
                score = 0
        else:
            # For all other types (None, list, dict, etc.), default to 0
            logging.warning(f"Invalid score type {type(score)}, using default 0")
            score = 0
    
    # Clamp score to valid range
    validated["score"] = max(0, min(10, score))
    
    # Validate comment
    comment = data.get("comment") or data.get("critique") or data.get("feedback") or ""
    validated["comment"] = str(comment).strip() or "No comment provided"
    
    return validated