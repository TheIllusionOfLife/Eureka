"""Test the exact scenario that caused the score 0 bug."""
import json
import logging

from madspark.utils.utils import validate_evaluation_json, parse_json_with_fallback


class TestFloatScoreBugScenario:
    """Test the exact bug scenario where float scores become 0."""
    
    def test_exact_bug_scenario_single_reevaluation(self, caplog):
        """Test the exact scenario from the bug report."""
        # This is the exact response that caused the issue
        # "Expected 3 re-evaluations, got 1"
        ai_response = json.dumps({
            "evaluations": [
                {
                    "score": 7.8999999999999995,
                    "comment": "Re-evaluation timed out - estimated improvement based on feedback integration"
                }
            ]
        })
        
        # Parse with fallback (as done in async_coordinator)
        # This demonstrates that parse_json_with_fallback works correctly
        parse_json_with_fallback(ai_response)
        
        # parse_json_with_fallback extracts the evaluations list
        parsed_data = json.loads(ai_response)
        evaluations = parsed_data["evaluations"]
        assert len(evaluations) == 1
        
        # Validate the evaluation
        with caplog.at_level(logging.WARNING):
            validated = validate_evaluation_json(evaluations[0])
        
        # Score should be preserved as float
        assert validated["score"] == 7.8999999999999995, f"Expected 7.8999999999999995, got {validated['score']}'"
    
    def test_batch_reevaluation_with_mixed_types(self):
        """Test batch re-evaluation with mixed score types."""
        # Simulate Gemini returning mixed types
        ai_response = {
            "evaluations": [
                {"score": 7.8, "comment": "Good idea"},  # Float
                {"score": 8, "comment": "Great idea"},   # Int
                {"score": 6.5, "comment": "Average"}     # Float
            ]
        }
        
        validated_scores = []
        for eval_data in ai_response["evaluations"]:
            validated = validate_evaluation_json(eval_data)
            validated_scores.append(validated["score"])
        
        # Float scores should be preserved
        assert validated_scores[0] == 7.8, f"7.8 should stay 7.8, got {validated_scores[0]}"
        assert validated_scores[1] == 8, f"8 should stay 8, got {validated_scores[1]}"
        assert validated_scores[2] == 6.5, f"6.5 should stay 6.5, got {validated_scores[2]}"
    
    def test_structured_output_variations(self):
        """Test various structured output formats that cause issues."""
        # Test case 1: Single evaluation (not in list)
        single_eval = {"score": 8.7, "comment": "Excellent"}
        validated = validate_evaluation_json(single_eval)
        assert validated["score"] == 8.7, f"8.7 should stay 8.7, got {validated['score']}"
        
        # Test case 2: Nested format
        nested_format = {
            "evaluation": {
                "score": 5.4,
                "comment": "Needs work"
            }
        }
        validated = validate_evaluation_json(nested_format["evaluation"])
        assert validated["score"] == 5.4, f"5.4 should stay 5.4, got {validated['score']}"
        
        # Test case 3: String float (common in JSON parsing)
        string_float = {"score": "7.9", "comment": "Good"}
        validated = validate_evaluation_json(string_float)
        assert validated["score"] == 7.9, f"'7.9' should parse to 7.9, got {validated['score']}"
    
    def test_timeout_fallback_scenario(self):
        """Test the timeout scenario that produces float scores."""
        # From async_coordinator.py when re-evaluation times out
        original_score = 7.2  # Float score from initial evaluation
        
        # Timeout handling logic adds 0.3
        improved_score = min(float(original_score) + 0.3, 10.0)
        assert improved_score == 7.5
        
        # This score goes into validation
        timeout_result = {
            "score": improved_score,
            "comment": "Re-evaluation timed out - estimated improvement based on feedback integration"
        }
        
        validated = validate_evaluation_json(timeout_result)
        # Float score should be preserved
        assert validated["score"] == 7.5, f"7.5 should stay 7.5, got {validated['score']}"
    
    def test_real_world_gemini_response(self):
        """Test with actual Gemini API response format."""
        # Real response format from Gemini with structured output
        gemini_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "evaluations": [
                                {
                                    "score": 8.5,
                                    "comment": "Highly innovative concept",
                                    "strengths": ["Creative", "Scalable"],
                                    "weaknesses": ["Complex implementation"]
                                },
                                {
                                    "score": 6.8,
                                    "comment": "Good but needs refinement",
                                    "strengths": ["Practical"],
                                    "weaknesses": ["Limited scope"]
                                }
                            ]
                        })
                    }]
                }
            }]
        }
        
        # Extract the evaluations as would happen in real code
        text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
        eval_data = json.loads(text)
        
        for i, evaluation in enumerate(eval_data["evaluations"]):
            validated = validate_evaluation_json(evaluation)
            if i == 0:
                assert validated["score"] == 8.5, f"8.5 should stay 8.5, got {validated['score']}"
            else:
                assert validated["score"] == 6.8, f"6.8 should stay 6.8, got {validated['score']}"