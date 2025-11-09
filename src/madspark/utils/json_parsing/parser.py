"""Main JSON parser with fallback strategy chain.

This module provides the JsonParser class, which orchestrates multiple
parsing strategies in a progressive fallback chain. The parser tries
strategies from fastest to slowest until one succeeds.

Performance Characteristics:
- ~80% of inputs parse via DirectJsonStrategy (O(n) fast path)
- ~15% require fallback strategies (O(n) to O(n²))
- ~5% use legacy score/comment extraction (regex)

Example:
    >>> from madspark.utils.json_parsing.parser import JsonParser
    >>> parser = JsonParser()
    >>> result = parser.parse('[{"id": 1}, {"id": 2}]')
    >>> print(f"Parsed {len(result)} items")
    Parsed 2 items
"""

import logging
from typing import Any, Optional

from madspark.utils.json_parsing.strategies import (
    ParsingStrategy,
    DirectJsonStrategy,
    JsonArrayExtractionStrategy,
    LineByLineStrategy,
    RegexObjectExtractionStrategy,
    ScoreCommentExtractionStrategy,
)
from madspark.utils.json_parsing.telemetry import ParsingTelemetry

logger = logging.getLogger(__name__)


class JsonParser:
    """Orchestrates JSON parsing with progressive fallback strategies.

    The parser maintains a list of parsing strategies and tries them in order
    until one succeeds. Strategies are ordered from fastest/most-reliable to
    slowest/least-reliable.

    Strategy Execution Order:
    1. DirectJsonStrategy - Parse as complete JSON (fast path, ~80% success)
    2. JsonArrayExtractionStrategy - Extract arrays with bracket matching
    3. LineByLineStrategy - Parse newline-separated objects
    4. RegexObjectExtractionStrategy - Extract objects from mixed content
    5. ScoreCommentExtractionStrategy - Legacy text format (last resort)

    Attributes:
        strategies: List of ParsingStrategy instances in execution order
        telemetry: ParsingTelemetry instance for tracking strategy usage

    Example:
        >>> parser = JsonParser()
        >>> result = parser.parse('{"key": "value"}')
        >>> stats = parser.telemetry.get_stats()
        >>> print(f"Used {stats['DirectJson']} DirectJson parses")
    """

    def __init__(self):
        """Initialize parser with default strategy chain and telemetry."""
        # Initialize strategies in execution order (fast to slow)
        self.strategies = [
            DirectJsonStrategy(),
            JsonArrayExtractionStrategy(),
            LineByLineStrategy(),
            RegexObjectExtractionStrategy(),
            ScoreCommentExtractionStrategy(),
        ]

        # Initialize telemetry for tracking strategy effectiveness
        self.telemetry = ParsingTelemetry()

        logger.debug(f"JsonParser initialized with {len(self.strategies)} strategies")

    def parse(self, text: str, expected_count: Optional[int] = None) -> Any:
        """Parse JSON with fallback strategies.

        Tries each strategy in order until one returns a non-None result.
        Stops at the first successful strategy (no unnecessary work).

        Args:
            text: Raw text to parse (may contain JSON or be pure JSON)
            expected_count: Expected number of results (used for placeholder
                generation if all strategies fail)

        Returns:
            Parsed data structure:
            - List of dicts for array/multi-object results
            - Single dict for single object results
            - None if text is None/empty

        Note:
            If all strategies fail and expected_count is provided, the last
            strategy (ScoreCommentExtraction) will return placeholder data.

        Example:
            >>> parser = JsonParser()
            >>> # Valid JSON - uses DirectJson
            >>> parser.parse('[{"id": 1}]')
            [{'id': 1}]
            >>> # Mixed content - uses ArrayExtraction
            >>> parser.parse('Text [{"id": 2}] more text')
            [{'id': 2}]
            >>> # Legacy format - uses ScoreComment
            >>> parser.parse('Score: 8 Comment: Good')
            {'score': 8, 'comment': 'Good'}
        """
        # Handle None or empty input immediately
        if text is None or (isinstance(text, str) and not text.strip()):
            logger.debug("Empty or None input, returning None")
            return None

        # Try each strategy in order until one succeeds
        for strategy in self.strategies:
            result = strategy.parse(text, self.telemetry, expected_count)

            if result is not None:
                # Strategy succeeded - return result immediately
                logger.debug(
                    f"Parsing succeeded using {strategy.__class__.__name__}"
                )
                return result

        # All strategies failed
        logger.warning("All parsing strategies failed")
        return None
