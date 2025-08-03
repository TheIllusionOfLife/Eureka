"""
Utility to clean up improved idea text for better presentation.
Removes meta-commentary and references to original ideas.

Performance optimized with compiled regex patterns and caching.
"""

import re
from functools import lru_cache
from typing import List, Tuple, Optional

try:
    from madspark.utils.constants import (
        CLEANER_META_HEADERS,
        CLEANER_META_PHRASES,
        CLEANER_REPLACEMENT_PATTERNS,
        CLEANER_FRAMEWORK_CLEANUP_PATTERN,
        CLEANER_TITLE_EXTRACTION_PATTERN,
        CLEANER_TITLE_REPLACEMENT_PATTERN,
        CLEANER_TITLE_KEYWORDS
    )
except ImportError:
    from .constants import (
        CLEANER_META_HEADERS,
        CLEANER_META_PHRASES,
        CLEANER_REPLACEMENT_PATTERNS,
        CLEANER_FRAMEWORK_CLEANUP_PATTERN,
        CLEANER_TITLE_EXTRACTION_PATTERN,
        CLEANER_TITLE_REPLACEMENT_PATTERN,
        CLEANER_TITLE_KEYWORDS
    )

# Legacy aliases for backward compatibility
META_HEADERS = CLEANER_META_HEADERS
META_PHRASES = CLEANER_META_PHRASES


@lru_cache(maxsize=None)
def get_compiled_patterns() -> List[Tuple[re.Pattern, str]]:
    """
    Get compiled regex patterns with LRU caching for optimal performance.
    
    This function compiles all replacement patterns once and caches them
    for reuse, significantly improving performance for large text processing.
    
    Returns:
        List of compiled (pattern, replacement) tuples
    """
    return [
        (re.compile(pattern, re.IGNORECASE | re.MULTILINE), replacement)
        for pattern, replacement in CLEANER_REPLACEMENT_PATTERNS
    ]


@lru_cache(maxsize=None)
def get_compiled_framework_pattern() -> re.Pattern:
    """
    Get compiled framework cleanup pattern with caching.
    
    Returns:
        Compiled regex pattern for framework cleanup
    """
    return re.compile(CLEANER_FRAMEWORK_CLEANUP_PATTERN, re.IGNORECASE)


@lru_cache(maxsize=None)
def get_compiled_title_patterns() -> Tuple[re.Pattern, re.Pattern]:
    """
    Get compiled title extraction and replacement patterns with caching.
    
    Returns:
        Tuple of (extraction_pattern, replacement_pattern)
    """
    extraction_pattern = re.compile(CLEANER_TITLE_EXTRACTION_PATTERN)
    replacement_pattern = re.compile(CLEANER_TITLE_REPLACEMENT_PATTERN)
    return extraction_pattern, replacement_pattern


@lru_cache(maxsize=None)
def get_compiled_meta_patterns() -> Tuple[List[re.Pattern], List[re.Pattern]]:
    """
    Get compiled meta header and phrase patterns with caching.
    
    Returns:
        Tuple of (compiled_headers, compiled_phrases)
    """
    compiled_headers = [
        re.compile(re.escape(header), re.IGNORECASE) 
        for header in CLEANER_META_HEADERS
    ]
    compiled_phrases = [
        re.compile(re.escape(phrase), re.IGNORECASE) 
        for phrase in CLEANER_META_PHRASES
    ]
    return compiled_headers, compiled_phrases


# Pre-compiled regex patterns for backward compatibility and immediate use
# These are now dynamically generated from the cached functions
COMPILED_REPLACEMENTS = None  # Will be lazily initialized


def _ensure_compiled_replacements():
    """
    Ensure COMPILED_REPLACEMENTS is initialized for backward compatibility.
    
    This function lazily initializes the legacy COMPILED_REPLACEMENTS variable
    using the optimized cached pattern compilation.
    """
    global COMPILED_REPLACEMENTS
    if COMPILED_REPLACEMENTS is None:
        COMPILED_REPLACEMENTS = get_compiled_patterns()


