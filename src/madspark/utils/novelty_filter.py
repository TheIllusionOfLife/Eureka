"""Novelty Filter Module.

This module implements a lightweight Tier0 novelty filter to detect similar
or duplicate ideas before expensive LLM evaluation. It uses multiple techniques
including hash-based similarity, keyword overlap, and semantic similarity.
"""
import hashlib
import re
from typing import List, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FilteredIdea:
    """Container for an idea with novelty metadata."""
    text: str
    is_novel: bool
    similarity_score: float
    similar_to: str = ""  # Text of similar idea if not novel


class NoveltyFilter:
    """Lightweight novelty filter for idea deduplication."""
    
    _STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                   'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was',
                   'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
                   'did', 'will', 'would', 'should', 'could', 'can', 'may',
                   'might', 'this', 'that', 'these', 'those'}
    
    def __init__(self, similarity_threshold: float = 0.8):
        """Initialize the novelty filter.
        
        Args:
            similarity_threshold: Threshold for considering ideas similar (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: Set[str] = set()
        self.processed_ideas: List[str] = []
        self.processed_keywords: List[Set[str]] = []
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase, remove extra whitespace, and basic punctuation
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for exact duplicate detection."""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()
    
    def _get_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text."""
        normalized = self._normalize_text(text)
        # Simple keyword extraction - remove common words
        words = set(normalized.split())
        return words - self._STOP_WORDS
    
    def _calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on keyword overlap."""
        keywords1 = self._get_keywords(text1)
        keywords2 = self._get_keywords(text2)
        
        return self._calculate_similarity_from_sets(keywords1, keywords2)

    def _calculate_similarity_from_sets(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """Calculate similarity based on pre-computed keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0
            
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _find_most_similar(self, text: str, text_keywords: Set[str] = None) -> Tuple[float, str]:
        """Find the most similar existing idea."""
        if not self.processed_ideas:
            return 0.0, ""
            
        max_similarity = 0.0
        most_similar = ""
        
        # Calculate keywords once if not provided
        if text_keywords is None:
            text_keywords = self._get_keywords(text)

        # Use parallel lists if available (should always be synchronized)
        if len(self.processed_keywords) == len(self.processed_ideas):
            for existing_idea, existing_keywords in zip(self.processed_ideas, self.processed_keywords):
                similarity = self._calculate_similarity_from_sets(text_keywords, existing_keywords)
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar = existing_idea
        else:
            # Fallback if lists are out of sync (should not happen)
            logger.warning("NoveltyFilter lists out of sync, falling back to slow comparison")
            for existing_idea in self.processed_ideas:
                similarity = self._calculate_keyword_similarity(text, existing_idea)
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar = existing_idea
                
        return max_similarity, most_similar
    
    def filter_idea(self, idea_text: str) -> FilteredIdea:
        """Filter a single idea for novelty.
        
        Args:
            idea_text: The idea text to filter
            
        Returns:
            FilteredIdea with novelty assessment
        """
        if not idea_text or not idea_text.strip():
            return FilteredIdea(
                text=idea_text,
                is_novel=False,
                similarity_score=1.0,
                similar_to="Empty or invalid idea"
            )
        
        # Check for exact duplicates
        text_hash = self._get_text_hash(idea_text)
        if text_hash in self.seen_hashes:
            logger.debug(f"Exact duplicate detected: {idea_text[:50]}...")
            return FilteredIdea(
                text=idea_text,
                is_novel=False,
                similarity_score=1.0,
                similar_to="Exact duplicate"
            )
        
        # Calculate keywords for the new idea
        idea_keywords = self._get_keywords(idea_text)

        # Check for semantic similarity
        max_similarity, most_similar = self._find_most_similar(idea_text, idea_keywords)
        
        is_novel = max_similarity < self.similarity_threshold
        
        # Store for future comparisons
        self.seen_hashes.add(text_hash)
        if is_novel:
            self.processed_ideas.append(idea_text)
            self.processed_keywords.append(idea_keywords)
        
        logger.debug(
            f"Idea novelty check: {idea_text[:50]}... "
            f"(novel: {is_novel}, similarity: {max_similarity:.2f})"
        )
        
        return FilteredIdea(
            text=idea_text,
            is_novel=is_novel,
            similarity_score=max_similarity,
            similar_to=most_similar if not is_novel else ""
        )
    
    def filter_ideas(self, ideas: List[str]) -> List[FilteredIdea]:
        """Filter a list of ideas for novelty.
        
        Args:
            ideas: List of idea texts to filter
            
        Returns:
            List of FilteredIdea objects with novelty assessment
        """
        filtered_ideas = []
        
        for idea in ideas:
            filtered_idea = self.filter_idea(idea)
            filtered_ideas.append(filtered_idea)
            
        novel_count = sum(1 for idea in filtered_ideas if idea.is_novel)
        logger.info(
            f"Novelty filter processed {len(ideas)} ideas: "
            f"{novel_count} novel, {len(ideas) - novel_count} duplicates/similar"
        )
        
        return filtered_ideas
    
    def get_novel_ideas(self, ideas: List[str]) -> List[str]:
        """Get only the novel ideas from a list.
        
        Args:
            ideas: List of idea texts to filter
            
        Returns:
            List of novel idea texts only
        """
        filtered_ideas = self.filter_ideas(ideas)
        return [idea.text for idea in filtered_ideas if idea.is_novel]
    
    def reset(self):
        """Reset the filter state."""
        self.seen_hashes.clear()
        self.processed_ideas.clear()
        self.processed_keywords.clear()
        logger.debug("Novelty filter state reset")


# Convenience function for one-time filtering
def filter_ideas_for_novelty(
    ideas: List[str], 
    similarity_threshold: float = 0.8
) -> Tuple[List[str], List[FilteredIdea]]:
    """Filter ideas for novelty using default settings.
    
    Args:
        ideas: List of idea texts to filter
        similarity_threshold: Threshold for similarity detection
        
    Returns:
        Tuple of (novel_ideas_only, all_filtered_ideas_with_metadata)
    """
    filter_instance = NoveltyFilter(similarity_threshold)
    filtered_ideas = filter_instance.filter_ideas(ideas)
    novel_ideas = [idea.text for idea in filtered_ideas if idea.is_novel]
    
    return novel_ideas, filtered_ideas