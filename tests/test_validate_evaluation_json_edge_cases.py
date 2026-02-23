"""Edge case tests for validate_evaluation_json utility."""
from madspark.utils.utils import validate_evaluation_json


def test_boolean_score():
    """Test that boolean scores are treated as invalid (default to 0)."""
    # True should be 0, not 1
    data = {"score": True, "comment": "Boolean True"}
    result = validate_evaluation_json(data)
    assert result["score"] == 0
    assert result["comment"] == "Boolean True"

    # False should be 0
    data = {"score": False, "comment": "Boolean False"}
    result = validate_evaluation_json(data)
    assert result["score"] == 0


def test_complex_types_score():
    """Test that list and dict scores are treated as invalid (default to 0)."""
    # List
    data = {"score": [8], "comment": "List score"}
    result = validate_evaluation_json(data)
    assert result["score"] == 0

    # Dict
    data = {"score": {"value": 8}, "comment": "Dict score"}
    result = validate_evaluation_json(data)
    assert result["score"] == 0


def test_whitespace_string_score():
    """Test that whitespace around numbers is handled correctly."""
    data = {"score": " 8 ", "comment": "Whitespace score"}
    result = validate_evaluation_json(data)
    assert result["score"] == 8.0

    data = {"score": "  8.5  ", "comment": "Whitespace float"}
    result = validate_evaluation_json(data)
    assert result["score"] == 8.5
