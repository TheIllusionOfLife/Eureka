"""Test coordinator warning behavior."""
import os
import sys
from unittest.mock import patch

# Add src to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.coordinator import run_multistep_workflow


class TestCoordinatorWarnings:
    """Test that coordinator warnings are suppressed in normal operation."""
    
    def test_warnings_suppressed_in_normal_mode(self):
        """Warnings should not show in normal mode."""
        # Capture root logger warnings
        with patch('logging.warning') as mock_warning:
            # Mock the agents to return mismatched responses
            with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_generate:
                with patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_evaluate:
                    # Return many ideas
                    mock_generate.return_value = "1. Idea one\n2. Idea two\n3. Idea three\n4. Idea four\n5. Idea five"
                    # Return fewer evaluations (simulating mismatch)
                    mock_evaluate.return_value = '{"evaluations": [{"id": 1, "score": 5, "comment": "Good"}]}'
                    
                    # Run workflow in normal mode (not verbose)
                    run_multistep_workflow("test theme", "test constraints", verbose=False)
                    
                    # Count how many times warning was called
                    warning_calls = [call for call in mock_warning.call_args_list 
                                   if 'Mismatch between number of ideas' in str(call) 
                                   or 'No evaluation available' in str(call)]
                    
                    # In normal mode, we should have minimal warnings
                    assert len(warning_calls) <= 1, f"Too many warnings in normal mode: {len(warning_calls)}"
    
    def test_warnings_shown_in_verbose_mode(self):
        """Warnings should show in verbose mode for debugging."""
        # Capture root logger warnings
        with patch('logging.warning') as mock_warning:
            # Mock the agents to return mismatched responses
            with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_generate:
                with patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_evaluate:
                    # Return multiple ideas to ensure count mismatch
                    mock_generate.return_value = "1. Idea one\n2. Idea two\n3. Idea three\n4. Idea four\n5. Idea five"
                    # Return only one evaluation (mismatch count)
                    mock_evaluate.return_value = '{"evaluations": [{"id": 1, "score": 5, "comment": "Good"}]}'
                    
                    # Run workflow in verbose mode
                    run_multistep_workflow("test theme", "test constraints", verbose=True, num_top_candidates=1)
                    
                    # In verbose mode, warnings should be shown for mismatches or missing evaluations
                    warning_calls = [call for call in mock_warning.call_args_list 
                                   if any(keyword in str(call) for keyword in ['Mismatch', 'No evaluation', 'available'])]
                    
                    assert len(warning_calls) >= 1, "Warnings should be shown in verbose mode"