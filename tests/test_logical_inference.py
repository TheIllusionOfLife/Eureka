"""Tests for the LogicalInferenceEngine."""
import pytest
from unittest.mock import Mock, MagicMock
import json
from typing import Dict, Any

from madspark.utils.logical_inference_engine import (
    LogicalInferenceEngine,
    InferenceResult,
    InferenceType
)


class TestLogicalInferenceEngine:
    """Test suite for LogicalInferenceEngine."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Create a mock GenAI client."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def engine(self, mock_genai_client):
        """Create a LogicalInferenceEngine instance with mocked client."""
        return LogicalInferenceEngine(mock_genai_client)
    
    def test_engine_initialization(self, mock_genai_client):
        """Test that engine initializes correctly."""
        engine = LogicalInferenceEngine(mock_genai_client)
        assert engine.genai_client == mock_genai_client
        assert hasattr(engine, 'inference_types')
        assert InferenceType.FULL in engine.inference_types
    
    def test_analyze_full_inference(self, engine, mock_genai_client):
        """Test full logical inference analysis."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = """INFERENCE_CHAIN:
- [Observation]: Urban areas have limited horizontal space
- [Deduction]: Vertical solutions are more suitable
- [Analysis]: Building-integrated systems reduce installation costs
- [Conclusion]: Vertical axis wind turbines are optimal

CONCLUSION: Vertical axis wind turbines integrated into buildings provide the best solution for urban renewable energy generation.

CONFIDENCE: 0.85

IMPROVEMENTS: Consider hybrid systems combining solar panels with wind turbines for maximum efficiency."""
        
        mock_genai_client.generate_content.return_value = mock_response
        
        # Test
        result = engine.analyze(
            idea="Install vertical axis wind turbines on skyscrapers",
            theme="renewable energy",
            context="urban environment constraints",
            analysis_type=InferenceType.FULL
        )
        
        # Assertions
        assert isinstance(result, InferenceResult)
        assert len(result.inference_chain) == 4
        assert result.conclusion.startswith("Vertical axis wind turbines")
        assert result.confidence == 0.85
        assert "hybrid systems" in result.improvements
        assert mock_genai_client.generate_content.called
    
    def test_analyze_causal_reasoning(self, engine, mock_genai_client):
        """Test causal reasoning analysis."""
        mock_response = Mock()
        mock_response.text = """CAUSAL_CHAIN:
1. Urban density → Limited ground space
2. Limited space → Need for vertical solutions
3. Vertical solutions → Building integration required
4. Building integration → Reduced installation costs
5. Cost reduction → Increased adoption rates

FEEDBACK_LOOPS:
- More adoption → Economy of scale → Lower costs → More adoption

ROOT_CAUSE: Urban space constraints drive innovation in vertical renewable energy"""
        
        mock_genai_client.generate_content.return_value = mock_response
        
        result = engine.analyze(
            idea="Vertical wind turbines for cities",
            theme="renewable energy", 
            context="urban constraints",
            analysis_type=InferenceType.CAUSAL
        )
        
        assert result.causal_chain is not None
        assert len(result.causal_chain) == 5
        assert result.feedback_loops is not None
        assert "Urban space constraints" in result.root_cause
    
    def test_analyze_constraint_satisfaction(self, engine, mock_genai_client):
        """Test constraint satisfaction analysis."""
        mock_response = Mock()
        mock_response.text = """CONSTRAINT_ANALYSIS:
- Space limitation: SATISFIED (90%) - Vertical design minimizes footprint
- Cost effectiveness: SATISFIED (75%) - Initial cost high but ROI in 5 years  
- Environmental impact: SATISFIED (95%) - Zero emissions, minimal noise
- Urban regulations: PARTIALLY SATISFIED (60%) - May need zoning approvals

OVERALL_SATISFACTION: 80%

TRADE_OFFS:
- Higher upfront cost for better long-term savings
- Some aesthetic impact for environmental benefits"""
        
        mock_genai_client.generate_content.return_value = mock_response
        
        result = engine.analyze(
            idea="Rooftop wind turbines",
            theme="renewable energy",
            context="must be cost-effective, environmentally friendly, fit urban regulations",
            analysis_type=InferenceType.CONSTRAINTS
        )
        
        assert result.constraint_satisfaction is not None
        assert result.overall_satisfaction == 80
        assert len(result.trade_offs) == 2
    
    def test_analyze_contradiction_detection(self, engine, mock_genai_client):
        """Test contradiction detection analysis."""
        mock_response = Mock()
        mock_response.text = """CONTRADICTIONS_FOUND: 1

CONTRADICTION_1:
- Conflict: "Anonymous" vs "for teenagers"  
- Type: Safety requirement conflict
- Severity: HIGH
- Explanation: True anonymity prevents safety measures required for minors

RESOLUTION:
Use pseudo-anonymity with verified guardian oversight while maintaining peer anonymity

