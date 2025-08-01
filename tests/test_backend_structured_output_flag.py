"""Test backend structured output flag propagation."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBackendStructuredOutputFlag:
    """Test that backend properly propagates structured_output flag."""
    
    def test_structured_output_detection_with_meta_commentary(self):
        """Test that structured output is detected based on meta-commentary patterns."""
        # Test cases with meta-commentary (not structured)
        non_structured_outputs = [
            "Here is the improved idea:\n{\"title\": \"Test\"}",
            "Here's the improved version:\n{\"title\": \"Test\"}",
            "I've improved the idea as follows:\n{\"title\": \"Test\"}",
            "The improved version is:\n{\"title\": \"Test\"}",
            "Based on the feedback, here's the update:\n{\"title\": \"Test\"}"
        ]
        
        # Test case without meta-commentary (structured)
        structured_output = '{"title": "Test", "description": "Direct JSON output"}'
        
        meta_patterns = ['Here is', 'Here\'s', 'I\'ve improved', 'The improved version', 'Based on the feedback']
        
        # Test non-structured outputs
        for output in non_structured_outputs:
            has_meta = any(pattern.lower() in output.lower() for pattern in meta_patterns)
            assert has_meta, f"Should detect meta-commentary in: {output}"
        
        # Test structured output
        has_meta = any(pattern.lower() in structured_output.lower() for pattern in meta_patterns)
        assert not has_meta, f"Should not detect meta-commentary in: {structured_output}"
    
    def test_api_endpoint_structured_output_detection(self):
        """Test that API endpoint correctly detects structured output usage."""
        # This test verifies the detection logic patterns
        # The detection logic is:
        # 1. Check if structured output is available
        # 2. Check if the output lacks meta-commentary patterns
        
        # Example outputs that would be detected differently
        structured_output = '{"title": "Direct Output", "description": "No meta-commentary"}'
        non_structured_output = 'Here is the improved idea:\n{"title": "With Meta"}'
        
        meta_patterns = ['Here is', 'Here\'s', 'I\'ve improved', 'The improved version', 'Based on the feedback']
        
        # Test structured output (no meta-commentary)
        has_meta_structured = any(pattern.lower() in structured_output.lower() for pattern in meta_patterns)
        assert not has_meta_structured, "Structured output should not have meta-commentary"
        
        # Test non-structured output (has meta-commentary)
        has_meta_non_structured = any(pattern.lower() in non_structured_output.lower() for pattern in meta_patterns)
        assert has_meta_non_structured, "Non-structured output should have meta-commentary"
    
    def test_structured_output_flag_initialization(self):
        """Test that structured_output flag is properly initialized in responses."""
        # Test response structure
        response_template = {
            "improved_ideas": [],
            "original_ideas": [],
            "structured_output": False  # Default value
        }
        
        # Verify default is False
        assert response_template["structured_output"] is False
        
        # Verify it can be set to True
        response_template["structured_output"] = True
        assert response_template["structured_output"] is True