def clean_improved_idea(text: Optional[str]) -> Optional[str]:
    """
    Clean up improved idea text by removing meta-commentary and references to improvements.
    
    Performance optimized with cached compiled regex patterns.
    
    Args:
        text: The raw improved idea text
        
    Returns:
        Cleaned text focused on the idea itself
    """
    if text is None:
        return None
    if not text.strip():
        return text
    
    # Remove meta-commentary sections at the beginning
    lines = text.split('\n')
    cleaned_lines = []
    skip_until_empty = False
    
    # Get compiled meta patterns for performance
    compiled_headers, compiled_phrases = get_compiled_meta_patterns()
    
    for line in lines:
        # Skip meta headers using compiled patterns
        if any(pattern.search(line) for pattern in compiled_headers):
            skip_until_empty = True
            continue
        
        # Skip until we hit an empty line after meta headers
        if skip_until_empty:
            if line.strip() == '':
                skip_until_empty = False
            continue
        
        # Skip lines that are pure meta-commentary using compiled patterns
        if any(pattern.search(line) for pattern in compiled_phrases):
            continue
        
        cleaned_lines.append(line)
    
    cleaned = '\n'.join(cleaned_lines)
    
    # Apply cached compiled regex patterns for optimal performance
    compiled_patterns = get_compiled_patterns()
    for pattern, replacement in compiled_patterns:
        cleaned = pattern.sub(replacement, cleaned)
    
    # Clean up the beginning if it starts with a framework name using cached pattern
    framework_pattern = get_compiled_framework_pattern()
    cleaned = framework_pattern.sub('', cleaned)
    
    # Final cleanup
    cleaned = cleaned.strip()
    
    # If there's a clear title at the beginning, format it properly
    first_line = cleaned.split('\n')[0] if cleaned else ''
    if any(keyword in first_line for keyword in CLEANER_TITLE_KEYWORDS):
        # Extract the main concept name using cached patterns
        title_extraction_pattern, title_replacement_pattern = get_compiled_title_patterns()
        title_match = title_extraction_pattern.search(first_line)
        if title_match:
            title = title_match.group(1)
            cleaned = title_replacement_pattern.sub(f'# {title}\n\n', cleaned)
    
    return cleaned


def clean_improved_ideas_in_results(results: List[dict]) -> List[dict]:
    """
    Clean improved ideas in a list of results.
    
    Performance optimized for batch processing with pre-warmed pattern cache.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        List with cleaned improved ideas
    """
    # Pre-warm the pattern cache for batch processing
    get_compiled_patterns()
    get_compiled_framework_pattern()
    get_compiled_title_patterns()
    get_compiled_meta_patterns()
    
    cleaned_results = []
    for result in results:
        cleaned_result = result.copy()
        if 'improved_idea' in cleaned_result:
            improved_idea = cleaned_result['improved_idea']
            # Only clean string format improved ideas, leave dictionary format as-is
            if isinstance(improved_idea, str):
                cleaned_result['improved_idea'] = clean_improved_idea(improved_idea)
            # Dictionary format doesn't need text cleaning
        cleaned_results.append(cleaned_result)
    return cleaned_results


# Initialize legacy COMPILED_REPLACEMENTS for backward compatibility
_ensure_compiled_replacements()


# Example usage
if __name__ == "__main__":
    import time
    
    # Test with sample text
    sample = """
## ENHANCED CONCEPT: The "Insight Catalyst" Framework – Accelerating Impact Through Strategic, Simple Testing

**ORIGINAL THEME:** Test Idea

**REVISED CORE PREMISE:** The "Insight Catalyst" Framework leverages *strategically simple and innovative tests* to rapidly generate actionable insights.

### 1. The "Insight Catalyst" Framework: A New Paradigm for Rapid Learning

Our enhanced approach isn't just a list of tests; it's a **structured framework**.
"""
    
    print("BEFORE:")
    print(sample)
    print("\n" + "="*80 + "\n")
    print("AFTER:")
    print(clean_improved_idea(sample))
    
    # Performance test
    print("\n" + "="*80 + "\n")
    print("PERFORMANCE TEST:")
    
    large_sample = sample * 20  # Make it larger for testing
    print(f"Test text size: {len(large_sample)} characters")
    
    # Test performance
    start_time = time.time()
    for i in range(100):
        clean_improved_idea(large_sample)
    end_time = time.time()
    
    print(f"Optimized performance: {(end_time - start_time)*1000:.2f}ms for 100 iterations")
    print(f"Pattern cache status: {get_compiled_patterns.cache_info()}")
    print("✅ Performance test completed")