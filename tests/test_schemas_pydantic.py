"""
Comprehensive tests for Pydantic schema models.

Tests validation, constraints, adapters, and integration with GenAI format.
Following TDD: these tests are written BEFORE implementation.
"""

import pytest
import json
from pydantic import ValidationError

# These imports will fail initially - that's the TDD approach
from madspark.schemas.base import TitledItem, ConfidenceRated, ScoredEvaluation
from madspark.schemas.evaluation import (
    EvaluatorResponse,
    DimensionScore,
    CriticEvaluation,
    CriticEvaluations
)
from madspark.schemas.adapters import (
    pydantic_to_genai_schema,
    genai_response_to_pydantic
)


class TestBaseModels:
    """Test base model validation and constraints."""

    def test_titled_item_valid(self):
        """Valid TitledItem should create successfully."""
        item = TitledItem(
            title="Test Title",
            description="Test description with sufficient length"
        )
        assert item.title == "Test Title"
        assert item.description == "Test description with sufficient length"

    def test_titled_item_title_empty(self):
        """Empty title should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TitledItem(title="", description="Valid description")
        errors = exc_info.value.errors()
        assert any('title' in str(error) for error in errors)

    def test_titled_item_title_too_long(self):
        """Title exceeding 200 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TitledItem(title="A" * 201, description="Valid description")
        errors = exc_info.value.errors()
        assert any('title' in str(error) for error in errors)

    def test_titled_item_description_empty(self):
        """Empty description should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TitledItem(title="Valid Title", description="")
        errors = exc_info.value.errors()
        assert any('description' in str(error) for error in errors)

    def test_titled_item_description_too_long(self):
        """Description exceeding 2000 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TitledItem(title="Valid Title", description="A" * 2001)
        errors = exc_info.value.errors()
        assert any('description' in str(error) for error in errors)

    def test_confidence_rated_valid(self):
        """Valid confidence score should create successfully."""
        model = ConfidenceRated(confidence=0.85)
        assert model.confidence == 0.85

    def test_confidence_rated_rounding(self):
        """Confidence should round to 2 decimal places."""
        model = ConfidenceRated(confidence=0.8567)
        assert model.confidence == 0.86

    def test_confidence_rated_too_low(self):
        """Confidence below 0.0 should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ConfidenceRated(confidence=-0.1)
        errors = exc_info.value.errors()
        assert any('confidence' in str(error) for error in errors)

    def test_confidence_rated_too_high(self):
        """Confidence above 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ConfidenceRated(confidence=1.1)
        errors = exc_info.value.errors()
        assert any('confidence' in str(error) for error in errors)

    def test_confidence_rated_boundary_lower(self):
        """Confidence exactly 0.0 should be valid."""
        model = ConfidenceRated(confidence=0.0)
        assert model.confidence == 0.0

    def test_confidence_rated_boundary_upper(self):
        """Confidence exactly 1.0 should be valid."""
        model = ConfidenceRated(confidence=1.0)
        assert model.confidence == 1.0

    def test_scored_evaluation_valid(self):
        """Valid scored evaluation should create successfully."""
        eval_obj = ScoredEvaluation(
            score=8.5,
            critique="Excellent concept with strong execution and clear market fit"
        )
        assert eval_obj.score == 8.5
        assert "Excellent" in eval_obj.critique

    def test_scored_evaluation_score_rounding(self):
        """Score should round to 1 decimal place."""
        eval_obj = ScoredEvaluation(
            score=7.89,
            critique="Good idea with potential for growth"
        )
        assert eval_obj.score == 7.9

    def test_scored_evaluation_score_too_low(self):
        """Score below 0.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ScoredEvaluation(score=-1, critique="Invalid negative score test")

    def test_scored_evaluation_score_too_high(self):
        """Score above 10.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ScoredEvaluation(score=11, critique="Invalid high score test")

    def test_scored_evaluation_score_boundary_lower(self):
        """Score exactly 0.0 should be valid."""
        eval_obj = ScoredEvaluation(score=0.0, critique="Minimum valid score test")
        assert eval_obj.score == 0.0

    def test_scored_evaluation_score_boundary_upper(self):
        """Score exactly 10.0 should be valid."""
        eval_obj = ScoredEvaluation(score=10.0, critique="Maximum valid score test")
        assert eval_obj.score == 10.0

    def test_scored_evaluation_critique_too_short(self):
        """Critique under 10 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ScoredEvaluation(score=5, critique="Too short")
        errors = exc_info.value.errors()
        assert any('critique' in str(error) for error in errors)

    def test_scored_evaluation_critique_exactly_10_chars(self):
        """Critique with exactly 10 chars should be valid."""
        eval_obj = ScoredEvaluation(score=5, critique="1234567890")
        assert len(eval_obj.critique) == 10


class TestEvaluationModels:
    """Test evaluation-specific models."""

    def test_evaluator_response_minimal(self):
        """Evaluator with only required fields should work."""
        eval_obj = EvaluatorResponse(
            score=7.0,
            critique="Solid concept with significant potential for growth"
        )
        assert eval_obj.score == 7.0
        assert eval_obj.strengths is None
        assert eval_obj.weaknesses is None

    def test_evaluator_response_full(self):
        """Evaluator with all fields should work."""
        eval_obj = EvaluatorResponse(
            score=8.5,
            critique="Strong innovative approach with clear value proposition",
            strengths=["Novel technology", "Clear market need"],
            weaknesses=["High initial cost"]
        )
        assert len(eval_obj.strengths) == 2
        assert len(eval_obj.weaknesses) == 1
        assert "Novel" in eval_obj.strengths[0]

    def test_evaluator_response_empty_arrays(self):
        """Evaluator with empty arrays should work."""
        eval_obj = EvaluatorResponse(
            score=5.0,
            critique="Neutral evaluation with no specific highlights",
            strengths=[],
            weaknesses=[]
        )
        assert eval_obj.strengths == []
        assert eval_obj.weaknesses == []

    def test_dimension_score_with_reasoning(self):
        """DimensionScore with reasoning should work."""
        dim = DimensionScore(
            score=9.0,
            reasoning="Excellent feasibility due to existing infrastructure"
        )
        assert dim.score == 9.0
        assert "feasibility" in dim.reasoning

    def test_dimension_score_without_reasoning(self):
        """DimensionScore without reasoning should work."""
        dim = DimensionScore(score=7.5)
        assert dim.score == 7.5
        assert dim.reasoning is None

    def test_dimension_score_reasoning_too_long(self):
        """Reasoning exceeding 1000 chars should raise ValidationError."""
        with pytest.raises(ValidationError):
            DimensionScore(score=5.0, reasoning="A" * 1001)

    def test_critic_evaluation_structure(self):
        """CriticEvaluation should match expected structure."""
        critic = CriticEvaluation(
            score=6.5,
            comment="Interesting concept but faces significant challenges",
            strengths=["Innovative approach"],
            weaknesses=["High risk factor"]
        )
        assert critic.score == 6.5
        assert "challenging" in critic.comment or "challenges" in critic.comment

    def test_critic_evaluation_minimal(self):
        """CriticEvaluation with minimal fields should work."""
        critic = CriticEvaluation(
            score=7.0,
            comment="Standard evaluation without detailed breakdown"
        )
        assert critic.score == 7.0
        assert critic.strengths is None
        assert critic.weaknesses is None

    def test_critic_evaluations_array(self):
        """CriticEvaluations should handle array of evaluations."""
        evals = CriticEvaluations([
            CriticEvaluation(score=8, comment="Great idea with strong potential"),
            CriticEvaluation(score=6, comment="Needs significant improvement")
        ])
        assert len(evals) == 2
        assert evals[0].score == 8.0
        assert evals[1].score == 6.0

    def test_critic_evaluations_empty_array(self):
        """CriticEvaluations with empty array should work."""
        evals = CriticEvaluations([])
        assert len(evals) == 0

    def test_critic_evaluations_iteration(self):
        """CriticEvaluations should support iteration."""
        evals = CriticEvaluations([
            CriticEvaluation(score=7, comment="Good concept overall"),
            CriticEvaluation(score=5, comment="Average execution quality")
        ])
        scores = [eval_item.score for eval_item in evals]
        assert scores == [7.0, 5.0]

    def test_critic_evaluations_single_item(self):
        """CriticEvaluations with single item should work."""
        evals = CriticEvaluations([
            CriticEvaluation(score=9, comment="Exceptional innovative approach")
        ])
        assert len(evals) == 1
        assert evals[0].score == 9.0


class TestAdapters:
    """Test Pydantic to GenAI schema conversion."""

    def test_optional_field_with_description_preserved(self):
        """Optional fields with descriptions should convert correctly."""
        schema = pydantic_to_genai_schema(DimensionScore)

        reasoning_schema = schema['properties']['reasoning']
        assert reasoning_schema['type'] == 'STRING'
        assert reasoning_schema['nullable'] is True
        assert 'Explanation for the assigned score' in reasoning_schema['description']
        assert reasoning_schema['maxLength'] == 1000

    def test_simple_model_conversion(self):
        """Simple model should convert to GenAI format."""
        schema = pydantic_to_genai_schema(DimensionScore)

        assert schema['type'] == 'OBJECT'
        assert 'properties' in schema
        assert 'score' in schema['properties']
        assert schema['properties']['score']['type'] == 'NUMBER'
        # New Gemini API feature: numeric constraints
        assert schema['properties']['score']['minimum'] == 0.0
        assert schema['properties']['score']['maximum'] == 10.0

    def test_nested_model_conversion(self):
        """Nested model should convert recursively."""
        schema = pydantic_to_genai_schema(EvaluatorResponse)

        assert schema['type'] == 'OBJECT'
        assert 'score' in schema['properties']
        assert 'critique' in schema['properties']
        assert 'strengths' in schema['properties']
        assert 'weaknesses' in schema['properties']

        # Check array type for strengths
        strengths_schema = schema['properties']['strengths']
        assert strengths_schema['type'] == 'ARRAY'
        assert strengths_schema['items']['type'] == 'STRING'

    def test_array_model_conversion(self):
        """Array wrapper should convert to ARRAY type."""
        schema = pydantic_to_genai_schema(CriticEvaluations)

        assert schema['type'] == 'ARRAY'
        assert 'items' in schema
        assert schema['items']['type'] == 'OBJECT'
        assert 'score' in schema['items']['properties']

    def test_required_fields_preserved(self):
        """Required fields should be listed in schema."""
        schema = pydantic_to_genai_schema(EvaluatorResponse)

        assert 'required' in schema
        assert 'score' in schema['required']
        assert 'critique' in schema['required']
        # Optional fields should NOT be required
        if 'strengths' in schema['required']:
            pytest.fail("strengths should not be required")
        if 'weaknesses' in schema['required']:
            pytest.fail("weaknesses should not be required")

    def test_string_constraints_preserved(self):
        """String length constraints should be preserved."""
        schema = pydantic_to_genai_schema(TitledItem)

        title_schema = schema['properties']['title']
        assert title_schema['maxLength'] == 200
        assert title_schema['minLength'] == 1

        desc_schema = schema['properties']['description']
        assert desc_schema['maxLength'] == 2000
        assert desc_schema['minLength'] == 1

    def test_genai_response_parsing(self):
        """GenAI response should parse into Pydantic model."""
        response_text = json.dumps({
            "score": 8.5,
            "critique": "Excellent idea with strong potential for market success",
            "strengths": ["Innovative technology", "Clear market need"],
            "weaknesses": ["High initial cost"]
        })

        result = genai_response_to_pydantic(response_text, EvaluatorResponse)

        assert isinstance(result, EvaluatorResponse)
        assert result.score == 8.5
        assert len(result.strengths) == 2
        assert len(result.weaknesses) == 1

    def test_genai_response_validation_error(self):
        """Invalid GenAI response should raise ValidationError."""
        response_text = json.dumps({
            "score": 11,  # Invalid: exceeds maximum
            "critique": "Score too high for validation"
        })

        with pytest.raises(ValidationError):
            genai_response_to_pydantic(response_text, EvaluatorResponse)

    def test_genai_response_array_parsing(self):
        """Array response should parse correctly."""
        response_text = json.dumps([
            {"score": 8, "comment": "Great innovative concept"},
            {"score": 6, "comment": "Good but needs refinement"}
        ])

        result = genai_response_to_pydantic(response_text, CriticEvaluations)

        assert len(result) == 2
        assert result[0].score == 8.0
        assert result[1].score == 6.0

    def test_genai_response_malformed_json(self):
        """Malformed JSON should raise appropriate error."""
        response_text = "{invalid json}"

        with pytest.raises(json.JSONDecodeError):
            genai_response_to_pydantic(response_text, EvaluatorResponse)


class TestConstraints:
    """Test field constraints and validation."""

    def test_numeric_minimum_enforced(self):
        """Minimum numeric constraint should be enforced."""
        with pytest.raises(ValidationError):
            DimensionScore(score=-0.5)

    def test_numeric_maximum_enforced(self):
        """Maximum numeric constraint should be enforced."""
        with pytest.raises(ValidationError):
            DimensionScore(score=10.5)

    def test_string_min_length_enforced(self):
        """Minimum string length should be enforced."""
        with pytest.raises(ValidationError):
            ScoredEvaluation(score=5, critique="Short")

    def test_string_max_length_enforced(self):
        """Maximum string length should be enforced."""
        with pytest.raises(ValidationError):
            TitledItem(title="A" * 201, description="Valid description here")

    def test_required_field_missing(self):
        """Missing required field should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvaluatorResponse(critique="Missing score field")

    def test_optional_field_can_be_none(self):
        """Optional field can be explicitly None."""
        eval_obj = EvaluatorResponse(
            score=7.0,
            critique="Valid evaluation",
            strengths=None  # Explicit None
        )
        assert eval_obj.strengths is None

    def test_optional_field_can_be_omitted(self):
        """Optional field can be completely omitted."""
        eval_obj = EvaluatorResponse(
            score=7.0,
            critique="Valid evaluation without optional fields"
            # strengths not provided
        )
        assert eval_obj.strengths is None

    def test_wrong_type_raises_error(self):
        """Wrong field type should raise ValidationError."""
        with pytest.raises(ValidationError):
            DimensionScore(score="eight point five")  # String instead of number


