"""Integration tests for coordinator workflow."""
import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCoordinatorWorkflows:
    """Test coordinator workflow functions."""
    
    @patch('coordinator.idea_generator_agent')
    @patch('coordinator.critic_agent')
    @patch('coordinator.advocate_agent')
    @patch('coordinator.skeptic_agent')
    def test_adk_workflow_success(self, mock_skeptic, mock_advocate, mock_critic, mock_generator,
                                  sample_theme, sample_constraints):
        """Test successful ADK workflow execution."""
        from coordinator import run_multistep_workflow
        
        # Mock idea generation
        mock_gen_response = Mock()
        mock_gen_response.content = "1. 猫型宇宙船\n2. 重力逆転システム\n3. 宇宙船ナビゲーション"
        mock_generator.invoke.return_value = mock_gen_response
        
        # Mock evaluation
        mock_eval_response = Mock()
        mock_eval_response.content = "アイデア1: スコア4\nアイデア2: スコア5\nアイデア3: スコア3"
        mock_critic.invoke.return_value = mock_eval_response
        
        # Mock advocacy and criticism
        mock_adv_response = Mock()
        mock_adv_response.content = "革新的で実用的です"
        mock_advocate.invoke.return_value = mock_adv_response
        
        mock_skp_response = Mock()
        mock_skp_response.content = "技術的課題があります"
        mock_skeptic.invoke.return_value = mock_skp_response
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=True)
        
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 3  # Top 3 candidates
        
        # Verify agent calls
        mock_generator.invoke.assert_called_once()
        mock_critic.invoke.assert_called_once()
        assert mock_advocate.invoke.call_count >= 1
        assert mock_skeptic.invoke.call_count >= 1
        
        # Check result structure
        candidate = result["results"][0]
        assert "idea" in candidate
        assert "score" in candidate
        assert "critic_comment" in candidate
        assert "advocacy" in candidate
        assert "criticism" in candidate
    
    @patch('coordinator.generate_ideas')
    @patch('coordinator.evaluate_ideas')
    @patch('coordinator.advocate_idea')
    @patch('coordinator.criticize_idea')
    def test_direct_workflow_success(self, mock_criticize, mock_advocate, mock_evaluate, mock_generate,
                                     sample_theme, sample_constraints):
        """Test successful direct function workflow."""
        from coordinator import run_multistep_workflow
        
        # Mock idea generation
        mock_generate.return_value = {
            "status": "success",
            "ideas": ["猫型宇宙船", "重力逆転システム", "宇宙船ナビゲーション"]
        }
        
        # Mock evaluation
        mock_evaluate.return_value = {
            "status": "success",
            "evaluations": [
                {"idea": "猫型宇宙船", "score": 4, "comment": "面白い"},
                {"idea": "重力逆転システム", "score": 5, "comment": "革新的"},
                {"idea": "宇宙船ナビゲーション", "score": 3, "comment": "普通"}
            ]
        }
        
        # Mock advocacy and criticism
        mock_advocate.return_value = {"status": "success", "advocacy": "革新的です"}
        mock_criticize.return_value = {"status": "success", "criticism": "課題があります"}
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=False)
        
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 3
        
        # Verify function calls
        mock_generate.assert_called_once_with(sample_theme, sample_constraints, 0.7)
        mock_evaluate.assert_called_once()
        assert mock_advocate.call_count >= 1
        assert mock_criticize.call_count >= 1
    
    @patch('coordinator.generate_ideas')
    def test_workflow_idea_generation_failure(self, mock_generate, sample_theme, sample_constraints):
        """Test workflow handles idea generation failure."""
        from coordinator import run_multistep_workflow
        
        mock_generate.return_value = {"status": "error", "message": "API failed"}
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=False)
        
        assert result["status"] == "error"
        assert "アイデア生成に失敗" in result["message"]
    
    @patch('coordinator.generate_ideas')
    @patch('coordinator.evaluate_ideas')
    def test_workflow_evaluation_failure(self, mock_evaluate, mock_generate, sample_theme, sample_constraints):
        """Test workflow handles evaluation failure."""
        from coordinator import run_multistep_workflow
        
        mock_generate.return_value = {
            "status": "success",
            "ideas": ["テストアイデア"]
        }
        mock_evaluate.return_value = {"status": "error", "message": "評価失敗"}
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=False)
        
        assert result["status"] == "error"
        assert "評価に失敗" in result["message"]
    
    def test_workflow_exception_handling(self, sample_theme, sample_constraints):
        """Test workflow handles unexpected exceptions."""
        from coordinator import run_multistep_workflow
        
        # This should trigger an exception due to missing mocks
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=False)
        
        assert result["status"] == "error"
        assert "ワークフロー実行エラー" in result["message"]


