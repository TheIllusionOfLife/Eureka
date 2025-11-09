"""Tests for JSON parsing strategy implementations.

Following TDD: These tests are written BEFORE implementation.
They will fail until strategies.py is created.
"""

import pytest


class TestParsingStrategyBase:
    """Test the abstract base class for parsing strategies."""

    def test_strategy_base_is_abstract(self):
        """ParsingStrategy should be an abstract base class."""
        from madspark.utils.json_parsing.strategies import ParsingStrategy

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            ParsingStrategy()

    def test_strategy_has_parse_method(self):
        """Strategy must define parse() method."""
        from madspark.utils.json_parsing.strategies import ParsingStrategy
        import inspect

        # Check that parse is an abstract method
        assert hasattr(ParsingStrategy, 'parse')
        assert inspect.isabstract(ParsingStrategy)


class TestDirectJsonStrategy:
    """Test direct JSON parsing strategy."""

    def test_direct_json_parses_valid_json(self):
        """Should parse valid JSON directly."""
        from madspark.utils.json_parsing.strategies import DirectJsonStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = DirectJsonStrategy()
        telemetry = ParsingTelemetry()

        json_text = '{"key": "value", "num": 42}'
        result = strategy.parse(json_text, telemetry)

        assert result is not None
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_direct_json_parses_array(self):
        """Should parse JSON arrays."""
        from madspark.utils.json_parsing.strategies import DirectJsonStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = DirectJsonStrategy()
        telemetry = ParsingTelemetry()

        json_text = '[{"id": 1}, {"id": 2}]'
        result = strategy.parse(json_text, telemetry)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2

    def test_direct_json_returns_none_on_invalid(self):
        """Should return None for invalid JSON."""
        from madspark.utils.json_parsing.strategies import DirectJsonStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = DirectJsonStrategy()
        telemetry = ParsingTelemetry()

        invalid_text = '{"key": "value"'  # Missing closing brace
        result = strategy.parse(invalid_text, telemetry)

        assert result is None

    def test_direct_json_records_success_telemetry(self):
        """Should record telemetry on successful parse."""
        from madspark.utils.json_parsing.strategies import DirectJsonStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = DirectJsonStrategy()
        telemetry = ParsingTelemetry()

        json_text = '{"test": true}'
        strategy.parse(json_text, telemetry)

        assert "DirectJson" in telemetry.strategy_counts
        assert telemetry.strategy_counts["DirectJson"] == 1


class TestJsonArrayExtractionStrategy:
    """Test JSON array extraction with bracket matching."""

    def test_extracts_single_array(self):
        """Should extract array from text."""
        from madspark.utils.json_parsing.strategies import JsonArrayExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = JsonArrayExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Some text [{"id": 1}, {"id": 2}] more text'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2

    def test_extracts_nested_arrays(self):
        """Should handle nested array structures."""
        from madspark.utils.json_parsing.strategies import JsonArrayExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = JsonArrayExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = '[{"data": [1, 2, 3]}, {"data": [4, 5, 6]}]'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert len(result) == 2
        assert result[0]["data"] == [1, 2, 3]

    def test_handles_escaped_quotes_in_strings(self):
        """Should correctly handle escaped quotes within array strings."""
        from madspark.utils.json_parsing.strategies import JsonArrayExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = JsonArrayExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = '[{"text": "He said \\"hello\\""}]'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert 'hello' in result[0]["text"]

    def test_handles_nested_arrays_with_quotes(self):
        """Should handle nested arrays with quoted strings containing brackets."""
        from madspark.utils.json_parsing.strategies import JsonArrayExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = JsonArrayExtractionStrategy()
        telemetry = ParsingTelemetry()

        # Edge case: nested arrays with strings that look like JSON
        text = '[{"data": [1, 2], "note": "Values: [a, b, c]"}]'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert len(result) == 1
        assert result[0]["data"] == [1, 2]
        # String with brackets should be preserved
        assert result[0]["note"] == "Values: [a, b, c]"

    def test_returns_none_when_no_arrays(self):
        """Should return None if no valid arrays found."""
        from madspark.utils.json_parsing.strategies import JsonArrayExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = JsonArrayExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = '{"not": "an array"}'
        result = strategy.parse(text, telemetry)

        assert result is None


class TestLineByLineStrategy:
    """Test line-by-line JSON parsing strategy."""

    def test_parses_multiple_json_objects(self):
        """Should parse each line as separate JSON."""
        from madspark.utils.json_parsing.strategies import LineByLineStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = LineByLineStrategy()
        telemetry = ParsingTelemetry()

        text = '{"id": 1}\n{"id": 2}\n{"id": 3}'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3

    def test_skips_invalid_lines(self):
        """Should skip lines that aren't valid JSON."""
        from madspark.utils.json_parsing.strategies import LineByLineStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = LineByLineStrategy()
        telemetry = ParsingTelemetry()

        text = '{"id": 1}\nInvalid line\n{"id": 2}'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert len(result) == 2

    def test_ignores_empty_lines(self):
        """Should skip empty lines."""
        from madspark.utils.json_parsing.strategies import LineByLineStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = LineByLineStrategy()
        telemetry = ParsingTelemetry()

        text = '{"id": 1}\n\n\n{"id": 2}\n'
        result = strategy.parse(text, telemetry)

        assert len(result) == 2

    def test_returns_none_when_no_valid_json(self):
        """Should return None if no lines parse successfully."""
        from madspark.utils.json_parsing.strategies import LineByLineStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = LineByLineStrategy()
        telemetry = ParsingTelemetry()

        text = 'Not JSON\nAlso not JSON'
        result = strategy.parse(text, telemetry)

        assert result is None


