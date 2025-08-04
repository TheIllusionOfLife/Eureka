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


def parse_json_with_fallback(
    text: str,
    expected_count: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Parse JSON data with multiple fallback strategies.
    
    This function attempts to parse JSON data using several strategies:
    1. Parse as a JSON array
    2. Extract JSON arrays from text
    3. Parse line-by-line as separate JSON objects
    4. Extract JSON objects using regex
    5. Extract score/comment pairs using regex patterns
    
    Args:
        text: Raw text potentially containing JSON data
        expected_count: Expected number of JSON objects (optional)
        
    Returns:
        List of parsed dictionaries
    """
    results: List[Dict[str, Any]] = []
    
    # Handle None or empty input
    if text is None or text == "":
        return []
    
    # Strategy 1: Try to parse as a complete JSON array
    try:
        data = json.loads(text)
        if isinstance(data, list):
            results = data
            logging.debug(f"Successfully parsed as JSON array with {len(results)} items")
            return results
        elif isinstance(data, dict):
            results = [data]
            logging.debug("Successfully parsed as single JSON object")
            return results
    except json.JSONDecodeError:
        logging.debug("Failed to parse as complete JSON, trying other strategies")
    
    # Strategy 2: Extract JSON arrays from text
    # Helper function to extract JSON arrays with proper bracket matching
    def _extract_json_arrays(text):
        """Extract JSON arrays from text with proper bracket matching."""
        arrays_found = []
        array_start = text.find('[')
        
        while array_start != -1:
            # Try to find the matching closing bracket
            bracket_count = 0
            in_string = False
            escape_next = False
            pos = array_start
            
            while pos < len(text):
                char = text[pos]
                
                if escape_next:
                    escape_next = False
                elif char == '\\' and in_string:
                    escape_next = True
                elif char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # Found matching closing bracket
                            array_str = text[array_start:pos+1]
                            try:
                                array_data = json.loads(array_str)
                                if isinstance(array_data, list):
                                    arrays_found.append((array_start, pos+1, array_data))
                            except json.JSONDecodeError:
                                pass
                            break
                
                pos += 1
            
            # Look for next array after the current one's closing bracket
            if bracket_count == 0:
                array_start = text.find('[', pos + 1)
            else:
                array_start = text.find('[', array_start + 1)
        
        return arrays_found
    
    # Extract all JSON arrays
    arrays = _extract_json_arrays(text)
    for start_pos, end_pos, array_data in arrays:
        for item in array_data:
            if isinstance(item, dict):
                results.append(item)
    
    if results:
        logging.debug(f"Successfully extracted {len(results)} items from JSON arrays")
        return results
    
    # Strategy 3: Try line-by-line parsing
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines:
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                results.append(obj)
        except json.JSONDecodeError:
            continue
    
    if results:
        logging.debug(f"Successfully parsed {len(results)} JSON objects line-by-line")
        return results
    
    # Try to find individual JSON objects (including multi-line)
    # This pattern handles nested objects and multi-line strings
    json_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', re.DOTALL)
    potential_jsons = json_pattern.findall(text)
    
    for json_str in potential_jsons:
        try:
            # First try direct parsing
            obj = json.loads(json_str)
            if isinstance(obj, dict):
                results.append(obj)
        except json.JSONDecodeError:
            # If that fails, try to clean up multi-line strings
            try:
                # Replace actual newlines in strings with escaped newlines
                cleaned = re.sub(r'("(?:[^"\\]|\\.)*")', lambda m: m.group(0).replace('\n', '\\n'), json_str)
                obj = json.loads(cleaned)
                if isinstance(obj, dict):
                    results.append(obj)
            except json.JSONDecodeError:
                continue
    
    if results:
        logging.debug(f"Successfully extracted {len(results)} JSON objects using regex")
        return results
    
    # Strategy 5: Extract score/comment patterns using regex
    # Look for various patterns like "Score: 8, Comment: ..." or narrative formats
    
    # Pattern 1: Standard "Score: X, Comment: Y" format
    score_comment_pattern = re.compile(
        r'(?:score|Score)[\s:]+(\d+).*?(?:comment|Comment|critique|Critique)[\s:]+([^\n]+)',
        re.IGNORECASE | re.DOTALL
    )
    
    matches = score_comment_pattern.findall(text)
    for score_str, comment in matches:
        try:
            results.append({
                "score": int(score_str),
                "comment": comment.strip().strip('"\'')
            })
        except ValueError:
            continue
    
    # Pattern 2: Narrative format with improved regex patterns
    # Limited repetition to prevent ReDoS, capture until newline for robust comments
    narrative_patterns = [
        re.compile(r'scores?\s+an?\s+(\d+)(?:\s+out\s+of\s+\d+)?[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})', re.IGNORECASE),
        re.compile(r'give\s+it\s+a\s+score\s+of\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})', re.IGNORECASE),
        re.compile(r'(?:deserves?|gets?)\s+an?\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})', re.IGNORECASE),
        re.compile(r'scores?\s+(\d+)[.,]?\s*(?:Comment|comment)?:?\s*([^\n]{1,500})', re.IGNORECASE),
    ]
    
    for pattern in narrative_patterns:
        narrative_matches = pattern.findall(text)
        for score_str, comment in narrative_matches:
            try:
                results.append({
                    "score": int(score_str),
                    "comment": comment.strip().strip('"\'.')  # Also strip trailing period
                })
            except ValueError:
                continue
    
    if results:
        logging.debug(f"Successfully extracted {len(results)} score/comment pairs using regex")
        return results
    
    # If expected_count is provided and we have no results, create placeholders
    if expected_count and expected_count > 0 and not results:
        logging.warning(
            f"Could not parse any JSON data. Creating {expected_count} placeholder entries."
        )
        results = [
            {"score": 0, "comment": "Failed to parse evaluation"}
            for _ in range(expected_count)
        ]
    
    return results


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
    if isinstance(score, str):
        try:
            # Try to parse as float first to handle "8.7" style strings
            float_score = float(score)
            score = round(float_score)
        except ValueError:
            logging.warning(f"Could not convert score '{score}' to number, using default 0")
            score = 0
    elif isinstance(score, float):
        # Round float scores to nearest integer
        score = round(score)
    elif isinstance(score, int):
        # Integer scores are fine as-is
        pass
    else:
        logging.warning(f"Invalid score type {type(score)}, using default 0")
        score = 0
    
    # Clamp score to valid range
    validated["score"] = max(0, min(10, score))
    
    # Validate comment
    comment = data.get("comment") or data.get("critique") or data.get("feedback") or ""
    validated["comment"] = str(comment).strip() or "No comment provided"
    
    return validated