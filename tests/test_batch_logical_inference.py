"""Tests for batch logical inference optimization."""
import pytest
from unittest.mock import Mock, patch
from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceResult, InferenceType
from madspark.core.async_coordinator import AsyncCoordinator


class TestBatchLogicalInference:
    """Test cases for batch logical inference processing."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Mock GenAI client for testing."""
        client = Mock()
        client.models = Mock()
        return client
    
    @pytest.fixture
    def inference_engine(self, mock_genai_client):
        """Create LogicalInferenceEngine instance with mocked client."""
        return LogicalInferenceEngine(mock_genai_client)
    
    @pytest.fixture
    def sample_ideas(self):
        """Sample ideas for batch processing."""
        return [
            "Simple mobile game with one-button controls",
            "Puzzle game using color matching mechanics",
            "Endless runner with procedural generation"
        ]
    
    def test_analyze_batch_basic_functionality(self, inference_engine, mock_genai_client, sample_ideas):
        """Test basic batch analysis functionality."""
        # Mock the API response
        mock_response = Mock()
        mock_response.text = """=== ANALYSIS_FOR_IDEA_1 ===
INFERENCE_CHAIN:
- [Step 1]: Simple controls address mobile constraints
- [Step 2]: One-button design reduces complexity

CONCLUSION: Logically sound for mobile development

CONFIDENCE: 0.8

IMPROVEMENTS: Add visual feedback for button presses

=== ANALYSIS_FOR_IDEA_2 ===
INFERENCE_CHAIN:
- [Step 1]: Color matching is intuitive
- [Step 2]: Puzzle mechanics provide engagement

CONCLUSION: Strong logical foundation for puzzle games

CONFIDENCE: 0.9

IMPROVEMENTS: Consider colorblind accessibility

=== ANALYSIS_FOR_IDEA_3 ===
INFERENCE_CHAIN:
- [Step 1]: Procedural generation increases replayability
- [Step 2]: Endless format suits mobile sessions

CONCLUSION: Well-suited for mobile endless runner genre

CONFIDENCE: 0.85

IMPROVEMENTS: Balance difficulty progression"""
        
        mock_genai_client.models.generate_content.return_value = mock_response
        
        # Perform batch analysis
        results = inference_engine.analyze_batch(ideas=sample_ideas,
            topic="mobile games",
            context="simple development",
            analysis_type=InferenceType.FULL
        )
        
        # Verify results
        assert len(results) == 3
        assert all(isinstance(result, InferenceResult) for result in results)
        
        # Check first result
        assert results[0].confidence == 0.8
        assert "Simple controls address mobile constraints" in results[0].inference_chain[0]
        assert "Add visual feedback" in results[0].improvements
        
        # Check API call was made correctly
        mock_genai_client.models.generate_content.assert_called_once()
        call_args = mock_genai_client.models.generate_content.call_args
        assert "IDEA_1:" in call_args.kwargs['contents']
        assert "IDEA_2:" in call_args.kwargs['contents']
        assert "IDEA_3:" in call_args.kwargs['contents']
    
    def test_analyze_batch_empty_list(self, inference_engine):
        """Test batch analysis with empty ideas list."""
        results = inference_engine.analyze_batch(ideas=[],
            topic="test",
            context="test"
        )
        
        assert results == []
    
    def test_analyze_batch_api_error(self, inference_engine, mock_genai_client, sample_ideas):
        """Test batch analysis with API error."""
        # Mock API error
        mock_genai_client.models.generate_content.side_effect = RuntimeError("API Error")
        
        results = inference_engine.analyze_batch(ideas=sample_ideas,
            topic="test",
            context="test"
        )
        
        # Should return error results for all ideas
        assert len(results) == 3
        assert all(result.error == "API Error" for result in results)
        assert all(result.confidence == 0.0 for result in results)
    
    def test_analyze_batch_parsing_failure(self, inference_engine, mock_genai_client, sample_ideas):
        """Test batch analysis with malformed response."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.text = "Invalid response format"
        mock_genai_client.models.generate_content.return_value = mock_response
        
        results = inference_engine.analyze_batch(ideas=sample_ideas,
            topic="test",
            context="test"
        )
        
        # Should return error results for all ideas
        assert len(results) == 3
        
        # The first result might be parsed from invalid data, so it could have low confidence
        # The remaining results should be error placeholders
        assert all(result.confidence <= 0.5 for result in results)  # All should have low confidence
        assert any("Unable to parse" in result.conclusion for result in results)  # At least some should have error messages
    
    def test_analyze_batch_partial_parsing(self, inference_engine, mock_genai_client, sample_ideas):
        """Test batch analysis with partially parseable response."""
        # Mock response with only one valid analysis
        mock_response = Mock()
        mock_response.text = """=== ANALYSIS_FOR_IDEA_1 ===
INFERENCE_CHAIN:
- [Step 1]: Valid analysis

CONCLUSION: First idea analyzed correctly

CONFIDENCE: 0.8

IMPROVEMENTS: None needed

