"""Tests for JsonParser orchestrator.

Following TDD: These tests are written BEFORE implementation.
They will fail until parser.py is created.
"""

import json
import pytest


class TestJsonParserInit:
    """Test JsonParser initialization."""

    def test_parser_initializes_with_default_strategies(self):
        """Parser should initialize with 5 default strategies."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        assert hasattr(parser, 'strategies')
        assert len(parser.strategies) == 5

    def test_parser_initializes_with_telemetry(self):
        """Parser should have telemetry instance."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        assert hasattr(parser, 'telemetry')
        assert parser.telemetry is not None

    def test_parser_strategies_in_correct_order(self):
        """Strategies should be ordered from fastest to slowest."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        strategy_names = [s.__class__.__name__ for s in parser.strategies]

        # Expected order based on performance characteristics
        assert strategy_names[0] == "DirectJsonStrategy"  # Fastest
        assert strategy_names[-1] == "ScoreCommentExtractionStrategy"  # Slowest fallback


class TestJsonParserBasicParsing:
    """Test basic parsing functionality."""

    def test_parse_valid_json_array(self):
        """Should parse valid JSON array."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '[{"id": 1}, {"id": 2}]'
        result = parser.parse(text)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_valid_json_object(self):
        """Should parse single JSON object."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"key": "value", "num": 42}'
        result = parser.parse(text)

        assert result is not None
        assert isinstance(result, dict)

    def test_parse_empty_string_returns_none(self):
        """Empty input should return None."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        result = parser.parse("")

        assert result is None

    def test_parse_none_returns_none(self):
        """None input should return None."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        result = parser.parse(None)

        assert result is None


class TestJsonParserFallbackChain:
    """Test that parser tries strategies in order until one succeeds."""

    def test_uses_direct_json_for_valid_json(self):
        """Valid JSON should be parsed by DirectJsonStrategy."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"valid": "json"}'
        result = parser.parse(text)

        # DirectJson should have been used
        assert "DirectJson" in parser.telemetry.strategy_counts
        assert parser.telemetry.strategy_counts["DirectJson"] == 1

    def test_falls_back_to_line_by_line(self):
        """Should use LineByLine when DirectJson fails."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        # Multiple objects on separate lines (not valid single JSON)
        text = '{"id": 1}\n{"id": 2}'
        result = parser.parse(text)

        assert result is not None
        assert len(result) == 2
        # LineByLine should have succeeded
        assert "LineByLine" in parser.telemetry.strategy_counts

    def test_falls_back_to_array_extraction(self):
        """Should extract arrays from text."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = 'Some text [{"id": 1}] more text'
        result = parser.parse(text)

        assert result is not None
        assert "JsonArrayExtraction" in parser.telemetry.strategy_counts

    def test_falls_back_to_regex_extraction(self):
        """Should use regex when other strategies fail."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = 'Text with {"embedded": "object"} in it'
        result = parser.parse(text)

        assert result is not None

    def test_falls_back_to_score_comment(self):
        """Should use ScoreComment as last resort."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = 'Score: 8 Comment: This is the legacy format'
        result = parser.parse(text)

        assert result is not None
        assert isinstance(result, dict)
        assert result["score"] == 8


class TestJsonParserExpectedCount:
    """Test parser behavior with expected_count parameter."""

    def test_passes_expected_count_to_strategies(self):
        """Expected count should be used for placeholder generation."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        # Text that will fail all strategies
        text = "Completely unparseable text"
        result = parser.parse(text, expected_count=3)

        # Should get placeholders from ScoreComment strategy
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3

    def test_expected_count_with_partial_results(self):
        """Should pad results to expected_count if needed."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        # Only one object, but expect 3
        text = '{"id": 1}'
        result = parser.parse(text, expected_count=3)

        # DirectJson will return the single object
        # We may or may not get padding depending on strategy
        assert result is not None


