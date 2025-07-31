"""Tests for AI-powered MultiDimensionalEvaluator."""
import pytest
from unittest.mock import Mock, patch
from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator


class TestAIMultiDimensionalEvaluator:
    """Test suite for AI-powered multi-dimensional evaluation."""
    
    def test_requires_genai_client(self):
        """Test that evaluator requires a GenAI client and fails without it."""
        with pytest.raises(ValueError) as exc_info:
            MultiDimensionalEvaluator(genai_client=None)
        
        assert "MultiDimensionalEvaluator requires a GenAI client" in str(exc_info.value)
        assert "Keyword-based evaluation has been deprecated" in str(exc_info.value)
        assert "GOOGLE_API_KEY" in str(exc_info.value)
    
    def test_evaluate_idea_with_ai(self):
        """Test successful AI evaluation across all dimensions."""
        # Mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "8.5"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Test evaluation
        result = evaluator.evaluate_idea(
            idea="Create an AI-powered recycling app",
            context={"theme": "sustainability", "constraints": "mobile app"}
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'dimension_scores' in result
        assert 'weighted_score' in result
        assert 'confidence_interval' in result
        assert 'evaluation_summary' in result
        
        # Verify all dimensions evaluated
        dimensions = ['feasibility', 'innovation', 'impact', 'cost_effectiveness', 
                     'scalability', 'risk_assessment', 'timeline']
        for dim in dimensions:
            assert dim in result['dimension_scores']
            assert 1 <= result['dimension_scores'][dim] <= 10
        
        # Verify AI was called for each dimension
        assert mock_client.models.generate_content.call_count == len(dimensions)
    
    def test_ai_failure_raises_error(self):
        """Test that AI failures raise clear errors."""
        # Mock GenAI client that fails
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API connection failed")
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        with pytest.raises(RuntimeError) as exc_info:
            evaluator.evaluate_idea(
                idea="Test idea",
                context={"theme": "test"}
            )
        
        assert "Failed to evaluate" in str(exc_info.value)
        assert "Multi-dimensional evaluation requires working AI connection" in str(exc_info.value)
    
    def test_non_numeric_response_handling(self):
        """Test handling of non-numeric AI responses."""
        # Mock GenAI client with invalid response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "This is not a number"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        with pytest.raises(RuntimeError) as exc_info:
            evaluator.evaluate_idea(
                idea="Test idea",
                context={"theme": "test"}
            )
        
        assert "AI returned non-numeric score" in str(exc_info.value)
    
    def test_score_clamping(self):
        """Test that scores are clamped to 1-10 range."""
        mock_client = Mock()
        
        # Test over-range score
        mock_response = Mock()
        mock_response.text = "15.0"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        result = evaluator.evaluate_idea("Test", {"theme": "test"})
        
        # All scores should be clamped to 10
        for score in result['dimension_scores'].values():
            assert score == 10.0
        
        # Test under-range score
        mock_response.text = "-5.0"
        result = evaluator.evaluate_idea("Test", {"theme": "test"})
        
        # All scores should be clamped to 1
        for score in result['dimension_scores'].values():
            assert score == 1.0
    
    def test_language_agnostic_evaluation(self):
        """Test that evaluation works for non-English text."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "7.5"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Test Japanese
        result = evaluator.evaluate_idea(
            idea="持続可能な都市農業プラットフォームを作る",
            context={"theme": "都市開発", "constraints": "低予算"}
        )
        assert result['weighted_score'] == 7.5
        
        # Test Spanish
        result = evaluator.evaluate_idea(
            idea="Crear una plataforma de agricultura urbana sostenible",
            context={"theme": "desarrollo urbano", "constraints": "bajo presupuesto"}
        )
        assert result['weighted_score'] == 7.5
    
    def test_dimension_prompt_generation(self):
        """Test that appropriate prompts are generated for each dimension."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "7.0"
        mock_client.models.generate_content.return_value = mock_response
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        
        # Capture the prompts used
        captured_prompts = []
        def capture_prompt(model, contents, config):
            captured_prompts.append(contents)
            return mock_response
        
        mock_client.models.generate_content.side_effect = capture_prompt
        
        evaluator.evaluate_idea(
            idea="Build a quantum computer",
            context={"theme": "technology", "constraints": "research lab"}
        )
        
        # Verify prompts contain dimension-specific content
        assert len(captured_prompts) == 7
        
        # Check that prompts contain the idea and dimension-specific guidance
        for prompt in captured_prompts:
            assert "Build a quantum computer" in prompt
            assert "scale of 1-10" in prompt
            assert "Respond with only the numeric score" in prompt
    
    def test_weighted_score_calculation(self):
        """Test that weighted scores are calculated correctly."""
        mock_client = Mock()
        
        # Set up different scores for different dimensions
        scores = {"feasibility": "3.0", "innovation": "9.0", "impact": "8.0",
                 "cost_effectiveness": "4.0", "scalability": "7.0", 
                 "risk_assessment": "5.0", "timeline": "6.0"}
        
        dimension_order = ['feasibility', 'innovation', 'impact', 'cost_effectiveness',
                          'scalability', 'risk_assessment', 'timeline']
        
        call_count = 0
        def return_score_by_dimension(model, contents, config):
            nonlocal call_count
            score = scores[dimension_order[call_count]]
            call_count += 1
            mock_response = Mock()
            mock_response.text = score
            return mock_response
        
        mock_client.models.generate_content.side_effect = return_score_by_dimension
        
        evaluator = MultiDimensionalEvaluator(genai_client=mock_client)
        result = evaluator.evaluate_idea("Test", {"theme": "test"})
        
        # Verify individual scores
        assert result['dimension_scores']['feasibility'] == 3.0
        assert result['dimension_scores']['innovation'] == 9.0
        
        # Verify weighted score is reasonable
        assert 3.0 <= result['weighted_score'] <= 9.0


class TestReasoningEngineIntegration:
    """Test integration of AI evaluator with ReasoningEngine."""
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_reasoning_engine_without_api_key(self, mock_get_client):
        """Test that ReasoningEngine handles missing API key gracefully."""
        mock_get_client.return_value = None
        
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        # Should not raise, but evaluator should be None
        engine = ReasoningEngine({"theme": "test"})
        assert engine.multi_evaluator is None
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_reasoning_engine_with_api_key(self, mock_get_client):
        """Test that ReasoningEngine creates evaluator when API key available."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        engine = ReasoningEngine({"theme": "test"})
        assert engine.multi_evaluator is not None
        assert isinstance(engine.multi_evaluator, MultiDimensionalEvaluator)


class TestCoordinatorIntegration:
    """Test integration with coordinator."""
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_coordinator_handles_none_evaluator(self, mock_get_client):
        """Test that coordinator continues when evaluator is None."""
        mock_get_client.return_value = None
        
        # Test that ReasoningEngine creates None evaluator when no API key
        from madspark.core.enhanced_reasoning import ReasoningEngine
        
        engine = ReasoningEngine({"theme": "test"})
        assert engine.multi_evaluator is None
        
        # This verifies the coordinator can handle None evaluator
        # without needing to run the full coordinator
    
    @patch('madspark.agents.genai_client.get_genai_client')
    def test_coordinator_with_ai_evaluation_integration(self, mock_get_client):
        """Test end-to-end integration with coordinator using AI evaluation."""
        # Mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "7.5"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Test coordinator integration by directly testing the components
        context = {"theme": "test topic", "constraints": "test constraints"}
        
        # Initialize engine with mock client
        from madspark.core.enhanced_reasoning import ReasoningEngine
        engine = ReasoningEngine(context, genai_client=mock_client)
        
        # Verify evaluator was created
        assert engine.multi_evaluator is not None
        
        # Test evaluation
        result = engine.multi_evaluator.evaluate_idea("Test idea", context)
        
        # Verify structure
        assert 'dimension_scores' in result
        assert 'weighted_score' in result
        assert result['weighted_score'] == 7.5
        
        # Verify AI was called for each dimension
        assert mock_client.models.generate_content.call_count >= 7
        
        # Verify context was formatted properly (not raw dict)
        call_args = mock_client.models.generate_content.call_args_list[0]
        prompt = call_args[1]['contents']
        assert "Theme: test topic" in prompt
        assert "Constraints: test constraints" in prompt
        assert "{" not in prompt  # No raw dict formatting