NO_CONTRADICTIONS: False"""
        
        mock_genai_client.generate_content.return_value = mock_response
        
        result = engine.analyze(
            idea="Anonymous social network for teenagers",
            theme="social networking",
            context="must be safe for minors",
            analysis_type=InferenceType.CONTRADICTION
        )
        
        assert result.contradictions is not None
        assert len(result.contradictions) == 1
        assert result.contradictions[0]['severity'] == 'HIGH'
        assert 'pseudo-anonymity' in result.resolution
    
    def test_format_for_display_brief(self, engine):
        """Test brief display formatting."""
        result = InferenceResult(
            inference_chain=["Step 1", "Step 2", "Step 3"],
            conclusion="This is the conclusion",
            confidence=0.9,
            improvements="Some improvements"
        )
        
        formatted = engine.format_for_display(result, verbosity='brief')
        assert "Conclusion:" in formatted
        assert "Confidence: 90%" in formatted
        assert "Step 1" not in formatted  # Chain not shown in brief
    
    def test_format_for_display_standard(self, engine):
        """Test standard display formatting."""
        result = InferenceResult(
            inference_chain=["Step 1", "Step 2", "Step 3"],
            conclusion="This is the conclusion",
            confidence=0.9,
            improvements="Some improvements"
        )
        
        formatted = engine.format_for_display(result, verbosity='standard')
        assert "Logical Inference Analysis" in formatted
        assert "Step 1" in formatted
        assert "Step 2" in formatted
        assert "Conclusion:" in formatted
        assert "Confidence: 90%" in formatted
    
    def test_format_for_display_detailed(self, engine):
        """Test detailed display formatting."""
        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Conclusion here",
            confidence=0.85,
            improvements="Improvements here",
            causal_chain=["Cause 1", "Cause 2"],
            contradictions=[{"conflict": "A vs B", "severity": "HIGH"}]
        )
        
        formatted = engine.format_for_display(result, verbosity='detailed')
        assert "Causal Analysis:" in formatted
        assert "Cause 1" in formatted
        assert "Contradictions Found:" in formatted
        assert "A vs B" in formatted
        assert "Improvements:" in formatted
    
    def test_error_handling_api_failure(self, engine, mock_genai_client):
        """Test handling of API failures."""
        mock_genai_client.generate_content.side_effect = Exception("API Error")
        
        result = engine.analyze(
            idea="Test idea",
            theme="Test theme",
            context="Test context"
        )
        
        assert result.error is not None
        assert "API Error" in result.error
        assert result.confidence == 0.0
    
    def test_error_handling_malformed_response(self, engine, mock_genai_client):
        """Test handling of malformed API responses."""
        mock_response = Mock()
        mock_response.text = "This is not the expected format"
        mock_genai_client.generate_content.return_value = mock_response
        
        result = engine.analyze(
            idea="Test idea",
            theme="Test theme", 
            context="Test context"
        )
        
        # Should provide basic analysis even with malformed response
        assert result.conclusion is not None
        assert result.confidence > 0
    
    def test_prompt_template_includes_all_fields(self, engine, mock_genai_client):
        """Test that prompts include all necessary fields."""
        engine.analyze(
            idea="Test idea",
            theme="Test theme",
            context="Test context",
            analysis_type=InferenceType.FULL
        )
        
        # Check the prompt that was sent
        call_args = mock_genai_client.generate_content.call_args
        prompt = call_args[0][0]
        
        assert "Test idea" in prompt
        assert "Test theme" in prompt  
        assert "Test context" in prompt
        assert "INFERENCE_CHAIN:" in prompt
        assert "CONCLUSION:" in prompt
        assert "CONFIDENCE:" in prompt


class TestInferenceResult:
    """Test the InferenceResult dataclass."""
    
    def test_inference_result_creation(self):
        """Test creating an InferenceResult."""
        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Test conclusion",
            confidence=0.75,
            improvements="Test improvements"
        )
        
        assert len(result.inference_chain) == 2
        assert result.conclusion == "Test conclusion"
        assert result.confidence == 0.75
        assert result.improvements == "Test improvements"
    
    def test_inference_result_to_dict(self):
        """Test converting InferenceResult to dictionary."""
        result = InferenceResult(
            inference_chain=["Step 1"],
            conclusion="Conclusion",
            confidence=0.8,
            causal_chain=["Cause 1"]
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['confidence'] == 0.8
        assert 'causal_chain' in result_dict
        assert result_dict['causal_chain'] == ["Cause 1"]


class TestIntegration:
    """Integration tests for logical inference with the system."""
    
    @pytest.mark.integration
    def test_cli_integration(self, tmp_path, monkeypatch):
        """Test integration with CLI."""
        # This will be implemented when we integrate with CLI
        pass
    
    @pytest.mark.integration  
    def test_web_api_integration(self):
        """Test integration with web API."""
        # This will be implemented when we integrate with web API
        pass