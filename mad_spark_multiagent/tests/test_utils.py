"""Tests for utility functions."""
import pytest
import json
import time
from unittest.mock import Mock, patch
from mad_spark_multiagent.utils import (
    exponential_backoff_retry,
    parse_json_with_fallback,
    validate_evaluation_json,
)


class TestExponentialBackoffRetry:
    """Test cases for exponential backoff retry decorator."""
    
    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        mock_func = Mock(return_value="success")
        decorated_func = exponential_backoff_retry(max_retries=3)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test that function retries on exceptions."""
        mock_func = Mock(side_effect=[Exception("error"), Exception("error"), "success"])
        decorated_func = exponential_backoff_retry(
            max_retries=3, initial_delay=0.1
        )(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        mock_func = Mock(side_effect=Exception("persistent error"))
        decorated_func = exponential_backoff_retry(
            max_retries=2, initial_delay=0.1
        )(mock_func)
        
        with pytest.raises(Exception) as exc_info:
            decorated_func()
        
        assert str(exc_info.value) == "persistent error"
        assert mock_func.call_count == 3  # initial + 2 retries
    
    def test_exponential_backoff_timing(self):
        """Test that delays increase exponentially."""
        call_times = []
        
        def track_time():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("retry me")
            return "success"
        
        decorated_func = exponential_backoff_retry(
            max_retries=3, initial_delay=0.1, backoff_factor=2
        )(track_time)
        
        result = decorated_func()
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Check that delays are approximately correct (allowing for some variance)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert 0.08 < delay1 < 0.12  # ~0.1 seconds
        assert 0.18 < delay2 < 0.22  # ~0.2 seconds


class TestParseJsonWithFallback:
    """Test cases for robust JSON parsing."""
    
    def test_parse_json_array(self):
        """Test parsing a valid JSON array."""
        text = '[{"score": 8, "comment": "Great idea"}, {"score": 6, "comment": "Needs work"}]'
        result = parse_json_with_fallback(text)
        
        assert len(result) == 2
        assert result[0]["score"] == 8
        assert result[0]["comment"] == "Great idea"
    
    def test_parse_line_by_line(self):
        """Test parsing JSON objects line by line."""
        text = '{"score": 7, "comment": "Good"}\n{"score": 9, "comment": "Excellent"}'
        result = parse_json_with_fallback(text)
        
        assert len(result) == 2
        assert result[0]["score"] == 7
        assert result[1]["score"] == 9
    
    def test_extract_json_with_regex(self):
        """Test extracting JSON objects from mixed text."""
        text = 'Some text before {"score": 5, "comment": "Average"} and after'
        result = parse_json_with_fallback(text)
        
        assert len(result) == 1
        assert result[0]["score"] == 5
    
    def test_extract_score_comment_patterns(self):
        """Test extracting score/comment patterns from text."""
        text = """
        Evaluation 1:
        Score: 8
        Comment: This is a creative idea
        
        Evaluation 2:
        score: 6, comment: Needs more detail
        """
        result = parse_json_with_fallback(text)
        
        assert len(result) == 2
        assert result[0]["score"] == 8
        assert "creative idea" in result[0]["comment"]
        assert result[1]["score"] == 6
    
    def test_fallback_with_expected_count(self):
        """Test that placeholders are created when parsing fails."""
        text = "This is not JSON at all"
        result = parse_json_with_fallback(text, expected_count=3)
        
        assert len(result) == 3
        assert all(item["score"] == 0 for item in result)
        assert all(item["comment"] == "Failed to parse evaluation" for item in result)
    
    def test_mixed_valid_invalid_json(self):
        """Test parsing mixed valid and invalid JSON lines."""
        text = '{"score": 7, "comment": "Good"}\nNot JSON\n{"score": 8, "comment": "Great"}'
        result = parse_json_with_fallback(text)
        
        assert len(result) == 2
        assert result[0]["score"] == 7
        assert result[1]["score"] == 8


class TestValidateEvaluationJson:
    """Test cases for JSON validation."""
    
    def test_valid_data(self):
        """Test validation of valid data."""
        data = {"score": 7, "comment": "Good idea"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 7
        assert result["comment"] == "Good idea"
    
    def test_score_string_conversion(self):
        """Test conversion of string score to integer."""
        data = {"score": "8", "comment": "Great"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 8
        assert isinstance(result["score"], int)
    
    def test_score_clamping(self):
        """Test that scores are clamped to valid range."""
        data1 = {"score": 15, "comment": "Too high"}
        data2 = {"score": -5, "comment": "Too low"}
        
        result1 = validate_evaluation_json(data1)
        result2 = validate_evaluation_json(data2)
        
        assert result1["score"] == 10
        assert result2["score"] == 0
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        data = {}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 0
        assert result["comment"] == "No comment provided"
    
    def test_alternative_comment_fields(self):
        """Test that alternative comment field names are recognized."""
        data1 = {"score": 7, "critique": "Needs improvement"}
        data2 = {"score": 8, "feedback": "Well done"}
        
        result1 = validate_evaluation_json(data1)
        result2 = validate_evaluation_json(data2)
        
        assert result1["comment"] == "Needs improvement"
        assert result2["comment"] == "Well done"
    
    def test_invalid_score_type(self):
        """Test handling of invalid score types."""
        data = {"score": {"nested": "value"}, "comment": "Test"}
        result = validate_evaluation_json(data)
        
        assert result["score"] == 0
        assert result["comment"] == "Test"