Invalid content for remaining ideas..."""
        
        mock_genai_client.models.generate_content.return_value = mock_response
        
        results = inference_engine.analyze_batch(ideas=sample_ideas,
            topic="test",
            context="test"
        )
        
        # Should have one valid result and two error results
        assert len(results) == 3
        assert results[0].confidence == 0.8
        assert results[0].conclusion == "First idea analyzed correctly"
        # Remaining results should be error placeholders
        assert "Unable to parse" in results[1].conclusion
        assert "Unable to parse" in results[2].conclusion
    
    def test_batch_prompt_format(self, inference_engine):
        """Test that batch prompt is properly formatted."""
        ideas = ["Idea 1", "Idea 2"]
        prompt = inference_engine._get_batch_analysis_prompt(
            ideas, "topic", "context", InferenceType.FULL
        )
        
        # Check prompt contains all ideas
        assert "IDEA_1:" in prompt
        assert "IDEA_2:" in prompt
        assert "Idea 1" in prompt
        assert "Idea 2" in prompt
        
        # Check prompt has proper structure
        assert "=== ANALYSIS_FOR_IDEA_1 ===" in prompt
        assert "=== ANALYSIS_FOR_IDEA_2 ===" in prompt
        assert "INFERENCE_CHAIN:" in prompt
        assert "CONFIDENCE:" in prompt
        assert "IMPROVEMENTS:" in prompt
    
    def test_to_dict_method(self):
        """Test InferenceResult to_dict conversion."""
        result = InferenceResult(
            inference_chain=["Step 1", "Step 2"],
            conclusion="Test conclusion",
            confidence=0.8,
            improvements="Test improvements"
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["inference_chain"] == ["Step 1", "Step 2"]
        assert data["conclusion"] == "Test conclusion"
        assert data["confidence"] == 0.8
        assert data["improvements"] == "Test improvements"


class TestAsyncCoordinatorBatchLogicalInference:
    """Test async coordinator's batch logical inference implementation."""
    
    @pytest.fixture
    def async_coordinator(self):
        """Create an async coordinator instance."""
        return AsyncCoordinator()
    
    @pytest.fixture
    def sample_candidates(self):
        """Create sample candidates for testing."""
        return [
            {
                "text": "Idea 1: AI-powered education platform",
                "score": 7.5,
                "critique": "Good concept"
            },
            {
                "text": "Idea 2: Smart home automation system",
                "score": 8.0,
                "critique": "Strong potential"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_with_engine(self, async_coordinator, sample_candidates):
        """Test _run_batch_logical_inference with provided engine."""
        # Create mock reasoning engine
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.return_value = [
            InferenceResult(
                inference_chain=["Step 1: AI enhances learning", "Step 2: Personalization improves outcomes"],
                conclusion="AI education platform is logically sound",
                confidence=0.85,
                improvements="Add privacy protections"
            ),
            InferenceResult(
                inference_chain=["Step 1: Automation saves energy", "Step 2: Integration improves efficiency"],
                conclusion="Smart home system provides clear benefits",
                confidence=0.90,
                improvements="Consider security measures"
            )
        ]
        mock_engine.logical_inference_engine = mock_logical_engine
        
        # Extract ideas from candidates
        ideas = [c["text"] for c in sample_candidates]
        
        # Set up reasoning engine on coordinator
        async_coordinator.reasoning_engine = mock_engine
        
        # Run batch logical inference with new signature
        results = await async_coordinator._run_batch_logical_inference(ideas=ideas,
            topic="Technology innovations",
            context="Must be practical",
            analysis_type=InferenceType.FULL
        )
        
        # Verify analyze_batch was called correctly
        mock_logical_engine.analyze_batch.assert_called_once_with(
            ["Idea 1: AI-powered education platform", "Idea 2: Smart home automation system"],
            "Technology innovations",
            "Must be practical",
            InferenceType.FULL
        )
        
        # Verify results structure - now returns InferenceResult objects
        assert len(results) == 2
        assert results[0].confidence == 0.85
        assert results[0].conclusion == "AI education platform is logically sound"
        assert results[0].improvements == "Add privacy protections"
        assert len(results[0].inference_chain) == 2
        
        assert results[1].confidence == 0.90
        assert results[1].conclusion == "Smart home system provides clear benefits"
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_no_engine(self, async_coordinator, sample_candidates):
        """Test _run_batch_logical_inference without engine falls back correctly."""
        # Extract ideas from candidates
        ideas = [c["text"] for c in sample_candidates]
        
        # No reasoning engine set
        async_coordinator.reasoning_engine = None
            
        results = await async_coordinator._run_batch_logical_inference(ideas=ideas,
            topic="Test",
            context="Test"
        )
        
        # Should return empty list when no engine available
        assert results == []
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_error_handling(self, async_coordinator, sample_candidates):
        """Test error handling in batch logical inference."""
        # Extract ideas from candidates
        ideas = [c["text"] for c in sample_candidates]
        
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = RuntimeError("API failure")
        mock_engine.logical_inference_engine = mock_logical_engine
        
        # Set up coordinator with mock engine
        async_coordinator.reasoning_engine = mock_engine
        
        # Import logger mock
        with patch('madspark.core.async_coordinator.logger') as mock_logger:
            results = await async_coordinator._run_batch_logical_inference(ideas=ideas,
                topic="Test",
                context="Test"
            )
            
            # Should return empty list on error
            assert results == []
            # Should log the error
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_empty_candidates(self, async_coordinator):
        """Test with empty ideas list."""
        results = await async_coordinator._run_batch_logical_inference(ideas=[],
            topic="Test",
            context="Test"
        )
        
        assert results == []