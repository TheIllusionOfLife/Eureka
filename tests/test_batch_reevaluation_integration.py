"""Integration tests for batch re-evaluation with float score handling."""
import pytest
import asyncio
from unittest.mock import Mock, patch
import json

from madspark.core.async_coordinator import AsyncCoordinator, async_evaluate_ideas
from madspark.utils.temperature_control import TemperatureManager


class TestBatchReevaluationIntegration:
    """Integration tests for batch re-evaluation process."""
    
    @pytest.mark.asyncio
    async def test_batch_reevaluation_with_float_scores(self):
        """Test batch re-evaluation handling float scores from AI."""
        # Mock genai client to return float scores
        mock_genai_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "evaluations": [
                {"score": 7.8, "comment": "Good idea with potential"},
                {"score": 8.5, "comment": "Excellent concept"},
                {"score": 6.3, "comment": "Average but workable"}
            ]
        })
        mock_genai_client.models.generate_content.return_value = mock_response
        
        # Mock candidates
        candidates = [
            {
                "text": "AI-powered productivity tool",
                "score": 7,
                "critique": "Initial evaluation",
                "improved_idea": "Enhanced AI productivity suite"
            },
            {
                "text": "Smart home automation",
                "score": 8,
                "critique": "Initial evaluation",
                "improved_idea": "Advanced home AI system"
            },
            {
                "text": "Educational gaming platform",
                "score": 6,
                "critique": "Initial evaluation",
                "improved_idea": "Gamified learning ecosystem"
            }
        ]
        
        # This test will FAIL initially
        with patch('madspark.agents.genai_client.get_genai_client', return_value=mock_genai_client):
            # Process batch re-evaluation
            improved_ideas_text = "\n\n".join([
                f"Idea {i+1}: {c['improved_idea']}" 
                for i, c in enumerate(candidates)
            ])
            
            # Call the actual re-evaluation logic
            eval_result = await async_evaluate_ideas(
                ideas=improved_ideas_text,
                criteria="Test criteria",
                context="Re-evaluation after improvements",
                temperature=0.5,
                use_structured_output=True
            )
            
            # eval_result should be the JSON string
            # Parse the result - handle both dict and list formats
            eval_data = json.loads(eval_result) if isinstance(eval_result, str) else eval_result
            
            if isinstance(eval_data, dict) and "evaluations" in eval_data:
                evaluations = eval_data["evaluations"]
            elif isinstance(eval_data, list):
                evaluations = eval_data
            else:
                evaluations = [eval_data] if isinstance(eval_data, dict) else []
            
            # Validate scores are properly converted
            assert len(evaluations) == 3
            
            # Import and use validate_evaluation_json
            from madspark.utils.utils import validate_evaluation_json
            
            # Process each evaluation
            for i, eval_item in enumerate(evaluations):
                print(f"Eval item {i}: {eval_item}")
                validated = validate_evaluation_json(eval_item)
                print(f"Validated: {validated}")
                # These assertions will FAIL until we fix the float handling
                assert validated["score"] > 0, f"Score should not be 0, got {validated['score']}"
                assert validated["score"] == round(eval_item["score"]), f"Expected {round(eval_item['score'])}, got {validated['score']}"
    
    @pytest.mark.asyncio
    async def test_batch_reevaluation_partial_failure(self):
        """Test handling when batch re-evaluation returns fewer results than expected."""
        mock_genai_client = Mock()
        mock_response = Mock()
        # Return only 1 evaluation when 3 were expected
        mock_response.text = json.dumps({
            "evaluations": [
                {"score": 7.5, "comment": "Only one evaluation returned"}
            ]
        })
        mock_genai_client.models.generate_content.return_value = mock_response
        
        coordinator = AsyncCoordinator()
        
        candidates = [
            {"text": "Idea 1", "score": 5, "critique": "Initial", "improved_idea": "Better 1"},
            {"text": "Idea 2", "score": 6, "critique": "Initial", "improved_idea": "Better 2"},
            {"text": "Idea 3", "score": 7, "critique": "Initial", "improved_idea": "Better 3"}
        ]
        
        # This test verifies the warning behavior we saw in the logs
        with patch('madspark.agents.genai_client.get_genai_client', return_value=mock_genai_client):
            # The coordinator should handle partial results gracefully
            temp_manager = TemperatureManager.from_preset("balanced")
            
            # Process candidates with batch improvement
            result = await coordinator._process_candidates_with_batch_improvement(
                candidates, "Test theme", temp_manager.get_temperature_for_stage("idea_generation")
            )
            
            # Should handle partial failure gracefully
            assert len(result) == 3  # All candidates returned
            # First candidate should have the single evaluation applied
            assert result[0]["improved_score"] > 0
    
    @pytest.mark.asyncio 
    async def test_batch_reevaluation_timeout_handling(self):
        """Test handling of re-evaluation timeout with float score fallback."""
        # Mock a timeout scenario
        async def mock_timeout_evaluate(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Re-evaluation timed out")
        
        coordinator = AsyncCoordinator()
        
        candidate = {
            "text": "Test idea",
            "score": 7.2,  # Float score
            "critique": "Initial critique",
            "improved_idea": "Improved test idea"
        }
        
        with patch('madspark.core.async_coordinator.async_evaluate_ideas', mock_timeout_evaluate):
            # Process single candidate
            result = await coordinator._process_single_candidate(
                candidate,
                idea_temp=0.9,
                eval_temp=0.5,
                constraints="Test constraints"
            )
            
            # Should handle timeout with estimated score
            assert "improved_score" in result
            assert result["improved_score"] > 0  # Should not be 0
            assert "Re-evaluation timed out" in result["improved_critique"]
            assert "partial_failures" in result
    
    @pytest.mark.asyncio
    async def test_mixed_score_types_in_batch(self):
        """Test batch with mixed integer and float scores."""
        mock_genai_client = Mock()
        mock_response = Mock()
        # Mix of int and float scores
        mock_response.text = json.dumps({
            "evaluations": [
                {"score": 8, "comment": "Integer score"},
                {"score": 7.6, "comment": "Float score"},
                {"score": "9.2", "comment": "String float score"}
            ]
        })
        mock_genai_client.models.generate_content.return_value = mock_response
        
        # This test will FAIL initially
        with patch('madspark.agents.genai_client.get_genai_client', return_value=mock_genai_client):
            from madspark.utils.utils import validate_evaluation_json
            
            eval_json = json.loads(mock_response.text)
            validated_scores = []
            
            for eval_data in eval_json["evaluations"]:
                validated = validate_evaluation_json(eval_data)
                validated_scores.append(validated["score"])
            
            # All scores should be properly converted
            assert validated_scores[0] == 8  # Int stays int
            assert validated_scores[1] == 8  # 7.6 rounds to 8
            assert validated_scores[2] == 9  # "9.2" parses and rounds to 9
            
            # None should be 0
            assert all(score > 0 for score in validated_scores)
    
    @pytest.mark.asyncio
    async def test_structured_output_format_variations(self):
        """Test handling various structured output formats from different models."""
        test_cases = [
            # Gemini-style nested evaluations
            {
                "evaluations": [
                    {"score": 8.4, "comment": "Excellent"},
                    {"score": 7.1, "comment": "Good"}
                ]
            },
            # Single evaluation wrapped in dict
            {
                "score": 8.9,
                "comment": "Single evaluation"
            },
            # Array format
            [
                {"score": 7.7, "comment": "First"},
                {"score": 8.2, "comment": "Second"}
            ]
        ]
        
        for test_case in test_cases:
            mock_genai_client = Mock()
            mock_response = Mock()
            mock_response.text = json.dumps(test_case)
            mock_genai_client.models.generate_content.return_value = mock_response
            
            with patch('madspark.agents.genai_client.get_genai_client', return_value=mock_genai_client):
                # Test parsing logic
                
                # Simulate the parsing logic from async_coordinator
                re_eval_json = json.loads(mock_response.text)
                re_eval_results = []
                
                if isinstance(re_eval_json, list):
                    re_eval_results = re_eval_json
                elif isinstance(re_eval_json, dict):
                    if "evaluations" in re_eval_json:
                        re_eval_results = re_eval_json["evaluations"]
                    elif "score" in re_eval_json:
                        re_eval_results = [re_eval_json]
                
                # Validate all formats parse correctly
                assert len(re_eval_results) > 0
                
                from madspark.utils.utils import validate_evaluation_json
                for eval_data in re_eval_results:
                    validated = validate_evaluation_json(eval_data)
                    # This will FAIL until float handling is fixed
                    assert validated["score"] > 0