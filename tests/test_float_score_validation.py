"""Test cases for float score validation bug fix.

This test suite verifies that validate_evaluation_json properly handles
both int and float scores, addressing the web interface display issue
where float scores were showing as 0.0.
"""
from src.madspark.utils.utils import validate_evaluation_json


class TestFloatScoreValidation:
    """Test suite for float score validation in validate_evaluation_json."""
    
    def test_integer_score_unchanged(self):
        """Integer scores should work as before."""
        data = {"score": 8, "comment": "Good idea"}
        result = validate_evaluation_json(data)
        assert result["score"] == 8
        assert isinstance(result["score"], int)
        
    def test_float_score_accepted(self):
        """Float scores should be accepted and preserved."""
        data = {"score": 7.5, "comment": "Good idea"}
        result = validate_evaluation_json(data)
        assert result["score"] == 7.5
        assert isinstance(result["score"], float)
        
    def test_float_score_various_values(self):
        """Test various float score values."""
        test_cases = [
            (0.0, 0.0),
            (5.5, 5.5),
            (7.8, 7.8),
            (10.0, 10.0),
            (3.14159, 3.14159)
        ]
        
        for input_score, expected_score in test_cases:
            data = {"score": input_score, "comment": "Test"}
            result = validate_evaluation_json(data)
            assert result["score"] == expected_score
            assert isinstance(result["score"], (int, float))
    
    def test_string_score_conversion(self):
        """String scores should still be converted."""
        test_cases = [
            ("8", 8),
            ("7.5", 7.5),  # String floats should convert to float
            ("10", 10),
            ("invalid", 0),  # Invalid strings default to 0
            ("", 0)  # Empty string defaults to 0
        ]
        
        for input_score, expected_score in test_cases:
            data = {"score": input_score, "comment": "Test"}
            result = validate_evaluation_json(data)
            assert result["score"] == expected_score
            
    def test_invalid_score_types(self):
        """Invalid score types should default to 0."""
        invalid_scores = [
            None,
            [],
            {},
            {"nested": "object"},
            True,
            False
        ]
        
        for invalid_score in invalid_scores:
            data = {"score": invalid_score, "comment": "Test"}
            result = validate_evaluation_json(data)
            assert result["score"] == 0
            
    def test_score_clamping(self):
        """Scores should be clamped to 0-10 range."""
        test_cases = [
            (-5, 0),
            (-0.5, 0),
            (11, 10),
            (10.5, 10),
            (100, 10)
        ]
        
        for input_score, expected_score in test_cases:
            data = {"score": input_score, "comment": "Test"}
            result = validate_evaluation_json(data)
            assert result["score"] == expected_score
            
    def test_comment_handling_unchanged(self):
        """Comment handling should remain unchanged."""
        test_cases = [
            {"score": 7.5, "comment": "Good idea"},
            {"score": 8, "critique": "Needs work"},
            {"score": 6.5, "feedback": "Interesting"},
            {"score": 5.0}  # No comment field
        ]
        
        for data in test_cases:
            result = validate_evaluation_json(data)
            assert "comment" in result
            if "comment" in data:
                assert result["comment"] == data["comment"].strip()
            elif "critique" in data:
                assert result["comment"] == data["critique"].strip()
            elif "feedback" in data:
                assert result["comment"] == data["feedback"].strip()
            else:
                assert result["comment"] == "No comment provided"
                
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty dict
        result = validate_evaluation_json({})
        assert result["score"] == 0
        assert result["comment"] == "No comment provided"
        
        # Float at boundaries
        result = validate_evaluation_json({"score": 0.0})
        assert result["score"] == 0.0
        
        result = validate_evaluation_json({"score": 10.0})
        assert result["score"] == 10.0
        
        # Very small float
        result = validate_evaluation_json({"score": 0.00001})
        assert result["score"] == 0.00001
        
        # Scientific notation
        result = validate_evaluation_json({"score": 5e0})
        assert result["score"] == 5.0