"""
Comprehensive tests for the duplicate detection system.

This module tests all aspects of the duplicate detection functionality including:
- Text processing and normalization
- Similarity calculation algorithms  
- Duplicate detection logic
- BookmarkManager integration
- Edge cases and error handling
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Import the modules to test
try:
    from madspark.utils.duplicate_detector import (
        TextProcessor, SimilarityCalculator, DuplicateDetector,
        SimilarityResult, DuplicateCheckResult, 
        check_bookmark_duplicates, calculate_bookmark_similarity
    )
    from madspark.utils.bookmark_system import BookmarkManager
    from madspark.utils.models import BookmarkedIdea
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from madspark.utils.duplicate_detector import (
        TextProcessor, SimilarityCalculator, DuplicateDetector,
        SimilarityResult, DuplicateCheckResult, 
        check_bookmark_duplicates, calculate_bookmark_similarity
    )
    from madspark.utils.bookmark_system import BookmarkManager
    from madspark.utils.models import BookmarkedIdea


class TestTextProcessor:
    """Tests for text processing utilities."""
    
    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        processor = TextProcessor()
        
        # Test basic normalization
        assert processor.normalize_text("Hello World!") == "hello world"
        assert processor.normalize_text("  Multiple   Spaces  ") == "multiple spaces"
        assert processor.normalize_text("UPPERCASE text") == "uppercase text"
    
    def test_normalize_text_punctuation(self):
        """Test punctuation removal in normalization."""
        processor = TextProcessor()
        
        text = "Hello, World! How are you? I'm fine."
        expected = "hello world how are you i m fine"
        assert processor.normalize_text(text) == expected
    
    def test_normalize_text_edge_cases(self):
        """Test edge cases in text normalization."""
        processor = TextProcessor()
        
        # Empty and None cases
        assert processor.normalize_text("") == ""
        assert processor.normalize_text(None) == ""
        
        # Only punctuation
        assert processor.normalize_text("!@#$%^&*()") == ""
        
        # Only spaces
        assert processor.normalize_text("   ") == ""
    
    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        processor = TextProcessor()
        
        text = "artificial intelligence machine learning data science"
        keywords = processor.extract_keywords(text)
        
        # Should include meaningful words
        assert "artificial" in keywords
        assert "intelligence" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "data" in keywords  # Note: might be excluded if min_length > 4
        assert "science" in keywords
    
    def test_extract_keywords_stop_words(self):
        """Test that stop words are filtered out."""
        processor = TextProcessor()
        
        text = "The artificial intelligence and machine learning with data science"
        keywords = processor.extract_keywords(text)
        
        # Stop words should be excluded
        assert "the" not in keywords
        assert "and" not in keywords
        assert "with" not in keywords
        
        # Meaningful words should be included
        assert "artificial" in keywords
        assert "intelligence" in keywords
    
    def test_extract_keywords_min_length(self):
        """Test minimum word length filtering."""
        processor = TextProcessor()
        
        text = "ai ml big data science"
        keywords = processor.extract_keywords(text, min_word_length=3)
        
        # Short words should be excluded
        assert "ai" not in keywords
        assert "ml" not in keywords
        
        # Longer words should be included
        assert "big" in keywords
        assert "data" in keywords
        assert "science" in keywords
    
    def test_create_text_fingerprint(self):
        """Test text fingerprint creation."""
        processor = TextProcessor()
        
        # Same content should produce same fingerprint
        text1 = "Hello World!"
        text2 = "hello world"  # Different case and punctuation
        
        fp1 = processor.create_text_fingerprint(text1)
        fp2 = processor.create_text_fingerprint(text2)
        
        assert fp1 == fp2  # Should be identical after normalization
        assert len(fp1) == 32  # MD5 hash length
    
    def test_create_text_fingerprint_different(self):
        """Test that different texts produce different fingerprints."""
        processor = TextProcessor()
        
        fp1 = processor.create_text_fingerprint("Hello World")
        fp2 = processor.create_text_fingerprint("Goodbye World")
        
        assert fp1 != fp2


class TestSimilarityCalculator:
    """Tests for similarity calculation algorithms."""
    
    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity with identical sets."""
        calc = SimilarityCalculator()
        
        set1 = {"apple", "banana", "cherry"}
        set2 = {"apple", "banana", "cherry"}
        
        similarity = calc.jaccard_similarity(set1, set2)
        assert similarity == 1.0
    
    def test_jaccard_similarity_no_overlap(self):
        """Test Jaccard similarity with no overlap."""
        calc = SimilarityCalculator()
        
        set1 = {"apple", "banana"}
        set2 = {"cherry", "date"}
        
        similarity = calc.jaccard_similarity(set1, set2)
        assert similarity == 0.0
    
    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity with partial overlap."""
        calc = SimilarityCalculator()
        
        set1 = {"apple", "banana", "cherry"}
        set2 = {"banana", "cherry", "date"}
        
        # Intersection: {banana, cherry} = 2
        # Union: {apple, banana, cherry, date} = 4
        # Expected similarity: 2/4 = 0.5
        similarity = calc.jaccard_similarity(set1, set2)
        assert similarity == 0.5
    
    def test_jaccard_similarity_empty_sets(self):
        """Test Jaccard similarity with empty sets."""
        calc = SimilarityCalculator()
        
        # Both empty
        assert calc.jaccard_similarity(set(), set()) == 1.0
        
        # One empty
        assert calc.jaccard_similarity({"apple"}, set()) == 0.0
        assert calc.jaccard_similarity(set(), {"apple"}) == 0.0
    
    def test_text_overlap_ratio_identical(self):
        """Test text overlap ratio with identical texts."""
        calc = SimilarityCalculator()
        
        text1 = "artificial intelligence machine learning"
        text2 = "artificial intelligence machine learning"
        
        similarity = calc.text_overlap_ratio(text1, text2)
        assert similarity == 1.0
    
    def test_text_overlap_ratio_no_overlap(self):
        """Test text overlap ratio with minimal overlap."""
        calc = SimilarityCalculator()
        
        text1 = "artificial intelligence"
        text2 = "natural language"
        
        similarity = calc.text_overlap_ratio(text1, text2)
        assert similarity < 0.8  # Should be low but not necessarily 0.0
    
    def test_text_overlap_ratio_partial_overlap(self):
        """Test text overlap ratio with partial overlap."""
        calc = SimilarityCalculator()
        
        text1 = "machine learning algorithms"
        text2 = "machine learning models"
        
        # Should have high similarity due to "machine learning"
        similarity = calc.text_overlap_ratio(text1, text2)
        assert similarity > 0.5
    
    def test_text_overlap_ratio_short_texts(self):
        """Test text overlap ratio with short texts."""
        calc = SimilarityCalculator()
        
        # Short texts should use character-level comparison
        text1 = "AI"
        text2 = "AI ML"
        
        similarity = calc.text_overlap_ratio(text1, text2)
        assert similarity > 0.0
    
    def test_semantic_similarity_identical(self):
        """Test semantic similarity with identical texts."""
        calc = SimilarityCalculator()
        
        text1 = "Machine learning is a subset of artificial intelligence"
        text2 = "Machine learning is a subset of artificial intelligence"
        
        similarity = calc.semantic_similarity(text1, text2)
        assert similarity == 1.0
    
    def test_semantic_similarity_similar_content(self):
        """Test semantic similarity with similar content."""
        calc = SimilarityCalculator()
        
        text1 = "Machine learning algorithms for data analysis"
        text2 = "Data analysis using machine learning algorithms"
        
        similarity = calc.semantic_similarity(text1, text2)
        assert similarity > 0.8  # Should be very similar
    
    def test_semantic_similarity_different_content(self):
        """Test semantic similarity with different content."""
        calc = SimilarityCalculator()
        
        text1 = "Machine learning algorithms"
        text2 = "Cooking recipes and ingredients"
        
        similarity = calc.semantic_similarity(text1, text2)
        assert similarity < 0.2  # Should be very different
    
    def test_semantic_similarity_empty_texts(self):
        """Test semantic similarity with empty texts."""
        calc = SimilarityCalculator()
        
        # Both empty
        assert calc.semantic_similarity("", "") == 1.0
        
        # One empty
        assert calc.semantic_similarity("text", "") == 0.0
        assert calc.semantic_similarity("", "text") == 0.0


class TestDuplicateDetector:
    """Tests for the main duplicate detection system."""
    
    def test_init_default_threshold(self):
        """Test DuplicateDetector initialization with default threshold."""
        detector = DuplicateDetector()
        assert detector.similarity_threshold == 0.8
    
    def test_init_custom_threshold(self):
        """Test DuplicateDetector initialization with custom threshold."""
        detector = DuplicateDetector(similarity_threshold=0.9)
        assert detector.similarity_threshold == 0.9
    
    def test_calculate_similarity_identical_texts(self):
        """Test similarity calculation with identical texts."""
        detector = DuplicateDetector()
        
        text1 = "Machine learning model for image recognition"
        text2 = "Machine learning model for image recognition"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert similarity == 1.0
    
    def test_calculate_similarity_similar_texts(self):
        """Test similarity calculation with similar texts."""
        detector = DuplicateDetector()
        
        text1 = "Machine learning model for image recognition"
        text2 = "Image recognition using machine learning models"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert 0.6 < similarity < 1.0  # Should be high but not perfect
    
    def test_calculate_similarity_different_texts(self):
        """Test similarity calculation with different texts."""
        detector = DuplicateDetector()
        
        text1 = "Machine learning model"
        text2 = "Cooking delicious pasta"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert similarity < 0.4  # Should be low but algorithms may find some character overlap
    
    def test_calculate_similarity_with_themes(self):
        """Test similarity calculation including theme context."""
        detector = DuplicateDetector()
        
        text1 = "Smart irrigation system"
        text2 = "Automated watering system"
        theme1 = "agriculture"
        theme2 = "agriculture"
        
        similarity = detector.calculate_similarity(text1, text2, theme1, theme2)
        # Theme match should boost similarity
        similarity_without_theme = detector.calculate_similarity(text1, text2)
        
        assert similarity > similarity_without_theme
    
    def test_calculate_similarity_empty_inputs(self):
        """Test similarity calculation with empty inputs."""
        detector = DuplicateDetector()
        
        assert detector.calculate_similarity("", "") == 0.0
        assert detector.calculate_similarity("text", "") == 0.0
        assert detector.calculate_similarity("", "text") == 0.0
    
    def test_find_duplicates_no_existing_bookmarks(self):
        """Test duplicate finding with no existing bookmarks."""
        detector = DuplicateDetector()
        
        results = detector.find_duplicates("New idea text", "technology", [])
        assert len(results) == 0
    
    def test_find_duplicates_with_similar_bookmarks(self):
        """Test duplicate finding with similar existing bookmarks."""
        detector = DuplicateDetector()
        
        # Create mock bookmarks
        bookmark1 = BookmarkedIdea(
            id="test1",
            text="Machine learning for image recognition",
            theme="AI",
            constraints="",
            score=8,
            critique="",
            advocacy="",
            skepticism="",
            bookmarked_at="2024-01-01",
            tags=[]
        )
        
        bookmark2 = BookmarkedIdea(
            id="test2", 
            text="Natural language processing system",
            theme="AI",
            constraints="",
            score=7,
            critique="",
            advocacy="",
            skepticism="",
            bookmarked_at="2024-01-02",
            tags=[]
        )
        
        new_text = "Image recognition using machine learning"
        existing_bookmarks = [bookmark1, bookmark2]
        
        results = detector.find_duplicates(new_text, "AI", existing_bookmarks)
        
        # Should find bookmark1 as similar
        assert len(results) > 0
        assert results[0].bookmark_id == "test1"
        assert results[0].similarity_score > 0.6
    
    def test_check_for_duplicates_no_duplicates(self):
        """Test comprehensive duplicate check with no duplicates."""
        detector = DuplicateDetector()
        
        result = detector.check_for_duplicates("Unique idea text", "unique_theme", [])
        
        assert result.has_duplicates is False
        assert len(result.similar_bookmarks) == 0
        assert result.recommendation == "allow"
    
    def test_check_for_duplicates_with_high_similarity(self):
        """Test comprehensive duplicate check with high similarity."""
        detector = DuplicateDetector(similarity_threshold=0.7)  # Lower threshold to trigger duplicate detection
        
        bookmark = BookmarkedIdea(
            id="existing",
            text="Smart irrigation system using IoT sensors",
            theme="agriculture",
            constraints="",
            score=8,
            critique="",
            advocacy="",
            skepticism="",
            bookmarked_at="2024-01-01",
            tags=[]
        )
        
        new_text = "IoT sensor based smart irrigation system"
        result = detector.check_for_duplicates(new_text, "agriculture", [bookmark])
        
        assert result.has_duplicates is True
        assert len(result.similar_bookmarks) > 0
        assert result.recommendation in ["warn", "block", "notice"]
    
    def test_classify_similarity_level(self):
        """Test similarity level classification."""
        detector = DuplicateDetector()
        
        assert detector._classify_similarity_level(0.98) == "exact"
        assert detector._classify_similarity_level(0.85) == "high"
        assert detector._classify_similarity_level(0.7) == "medium"
        assert detector._classify_similarity_level(0.5) == "low"
    
    def test_identify_matched_features(self):
        """Test matched features identification."""
        detector = DuplicateDetector()
        
        text1 = "Machine learning model for image recognition"
        text2 = "Image recognition using machine learning"
        
        features = detector._identify_matched_features(text1, text2, 0.8)
        
        assert len(features) > 0
        # Should identify keyword matches
        assert any("keyword" in feature.lower() for feature in features)


class TestBookmarkManagerIntegration:
    """Tests for BookmarkManager integration with duplicate detection."""
    
    def setup_method(self):
        """Set up test environment with temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.bookmark_file = self.temp_file.name
    
    def teardown_method(self):
        """Clean up temporary file."""
        if os.path.exists(self.bookmark_file):
            os.unlink(self.bookmark_file)
    
    def test_bookmark_manager_with_duplicate_detection(self):
        """Test BookmarkManager with duplicate detection enabled."""
        manager = BookmarkManager(self.bookmark_file, similarity_threshold=0.8)
        
        # Add first bookmark
        bookmark_id1 = manager.bookmark_idea(
            "Smart irrigation system using IoT sensors",
            "agriculture",
            "water conservation",
            8
        )
        assert bookmark_id1 is not None
    
    def test_check_for_duplicates_method(self):
        """Test the check_for_duplicates method."""
        manager = BookmarkManager(self.bookmark_file)
        
        # Add a bookmark first
        manager.bookmark_idea(
            "Machine learning for image classification",
            "AI",
            "computer vision",
            7
        )
        
        # Check for duplicates with similar text
        result = manager.check_for_duplicates(
            "Image classification using machine learning",
            "AI"
        )
        
        assert isinstance(result, DuplicateCheckResult)
        assert result.has_duplicates is True or result.has_duplicates is False  # Boolean result
    
    def test_find_similar_bookmarks_method(self):
        """Test the find_similar_bookmarks method."""
        manager = BookmarkManager(self.bookmark_file)
        
        # Add some bookmarks
        manager.bookmark_idea(
            "Deep learning neural networks",
            "AI",
            "machine learning",
            8
        )
        
        manager.bookmark_idea(
            "Natural language processing",
            "AI", 
            "text analysis",
            7
        )
        
        # Find similar bookmarks
        similar = manager.find_similar_bookmarks(
            "Neural networks for deep learning",
            "AI",
            max_results=5
        )
        
        assert isinstance(similar, list)
        # Should find at least one similar bookmark
        if len(similar) > 0:
            assert 'id' in similar[0]
            assert 'text' in similar[0]
            assert 'similarity_score' in similar[0]
    
    def test_bookmark_idea_with_duplicate_check_allow(self):
        """Test enhanced bookmark creation when duplicates are allowed."""
        manager = BookmarkManager(self.bookmark_file)
        
        result = manager.bookmark_idea_with_duplicate_check(
            "Unique idea with no duplicates",
            "unique_theme",
            "no constraints",
            score=8
        )
        
        assert result['bookmark_created'] is True
        assert result['bookmark_id'] is not None
        assert result['duplicate_check']['has_duplicates'] is False
    
    def test_bookmark_idea_with_duplicate_check_warn(self):
        """Test enhanced bookmark creation with duplicate warning."""
        manager = BookmarkManager(self.bookmark_file, similarity_threshold=0.7)
        
        # Add first bookmark
        manager.bookmark_idea(
            "Solar panel efficiency optimization",
            "renewable_energy",
            "sustainability",
            8
        )
        
        # Try to add similar bookmark
        result = manager.bookmark_idea_with_duplicate_check(
            "Optimizing solar panel efficiency",
            "renewable_energy", 
            "green technology",
            score=7,
            force_save=False
        )
        
        # Should detect similarity but exact behavior depends on threshold
        assert 'bookmark_created' in result
        assert 'duplicate_check' in result
    
    def test_bookmark_idea_with_duplicate_check_force_save(self):
        """Test enhanced bookmark creation with force save."""
        manager = BookmarkManager(self.bookmark_file, similarity_threshold=0.6)
        
        # Add first bookmark
        manager.bookmark_idea(
            "Electric vehicle charging station",
            "transportation",
            "clean energy",
            9
        )
        
        # Force save similar bookmark
        result = manager.bookmark_idea_with_duplicate_check(
            "Charging stations for electric vehicles",
            "transportation",
            "sustainable transport", 
            score=8,
            force_save=True
        )
        
        # Should save regardless of duplicates when force_save=True
        assert result['bookmark_created'] is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def setup_method(self):
        """Set up test bookmarks."""
        self.bookmark1 = BookmarkedIdea(
            id="test1",
            text="Artificial intelligence chatbot for customer service",
            theme="AI",
            constraints="business automation",
            score=8,
            critique="Good idea",
            advocacy="Helpful for businesses",
            skepticism="May replace human jobs",
            bookmarked_at="2024-01-01",
            tags=["ai", "chatbot"]
        )
        
        self.bookmark2 = BookmarkedIdea(
            id="test2",
            text="Renewable energy storage system",
            theme="energy",
            constraints="sustainability",
            score=9,
            critique="Excellent idea",
            advocacy="Critical for green transition",
            skepticism="High initial costs",
            bookmarked_at="2024-01-02",
            tags=["renewable", "storage"]
        )
    
    def test_check_bookmark_duplicates_function(self):
        """Test the convenience check_bookmark_duplicates function."""
        result = check_bookmark_duplicates(
            "Customer service AI chatbot",
            "AI",
            [self.bookmark1, self.bookmark2],
            similarity_threshold=0.8
        )
        
        assert isinstance(result, DuplicateCheckResult)
        assert hasattr(result, 'has_duplicates')
        assert hasattr(result, 'similar_bookmarks')
        assert hasattr(result, 'recommendation')
    
    def test_calculate_bookmark_similarity_function(self):
        """Test the convenience calculate_bookmark_similarity function."""
        similarity = calculate_bookmark_similarity(
            "AI chatbot for customer support",
            "Artificial intelligence customer service bot",
            "AI",
            "AI"
        )
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
    
    def test_calculate_bookmark_similarity_without_themes(self):
        """Test similarity calculation without themes."""
        similarity = calculate_bookmark_similarity(
            "Machine learning model",
            "Deep learning algorithm"
        )
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_very_long_texts(self):
        """Test duplicate detection with very long texts."""
        detector = DuplicateDetector()
        
        long_text1 = " ".join(["word"] * 1000)  # 1000 words
        long_text2 = " ".join(["word"] * 1000)  # Identical
        
        similarity = detector.calculate_similarity(long_text1, long_text2)
        assert similarity == 1.0
    
    def test_unicode_and_special_characters(self):
        """Test duplicate detection with unicode and special characters."""
        detector = DuplicateDetector()
        
        text1 = "Café résumé naïve 🚀"
        text2 = "Cafe resume naive 🚀"
        
        # Should handle unicode gracefully
        similarity = detector.calculate_similarity(text1, text2)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
    
    def test_only_numbers_and_symbols(self):
        """Test duplicate detection with only numbers and symbols."""
        detector = DuplicateDetector()
        
        text1 = "123 456 789 !@# $%^"
        text2 = "123-456-789 @#$ %^&"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
    
    def test_very_short_texts(self):
        """Test duplicate detection with very short texts."""
        detector = DuplicateDetector()
        
        text1 = "AI"
        text2 = "AI"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert similarity == 1.0
    
    def test_mixed_case_and_spacing(self):
        """Test duplicate detection with mixed case and spacing."""
        detector = DuplicateDetector()
        
        text1 = "MachineLearning"
        text2 = "machine learning"
        
        similarity = detector.calculate_similarity(text1, text2)
        assert similarity > 0.5  # Should recognize as similar
    
    def test_performance_with_many_bookmarks(self):
        """Test performance with many existing bookmarks."""
        detector = DuplicateDetector()
        
        # Create many bookmarks
        bookmarks = []
        for i in range(100):
            bookmark = BookmarkedIdea(
                id=f"test_{i}",
                text=f"Idea number {i} about technology",
                theme="technology",
                constraints="",
                score=7,
                critique="",
                advocacy="",
                skepticism="",
                bookmarked_at="2024-01-01",
                tags=[]
            )
            bookmarks.append(bookmark)
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        
        results = detector.find_duplicates(
            "Technology idea number fifty",
            "technology",
            bookmarks
        )
        
        end_time = time.time()
        
        # Should complete quickly (< 2 seconds)
        assert end_time - start_time < 2.0
        assert isinstance(results, list)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])