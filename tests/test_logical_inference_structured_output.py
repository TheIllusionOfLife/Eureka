"""Tests for Logical Inference structured output migration.

Following TDD: These tests verify that logical inference uses structured
output instead of text parsing with regex.
"""

import pytest
from unittest.mock import Mock, patch
import json


class TestFullAnalysisStructuredOutput:
    """Test that full analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_full_analysis_uses_structured_output_config(self, mock_get_model):
        """Should use response_mime_type and response_schema for full analysis."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from google.genai import types

        mock_get_model.return_value = "gemini-1.5-flash"

        # Create mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "inference_chain": ["Step 1", "Step 2"],
            "conclusion": "Test conclusion",
            "confidence": 0.8,
            "improvements": "Test improvements"
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        # Perform full analysis
        result = engine.analyze(
            idea="Test idea",
            topic="AI safety",
            context="Testing context",
            analysis_type=InferenceType.FULL
        )

        # Verify generate_content was called with structured output config
        call_args = mock_client.models.generate_content.call_args
        assert call_args is not None
        assert 'config' in call_args.kwargs

        api_config = call_args.kwargs['config']
        assert isinstance(api_config, types.GenerateContentConfig)
        assert api_config.response_mime_type == "application/json"
        assert api_config.response_schema is not None

    @patch('madspark.agents.genai_client.get_model_name')
    def test_full_analysis_parses_json_response(self, mock_get_model):
        """Should parse JSON response for full analysis."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "inference_chain": ["Premise 1", "Premise 2", "Conclusion"],
            "conclusion": "Therefore, the idea is feasible",
            "confidence": 0.85,
            "improvements": "Consider scalability"
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Build an AI system",
            topic="AI development",
            context="Limited budget",
            analysis_type=InferenceType.FULL
        )

        # Should have parsed the JSON correctly
        assert result.inference_chain == ["Premise 1", "Premise 2", "Conclusion"]
        assert result.conclusion == "Therefore, the idea is feasible"
        assert result.confidence == 0.85
        assert result.improvements == "Consider scalability"


class TestCausalAnalysisStructuredOutput:
    """Test that causal analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_causal_analysis_uses_structured_output(self, mock_get_model):
        """Should use structured output for causal analysis."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from google.genai import types

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "causal_chain": ["Initial state", "First effect", "Second effect"],
            "feedback_loops": ["Loop 1", "Loop 2"],
            "root_cause": "Primary driver",
            "conclusion": "Causal analysis complete",
            "confidence": 0.75
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Test idea",
            topic="Testing",
            context="Test context",
            analysis_type=InferenceType.CAUSAL
        )

        # Verify structured output was used
        call_args = mock_client.models.generate_content.call_args
        api_config = call_args.kwargs['config']
        assert api_config.response_mime_type == "application/json"

        # Verify parsed data
        assert result.causal_chain == ["Initial state", "First effect", "Second effect"]
        assert result.feedback_loops == ["Loop 1", "Loop 2"]
        assert result.root_cause == "Primary driver"


class TestConstraintAnalysisStructuredOutput:
    """Test that constraint analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_constraint_analysis_uses_structured_output(self, mock_get_model):
        """Should use structured output for constraint analysis."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "constraint_satisfaction": {
                "Budget": 85.0,
                "Timeline": 70.0,
                "Quality": 90.0
            },
            "overall_satisfaction": 81.67,
            "trade_offs": ["Cost vs Quality", "Speed vs Accuracy"],
            "conclusion": "Constraints moderately satisfied",
            "confidence": 0.82
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Project plan",
            topic="Planning",
            context="Resource constraints",
            analysis_type=InferenceType.CONSTRAINTS
        )

        # Verify parsed constraint data
        assert result.constraint_satisfaction == {
            "Budget": 85.0,
            "Timeline": 70.0,
            "Quality": 90.0
        }
        assert result.overall_satisfaction == 81.67
        assert result.trade_offs == ["Cost vs Quality", "Speed vs Accuracy"]


class TestContradictionAnalysisStructuredOutput:
    """Test that contradiction analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_contradiction_analysis_with_contradictions(self, mock_get_model):
        """Should parse contradictions from structured output."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "contradictions": [
                {
                    "conflict": "Claim A contradicts Claim B",
                    "severity": "HIGH",
                    "type": "Logical inconsistency",
                    "explanation": "These statements cannot both be true"
                }
            ],
            "resolution": "Resolve by clarifying assumptions",
            "conclusion": "Found 1 logical contradiction(s)",
            "confidence": 0.6
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Contradictory idea",
            topic="Logic",
            context="Testing",
            analysis_type=InferenceType.CONTRADICTION
        )

        # Verify contradiction parsing
        assert len(result.contradictions) == 1
        assert result.contradictions[0]["conflict"] == "Claim A contradicts Claim B"
        assert result.contradictions[0]["severity"] == "HIGH"
        assert result.resolution == "Resolve by clarifying assumptions"

    @patch('madspark.agents.genai_client.get_model_name')
    def test_contradiction_analysis_no_contradictions(self, mock_get_model):
        """Should handle case with no contradictions."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "contradictions": [],
            "resolution": None,
            "conclusion": "No logical contradictions detected",
            "confidence": 0.9
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Consistent idea",
            topic="Logic",
            context="Testing",
            analysis_type=InferenceType.CONTRADICTION
        )

        # Verify no contradictions
        assert result.contradictions == []
        assert result.conclusion == "No logical contradictions detected"
        assert result.confidence == 0.9


