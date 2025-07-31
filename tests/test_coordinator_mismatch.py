"""Test the specific mismatch issue reported in Issue #118."""
import json
from unittest.mock import patch, MagicMock
import os
import sys
import logging

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.coordinator import run_multistep_workflow


class TestCoordinatorMismatchIssue:
    """Test suite for the specific mismatch issue where coordinator generates many ideas but parses few evaluations."""
    
    def test_coordinator_handles_partial_evaluations(self, caplog):
        """Test coordinator when Critic returns fewer evaluations than ideas."""
        with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.core.coordinator.call_critic_with_retry') as mock_critic, \
             patch('madspark.core.coordinator.call_advocate_with_retry') as mock_advocate, \
             patch('madspark.core.coordinator.call_skeptic_with_retry') as mock_skeptic, \
             patch('madspark.core.coordinator.call_improve_idea_with_retry') as mock_improve, \
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
            
            # Mock other agents
            mock_advocate.return_value = "Strong points"
            mock_skeptic.return_value = "Concerns raised"
            mock_improve.return_value = "Enhanced version"
            
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
    
    def test_critic_response_with_incomplete_json(self):
        """Test when Critic returns a mix of valid JSON and text."""
        with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.core.coordinator.call_critic_with_retry') as mock_critic, \
             patch('madspark.core.coordinator.call_advocate_with_retry') as mock_advocate, \
             patch('madspark.core.coordinator.call_skeptic_with_retry') as mock_skeptic, \
             patch('madspark.core.coordinator.call_improve_idea_with_retry') as mock_improve, \
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
            
            # Mock other agents
            mock_advocate.return_value = "Support"
            mock_skeptic.return_value = "Concerns"  
            mock_improve.return_value = "Better version"
            
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
    
