"""Tests for integration of LogicalInferenceEngine with enhanced reasoning."""
import pytest
from unittest.mock import Mock, patch

from madspark.core.enhanced_reasoning import (
    ReasoningEngine
)
from madspark.utils.logical_inference_engine import (
    InferenceType
)


class TestLogicalInferenceIntegration:
    """Test integration of LogicalInferenceEngine with enhanced reasoning system."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Create a mock GenAI client."""
        return Mock()
    
    @pytest.fixture
    def reasoning_engine(self, mock_genai_client):
        """Create ReasoningEngine with mocked GenAI client."""
        return ReasoningEngine(genai_client=mock_genai_client)
    
    def test_logical_inference_uses_new_engine(self, reasoning_engine, mock_genai_client):
        """Test that LogicalInference now uses LogicalInferenceEngine."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = """INFERENCE_CHAIN:
- Urban areas have limited space
- Vertical solutions maximize space efficiency
- Rooftop gardens provide food production
- Community involvement increases success

CONCLUSION: Rooftop gardens are an effective urban farming solution.

CONFIDENCE: 0.85

IMPROVEMENTS: Consider hydroponic systems for higher yields."""
        
        # Mock the nested API structure
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        mock_genai_client.models = mock_models
        
        # Test using the generate_inference_chain method
        premises = [
            "Urban areas need sustainable food sources",
            "Limited ground space is available",
            "Community engagement improves success"
        ]
        
        result = reasoning_engine.generate_inference_chain(
            premises=premises,
            conclusion="Rooftop gardens are ideal"
        )
        
        # Should have real inference steps, not hardcoded ones
        assert 'logical_steps' in result
        assert len(result['logical_steps']) > 0
        
        # Should include LLM-based analysis
        assert mock_genai_client.models.generate_content.called
        
    def test_process_complete_workflow_with_logical_inference(self, reasoning_engine, mock_genai_client):
        """Test complete workflow includes logical inference when flag is set."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = """INFERENCE_CHAIN:
- Theme focuses on renewable energy
- Urban constraints require compact solutions
- Wind turbines can be integrated into buildings

CONCLUSION: Building-integrated wind turbines are optimal for urban renewable energy.

CONFIDENCE: 0.9

IMPROVEMENTS: Consider hybrid solar-wind systems."""
        
        # Mock the nested API structure
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        mock_genai_client.models = mock_models
        
        # Create conversation data with logical inference flag
        conversation_data = {
            'topic': 'renewable energy',
            'context': 'urban environment',
            'current_request': {
                'idea': 'Building-integrated wind turbines',
                'agent': 'idea_generator',
                'enable_logical_inference': True
            },
            'previous_interactions': []
        }
        
        result = reasoning_engine.process_complete_workflow(conversation_data)
        
        # Should include logical inference results
        assert 'logical_inference' in result
        assert result['logical_inference'] != {}
        
        # Verify inference contains real analysis
        logical_inference = result['logical_inference']
        assert 'inference_conclusion' in logical_inference
        assert 'Building-integrated wind turbines' in logical_inference['inference_conclusion']
        
    def test_logical_inference_error_handling(self, reasoning_engine, mock_genai_client):
        """Test error handling when logical inference fails."""
        # Make API call fail
        mock_models = Mock()
        mock_models.generate_content.side_effect = RuntimeError("API Error")
        mock_genai_client.models = mock_models
        
        premises = ["Test premise"]
        result = reasoning_engine.generate_inference_chain(premises, "Test conclusion")
        
        # Should still return a result with error indication
        assert 'logical_steps' in result
        assert 'confidence_score' in result
        assert result['confidence_score'] == 0.0  # Low confidence on error
        
    @patch('madspark.core.enhanced_reasoning.LogicalInferenceEngine')
    def test_reasoning_engine_creates_inference_engine(self, MockInferenceEngine, mock_genai_client):
        """Test that ReasoningEngine properly creates LogicalInferenceEngine instance."""
        mock_engine_instance = Mock()
        MockInferenceEngine.return_value = mock_engine_instance
        
        # Create ReasoningEngine
        reasoning_engine = ReasoningEngine(genai_client=mock_genai_client)
        
        # Should have created LogicalInferenceEngine (once in LogicalInference, shared with ReasoningEngine)
        assert hasattr(reasoning_engine, 'logical_inference_engine')
        assert MockInferenceEngine.call_count == 1  # Created once and shared (DRY principle)
        # Verify it's the same instance
        assert reasoning_engine.logical_inference_engine is reasoning_engine.logical_inference.inference_engine
        
    def test_inference_results_formatting(self, reasoning_engine, mock_genai_client):
        """Test that inference results are properly formatted for display."""
        # Setup mock with detailed response
        mock_response = Mock()
        mock_response.text = """CAUSAL_CHAIN:
1. Limited urban space → Need for vertical solutions
2. Vertical solutions → Rooftop availability
3. Rooftop availability → Garden implementation

FEEDBACK_LOOPS:
- More gardens → Community interest → More funding → More gardens

ROOT_CAUSE: Urban space constraints drive vertical farming innovation"""
        
        # Mock the nested API structure
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        mock_genai_client.models = mock_models
        
        # Test causal analysis
        result = reasoning_engine.generate_inference_chain(
            premises=["Urban space is limited"],
            conclusion="Vertical farming is necessary",
            analysis_type=InferenceType.CAUSAL
        )
        
        # Should have causal-specific fields
        assert 'causal_analysis' in result
        assert 'feedback_loops' in result['causal_analysis']
        assert 'root_cause' in result['causal_analysis']


class TestCLIIntegration:
    """Test integration with CLI for logical inference display."""
    
    @pytest.mark.asyncio
    async def test_cli_displays_logical_inference(self, tmp_path, monkeypatch):
        """Test that CLI properly displays logical inference results."""
        # This will be implemented when we integrate with CLI
        pass
        
    def test_cli_logical_flag_enables_inference(self):
        """Test that --logical flag enables logical inference in coordinator."""
        # This will be implemented when we integrate with CLI
        pass


class TestWebAPIIntegration:
    """Test integration with web API for logical inference."""
    
    def test_web_api_includes_logical_inference(self):
        """Test that web API response includes logical inference when enabled."""
        # This will be implemented when we integrate with web API
        pass
        
    def test_frontend_receives_inference_results(self):
        """Test that frontend can receive and display inference results."""
        # This will be implemented when we integrate with web API
        pass