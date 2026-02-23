"""Edge case tests for validate_evaluation_json utility."""
from madspark.utils.utils import validate_evaluation_json


class TestValidateEvaluationJsonEdgeCases:
    """Test suite for edge cases in validate_evaluation_json."""

    def test_fraction_string_score(self):
        """Test that fraction strings like '8/10' result in default 0 (current behavior)."""
        data = {"score": "8/10", "comment": "Fraction score"}
        result = validate_evaluation_json(data)
        # Currently, float("8/10") raises ValueError, so it defaults to 0
        assert result["score"] == 0

    def test_whitespace_string_score(self):
        """Test that whitespace around numbers is handled correctly."""
        data = {"score": " 8 ", "comment": "Whitespace score"}
        result = validate_evaluation_json(data)
        assert result["score"] == 8.0

        data = {"score": "  8.5  ", "comment": "Whitespace float"}
        result = validate_evaluation_json(data)
        assert result["score"] == 8.5