class TestImplicationsAnalysisStructuredOutput:
    """Test that implications analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_implications_analysis_uses_structured_output(self, mock_get_model):
        """Should use structured output for implications."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "implications": [
                "Direct implication 1",
                "Direct implication 2"
            ],
            "second_order_effects": [
                "Secondary effect 1",
                "Secondary effect 2"
            ],
            "conclusion": "Analysis reveals 2 direct implications",
            "confidence": 0.8
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="New policy",
            topic="Policy",
            context="Implementation",
            analysis_type=InferenceType.IMPLICATIONS
        )

        # Verify implications parsing
        assert result.implications == ["Direct implication 1", "Direct implication 2"]
        assert result.second_order_effects == ["Secondary effect 1", "Secondary effect 2"]
        assert len(result.implications) == 2


class TestStructuredOutputSchemas:
    """Test that schemas are properly defined."""

    def test_full_analysis_schema_exists(self):
        """Schema for full analysis should be defined."""
        from madspark.agents.response_schemas import FULL_ANALYSIS_SCHEMA

        assert FULL_ANALYSIS_SCHEMA is not None
        assert isinstance(FULL_ANALYSIS_SCHEMA, dict)
        assert "type" in FULL_ANALYSIS_SCHEMA
        assert "properties" in FULL_ANALYSIS_SCHEMA

    def test_full_analysis_schema_required_fields(self):
        """Schema should have required fields for full analysis."""
        from madspark.agents.response_schemas import FULL_ANALYSIS_SCHEMA

        properties = FULL_ANALYSIS_SCHEMA["properties"]
        assert "inference_chain" in properties
        assert "conclusion" in properties
        assert "confidence" in properties

        required = FULL_ANALYSIS_SCHEMA.get("required", [])
        assert "inference_chain" in required
        assert "conclusion" in required
        assert "confidence" in required

    def test_causal_analysis_schema_exists(self):
        """Schema for causal analysis should be defined."""
        from madspark.agents.response_schemas import CAUSAL_ANALYSIS_SCHEMA

        assert CAUSAL_ANALYSIS_SCHEMA is not None
        properties = CAUSAL_ANALYSIS_SCHEMA["properties"]
        assert "causal_chain" in properties
        assert "root_cause" in properties

    def test_constraint_analysis_schema_exists(self):
        """Schema for constraint analysis should be defined."""
        from madspark.agents.response_schemas import CONSTRAINT_ANALYSIS_SCHEMA

        assert CONSTRAINT_ANALYSIS_SCHEMA is not None
        properties = CONSTRAINT_ANALYSIS_SCHEMA["properties"]
        assert "constraint_satisfaction" in properties
        assert "overall_satisfaction" in properties

    def test_contradiction_analysis_schema_exists(self):
        """Schema for contradiction analysis should be defined."""
        from madspark.agents.response_schemas import CONTRADICTION_ANALYSIS_SCHEMA

        assert CONTRADICTION_ANALYSIS_SCHEMA is not None
        properties = CONTRADICTION_ANALYSIS_SCHEMA["properties"]
        assert "contradictions" in properties

    def test_implications_analysis_schema_exists(self):
        """Schema for implications analysis should be defined."""
        from madspark.agents.response_schemas import IMPLICATIONS_ANALYSIS_SCHEMA

        assert IMPLICATIONS_ANALYSIS_SCHEMA is not None
        properties = IMPLICATIONS_ANALYSIS_SCHEMA["properties"]
        assert "implications" in properties
        assert "second_order_effects" in properties


