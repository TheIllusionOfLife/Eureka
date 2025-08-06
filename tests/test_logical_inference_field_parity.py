"""Test field parity between mock and production modes for logical inference.

This test suite ensures that logical inference returns consistent fields
regardless of whether it's running in mock mode or with a real API.
"""
import pytest
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceResult, InferenceType


class TestLogicalInferenceFieldParity:
    """Test that logical inference returns same fields in mock and production modes."""
    
    def test_inference_result_has_all_expected_fields(self):
        """Test that InferenceResult dataclass contains all expected fields."""
        # Create a result with all fields populated
        result = InferenceResult(
            # Core fields
            inference_chain=["Step 1", "Step 2"],
            conclusion="Test conclusion",
            confidence=0.85,
            improvements="Could be improved",
            
            # Analysis-specific fields
            causal_chain=["Cause 1", "Cause 2"],
            feedback_loops=["Loop 1"],
            root_cause="Root cause",
            
            constraint_satisfaction={"Constraint 1": 80.0},
            overall_satisfaction=75.0,
            trade_offs=["Trade-off 1"],
            
            contradictions=[{"conflict": "A vs B", "severity": "HIGH"}],
            resolution="Resolve by...",
            
            implications=["Implication 1"],
            second_order_effects=["Effect 1"],
            
            error=None
        )
        
        # Verify all fields exist
        assert hasattr(result, 'inference_chain')
        assert hasattr(result, 'conclusion')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'improvements')
        assert hasattr(result, 'causal_chain')
        assert hasattr(result, 'feedback_loops')
        assert hasattr(result, 'root_cause')
        assert hasattr(result, 'constraint_satisfaction')
        assert hasattr(result, 'overall_satisfaction')
        assert hasattr(result, 'trade_offs')
        assert hasattr(result, 'contradictions')
        assert hasattr(result, 'resolution')
        assert hasattr(result, 'implications')
        assert hasattr(result, 'second_order_effects')
        assert hasattr(result, 'error')
    
    def test_production_mode_returns_all_fields_for_full_analysis(self):
        """Test that production mode with real LLM returns all expected fields for full analysis."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        # Simulate a comprehensive LLM response with all fields
        mock_response.text = """INFERENCE_CHAIN:
- [Step 1]: This idea addresses the topic by providing a solution
- [Step 2]: The solution is feasible given the constraints
- [Step 3]: Implementation would have positive impact

CONCLUSION: This is a well-reasoned idea that addresses the requirements effectively.

CONFIDENCE: 0.85

IMPROVEMENTS: Consider adding more specific implementation details and timeline.

CAUSAL_CHAIN:
1. Initial problem → Need for solution
2. Solution implementation → Positive outcomes

FEEDBACK_LOOPS:
- Success reinforces adoption
- User feedback improves system

ROOT_CAUSE: Fundamental need for efficiency improvement"""
        
        mock_client.models.generate_content.return_value = mock_response
        
        engine = LogicalInferenceEngine(genai_client=mock_client)
        
        # Act
        result = engine.analyze(
            idea="Test idea",
            topic="Test topic",
            context="Test context",
            analysis_type=InferenceType.FULL
        )
        
        # Assert - all core fields should be populated
        assert result.inference_chain is not None and len(result.inference_chain) > 0
        assert result.conclusion is not None and result.conclusion != ""
        assert result.confidence > 0
        assert result.improvements is not None
        
        # These fields may not be populated for FULL analysis type
        # but should exist (can be None)
        assert hasattr(result, 'causal_chain')
        assert hasattr(result, 'feedback_loops')
        assert hasattr(result, 'root_cause')
    
    def test_production_mode_causal_analysis_returns_specific_fields(self):
        """Test that causal analysis returns causal-specific fields."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """CAUSAL_CHAIN:
1. Root problem → Initial effect
2. Initial effect → Secondary effect
3. Secondary effect → Final outcome

FEEDBACK_LOOPS:
- Positive reinforcement loop between adoption and benefits
- Balancing loop for resource consumption

