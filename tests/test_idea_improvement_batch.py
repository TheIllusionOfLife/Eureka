"""Tests for batch idea improvement functionality."""
import pytest
from unittest.mock import Mock, patch

try:
    from madspark.agents.idea_generator import improve_ideas_batch
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.agents.idea_generator import improve_ideas_batch


class TestIdeaImprovementBatch:
    """Test batch idea improvement functionality."""
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_improve_ideas_batch_single(self, mock_model_name, mock_client):
        """Test batch improvement with single idea."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "improved_idea": "An AI-powered personalized tutoring system with adaptive learning algorithms, real-time progress tracking, and multi-modal content delivery supporting visual, auditory, and kinesthetic learners.",
            "key_improvements": ["Added adaptive learning", "Enhanced tracking", "Multi-modal support"]
        }]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_feedback = [{
            "idea": "AI tutoring system",
            "critique": "Good but needs personalization",
            "advocacy": "Strong potential impact",
            "skepticism": "Implementation complexity"
        }]
        
        results, token_usage = improve_ideas_batch(ideas_with_feedback, "Education tech", 0.9)
        
        assert len(results) == 1
        assert results[0]["idea_index"] == 0
        assert "improved_idea" in results[0]
        assert "key_improvements" in results[0]
        assert len(results[0]["key_improvements"]) == 3
        
        # Verify single API call
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_improve_ideas_batch_multiple(self, mock_model_name, mock_client):
        """Test batch improvement with multiple ideas."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response for 3 ideas
        mock_response = Mock()
        mock_response.text = '''[
            {
                "idea_index": 0,
                "improved_idea": "Improved AI tutoring with personalization",
                "key_improvements": ["Enhanced personalization", "Better tracking"]
            },
            {
                "idea_index": 1,
                "improved_idea": "VR classroom with haptic feedback and social features",
                "key_improvements": ["Added haptics", "Social integration"]
            },
            {
                "idea_index": 2,
                "improved_idea": "Automated grading with bias detection and feedback generation",
                "key_improvements": ["Bias detection", "Detailed feedback"]
            }
        ]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_feedback = [
            {
                "idea": "AI tutoring",
                "critique": "Needs work",
                "advocacy": "Good potential",
                "skepticism": "Complex"
            },
            {
                "idea": "VR classroom", 
                "critique": "Missing features",
                "advocacy": "Innovative",
                "skepticism": "Expensive"
            },
            {
                "idea": "Auto grading",
                "critique": "Bias concerns",
                "advocacy": "Efficient", 
                "skepticism": "Accuracy issues"
            }
        ]
        
        results, token_usage = improve_ideas_batch(ideas_with_feedback, "EdTech", 0.9)
        
        assert len(results) == 3
        assert isinstance(token_usage, int)
        for i in range(3):
            assert results[i]["idea_index"] == i
            assert "improved_idea" in results[i]
            assert "key_improvements" in results[i]
        
        # Single API call for all ideas
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    def test_improve_ideas_batch_empty_list(self, mock_client):
        """Test batch improvement with empty list."""
        results, token_usage = improve_ideas_batch([], "Test context", 0.9)
        
        assert results == []
        assert token_usage == 0
        # Should not make API call
        assert mock_client.models.generate_content.call_count == 0
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_improve_ideas_batch_invalid_json(self, mock_model_name, mock_client):
        """Test handling of invalid JSON response."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [{
            "idea": "Test",
            "critique": "Test",
            "advocacy": "Test",
            "skepticism": "Test"
        }]
        
        with pytest.raises(RuntimeError, match="Batch improvement failed: Expected 1 improvements, got 0"):
            improve_ideas_batch(ideas, "Test", 0.9)
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_improve_ideas_batch_api_error(self, mock_model_name, mock_client):
        """Test handling of API errors."""
        mock_model_name.return_value = "gemini-2.5-flash"
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        ideas = [{
            "idea": "Test",
            "critique": "Test",
            "advocacy": "Test",
            "skepticism": "Test"
        }]
        
        with pytest.raises(RuntimeError, match="Batch improvement failed"):
            improve_ideas_batch(ideas, "Test", 0.9)
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', False)
    def test_improve_ideas_batch_mock_mode(self):
        """Test batch improvement in mock mode (no API key)."""
        ideas = [
            {
                "idea": "Test idea 1",
                "critique": "Needs work",
                "advocacy": "Good", 
                "skepticism": "Risky"
            },
            {
                "idea": "Test idea 2",
                "critique": "Could be better",
                "advocacy": "Strong",
                "skepticism": "Complex"
            }
        ]
        
        results, token_usage = improve_ideas_batch(ideas, "Test context", 0.9)
        
        # Should return mock data
        assert len(results) == 2
        for i, result in enumerate(results):
            assert result["idea_index"] == i
            assert "improved_idea" in result
            assert "Mock improved version" in result["improved_idea"]
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_improve_ideas_batch_no_client(self):
        """Test batch improvement when client is None."""
        with patch('madspark.agents.idea_generator.idea_generator_client', None):
            ideas = [{
                "idea": "Test",
                "critique": "Test",
                "advocacy": "Test",
                "skepticism": "Test"
            }]
            
            # Should return mock results when client is None
            results, token_usage = improve_ideas_batch(ideas, "Test", 0.9)
            assert len(results) == 1
            assert "improved_idea" in results[0]
    
    def test_improve_ideas_batch_validates_input(self):
        """Test that input validation works correctly."""
        # Test with non-dict item
        with pytest.raises(ValueError, match="must be a dictionary"):
            improve_ideas_batch(["not a dict"], "Test", 0.9)
        
        # Test with missing keys
        with pytest.raises(ValueError, match="must have 'idea', 'critique', 'advocacy', and 'skepticism' keys"):
            improve_ideas_batch([{"idea": "Test"}], "Test", 0.9)
        
        # Test with partial keys
        with pytest.raises(ValueError, match="must have 'idea', 'critique', 'advocacy', and 'skepticism' keys"):
            improve_ideas_batch([{
                "idea": "Test",
                "critique": "Test",
                "advocacy": "Test"
                # Missing skepticism
            }], "Test", 0.9)
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_improve_ideas_batch_preserves_order(self, mock_model_name, mock_client):
        """Test that batch improvement preserves idea order."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Return in different order to test ordering
        mock_response = Mock()
        mock_response.text = '''[
            {
                "idea_index": 2,
                "improved_idea": "Improved C",
                "key_improvements": ["C improvement"]
            },
            {
                "idea_index": 0,
                "improved_idea": "Improved A",
                "key_improvements": ["A improvement"]
            },
            {
                "idea_index": 1,
                "improved_idea": "Improved B",
                "key_improvements": ["B improvement"]
            }
        ]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [
            {"idea": "A", "critique": "C", "advocacy": "A", "skepticism": "S"},
            {"idea": "B", "critique": "C", "advocacy": "A", "skepticism": "S"},
            {"idea": "C", "critique": "C", "advocacy": "A", "skepticism": "S"}
        ]
        
        results, token_usage = improve_ideas_batch(ideas, "Test", 0.9)
        
        # Results should be sorted by idea_index
        assert results[0]["idea_index"] == 0
        assert results[0]["improved_idea"] == "Improved A"
        assert results[1]["idea_index"] == 1
        assert results[1]["improved_idea"] == "Improved B"
        assert results[2]["idea_index"] == 2
        assert results[2]["improved_idea"] == "Improved C"