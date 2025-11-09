"""Parsing strategy implementations.

This module implements the Strategy Pattern for JSON parsing with progressive
fallback strategies. Each strategy is independent and testable, making it easy
to add, remove, or reorder strategies.

Strategy Execution Order (in JsonParser):
1. DirectJsonStrategy - Parse as complete valid JSON
2. JsonArrayExtractionStrategy - Extract arrays with bracket matching
3. LineByLineStrategy - Parse each line separately
4. RegexObjectExtractionStrategy - Extract objects with regex
5. ScoreCommentExtractionStrategy - Legacy text format fallback
"""

from abc import ABC, abstractmethod
import json
import logging
import re
from typing import Any, Dict, List, Optional

from madspark.utils.json_parsing.telemetry import ParsingTelemetry
from madspark.utils.json_parsing import patterns

logger = logging.getLogger(__name__)


class ParsingStrategy(ABC):
    """Base class for JSON parsing strategies.

    Each strategy implements a different approach to extracting structured data
    from text. Strategies return None on failure, allowing the parser to try
    the next strategy in the chain.

    Attributes:
        name: Human-readable name for telemetry tracking
    """

    def __init__(self):
        """Initialize strategy with name for telemetry."""
        self.name = self.__class__.__name__.replace('Strategy', '')

    @abstractmethod
    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[Any]:
        """Attempt to parse text using this strategy.

        Args:
            text: Raw text to parse
            telemetry: Telemetry tracker for recording success/failure
            expected_count: Expected number of results (for fallback strategies)

        Returns:
            Parsed data structure (list, dict, etc.) or None if parsing failed
        """
        pass


class DirectJsonStrategy(ParsingStrategy):
    """Strategy 1: Direct JSON parsing.

    Attempts to parse the entire text as valid JSON using json.loads().
    This is the fastest strategy and should succeed ~80% of the time with
    well-formed LLM output.

    Returns:
        - List if text is a JSON array
        - Dict if text is a single JSON object
        - None if parsing fails
    """

    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[Any]:
        """Parse as complete JSON."""
        if not text or not text.strip():
            return None

        try:
            data = json.loads(text)
            telemetry.record_success(self.name, len(text))

            if isinstance(data, list):
                logger.debug(f"Parsed as JSON array with {len(data)} items")
                return data
            elif isinstance(data, dict):
                logger.debug("Parsed as single JSON object")
                return data
            else:
                # Unexpected type (string, number, etc.)
                return None

        except json.JSONDecodeError as e:
            telemetry.record_failure(self.name, str(e))
            return None


class JsonArrayExtractionStrategy(ParsingStrategy):
    """Strategy 2: Extract JSON arrays with bracket matching.

    Uses manual bracket counting to extract JSON arrays from text,
    even when surrounded by non-JSON content. Handles:
    - Nested arrays
    - Escaped characters in strings
    - Multiple arrays in same text

    Algorithm:
    1. Find opening bracket '['
    2. Count brackets while tracking string boundaries
    3. Extract when bracket count returns to zero
    4. Parse extracted array as JSON
    5. Return all dict items from all arrays

    Returns:
        List of dicts extracted from arrays, or None if no valid arrays found
    """

    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract arrays using bracket matching algorithm."""
        if not text or not text.strip():
            return None

        arrays_found = self._extract_json_arrays(text)
        results: List[Dict[str, Any]] = []

        for start_pos, end_pos, array_data in arrays_found:
            for item in array_data:
                if isinstance(item, dict):
                    results.append(item)

        if results:
            telemetry.record_success(self.name, len(text))
            logger.debug(f"Extracted {len(results)} items from JSON arrays")
            return results

        telemetry.record_failure(self.name, "No valid arrays found")
        return None

    def _extract_json_arrays(self, text: str) -> List[tuple]:
        """Extract JSON arrays from text with proper bracket matching.

        Returns:
            List of tuples: (start_position, end_position, parsed_array_data)
        """
        arrays_found = []
        array_start = text.find('[')

        while array_start != -1:
            # Try to find the matching closing bracket
            bracket_count = 0
            in_string = False
            escape_next = False
            pos = array_start

            while pos < len(text):
                char = text[pos]

                if escape_next:
                    escape_next = False
                elif char == '\\' and in_string:
                    escape_next = True
                elif char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # Found matching closing bracket
                            array_str = text[array_start:pos+1]
                            try:
                                array_data = json.loads(array_str)
                                if isinstance(array_data, list):
                                    arrays_found.append((array_start, pos+1, array_data))
                            except json.JSONDecodeError:
                                pass
                            break

                pos += 1

            # Look for next array after the current one's closing bracket
            if bracket_count == 0:
                array_start = text.find('[', pos + 1)
            else:
                array_start = text.find('[', array_start + 1)

        return arrays_found


class LineByLineStrategy(ParsingStrategy):
    """Strategy 3: Parse each line as separate JSON object.

    Useful when LLM outputs multiple JSON objects separated by newlines
    instead of as a proper JSON array.

    Algorithm:
    1. Split text into lines
    2. Try to parse each non-empty line as JSON
    3. Collect all successfully parsed dicts

    Returns:
        List of dicts, one per valid line, or None if no lines parse
    """

    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Parse each line as separate JSON object."""
        if not text or not text.strip():
            return None

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        results: List[Dict[str, Any]] = []

        for line in lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    results.append(obj)
            except json.JSONDecodeError:
                continue

        if results:
            telemetry.record_success(self.name, len(text))
            logger.debug(f"Parsed {len(results)} JSON objects line-by-line")
            return results

        telemetry.record_failure(self.name, "No valid JSON lines found")
        return None


