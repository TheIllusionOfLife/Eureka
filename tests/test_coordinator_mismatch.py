"""Test the specific mismatch issue reported in Issue #118."""
import json
from unittest.mock import patch, MagicMock
import os
import sys
import logging
import pytest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.coordinator import run_multistep_workflow


class TestCoordinatorMismatchIssue:
    """Test suite for the specific mismatch issue where coordinator generates many ideas but parses few evaluations."""
    
    @pytest.mark.skipif(os.getenv("MADSPARK_MODE") == "mock", reason="Test requires full mock control")
    def test_coordinator_handles_partial_evaluations(self, caplog):
        """Test coordinator when Critic returns fewer evaluations than ideas."""
        with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_critic, \
             patch('madspark.agents.advocate.advocate_ideas_batch') as mock_advocate_batch, \
             patch('madspark.agents.skeptic.criticize_ideas_batch') as mock_skeptic_batch, \
             patch('madspark.agents.idea_generator.improve_ideas_batch') as mock_improve_batch, \
             patch('madspark.core.coordinator.ReasoningEngine') as mock_engine:
            
            # Mock reasoning engine
            mock_engine_instance = MagicMock()
            mock_engine_instance.multi_evaluator = None
            mock_engine.return_value = mock_engine_instance
            
            # Generate 31 ideas (as reported in issue)
            ideas_list = [f"Idea {i}: Solution for urban sustainability challenge #{i}" for i in range(1, 32)]
            mock_generator.return_value = "\n".join(ideas_list)
            
            # Return only 5 evaluations (as reported in issue)
            evaluations = [
                {"score": 8, "comment": "Excellent idea with strong feasibility"},
                {"score": 7, "comment": "Good concept but needs refinement"},
                {"score": 9, "comment": "Outstanding innovation potential"},
                {"score": 6, "comment": "Average idea with some merit"},
                {"score": 7, "comment": "Solid approach worth exploring"}
            ]
            mock_critic.return_value = json.dumps(evaluations)
            
            # Mock batch functions with proper return format (list of results, token count)
            def mock_advocate_response(ideas_with_evals, context, temperature):
                return [{
                    "idea_index": i,
                    "strengths": ["Strong point 1", "Strong point 2"],
                    "opportunities": ["Opportunity 1", "Opportunity 2"],
                    "addressing_concerns": ["Mitigation 1", "Mitigation 2"],
                    "formatted": "STRENGTHS:\n• Strong point 1\n• Strong point 2"
                } for i in range(len(ideas_with_evals))], 100
            
            def mock_skeptic_response(ideas_with_advocacies, context, temperature):
                return [{
                    "idea_index": i,
                    "critical_flaws": ["Flaw 1", "Flaw 2"],
                    "risks_challenges": ["Risk 1", "Risk 2"],
                    "questionable_assumptions": ["Assumption 1", "Assumption 2"],
                    "missing_considerations": ["Missing 1", "Missing 2"],
                    "formatted": "CRITICAL FLAWS:\n• Flaw 1\n• Flaw 2"
                } for i in range(len(ideas_with_advocacies))], 100
            
            def mock_improve_response(ideas_with_feedback, theme, temperature):
                return [{
                    "idea_index": i,
                    "improved_idea": f"Enhanced: {ideas_with_feedback[i]['idea']}",
                    "key_improvements": ["Improvement 1", "Improvement 2"]
                } for i in range(len(ideas_with_feedback))], 100
            
            mock_advocate_batch.side_effect = mock_advocate_response
            mock_skeptic_batch.side_effect = mock_skeptic_response
            mock_improve_batch.side_effect = mock_improve_response
            
            # Set log level to capture warnings
            caplog.set_level(logging.WARNING)
            
            # Run workflow (results not used, we're testing warnings)
            _ = run_multistep_workflow(
                theme="Test Theme",
                constraints="Test Constraints",
                num_top_candidates=3,
                enable_novelty_filter=False,
                verbose=True  # Enable verbose to see warnings
            )
            
            # Check for the mismatch warning
            mismatch_warnings = [record for record in caplog.records if "Mismatch between number of ideas" in record.message]
            
            # Should have logged a mismatch warning
            assert len(mismatch_warnings) > 0, "Should warn about mismatch"
            
            # Check the warning message
            warning_msg = mismatch_warnings[0].message
            assert "31" in warning_msg and "5" in warning_msg, f"Warning should mention 31 ideas and 5 evaluations, got: {warning_msg}"
            
            # Check that ideas without evaluations got default values
            default_warnings = [record for record in caplog.records if "No evaluation available" in record.message]
            assert len(default_warnings) > 20, f"Should have warnings for ideas without evaluations, got {len(default_warnings)}"
    
    @pytest.mark.skipif(os.getenv("MADSPARK_MODE") == "mock", reason="Test requires full mock control")
    def test_critic_response_with_incomplete_json(self):
        """Test when Critic returns a mix of valid JSON and text."""
        with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_critic, \
             patch('madspark.agents.advocate.advocate_ideas_batch') as mock_advocate_batch, \
             patch('madspark.agents.skeptic.criticize_ideas_batch') as mock_skeptic_batch, \
             patch('madspark.agents.idea_generator.improve_ideas_batch') as mock_improve_batch, \
             patch('madspark.core.coordinator.ReasoningEngine') as mock_engine:
            
            # Mock reasoning engine
            mock_engine_instance = MagicMock()
            mock_engine_instance.multi_evaluator = None
            mock_engine.return_value = mock_engine_instance
            
            # Generate 10 ideas
            ideas_list = [f"Idea {i}" for i in range(1, 11)]
            mock_generator.return_value = "\n".join(ideas_list)
            
            # Return a realistic Critic response with only partial evaluations
            mock_critic.return_value = """Let me evaluate these ideas:

{"score": 8, "comment": "First idea is excellent"}
{"score": 7, "comment": "Second idea shows promise"}
{"score": 9, "comment": "Third idea is outstanding"}

The remaining ideas are more challenging to evaluate without additional context...
{"score": 6, "comment": "Fourth idea needs work"}
{"score": 5, "comment": "Fifth idea has limited potential"}

[Analysis continues but no more formal evaluations provided]"""
            
            # Mock batch functions with proper return format
            mock_advocate_batch.side_effect = lambda ideas, ctx, temp: ([{
                "idea_index": i,
                "strengths": ["Support 1", "Support 2"],
                "opportunities": ["Opp 1", "Opp 2"],
                "addressing_concerns": ["Mit 1", "Mit 2"],
                "formatted": "STRENGTHS:\n• Support 1\n• Support 2"
            } for i in range(len(ideas))], 100)
            
            mock_skeptic_batch.side_effect = lambda ideas, ctx, temp: ([{
                "idea_index": i,
                "critical_flaws": ["Concern 1", "Concern 2"],
                "risks_challenges": ["Risk 1", "Risk 2"],
                "questionable_assumptions": ["Assumption 1", "Assumption 2"],
                "missing_considerations": ["Missing 1", "Missing 2"],
                "formatted": "CRITICAL FLAWS:\n• Concern 1\n• Concern 2"
            } for i in range(len(ideas))], 100)
            
            mock_improve_batch.side_effect = lambda ideas, theme, temp: ([{
                "idea_index": i,
                "improved_idea": f"Better version: {ideas[i]['idea']}",
                "key_improvements": ["Improvement 1", "Improvement 2"]
            } for i in range(len(ideas))], 100)
            
            # Run workflow
            results = run_multistep_workflow(
                theme="Test",
                constraints="Test",
                num_top_candidates=2,
                enable_novelty_filter=False,
                verbose=False
            )
            
            # Should get top 2 results based on the 5 parsed evaluations
            assert len(results) == 2
            # Top scores should be 9 and 8
            scores = sorted([r['initial_score'] for r in results], reverse=True)
            assert scores[0] == 9, f"Top score should be 9, got {scores[0]}"
            assert scores[1] == 8, f"Second score should be 8, got {scores[1]}"
    
