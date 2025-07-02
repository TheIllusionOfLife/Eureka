"""Tests for agent definitions."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from mad_spark_multiagent.constants import ADVOCATE_EMPTY_RESPONSE, SKEPTIC_EMPTY_RESPONSE


class TestAgentDefinitions:
    """Test cases for agent definitions."""
    
    def setup_method(self):
        """Set up test environment."""
        # Ensure required environment variables are set for tests
        os.environ["GOOGLE_API_KEY"] = "test-api-key"
        os.environ["GOOGLE_GENAI_MODEL"] = "gemini-pro"
    
    @patch('mad_spark_multiagent.agent_defs.idea_generator.Agent')
    def test_idea_generator_agent_initialization(self, mock_agent_class):
        """Test idea generator agent is properly initialized."""
        from mad_spark_multiagent.agent_defs.idea_generator import idea_generator_agent
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        # Verify agent was created with only model and instructions (no name parameter)
        assert "generate diverse and creative ideas" in call_args.kwargs["instructions"]
        assert call_args.kwargs["model"] == "gemini-pro"
        # Agent constructor doesn't take a 'name' parameter in the actual implementation
    
    @patch('mad_spark_multiagent.agent_defs.critic.Agent')
    def test_critic_agent_initialization(self, mock_agent_class):
        """Test critic agent is properly initialized."""
        from mad_spark_multiagent.agent_defs.critic import critic_agent
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        # Verify agent was created with only model and instructions (no name parameter)
        assert "evaluate ideas" in call_args.kwargs["instructions"]
        assert call_args.kwargs["model"] == "gemini-pro"
        # Agent constructor doesn't take a 'name' parameter in the actual implementation
    
    @patch('mad_spark_multiagent.agent_defs.advocate.Agent')
    def test_advocate_agent_initialization(self, mock_agent_class):
        """Test advocate agent is properly initialized."""
        from mad_spark_multiagent.agent_defs.advocate import advocate_agent
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        # Verify agent was created with only model and instructions (no name parameter)
        assert "build a strong case" in call_args.kwargs["instructions"]
        assert call_args.kwargs["model"] == "gemini-pro"
        # Agent constructor doesn't take a 'name' parameter in the actual implementation
    
    @patch('mad_spark_multiagent.agent_defs.skeptic.Agent')
    def test_skeptic_agent_initialization(self, mock_agent_class):
        """Test skeptic agent is properly initialized."""
        from mad_spark_multiagent.agent_defs.skeptic import skeptic_agent
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        # Verify agent was created with only model and instructions (no name parameter)
        assert "devil's advocate" in call_args.kwargs["instructions"]
        assert call_args.kwargs["model"] == "gemini-pro"
        # Agent constructor doesn't take a 'name' parameter in the actual implementation
    
    @patch('mad_spark_multiagent.agent_defs.idea_generator.idea_generator_agent')
    def test_generate_ideas_tool(self, mock_agent):
        """Test the generate_ideas tool function."""
        from mad_spark_multiagent.agent_defs.idea_generator import generate_ideas
        
        # Mock agent response
        mock_agent.call.return_value = "Idea 1\nIdea 2"
        
        # Call the tool
        result = generate_ideas(topic="Test", context="Context")
        
        assert result == "Idea 1\nIdea 2"
        
        # Test empty response handling - returns empty string (no exception)
        mock_agent.call.return_value = ""
        result = generate_ideas(topic="Test", context="Context")
        assert result == ""
    
    @patch('mad_spark_multiagent.agent_defs.critic.critic_agent')
    def test_evaluate_ideas_tool(self, mock_agent):
        """Test the evaluate_ideas tool function."""
        from mad_spark_multiagent.agent_defs.critic import evaluate_ideas
        
        # Mock agent response
        mock_agent.call.return_value = '{"score": 8, "comment": "Good"}'
        
        # Call the tool
        result = evaluate_ideas(ideas="Idea 1", criteria="Criteria", context="Context")
        
        assert result == '{"score": 8, "comment": "Good"}'
        
        # Test empty response handling - returns empty string (no exception)
        mock_agent.call.return_value = ""
        result = evaluate_ideas(ideas="Ideas", criteria="Criteria", context="Context")
        assert result == ""
    
    @patch('mad_spark_multiagent.agent_defs.advocate.advocate_agent')
    def test_advocate_idea_tool(self, mock_agent):
        """Test the advocate_idea tool function."""
        from mad_spark_multiagent.agent_defs.advocate import advocate_idea
        
        # Mock agent response
        mock_agent.call.return_value = "Strong arguments"
        
        # Call the tool
        result = advocate_idea(idea="Idea", evaluation="Good", context="Context")
        
        assert result == "Strong arguments"
        
        # Test empty response handling - returns placeholder string (no exception)
        mock_agent.call.return_value = ""
        result = advocate_idea(idea="Idea", evaluation="Eval", context="Context")
        assert result == ADVOCATE_EMPTY_RESPONSE
    
    @patch('mad_spark_multiagent.agent_defs.skeptic.skeptic_agent')
    def test_criticize_idea_tool(self, mock_agent):
        """Test the criticize_idea tool function."""
        from mad_spark_multiagent.agent_defs.skeptic import criticize_idea
        
        # Mock agent response
        mock_agent.call.return_value = "Valid concerns"
        
        # Call the tool
        result = criticize_idea(idea="Idea", advocacy="Arguments", context="Context")
        
        assert result == "Valid concerns"
        
        # Test empty response handling - returns placeholder string (no exception)
        mock_agent.call.return_value = ""
        result = criticize_idea(idea="Idea", advocacy="Args", context="Context")
        assert result == SKEPTIC_EMPTY_RESPONSE
    
    def test_build_generation_prompt(self):
        """Test the prompt building function."""
        from mad_spark_multiagent.agent_defs.idea_generator import build_generation_prompt
        
        prompt = build_generation_prompt("Urban Planning", "Budget-friendly")
        
        assert "Urban Planning" in prompt
        assert "Budget-friendly" in prompt
        assert "Context:" in prompt