class TestHelperFunctions:
    """Test coordinator helper functions."""
    
    def test_build_generation_prompt(self, sample_theme, sample_constraints):
        """Test generation prompt building."""
        from coordinator import build_generation_prompt
        
        prompt = build_generation_prompt(sample_theme, sample_constraints)
        
        assert sample_theme in prompt
        assert "逆転の発想" in prompt
        assert "猫" in prompt
        assert "宇宙船" in prompt
        assert "5件生成" in prompt
    
    def test_build_evaluation_prompt(self, sample_ideas):
        """Test evaluation prompt building."""
        from coordinator import build_evaluation_prompt
        
        prompt = build_evaluation_prompt(sample_ideas[:3])
        
        assert "1～5のスケール" in prompt
        assert "1. " in prompt  # Numbered list
        assert sample_ideas[0] in prompt
        assert sample_ideas[1] in prompt
        assert sample_ideas[2] in prompt
    
    def test_parse_ideas_from_response(self):
        """Test idea parsing from various response formats."""
        from coordinator import parse_ideas_from_response
        
        # Test numbered list format
        response1 = "1. 猫型宇宙船\n2. 重力逆転\n3. ナビゲーション"
        ideas1 = parse_ideas_from_response(response1)
        assert len(ideas1) == 3
        assert "猫型宇宙船" in ideas1[0]
        
        # Test bullet point format
        response2 = "• アイデア1\n• アイデア2\n• アイデア3"
        ideas2 = parse_ideas_from_response(response2)
        assert len(ideas2) == 3
        
        # Test double newline format
        response3 = "アイデア1\n\nアイデア2\n\nアイデア3"
        ideas3 = parse_ideas_from_response(response3)
        assert len(ideas3) == 3
        
        # Test single idea fallback
        response4 = "単一のアイデア"
        ideas4 = parse_ideas_from_response(response4)
        assert len(ideas4) == 1
        assert ideas4[0] == "単一のアイデア"
    
    def test_parse_evaluations_from_response(self, sample_ideas):
        """Test evaluation parsing."""
        from coordinator import parse_evaluations_from_response
        
        response = "アイデア1: スコア4 面白い\nアイデア2: スコア5 革新的\nアイデア3: スコア2 普通"
        evaluations = parse_evaluations_from_response(response, sample_ideas[:3])
        
        assert len(evaluations) == 3
        assert evaluations[0]["score"] == 4
        assert evaluations[1]["score"] == 5
        assert evaluations[2]["score"] == 2
        
        for eval_item in evaluations:
            assert "idea" in eval_item
            assert "score" in eval_item
            assert "comment" in eval_item
    
    def test_parse_evaluations_default_scores(self, sample_ideas):
        """Test evaluation parsing with default scores."""
        from coordinator import parse_evaluations_from_response
        
        response = "評価結果ですが、スコアが明記されていません"
        evaluations = parse_evaluations_from_response(response, sample_ideas[:2])
        
        assert len(evaluations) == 2
        # Should use default score of 3
        assert all(eval_item["score"] == 3 for eval_item in evaluations)


class TestTemperatureControl:
    """Test temperature control across workflows."""
    
    @patch('coordinator.generate_ideas')
    @patch('coordinator.evaluate_ideas')
    @patch('coordinator.advocate_idea')
    @patch('coordinator.criticize_idea')
    def test_temperature_propagation(self, mock_criticize, mock_advocate, mock_evaluate, mock_generate,
                                     sample_theme, sample_constraints):
        """Test that temperature is properly propagated to functions."""
        from coordinator import run_multistep_workflow
        
        # Setup mocks to return success
        mock_generate.return_value = {"status": "success", "ideas": ["test"]}
        mock_evaluate.return_value = {"status": "success", "evaluations": [{"idea": "test", "score": 4, "comment": "good"}]}
        mock_advocate.return_value = {"status": "success", "advocacy": "good"}
        mock_criticize.return_value = {"status": "success", "criticism": "bad"}
        
        # Test with custom temperature
        custom_temp = 0.8
        result = run_multistep_workflow(sample_theme, sample_constraints, 
                                         temperature=custom_temp, use_adk=False)
        
        assert result["status"] == "success"
        
        # Verify temperature was passed correctly
        mock_generate.assert_called_once_with(sample_theme, sample_constraints, custom_temp)
        mock_evaluate.assert_called_once_with(["test"], temperature=0.3)  # Fixed temperature for evaluation
        mock_advocate.assert_called_once_with("test", temperature=0.5)    # Fixed temperature for advocacy
        mock_criticize.assert_called_once_with("test", temperature=0.5)   # Fixed temperature for criticism


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    @patch('coordinator.idea_generator_agent')
    def test_adk_null_response_handling(self, mock_generator, sample_theme, sample_constraints):
        """Test handling of null responses from ADK agents."""
        from coordinator import run_multistep_workflow
        
        mock_generator.invoke.return_value = None
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=True)
        
        assert result["status"] == "error"
        assert "アイデア生成に失敗" in result["message"]
    
    @patch('coordinator.idea_generator_agent')
    def test_adk_empty_content_handling(self, mock_generator, sample_theme, sample_constraints):
        """Test handling of empty content from ADK agents."""
        from coordinator import run_multistep_workflow
        
        mock_response = Mock()
        mock_response.content = ""
        mock_generator.invoke.return_value = mock_response
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=True)
        
        assert result["status"] == "error"
        assert "アイデア生成に失敗" in result["message"]
    
    @patch('coordinator.generate_ideas')
    @patch('coordinator.evaluate_ideas')
    @patch('coordinator.advocate_idea')
    @patch('coordinator.criticize_idea')
    def test_partial_failure_handling(self, mock_criticize, mock_advocate, mock_evaluate, mock_generate,
                                      sample_theme, sample_constraints):
        """Test handling when some agents fail but others succeed."""
        from coordinator import run_multistep_workflow
        
        # Setup basic success for idea generation and evaluation
        mock_generate.return_value = {"status": "success", "ideas": ["test idea"]}
        mock_evaluate.return_value = {"status": "success", "evaluations": [{"idea": "test idea", "score": 4, "comment": "good"}]}
        
        # Make advocacy fail but criticism succeed
        mock_advocate.return_value = {"status": "error", "message": "Advocacy failed"}
        mock_criticize.return_value = {"status": "success", "criticism": "Some criticism"}
        
        result = run_multistep_workflow(sample_theme, sample_constraints, use_adk=False)
        
        assert result["status"] == "success"
        assert len(result["results"]) == 1
        
        candidate = result["results"][0]
        assert candidate["advocacy"] == ""  # Should be empty due to failure
        assert candidate["criticism"] == "Some criticism"  # Should succeed