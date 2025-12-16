"""Tests for multi-dimensional batch evaluation functionality."""
import pytest
from unittest.mock import Mock

try:
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator


class TestMultiDimensionalBatchEvaluation:
    """Test batch evaluation of multiple ideas across all dimensions."""
    
    def test_batch_evaluation_requires_genai_client(self):
        """Test that batch evaluation requires a configured GenAI client."""
        # Error message now mentions "either a GenAI client or LLM router"
        with pytest.raises(ValueError, match="MultiDimensionalEvaluator requires either a GenAI client or LLM router"):
            MultiDimensionalEvaluator(genai_client=None)
    
    def test_evaluate_ideas_batch_single_idea(self):
        """Test batch evaluation with a single idea."""
        # Mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "feasibility": 8,
            "innovation": 7,
            "impact": 9,
            "cost_effectiveness": 6,
            "scalability": 8,
            "risk_assessment": 7,
            "timeline": 6
        }]'''
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = ["Create an AI-powered tutoring system"]
        context = {"theme": "Education", "constraints": "Limited budget"}
        
        results = evaluator.evaluate_ideas_batch(ideas, context)
        
        assert len(results) == 1
        assert results[0]["idea_index"] == 0
        assert results[0]["feasibility"] == 8
        assert results[0]["innovation"] == 7
        assert "overall_score" in results[0]
        assert "weighted_score" in results[0]
        
        # Verify API calls: 1 for batch evaluation + 1 for summary
        assert mock_client.models.generate_content.call_count == 2
    
    def test_evaluate_ideas_batch_multiple_ideas(self):
        """Test batch evaluation with multiple ideas."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''[
            {
                "idea_index": 0,
                "feasibility": 8,
                "innovation": 7,
                "impact": 9,
                "cost_effectiveness": 6,
                "scalability": 8,
                "risk_assessment": 7,
                "timeline": 6
            },
            {
                "idea_index": 1,
                "feasibility": 6,
                "innovation": 9,
                "impact": 7,
                "cost_effectiveness": 8,
                "scalability": 6,
                "risk_assessment": 5,
                "timeline": 8
            },
            {
                "idea_index": 2,
                "feasibility": 9,
                "innovation": 5,
                "impact": 6,
                "cost_effectiveness": 9,
                "scalability": 7,
                "risk_assessment": 8,
                "timeline": 9
            }
        ]'''
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = [
            "AI tutoring system",
            "VR classroom experience",
            "Automated grading platform"
        ]
        context = {"theme": "Education", "constraints": "Limited budget"}
        
        results = evaluator.evaluate_ideas_batch(ideas, context)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["idea_index"] == i
            assert all(dim in result for dim in [
                "feasibility", "innovation", "impact", 
                "cost_effectiveness", "scalability", 
                "risk_assessment", "timeline"
            ])
            assert "overall_score" in result
            assert "weighted_score" in result
        
        # Verify API calls: 1 for batch evaluation + 3 for summaries (one per idea)
        assert mock_client.models.generate_content.call_count == 4
    
    def test_evaluate_ideas_batch_validates_response(self):
        """Test that batch evaluation validates response structure."""
        mock_client = Mock()
        mock_response = Mock()
        # Missing required fields
        mock_response.text = '[{"idea_index": 0, "feasibility": 8}]'
        mock_client.models.generate_content.return_value = mock_response

        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)

        ideas = ["Test idea"]
        context = {"theme": "Test", "constraints": "None"}

        with pytest.raises(RuntimeError, match="Failed to evaluate ideas.*validation errors"):
            evaluator.evaluate_ideas_batch(ideas, context)
    
    def test_evaluate_ideas_batch_handles_api_errors(self):
        """Test graceful handling of API errors during batch evaluation."""
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = ["Test idea"]
        context = {"theme": "Test", "constraints": "None"}
        
        with pytest.raises(RuntimeError, match="Failed to evaluate ideas"):
            evaluator.evaluate_ideas_batch(ideas, context)
    
    def test_evaluate_ideas_batch_empty_list(self):
        """Test batch evaluation with empty idea list."""
        mock_client = Mock()
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = []
        context = {"theme": "Test", "constraints": "None"}
        
        results = evaluator.evaluate_ideas_batch(ideas, context)
        
        assert results == []
        # Should not make API call for empty list
        assert mock_client.models.generate_content.call_count == 0
    
    def test_evaluate_ideas_batch_preserves_order(self):
        """Test that batch evaluation preserves idea order."""
        mock_client = Mock()
        mock_response = Mock()
        # Return in different order to test ordering
        mock_response.text = '''[
            {
                "idea_index": 2,
                "feasibility": 9,
                "innovation": 5,
                "impact": 6,
                "cost_effectiveness": 9,
                "scalability": 7,
                "risk_assessment": 8,
                "timeline": 9
            },
            {
                "idea_index": 0,
                "feasibility": 8,
                "innovation": 7,
                "impact": 9,
                "cost_effectiveness": 6,
                "scalability": 8,
                "risk_assessment": 7,
                "timeline": 6
            },
            {
                "idea_index": 1,
                "feasibility": 6,
                "innovation": 9,
                "impact": 7,
                "cost_effectiveness": 8,
                "scalability": 6,
                "risk_assessment": 5,
                "timeline": 8
            }
        ]'''
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = ["Idea A", "Idea B", "Idea C"]
        context = {"theme": "Test", "constraints": "None"}
        
        results = evaluator.evaluate_ideas_batch(ideas, context)
        
        # Results should be sorted by idea_index
        assert results[0]["idea_index"] == 0
        assert results[1]["idea_index"] == 1
        assert results[2]["idea_index"] == 2
    
    def test_evaluate_ideas_batch_calculates_aggregate_scores(self):
        """Test that batch evaluation calculates overall and weighted scores."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "feasibility": 8,
            "innovation": 8,
            "impact": 8,
            "cost_effectiveness": 8,
            "scalability": 8,
            "risk_assessment": 8,
            "timeline": 8
        }]'''
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        ideas = ["Test idea"]
        context = {"theme": "Test", "constraints": "None"}
        
        results = evaluator.evaluate_ideas_batch(ideas, context)
        
        result = results[0]
        # All dimensions are 8, so overall should be 8
        assert result["overall_score"] == 8.0
        # Weighted score depends on dimension weights
        assert "weighted_score" in result
        assert "evaluation_summary" in result
        assert "confidence_interval" in result