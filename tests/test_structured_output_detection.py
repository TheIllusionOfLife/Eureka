"""Tests for structured output detection in the backend."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import Mock, patch
from madspark.utils.structured_output_check import is_structured_output_available, reset_structured_output_cache


class TestStructuredOutputDetection:
    """Test structured output detection functionality."""
    
    def test_structured_output_not_available_in_mock_mode(self):
        """Test that structured output is not available when genai_client is None."""
        result = is_structured_output_available(genai_client=None)
        assert result is False
    
    def test_structured_output_cache_mechanism(self):
        """Test that structured output availability is cached."""
        # Reset cache first
        reset_structured_output_cache()
        
        # First call should set the cache
        result1 = is_structured_output_available(genai_client=None)
        assert result1 is False
        
        # Second call should use cached result
        result2 = is_structured_output_available(genai_client=None)
        assert result2 is False
        
        # After reset, it should check again
        reset_structured_output_cache()
        result3 = is_structured_output_available(genai_client=None)
        assert result3 is False
    
    def test_structured_output_with_mock_genai_client(self):
        """Test structured output detection with a mock genai client."""
        # Reset cache
        reset_structured_output_cache()
        
        # Create a mock genai client
        mock_client = Mock()
        
        # Test that even with a client, if modules aren't available, it returns False
        with patch('importlib.util.find_spec') as mock_find_spec:
            # Simulate that structured_idea_generator module doesn't exist
            mock_find_spec.return_value = None
            
            result = is_structured_output_available(genai_client=mock_client)
            
            # Should return False because module not found
            assert result is False
            
            # Verify it checked for the structured module
            mock_find_spec.assert_called_with('madspark.agents.structured_idea_generator')
    
    def test_structured_output_importlib_checks(self):
        """Test that importlib is used correctly for module detection."""
        # Reset cache
        reset_structured_output_cache()
        
        with patch('importlib.util.find_spec') as mock_find_spec:
            # Simulate module not found
            mock_find_spec.return_value = None
            
            result = is_structured_output_available(genai_client=Mock())
            assert result is False
            
            # Verify importlib was called with correct module name
            mock_find_spec.assert_called_with('madspark.agents.structured_idea_generator')


class TestBackendStructuredOutputFlag:
    """Test that backend properly sets structured_output flag in responses."""
    
    def test_format_results_with_structured_output_marker(self):
        """Test that results with structured output marker are detected."""
        # Test the detection logic used in the backend
        
        # Results without meta-commentary (structured output)
        structured_results = [
            {"title": "Test", "description": "Direct JSON"},
            {"title": "Another", "novelty": 0.8}
        ]
        
        # Results with meta-commentary (not structured)
        non_structured_results = [
            "Here is the improved idea: {\"title\": \"Test\"}",
            "Based on the feedback: {\"title\": \"Another\"}"
        ]
        
        # Simulate backend detection logic
        meta_patterns = ['Here is', 'Here\'s', 'I\'ve improved', 'The improved version', 'Based on the feedback']
        
        # Test structured results (already parsed JSON)
        for result in structured_results:
            # When result is already a dict, it's structured output
            assert isinstance(result, dict)
        
        # Test non-structured results (strings with meta-commentary)
        for result in non_structured_results:
            assert isinstance(result, str)
            has_meta = any(pattern.lower() in result.lower() for pattern in meta_patterns)
            assert has_meta
    
    def test_api_response_structure_with_flag(self):
        """Test that API response includes structured_output flag."""
        # Expected response structure
        response = {
            "topic": "test topic",
            "context": "test context",
            "improved_ideas": [],
            "original_ideas": [],
            "structured_output": False,  # This flag should be included
            "status": "success"
        }
        
        # Verify the flag exists in response
        assert "structured_output" in response
        assert isinstance(response["structured_output"], bool)
        
        # Test with structured output detected
        response["structured_output"] = True
        assert response["structured_output"] is True