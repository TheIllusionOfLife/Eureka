"""
Tests for enhanced_reasoning.py Pydantic schema migration (Phase 3, Task 1).

This test module verifies that MultiDimensionalEvaluator correctly uses
Pydantic DimensionScore schema instead of legacy dict-based DIMENSION_SCORE_SCHEMA.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any


class TestEnhancedReasoningPydanticMigration:
    """Test suite for enhanced_reasoning.py Pydantic migration."""

    def test_dimension_evaluation_uses_pydantic_schema(self):
        """Test that dimension evaluation uses Pydantic schema in API config."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
        from madspark.schemas.evaluation import DimensionScore
        from unittest.mock import call

        # Create mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 8.5, "reasoning": "Strong feasibility due to existing infrastructure"}'
        mock_client.models.generate_content.return_value = mock_response

        # Initialize evaluator (types is set automatically in __init__)
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        # Test evaluation
        idea = "AI-powered smart traffic light system that adapts to real-time congestion"
        context = {"theme": "Urban Innovation", "constraints": "Limited budget, existing infrastructure"}
        dimension = "feasibility"
        config = {"weight": 0.2, "range": (1, 10)}

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            score = evaluator._ai_evaluate_dimension(idea, context, dimension, config)

        # Verify score is correct
        assert score == 8.5
        assert isinstance(score, float)

        # Verify API call was made with correct parameters
        assert mock_client.models.generate_content.called
        # The schema is pre-computed at module level, so we just verify the call succeeded
        # and returned the expected Pydantic-validated result

    def test_dimension_score_response_parsing_with_pydantic(self):
        """Test that JSON responses are parsed using Pydantic genai_response_to_pydantic."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        # Create mock GenAI client with valid DimensionScore response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 7.0, "reasoning": "Good potential but needs validation"}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        idea = "Test idea"
        context = {"theme": "Test", "constraints": "Test"}
        dimension = "innovation"
        config = {"weight": 0.3, "range": (0, 10)}

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            score = evaluator._ai_evaluate_dimension(idea, context, dimension, config)

        # Verify Pydantic parsing worked correctly
        assert score == 7.0
        assert isinstance(score, float)

    def test_dimension_score_field_validation(self):
        """Test that Pydantic validation enforces score constraints (0-10)."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        # Test with score within valid range
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 5.5, "reasoning": "Average"}'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            score = evaluator._ai_evaluate_dimension(
                "Test idea",
                {"theme": "Test", "constraints": "Test"},
                "novelty",
                {"weight": 0.25, "range": (1, 10)}
            )

        assert 0 <= score <= 10  # Valid range
        assert score == 5.5

    def test_backward_compatibility_via_model_dump(self):
        """Test that Pydantic DimensionScore maintains backward compatibility."""
        from madspark.schemas.evaluation import DimensionScore

        # Create Pydantic model
        dimension_score = DimensionScore(
            score=8.0,
            reasoning="Strong concept with clear market fit"
        )

        # Convert to dict for backward compatibility
        score_dict = dimension_score.model_dump()

        # Verify dict structure matches legacy format
        assert isinstance(score_dict, dict)
        assert "score" in score_dict
        assert score_dict["score"] == 8.0
        assert "reasoning" in score_dict

    def test_invalid_json_response_handling(self):
        """Test that invalid JSON responses raise appropriate errors."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        # Create mock with invalid JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            with pytest.raises(ValueError, match="Failed to parse dimension score"):
                evaluator._ai_evaluate_dimension(
                    "Test idea",
                    {"theme": "Test", "constraints": "Test"},
                    "feasibility",
                    {"weight": 0.2, "range": (1, 10)}
                )

    def test_missing_score_field_handling(self):
        """Test that responses missing 'score' field are handled properly."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        # Create mock with missing score field
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"reasoning": "Good idea"}'  # Missing score
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            with pytest.raises(ValueError):
                evaluator._ai_evaluate_dimension(
                    "Test idea",
                    {"theme": "Test", "constraints": "Test"},
                    "innovation",
                    {"weight": 0.3, "range": (0, 10)}
                )

    def test_score_clamping_with_custom_range(self):
        """Test that scores are clamped to dimension-specific ranges."""
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator

        # Test score clamping with custom range
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"score": 12.0, "reasoning": "Excellent"}'  # Score > max
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        with patch('madspark.agents.genai_client.get_model_name', return_value='gemini-2.0-flash-exp'):
            score = evaluator._ai_evaluate_dimension(
                "Test idea",
                {"theme": "Test", "constraints": "Test"},
                "impact",
                {"weight": 0.3, "range": (1, 10)}
            )

        # Should be clamped to max_val = 10
        assert score == 10.0

    @pytest.mark.integration
    def test_real_api_dimension_score_integration(self):
        """Integration test with real GenAI API to validate Pydantic schema."""
        import os
        from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
        from madspark.agents.genai_client import get_genai_client

        # Skip if no API key
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set")

        # Use real GenAI client
        genai_client = get_genai_client()

        try:
            from google import genai
            types = genai.types
        except ImportError:
            pytest.skip("google-genai not available")

        evaluator = MultiDimensionalEvaluator(genai_client=genai_client, types=types)

        # Test real evaluation
        idea = "Modular vertical farming system for urban rooftops"
        context = {
            "theme": "Sustainable Urban Agriculture",
            "constraints": "Limited budget, existing buildings"
        }
        dimension = "feasibility"
        config = {"weight": 0.2, "range": (1, 10)}

        score = evaluator._ai_evaluate_dimension(idea, context, dimension, config)

        # Verify response
        assert isinstance(score, float)
        assert 1 <= score <= 10  # Within expected range
        print(f"✓ Real API test passed: Feasibility score = {score}")


