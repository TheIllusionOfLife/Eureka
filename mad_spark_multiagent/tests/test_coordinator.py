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