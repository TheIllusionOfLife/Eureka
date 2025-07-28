"""Test text similarity utilities."""
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.text_similarity import calculate_jaccard_similarity, is_meaningful_improvement


class TestTextSimilarity:
    """Test text similarity functions."""
    
    def test_calculate_jaccard_similarity_identical(self):
        """Test Jaccard similarity for identical texts."""
        text = "renewable energy solar panels"
        similarity = calculate_jaccard_similarity(text, text)
        assert similarity == 1.0
    
    def test_calculate_jaccard_similarity_different(self):
        """Test Jaccard similarity for completely different texts."""
        text1 = "renewable energy solar panels"
        text2 = "quantum computing artificial intelligence"
        similarity = calculate_jaccard_similarity(text1, text2)
        assert similarity == 0.0
    
    def test_calculate_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity for partial overlap."""
        text1 = "renewable energy solar panels"
        text2 = "renewable solar power systems"
        similarity = calculate_jaccard_similarity(text1, text2)
        # Should have some overlap but not complete
        assert 0.0 < similarity < 1.0
    
    def test_calculate_jaccard_similarity_empty_texts(self):
        """Test Jaccard similarity handles empty texts."""
        assert calculate_jaccard_similarity("", "text") == 0.0
        assert calculate_jaccard_similarity("text", "") == 0.0
        assert calculate_jaccard_similarity("", "") == 0.0
    
    def test_is_meaningful_improvement_identical_low_score_delta(self):
        """Test that identical texts with low score delta are not meaningful."""
        text = "renewable energy solar panel installation"
        is_meaningful, similarity = is_meaningful_improvement(
            text, text, score_delta=0.1,
            similarity_threshold=0.9, score_delta_threshold=0.3
        )
        assert not is_meaningful
        assert similarity == 1.0
    
    def test_is_meaningful_improvement_different_texts(self):
        """Test that different texts are considered meaningful."""
        text1 = "renewable energy solar panels"
        text2 = "community solar gardens with battery storage"
        is_meaningful, similarity = is_meaningful_improvement(
            text1, text2, score_delta=0.1,
            similarity_threshold=0.9, score_delta_threshold=0.3
        )
        assert is_meaningful
        assert similarity < 0.9
    
    def test_is_meaningful_improvement_high_score_delta(self):
        """Test that high score delta makes improvement meaningful even with similar text."""
        text1 = "renewable energy solar panels"
        text2 = "renewable energy solar panels installation"
        is_meaningful, similarity = is_meaningful_improvement(
            text1, text2, score_delta=2.0,
            similarity_threshold=0.9, score_delta_threshold=0.3
        )
        assert is_meaningful  # High score delta makes it meaningful
    
    def test_is_meaningful_improvement_edge_cases(self):
        """Test edge cases for meaningful improvement detection."""
        # Empty texts
        is_meaningful, _ = is_meaningful_improvement("", "", 0.0)
        assert is_meaningful  # Default to meaningful when can't compare
        
        # One empty text
        is_meaningful, _ = is_meaningful_improvement("text", "", 0.0)
        assert is_meaningful  # Default to meaningful when can't compare