class TestBatchAnalysisStructuredOutput:
    """Test that batch analysis uses structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_batch_analysis_uses_structured_output(self, mock_get_model):
        """Should use structured output for batch analysis."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
        from google.genai import types

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        # Batch response should be an array of analysis results
        mock_response.text = json.dumps([
            {
                "inference_chain": ["Step 1", "Step 2"],
                "conclusion": "Conclusion for idea 1",
                "confidence": 0.8
            },
            {
                "inference_chain": ["Step A", "Step B"],
                "conclusion": "Conclusion for idea 2",
                "confidence": 0.75
            }
        ])
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        results = engine.analyze_batch(
            ideas=["Idea 1", "Idea 2"],
            topic="Testing",
            context="Batch test",
            analysis_type=InferenceType.FULL
        )

        # Verify structured output was used
        call_args = mock_client.models.generate_content.call_args
        api_config = call_args.kwargs['config']
        assert api_config.response_mime_type == "application/json"
        assert api_config.response_schema is not None

        # Verify batch parsing
        assert len(results) == 2
        assert results[0].conclusion == "Conclusion for idea 1"
        assert results[1].conclusion == "Conclusion for idea 2"


class TestErrorHandling:
    """Test error handling with structured output."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_invalid_json_raises_clear_error(self, mock_get_model):
        """Should handle invalid JSON gracefully with fallback to text parsing."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Not valid JSON"
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Test",
            topic="Test",
            context="Test",
            analysis_type=InferenceType.FULL
        )

        # Should fall back to text parsing (which may or may not succeed)
        # The key is it doesn't raise an exception
        assert result is not None
        # Text parsing will attempt to parse "Not valid JSON" and likely fail gracefully
        # Either error is set OR confidence is 0 (from failed text parsing)
        assert result.error is not None or result.confidence <= 0.5

    @patch('madspark.agents.genai_client.get_model_name')
    def test_missing_required_fields_handled(self, mock_get_model):
        """Should handle missing required fields."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        # Missing 'conclusion' required field
        mock_response.text = json.dumps({
            "inference_chain": ["Step 1"],
            "confidence": 0.8
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        result = engine.analyze(
            idea="Test",
            topic="Test",
            context="Test",
            analysis_type=InferenceType.FULL
        )

        # Should handle gracefully with error
        # Either populate with defaults or set error field
        assert result is not None
        # At minimum, should have some data even if incomplete
        assert result.inference_chain == ["Step 1"] or result.error is not None


class TestBackwardCompatibility:
    """Ensure changes don't break existing functionality."""

    @patch('madspark.agents.genai_client.get_model_name')
    def test_existing_test_patterns_still_work(self, mock_get_model):
        """Existing test patterns should continue working."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType

        mock_get_model.return_value = "gemini-1.5-flash"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "inference_chain": ["Test step"],
            "conclusion": "Test conclusion",
            "confidence": 0.5
        })
        mock_client.models.generate_content.return_value = mock_response

        engine = LogicalInferenceEngine(genai_client=mock_client)

        # This is the pattern used in existing tests
        result = engine.analyze(
            idea="Test idea",
            topic="topic",
            context="context",
            analysis_type=InferenceType.FULL
        )

        assert isinstance(result.inference_chain, list)
        assert isinstance(result.conclusion, str)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
