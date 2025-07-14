"""Bookmark and Remix System.

This module implements a simple file-based bookmark system for saving
and managing ideas, with remix functionality for generating new ideas
based on saved ones.
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

try:
    from madspark.utils.utils.utils.constants import HIGH_SCORE_THRESHOLD, MAX_REMIX_BOOKMARKS
except ImportError:
    from constants import HIGH_SCORE_THRESHOLD, MAX_REMIX_BOOKMARKS

logger = logging.getLogger(__name__)


@dataclass
class BookmarkedIdea:
    """Container for a bookmarked idea with metadata."""
    id: str
    text: str
    theme: str
    constraints: str
    score: int
    critique: str
    advocacy: str
    skepticism: str
    bookmarked_at: str
    tags: List[str]


class BookmarkManager:
    """Manages bookmarked ideas with file-based storage."""
    
    def __init__(self, bookmark_file: str = "bookmarks.json"):
        """Initialize the bookmark manager.
        
        Args:
            bookmark_file: Path to the bookmark storage file
        """
        self.bookmark_file = bookmark_file
        self.bookmarks: Dict[str, BookmarkedIdea] = {}
        self._load_bookmarks()
    
    def _load_bookmarks(self):
        """Load bookmarks from file."""
        if os.path.exists(self.bookmark_file):
            try:
                with open(self.bookmark_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bookmarks = {
                        id: BookmarkedIdea(**bookmark_data) 
                        for id, bookmark_data in data.items()
                    }
                logger.info(f"Loaded {len(self.bookmarks)} bookmarks from {self.bookmark_file}")
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.error(f"Failed to load bookmarks: {e}")
                self.bookmarks = {}
        else:
            logger.info(f"No existing bookmark file found at {self.bookmark_file}")
    
    def _save_bookmarks(self):
        """Save bookmarks to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.bookmark_file) if os.path.dirname(self.bookmark_file) else '.', exist_ok=True)
            
            data = {id: asdict(bookmark) for id, bookmark in self.bookmarks.items()}
            with open(self.bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.bookmarks)} bookmarks to {self.bookmark_file}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save bookmarks: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a bookmark."""
        # Use UUID for guaranteed uniqueness
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars for readability
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"bookmark_{timestamp}_{unique_id}"
    
    def bookmark_idea(
        self, 
        idea_text: str, 
        theme: str, 
        constraints: str,
        score: int = 0,
        critique: str = "",
        advocacy: str = "",
        skepticism: str = "",
        tags: Optional[List[str]] = None
    ) -> str:
        """Bookmark an idea.
        
        Args:
            idea_text: The idea text to bookmark
            theme: Theme used to generate the idea
            constraints: Constraints used to generate the idea
            score: Critic score for the idea
            critique: Critic's feedback
            advocacy: Advocate's arguments
            skepticism: Skeptic's analysis
            tags: Optional tags for organization
            
        Returns:
            The bookmark ID
        """
        if tags is None:
            tags = []
            
        bookmark_id = self._generate_id()
        bookmark = BookmarkedIdea(
            id=bookmark_id,
            text=idea_text,
            theme=theme,
            constraints=constraints,
            score=score,
            critique=critique,
            advocacy=advocacy,
            skepticism=skepticism,
            bookmarked_at=datetime.now().isoformat(),
            tags=tags
        )
        
        self.bookmarks[bookmark_id] = bookmark
        self._save_bookmarks()
        
        logger.info(f"Bookmarked idea: {idea_text[:50]}... (ID: {bookmark_id})")
        return bookmark_id
    
    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove a bookmark.
        
        Args:
            bookmark_id: ID of the bookmark to remove
            
        Returns:
            True if bookmark was removed, False if not found
        """
        if bookmark_id in self.bookmarks:
            idea_text = self.bookmarks[bookmark_id].text
            del self.bookmarks[bookmark_id]
            self._save_bookmarks()
            logger.info(f"Removed bookmark {bookmark_id}: {idea_text[:50]}...")
            return True
        else:
            logger.warning(f"Bookmark {bookmark_id} not found")
            return False
    
    def get_bookmark(self, bookmark_id: str) -> Optional[BookmarkedIdea]:
        """Get a specific bookmark.
        
        Args:
            bookmark_id: ID of the bookmark to retrieve
            
        Returns:
            BookmarkedIdea if found, None otherwise
        """
        return self.bookmarks.get(bookmark_id)
    
    def list_bookmarks(self, tags: Optional[List[str]] = None) -> List[BookmarkedIdea]:
        """List all bookmarks, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            List of bookmarked ideas
        """
        bookmarks = list(self.bookmarks.values())
        
        if tags:
            bookmarks = [
                bookmark for bookmark in bookmarks
                if any(tag in bookmark.tags for tag in tags)
            ]
        
        # Sort by bookmark date (newest first)
        bookmarks.sort(key=lambda x: x.bookmarked_at, reverse=True)
        return bookmarks
    
    def search_bookmarks(self, query: str) -> List[BookmarkedIdea]:
        """Search bookmarks by text content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching bookmarked ideas
        """
        query_lower = query.lower()
        matches = []
        
        for bookmark in self.bookmarks.values():
            if (query_lower in bookmark.text.lower() or
                query_lower in bookmark.theme.lower() or
                query_lower in bookmark.constraints.lower()):
                matches.append(bookmark)
        
        # Sort by bookmark date (newest first)
        matches.sort(key=lambda x: x.bookmarked_at, reverse=True)
        return matches
    
    def get_remix_context(self, bookmark_ids: Optional[List[str]] = None) -> str:
        """Generate context for remixing based on bookmarked ideas.
        
        Args:
            bookmark_ids: Optional list of specific bookmark IDs to use.
                         If None, uses all bookmarks.
            
        Returns:
            Context string for idea generation
        """
        if bookmark_ids:
            bookmarks = [b for id in bookmark_ids if (b := self.get_bookmark(id))]
        else:
            bookmarks = sorted(self.bookmarks.values(), key=lambda b: b.bookmarked_at, reverse=True)[:MAX_REMIX_BOOKMARKS]
        
        if not bookmarks:
            return "No bookmarked ideas available for remix context."
        
        context_parts = [
            "Build upon or combine elements from these previously generated ideas:"
        ]
        
        for bookmark in bookmarks:  # Now properly sorted and limited
            context_parts.append(f"- {bookmark.text}")
            if bookmark.score > HIGH_SCORE_THRESHOLD:  # Highlight high-scoring ideas
                context_parts.append(f"  (High-rated idea with score {bookmark.score})")
        
        context_parts.append(
            "\nCreate new ideas that either improve upon these concepts, "
            "combine multiple elements, or take them in new directions."
        )
        
        return "\n".join(context_parts)


