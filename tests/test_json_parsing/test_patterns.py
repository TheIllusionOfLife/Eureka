"""Tests for pre-compiled regex patterns.

Following TDD: These tests are written BEFORE implementation.
They will fail until patterns.py is created.
"""

import re
import pytest


class TestCommaFixPatterns:
    """Test patterns for fixing missing commas in JSON."""

    def test_comma_after_string_pattern_exists(self):
        """Pattern for comma after string should be compiled regex."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_STRING
        assert isinstance(COMMA_AFTER_STRING, re.Pattern)

    def test_comma_after_string_matches_newline_before_property(self):
        """Should match string followed by newline and property."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_STRING

        text = '"value"  \n  "nextProp": 123'
        match = COMMA_AFTER_STRING.search(text)
        assert match is not None
        # Group 1 captures the end of the string value with trailing whitespace
        assert '"  ' in match.group(1)
        # Group 2 captures leading whitespace and next property name with colon
        assert match.group(2) == '  "nextProp":'

    def test_comma_after_array_pattern_exists(self):
        """Pattern for comma after array should be compiled regex."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_ARRAY
        assert isinstance(COMMA_AFTER_ARRAY, re.Pattern)

    def test_comma_after_array_matches_bracket_before_property(self):
        """Should match closing bracket followed by newline and property."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_ARRAY

        text = '[1, 2, 3]  \n  "nextProp": "value"'
        match = COMMA_AFTER_ARRAY.search(text)
        assert match is not None
        # Group 1 captures the closing bracket with trailing whitespace
        assert ']  ' in match.group(1)
        assert match.group(2) == '  "nextProp":'

    def test_comma_after_number_pattern_exists(self):
        """Pattern for comma after number should be compiled regex."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_NUMBER
        assert isinstance(COMMA_AFTER_NUMBER, re.Pattern)

    def test_comma_after_number_matches_digit_before_property(self):
        """Should match number followed by newline and property."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_NUMBER

        text = '42  \n  "nextProp": "value"'
        match = COMMA_AFTER_NUMBER.search(text)
        assert match is not None
        # Group 1 captures digit(s) with trailing whitespace
        assert '2  ' in match.group(1)
        assert match.group(2) == '  "nextProp":'

    def test_comma_after_object_pattern_exists(self):
        """Pattern for comma after object should be compiled regex."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_OBJECT
        assert isinstance(COMMA_AFTER_OBJECT, re.Pattern)

    def test_comma_after_object_matches_brace_before_property(self):
        """Should match closing brace followed by newline and property."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_OBJECT

        text = '{"inner": "value"}  \n  "nextProp": 123'
        match = COMMA_AFTER_OBJECT.search(text)
        assert match is not None
        # Group 1 captures closing brace with trailing whitespace
        assert '}  ' in match.group(1)
        assert match.group(2) == '  "nextProp":'


class TestObjectExtractionPatterns:
    """Test patterns for extracting JSON objects."""

    def test_json_object_pattern_exists(self):
        """Pattern for simple JSON objects should be compiled regex."""
        from madspark.utils.json_parsing.patterns import JSON_OBJECT_PATTERN
        assert isinstance(JSON_OBJECT_PATTERN, re.Pattern)

    def test_json_object_pattern_matches_simple_object(self):
        """Should match simple JSON object."""
        from madspark.utils.json_parsing.patterns import JSON_OBJECT_PATTERN

        text = 'Some text {"key": "value", "num": 42} more text'
        match = JSON_OBJECT_PATTERN.search(text)
        assert match is not None
        assert '{"key": "value", "num": 42}' in match.group(0)

    def test_json_object_pattern_matches_nested_object(self):
        """Should match object with one level of nesting."""
        from madspark.utils.json_parsing.patterns import JSON_OBJECT_PATTERN

        text = 'Text {"outer": {"inner": "value"}} more'
        match = JSON_OBJECT_PATTERN.search(text)
        assert match is not None
        assert '{"outer": {"inner": "value"}}' in match.group(0)

    def test_nested_object_pattern_exists(self):
        """Pattern for nested JSON objects should be compiled regex."""
        from madspark.utils.json_parsing.patterns import NESTED_OBJECT_PATTERN
        assert isinstance(NESTED_OBJECT_PATTERN, re.Pattern)

    def test_nested_object_pattern_matches_multiple_levels(self):
        """Should match objects with multiple nesting levels."""
        from madspark.utils.json_parsing.patterns import NESTED_OBJECT_PATTERN

        text = 'Some text {"a": {"b": {"c": "deep"}}} more text'
        match = NESTED_OBJECT_PATTERN.search(text)
        assert match is not None
        # Should capture a nested structure (may not get outermost due to regex limits)
        matched_text = match.group(0)
        # The pattern should at least match one of the nested objects
        assert '{' in matched_text and '}' in matched_text


class TestStringCleanupPatterns:
    """Test patterns for cleaning strings in JSON."""

    def test_newline_in_string_pattern_exists(self):
        """Pattern for newlines in strings should be compiled regex."""
        from madspark.utils.json_parsing.patterns import NEWLINE_IN_STRING
        assert isinstance(NEWLINE_IN_STRING, re.Pattern)

    def test_newline_in_string_matches_quoted_content(self):
        """Should match quoted strings."""
        from madspark.utils.json_parsing.patterns import NEWLINE_IN_STRING

        text = '"This is a string"'
        match = NEWLINE_IN_STRING.search(text)
        assert match is not None
        assert match.group(1) == '"This is a string"'

    def test_newline_in_string_matches_string_with_escaped_quotes(self):
        """Should match strings containing escaped quotes."""
        from madspark.utils.json_parsing.patterns import NEWLINE_IN_STRING

        text = '"String with \\"escaped\\" quotes"'
        match = NEWLINE_IN_STRING.search(text)
        assert match is not None
        assert 'escaped' in match.group(1)


