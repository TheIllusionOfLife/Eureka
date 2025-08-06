"""Test language consistency across all agents and evaluators.

This test suite ensures that all components respond in the same language
as the user's input, addressing the issue where Multi-dimensional Analysis
doesn't respond in the user's language.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION


class TestLanguageConsistency:
    """Test language consistency across all evaluation components."""
    
    def test_multi_dimensional_evaluator_includes_language_instruction(self):
        """Test that MultiDimensionalEvaluator includes language consistency instruction."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "8"  # Mock score response
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Act
        prompt = evaluator._build_dimension_prompt(
            idea="革新的なアイデア",  # Japanese idea
            context={"theme": "テーマ", "constraints": "制約"},  # Japanese context
            dimension="feasibility"
        )
        
        # Assert - prompt should include language consistency instruction
        assert LANGUAGE_CONSISTENCY_INSTRUCTION in prompt, \
            "Multi-dimensional evaluation prompt must include language consistency instruction"
        
    def test_multi_dimensional_batch_prompt_includes_language_instruction(self):
        """Test that batch evaluation prompts include language consistency instruction."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '[{"idea_index": 0, "feasibility": 8, "innovation": 7, "impact": 9, "cost_effectiveness": 6, "scalability": 8, "risk_assessment": 7, "timeline": 6}]'
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Act
        prompt = evaluator._build_batch_evaluation_prompt(
            ideas=["アイデア1", "アイデア2"],  # Japanese ideas
            context={"theme": "テーマ", "constraints": "制約"},  # Japanese context
        )
        
        # Assert - batch prompt should include language consistency instruction
        assert LANGUAGE_CONSISTENCY_INSTRUCTION in prompt, \
            "Batch evaluation prompt must include language consistency instruction"
    
    def test_evaluation_summary_respects_language(self):
        """Test that evaluation summary generation respects input language."""
        # Arrange
        mock_client = Mock()
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Mock Japanese dimension scores
        dimension_scores = {
            'feasibility': 8.0,
            'innovation': 7.0, 
            'impact': 9.0,
            'cost_effectiveness': 6.0,
            'scalability': 8.0,
            'risk_assessment': 7.0,
            'timeline': 6.0
        }
        
        # Act
        summary = evaluator._generate_evaluation_summary(
            dimension_scores, 
            "革新的なアイデア"  # Japanese idea
        )
        
        # Assert - summary format should be consistent (not testing actual translation)
        # The method currently generates English summaries, but with language instruction
        # it should generate in the user's language
        assert "Good idea" in summary or "良いアイデア" in summary, \
            "Summary should be generated (language depends on LLM response)"
            
    def test_dimension_prompts_format_correctly_with_unicode(self):
        """Test that dimension prompts handle Unicode characters correctly."""
        # Arrange
        mock_client = Mock()
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Test with various Unicode content
        test_cases = [
            ("中文测试", {"theme": "主题", "constraints": "约束"}),  # Chinese
            ("Test français", {"theme": "Thème", "constraints": "Contraintes"}),  # French
            ("テスト", {"theme": "テーマ", "constraints": "制約"}),  # Japanese
            ("Тест", {"theme": "Тема", "constraints": "Ограничения"}),  # Russian
            ("🚀 Emoji test", {"theme": "🎯 Theme", "constraints": "📝 Constraints"}),  # Emojis
        ]
        
        for idea, context in test_cases:
            # Act
            prompt = evaluator._build_dimension_prompt(idea, context, "feasibility")
            
            # Assert
            assert idea in prompt, f"Prompt should contain the idea text: {idea}"
            assert context["theme"] in prompt, f"Prompt should contain theme: {context['theme']}"
            assert context["constraints"] in prompt, f"Prompt should contain constraints: {context['constraints']}"
            # Verify no encoding issues
            assert "�" not in prompt, "Prompt should not contain replacement characters"
    
    @patch('madspark.agents.genai_client.get_model_name')
    def test_actual_api_call_includes_language_instruction(self, mock_get_model):
        """Test that actual API calls include language instruction in the prompt."""
        # Arrange
        mock_get_model.return_value = "gemini-1.5-flash"
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "7"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Act
        evaluator.evaluate_idea(
            idea="Une idée innovante",  # French idea
            context={"theme": "Thème", "constraints": "Contraintes"}
        )
        
        # Assert - verify the actual prompt sent to API
        call_args = mock_client.models.generate_content.call_args
        actual_prompt = call_args[1]['contents']
        
        assert LANGUAGE_CONSISTENCY_INSTRUCTION in actual_prompt, \
            "API call must include language consistency instruction"
        assert "Une idée innovante" in actual_prompt, \
            "API call must include the original idea text"


class TestLogicalInferenceLanguageConsistency:
    """Test language consistency in logical inference outputs."""
    
    def test_logical_inference_respects_input_language(self):
        """Test that logical inference engine respects input language."""
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine
        
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        # Mock a response that would be in the same language
        mock_response.text = """INFERENCE_CHAIN:
- [Step 1]: このアイデアはテーマに対応しています
- [Step 2]: 制約を満たしています

CONCLUSION: 論理的に妥当です

CONFIDENCE: 0.8

IMPROVEMENTS: より詳細な説明が必要です"""
        
        mock_client.models.generate_content.return_value = mock_response
        
        engine = LogicalInferenceEngine(genai_client=mock_client)
        
        # Act
        result = engine.analyze(
            idea="革新的なアイデア",
            topic="テーマ",
            context="制約",
            analysis_type="full"
        )
        
        # Assert
        assert result.conclusion == "論理的に妥当です", \
            "Logical inference should preserve language from LLM response"
        assert len(result.inference_chain) > 0, \
            "Inference chain should be populated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])