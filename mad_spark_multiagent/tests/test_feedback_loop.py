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
        
        # Mock the model response
        with patch('mad_spark_multiagent.agent_defs.idea_generator.idea_generator_model') as mock_model:
            mock_response = Mock()
            mock_response.text = "Privacy-first AI companion with local processing and family oversight controls"
            mock_model.generate_content.return_value = mock_response
            
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
            
            # Verify the model was called with correct parameters
            mock_model.generate_content.assert_called_once()
            call_args = mock_model.generate_content.call_args[0]
            prompt = call_args[0]
            assert original_idea in prompt
            assert critique in prompt
            assert advocacy_points in prompt
            assert skeptic_points in prompt
            assert theme in prompt
            
            # Verify temperature was set correctly
            generation_config = mock_model.generate_content.call_args[1]['generation_config']
            assert generation_config.temperature == 0.9
    
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
        
        # Mock the model to raise an exception
        with patch('mad_spark_multiagent.agent_defs.idea_generator.idea_generator_model') as mock_model:
            mock_model.generate_content.side_effect = Exception("API Error: Rate limit exceeded")
            
            # The function returns empty string on API failure (not IdeaGenerationError)
            result = improve_idea(
                original_idea="Test idea",
                critique="Test critique",
                advocacy_points="Test advocacy",
                skeptic_points="Test skeptic",
                theme="Test theme"
            )
            
            # Verify it returns empty string on failure
            assert result == ""
    
    def test_feedback_loop_workflow_end_to_end(self):
        """Test the complete feedback loop workflow in coordinator."""
        from mad_spark_multiagent.coordinator import run_multistep_workflow
        
        # Mock the retry functions that wrap the actual agent functions
        with patch('mad_spark_multiagent.coordinator.call_idea_generator_with_retry') as mock_idea_gen, \
             patch('mad_spark_multiagent.coordinator.call_critic_with_retry') as mock_critic, \
             patch('mad_spark_multiagent.coordinator.call_advocate_with_retry') as mock_advocate, \
             patch('mad_spark_multiagent.coordinator.call_skeptic_with_retry') as mock_skeptic, \
             patch('mad_spark_multiagent.coordinator.call_improve_idea_with_retry') as mock_improve:
            
            # Setup mock responses
            mock_idea_gen.return_value = "Original AI healthcare idea"
            
            # First critique - JSON format as expected by coordinator
            mock_critic.side_effect = [
                '{"score": 7.5, "comment": "Good idea but needs more details"}',  # First evaluation  
                '{"score": 8.5, "comment": "Significant improvement with better feasibility"}'  # Re-evaluation
            ]
            
            mock_advocate.return_value = """STRENGTHS:
• Innovative approach
• Market potential"""
            
            mock_skeptic.return_value = """CRITICAL FLAWS:
• Technical complexity
• Cost concerns"""
            
            mock_improve.return_value = "Improved AI healthcare idea with addressed concerns"
            
            # Run the workflow with correct parameters
            result = run_multistep_workflow(
                theme="AI healthcare",
                constraints="budget-friendly solutions",  # Changed from 'context'
                num_top_candidates=1,  # Changed from 'num_candidates'
                enable_novelty_filter=False,
                verbose=False
            )
            
            # Verify the result is a list of CandidateData
            assert isinstance(result, list)
            assert len(result) == 1
            candidate = result[0]
            
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