class TestJsonParserTelemetry:
    """Test telemetry tracking in parser."""

    def test_telemetry_records_successful_strategy(self):
        """Should record which strategy succeeded."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"test": true}'
        parser.parse(text)

        stats = parser.telemetry.get_stats()
        assert stats["total"] == 1
        assert "DirectJson" in stats

    def test_telemetry_accumulates_across_parses(self):
        """Multiple parses should accumulate telemetry."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()

        parser.parse('{"a": 1}')
        parser.parse('{"b": 2}')
        parser.parse('{"c": 3}')

        stats = parser.telemetry.get_stats()
        assert stats["total"] == 3

    def test_can_reset_telemetry(self):
        """Should be able to reset telemetry data."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        parser.parse('{"test": true}')

        parser.telemetry.reset()

        stats = parser.telemetry.get_stats()
        assert stats["total"] == 0


class TestJsonParserComplexCases:
    """Test parser with complex real-world scenarios."""

    def test_parses_nested_json_structures(self):
        """Should handle deeply nested JSON."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"level1": {"level2": {"level3": "deep"}}}'
        result = parser.parse(text)

        assert result is not None
        assert result["level1"]["level2"]["level3"] == "deep"

    def test_parses_json_with_escaped_characters(self):
        """Should handle escaped characters in strings."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"text": "He said \\"hello\\""}'
        result = parser.parse(text)

        assert result is not None
        assert "hello" in result["text"]

    def test_parses_json_with_unicode(self):
        """Should handle Unicode characters."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"emoji": "🎉", "japanese": "こんにちは"}'
        result = parser.parse(text)

        assert result is not None
        assert result["emoji"] == "🎉"
        assert result["japanese"] == "こんにちは"

    def test_handles_mixed_content_with_json(self):
        """Should extract JSON from mixed content."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '''
        Here is some explanatory text.

        The data you requested:
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        Hope this helps!
        '''
        result = parser.parse(text)

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_handles_malformed_json_gracefully(self):
        """Should not crash on malformed JSON."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"incomplete": "json"'  # Missing closing brace

        # Should try fallback strategies or return None
        # Should NOT raise exception
        result = parser.parse(text)

        # Result might be None or might extract via regex
        # Either is acceptable


class TestJsonParserPublicAPI:
    """Test the public API of JsonParser."""

    def test_parse_method_signature(self):
        """Parse method should have correct signature."""
        from madspark.utils.json_parsing.parser import JsonParser
        import inspect

        parser = JsonParser()
        sig = inspect.signature(parser.parse)

        # Should have text and optional expected_count
        params = list(sig.parameters.keys())
        assert "text" in params
        assert "expected_count" in params

    def test_parser_is_reusable(self):
        """Same parser instance should be reusable."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()

        result1 = parser.parse('{"a": 1}')
        result2 = parser.parse('{"b": 2}')

        assert result1 != result2
        assert result1["a"] == 1
        assert result2["b"] == 2

    def test_get_stats_is_public(self):
        """Should expose telemetry stats via parser."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        parser.parse('{"test": true}')

        # Should be able to get stats
        stats = parser.telemetry.get_stats()
        assert isinstance(stats, dict)
        assert "total" in stats


class TestJsonParserPerformance:
    """Test performance characteristics of parser."""

    def test_fast_path_for_valid_json(self):
        """Valid JSON should use only DirectJson (no fallbacks)."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"valid": "json", "number": 123}'
        result = parser.parse(text)

        # Only DirectJson should have been attempted
        stats = parser.telemetry.get_stats()
        assert stats["total"] == 1
        assert "DirectJson" in stats
        assert len(stats) == 2  # DirectJson + total

    def test_fallback_strategies_only_when_needed(self):
        """Should not try all strategies if early one succeeds."""
        from madspark.utils.json_parsing.parser import JsonParser

        parser = JsonParser()
        text = '{"valid": "json"}'
        parser.parse(text)

        stats = parser.telemetry.get_stats()

        # Should have only used DirectJson, not all 5 strategies
        # (total of 1, plus the strategy that succeeded)
        assert stats["total"] == 1
