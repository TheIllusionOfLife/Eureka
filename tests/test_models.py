"""Comprehensive tests for data models."""
import pytest
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict, fields

from madspark.utils.models import BookmarkedIdea


class TestBookmarkedIdea:
    """Test cases for BookmarkedIdea model."""
    
    def test_bookmarked_idea_creation(self):
        """Test creating BookmarkedIdea instance."""
        bookmark = BookmarkedIdea(
            id="bookmark_001",
            text="Revolutionary AI concept for automation",
            theme="AI Automation",
            constraints="Budget-friendly, scalable",
            score=85,
            critique="Innovative but needs refinement",
            advocacy="Strong market potential",
            skepticism="Implementation complexity",
            bookmarked_at="2025-07-22T10:00:00Z",
            tags=["ai", "automation", "favorite"]
        )
        
        assert bookmark.id == "bookmark_001"
        assert bookmark.score == 85
        assert "favorite" in bookmark.tags
        assert bookmark.bookmarked_at == "2025-07-22T10:00:00Z"
    
    def test_bookmarked_idea_with_empty_tags(self):
        """Test BookmarkedIdea with empty tags list."""
        bookmark = BookmarkedIdea(
            id="bookmark_002",
            text="Test idea",
            theme="Testing",
            constraints="None",
            score=50,
            critique="Average",
            advocacy="Some potential",
            skepticism="Limited scope",
            bookmarked_at="2025-07-22T11:00:00Z",
            tags=[]
        )
        
        assert bookmark.tags == []
        assert bookmark.score == 50
    
    def test_bookmarked_idea_serialization(self):
        """Test bookmark serialization for storage."""
        bookmark = BookmarkedIdea(
            id="bookmark_003",
            text="Test bookmark",
            theme="Test theme",
            constraints="Test constraints",
            score=75,
            critique="Good",
            advocacy="Positive",
            skepticism="Minor concerns",
            bookmarked_at="2025-07-22T12:00:00Z",
            tags=["test"]
        )
        
        # Serialize using asdict
        data = asdict(bookmark)
        assert data["text"] == "Test bookmark"
        assert data["score"] == 75
        assert data["bookmarked_at"] == "2025-07-22T12:00:00Z"
        
        # JSON serialization
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        
        assert loaded["text"] == bookmark.text
        assert loaded["score"] == bookmark.score
        assert loaded["bookmarked_at"] == bookmark.bookmarked_at
    
    def test_bookmarked_idea_with_long_text(self):
        """Test BookmarkedIdea with very long text."""
        long_text = "This is a very long idea " * 100
        bookmark = BookmarkedIdea(
            id="bookmark_004",
            text=long_text,
            theme="Long ideas",
            constraints="No length limit",
            score=60,
            critique="Too verbose",
            advocacy="Comprehensive",
            skepticism="Needs summarization",
            bookmarked_at="2025-07-22T13:00:00Z",
            tags=["long", "verbose"]
        )
        
        assert len(bookmark.text) > 1000
        assert bookmark.text == long_text
    
    def test_bookmarked_idea_with_special_characters(self):
        """Test BookmarkedIdea with special characters and unicode."""
        bookmark = BookmarkedIdea(
            id="bookmark_005",
            text="AI-powered task automation with émojis 🤖 and spëcial chars: café ☕",
            theme="Unicode Testing 多语言测试",
            constraints="Must handle unicode properly",
            score=90,
            critique="Excellent unicode support",
            advocacy="Global market ready",
            skepticism="Encoding issues?",
            bookmarked_at="2025-07-22T14:00:00Z",
            tags=["unicode", "测试", "🏷️"]
        )
        
        assert "🤖" in bookmark.text
        assert "café" in bookmark.text
        assert "测试" in bookmark.theme
        assert "🏷️" in bookmark.tags
        
        # Test JSON serialization with unicode
        data = asdict(bookmark)
        json_str = json.dumps(data, ensure_ascii=False)
        loaded = json.loads(json_str)
        
        assert loaded["text"] == bookmark.text
        assert loaded["theme"] == bookmark.theme
    
    def test_bookmarked_idea_field_types(self):
        """Test that BookmarkedIdea has correct field types."""
        # Get field information
        bookmark_fields = fields(BookmarkedIdea)
        
        # Check field names
        field_names = [f.name for f in bookmark_fields]
        expected_fields = [
            "id", "text", "theme", "constraints", "score",
            "critique", "advocacy", "skepticism", "bookmarked_at", "tags"
        ]
        for field in expected_fields:
            assert field in field_names
        
        # Check specific field types
        field_dict = {f.name: f for f in bookmark_fields}
        assert field_dict["tags"].type == List[str]
        assert field_dict["score"].type == int
        assert field_dict["id"].type == str
    
    def test_bookmarked_idea_equality(self):
        """Test BookmarkedIdea equality comparison."""
        bookmark1 = BookmarkedIdea(
            id="same_id",
            text="Idea 1",
            theme="Theme 1",
            constraints="Constraints 1",
            score=80,
            critique="Good",
            advocacy="Strong",
            skepticism="Minor",
            bookmarked_at="2025-07-22T15:00:00Z",
            tags=["tag1"]
        )
        
        bookmark2 = BookmarkedIdea(
            id="same_id",
            text="Idea 2",
            theme="Theme 2",
            constraints="Constraints 2",
            score=70,
            critique="Average",
            advocacy="Moderate",
            skepticism="Major",
            bookmarked_at="2025-07-22T16:00:00Z",
            tags=["tag2"]
        )
        
        bookmark3 = BookmarkedIdea(
            id="different_id",
            text="Idea 1",
            theme="Theme 1",
            constraints="Constraints 1",
            score=80,
            critique="Good",
            advocacy="Strong",
            skepticism="Minor",
            bookmarked_at="2025-07-22T15:00:00Z",
            tags=["tag1"]
        )
        
        # Dataclasses compare all fields by default
        assert bookmark1 != bookmark2  # Different content
        assert bookmark1 != bookmark3  # Different ID
        
        # Create identical bookmark
        bookmark4 = BookmarkedIdea(
            id="same_id",
            text="Idea 1",
            theme="Theme 1",
            constraints="Constraints 1",
            score=80,
            critique="Good",
            advocacy="Strong",
            skepticism="Minor",
            bookmarked_at="2025-07-22T15:00:00Z",
            tags=["tag1"]
        )
        assert bookmark1 == bookmark4  # Identical
    
    def test_bookmarked_idea_multiple_tags(self):
        """Test BookmarkedIdea with multiple tags."""
        tags = ["ai", "automation", "productivity", "innovation", "scalable", "enterprise"]
        bookmark = BookmarkedIdea(
            id="bookmark_006",
            text="Multi-tagged idea",
            theme="Tag testing",
            constraints="None",
            score=70,
            critique="Well categorized",
            advocacy="Easy to find",
            skepticism="Over-tagged?",
            bookmarked_at="2025-07-22T17:00:00Z",
            tags=tags
        )
        
        assert len(bookmark.tags) == 6
        assert all(tag in bookmark.tags for tag in tags)
        
        # Test tag operations
        assert "ai" in bookmark.tags
        assert "nonexistent" not in bookmark.tags
    
    def test_bookmarked_idea_edge_scores(self):
        """Test BookmarkedIdea with edge case scores."""
        # Minimum score
        bookmark_min = BookmarkedIdea(
            id="bookmark_007",
            text="Low score idea",
            theme="Testing",
            constraints="None",
            score=0,
            critique="Poor",
            advocacy="None",
            skepticism="Total",
            bookmarked_at="2025-07-22T18:00:00Z",
            tags=["low"]
        )
        assert bookmark_min.score == 0
        
        # Maximum reasonable score
        bookmark_max = BookmarkedIdea(
            id="bookmark_008",
            text="High score idea",
            theme="Testing",
            constraints="None",
            score=100,
            critique="Perfect",
            advocacy="Unanimous",
            skepticism="None",
            bookmarked_at="2025-07-22T19:00:00Z",
            tags=["high"]
        )
        assert bookmark_max.score == 100
        
        # Negative score (if allowed)
        bookmark_neg = BookmarkedIdea(
            id="bookmark_009",
            text="Negative score idea",
            theme="Testing",
            constraints="None",
            score=-10,
            critique="Invalid",
            advocacy="None",
            skepticism="Complete",
            bookmarked_at="2025-07-22T20:00:00Z",
            tags=["negative"]
        )
        assert bookmark_neg.score == -10