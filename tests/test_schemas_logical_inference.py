"""
Tests for logical inference Pydantic schemas.

Following TDD approach - these tests are written BEFORE implementation.
Tests cover validation, constraints, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError


class TestInferenceResult:
    """Tests for InferenceResult base model."""

    def test_inference_result_minimal(self):
        """Valid InferenceResult with minimal fields."""
        from madspark.schemas.logical_inference import InferenceResult

        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Final conclusion",
            confidence=0.85
        )

        assert len(result.inference_chain) == 2
        assert result.conclusion == "Final conclusion"
        assert result.confidence == 0.85

    def test_inference_result_confidence_rounding(self):
        """Confidence score rounds to 2 decimal places."""
        from madspark.schemas.logical_inference import InferenceResult

        result = InferenceResult(
            inference_chain=["Step"],
            conclusion="Conclusion",
            confidence=0.8567
        )

        assert result.confidence == 0.86

    def test_inference_result_confidence_too_low(self):
        """Confidence cannot be below 0.0."""
        from madspark.schemas.logical_inference import InferenceResult

        with pytest.raises(ValidationError) as exc_info:
            InferenceResult(
                inference_chain=["Step"],
                conclusion="Conclusion",
                confidence=-0.1
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_inference_result_confidence_too_high(self):
        """Confidence cannot exceed 1.0."""
        from madspark.schemas.logical_inference import InferenceResult

        with pytest.raises(ValidationError) as exc_info:
            InferenceResult(
                inference_chain=["Step"],
                conclusion="Conclusion",
                confidence=1.1
            )
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_inference_result_with_improvements(self):
        """InferenceResult supports improvements field."""
        from madspark.schemas.logical_inference import InferenceResult

        result = InferenceResult(
            inference_chain=["Step 1"],
            conclusion="Conclusion",
            confidence=0.9,
            improvements="Suggested improvements here"
        )

        assert result.improvements == "Suggested improvements here"

    def test_inference_result_empty_inference_chain(self):
        """Inference chain must have at least one step."""
        from madspark.schemas.logical_inference import InferenceResult

        with pytest.raises(ValidationError) as exc_info:
            InferenceResult(
                inference_chain=[],
                conclusion="Conclusion",
                confidence=0.8
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_inference_result_conclusion_too_short(self):
        """Conclusion must be at least 1 character."""
        from madspark.schemas.logical_inference import InferenceResult

        with pytest.raises(ValidationError) as exc_info:
            InferenceResult(
                inference_chain=["Step"],
                conclusion="",
                confidence=0.8
            )
        assert "conclusion" in str(exc_info.value).lower()


class TestCausalAnalysis:
    """Tests for CausalAnalysis model."""

    def test_causal_analysis_valid(self):
        """Valid CausalAnalysis with all fields."""
        from madspark.schemas.logical_inference import CausalAnalysis

        analysis = CausalAnalysis(
            inference_chain=["Cause 1", "Cause 2"],
            conclusion="Final effect",
            confidence=0.8,
            causal_chain=["A causes B", "B causes C"],
            feedback_loops=["Loop 1"],
            root_cause="Root cause identified"
        )

        assert len(analysis.causal_chain) == 2
        assert len(analysis.feedback_loops) == 1
        assert analysis.root_cause == "Root cause identified"

    def test_causal_analysis_optional_fields(self):
        """CausalAnalysis optional fields can be None."""
        from madspark.schemas.logical_inference import CausalAnalysis

        analysis = CausalAnalysis(
            inference_chain=["Step"],
            conclusion="Conclusion",
            confidence=0.7
        )

        assert analysis.causal_chain is None
        assert analysis.feedback_loops is None
        assert analysis.root_cause is None


class TestConstraintAnalysis:
    """Tests for ConstraintAnalysis model."""

    def test_constraint_analysis_valid(self):
        """Valid ConstraintAnalysis with all fields."""
        from madspark.schemas.logical_inference import ConstraintAnalysis

        analysis = ConstraintAnalysis(
            inference_chain=["Check 1", "Check 2"],
            conclusion="Constraints satisfied",
            confidence=0.75,
            constraint_satisfaction={"cost": 0.8, "time": 0.6},
            overall_satisfaction=0.7,
            trade_offs=["Trade-off 1", "Trade-off 2"]
        )

        assert len(analysis.constraint_satisfaction) == 2
        assert analysis.overall_satisfaction == 0.7
        assert len(analysis.trade_offs) == 2

    def test_constraint_analysis_overall_satisfaction_rounding(self):
        """Overall satisfaction rounds to 2 decimal places."""
        from madspark.schemas.logical_inference import ConstraintAnalysis

        analysis = ConstraintAnalysis(
            inference_chain=["Step"],
            conclusion="Conclusion",
            confidence=0.8,
            overall_satisfaction=0.6789
        )

        assert analysis.overall_satisfaction == 0.68


class TestContradictionAnalysis:
    """Tests for ContradictionAnalysis model."""

    def test_contradiction_analysis_valid(self):
        """Valid ContradictionAnalysis with contradictions."""
        from madspark.schemas.logical_inference import ContradictionAnalysis

        analysis = ContradictionAnalysis(
            inference_chain=["Check 1"],
            conclusion="Contradictions found",
            confidence=0.9,
            contradictions=[
                {"statement1": "A", "statement2": "Not A", "severity": "high"}
            ],
            resolution="Resolve by clarifying assumptions"
        )

        assert len(analysis.contradictions) == 1
        assert analysis.resolution == "Resolve by clarifying assumptions"


class TestImplicationsAnalysis:
    """Tests for ImplicationsAnalysis model."""

    def test_implications_analysis_valid(self):
        """Valid ImplicationsAnalysis with implications."""
        from madspark.schemas.logical_inference import ImplicationsAnalysis

        analysis = ImplicationsAnalysis(
            inference_chain=["Derive 1", "Derive 2"],
            conclusion="Multiple implications identified",
            confidence=0.85,
            implications=["Implication 1", "Implication 2"],
            second_order_effects=["Effect 1", "Effect 2"]
        )

        assert len(analysis.implications) == 2
        assert len(analysis.second_order_effects) == 2


class TestLogicalInferenceAdapters:
    """Tests for adapter conversions with logical inference schemas."""

    def test_inference_result_to_genai_schema(self):
        """InferenceResult converts to GenAI schema."""
        from madspark.schemas.logical_inference import InferenceResult
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(InferenceResult)

        assert schema["type"] == "OBJECT"
        assert "inference_chain" in schema["properties"]
        assert schema["properties"]["inference_chain"]["type"] == "ARRAY"
        assert "conclusion" in schema["properties"]
        assert "confidence" in schema["properties"]

    def test_genai_response_to_inference_result(self):
        """GenAI JSON response parses to InferenceResult."""
        from madspark.schemas.logical_inference import InferenceResult
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "inference_chain": ["Step 1", "Step 2"],
            "conclusion": "Final conclusion",
            "confidence": 0.85
        })

        result = genai_response_to_pydantic(response_text, InferenceResult)

        assert isinstance(result, InferenceResult)
        assert len(result.inference_chain) == 2
        assert result.confidence == 0.85

    def test_genai_response_to_causal_analysis(self):
        """GenAI response parses to CausalAnalysis."""
        from madspark.schemas.logical_inference import CausalAnalysis
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "inference_chain": ["Step"],
            "conclusion": "Conclusion",
            "confidence": 0.8,
            "causal_chain": ["A causes B"],
            "root_cause": "Root"
        })

        result = genai_response_to_pydantic(response_text, CausalAnalysis)

        assert isinstance(result, CausalAnalysis)
        assert result.root_cause == "Root"


class TestBackwardCompatibility:
    """Tests for backward compatibility with dict format."""

    def test_inference_result_to_dict(self):
        """InferenceResult serializes to dict for backward compatibility."""
        from madspark.schemas.logical_inference import InferenceResult

        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Conclusion",
            confidence=0.85,
            improvements="Improvements"
        )

        data = result.model_dump()

        assert isinstance(data, dict)
        assert data["inference_chain"] == ["Step 1", "Step 2"]
        assert data["confidence"] == 0.85
        assert data["improvements"] == "Improvements"

    def test_dict_excludes_none_values(self):
        """model_dump excludes None values when specified."""
        from madspark.schemas.logical_inference import CausalAnalysis

        analysis = CausalAnalysis(
            inference_chain=["Step"],
            conclusion="Conclusion",
            confidence=0.8
        )

        data = analysis.model_dump(exclude_none=True)

        assert "causal_chain" not in data
        assert "feedback_loops" not in data
        assert "inference_chain" in data
