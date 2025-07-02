"""Tests for the novelty filter module."""
import pytest
from mad_spark_multiagent.novelty_filter import NoveltyFilter, FilteredIdea, filter_ideas_for_novelty


class TestNoveltyFilter:
    """Test cases for the NoveltyFilter class."""
    
    def test_exact_duplicate_detection(self):
        """Test detection of exact duplicates."""
        filter_instance = NoveltyFilter()
        
        idea1 = "Solar panels for homes"
        idea2 = "Solar panels for homes"  # Exact duplicate
        
        result1 = filter_instance.filter_idea(idea1)
        result2 = filter_instance.filter_idea(idea2)
        
        assert result1.is_novel is True
        assert result2.is_novel is False
        assert result2.similarity_score == 1.0
    
    def test_case_insensitive_duplicate_detection(self):
        """Test case-insensitive duplicate detection."""
        filter_instance = NoveltyFilter()
        
        idea1 = "Solar Panels for Homes"
        idea2 = "solar panels for homes"  # Case difference
        
        result1 = filter_instance.filter_idea(idea1)
        result2 = filter_instance.filter_idea(idea2)
        
        assert result1.is_novel is True
        assert result2.is_novel is False
    
    def test_punctuation_normalization(self):
        """Test that punctuation differences don't prevent duplicate detection."""
        filter_instance = NoveltyFilter()
        
        idea1 = "Solar panels for homes!"
        idea2 = "Solar panels for homes..."  # Different punctuation
        
        result1 = filter_instance.filter_idea(idea1)
        result2 = filter_instance.filter_idea(idea2)
        
        assert result1.is_novel is True
        assert result2.is_novel is False
    
    def test_similarity_threshold(self):
        """Test similarity threshold configuration."""
        # High threshold (more permissive)
        filter_high = NoveltyFilter(similarity_threshold=0.9)
        
        idea1 = "Solar panels for residential homes"
        idea2 = "Solar panels for home use"  # Similar but not identical
        
        result1 = filter_high.filter_idea(idea1)
        result2 = filter_high.filter_idea(idea2)
        
        assert result1.is_novel is True
        assert result2.is_novel is True  # Should pass with high threshold
        
        # Low threshold (more strict)
        filter_low = NoveltyFilter(similarity_threshold=0.3)
        filter_low.filter_idea(idea1)  # Add first idea
        result3 = filter_low.filter_idea(idea2)
        
        assert result3.is_novel is False  # Should fail with low threshold
    
    def test_keyword_similarity_calculation(self):
        """Test keyword-based similarity calculation."""
        filter_instance = NoveltyFilter()
        
        # Test similar ideas
        similarity = filter_instance._calculate_keyword_similarity(
            "Solar panels for homes",
            "Home solar panel systems"
        )
        assert similarity > 0.5  # Should have significant overlap
        
        # Test dissimilar ideas
        similarity = filter_instance._calculate_keyword_similarity(
            "Solar panels for homes",
            "Wind turbines for cities"
        )
        assert similarity < 0.3  # Should have little overlap
    
    def test_empty_and_invalid_ideas(self):
        """Test handling of empty and invalid ideas."""
        filter_instance = NoveltyFilter()
        
        # Empty idea
        result = filter_instance.filter_idea("")
        assert result.is_novel is False
        assert "Empty or invalid" in result.similar_to
        
        # Whitespace only
        result = filter_instance.filter_idea("   ")
        assert result.is_novel is False
    
    def test_filter_ideas_batch(self):
        """Test filtering multiple ideas at once."""
        ideas = [
            "Solar panels for homes",
            "Wind turbines for cities",
            "Solar panels for homes",  # Duplicate
            "Home solar energy systems",  # Similar
            "Electric vehicle charging stations"
        ]
        
        filter_instance = NoveltyFilter(similarity_threshold=0.7)
        filtered_ideas = filter_instance.filter_ideas(ideas)
        
        assert len(filtered_ideas) == 5
        assert filtered_ideas[0].is_novel is True  # First solar idea
        assert filtered_ideas[1].is_novel is True  # Wind turbines
        assert filtered_ideas[2].is_novel is False  # Exact duplicate
        # Fourth idea might be filtered as similar depending on threshold
        assert filtered_ideas[4].is_novel is True  # EV charging
    
    def test_get_novel_ideas_only(self):
        """Test getting only novel ideas."""
        ideas = [
            "Solar panels for homes",
            "Solar panels for homes",  # Duplicate
            "Wind turbines for cities",
            "Electric vehicles"
        ]
        
        filter_instance = NoveltyFilter()
        novel_ideas = filter_instance.get_novel_ideas(ideas)
        
        assert len(novel_ideas) == 3  # Should exclude duplicate
        assert "Solar panels for homes" in novel_ideas
        assert "Wind turbines for cities" in novel_ideas
        assert "Electric vehicles" in novel_ideas
    
    def test_filter_reset(self):
        """Test resetting filter state."""
        filter_instance = NoveltyFilter()
        
        # Add some ideas
        filter_instance.filter_idea("Solar panels")
        filter_instance.filter_idea("Wind turbines")
        
        assert len(filter_instance.seen_hashes) == 2
        assert len(filter_instance.processed_ideas) == 2
        
        # Reset
        filter_instance.reset()
        
        assert len(filter_instance.seen_hashes) == 0
        assert len(filter_instance.processed_ideas) == 0
        
        # Same idea should now be novel again
        result = filter_instance.filter_idea("Solar panels")
        assert result.is_novel is True


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_filter_ideas_for_novelty(self):
        """Test the convenience function for filtering ideas."""
        ideas = [
            "Solar energy systems",
            "Wind power generation",
            "Solar energy systems",  # Duplicate
            "Hydroelectric power"
        ]
        
        novel_ideas, all_filtered = filter_ideas_for_novelty(ideas, similarity_threshold=0.8)
        
        assert len(novel_ideas) == 3  # Should exclude duplicate
        assert len(all_filtered) == 4  # Should include all with metadata
        
        # Check that metadata is included
        assert all(isinstance(idea, FilteredIdea) for idea in all_filtered)
        assert all_filtered[2].is_novel is False  # Duplicate should be marked
    
    def test_keyword_extraction(self):
        """Test keyword extraction with stop words."""
        filter_instance = NoveltyFilter()
        
        # Test stop word removal
        keywords = filter_instance._get_keywords("The solar panels are for the homes")
        stop_words_present = any(word in keywords for word in ['the', 'are', 'for'])
        assert not stop_words_present
        
        # Test meaningful keywords are kept
        assert 'solar' in keywords
        assert 'panels' in keywords
        assert 'homes' in keywords
    
    def test_normalization(self):
        """Test text normalization."""
        filter_instance = NoveltyFilter()
        
        # Test punctuation removal and case normalization
        normalized = filter_instance._normalize_text("Solar Panels!!! For... Homes???")
        expected = "solar panels for homes"
        assert normalized == expected
        
        # Test whitespace normalization
        normalized = filter_instance._normalize_text("Solar    panels   for\thomes")
        assert normalized == "solar panels for homes"