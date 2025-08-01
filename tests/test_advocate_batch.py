"""Tests for batch advocate functionality."""
import pytest
from unittest.mock import Mock, patch

try:
    from madspark.agents.advocate import advocate_ideas_batch
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.agents.advocate import advocate_ideas_batch


class TestAdvocateBatch:
    """Test batch advocate functionality."""
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.get_model_name')
    def test_advocate_ideas_batch_single(self, mock_model_name, mock_client):
        """Test batch advocate with single idea."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "strengths": ["Strong technical foundation", "Addresses real need"],
            "opportunities": ["Could revolutionize education", "Scalable solution"],
            "addressing_concerns": ["Implementation timeline manageable", "Budget concerns can be mitigated"]
        }]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_evaluations = [{
            "idea": "AI-powered personalized tutoring system",
            "evaluation": "Score: 8/10. Strong concept with good feasibility."
        }]
        
        results, token_usage = advocate_ideas_batch(ideas_with_evaluations, "Education technology", 0.5)
        
        assert len(results) == 1
        assert results[0]["idea_index"] == 0
        assert len(results[0]["strengths"]) == 2
        assert len(results[0]["opportunities"]) == 2
        assert len(results[0]["addressing_concerns"]) == 2
        assert isinstance(token_usage, int)  # Token usage should be an integer
        
        # Verify single API call
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.get_model_name')
    def test_advocate_ideas_batch_multiple(self, mock_model_name, mock_client):
        """Test batch advocate with multiple ideas."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response for 3 ideas
        mock_response = Mock()
        mock_response.text = '''[
            {
                "idea_index": 0,
                "strengths": ["Innovation in AI", "User-friendly"],
                "opportunities": ["Market leader potential", "High impact"],
                "addressing_concerns": ["Timeline realistic", "Costs justified"]
            },
            {
                "idea_index": 1,
                "strengths": ["Immersive experience", "Cutting-edge tech"],
                "opportunities": ["First to market", "Partnership opportunities"],
                "addressing_concerns": ["Technical challenges manageable", "ROI positive"]
            },
            {
                "idea_index": 2,
                "strengths": ["Efficiency gains", "Proven approach"],
                "opportunities": ["Quick deployment", "Cost savings"],
                "addressing_concerns": ["Change management handled", "Security addressed"]
            }
        ]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_evaluations = [
            {"idea": "AI tutoring", "evaluation": "Score: 8/10"},
            {"idea": "VR classroom", "evaluation": "Score: 7/10"},
            {"idea": "Auto grading", "evaluation": "Score: 9/10"}
        ]
        
        results, token_usage = advocate_ideas_batch(ideas_with_evaluations, "EdTech", 0.5)
        
        assert len(results) == 3
        assert isinstance(token_usage, int)
        for i in range(3):
            assert results[i]["idea_index"] == i
            assert "strengths" in results[i]
            assert "opportunities" in results[i]
            assert "addressing_concerns" in results[i]
        
        # Single API call for all ideas
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    def test_advocate_ideas_batch_empty_list(self, mock_client):
        """Test batch advocate with empty list."""
        results, token_usage = advocate_ideas_batch([], "Test context", 0.5)
        
        assert results == []
        assert token_usage == 0
        # Should not make API call
        assert mock_client.models.generate_content.call_count == 0
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.get_model_name')
    def test_advocate_ideas_batch_invalid_json(self, mock_model_name, mock_client):
        """Test handling of invalid JSON response."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [{"idea": "Test", "evaluation": "Test eval"}]
        
        from madspark.utils.batch_exceptions import BatchAPIError
        with pytest.raises(BatchAPIError, match="Batch advocate failed.*Invalid JSON"):
            advocate_ideas_batch(ideas, "Test", 0.5)
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.get_model_name')
    def test_advocate_ideas_batch_api_error(self, mock_model_name, mock_client):
        """Test handling of API errors."""
        mock_model_name.return_value = "gemini-2.5-flash"
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        ideas = [{"idea": "Test", "evaluation": "Test eval"}]
        
        from madspark.utils.batch_exceptions import BatchAPIError
        with pytest.raises(BatchAPIError, match="Batch advocate failed"):
            advocate_ideas_batch(ideas, "Test", 0.5)
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.get_model_name')
    def test_advocate_ideas_batch_formatted_output(self, mock_model_name, mock_client):
        """Test that batch results include formatted text output."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "strengths": ["Innovation", "Scalability"],
            "opportunities": ["Market leadership", "High ROI"],
            "addressing_concerns": ["Timeline managed", "Budget feasible"]
        }]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [{"idea": "Test idea", "evaluation": "Good"}]
        results, token_usage = advocate_ideas_batch(ideas, "Test", 0.5)
        
        assert isinstance(token_usage, int)
        assert "formatted" in results[0]
        formatted = results[0]["formatted"]
        assert "STRENGTHS:" in formatted
        assert "OPPORTUNITIES:" in formatted
        assert "ADDRESSING CONCERNS:" in formatted
        assert "• Innovation" in formatted
        assert "• Market leadership" in formatted
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', False)
    def test_advocate_ideas_batch_mock_mode(self):
        """Test batch advocate in mock mode (no API key)."""
        ideas = [
            {"idea": "Test idea 1", "evaluation": "Good"},
            {"idea": "Test idea 2", "evaluation": "Better"}
        ]
        
        results, token_usage = advocate_ideas_batch(ideas, "Test context", 0.5)
        
        # Should return mock data
        assert len(results) == 2
        for i, result in enumerate(results):
            assert result["idea_index"] == i
            assert len(result["strengths"]) > 0
            assert len(result["opportunities"]) > 0
            assert "formatted" in result
    
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    def test_advocate_ideas_batch_no_client(self):
        """Test batch advocate when client is None."""
        with patch('madspark.agents.advocate.advocate_client', None):
            ideas = [{"idea": "Test", "evaluation": "Test"}]
            
            # Should return mock results when client is None
            results, token_usage = advocate_ideas_batch(ideas, "Test", 0.5)
            assert len(results) == 1
            assert token_usage == 0  # Mock mode
            assert "strengths" in results[0]