"""Unit tests for agent functions with mocked API calls."""
import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIdeaGenerator:
    """Test IdeaGenerator agent functions."""
    
    @patch('agent_defs.idea_generator.genai')
    def test_generate_ideas_success(self, mock_genai, sample_theme, sample_constraints):
        """Test successful idea generation."""
        from agent_defs.idea_generator import generate_ideas
        
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "1. 猫型宇宙船\n2. 宇宙船猫システム\n3. 逆転重力移動"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = generate_ideas(sample_theme, sample_constraints, temperature=0.5)
        
        assert result["status"] == "success"
        assert "ideas" in result
        assert len(result["ideas"]) == 3
        assert "猫型宇宙船" in result["ideas"][0]
        
        # Verify API call
        mock_genai.GenerativeModel.assert_called_once_with('gemini-2.0-flash')
        mock_model.generate_content.assert_called_once()
    
    @patch('agent_defs.idea_generator.genai')
    def test_generate_ideas_with_temperature(self, mock_genai, sample_theme, sample_constraints):
        """Test idea generation with different temperature values."""
        from agent_defs.idea_generator import generate_ideas
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "1. Test idea"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test with custom temperature
        result = generate_ideas(sample_theme, sample_constraints, temperature=0.9)
        
        assert result["status"] == "success"
        # Verify temperature was passed to generation config
        call_args = mock_model.generate_content.call_args
        assert 'generation_config' in call_args.kwargs
    
    @patch('agent_defs.idea_generator.genai')
    def test_generate_ideas_api_error(self, mock_genai, sample_theme, sample_constraints):
        """Test error handling when API fails."""
        from agent_defs.idea_generator import generate_ideas
        
        mock_genai.GenerativeModel.side_effect = Exception("API Error")
        
        result = generate_ideas(sample_theme, sample_constraints)
        
        assert result["status"] == "error"
        assert "message" in result
        assert "API Error" in result["message"]
    
    def test_build_generation_prompt(self, sample_theme, sample_constraints):
        """Test prompt building function."""
        from agent_defs.idea_generator import build_generation_prompt
        
        prompt = build_generation_prompt(sample_theme, sample_constraints)
        
        assert sample_theme in prompt
        assert "逆転の発想" in prompt
        assert "猫" in prompt
        assert "宇宙船" in prompt
        assert "番号付きリスト" in prompt


class TestCritic:
    """Test Critic agent functions."""
    
    @patch('agent_defs.critic.genai')
    def test_evaluate_ideas_success(self, mock_genai, sample_ideas):
        """Test successful idea evaluation."""
        from agent_defs.critic import evaluate_ideas
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "スコア: 4\n面白いアイデアです"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = evaluate_ideas(sample_ideas[:2], temperature=0.3)
        
        assert result["status"] == "success"
        assert "evaluations" in result
        assert len(result["evaluations"]) == 2
        
        evaluation = result["evaluations"][0]
        assert "idea" in evaluation
        assert "score" in evaluation
        assert "comment" in evaluation
        assert evaluation["score"] == 4
    
    @patch('agent_defs.critic.genai')
    def test_evaluate_ideas_score_extraction(self, mock_genai, sample_ideas):
        """Test score extraction from various response formats."""
        from agent_defs.critic import evaluate_ideas
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "評価結果: スコア: 5 - 非常に創造的"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = evaluate_ideas([sample_ideas[0]])
        
        assert result["status"] == "success"
        assert result["evaluations"][0]["score"] == 5
    
    @patch('agent_defs.critic.genai')
    def test_evaluate_ideas_default_score(self, mock_genai, sample_ideas):
        """Test default score when extraction fails."""
        from agent_defs.critic import evaluate_ideas
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "面白いですね"  # No score pattern
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = evaluate_ideas([sample_ideas[0]])
        
        assert result["status"] == "success"
        assert result["evaluations"][0]["score"] == 3  # Default fallback


class TestAdvocate:
    """Test Advocate agent functions."""
    
    @patch('agent_defs.advocate.genai')
    def test_advocate_idea_success(self, mock_genai):
        """Test successful advocacy generation."""
        from agent_defs.advocate import advocate_idea
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "1. 革新的な発想\n2. 実用性が高い\n3. 環境に優しい"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        idea = "猫型宇宙船で移動する"
        result = advocate_idea(idea, temperature=0.5)
        
        assert result["status"] == "success"
        assert "advocacy" in result
        assert "革新的" in result["advocacy"]
    
    @patch('agent_defs.advocate.genai')
    def test_advocate_idea_error(self, mock_genai):
        """Test error handling in advocacy."""
        from agent_defs.advocate import advocate_idea
        
        mock_genai.GenerativeModel.side_effect = Exception("Network error")
        
        result = advocate_idea("test idea")
        
        assert result["status"] == "error"
        assert "message" in result


class TestSkeptic:
    """Test Skeptic agent functions."""
    
    @patch('agent_defs.skeptic.genai')
    def test_criticize_idea_success(self, mock_genai):
        """Test successful criticism generation."""
        from agent_defs.skeptic import criticize_idea
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "1. 技術的な課題\n2. コストが高い\n3. 安全性の懸念"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        idea = "猫型宇宙船で移動する"
        result = criticize_idea(idea, temperature=0.5)
        
        assert result["status"] == "success"
        assert "criticism" in result
        assert "課題" in result["criticism"]
    
    @patch('agent_defs.skeptic.genai')
    def test_criticize_idea_empty_response(self, mock_genai):
        """Test handling of empty response."""
        from agent_defs.skeptic import criticize_idea
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = criticize_idea("test idea")
        
        assert result["status"] == "success"
        assert result["criticism"] == ""


class TestParameterValidation:
    """Test parameter validation across all agent functions."""
    
    @patch('agent_defs.idea_generator.genai')
    def test_temperature_range_validation(self, mock_genai):
        """Test that functions handle various temperature values."""
        from agent_defs.idea_generator import generate_ideas
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "1. Test idea"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test edge cases
        temperatures = [0.0, 0.1, 0.5, 0.9, 1.0]
        for temp in temperatures:
            result = generate_ideas("test", {}, temperature=temp)
            assert result["status"] == "success"
    
    def test_constraint_handling(self):
        """Test handling of various constraint formats."""
        from agent_defs.idea_generator import build_generation_prompt
        
        test_cases = [
            {},  # Empty constraints
            {"mode": "逆転"},  # Mode only
            {"random_words": ["猫"]},  # Single word
            {"random_words": ["猫", "宇宙船"]},  # Two words
            {"random_words": ["猫", "宇宙船", "未来"]},  # Multiple words
            {"mode": "逆転", "random_words": ["猫", "宇宙船"]},  # Combined
        ]
        
        for constraints in test_cases:
            prompt = build_generation_prompt("テスト", constraints)
            assert "テスト" in prompt
            assert isinstance(prompt, str)
            assert len(prompt) > 0