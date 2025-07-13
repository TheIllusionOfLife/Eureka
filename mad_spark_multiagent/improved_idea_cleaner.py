"""
Utility to clean up improved idea text for better presentation.
Removes meta-commentary and references to original ideas.
"""

import re
from typing import List, Tuple


def clean_improved_idea(text: str) -> str:
    """
    Clean up improved idea text by removing meta-commentary and references to improvements.
    
    Args:
        text: The raw improved idea text
        
    Returns:
        Cleaned text focused on the idea itself
    """
    if not text:
        return text
    
    # Remove meta-commentary sections at the beginning
    lines = text.split('\n')
    cleaned_lines = []
    skip_until_empty = False
    
    for i, line in enumerate(lines):
        # Skip meta headers
        if any(pattern in line for pattern in [
            'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
            'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
        ]):
            skip_until_empty = True
            continue
        
        # Skip until we hit an empty line after meta headers
        if skip_until_empty:
            if line.strip() == '':
                skip_until_empty = False
            continue
        
        # Skip lines that are pure meta-commentary
        if any(phrase in line for phrase in [
            'Addresses Evaluation Criteria', 'Enhancing Impact Through',
            'Preserving & Amplifying Strengths', 'Addressing Concerns',
            'Score:', 'from Score', 'Building on Score', '↑↑ from', '↑ from'
        ]):
            continue
        
        cleaned_lines.append(line)
    
    cleaned = '\n'.join(cleaned_lines)
    
    # Remove or replace specific patterns
    replacements = [
        # Remove improvement references
        (r'Our enhanced approach', 'This approach'),
        (r'The enhanced concept', 'The concept'),
        (r'This enhanced version', 'This version'),
        (r'enhanced ', ''),
        (r'improved ', ''),
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
    
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up the beginning if it starts with a framework name
    cleaned = re.sub(r'^[:\s]*(?:a\s+)?more\s+robust.*?system\s+', '', cleaned, flags=re.IGNORECASE)
    
    # Final cleanup
    cleaned = cleaned.strip()
    
    # If there's a clear title at the beginning, format it properly
    first_line = cleaned.split('\n')[0] if cleaned else ''
    if 'Framework' in first_line or 'System' in first_line or 'Engine' in first_line:
        # Extract the main concept name
        title_match = re.search(r'"([^"]+)"', first_line)
        if title_match:
            title = title_match.group(1)
            cleaned = re.sub(r'^.*?"[^"]+".*?\n+', f'# {title}\n\n', cleaned)
    
    return cleaned


def clean_improved_ideas_in_results(results: List[dict]) -> List[dict]:
    """
    Clean improved ideas in a list of results.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        List with cleaned improved ideas
    """
    cleaned_results = []
    for result in results:
        cleaned_result = result.copy()
        if 'improved_idea' in cleaned_result:
            cleaned_result['improved_idea'] = clean_improved_idea(cleaned_result['improved_idea'])
        cleaned_results.append(cleaned_result)
    return cleaned_results


# Example usage
if __name__ == "__main__":
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