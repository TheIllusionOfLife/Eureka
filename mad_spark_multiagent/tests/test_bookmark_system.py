"""Tests for the bookmark system module."""
import pytest
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

from mad_spark_multiagent.bookmark_system import (
    BookmarkManager, 
    BookmarkedIdea, 
    bookmark_from_result,
    list_bookmarks_cli,
    remix_with_bookmarks
)


class TestBookmarkedIdea:
    """Test cases for BookmarkedIdea dataclass."""
    
    def test_bookmark_creation(self):
        """Test creating a bookmarked idea."""
        bookmark = BookmarkedIdea(
            id="test_id",
            text="Solar panels for homes",
            theme="Green energy",
            constraints="Budget-friendly",
            score=8,
            critique="Great idea",
            advocacy="Environmentally friendly",
            skepticism="Installation costs",
            bookmarked_at="2024-01-01T10:00:00",
            tags=["renewable", "energy"]
        )
        
        assert bookmark.id == "test_id"
        assert bookmark.text == "Solar panels for homes"
        assert bookmark.score == 8
        assert "renewable" in bookmark.tags


class TestBookmarkManager:
    """Test cases for BookmarkManager class."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = BookmarkManager(self.temp_file.name)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_bookmark_idea(self):
        """Test bookmarking an idea."""
        bookmark_id = self.manager.bookmark_idea(
            idea_text="Solar panels for homes",
            theme="Green energy",
            constraints="Budget-friendly",
            score=8,
            critique="Excellent idea",
            advocacy="Cost-effective",
            skepticism="Weather dependent",
            tags=["renewable"]
        )
        
        assert bookmark_id.startswith("bookmark_")
        assert bookmark_id in self.manager.bookmarks
        
        bookmark = self.manager.bookmarks[bookmark_id]
        assert bookmark.text == "Solar panels for homes"
        assert bookmark.theme == "Green energy"
        assert bookmark.score == 8
        assert "renewable" in bookmark.tags
    
    def test_remove_bookmark(self):
        """Test removing a bookmark."""
        # Add a bookmark
        bookmark_id = self.manager.bookmark_idea(
            idea_text="Test idea",
            theme="Test theme",
            constraints="Test constraints"
        )
        
        assert bookmark_id in self.manager.bookmarks
        
        # Remove it
        result = self.manager.remove_bookmark(bookmark_id)
        assert result is True
        assert bookmark_id not in self.manager.bookmarks
        
        # Try to remove non-existent bookmark
        result = self.manager.remove_bookmark("non_existent")
        assert result is False
    
    def test_get_bookmark(self):
        """Test retrieving a specific bookmark."""
        bookmark_id = self.manager.bookmark_idea(
            idea_text="Test idea",
            theme="Test theme",
            constraints="Test constraints"
        )
        
        bookmark = self.manager.get_bookmark(bookmark_id)
        assert bookmark is not None
        assert bookmark.text == "Test idea"
        
        # Test non-existent bookmark
        bookmark = self.manager.get_bookmark("non_existent")
        assert bookmark is None
    
    def test_list_bookmarks(self):
        """Test listing all bookmarks."""
        # Add multiple bookmarks
        id1 = self.manager.bookmark_idea("Idea 1", "Theme 1", "Constraints 1", tags=["tag1"])
        id2 = self.manager.bookmark_idea("Idea 2", "Theme 2", "Constraints 2", tags=["tag2"])
        id3 = self.manager.bookmark_idea("Idea 3", "Theme 3", "Constraints 3", tags=["tag1", "tag2"])
        
        # List all bookmarks
        all_bookmarks = self.manager.list_bookmarks()
        assert len(all_bookmarks) == 3
        
        # List bookmarks by tag
        tag1_bookmarks = self.manager.list_bookmarks(tags=["tag1"])
        assert len(tag1_bookmarks) == 2
        
        tag2_bookmarks = self.manager.list_bookmarks(tags=["tag2"])
        assert len(tag2_bookmarks) == 2
    
    def test_search_bookmarks(self):
        """Test searching bookmarks by text content."""
        # Add bookmarks with different content
        self.manager.bookmark_idea("Solar energy system", "Green tech", "Residential")
        self.manager.bookmark_idea("Wind turbine design", "Green tech", "Industrial")
        self.manager.bookmark_idea("Battery storage solution", "Energy storage", "Grid scale")
        
        # Search by idea text
        results = self.manager.search_bookmarks("solar")
        assert len(results) == 1
        assert "Solar energy system" in results[0].text
        
        # Search by theme
        results = self.manager.search_bookmarks("green")
        assert len(results) == 2
        
        # Search by constraints
        results = self.manager.search_bookmarks("industrial")
        assert len(results) == 1
        
        # Search with no matches
        results = self.manager.search_bookmarks("quantum")
        assert len(results) == 0
    
    def test_get_remix_context(self):
        """Test generating remix context from bookmarks."""
        # Add some bookmarks
        self.manager.bookmark_idea("Solar panels", "Energy", "Residential", score=8)
        self.manager.bookmark_idea("Wind turbines", "Energy", "Commercial", score=6)
        self.manager.bookmark_idea("Battery storage", "Storage", "Grid", score=9)
        
        # Test getting context from all bookmarks
        context = self.manager.get_remix_context()
        assert "Solar panels" in context
        assert "Wind turbines" in context
        assert "Battery storage" in context
        assert "Build upon or combine" in context
        assert "High-rated idea with score 9" in context  # High score highlight
        
        # Test getting context from specific bookmarks
        bookmark_ids = list(self.manager.bookmarks.keys())[:2]
        context = self.manager.get_remix_context(bookmark_ids)
        assert "Solar panels" in context or "Wind turbines" in context
    
    def test_persistence(self):
        """Test that bookmarks are saved and loaded correctly."""
        # Add a bookmark
        bookmark_id = self.manager.bookmark_idea(
            idea_text="Persistent idea",
            theme="Persistence test",
            constraints="Must persist"
        )
        
        # Create new manager with same file
        new_manager = BookmarkManager(self.temp_file.name)
        
        # Check that bookmark was loaded
        assert bookmark_id in new_manager.bookmarks
        bookmark = new_manager.get_bookmark(bookmark_id)
        assert bookmark.text == "Persistent idea"
    
    def test_empty_file_handling(self):
        """Test handling of non-existent bookmark file."""
        # Use a non-existent file
        non_existent_file = "/tmp/non_existent_bookmarks.json"
        manager = BookmarkManager(non_existent_file)
        
        # Should start with empty bookmarks
        assert len(manager.bookmarks) == 0
        
        # Should be able to add bookmarks
        bookmark_id = manager.bookmark_idea("Test", "Test", "Test")
        assert bookmark_id in manager.bookmarks
        
        # Clean up
        if os.path.exists(non_existent_file):
            os.unlink(non_existent_file)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_bookmark_from_result(self):
        """Test bookmarking from workflow result."""
        result = {
            "idea": "Solar energy system",
            "initial_score": 8,
            "initial_critique": "Great potential",
            "advocacy": "Environmentally friendly",
            "skepticism": "High upfront costs"
        }
        
        bookmark_id = bookmark_from_result(
            result=result,
            theme="Green energy",
            constraints="Budget-friendly",
            tags=["renewable", "energy"],
            bookmark_file=self.temp_file.name
        )
        
        assert bookmark_id.startswith("bookmark_")
        
        # Verify bookmark was saved
        manager = BookmarkManager(self.temp_file.name)
        bookmark = manager.get_bookmark(bookmark_id)
        assert bookmark.text == "Solar energy system"
        assert bookmark.score == 8
        assert "renewable" in bookmark.tags
    
    def test_list_bookmarks_cli(self):
        """Test CLI bookmark listing function."""
        # Add some bookmarks first
        manager = BookmarkManager(self.temp_file.name)
        manager.bookmark_idea("Idea 1", "Theme 1", "Constraints 1")
        manager.bookmark_idea("Idea 2", "Theme 2", "Constraints 2")
        
        # Test CLI listing
        bookmarks = list_bookmarks_cli(self.temp_file.name)
        assert len(bookmarks) == 2
        assert all(isinstance(bookmark, dict) for bookmark in bookmarks)
        assert bookmarks[0]['text'] in ["Idea 1", "Idea 2"]
    
    def test_remix_with_bookmarks(self):
        """Test remix context generation."""
        # Add some bookmarks
        manager = BookmarkManager(self.temp_file.name)
        id1 = manager.bookmark_idea("Solar panels", "Energy", "Residential")
        id2 = manager.bookmark_idea("Wind turbines", "Energy", "Commercial")
        
        # Test remix with all bookmarks
        constraints = remix_with_bookmarks(
            theme="Renewable energy",
            additional_constraints="Must be scalable",
            bookmark_file=self.temp_file.name
        )
        
        assert "Must be scalable" in constraints
        assert "Solar panels" in constraints
        assert "Wind turbines" in constraints
        
        # Test remix with specific bookmarks
        constraints = remix_with_bookmarks(
            theme="Renewable energy",
            additional_constraints="Must be affordable",
            bookmark_ids=[id1],
            bookmark_file=self.temp_file.name
        )
        
        assert "Must be affordable" in constraints
        assert "Solar panels" in constraints
        # Should not contain wind turbines since we only specified id1
    
    def test_empty_bookmarks_remix(self):
        """Test remix with no bookmarks."""
        constraints = remix_with_bookmarks(
            theme="Test theme",
            additional_constraints="Test constraints",
            bookmark_file=self.temp_file.name
        )
        
        assert "Test constraints" in constraints
        assert "No bookmarked ideas available" in constraints