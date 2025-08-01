"""Test backend structured output flag propagation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBackendStructuredOutputFlag:
    """Test that backend properly propagates structured_output flag."""
    
    def test_coordinator_tracks_structured_output_usage(self):
        """Test that coordinator tracks when structured output is used."""
        from madspark.core.coordinator import Coordinator
        
        # Mock the genai client
        mock_client = Mock()
        
        # Create coordinator with mock client
        coordinator = Coordinator(genai_client=mock_client)
        
        # Mock the agents to return results with metadata
        mock_idea = Mock()
        mock_idea.generate_ideas.return_value = [{
            'idea': 'Test idea',
            'metadata': {'structured_output_used': True}
        }]
        
        with patch.object(coordinator, 'idea_generator', mock_idea):
            results = coordinator.run_workflow('test topic', 'test context')
            
            # Check if metadata is preserved
            assert 'metadata' in results[0]
            assert results[0]['metadata'].get('structured_output_used') is True
    
    def test_format_results_preserves_structured_output_flag(self):
        """Test that format_results_for_frontend preserves structured output metadata."""
        # This will be implemented when we update the backend
        pass
    
    def test_api_endpoint_returns_structured_output_flag(self):
        """Test that API endpoint returns structured_output flag based on results."""
        # This will be implemented when we update the backend
        pass
    
    def test_async_coordinator_tracks_structured_output(self):
        """Test that async coordinator also tracks structured output usage."""
        # This will be implemented when we update the backend
        pass