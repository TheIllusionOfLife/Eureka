"""Tests for batch JSON parsing with fallback strategies."""
import pytest
from madspark.utils.utils import parse_batch_json_with_fallback

class TestBatchJsonParsing:
    """Test suite for parse_batch_json_with_fallback utility."""

    def test_valid_json(self):
        """Strategy 1: Test with perfectly valid JSON list."""
        valid_json = '[{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]'
        result = parse_batch_json_with_fallback(valid_json)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["name"] == "Item 2"

    @pytest.mark.parametrize("json_snippet, expected_key, expected_value", [
        (
            '[\n  {\n    "key1": "value1"\n    "key2": "value2"\n  }\n]',
            "key1", "value1"
        ),
        (
            '[\n  {\n    "list": ["a", "b"]\n    "key": "value"\n  }\n]',
            "list", ["a", "b"]
        ),
        (
            '[\n  {\n    "num": 123\n    "key": "value"\n  }\n]',
            "num", 123
        ),
        (
            '[\n  {\n    "nested": {"a": 1}\n    "key": "value"\n  }\n]',
            "nested", {"a": 1}
        ),
    ])
    def test_missing_comma_strategy(self, json_snippet, expected_key, expected_value):
        """Strategy 2: Test missing comma after various value types."""
        result = parse_batch_json_with_fallback(json_snippet)
        assert len(result) == 1
        assert result[0][expected_key] == expected_value
        # All test cases also have a second key to verify structure integrity
        if "key2" in result[0]:
            assert result[0]["key2"] == "value2"
        elif "key" in result[0]:
            assert result[0]["key"] == "value"

    def test_regex_extraction(self):
        """Strategy 3: Test extracting objects when list structure is broken."""
        # Just two objects concatenated or separated by newline, not in a list
        broken_list = '{"id": 1, "val": "A"}\n{"id": 2, "val": "B"}'
        result = parse_batch_json_with_fallback(broken_list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["val"] == "B"

    def test_regex_extraction_with_comma_fix(self):
        """Strategy 3: Test extraction where objects also have missing commas."""
        # Broken list + missing commas inside objects
        broken_mixed = '{\n  "id": 1\n  "val": "A"\n}\n{\n  "id": 2\n  "val": "B"\n}'
        result = parse_batch_json_with_fallback(broken_mixed)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["val"] == "A"
        assert result[1]["id"] == 2
        assert result[1]["val"] == "B"

    def test_fallback_returns_empty(self):
        """Strategy 4: Test that completely invalid input returns empty list."""
        invalid_text = "This is not JSON at all."
        # Even with expected_count, it should return empty list (and log a warning)
        result = parse_batch_json_with_fallback(invalid_text, expected_count=3)
        assert result == []
        assert isinstance(result, list)

    def test_empty_input(self):
        """Test with empty string input."""
        result = parse_batch_json_with_fallback("")
        assert result == []
