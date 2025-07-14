"""Comprehensive tests for MadSpark agent modules."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the agent functions we want to test
from madspark.agents.idea_generator import generate_ideas, build_generation_prompt
from madspark.agents.critic import evaluate_ideas
from madspark.agents.advocate import advocate_idea
from madspark.agents.skeptic import criticize_idea


class TestIdeaGenerator:
    """Test cases for the idea generator agent."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Mock Google GenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "ideas": [
                {
                    "title": "Test Idea 1",
                    "description": "A test idea for validation",
                    "innovation_score": 8,
                    "feasibility_score": 7
                },
                {
                    "title": "Test Idea 2", 
                    "description": "Another test idea",
                    "innovation_score": 9,
                    "feasibility_score": 6
                }
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        return mock_client
    
    @patch('madspark.agents.idea_generator.genai')
    def test_generate_ideas_success(self, mock_genai, mock_genai_client):
        """Test successful idea generation."""
        mock_genai.Client.return_value = mock_genai_client
        
        result = generate_ideas("AI automation", "Cost-effective solutions")
        
        assert result is not None
        assert len(result["ideas"]) == 2
        assert result["ideas"][0]["title"] == "Test Idea 1"
        assert result["ideas"][1]["innovation_score"] == 9
        
    @patch('madspark.agents.idea_generator.genai')
    def test_generate_ideas_api_error(self, mock_genai):
        """Test idea generation with API error."""
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        
        result = generate_ideas("AI automation", "Cost-effective solutions")
        
        # Should return empty structure or handle gracefully
        assert result is None or "error" in result
        
    def test_build_generation_prompt(self):
        """Test prompt building functionality."""
        prompt = build_generation_prompt("Test theme", "Test constraints")
        
        assert "Test theme" in prompt
        assert "Test constraints" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestCritic:
    """Test cases for the critic agent."""
    
    @pytest.fixture
    def sample_ideas(self):
        """Sample ideas for testing."""
        return [
            {
                "title": "AI-Powered Assistant",
                "description": "An AI assistant for productivity",
                "innovation_score": 7,
                "feasibility_score": 8
            },
            {
                "title": "Smart Home Integration",
                "description": "IoT device integration platform",
                "innovation_score": 6,
                "feasibility_score": 9
            }
        ]
    
    @patch('madspark.agents.critic.genai')
    def test_evaluate_ideas_success(self, mock_genai, sample_ideas):
        """Test successful idea evaluation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "evaluations": [
                {
                    "idea_title": "AI-Powered Assistant",
                    "overall_score": 7.5,
                    "strengths": ["Practical application", "Market demand"],
                    "weaknesses": ["High competition", "Technical complexity"]
                },
                {
                    "idea_title": "Smart Home Integration",
                    "overall_score": 8.0,
                    "strengths": ["Growing market", "Clear value proposition"],
                    "weaknesses": ["Privacy concerns", "Hardware dependencies"]
                }
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        result = evaluate_ideas(sample_ideas)
        
        assert result is not None
        assert len(result["evaluations"]) == 2
        assert result["evaluations"][0]["overall_score"] == 7.5
        assert "strengths" in result["evaluations"][0]
        assert "weaknesses" in result["evaluations"][0]


class TestAdvocate:
    """Test cases for the advocate agent."""
    
    @pytest.fixture
    def sample_idea(self):
        """Sample idea for testing."""
        return {
            "title": "AI-Powered Assistant",
            "description": "An AI assistant for productivity",
            "innovation_score": 7,
            "feasibility_score": 8
        }
    
    @patch('madspark.agents.advocate.genai')
    def test_advocate_idea_success(self, mock_genai, sample_idea):
        """Test successful idea advocacy."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "advocacy": {
                "key_strengths": [
                    "Addresses real productivity challenges",
                    "Scalable business model",
                    "Strong market demand"
                ],
                "value_proposition": "Significantly improves workplace efficiency",
                "market_potential": "Large and growing market segment",
                "competitive_advantages": [
                    "Advanced AI capabilities",
                    "User-friendly interface"
                ]
            }
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        result = advocate_idea(sample_idea)
        
        assert result is not None
        assert "advocacy" in result
        assert len(result["advocacy"]["key_strengths"]) == 3
        assert "value_proposition" in result["advocacy"]
        assert "market_potential" in result["advocacy"]


class TestSkeptic:
    """Test cases for the skeptic agent."""
    
    @pytest.fixture
    def sample_idea(self):
        """Sample idea for testing."""
        return {
            "title": "AI-Powered Assistant",
            "description": "An AI assistant for productivity",
            "innovation_score": 7,
            "feasibility_score": 8
        }
    
    @patch('madspark.agents.skeptic.genai')
    def test_criticize_idea_success(self, mock_genai, sample_idea):
        """Test successful idea criticism."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "criticism": {
                "key_concerns": [
                    "High development costs",
                    "Strong competition from established players",
                    "Technical complexity and maintenance"
                ],
                "risk_assessment": "Medium to high risk due to market saturation",
                "potential_failures": [
                    "User adoption challenges",
                    "Accuracy and reliability issues"
                ],
                "implementation_challenges": [
                    "Data privacy compliance",
                    "Integration complexity"
                ]
            }
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        result = criticize_idea(sample_idea)
        
        assert result is not None
        assert "criticism" in result
        assert len(result["criticism"]["key_concerns"]) == 3
        assert "risk_assessment" in result["criticism"]
        assert "potential_failures" in result["criticism"]


class TestAgentIntegration:
    """Integration tests for agent interactions."""
    
    def test_agent_error_handling(self):
        """Test that agents handle errors gracefully."""
        # Test with invalid input
        result = generate_ideas("", "")
        assert result is None or "error" in result
        
        # Test with None input
        result = evaluate_ideas(None)
        assert result is None or "error" in result
    
    @patch('madspark.agents.idea_generator.genai')
    @patch('madspark.agents.critic.genai')
    def test_workflow_integration(self, mock_critic_genai, mock_gen_genai):
        """Test basic workflow integration between agents."""
        # Mock idea generation
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = json.dumps({
            "ideas": [{"title": "Test Idea", "description": "Test description"}]
        })
        mock_gen_client.models.generate_content.return_value = mock_gen_response
        mock_gen_genai.Client.return_value = mock_gen_client
        
        # Mock critic evaluation
        mock_critic_client = Mock()
        mock_critic_response = Mock()
        mock_critic_response.text = json.dumps({
            "evaluations": [{"idea_title": "Test Idea", "overall_score": 8.0}]
        })
        mock_critic_client.models.generate_content.return_value = mock_critic_response
        mock_critic_genai.Client.return_value = mock_critic_client
        
        # Test the workflow
        ideas = generate_ideas("AI automation", "Cost-effective")
        assert ideas is not None
        
        evaluations = evaluate_ideas(ideas["ideas"])
        assert evaluations is not None
        assert len(evaluations["evaluations"]) == 1