"""Edge case tests for validate_evaluation_json utility."""
import unittest
from madspark.utils.utils import validate_evaluation_json


class TestValidateEvaluationJsonEdgeCases(unittest.TestCase):
    """Test suite for edge cases in validate_evaluation_json."""

    def test_boolean_score(self):
        """Test that boolean scores are treated as invalid (default to 0)."""
        # True should be 0, not 1
        data = {"score": True, "comment": "Boolean True"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["comment"], "Boolean True")

        # False should be 0
        data = {"score": False, "comment": "Boolean False"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)

    def test_complex_types_score(self):
        """Test that list and dict scores are treated as invalid (default to 0)."""
        # List
        data = {"score": [8], "comment": "List score"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)

        # Dict
        data = {"score": {"value": 8}, "comment": "Dict score"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)

    def test_fraction_string_score(self):
        """Test that fraction strings like '8/10' result in default 0 (current behavior)."""
        data = {"score": "8/10", "comment": "Fraction score"}
        result = validate_evaluation_json(data)
        # Currently, float("8/10") raises ValueError, so it defaults to 0
        self.assertEqual(result["score"], 0)

    def test_whitespace_string_score(self):
        """Test that whitespace around numbers is handled correctly."""
        data = {"score": " 8 ", "comment": "Whitespace score"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 8.0)

        data = {"score": "  8.5  ", "comment": "Whitespace float"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 8.5)

    def test_very_large_numbers(self):
        """Test handling of very large numbers (should clamp to 10)."""
        # Large integer
        data = {"score": 1000, "comment": "Large int"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 10)

        # Large float
        data = {"score": 1e6, "comment": "Large float"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 10)

        # Infinity (handled specially in code to default to 0)
        data = {"score": float('inf'), "comment": "Infinity"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)

    def test_very_small_numbers(self):
        """Test handling of negative numbers (should clamp to 0)."""
        data = {"score": -5, "comment": "Negative"}
        result = validate_evaluation_json(data)
        self.assertEqual(result["score"], 0)
