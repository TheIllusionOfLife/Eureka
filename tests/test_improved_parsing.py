"""Test improved JSON parsing for nested and multi-line JSON."""
import pytest
import json
import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.utils import parse_json_with_fallback


class TestImprovedJSONParsing:
    """Test suite for improved JSON parsing."""
    
    def test_parse_nested_json_objects(self):
        """Test parsing of JSON objects with nested structures."""
        raw_response = """Here are the evaluations:

{
    "score": 8,
    "comment": "This is a great idea with strong potential",
    "details": {
        "feasibility": 9,
        "innovation": 7
    }
}

{
    "score": 7,
    "comment": "Good concept but needs more work",
    "details": {
        "feasibility": 6,
        "innovation": 8
    }
}"""
        
        parsed = parse_json_with_fallback(raw_response, expected_count=2)
        
        # Current regex will fail on nested JSON
        # This test will fail initially, showing we need better parsing
        assert len(parsed) == 2, f"Expected 2 evaluations but got {len(parsed)}"
    
    def test_parse_multiline_json(self):
        """Test parsing of pretty-printed JSON."""
        raw_response = '''The evaluations are:

{
    "score": 9,
    "comment": "Excellent innovation with high impact potential. 
    This addresses multiple urban challenges effectively."
}

{
    "score": 6,
    "comment": "Average idea that needs significant refinement.
    The core concept is sound but implementation is unclear."
}'''
        
        parsed = parse_json_with_fallback(raw_response, expected_count=2)
        
        # Should handle multi-line strings in JSON
        assert len(parsed) == 2, f"Expected 2 evaluations but got {len(parsed)}"
        assert parsed[0]['score'] == 9
        assert "multiple urban challenges" in parsed[0]['comment']
    
    def test_parse_json_array_in_text(self):
        """Test parsing when JSON array is embedded in text."""
        raw_response = """Based on my analysis, here are the evaluations:

[
    {"score": 8, "comment": "Strong feasibility and good innovation"},
    {"score": 7, "comment": "Moderate impact but easy to implement"},
    {"score": 9, "comment": "Excellent all around"},
    {"score": 6, "comment": "Needs more development"},
    {"score": 8, "comment": "Very promising approach"}
]

These ideas show varying levels of potential."""
        
        parsed = parse_json_with_fallback(raw_response, expected_count=5)
        
        # Should extract the JSON array
        assert len(parsed) == 5, f"Expected 5 evaluations but got {len(parsed)}"
        scores = [item['score'] for item in parsed]
        assert scores == [8, 7, 9, 6, 8]
    
    def test_parse_mixed_json_formats(self):
        """Test parsing when response has different JSON formats."""
        raw_response = """Evaluation results:

First batch:
{"score": 8, "comment": "Great idea"}
{"score": 7, "comment": "Good concept"}

Second batch in array format:
[{"score": 9, "comment": "Excellent"}, {"score": 6, "comment": "Needs work"}]

Final one:
{
    "score": 7,
    "comment": "Solid approach"
}"""
        
        parsed = parse_json_with_fallback(raw_response, expected_count=5)
        
        # Should handle all formats
        assert len(parsed) >= 3, f"Expected at least 3 evaluations but got {len(parsed)}"
    
    def test_real_critic_response_format(self):
        """Test the actual format we see from Critic in production."""
        # This is based on real Critic responses
        raw_response = """I'll evaluate each idea based on the criteria of being budget-friendly and community-focused:

{"score": 8, "comment": "Community gardens are highly budget-friendly and foster strong community engagement. Residents can share tools, knowledge, and produce while transforming unused urban spaces."}

{"score": 9, "comment": "Neighborhood tool libraries are extremely cost-effective, requiring minimal investment while maximizing resource sharing. This builds community connections and reduces individual expenses."}

{"score": 7, "comment": "Bike repair workshops combine affordability with skill-sharing. Initial setup costs are moderate, but the long-term community benefits and cost savings are substantial."}

{"score": 6, "comment": "Rain barrel systems have upfront costs but provide long-term savings. Community bulk purchasing and installation workshops can reduce individual expenses."}

{"score": 8, "comment": "Street painting projects are low-cost community beautification initiatives that bring neighbors together. Materials are inexpensive and the impact on community pride is significant."}"""
        
        parsed = parse_json_with_fallback(raw_response, expected_count=5)
        
        assert len(parsed) == 5, f"Expected 5 evaluations but got {len(parsed)}"
        
        # Verify the content
        assert parsed[0]['score'] == 8
        assert "Community gardens" in parsed[0]['comment']
        
        assert parsed[1]['score'] == 9
        assert "tool libraries" in parsed[1]['comment']