# Convenience functions for CLI usage
def bookmark_from_result(
    result: Dict[str, Any], 
    theme: str, 
    constraints: str, 
    tags: Optional[List[str]] = None,
    bookmark_file: str = "bookmarks.json"
) -> str:
    """Bookmark an idea from a workflow result.
    
    Args:
        result: Result dictionary from run_multistep_workflow
        theme: Theme used to generate the idea
        constraints: Constraints used
        tags: Optional tags
        bookmark_file: Bookmark storage file
        
    Returns:
        Bookmark ID
    """
    manager = BookmarkManager(bookmark_file)
    return manager.bookmark_idea(
        idea_text=result.get("idea", ""),
        theme=theme,
        constraints=constraints,
        score=result.get("initial_score", 0),
        critique=result.get("initial_critique", ""),
        advocacy=result.get("advocacy", ""),
        skepticism=result.get("skepticism", ""),
        tags=tags or []
    )


def list_bookmarks_cli(bookmark_file: str = "bookmarks.json") -> List[Dict[str, Any]]:
    """List bookmarks for CLI display.
    
    Args:
        bookmark_file: Bookmark storage file
        
    Returns:
        List of bookmark dictionaries
    """
    manager = BookmarkManager(bookmark_file)
    bookmarks = manager.list_bookmarks()
    return [asdict(bookmark) for bookmark in bookmarks]


def remix_with_bookmarks(
    theme: str,
    additional_constraints: str = "",
    bookmark_ids: Optional[List[str]] = None,
    bookmark_file: str = "bookmarks.json"
) -> str:
    """Generate remix context from bookmarks.
    
    Args:
        theme: New theme for remix
        additional_constraints: Additional constraints
        bookmark_ids: Optional specific bookmarks to use
        bookmark_file: Bookmark storage file
        
    Returns:
        Enhanced constraints with remix context
    """
    manager = BookmarkManager(bookmark_file)
    remix_context = manager.get_remix_context(bookmark_ids)
    
    combined_constraints = f"{additional_constraints}\n\n{remix_context}"
    return combined_constraints.strip()