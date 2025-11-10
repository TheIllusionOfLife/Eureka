"""Shared data models for MadSpark utilities.

This module contains shared data structures used across different
utility modules to avoid circular imports.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class BookmarkedIdea:
    """Container for a bookmarked idea with metadata."""
    id: str
    text: str
    topic: str
    context: str
    score: int
    critique: str
    advocacy: str
    skepticism: str
    bookmarked_at: str
    tags: List[str]