"""Duplicate Detection System for Bookmarks.

This module implements sophisticated duplicate detection algorithms combining
lexical similarity (Jaccard) and semantic similarity to identify potential
duplicate bookmarks while avoiding false positives.
"""

import re
import hashlib
from typing import List, Set
from dataclasses import dataclass
import logging

from madspark.config.execution_constants import ThresholdConfig

try:
    from madspark.utils.models import BookmarkedIdea
except ImportError:
    from models import BookmarkedIdea

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of similarity comparison between two pieces of text."""

    bookmark_id: str
    similarity_score: float
    match_type: str  # 'exact', 'high', 'medium', 'low'
    matched_features: List[str]  # What caused the match


@dataclass
class DuplicateCheckResult:
    """Result of duplicate detection check."""

    has_duplicates: bool
    similar_bookmarks: List[SimilarityResult]
    similarity_threshold: float
    recommendation: str  # 'block', 'warn', 'allow'


class TextProcessor:
    """Text preprocessing utilities for similarity detection."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison by removing extra whitespace and standardizing case."""
        if not text:
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r"\s+", " ", text.lower().strip())

        # Remove common punctuation that doesn't affect meaning
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Remove extra spaces again after punctuation removal
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    @staticmethod
    def extract_keywords(text: str, min_word_length: int = 3) -> Set[str]:
        """Extract meaningful keywords from text for comparison."""
        normalized = TextProcessor.normalize_text(text)
        words = normalized.split()

        # Filter out short words and common stop words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "under",
            "within",
            "without",
            "this",
            "that",
            "these",
            "those",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "may",
            "might",
            "must",
            "can",
            "could",
        }

        keywords = {
            word
            for word in words
            if len(word) >= min_word_length and word not in stop_words
        }

        return keywords

    @staticmethod
    def create_text_fingerprint(text: str) -> str:
        """Create a hash-based fingerprint for exact duplicate detection."""
        normalized = TextProcessor.normalize_text(text)
        return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()


class SimilarityCalculator:
    """Implements various similarity calculation algorithms."""

    @staticmethod
    def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 1.0  # Both empty sets are identical

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def text_overlap_ratio(
        text1: str, text2: str, text1_clean: str = None, text2_clean: str = None
    ) -> float:
        """Calculate the ratio of overlapping characters between two texts."""
        if not text1 or not text2:
            return 0.0

        if text1_clean is None:
            text1_clean = TextProcessor.normalize_text(text1)
        if text2_clean is None:
            text2_clean = TextProcessor.normalize_text(text2)

        # For short texts, use character-level comparison
        if len(text1_clean) < 50 or len(text2_clean) < 50:
            # Simple character overlap for short texts
            set1 = set(text1_clean.replace(" ", ""))
            set2 = set(text2_clean.replace(" ", ""))
            return SimilarityCalculator.jaccard_similarity(set1, set2)

        # For longer texts, use word-level comparison
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        return SimilarityCalculator.jaccard_similarity(words1, words2)

    @staticmethod
    def semantic_similarity(
        text1: str,
        text2: str,
        keywords1: Set[str] = None,
        keywords2: Set[str] = None,
        text1_clean: str = None,
        text2_clean: str = None,
    ) -> float:
        """
        Calculate semantic similarity using keyword analysis and text structure.
        This is a lightweight alternative to embedding-based similarity.
        """
        if keywords1 is None:
            keywords1 = TextProcessor.extract_keywords(text1)
        if keywords2 is None:
            keywords2 = TextProcessor.extract_keywords(text2)

        if not keywords1 and not keywords2:
            if text1_clean is None:
                text1_clean = TextProcessor.normalize_text(text1)
            if text2_clean is None:
                text2_clean = TextProcessor.normalize_text(text2)
            return 1.0 if text1_clean == text2_clean else 0.0

        # Base similarity from keyword overlap
        keyword_similarity = SimilarityCalculator.jaccard_similarity(
            keywords1, keywords2
        )

        # Boost similarity if both texts have similar structure/length
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        min_len = min(len1, len2)
        length_similarity = min_len / max_len if max_len > 0 else 1.0

        # Combine keyword similarity with length similarity (weighted)
        combined_similarity = (keyword_similarity * 0.8) + (length_similarity * 0.2)

        return min(combined_similarity, 1.0)