class TestJSONSerialization:
    """Test JSON serialization and deserialization."""

    def test_model_dump_creates_dict(self):
        """model_dump() should create dictionary."""
        eval_obj = EvaluatorResponse(
            score=8.0,
            critique="Test evaluation for serialization"
        )
        data = eval_obj.model_dump()

        assert isinstance(data, dict)
        assert data['score'] == 8.0
        assert data['critique'] == "Test evaluation for serialization"

    def test_model_dump_includes_none_values(self):
        """model_dump() should include None values by default."""
        eval_obj = EvaluatorResponse(
            score=7.5,
            critique="Test with None values"
        )
        data = eval_obj.model_dump()

        assert 'strengths' in data
        assert data['strengths'] is None

    def test_model_dump_json_creates_string(self):
        """model_dump_json() should create JSON string."""
        eval_obj = EvaluatorResponse(
            score=7.5,
            critique="Test JSON serialization"
        )
        json_str = eval_obj.model_dump_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data['score'] == 7.5

    def test_model_validate_from_dict(self):
        """model_validate() should create from dict."""
        data = {
            "score": 9.0,
            "critique": "Excellent concept with strong execution"
        }
        eval_obj = EvaluatorResponse.model_validate(data)

        assert eval_obj.score == 9.0
        assert eval_obj.critique == "Excellent concept with strong execution"

    def test_backward_compatibility_with_dict(self):
        """Pydantic models should convert to dict for legacy code."""
        eval_obj = EvaluatorResponse(
            score=8.5,
            critique="Test backward compatibility",
            strengths=["Strength A", "Strength B"]
        )
        data = eval_obj.model_dump()

        # Legacy code expects dict access
        assert data['score'] == 8.5
        assert isinstance(data['strengths'], list)
        assert len(data['strengths']) == 2

    def test_array_model_serialization(self):
        """Array models should serialize correctly."""
        evals = CriticEvaluations([
            CriticEvaluation(score=8, comment="First evaluation"),
            CriticEvaluation(score=6, comment="Second evaluation")
        ])

        # Access root for RootModel
        data = [item.model_dump() for item in evals]

        assert len(data) == 2
        assert data[0]['score'] == 8.0
        assert data[1]['score'] == 6.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_confidence_with_many_decimals(self):
        """Confidence with many decimal places should round correctly."""
        model = ConfidenceRated(confidence=0.123456789)
        assert model.confidence == 0.12

    def test_score_with_many_decimals(self):
        """Score with many decimal places should round correctly."""
        eval_obj = ScoredEvaluation(
            score=7.123456789,
            critique="Testing decimal rounding behavior"
        )
        assert eval_obj.score == 7.1

    def test_unicode_in_strings(self):
        """Unicode characters should be handled correctly."""
        item = TitledItem(
            title="Test with émojis 🚀",
            description="Description with spëcial çharacters"
        )
        assert "🚀" in item.title
        assert "çharacters" in item.description

    def test_very_long_arrays(self):
        """Arrays with many items should work."""
        strengths = [f"Strength {i}" for i in range(100)]
        eval_obj = EvaluatorResponse(
            score=8.0,
            critique="Testing with many strengths",
            strengths=strengths
        )
        assert len(eval_obj.strengths) == 100

    def test_nested_quotes_in_strings(self):
        """Strings with nested quotes should serialize correctly."""
        eval_obj = EvaluatorResponse(
            score=7.0,
            critique='Evaluation with "quoted" and \'single\' quotes'
        )
        json_str = eval_obj.model_dump_json()
        parsed = json.loads(json_str)
        assert '"quoted"' in parsed['critique']
