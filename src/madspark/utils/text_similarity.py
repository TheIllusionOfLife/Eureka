"""Text similarity utilities for detecting meaningful improvements.

This module provides functions to calculate text similarity and determine
if improvements are meaningful based on both text similarity and score changes.
"""

from typing import Tuple


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts.
    
    Args:
        text1: First text to compare
        text2: Second text to compare
        
    Returns:
        Jaccard similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
        
    # Normalize both texts for comparison
    words1 = set(text1.lower().strip().split())
    words2 = set(text2.lower().strip().split())
    
    if not words1 or not words2:
        return 0.0
        
    # Jaccard similarity (intersection over union)
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def is_meaningful_improvement(
    original_text: str,
    improved_text: str,
    score_delta: float,
    similarity_threshold: float = 0.9,
    score_delta_threshold: float = 0.3
) -> Tuple[bool, float]:
    """Determine if an improvement is meaningful based on text similarity and score change.
    
    Args:
        original_text: Original idea text
        improved_text: Improved idea text
        score_delta: Score difference between improved and original
        similarity_threshold: Minimum similarity to consider texts too similar (default: 0.9)
        score_delta_threshold: Minimum score improvement to consider meaningful (default: 0.3)
        
    Returns:
        Tuple of (is_meaningful, similarity_score)
    """
    if not original_text or not improved_text:
        return True, 0.0  # Consider it meaningful if we can't compare
        
    similarity = calculate_jaccard_similarity(original_text, improved_text)
    score_improvement_minimal = abs(score_delta) < score_delta_threshold
    
    # Consider improvement non-meaningful if texts are very similar AND score change is minimal
    is_meaningful = not (similarity > similarity_threshold and score_improvement_minimal)
    
    return is_meaningful, similarity