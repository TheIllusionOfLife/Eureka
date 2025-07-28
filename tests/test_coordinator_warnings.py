"""Test coordinator warning behavior."""
import os
import sys
import logging
from unittest.mock import patch

# Add src to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.coordinator import run_multistep_workflow


class TestCoordinatorWarnings:
    """Test that coordinator warnings are suppressed in normal operation."""
    
    def test_warnings_suppressed_in_normal_mode(self, caplog):
        """Warnings should not show in normal mode."""
        # Mock the agent functions to simulate mismatched ideas/evaluations
        with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.core.coordinator.call_critic_with_retry') as mock_critic:
            
            # Set up mocks to create a mismatch
            mock_generator.return_value = "Idea 1\nIdea 2\nIdea 3"  # 3 ideas
            mock_critic.return_value = '[{"score": 7, "comment": "Good"}]'  # 1 evaluation
            
            # Run in non-verbose mode
            with caplog.at_level(logging.WARNING):
                caplog.clear()
                try:
                    run_multistep_workflow(
                        theme="test",
                        constraints="test",
                        num_top_candidates=1,
                        verbose=False  # Non-verbose mode
                    )
                except Exception:
                    pass  # We expect it might fail, we're just testing logging
                
                # Check that no warning about mismatch was logged
                warning_messages = [record.message for record in caplog.records if record.levelname == 'WARNING']
                mismatch_warnings = [msg for msg in warning_messages if "Mismatch between number of ideas" in msg]
                assert len(mismatch_warnings) == 0, "Mismatch warning should not appear in non-verbose mode"
    
    def test_warnings_shown_in_verbose_mode(self, caplog):
        """Warnings should show in verbose mode for debugging."""
        # Mock the agent functions to simulate mismatched ideas/evaluations
        with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.core.coordinator.call_critic_with_retry') as mock_critic:
            
            # Set up mocks to create a mismatch
            mock_generator.return_value = "Idea 1\nIdea 2\nIdea 3"  # 3 ideas
            mock_critic.return_value = '[{"score": 7, "comment": "Good"}]'  # 1 evaluation
            
            # Run in verbose mode
            with caplog.at_level(logging.WARNING):
                caplog.clear()
                try:
                    run_multistep_workflow(
                        theme="test",
                        constraints="test",
                        num_top_candidates=1,
                        verbose=True  # Verbose mode
                    )
                except Exception:
                    pass  # We expect it might fail, we're just testing logging
                
                # Check that warning about mismatch was logged
                warning_messages = [record.message for record in caplog.records if record.levelname == 'WARNING']
                mismatch_warnings = [msg for msg in warning_messages if "Mismatch between number of ideas" in msg]
                assert len(mismatch_warnings) > 0, "Mismatch warning should appear in verbose mode"