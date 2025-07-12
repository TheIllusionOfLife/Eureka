"""Tests for feedback loop enhancement functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from mad_spark_multiagent.errors import ValidationError, IdeaGenerationError


class TestFeedbackLoop:
    """Test cases for feedback loop enhancement."""
    
    def setup_method(self):
        """Set up test environment."""
        # Ensure required environment variables are set for tests
        os.environ["GOOGLE_API_KEY"] = "test-api-key"
        os.environ["GOOGLE_GENAI_MODEL"] = "gemini-pro"
    
    def test_improve_idea_with_valid_feedback(self):
        """Test improve_idea function with valid inputs."""
        from mad_spark_multiagent.agent_defs.idea_generator import improve_idea
        
        # Test inputs
        original_idea = "AI-powered personal assistant for elderly care"
        critique = "Lacks privacy considerations and technical feasibility details"
        advocacy_points = """STRENGTHS:
• Addresses significant social need
• Large potential market
• Can improve quality of life"""
        skeptic_points = """CRITICAL FLAWS:
• Privacy concerns with elderly data
• High implementation cost
• Requires constant internet connectivity"""
        theme = "AI healthcare"
        
        # Mock the agent response
        with patch('mad_spark_multiagent.agent_defs.idea_generator.idea_generator_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "Privacy-first AI companion with local processing and family oversight controls"
            mock_agent.run.return_value = mock_response
            
            # Call the function
            result = improve_idea(
                original_idea=original_idea,
                critique=critique,
                advocacy_points=advocacy_points,
                skeptic_points=skeptic_points,
                theme=theme,
                temperature=0.9
            )
            
            # Verify the result
            assert result == "Privacy-first AI companion with local processing and family oversight controls"
            
            # Verify the agent was called with correct parameters
            mock_agent.run.assert_called_once()
            call_args = mock_agent.run.call_args[1]
            assert original_idea in call_args['prompt']
            assert critique in call_args['prompt']
            assert advocacy_points in call_args['prompt']
            assert skeptic_points in call_args['prompt']
            assert theme in call_args['prompt']
            assert call_args['temperature'] == 0.9
    
    def test_improve_idea_with_empty_inputs(self):
        """Test improve_idea function raises ValidationError for empty inputs."""
        from mad_spark_multiagent.agent_defs.idea_generator import improve_idea
        
        # Test empty original idea
        with pytest.raises(ValidationError, match="original_idea must be a non-empty string"):
            improve_idea("", "critique", "advocacy", "skeptic", "theme")
        
        # Test empty critique
        with pytest.raises(ValidationError, match="critique must be a non-empty string"):
            improve_idea("idea", "", "advocacy", "skeptic", "theme")
        
        # Test empty advocacy points
        with pytest.raises(ValidationError, match="advocacy_points must be a non-empty string"):
            improve_idea("idea", "critique", "", "skeptic", "theme")
        
        # Test empty skeptic points
        with pytest.raises(ValidationError, match="skeptic_points must be a non-empty string"):
            improve_idea("idea", "critique", "advocacy", "", "theme")
        
        # Test empty theme
        with pytest.raises(ValidationError, match="theme must be a non-empty string"):
            improve_idea("idea", "critique", "advocacy", "skeptic", "")
    
    def test_improve_idea_with_api_failure(self):
        """Test improve_idea function handles API failures gracefully."""
        from mad_spark_multiagent.agent_defs.idea_generator import improve_idea
        
        # Mock the agent to raise an exception
        with patch('mad_spark_multiagent.agent_defs.idea_generator.idea_generator_agent') as mock_agent:
            mock_agent.run.side_effect = Exception("API Error: Rate limit exceeded")
            
            # The function should raise IdeaGenerationError
            with pytest.raises(IdeaGenerationError, match="Failed to improve idea"):
                improve_idea(
                    original_idea="Test idea",
                    critique="Test critique",
                    advocacy_points="Test advocacy",
                    skeptic_points="Test skeptic",
                    theme="Test theme"
                )
    
    def test_feedback_loop_workflow_end_to_end(self):
        """Test the complete feedback loop workflow in coordinator."""
        from mad_spark_multiagent.coordinator import run_multistep_workflow
        
        # Mock all the agent calls
        with patch('mad_spark_multiagent.coordinator.idea_generator_agent') as mock_idea_agent, \
             patch('mad_spark_multiagent.coordinator.critic_agent') as mock_critic_agent, \
             patch('mad_spark_multiagent.coordinator.advocate_agent') as mock_advocate_agent, \
             patch('mad_spark_multiagent.coordinator.skeptic_agent') as mock_skeptic_agent:
            
            # Setup mock responses
            mock_idea_response = Mock()
            mock_idea_response.content = "Original AI healthcare idea"
            mock_idea_agent.run.return_value = mock_idea_response
            
            mock_critic_response = Mock()
            mock_critic_response.content = "7.5\n\nGood idea but needs more details"
            mock_critic_agent.run.return_value = mock_critic_response
            
            mock_advocate_response = Mock()
            mock_advocate_response.content = """STRENGTHS:
• Innovative approach
• Market potential"""
            mock_advocate_agent.run.return_value = mock_advocate_response
            
            mock_skeptic_response = Mock()
            mock_skeptic_response.content = """CRITICAL FLAWS:
• Technical complexity
• Cost concerns"""
            mock_skeptic_agent.run.return_value = mock_skeptic_response
            
            # For improved idea generation
            mock_improved_idea = Mock()
            mock_improved_idea.content = "Improved AI healthcare idea with addressed concerns"
            # Second call to idea_generator_agent.run will return improved idea
            mock_idea_agent.run.side_effect = [mock_idea_response, mock_improved_idea]
            
            # For improved critique
            mock_improved_critique = Mock()
            mock_improved_critique.content = "8.5\n\nSignificant improvement with better feasibility"
            # Second call to critic_agent.run will return improved critique
            mock_critic_agent.run.side_effect = [mock_critic_response, mock_improved_critique]
            
            # Run the workflow
            result = run_multistep_workflow(
                theme="AI healthcare",
                context="budget-friendly solutions",
                num_candidates=1,
                mode="direct",
                temperature=0.7
            )
            
            # Verify the result structure
            assert len(result["candidates"]) == 1
            candidate = result["candidates"][0]
            
            # Check original fields
            assert candidate["idea"] == "Original AI healthcare idea"
            assert candidate["initial_score"] == 7.5
            assert candidate["initial_critique"] == "Good idea but needs more details"
            assert "Innovative approach" in candidate["advocacy"]
            assert "Technical complexity" in candidate["skepticism"]
            
            # Check improved fields
            assert candidate["improved_idea"] == "Improved AI healthcare idea with addressed concerns"
            assert candidate["improved_score"] == 8.5
            assert candidate["improved_critique"] == "Significant improvement with better feasibility"
            assert candidate["score_delta"] == 1.0  # 8.5 - 7.5
    
    def test_score_delta_calculation(self):
        """Test score delta calculation handles edge cases."""
        from mad_spark_multiagent.coordinator import CandidateData
        
        # Test normal case
        candidate: CandidateData = {
            "idea": "test",
            "initial_score": 6.0,
            "initial_critique": "test",
            "advocacy": "test",
            "skepticism": "test",
            "multi_dimensional_evaluation": None,
            "improved_idea": "test improved",
            "improved_score": 8.0,
            "improved_critique": "better",
            "score_delta": 2.0
        }
        assert candidate["score_delta"] == 2.0
        
        # Test zero initial score case (should be handled in frontend)
        candidate_zero: CandidateData = {
            "idea": "test",
            "initial_score": 0.0,
            "initial_critique": "test",
            "advocacy": "test",
            "skepticism": "test",
            "multi_dimensional_evaluation": None,
            "improved_idea": "test improved",
            "improved_score": 5.0,
            "improved_critique": "better",
            "score_delta": 5.0
        }
        assert candidate_zero["score_delta"] == 5.0