class TestRegexObjectExtractionStrategy:
    """Test regex-based object extraction strategy."""

    def test_extracts_simple_object(self):
        """Should extract JSON object from text using regex."""
        from madspark.utils.json_parsing.strategies import RegexObjectExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = RegexObjectExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Some text {"key": "value"} more text'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_extracts_multiple_objects(self):
        """Should extract all JSON objects from text."""
        from madspark.utils.json_parsing.strategies import RegexObjectExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = RegexObjectExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = '{"id": 1} some text {"id": 2}'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert len(result) >= 2

    def test_handles_newlines_in_strings(self):
        """Should correctly handle newlines within JSON strings."""
        from madspark.utils.json_parsing.strategies import RegexObjectExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = RegexObjectExtractionStrategy()
        telemetry = ParsingTelemetry()

        # Object with multiline string value
        text = '{"text": "line1\\nline2"}'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert len(result) > 0

    def test_returns_none_when_no_objects(self):
        """Should return None if no objects found."""
        from madspark.utils.json_parsing.strategies import RegexObjectExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = RegexObjectExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Just plain text with no JSON'
        result = strategy.parse(text, telemetry)

        assert result is None


class TestScoreCommentExtractionStrategy:
    """Test legacy score/comment extraction strategy."""

    def test_extracts_standard_format(self):
        """Should parse 'Score: N Comment: text' format."""
        from madspark.utils.json_parsing.strategies import ScoreCommentExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = ScoreCommentExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Score: 8 Comment: This is a good idea.'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert isinstance(result, dict)
        assert result["score"] == 8
        assert "good idea" in result["comment"]

    def test_extracts_narrative_format(self):
        """Should parse narrative formats like 'scores an 8'."""
        from madspark.utils.json_parsing.strategies import ScoreCommentExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = ScoreCommentExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'This idea scores an 8 out of 10.'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert result["score"] == 8

    def test_case_insensitive_matching(self):
        """Should match regardless of case."""
        from madspark.utils.json_parsing.strategies import ScoreCommentExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = ScoreCommentExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'score: 7 critique: Needs improvement'
        result = strategy.parse(text, telemetry)

        assert result is not None
        assert result["score"] == 7

    def test_returns_none_when_no_pattern_matches(self):
        """Should return None if no score/comment pattern found."""
        from madspark.utils.json_parsing.strategies import ScoreCommentExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = ScoreCommentExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Just plain text with no score or comment'
        result = strategy.parse(text, telemetry)

        assert result is None

    def test_returns_list_when_expected_count_provided(self):
        """Should return list of results when expected_count is given."""
        from madspark.utils.json_parsing.strategies import ScoreCommentExtractionStrategy
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        strategy = ScoreCommentExtractionStrategy()
        telemetry = ParsingTelemetry()

        text = 'Score: 8 Comment: Good'
        result = strategy.parse(text, telemetry, expected_count=3)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3


class TestStrategyIntegration:
    """Integration tests for strategy usage patterns."""

    def test_strategies_return_consistent_types(self):
        """All strategies should return None or valid data structures."""
        from madspark.utils.json_parsing.strategies import (
            DirectJsonStrategy,
            JsonArrayExtractionStrategy,
            LineByLineStrategy,
            RegexObjectExtractionStrategy,
            ScoreCommentExtractionStrategy
        )
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        invalid_text = "Not parseable"

        strategies = [
            DirectJsonStrategy(),
            JsonArrayExtractionStrategy(),
            LineByLineStrategy(),
            RegexObjectExtractionStrategy(),
            ScoreCommentExtractionStrategy()
        ]

        for strategy in strategies:
            result = strategy.parse(invalid_text, telemetry)
            # Should return None for unparseable input
            assert result is None

    def test_strategies_work_in_fallback_chain(self):
        """Strategies should complement each other in fallback chain."""
        from madspark.utils.json_parsing.strategies import (
            DirectJsonStrategy,
            LineByLineStrategy
        )
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()

        # Text that DirectJson can't parse but LineByLine can
        text = '{"id": 1}\n{"id": 2}'

        # DirectJson should fail (not valid single JSON)
        direct = DirectJsonStrategy()
        result1 = direct.parse(text, telemetry)
        assert result1 is None

        # LineByLine should succeed
        line_by_line = LineByLineStrategy()
        result2 = line_by_line.parse(text, telemetry)
        assert result2 is not None
        assert len(result2) == 2
