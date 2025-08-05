"""Test that demonstrates and fixes the ReasoningEngine initialization bug."""
from unittest.mock import Mock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.enhanced_reasoning import ReasoningEngine


class TestReasoningEngineInitializationBug:
    """Test suite demonstrating the initialization order bug."""
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_bug_logical_inference_initialized_before_genai_client(self, mock_get_client):
        """Demonstrate that LogicalInference is initialized before genai_client is obtained."""
        # Mock the get_genai_client to return a valid client
        mock_client = Mock()
        mock_client.__bool__ = Mock(return_value=True)  # Make it truthy
        mock_get_client.return_value = mock_client
        
        # Initialize ReasoningEngine without explicit genai_client
        engine = ReasoningEngine()
        
        # The bug has been fixed: logical_inference now gets the genai_client
        assert engine.logical_inference is not None
        
        # Fixed: LogicalInference now properly receives the genai_client
        assert engine.logical_inference.genai_client == mock_client  # Fixed!
        assert engine.logical_inference_engine is not None  # Fixed!
        
        # But multi_evaluator gets the client correctly
        assert engine.multi_evaluator is not None
        assert engine.multi_evaluator.genai_client == mock_client  # This works!
        
    def test_workaround_pass_genai_client_explicitly(self):
        """Test the workaround: pass genai_client explicitly."""
        mock_client = Mock()
        
        # When genai_client is passed explicitly, everything works
        engine = ReasoningEngine(genai_client=mock_client)
        
        assert engine.logical_inference.genai_client == mock_client
        assert engine.logical_inference_engine is not None
        assert engine.multi_evaluator.genai_client == mock_client