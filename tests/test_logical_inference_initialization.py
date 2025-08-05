"""Test that logical inference engine is properly initialized with genai_client."""
from unittest.mock import Mock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.enhanced_reasoning import ReasoningEngine, LogicalInference


class TestLogicalInferenceInitialization:
    """Test suite for logical inference engine initialization."""
    
    def test_reasoning_engine_without_genai_client(self):
        """Test that ReasoningEngine without genai_client has no logical inference engine."""
        # Initialize without genai_client
        engine = ReasoningEngine(genai_client=None)
        
        # Verify logical_inference is created but inference_engine is None
        assert engine.logical_inference is not None
        assert engine.logical_inference_engine is None
        
    def test_reasoning_engine_with_genai_client(self):
        """Test that ReasoningEngine with genai_client has logical inference engine."""
        # Mock genai_client
        mock_client = Mock()
        
        # Initialize with genai_client
        engine = ReasoningEngine(genai_client=mock_client)
        
        # Verify both logical_inference and inference_engine are created
        assert engine.logical_inference is not None
        assert engine.logical_inference_engine is not None
        assert engine.logical_inference.genai_client == mock_client
        
    def test_logical_inference_requires_genai_client(self):
        """Test that LogicalInference only creates inference_engine with genai_client."""
        # Without genai_client
        li_without = LogicalInference(genai_client=None)
        assert li_without.inference_engine is None
        
        # With genai_client
        mock_client = Mock()
        li_with = LogicalInference(genai_client=mock_client)
        assert li_with.inference_engine is not None
        
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_reasoning_engine_auto_gets_genai_client(self, mock_get_client):
        """Test that ReasoningEngine automatically gets genai_client if not provided."""
        # Mock the get_genai_client function
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Initialize without explicit genai_client
        engine = ReasoningEngine()
        
        # Verify get_genai_client was called
        mock_get_client.assert_called_once()
        
        # Verify logical_inference_engine is created with the auto-obtained client
        assert engine.logical_inference_engine is not None