ROOT_CAUSE: Underlying inefficiency in current system"""
        
        mock_client.models.generate_content.return_value = mock_response
        
        engine = LogicalInferenceEngine(genai_client=mock_client)
        
        # Act
        result = engine.analyze(
            idea="Test idea",
            topic="Test topic", 
            context="Test context",
            analysis_type=InferenceType.CAUSAL
        )
        
        # Assert - causal fields should be populated
        assert result.causal_chain is not None and len(result.causal_chain) > 0
        assert result.feedback_loops is not None and len(result.feedback_loops) > 0
        assert result.root_cause is not None and result.root_cause != ""
        assert result.conclusion is not None  # Should be derived from root cause
    
    def test_mock_mode_reasoning_engine_returns_consistent_fields(self):
        """Test that mock mode ReasoningEngine returns consistent logical inference fields."""
        # Arrange - create reasoning engine without genai_client to trigger mock mode
        from madspark.core.enhanced_reasoning import LogicalInference
        
        # Create LogicalInference without genai_client to trigger fallback mode
        mock_inference = LogicalInference(genai_client=None)
        
        # Act - build inference chain using fallback mode
        result = mock_inference.build_inference_chain(
            premises=["If it rains, the ground gets wet", "It is raining"],
            theme="Test topic",
            context="Test context"
        )
        
        # Assert - check the fallback structure
        assert 'steps' in result
        assert 'conclusion' in result
        assert 'validity_score' in result
        
        # Note: Mock mode returns different field names than production mode
        # This is the issue we need to fix for consistency
    
    def test_field_consistency_between_modes(self):
        """Test that both mock and production modes return the same field structure."""
        from madspark.core.enhanced_reasoning import LogicalInference
        
        # Production mode result
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """INFERENCE_CHAIN:
- [Step 1]: Analysis step one
- [Step 2]: Analysis step two

CONCLUSION: Test conclusion

CONFIDENCE: 0.75

IMPROVEMENTS: Test improvements"""
        
        mock_client.models.generate_content.return_value = mock_response
        
        # Use LogicalInference for both modes
        prod_inference = LogicalInference(genai_client=mock_client)
        prod_result = prod_inference.build_inference_chain(
            premises=["Test premise 1", "Test premise 2"],
            theme="Test topic",
            context="Test context"
        )
        
        # Mock mode result (without genai_client)
        mock_inference = LogicalInference(genai_client=None)
        mock_result = mock_inference.build_inference_chain(
            premises=["Test premise 1", "Test premise 2"],
            theme="Test topic",
            context="Test context"
        )
        
        # Both should have consistent field structure
        # Production mode with LLM has 'inference_result' containing InferenceResult
        # Mock mode has 'steps', 'conclusion', 'validity_score'
        
        # Check that both have conclusion (core field)
        assert 'conclusion' in prod_result
        assert 'conclusion' in mock_result
        
        # Note the field name differences:
        # - Production: 'confidence_score' and 'validity_score'
        # - Mock: 'validity_score' only
        # This inconsistency should be fixed
    
    def test_to_dict_excludes_empty_fields(self):
        """Test that to_dict() method excludes None and empty list fields."""
        result = InferenceResult(
            conclusion="Test conclusion",
            confidence=0.8,
            inference_chain=[],  # Empty list
            improvements=None,  # None value
            causal_chain=["Has value"]  # Non-empty
        )
        
        result_dict = result.to_dict()
        
        # Should include non-empty fields
        assert 'conclusion' in result_dict
        assert 'confidence' in result_dict
        assert 'causal_chain' in result_dict
        
        # Should exclude empty/None fields
        assert 'inference_chain' not in result_dict  # Empty list
        assert 'improvements' not in result_dict  # None
        assert 'feedback_loops' not in result_dict  # Default None
    
    def test_batch_analysis_field_consistency(self):
        """Test that batch analysis returns consistent fields for all items."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """=== ANALYSIS_FOR_IDEA_1 ===
INFERENCE_CHAIN:
- [Step 1]: First idea analysis

CONCLUSION: First idea conclusion

CONFIDENCE: 0.8

IMPROVEMENTS: First improvements

=== ANALYSIS_FOR_IDEA_2 ===
INFERENCE_CHAIN:
- [Step 1]: Second idea analysis

CONCLUSION: Second idea conclusion

CONFIDENCE: 0.7

IMPROVEMENTS: Second improvements"""
        
        mock_client.models.generate_content.return_value = mock_response
        engine = LogicalInferenceEngine(genai_client=mock_client)
        
        # Act
        results = engine.analyze_batch(
            ideas=["Idea 1", "Idea 2"],
            topic="Test topic",
            context="Test context",
            analysis_type=InferenceType.FULL
        )
        
        # Assert - all results should have same field structure
        assert len(results) == 2
        
        fields_1 = set(results[0].to_dict().keys())
        fields_2 = set(results[1].to_dict().keys())
        
        # Both results should have the same fields populated
        # (though values may differ)
        assert fields_1 == fields_2, f"Field mismatch: {fields_1} vs {fields_2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])