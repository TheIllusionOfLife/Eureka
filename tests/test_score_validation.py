"""Tests for score validation with float handling."""
from madspark.utils.utils import validate_evaluation_json


class TestScoreValidation:
    """Test cases for score validation, particularly float handling."""
    
    def test_validate_evaluation_json_with_integer_score(self):
        """Test validation with integer score (current behavior)."""
        data = {"score": 8, "comment": "Good idea"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 8
        assert result["comment"] == "Good idea"
    
    def test_validate_evaluation_json_with_float_score(self):
        """Test validation with float score - should convert to int."""
        # This test will FAIL initially as intended by TDD
        data = {"score": 7.8, "comment": "Excellent concept"}
        result = validate_evaluation_json(data)
        
        # Should round to nearest integer, not default to 0
        assert result["score"] == 8  # Round 7.8 to 8
        assert result["comment"] == "Excellent concept"
    
    def test_validate_evaluation_json_with_low_float_score(self):
        """Test validation with float score that rounds down."""
        # This test will FAIL initially as intended by TDD
        data = {"score": 4.3, "comment": "Needs improvement"}
        result = validate_evaluation_json(data)
        
        # Should round down to 4
        assert result["score"] == 4
        assert result["comment"] == "Needs improvement"
    
    def test_validate_evaluation_json_with_midpoint_float(self):
        """Test validation with .5 float (Python rounds to nearest even)."""
        # This test will FAIL initially as intended by TDD
        data = {"score": 6.5, "comment": "Average"}
        result = validate_evaluation_json(data)
        
        # Float scores should be preserved
        assert result["score"] == 6.5
        assert result["comment"] == "Average"
    
    def test_validate_evaluation_json_with_high_midpoint_float(self):
        """Test validation with 7.5 float (rounds to 8)."""
        # This test will FAIL initially as intended by TDD
        data = {"score": 7.5, "comment": "Good"}
        result = validate_evaluation_json(data)
        
        # Float scores should be preserved
        assert result["score"] == 7.5
        assert result["comment"] == "Good"
    
    def test_validate_evaluation_json_with_string_integer(self):
        """Test validation with string that can be converted to int."""
        data = {"score": "9", "comment": "Excellent"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 9
        assert result["comment"] == "Excellent"
    
    def test_validate_evaluation_json_with_string_float(self):
        """Test validation with string float."""
        # This test will FAIL initially as intended by TDD
        data = {"score": "8.7", "comment": "Very good"}
        result = validate_evaluation_json(data)
        
        # Should parse as float
        assert result["score"] == 8.7
        assert result["comment"] == "Very good"
    
    def test_validate_evaluation_json_with_invalid_string(self):
        """Test validation with non-numeric string."""
        data = {"score": "invalid", "comment": "Test"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 0  # Default for invalid
        assert result["comment"] == "Test"
    
    def test_validate_evaluation_json_with_none_score(self):
        """Test validation with None score."""
        data = {"score": None, "comment": "No score"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 0  # Default
        assert result["comment"] == "No score"
    
    def test_validate_evaluation_json_with_out_of_range_scores(self):
        """Test validation with scores outside 0-10 range."""
        # Test high score
        data = {"score": 15, "comment": "Too high"}
        result = validate_evaluation_json(data)
        assert result["score"] == 10  # Clamped to max
        
        # Test negative score
        data = {"score": -3, "comment": "Negative"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Clamped to min
        
        # Test float out of range
        data = {"score": 12.5, "comment": "Float too high"}
        result = validate_evaluation_json(data)
        assert result["score"] == 10  # Should round then clamp
    
    def test_validate_evaluation_json_with_missing_score(self):
        """Test validation with missing score field."""
        data = {"comment": "No score field"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 0  # Default
        assert result["comment"] == "No score field"
    
    def test_validate_evaluation_json_with_alternative_comment_fields(self):
        """Test validation with different comment field names."""
        # Test with 'critique' field
        data = {"score": 7, "critique": "Good but needs work"}
        result = validate_evaluation_json(data)
        assert result["comment"] == "Good but needs work"
        
        # Test with 'feedback' field
        data = {"score": 8, "feedback": "Excellent work"}
        result = validate_evaluation_json(data)
        assert result["comment"] == "Excellent work"
        
        # Test with multiple fields (comment takes precedence)
        data = {
            "score": 9,
            "comment": "Primary comment",
            "critique": "Should not appear",
            "feedback": "Also should not appear"
        }
        result = validate_evaluation_json(data)
        assert result["comment"] == "Primary comment"
    
    def test_validate_evaluation_json_with_empty_comment(self):
        """Test validation with empty or missing comment."""
        data = {"score": 5, "comment": ""}
        result = validate_evaluation_json(data)
        assert result["comment"] == "No comment provided"
        
        data = {"score": 5}
        result = validate_evaluation_json(data)
        assert result["comment"] == "No comment provided"
    
    def test_validate_evaluation_json_real_world_scenario(self):
        """Test with real-world float scores from Gemini API."""
        # Simulate the exact scenario from the bug report
        gemini_response = {
            "score": 7.8999999999999995,  # Float with many decimals
            "comment": "Re-evaluation timed out - estimated improvement based on feedback integration"
        }
        result = validate_evaluation_json(gemini_response)
        
        # Should preserve float value, not default to 0
        assert result["score"] == 7.8999999999999995
        assert result["comment"] == "Re-evaluation timed out - estimated improvement based on feedback integration"
    
    def test_validate_evaluation_json_with_special_floats(self):
        """Test validation with special float values (inf, -inf, nan) - cursor[bot] bug fix."""
        # Test infinity
        data = {"score": float('inf'), "comment": "Infinity score"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash
        assert result["comment"] == "Infinity score"
        
        # Test negative infinity
        data = {"score": float('-inf'), "comment": "Negative infinity"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash
        
        # Test NaN (Not a Number)
        data = {"score": float('nan'), "comment": "NaN score"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash
        
        # Test string representations of special floats
        data = {"score": "inf", "comment": "String infinity"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash
        
        data = {"score": "-inf", "comment": "String negative infinity"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash
        
        data = {"score": "nan", "comment": "String NaN"}
        result = validate_evaluation_json(data)
        assert result["score"] == 0  # Should default to 0, not crash