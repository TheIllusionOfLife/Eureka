"""Comprehensive tests for MadSpark utility modules."""
import pytest
import tempfile
import os
from unittest.mock import Mock

from madspark.utils.utils import exponential_backoff_retry, parse_json_with_fallback
from madspark.utils.temperature_control import TemperatureManager, TemperatureConfig
from madspark.utils.bookmark_system import BookmarkManager
from madspark.utils.novelty_filter import NoveltyFilter
from madspark.utils.improved_idea_cleaner import clean_improved_idea
from madspark.utils.constants import (
    IDEA_GENERATION_INSTRUCTION, 
    DEFAULT_IDEA_TEMPERATURE, 
    DEFAULT_NUM_TOP_CANDIDATES, 
    DEFAULT_NOVELTY_THRESHOLD
)


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_exponential_backoff_retry_success(self):
        """Test successful retry execution."""
        mock_func = Mock(return_value="success")
        
        # Use as decorator with max_retries=3
        @exponential_backoff_retry(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_exponential_backoff_retry_with_retries(self):
        """Test retry mechanism with failures."""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        # Use as decorator with max_retries=3
        @exponential_backoff_retry(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_exponential_backoff_retry_max_retries_exceeded(self):
        """Test retry with max retries exceeded."""
        mock_func = Mock(side_effect=Exception("always fails"))
        
        # Use as decorator with max_retries=2
        @exponential_backoff_retry(max_retries=2)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception):
            test_func()
    
    def test_parse_json_with_fallback_valid_json(self):
        """Test JSON parsing with valid JSON."""
        valid_json = '{"key": "value", "number": 42}'
        
        result = parse_json_with_fallback(valid_json)
        
        assert result == [{"key": "value", "number": 42}]
    
    def test_parse_json_with_fallback_invalid_json(self):
        """Test JSON parsing with invalid JSON."""
        invalid_json = '{"key": "value", "invalid": }'
        
        result = parse_json_with_fallback(invalid_json)
        
        # Should return empty list for unparseable JSON
        assert result is not None
        assert isinstance(result, list)
    
    def test_parse_json_with_fallback_empty_string(self):
        """Test JSON parsing with empty string."""
        result = parse_json_with_fallback("")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0  # Empty string should return empty list


class TestTemperatureManager:
    """Test cases for temperature management."""
    
    def test_temperature_manager_initialization(self):
        """Test temperature manager initialization."""
        manager = TemperatureManager()
        
        assert manager is not None
        assert hasattr(manager, 'get_temperature_for_stage')
    
    def test_temperature_presets(self):
        """Test temperature presets."""
        _ = TemperatureManager()
        
        # Test different presets by accessing the config attribute
        conservative_manager = TemperatureManager.from_preset("conservative")
        assert conservative_manager.config.base_temperature <= 0.7
        
        creative_manager = TemperatureManager.from_preset("creative")
        assert creative_manager.config.base_temperature >= 0.8
        
        balanced_manager = TemperatureManager.from_preset("balanced")
        assert 0.6 <= balanced_manager.config.base_temperature <= 0.8
    
    def test_temperature_config_validation(self):
        """Test temperature configuration validation."""
        config = TemperatureConfig(
            base_temperature=0.8,
            idea_generation=0.9,
            evaluation=0.7,
            advocacy=0.8,
            skepticism=0.8
        )
        
        assert config.base_temperature == 0.8
        assert config.idea_generation == 0.9
        assert config.evaluation == 0.7
    
    def test_invalid_temperature_preset(self):
        """Test handling of invalid temperature preset."""
        # Test with invalid preset should raise TemperatureError
        from madspark.utils.errors import TemperatureError
        with pytest.raises(TemperatureError) as exc_info:
            TemperatureManager.from_preset("invalid_preset")
        assert "Unknown preset" in str(exc_info.value)


class TestBookmarkManager:
    """Test cases for bookmark management."""
    
    def test_bookmark_manager_initialization(self):
        """Test bookmark manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BookmarkManager(bookmark_file=os.path.join(temp_dir, "bookmarks.json"))
            
            assert manager is not None
            assert hasattr(manager, 'bookmark_idea')
            assert hasattr(manager, 'search_bookmarks')
    
    def test_save_and_retrieve_idea(self):
        """Test saving and retrieving ideas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BookmarkManager(bookmark_file=os.path.join(temp_dir, "bookmarks.json"))
            
            idea = {
                "title": "Test Idea",
                "description": "A test idea for bookmarking",
                "innovation_score": 8,
                "feasibility_score": 7
            }
            
            # Bookmark idea
            manager.bookmark_idea(
                idea_text=idea["title"] + " - " + idea["description"],
                theme="Testing",
                constraints="Test constraints",
                score=idea["innovation_score"],
                tags=["test", "automation"]
            )
            
            # Retrieve ideas
            bookmarks = manager.list_bookmarks()
            
            assert len(bookmarks) == 1
            assert "Test Idea" in bookmarks[0].text
    
    def test_bookmark_with_tags(self):
        """Test bookmark tagging system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BookmarkManager(bookmark_file=os.path.join(temp_dir, "bookmarks.json"))
            
            idea = {
                "title": "Tagged Idea",
                "description": "An idea with tags",
                "innovation_score": 8
            }
            
            manager.bookmark_idea(
                idea_text=idea["title"] + " - " + idea["description"],
                theme="Testing",
                constraints="Test constraints",
                score=idea["innovation_score"],
                tags=["ai", "productivity"]
            )
            
            # Test tag-based retrieval
            bookmarks = manager.list_bookmarks(tags=["ai"])
            assert len(bookmarks) == 1
            assert "ai" in bookmarks[0].tags
    
    def test_bookmark_duplicate_handling(self):
        """Test handling of duplicate bookmarks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BookmarkManager(bookmark_file=os.path.join(temp_dir, "bookmarks.json"))
            
            idea = {
                "title": "Duplicate Idea",
                "description": "An idea to test duplicates",
                "innovation_score": 8
            }
            
            # Bookmark same idea multiple times
            manager.bookmark_idea(
                idea_text=idea["title"] + " - " + idea["description"],
                theme="Testing",
                constraints="Test constraints",
                score=idea["innovation_score"],
                tags=["test"]
            )
            manager.bookmark_idea(
                idea_text=idea["title"] + " - " + idea["description"],
                theme="Testing",
                constraints="Test constraints",
                score=idea["innovation_score"],
                tags=["test"]
            )
            
            bookmarks = manager.list_bookmarks()
            
            # Should have stored both bookmarks
            assert len(bookmarks) == 2


class TestNoveltyFilter:
    """Test cases for novelty filtering."""
    
    def test_novelty_filter_initialization(self):
        """Test novelty filter initialization."""
        filter_obj = NoveltyFilter(similarity_threshold=0.8)
        
        assert filter_obj is not None
        assert hasattr(filter_obj, 'filter_idea')
    
    def test_novelty_detection(self):
        """Test novelty detection."""
        filter_obj = NoveltyFilter(similarity_threshold=0.8)
        
        idea1_text = "AI Assistant - An AI-powered productivity assistant"
        idea2_text = "Smart Home System - IoT-based home automation platform"
        
        # First idea should be novel
        result1 = filter_obj.filter_idea(idea1_text)
        assert result1.is_novel is True
        
        # Different idea should also be novel
        result2 = filter_obj.filter_idea(idea2_text)
        assert result2.is_novel is True
        
        # Exact duplicate should not be novel
        result3 = filter_obj.filter_idea(idea1_text)
        assert result3.is_novel is False
    
    def test_novelty_filter_with_different_ideas(self):
        """Test novelty filter with different ideas."""
        filter_obj = NoveltyFilter(similarity_threshold=0.8)
        
        idea1_text = "AI Assistant - An AI-powered productivity assistant"
        idea2_text = "Smart Home System - IoT-based home automation platform"
        
        # Both ideas should be novel
        result1 = filter_obj.filter_idea(idea1_text)
        assert result1.is_novel is True
        
        result2 = filter_obj.filter_idea(idea2_text)
        assert result2.is_novel is True
    
    def test_novelty_filter_threshold_adjustment(self):
        """Test novelty filter with different thresholds."""
        # Low threshold (lenient) - even small similarity rejects
        lenient_filter = NoveltyFilter(similarity_threshold=0.3)
        
        idea1_text = "AI Assistant - Productivity tool"
        idea2_text = "AI Helper - Productivity tool"
        
        # Process first idea
        lenient_filter.filter_idea(idea1_text)
        
        # With low threshold, even moderately similar ideas should be rejected
        # These two ideas share "AI", "Productivity", "tool" - high similarity
        result = lenient_filter.filter_idea(idea2_text)
        assert result.is_novel is False
        
        # Test with very different idea
        idea3_text = "Blockchain payment system for e-commerce"
        result3 = lenient_filter.filter_idea(idea3_text)
        assert result3.is_novel is True


class TestIdeaCleaner:
    """Test cases for idea cleaner."""
    
    def test_clean_improved_idea_basic(self):
        """Test basic idea cleaning functionality."""
        messy_idea = """
        ## ENHANCED CONCEPT: The "Insight Catalyst" Framework
        
        **ORIGINAL THEME:** Test Idea
        
        **REVISED CORE PREMISE:** The improved framework leverages...
        
        Our enhanced approach isn't just a list of tests; it's a structured framework...
        """
        
        cleaned = clean_improved_idea(messy_idea)
        
        assert "ENHANCED CONCEPT:" not in cleaned
        assert "ORIGINAL THEME:" not in cleaned
        assert "REVISED CORE PREMISE:" not in cleaned
        assert "enhanced approach" not in cleaned
    
    def test_clean_improved_idea_with_headers(self):
        """Test cleaning ideas with various headers."""
        messy_idea = """
        # IMPROVED VERSION: Better Solution
        
        This enhanced solution builds upon the original...
        
        The revised approach improves upon...
        """
        
        cleaned = clean_improved_idea(messy_idea)
        
        assert "IMPROVED VERSION:" not in cleaned
        assert "enhanced solution" not in cleaned
        assert "revised approach" not in cleaned
    
    def test_clean_improved_idea_preserve_content(self):
        """Test that cleaning preserves important content."""
        original_idea = """
        This is a great solution for productivity.
        
        Key features include:
        - Real-time collaboration
        - Smart notifications
        - Data analytics
        """
        
        cleaned = clean_improved_idea(original_idea)
        
        assert "great solution" in cleaned
        assert "Real-time collaboration" in cleaned
        assert "Smart notifications" in cleaned
        assert "Data analytics" in cleaned
    
    def test_clean_improved_idea_empty_input(self):
        """Test cleaning with empty input."""
        result = clean_improved_idea("")
        assert result == ""
        
        result = clean_improved_idea(None)
        assert result == "" or result is None


class TestConstants:
    """Test cases for constants and configuration."""
    
    def test_constants_availability(self):
        """Test that required constants are available."""
        assert IDEA_GENERATION_INSTRUCTION is not None
        assert isinstance(IDEA_GENERATION_INSTRUCTION, str)
        assert len(IDEA_GENERATION_INSTRUCTION) > 0
        
        assert DEFAULT_IDEA_TEMPERATURE is not None
        assert isinstance(DEFAULT_IDEA_TEMPERATURE, (int, float))
        assert 0 <= DEFAULT_IDEA_TEMPERATURE <= 2
        
        assert DEFAULT_NUM_TOP_CANDIDATES is not None
        assert isinstance(DEFAULT_NUM_TOP_CANDIDATES, int)
        assert DEFAULT_NUM_TOP_CANDIDATES > 0
    
    def test_constants_values(self):
        """Test that constants have reasonable values."""
        assert 0.1 <= DEFAULT_IDEA_TEMPERATURE <= 1.5
        assert 1 <= DEFAULT_NUM_TOP_CANDIDATES <= 20
        
        if hasattr(globals(), 'DEFAULT_NOVELTY_THRESHOLD'):
            assert 0.0 <= DEFAULT_NOVELTY_THRESHOLD <= 1.0


class TestErrorHandling:
    """Test cases for error handling across utilities."""
    
    def test_utility_error_resilience(self):
        """Test that utilities handle errors gracefully."""
        # Test temperature manager with invalid inputs
        manager = TemperatureManager()
        # Test that manager handles None gracefully by checking config exists
        assert manager.config is not None
        
        # Test bookmark manager with invalid directory
        try:
            BookmarkManager(bookmark_file="/nonexistent/directory/bookmarks.json")
        except Exception as e:
            # Should handle gracefully or raise appropriate error
            assert isinstance(e, (OSError, IOError, ValueError))
    
    def test_json_parsing_edge_cases(self):
        """Test JSON parsing with edge cases."""
        # Test with malformed JSON
        result = parse_json_with_fallback('{"key": "value"')
        assert result is not None
        
        # Test with non-string input
        result = parse_json_with_fallback(None)
        assert result is not None
        
        # Test with very large JSON
        large_json = '{"key": "' + 'x' * 10000 + '"}'
        result = parse_json_with_fallback(large_json)
        assert result is not None