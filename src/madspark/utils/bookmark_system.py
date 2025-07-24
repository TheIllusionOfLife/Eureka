"""Bookmark and Remix System with Duplicate Detection.

This module implements a file-based bookmark system for saving
and managing ideas, with remix functionality and comprehensive
duplicate detection to prevent saving similar bookmarks.
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import logging

try:
    from madspark.utils.constants import HIGH_SCORE_THRESHOLD, MAX_REMIX_BOOKMARKS
    from madspark.utils.models import BookmarkedIdea
    from madspark.utils.duplicate_detector import DuplicateDetector, DuplicateCheckResult
except ImportError:
    from constants import HIGH_SCORE_THRESHOLD, MAX_REMIX_BOOKMARKS
    from models import BookmarkedIdea
    from duplicate_detector import DuplicateDetector, DuplicateCheckResult

logger = logging.getLogger(__name__)


class BookmarkManager:
    """Manages bookmarked ideas with file-based storage and duplicate detection."""
    
    def __init__(self, bookmark_file: str = "examples/data/bookmarks.json", similarity_threshold: float = 0.8):
        """Initialize the bookmark manager.
        
        Args:
            bookmark_file: Path to the bookmark storage file
            similarity_threshold: Threshold for duplicate detection (0.0-1.0)
        """
        self.bookmark_file = bookmark_file
        self.bookmarks: Dict[str, BookmarkedIdea] = {}
        self.duplicate_detector = DuplicateDetector(similarity_threshold)
        self._load_bookmarks()
    
    def _load_bookmarks(self):
        """Load bookmarks from file."""
        if os.path.exists(self.bookmark_file):
            try:
                with open(self.bookmark_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bookmarks = {
                        bookmark_id: BookmarkedIdea(**bookmark_data) 
                        for bookmark_id, bookmark_data in data.items()
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
    
    def check_for_duplicates(
        self, 
        idea_text: str, 
        theme: str,
        exclude_bookmark_id: Optional[str] = None
    ) -> DuplicateCheckResult:
        """Check if a bookmark idea would be a duplicate.
        
        Args:
            idea_text: The idea text to check for duplicates
            theme: Theme/topic of the idea
            exclude_bookmark_id: Optional bookmark ID to exclude from comparison
            
        Returns:
            DuplicateCheckResult with similarity findings
        """
        existing_bookmarks = []
        for bookmark in self.bookmarks.values():
            # Skip the bookmark being updated (for edit scenarios)
            if exclude_bookmark_id and bookmark.id == exclude_bookmark_id:
                continue
            existing_bookmarks.append(bookmark)
        
        return self.duplicate_detector.check_for_duplicates(
            idea_text, theme, existing_bookmarks
        )
    
    def find_similar_bookmarks(
        self, 
        idea_text: str, 
        theme: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find bookmarks similar to the given text.
        
        Args:
            idea_text: Text to find similar bookmarks for
            theme: Theme of the idea
            max_results: Maximum number of results to return
            
        Returns:
            List of similar bookmark information with similarity scores
        """
        existing_bookmarks = list(self.bookmarks.values())
        similar_results = self.duplicate_detector.find_duplicates(
            idea_text, theme, existing_bookmarks
        )
        
        # Convert to user-friendly format
        similar_bookmarks = []
        for result in similar_results[:max_results]:
            bookmark = self.get_bookmark(result.bookmark_id)
            if bookmark:
                similar_bookmarks.append({
                    'id': result.bookmark_id,
                    'text': bookmark.text,
                    'theme': bookmark.theme,
                    'score': bookmark.score,
                    'similarity_score': result.similarity_score,
                    'match_type': result.match_type,
                    'matched_features': result.matched_features,
                    'bookmarked_at': bookmark.bookmarked_at
                })
        
        return similar_bookmarks
    
    def bookmark_idea_with_duplicate_check(
        self,
        idea_text: str,
        theme: str,
        constraints: str,
        score: int = 0,
        critique: str = "",
        advocacy: str = "",
        skepticism: str = "",
        tags: Optional[List[str]] = None,
        force_save: bool = False
    ) -> Dict[str, Any]:
        """Bookmark an idea with comprehensive duplicate checking.
        
        Args:
            idea_text: The idea text to bookmark
            theme: Theme used to generate the idea
            constraints: Constraints used to generate the idea
            score: Critic score for the idea
            critique: Critic's feedback
            advocacy: Advocate's arguments
            skepticism: Skeptic's analysis
            tags: Optional tags for organization
            force_save: If True, save even if duplicates are found
            
        Returns:
            Dictionary with bookmark result and duplicate information
        """
        if tags is None:
            tags = []
        
        # Check for duplicates first
        duplicate_check = self.check_for_duplicates(idea_text, theme)
        
        result = {
            'duplicate_check': {
                'has_duplicates': duplicate_check.has_duplicates,
                'similar_count': len(duplicate_check.similar_bookmarks),
                'recommendation': duplicate_check.recommendation,
                'similarity_threshold': duplicate_check.similarity_threshold
            },
            'similar_bookmarks': [],
            'bookmark_created': False,
            'bookmark_id': None,
            'message': ''
        }
        
        # Add similar bookmark details
        for similar in duplicate_check.similar_bookmarks:
            bookmark = self.get_bookmark(similar.bookmark_id)
            if bookmark:
                result['similar_bookmarks'].append({
                    'id': similar.bookmark_id,
                    'text': bookmark.text[:200] + '...' if len(bookmark.text) > 200 else bookmark.text,
                    'theme': bookmark.theme,
                    'similarity_score': similar.similarity_score,
                    'match_type': similar.match_type
                })
        
        # Decide whether to save based on duplicate check and force_save flag
        should_save = True
        if duplicate_check.recommendation == "block" and not force_save:
            should_save = False
            result['message'] = "Bookmark appears to be a duplicate of existing content. Use force_save=True to save anyway."
        elif duplicate_check.recommendation == "warn" and not force_save:
            should_save = False
            result['message'] = "Similar bookmark found. Please review or use force_save=True to save anyway."
        
        if should_save or force_save:
            # Save the bookmark
            bookmark_id = self.bookmark_idea(
                idea_text, theme, constraints, score, 
                critique, advocacy, skepticism, tags
            )
            result['bookmark_created'] = True
            result['bookmark_id'] = bookmark_id
            
            if duplicate_check.has_duplicates:
                result['message'] = f"Bookmark saved despite {len(duplicate_check.similar_bookmarks)} similar bookmark(s) found."
            else:
                result['message'] = "Bookmark saved successfully."
        
        return result
    
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
    bookmark_file: str = "examples/data/bookmarks.json"
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


def list_bookmarks_cli(bookmark_file: str = "examples/data/bookmarks.json") -> List[Dict[str, Any]]:
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
    bookmark_file: str = "examples/data/bookmarks.json"
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