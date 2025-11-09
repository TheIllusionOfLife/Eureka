"""Tests for Enhanced Reasoning structured output migration.

Following TDD: These tests verify that enhanced reasoning uses structured
output instead of text parsing.
"""

import pytest
from unittest.mock import Mock, patch


class TestDimensionScoreStructuredOutput:
    """Test that dimension scoring uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_uses_structured_output_config(self, mock_get_model):
        """Should use response_mime_type and response_schema."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
        from google.genai import types

        mock_get_model.return_value = "gemini-1.5-flash"

        # Create mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 8.5, "reasoning": "Good idea"}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        # Evaluate a dimension
        _score = evaluator._evaluate_dimension(
            idea="Test idea",
            context={"topic": "AI", "context": "testing"},
            dimension="feasibility",
            config={"weight": 1.0, "range": (1, 10)}
        )

        # Verify generate_content was called with structured output config
        call_args = mock_client.models.generate_content.call_args
        assert call_args is not None

        # Check that config parameter was passed
        assert 'config' in call_args.kwargs
        api_config = call_args.kwargs['config']

        # Verify it's a GenerateContentConfig with structured output
        assert isinstance(api_config, types.GenerateContentConfig)
        assert api_config.response_mime_type == "application/json"
        assert api_config.response_schema is not None

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_parses_json_response(self, mock_get_model):
        """Should parse JSON response instead of raw text."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        # Mock client that returns structured JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 7.5}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        score = evaluator._evaluate_dimension(
            idea="Test idea",
            context={"topic": "AI", "context": "testing"},
            dimension="innovation",
            config={"weight": 1.0, "range": (0, 10)}
        )

        # Should have parsed the JSON and extracted the score
        assert score == 7.5

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_handles_optional_reasoning(self, mock_get_model):
        """Should handle responses with optional reasoning field."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 9.0, "reasoning": "Excellent feasibility"}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        score = evaluator._evaluate_dimension(
            idea="Great idea",
            context={"topic": "AI", "context": "testing"},
            dimension="feasibility",
            config={"weight": 1.0, "range": (1, 10)}
        )

        # Should extract score even when reasoning is present
        assert score == 9.0

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_clamps_score_to_range(self, mock_get_model):
        """Should clamp scores to dimension range."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        # Score is 15, but range is 1-10
        mock_response.text = '{"score": 15.0}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        score = evaluator._evaluate_dimension(
            idea="Test",
            context={"topic": "AI", "context": "test"},
            dimension="impact",
            config={"weight": 1.0, "range": (1, 10)}
        )

        # Should be clamped to max of 10
        assert score == 10.0

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_raises_on_invalid_json(self, mock_get_model):
        """Should raise clear error on invalid JSON response."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = 'Not valid JSON'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with pytest.raises(RuntimeError, match="Failed to evaluate.*Failed to parse.*JSON"):
            evaluator._evaluate_dimension(
                idea="Test",
                context={"topic": "AI", "context": "test"},
                dimension="feasibility",
                config={"weight": 1.0, "range": (1, 10)}
            )

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluate_dimension_raises_on_missing_score(self, mock_get_model):
        """Should raise clear error when score field is missing."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"reasoning": "Good but no score"}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with pytest.raises(RuntimeError, match="Failed to evaluate.*score"):
            evaluator._evaluate_dimension(
                idea="Test",
                context={"topic": "AI", "context": "test"},
                dimension="innovation",
                config={"weight": 1.0, "range": (0, 10)}
            )


class TestDimensionScoreSchema:
    """Test the DIMENSION_SCORE_SCHEMA definition."""

    def test_dimension_score_schema_exists(self):
        """Schema should be defined in response_schemas module."""
        from madspark.agents.response_schemas import DIMENSION_SCORE_SCHEMA

        assert DIMENSION_SCORE_SCHEMA is not None
        assert isinstance(DIMENSION_SCORE_SCHEMA, dict)

    def test_dimension_score_schema_has_required_fields(self):
        """Schema should define score as required field."""
        from madspark.agents.response_schemas import DIMENSION_SCORE_SCHEMA

        assert "type" in DIMENSION_SCORE_SCHEMA
        assert "properties" in DIMENSION_SCORE_SCHEMA
        assert "score" in DIMENSION_SCORE_SCHEMA["properties"]
        assert "required" in DIMENSION_SCORE_SCHEMA
        assert "score" in DIMENSION_SCORE_SCHEMA["required"]

    def test_dimension_score_schema_has_optional_reasoning(self):
        """Schema should have optional reasoning field."""
        from madspark.agents.response_schemas import DIMENSION_SCORE_SCHEMA

        assert "reasoning" in DIMENSION_SCORE_SCHEMA["properties"]
        # reasoning should NOT be in required list
        assert "reasoning" not in DIMENSION_SCORE_SCHEMA["required"]

    def test_dimension_score_schema_score_is_number(self):
        """Score field should be NUMBER type."""
        from madspark.agents.response_schemas import DIMENSION_SCORE_SCHEMA

        score_def = DIMENSION_SCORE_SCHEMA["properties"]["score"]
        assert score_def["type"] == "NUMBER"


class TestEnhancedReasoningIntegration:
    """Integration tests for enhanced reasoning with structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_multi_dimensional_evaluation_uses_structured_output(self, mock_get_model):
        """Full evaluation should use structured output for all dimensions."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        # Return different scores for different dimensions (default has 7 dimensions)
        mock_responses = [
            Mock(text='{"score": 8.0}'),   # feasibility
            Mock(text='{"score": 7.5}'),   # innovation
            Mock(text='{"score": 9.0}'),   # impact
            Mock(text='{"score": 8.5}'),   # cost_effectiveness
            Mock(text='{"score": 7.0}'),   # scalability
            Mock(text='{"score": 6.5}'),   # risk_level
            Mock(text='{"score": 8.0}'),   # timeline
        ]
        mock_client.models.generate_content.side_effect = mock_responses

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        # Evaluate with custom dimensions
        _result = evaluator.evaluate_idea(
            idea="Test idea",
            context={"topic": "AI", "context": "Testing"}
        )

        # Should have called generate_content (one per dimension)
        assert mock_client.models.generate_content.call_count >= 1

        # All dimension evaluation calls should have used structured output
        for call in mock_client.models.generate_content.call_args_list:
            # Only check calls that have config (dimension evaluations)
            if 'config' in call.kwargs:
                api_config = call.kwargs['config']
                assert api_config.response_mime_type == "application/json"


class TestBackwardCompatibility:
    """Ensure changes don't break existing functionality."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_evaluator_still_works_with_existing_tests(self, mock_get_model):
        """Existing test patterns should still work."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 8.0}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        # This is the pattern used in existing tests
        score = evaluator._evaluate_dimension(
            idea="Test",
            context={"topic": "test", "context": "test"},
            dimension="feasibility",
            config={"weight": 1.0}
        )

        assert isinstance(score, float)
        assert 0 <= score <= 10
