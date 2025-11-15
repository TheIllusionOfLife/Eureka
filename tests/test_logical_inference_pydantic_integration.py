"""
Tests for logical_inference_engine.py Pydantic migration (Phase 3, Task 2).

This test module verifies that LogicalInferenceEngine uses Pydantic models
instead of dataclass InferenceResult, with proper validation and type safety.
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestLogicalInferencePydanticIntegration:
    """Test suite for LogicalInferenceEngine Pydantic migration."""

    def test_inference_result_uses_pydantic_validation(self):
        """Test that InferenceResult uses Pydantic validation."""
        from madspark.schemas.logical_inference import InferenceResult as PydanticInferenceResult
        from pydantic import ValidationError

        # Test valid data passes validation
        valid_data = {
            "inference_chain": ["Premise 1: Market validation is essential", "Premise 2: No validation done yet"],
            "conclusion": "Recommend customer interviews before development",
            "confidence": 0.85,
            "improvements": "Consider landing page tests"
        }
        result = PydanticInferenceResult(**valid_data)
        assert result.confidence == 0.85
        assert len(result.inference_chain) == 2
        assert result.conclusion == "Recommend customer interviews before development"

        # Test invalid confidence fails validation (> 1.0)
        invalid_data = {
            "inference_chain": ["Step 1"],
            "conclusion": "Test conclusion",
            "confidence": 1.5  # Invalid: > 1.0
        }
        with pytest.raises(ValidationError):
            PydanticInferenceResult(**invalid_data)

        # Test missing required field fails
        missing_field_data = {
            "confidence": 0.5
            # Missing inference_chain and conclusion
        }
        with pytest.raises(ValidationError):
            PydanticInferenceResult(**missing_field_data)

    def test_analyze_returns_pydantic_model(self):
        """Test that analyze() method returns Pydantic InferenceResult."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from madspark.schemas.logical_inference import InferenceResult as PydanticInferenceResult

        # Create mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "inference_chain": ["Analysis step 1", "Analysis step 2"],
            "conclusion": "Implementation is feasible with constraints",
            "confidence": 0.9,
            "improvements": "Consider phased rollout"
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(mock_client)

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            result = engine.analyze(
                idea="Smart traffic system",
                topic="Urban Innovation",
                context="Limited budget",
                analysis_type=InferenceType.FULL
            )

        # Verify result is Pydantic model
        assert isinstance(result, PydanticInferenceResult)
        assert hasattr(result, 'model_dump')  # Pydantic method
        assert result.confidence == 0.9
        assert len(result.inference_chain) == 2

    def test_analyze_batch_returns_pydantic_list(self):
        """Test that analyze_batch() returns list of Pydantic models."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from madspark.schemas.logical_inference import InferenceResult as PydanticInferenceResult

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "inference_chain": ["Step 1"],
            "conclusion": "Analysis complete",
            "confidence": 0.8
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(mock_client)

        ideas = ["Idea 1", "Idea 2"]
        topic = "Test Topic"
        context = "Test Context"

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            results = engine.analyze_batch(
                ideas=ideas,
                topic=topic,
                context=context,
                analysis_type=InferenceType.FULL
            )

        # Verify all results are Pydantic models
        assert len(results) == 2
        for result in results:
            assert isinstance(result, PydanticInferenceResult)
            assert hasattr(result, 'model_dump')

    def test_create_result_from_json_with_pydantic(self):
        """Test _create_result_from_json uses Pydantic model validation."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from madspark.schemas.logical_inference import (
            InferenceResult,
            CausalAnalysis,
            ConstraintAnalysis
        )

        mock_client = Mock()
        engine = LogicalInferenceEngine(mock_client)

        # Test FULL analysis type
        full_data = {
            "inference_chain": ["Premise 1", "Premise 2", "Inference"],
            "conclusion": "Therefore X is true",
            "confidence": 0.92,
            "improvements": "Consider factor Y"
        }
        result = engine._create_result_from_json(full_data, InferenceType.FULL)
        assert isinstance(result, InferenceResult)
        assert result.confidence == 0.92
        assert len(result.inference_chain) == 3

        # Test CAUSAL analysis type
        causal_data = {
            "inference_chain": ["Step 1"],
            "conclusion": "Root cause is Z",
            "confidence": 0.85,
            "causal_chain": ["A → B", "B → C", "C → D"],
            "feedback_loops": ["Loop 1: Lower prices → Higher volume"],
            "root_cause": "Market commoditization"
        }
        result = engine._create_result_from_json(causal_data, InferenceType.CAUSAL)
        assert isinstance(result, CausalAnalysis)
        assert result.root_cause == "Market commoditization"
        assert len(result.causal_chain) == 3

        # Test CONSTRAINTS analysis type
        constraint_data = {
            "inference_chain": ["Evaluate constraints"],
            "conclusion": "Feasible with trade-offs",
            "confidence": 0.75,
            "constraint_satisfaction": {"budget": 0.8, "timeline": 0.6, "quality": 0.9},
            "overall_satisfaction": 0.75,
            "trade_offs": ["Fast delivery requires higher cost", "Quality vs timeline"]
        }
        result = engine._create_result_from_json(constraint_data, InferenceType.CONSTRAINTS)
        assert isinstance(result, ConstraintAnalysis)
        assert result.overall_satisfaction == 0.75
        assert len(result.trade_offs) == 2

    def test_pydantic_field_validation_confidence_range(self):
        """Test that Pydantic enforces confidence range (0.0-1.0)."""
        from madspark.schemas.logical_inference import InferenceResult
        from pydantic import ValidationError

        # Valid confidence
        valid_result = InferenceResult(
            inference_chain=["Step 1"],
            conclusion="Test",
            confidence=0.5
        )
        assert valid_result.confidence == 0.5

        # Invalid: confidence > 1.0
        with pytest.raises(ValidationError):
            InferenceResult(
                inference_chain=["Step 1"],
                conclusion="Test",
                confidence=1.2
            )

        # Invalid: confidence < 0.0
        with pytest.raises(ValidationError):
            InferenceResult(
                inference_chain=["Step 1"],
                conclusion="Test",
                confidence=-0.1
            )

    def test_causal_analysis_pydantic_specific_fields(self):
        """Test CausalAnalysis Pydantic model with causal-specific fields."""
        from madspark.schemas.logical_inference import CausalAnalysis

        analysis = CausalAnalysis(
            inference_chain=["Analyze market", "Identify forces"],
            conclusion="Market saturation drives price competition",
            confidence=0.88,
            causal_chain=["Saturation → Competition", "Competition → Price pressure"],
            feedback_loops=["Lower prices → Higher volume → Lower prices"],
            root_cause="Product commoditization"
        )

        assert isinstance(analysis, CausalAnalysis)
        assert analysis.root_cause == "Product commoditization"
        assert len(analysis.causal_chain) == 2
        assert len(analysis.feedback_loops) == 1

        # Test model_dump for backward compatibility
        data = analysis.model_dump()
        assert data["root_cause"] == "Product commoditization"
        assert isinstance(data, dict)

    def test_constraint_analysis_pydantic_satisfaction_scores(self):
        """Test ConstraintAnalysis with satisfaction scores validation."""
        from madspark.schemas.logical_inference import ConstraintAnalysis

        analysis = ConstraintAnalysis(
            inference_chain=["Evaluate budget", "Evaluate timeline"],
            conclusion="Project feasible with scope trade-offs",
            confidence=0.78,
            constraint_satisfaction={
                "budget": 0.85,
                "timeline": 0.65,
                "quality": 0.92,
                "resources": 0.73
            },
            overall_satisfaction=0.79,
            trade_offs=["Timeline vs budget", "Quality vs speed"]
        )

        assert analysis.overall_satisfaction == 0.79
        assert len(analysis.constraint_satisfaction) == 4
        assert analysis.constraint_satisfaction["quality"] == 0.92

    def test_contradiction_analysis_pydantic(self):
        """Test ContradictionAnalysis Pydantic model."""
        from madspark.schemas.logical_inference import ContradictionAnalysis

        analysis = ContradictionAnalysis(
            inference_chain=["Analyze positioning", "Compare with pricing"],
            conclusion="Fundamental contradiction found",
            confidence=0.93,
            contradictions=[{
                "statement1": "Premium brand positioning",
                "statement2": "Budget pricing ($9/month)",
                "severity": "high",
                "impact": "Confuses market positioning"
            }],
            resolution="Align pricing with premium positioning ($99/month)"
        )

        assert len(analysis.contradictions) == 1
        assert analysis.contradictions[0]["severity"] == "high"
        assert "premium positioning" in analysis.resolution

    def test_implications_analysis_pydantic(self):
        """Test ImplicationsAnalysis Pydantic model."""
        from madspark.schemas.logical_inference import ImplicationsAnalysis

        analysis = ImplicationsAnalysis(
            inference_chain=["Project direct impact", "Analyze dynamics"],
            conclusion="Significant industry changes expected",
            confidence=0.87,
            implications=[
                "Market disruption in distribution",
                "Competitive response within 6-12 months"
            ],
            second_order_effects=[
                "Industry consolidation",
                "Regulatory scrutiny increase",
                "New business models emerge"
            ]
        )

        assert len(analysis.implications) == 2
        assert len(analysis.second_order_effects) == 3
        assert "consolidation" in analysis.second_order_effects[0].lower()

    def test_backward_compatibility_model_dump(self):
        """Test that Pydantic models maintain backward compatibility via model_dump."""
        from madspark.schemas.logical_inference import InferenceResult

        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Analysis complete",
            confidence=0.82,
            improvements="Consider alternative approaches"
        )

        # Convert to dict for backward compatibility
        result_dict = result.model_dump()

        assert isinstance(result_dict, dict)
        assert result_dict["confidence"] == 0.82
        assert len(result_dict["inference_chain"]) == 2
        assert "improvements" in result_dict

    @pytest.mark.integration
    def test_real_api_logical_inference_integration(self):
        """Integration test with real GenAI API for logical inference."""
        import os
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from madspark.agents.genai_client import get_genai_client
        from madspark.schemas.logical_inference import InferenceResult

        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set")

        genai_client = get_genai_client()
        engine = LogicalInferenceEngine(genai_client)

        # Test real causal analysis
        result = engine.analyze(
            idea="Modular vertical farming system for urban rooftops",
            topic="Sustainable Urban Agriculture",
            context="Limited budget, existing buildings",
            analysis_type=InferenceType.CAUSAL
        )

        # Verify Pydantic model
        assert isinstance(result, InferenceResult)
        assert hasattr(result, 'model_dump')
        assert result.confidence > 0.0
        assert len(result.inference_chain) > 0
        assert len(result.conclusion) > 0
        print(f"✓ Real API test passed: Confidence = {result.confidence}")