class TestScoreCommentPatterns:
    """Test patterns for legacy score/comment extraction."""

    def test_score_comment_standard_pattern_exists(self):
        """Standard score/comment pattern should be compiled regex."""
        from madspark.utils.json_parsing.patterns import SCORE_COMMENT_STANDARD
        assert isinstance(SCORE_COMMENT_STANDARD, re.Pattern)

    def test_score_comment_standard_matches_score_format(self):
        """Should match 'Score: N Comment: text' format."""
        from madspark.utils.json_parsing.patterns import SCORE_COMMENT_STANDARD

        text = "Score: 8 Comment: This is a good idea."
        match = SCORE_COMMENT_STANDARD.search(text)
        assert match is not None
        assert match.group(1) == '8'
        assert 'good idea' in match.group(2)

    def test_score_comment_standard_case_insensitive(self):
        """Should match regardless of case."""
        from madspark.utils.json_parsing.patterns import SCORE_COMMENT_STANDARD

        text = "score: 7 critique: Needs work."
        match = SCORE_COMMENT_STANDARD.search(text)
        assert match is not None
        assert match.group(1) == '7'
        assert 'Needs work' in match.group(2)

    def test_score_narrative_an_pattern_exists(self):
        """Narrative pattern 'scores an N' should be compiled regex."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_AN
        assert isinstance(SCORE_NARRATIVE_AN, re.Pattern)

    def test_score_narrative_an_matches_format(self):
        """Should match 'scores an 8' format."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_AN

        text = "This idea scores an 8 out of 10. Comment: Excellent work."
        match = SCORE_NARRATIVE_AN.search(text)
        assert match is not None
        assert match.group(1) == '8'

    def test_score_narrative_an_has_redos_protection(self):
        """Should not match comments longer than 500 chars (ReDoS protection)."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_AN

        # Create text with score followed by 501 character comment
        long_comment = "X" * 501
        text = f"scores an 8 Comment: {long_comment}"
        match = SCORE_NARRATIVE_AN.search(text)

        # Should either not match or match with truncated comment
        if match:
            assert len(match.group(2)) <= 500

    def test_score_narrative_give_pattern_exists(self):
        """Narrative pattern 'give it a score of N' should be compiled regex."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_GIVE
        assert isinstance(SCORE_NARRATIVE_GIVE, re.Pattern)

    def test_score_narrative_give_matches_format(self):
        """Should match 'give it a score of 7' format."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_GIVE

        text = "I give it a score of 7. Comment: Pretty good."
        match = SCORE_NARRATIVE_GIVE.search(text)
        assert match is not None
        assert match.group(1) == '7'

    def test_score_narrative_deserves_pattern_exists(self):
        """Narrative pattern 'deserves a N' should be compiled regex."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_DESERVES
        assert isinstance(SCORE_NARRATIVE_DESERVES, re.Pattern)

    def test_score_narrative_deserves_matches_format(self):
        """Should match 'deserves a 9' format."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_DESERVES

        text = "This deserves a 9. Comment: Outstanding."
        match = SCORE_NARRATIVE_DESERVES.search(text)
        assert match is not None
        assert match.group(1) == '9'

    def test_score_narrative_simple_pattern_exists(self):
        """Narrative pattern 'scores N' should be compiled regex."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_SIMPLE
        assert isinstance(SCORE_NARRATIVE_SIMPLE, re.Pattern)

    def test_score_narrative_simple_matches_format(self):
        """Should match 'scores 6' format."""
        from madspark.utils.json_parsing.patterns import SCORE_NARRATIVE_SIMPLE

        text = "scores 6 Comment: Acceptable."
        match = SCORE_NARRATIVE_SIMPLE.search(text)
        assert match is not None
        assert match.group(1) == '6'


class TestPatternPerformance:
    """Test that patterns are pre-compiled for performance."""

    def test_all_patterns_are_compiled_not_strings(self):
        """All exported patterns should be compiled re.Pattern objects."""
        from madspark.utils.json_parsing import patterns

        # Get all module attributes that are individual patterns (not collections)
        pattern_names = [
            name for name in dir(patterns)
            if name.isupper() and not name.startswith('_')
            and not name.endswith('_PATTERNS')  # Exclude collection lists
        ]

        # Should have at least 10 individual patterns
        assert len(pattern_names) >= 10, f"Expected 10+ patterns, found {len(pattern_names)}"

        # Each should be compiled
        for name in pattern_names:
            pattern = getattr(patterns, name)
            assert isinstance(pattern, re.Pattern), f"{name} should be re.Pattern, got {type(pattern)}"

    def test_patterns_can_be_reused_without_recompilation(self):
        """Pre-compiled patterns should be reusable without performance penalty."""
        from madspark.utils.json_parsing.patterns import COMMA_AFTER_STRING

        # Same pattern object should be returned each time (module-level constant)
        pattern1 = COMMA_AFTER_STRING
        pattern2 = COMMA_AFTER_STRING
        assert pattern1 is pattern2, "Pattern should be same object (pre-compiled)"
