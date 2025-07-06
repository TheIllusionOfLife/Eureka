"""Tests for the coordinator module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List
import json

# Mock the agents before importing coordinator
with patch('mad_spark_multiagent.coordinator.idea_generator_agent'), \
     patch('mad_spark_multiagent.coordinator.critic_agent'), \
     patch('mad_spark_multiagent.coordinator.advocate_agent'), \
     patch('mad_spark_multiagent.coordinator.skeptic_agent'):
    from mad_spark_multiagent.coordinator import (
        run_multistep_workflow,
        CandidateData,
        call_idea_generator_with_retry,
        call_critic_with_retry,
        call_advocate_with_retry,
        call_skeptic_with_retry,
        log_verbose_step,
        log_verbose_data,
        log_verbose_completion,
        log_verbose_sample_list,
        log_agent_execution,
        log_agent_completion,
    )


class TestCoordinator:
    """Test cases for the coordinator workflow."""
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_advocate_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_skeptic_with_retry')
    def test_successful_workflow(
        self,
        mock_skeptic,
        mock_advocate,
        mock_critic,
        mock_idea_gen
    ):
        """Test a successful workflow execution."""
        # Setup mocks
        mock_idea_gen.return_value = "Idea 1: Solar panels\nIdea 2: Vertical gardens"
        mock_critic.return_value = json.dumps([
            {"score": 8, "comment": "Great potential"},
            {"score": 6, "comment": "Needs refinement"}
        ])
        mock_advocate.return_value = "Strong arguments for this idea"
        mock_skeptic.return_value = "Some concerns about implementation"
        
        # Run workflow
        results = run_multistep_workflow(
            theme="Sustainable Living",
            constraints="Budget-friendly",
            num_top_candidates=1
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["idea"] == "Idea 1: Solar panels"
        assert results[0]["initial_score"] == 8
        assert results[0]["advocacy"] == "Strong arguments for this idea"
        assert results[0]["skepticism"] == "Some concerns about implementation"
        
        # Verify all agents were called
        mock_idea_gen.assert_called_once()
        mock_critic.assert_called_once()
        mock_advocate.assert_called_once()
        mock_skeptic.assert_called_once()
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    def test_no_ideas_generated(self, mock_idea_gen):
        """Test handling when no ideas are generated."""
        mock_idea_gen.return_value = ""
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints"
        )
        
        assert results == []
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    def test_idea_generation_failure(self, mock_idea_gen):
        """Test handling of idea generation failure."""
        mock_idea_gen.side_effect = Exception("API Error")
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints"
        )
        
        assert results == []
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    def test_critic_failure_with_fallback(self, mock_critic, mock_idea_gen):
        """Test fallback when critic fails."""
        mock_idea_gen.return_value = "Idea 1\nIdea 2\nIdea 3"
        mock_critic.side_effect = Exception("Critic failed")
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints",
            num_top_candidates=2
        )
        
        # Should fall back to first N ideas
        assert len(results) == 2
        assert results[0]["idea"] == "Idea 1"
        assert results[0]["initial_score"] == 0
        assert results[0]["initial_critique"] == "N/A (CriticAgent failed)"
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_advocate_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_skeptic_with_retry')
    def test_advocate_skeptic_failures(
        self,
        mock_skeptic,
        mock_advocate,
        mock_critic,
        mock_idea_gen
    ):
        """Test handling of advocate and skeptic failures."""
        mock_idea_gen.return_value = "Idea 1"
        mock_critic.return_value = '{"score": 8, "comment": "Good"}'
        mock_advocate.side_effect = Exception("Advocate failed")
        mock_skeptic.side_effect = Exception("Skeptic failed")
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints",
            num_top_candidates=1
        )
        
        assert len(results) == 1
        assert results[0]["advocacy"] == "Advocacy not available due to agent error."
        assert results[0]["skepticism"] == "Skepticism not available due to agent error."
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    def test_malformed_critic_response(self, mock_critic, mock_idea_gen):
        """Test handling of malformed critic responses."""
        mock_idea_gen.return_value = "Idea 1\nIdea 2"
        mock_critic.return_value = "Not JSON at all\nAlso not JSON"
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints",
            num_top_candidates=2
        )
        
        # Should create placeholder evaluations
        assert len(results) == 2
        assert all(r["initial_score"] == 0 for r in results)
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    def test_partial_critic_response(self, mock_critic, mock_idea_gen):
        """Test handling when critic returns fewer evaluations than ideas."""
        mock_idea_gen.return_value = "Idea 1\nIdea 2\nIdea 3"
        mock_critic.return_value = '{"score": 8, "comment": "Good"}'  # Only one evaluation
        
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints",
            num_top_candidates=3
        )
        
        # First idea should have evaluation, others should have defaults
        assert results[0]["initial_score"] == 8
        assert results[1]["initial_score"] == 0
        assert results[2]["initial_score"] == 0


class TestRetryWrappers:
    """Test cases for retry wrapper functions."""
    
    @patch('mad_spark_multiagent.coordinator.idea_generator_agent')
    def test_idea_generator_retry_wrapper(self, mock_agent):
        """Test the idea generator retry wrapper."""
        mock_agent.call_tool.return_value = "Ideas"
        
        result = call_idea_generator_with_retry("theme", "context")
        
        assert result == "Ideas"
        mock_agent.call_tool.assert_called_once_with(
            "generate_ideas", topic="theme", context="context"
        )
    
    @patch('mad_spark_multiagent.coordinator.critic_agent')
    def test_critic_retry_wrapper(self, mock_agent):
        """Test the critic retry wrapper."""
        mock_agent.call_tool.return_value = "Evaluations"
        
        result = call_critic_with_retry("ideas", "criteria", "context")
        
        assert result == "Evaluations"
        mock_agent.call_tool.assert_called_once_with(
            "evaluate_ideas", ideas="ideas", criteria="criteria", context="context"
        )
    
    @patch('mad_spark_multiagent.coordinator.advocate_agent')
    def test_advocate_retry_wrapper(self, mock_agent):
        """Test the advocate retry wrapper."""
        mock_agent.call_tool.return_value = "Advocacy"
        
        result = call_advocate_with_retry("idea", "evaluation", "context")
        
        assert result == "Advocacy"
        mock_agent.call_tool.assert_called_once_with(
            "advocate_idea", idea="idea", evaluation="evaluation", context="context"
        )
    
    @patch('mad_spark_multiagent.coordinator.skeptic_agent')
    def test_skeptic_retry_wrapper(self, mock_agent):
        """Test the skeptic retry wrapper."""
        mock_agent.call_tool.return_value = "Skepticism"
        
        result = call_skeptic_with_retry("idea", "advocacy", "context")
        
        assert result == "Skepticism"
        mock_agent.call_tool.assert_called_once_with(
            "criticize_idea", idea="idea", advocacy="advocacy", context="context"
        )
    
    @patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_critic_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_advocate_with_retry')
    @patch('mad_spark_multiagent.coordinator.call_skeptic_with_retry')
    @patch('builtins.print')  # Mock print to capture verbose output
    def test_verbose_logging_workflow(
        self,
        mock_print,
        mock_skeptic,
        mock_advocate,
        mock_critic,
        mock_idea_gen
    ):
        """Test that verbose logging produces expected output."""
        # Setup mocks
        mock_idea_gen.return_value = "Idea 1: Test idea"
        mock_critic.return_value = '{"score": 8, "comment": "Good idea"}'
        mock_advocate.return_value = "Strong support for this idea"
        mock_skeptic.return_value = "Some concerns about feasibility"
        
        # Run workflow with verbose=True
        results = run_multistep_workflow(
            theme="Test Theme",
            constraints="Test Constraints",
            num_top_candidates=1,
            verbose=True
        )
        
        # Verify workflow completed successfully
        assert len(results) == 1
        assert results[0]["idea"] == "Idea 1: Test idea"
        assert results[0]["initial_score"] == 8
        
        # Verify verbose output was generated
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        verbose_outputs = [call for call in print_calls if isinstance(call, str)]
        
        # Check for key verbose logging elements
        step_headers = [output for output in verbose_outputs if "STEP" in output and "=" in output]
        completion_messages = [output for output in verbose_outputs if "Complete:" in output]
        
        # Should have multiple step headers and completion messages
        assert len(step_headers) >= 3, f"Expected at least 3 step headers, got {len(step_headers)}"
        assert len(completion_messages) >= 3, f"Expected at least 3 completion messages, got {len(completion_messages)}"
        
        # Verify specific verbose steps are present
        all_output = " ".join(verbose_outputs)
        assert "STEP 1: Idea Generation Agent" in all_output
        assert "STEP 2: Critic Agent Evaluation" in all_output
        assert "STEP 3.1: Processing Top Candidate" in all_output
        assert "WORKFLOW COMPLETE" in all_output
    
    @patch('builtins.print')
    @patch('mad_spark_multiagent.coordinator.logging')
    def test_verbose_logging_functions(self, mock_logging, mock_print):
        """Test the verbose logging helper functions."""
        
        # Test log_verbose_step
        log_verbose_step("Test Step", "Test details", verbose=True)
        mock_print.assert_called()
        mock_logging.info.assert_called()
        
        # Test with verbose=False
        mock_print.reset_mock()
        mock_logging.reset_mock()
        log_verbose_step("Test Step", "Test details", verbose=False)
        mock_print.assert_not_called()
        
        # Test log_verbose_data with truncation
        mock_print.reset_mock()
        mock_logging.reset_mock()
        long_data = "x" * 1000  # Longer than default max_length of 500
        log_verbose_data("Test Data", long_data, verbose=True, max_length=100)
        
        # Should print truncated version
        print_calls = mock_print.call_args_list
        assert len(print_calls) > 0
        # Check that truncation happened
        printed_content = " ".join([str(call.args[0]) for call in print_calls])
        assert "Truncated" in printed_content
        
        # Test log_verbose_completion
        mock_print.reset_mock()
        log_verbose_completion("Test Step", 5, 2.5, verbose=True, unit="items")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Test Step Complete" in call_args
        assert "5 items" in call_args
        assert "2.50s" in call_args
        
        # Test log_verbose_sample_list
        mock_print.reset_mock()
        test_items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
        log_verbose_sample_list(test_items, verbose=True, max_display=3)
        
        # Should print sample items
        print_calls = mock_print.call_args_list
        assert len(print_calls) > 0
        printed_content = " ".join([str(call.args[0]) for call in print_calls])
        assert "Sample Items" in printed_content
        assert "Item 1" in printed_content
        assert "and 2 more items" in printed_content  # Since we have 5 items, showing 3
        
        # Test log_agent_execution
        mock_print.reset_mock()
        log_agent_execution("STEP 1", "TestAgent", "🤖", "Testing functionality", 0.7, verbose=True)
        mock_print.assert_called()
        
        # Test log_agent_completion
        mock_print.reset_mock()
        log_agent_completion("TestAgent", "Test response data", "Idea #1", 2.5, verbose=True)
        mock_print.assert_called()