"""Test for the fixed ReasoningEngine initialization."""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestReasoningEngineInitializationFix:
    """Test that the initialization order fix works correctly."""
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_logical_inference_gets_auto_obtained_genai_client(self, mock_get_client):
        """Test that LogicalInference gets the auto-obtained genai_client after fix."""
        # Mock the get_genai_client to return a valid client
        mock_client = Mock()
        mock_client.__bool__ = Mock(return_value=True)
        mock_get_client.return_value = mock_client
        
        # Import here to get the patched version
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        # Initialize ReasoningEngine without explicit genai_client
        engine = ReasoningEngine()
        
        # After fix: logical_inference should have the auto-obtained client
        assert engine.logical_inference is not None
        assert engine.logical_inference.genai_client == mock_client  # Should be fixed!
        assert engine.logical_inference_engine is not None  # Should work now!
        
        # Multi-evaluator should still work
        assert engine.multi_evaluator is not None
        assert engine.multi_evaluator.genai_client == mock_client
        
    def test_explicit_genai_client_still_works(self):
        """Test that passing genai_client explicitly still works after fix."""
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        mock_client = Mock()
        engine = ReasoningEngine(genai_client=mock_client)
        
        assert engine.logical_inference.genai_client == mock_client
        assert engine.logical_inference_engine is not None
        assert engine.multi_evaluator.genai_client == mock_client
        
    def test_none_genai_client_behavior(self):
        """Test behavior when no genai_client is available."""
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        with patch('madspark.agents.genai_client.get_genai_client', return_value=None):
            engine = ReasoningEngine()
            
            assert engine.logical_inference is not None
            assert engine.logical_inference.genai_client is None
            assert engine.logical_inference_engine is None
            assert engine.multi_evaluator is None