class DuplicateDetector:
    """Main duplicate detection system for bookmarks."""

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize duplicate detector.

        Args:
            similarity_threshold: Threshold above which bookmarks are considered duplicates (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.exact_threshold = ThresholdConfig.EXACT_MATCH_THRESHOLD
        self.high_similarity_threshold = ThresholdConfig.HIGH_SIMILARITY_THRESHOLD
        self.medium_similarity_threshold = ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD

    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        theme1: str = "",
        theme2: str = "",
        text1_fingerprint: str = None,
        text1_keywords: Set[str] = None,
        text1_clean: str = None,
        theme1_clean: str = None,
    ) -> float:
        """
        Calculate comprehensive similarity between two bookmark texts.

        Args:
            text1: First text to compare
            text2: Second text to compare
            theme1: Theme/topic of first text (optional)
            theme2: Theme/topic of second text (optional)
            text1_fingerprint: Pre-calculated fingerprint for text1 (optional)
            text1_keywords: Pre-calculated keywords for text1 (optional)
            text1_clean: Pre-calculated normalized text for text1 (optional)
            theme1_clean: Pre-calculated normalized theme for theme1 (optional)

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0

        # Check for exact fingerprint match first
        t1_fp = (
            text1_fingerprint
            if text1_fingerprint is not None
            else TextProcessor.create_text_fingerprint(text1)
        )
        if t1_fp == TextProcessor.create_text_fingerprint(text2):
            return 1.0

        # Calculate different types of similarity
        semantic_score = SimilarityCalculator.semantic_similarity(
            text1, text2, keywords1=text1_keywords, text1_clean=text1_clean
        )
        overlap_score = SimilarityCalculator.text_overlap_ratio(
            text1, text2, text1_clean=text1_clean
        )

        # If themes provided, factor them in
        theme_bonus = 0.0
        if theme1 and theme2:
            theme_similarity = SimilarityCalculator.text_overlap_ratio(
                theme1, theme2, text1_clean=theme1_clean
            )
            # Themes matching adds a bonus to similarity
            theme_bonus = theme_similarity * 0.1

        # Weighted combination of similarity scores
        final_score = (semantic_score * 0.6) + (overlap_score * 0.4) + theme_bonus

        return min(final_score, 1.0)

    def find_duplicates(
        self, new_text: str, new_theme: str, existing_bookmarks: List[BookmarkedIdea]
    ) -> List[SimilarityResult]:
        """
        Find potential duplicates for a new bookmark text.

        Args:
            new_text: Text of the new bookmark
            new_theme: Theme of the new bookmark
            existing_bookmarks: List of existing bookmarks to compare against

        Returns:
            List of similar bookmarks with similarity scores
        """
        if not new_text or not existing_bookmarks:
            return []

        # Pre-calculate invariant features for new_text to avoid re-processing in loop
        new_text_fingerprint = TextProcessor.create_text_fingerprint(new_text)
        new_text_clean = TextProcessor.normalize_text(new_text)
        new_text_keywords = TextProcessor.extract_keywords(new_text)

        # Pre-calculate invariant features for new_theme
        new_theme_clean = TextProcessor.normalize_text(new_theme) if new_theme else ""

        similar_bookmarks = []

        for bookmark in existing_bookmarks:
            similarity = self.calculate_similarity(
                new_text,
                bookmark.text,
                new_theme,
                bookmark.topic,
                text1_fingerprint=new_text_fingerprint,
                text1_keywords=new_text_keywords,
                text1_clean=new_text_clean,
                theme1_clean=new_theme_clean,
            )

            if similarity >= self.medium_similarity_threshold:
                # Determine match type and features
                match_type = self._classify_similarity_level(similarity)
                matched_features = self._identify_matched_features(
                    new_text,
                    bookmark.text,
                    similarity,
                    text1_clean=new_text_clean,
                    text1_keywords=new_text_keywords,
                )

                result = SimilarityResult(
                    bookmark_id=bookmark.id,
                    similarity_score=round(similarity, 3),
                    match_type=match_type,
                    matched_features=matched_features,
                )

                similar_bookmarks.append(result)

        # Sort by similarity score (highest first)
        similar_bookmarks.sort(key=lambda x: x.similarity_score, reverse=True)

        return similar_bookmarks

    def check_for_duplicates(
        self, new_text: str, new_theme: str, existing_bookmarks: List[BookmarkedIdea]
    ) -> DuplicateCheckResult:
        """
        Perform comprehensive duplicate check for a new bookmark.

        Args:
            new_text: Text of the new bookmark
            new_theme: Theme of the new bookmark
            existing_bookmarks: List of existing bookmarks

        Returns:
            DuplicateCheckResult with recommendations
        """
        similar_bookmarks = self.find_duplicates(
            new_text, new_theme, existing_bookmarks
        )

        has_duplicates = any(
            result.similarity_score >= self.similarity_threshold
            for result in similar_bookmarks
        )

        # Determine recommendation based on highest similarity
        recommendation = "allow"
        if similar_bookmarks:
            highest_similarity = similar_bookmarks[0].similarity_score

            if highest_similarity >= self.exact_threshold:
                recommendation = "block"
            elif highest_similarity >= self.high_similarity_threshold:
                recommendation = "warn"
            elif highest_similarity >= self.medium_similarity_threshold:
                recommendation = "notice"

        return DuplicateCheckResult(
            has_duplicates=has_duplicates,
            similar_bookmarks=similar_bookmarks[:5],  # Limit to top 5 matches
            similarity_threshold=self.similarity_threshold,
            recommendation=recommendation,
        )

    def _classify_similarity_level(self, similarity: float) -> str:
        """Classify similarity score into categories."""
        if similarity >= self.exact_threshold:
            return "exact"
        elif similarity >= self.high_similarity_threshold:
            return "high"
        elif similarity >= self.medium_similarity_threshold:
            return "medium"
        else:
            return "low"

    def _identify_matched_features(
        self,
        text1: str,
        text2: str,
        similarity: float,
        text1_clean: str = None,
        text1_keywords: Set[str] = None,
    ) -> List[str]:
        """Identify what features caused the similarity match."""
        features = []

        if text1_clean is None:
            text1_clean = TextProcessor.normalize_text(text1)

        text2_clean = TextProcessor.normalize_text(text2)

        # Check for exact text match
        if text1_clean == text2_clean:
            features.append("identical_text")
            return features

        # Check keyword overlap
        if text1_keywords is None:
            keywords1 = TextProcessor.extract_keywords(text1)
        else:
            keywords1 = text1_keywords

        keywords2 = TextProcessor.extract_keywords(text2)
        keyword_overlap = len(keywords1.intersection(keywords2))

        if keyword_overlap >= 3:
            features.append(f"shared_keywords({keyword_overlap})")
        elif keyword_overlap >= 1:
            features.append(f"some_keywords({keyword_overlap})")

        # Check text length similarity
        len1, len2 = len(text1), len(text2)
        length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

        if length_ratio > 0.8:
            features.append("similar_length")

        # Check for common phrases (simple approach)
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        word_overlap_ratio = len(words1.intersection(words2)) / max(
            len(words1.union(words2)), 1
        )

        if word_overlap_ratio > 0.5:
            features.append("common_phrases")

        return features if features else ["general_similarity"]


# Convenience functions for integration
def check_bookmark_duplicates(
    text: str,
    theme: str,
    existing_bookmarks: List[BookmarkedIdea],
    similarity_threshold: float = 0.8,
) -> DuplicateCheckResult:
    """
    Convenience function to check for bookmark duplicates.

    Args:
        text: Bookmark text to check
        theme: Theme of the bookmark
        existing_bookmarks: Existing bookmarks to compare against
        similarity_threshold: Similarity threshold for duplicates

    Returns:
        DuplicateCheckResult with findings
    """
    detector = DuplicateDetector(similarity_threshold)
    return detector.check_for_duplicates(text, theme, existing_bookmarks)


def calculate_bookmark_similarity(
    text1: str, text2: str, theme1: str = "", theme2: str = ""
) -> float:
    """
    Convenience function to calculate similarity between two bookmark texts.

    Args:
        text1: First bookmark text
        text2: Second bookmark text
        theme1: First bookmark theme (optional)
        theme2: Second bookmark theme (optional)

    Returns:
        Similarity score between 0.0 and 1.0
    """
    detector = DuplicateDetector()
    return detector.calculate_similarity(text1, text2, theme1, theme2)