class RegexObjectExtractionStrategy(ParsingStrategy):
    """Strategy 4: Extract JSON objects using regex patterns.

    Uses pre-compiled regex patterns to extract JSON object structures
    from text, even when mixed with non-JSON content. Handles:
    - Multi-line strings (with newline escaping)
    - Nested objects
    - Multiple objects in text

    Returns:
        List of dicts extracted by regex, or None if no objects found
    """

    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract objects using regex patterns."""
        if not text or not text.strip():
            return None

        results: List[Dict[str, Any]] = []

        # Use pre-compiled pattern for performance
        potential_jsons = patterns.JSON_OBJECT_PATTERN.findall(text)

        for json_str in potential_jsons:
            try:
                # First try direct parsing
                obj = json.loads(json_str)
                if isinstance(obj, dict):
                    results.append(obj)
            except json.JSONDecodeError:
                # If that fails, try to clean up multi-line strings
                try:
                    # Replace actual newlines in strings with escaped newlines
                    cleaned = patterns.NEWLINE_IN_STRING.sub(
                        lambda m: m.group(0).replace('\n', '\\n'),
                        json_str
                    )
                    obj = json.loads(cleaned)
                    if isinstance(obj, dict):
                        results.append(obj)
                except json.JSONDecodeError:
                    continue

        if results:
            telemetry.record_success(self.name, len(text))
            logger.debug(f"Extracted {len(results)} JSON objects using regex")
            return results

        telemetry.record_failure(self.name, "No valid objects found by regex")
        return None


class ScoreCommentExtractionStrategy(ParsingStrategy):
    """Strategy 5: Extract score/comment patterns (legacy fallback).

    Last-resort strategy for parsing text-based evaluation outputs.
    Uses multiple regex patterns to match various formats:
    - Standard: "Score: 8 Comment: text"
    - Narrative: "scores an 8", "give it a score of 7", etc.

    All patterns have ReDoS protection (character limits).

    Returns:
        - Dict with score and comment if expected_count is None
        - List of dicts if expected_count is provided
        - None if no pattern matches
    """

    def parse(
        self,
        text: str,
        telemetry: ParsingTelemetry,
        expected_count: Optional[int] = None
    ) -> Optional[Any]:
        """Extract score/comment using regex patterns."""
        if not text or not text.strip():
            return None

        results: List[Dict[str, Any]] = []

        # Try standard format first
        matches = patterns.SCORE_COMMENT_STANDARD.findall(text)
        for score_str, comment in matches:
            try:
                results.append({
                    "score": int(score_str),
                    "comment": comment.strip().strip('"\'')
                })
            except ValueError:
                continue

        # Try narrative patterns if standard didn't work
        if not results:
            for pattern in patterns.SCORE_NARRATIVE_PATTERNS:
                narrative_matches = pattern.findall(text)
                for score_str, comment in narrative_matches:
                    try:
                        results.append({
                            "score": int(score_str),
                            "comment": comment.strip().strip('"\'.')
                        })
                    except ValueError:
                        continue

        if results:
            telemetry.record_success(self.name, len(text))
            logger.debug(f"Extracted {len(results)} score/comment pairs")

            # Return based on expected_count
            if expected_count is None:
                return results[0] if len(results) == 1 else results
            else:
                # Pad or truncate to expected_count
                while len(results) < expected_count:
                    results.append({"score": 0, "comment": "Failed to parse evaluation"})
                return results[:expected_count]

        telemetry.record_failure(self.name, "No score/comment patterns matched")

        # If expected_count provided, return placeholders
        if expected_count and expected_count > 0:
            logger.warning(f"Creating {expected_count} placeholder entries")
            return [
                {"score": 0, "comment": "Failed to parse evaluation"}
                for _ in range(expected_count)
            ]

        return None
