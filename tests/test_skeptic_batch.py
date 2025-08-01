"""Tests for batch skeptic functionality."""
import pytest
from unittest.mock import Mock, patch

try:
    from madspark.agents.skeptic import criticize_ideas_batch
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.agents.skeptic import criticize_ideas_batch


class TestSkepticBatch:
    """Test batch skeptic/devil's advocate functionality."""
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    @patch('madspark.agents.skeptic.get_model_name')
    def test_criticize_ideas_batch_single(self, mock_model_name, mock_client):
        """Test batch skeptic with single idea."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "critical_flaws": ["Implementation complexity", "Resource requirements"],
            "risks_challenges": ["Technical debt accumulation", "User adoption barriers"],
            "questionable_assumptions": ["Market readiness", "Team expertise"],
            "missing_considerations": ["Regulatory compliance", "Scalability limits"]
        }]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_advocacies = [{
            "idea": "AI-powered tutoring system",
            "advocacy": "STRENGTHS:\n• Innovative\n• High impact\n\nOPPORTUNITIES:\n• Market leader"
        }]
        
        results, token_usage = criticize_ideas_batch(ideas_with_advocacies, "Education technology", 0.5)
        
        assert len(results) == 1
        assert isinstance(token_usage, int)
        assert results[0]["idea_index"] == 0
        assert len(results[0]["critical_flaws"]) == 2
        assert len(results[0]["risks_challenges"]) == 2
        assert len(results[0]["questionable_assumptions"]) == 2
        assert len(results[0]["missing_considerations"]) == 2
        assert "formatted" in results[0]
        
        # Verify single API call
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    @patch('madspark.agents.skeptic.get_model_name')
    def test_criticize_ideas_batch_multiple(self, mock_model_name, mock_client):
        """Test batch skeptic with multiple ideas."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        # Mock response for 3 ideas
        mock_response = Mock()
        mock_response.text = '''[
            {
                "idea_index": 0,
                "critical_flaws": ["Flaw A1", "Flaw A2"],
                "risks_challenges": ["Risk A1", "Risk A2"],
                "questionable_assumptions": ["Assumption A1", "Assumption A2"],
                "missing_considerations": ["Missing A1", "Missing A2"]
            },
            {
                "idea_index": 1,
                "critical_flaws": ["Flaw B1", "Flaw B2"],
                "risks_challenges": ["Risk B1", "Risk B2"],
                "questionable_assumptions": ["Assumption B1", "Assumption B2"],
                "missing_considerations": ["Missing B1", "Missing B2"]
            },
            {
                "idea_index": 2,
                "critical_flaws": ["Flaw C1", "Flaw C2"],
                "risks_challenges": ["Risk C1", "Risk C2"],
                "questionable_assumptions": ["Assumption C1", "Assumption C2"],
                "missing_considerations": ["Missing C1", "Missing C2"]
            }
        ]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas_with_advocacies = [
            {"idea": "AI tutoring", "advocacy": "Strong benefits"},
            {"idea": "VR classroom", "advocacy": "Innovative approach"},
            {"idea": "Auto grading", "advocacy": "Efficiency gains"}
        ]
        
        results, token_usage = criticize_ideas_batch(ideas_with_advocacies, "EdTech", 0.5)
        
        assert len(results) == 3
        assert isinstance(token_usage, int)
        for i in range(3):
            assert results[i]["idea_index"] == i
            assert "critical_flaws" in results[i]
            assert "risks_challenges" in results[i]
            assert "questionable_assumptions" in results[i]
            assert "missing_considerations" in results[i]
            assert "formatted" in results[i]
        
        # Single API call for all ideas
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    def test_criticize_ideas_batch_empty_list(self, mock_client):
        """Test batch skeptic with empty list."""
        results, token_usage = criticize_ideas_batch([], "Test context", 0.5)
        
        assert results == []
        assert token_usage == 0
        # Should not make API call
        assert mock_client.models.generate_content.call_count == 0
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    @patch('madspark.agents.skeptic.get_model_name')
    def test_criticize_ideas_batch_invalid_json(self, mock_model_name, mock_client):
        """Test handling of invalid JSON response."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [{"idea": "Test", "advocacy": "Test advocacy"}]
        
        with pytest.raises(RuntimeError, match="Batch skeptic failed.*Invalid JSON"):
            criticize_ideas_batch(ideas, "Test", 0.5)
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    @patch('madspark.agents.skeptic.get_model_name')
    def test_criticize_ideas_batch_api_error(self, mock_model_name, mock_client):
        """Test handling of API errors."""
        mock_model_name.return_value = "gemini-2.5-flash"
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        ideas = [{"idea": "Test", "advocacy": "Test advocacy"}]
        
        with pytest.raises(RuntimeError, match="Batch skeptic failed"):
            criticize_ideas_batch(ideas, "Test", 0.5)
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    @patch('madspark.agents.skeptic.skeptic_client')
    @patch('madspark.agents.skeptic.get_model_name')
    def test_criticize_ideas_batch_formatted_output(self, mock_model_name, mock_client):
        """Test that batch results include formatted text output."""
        mock_model_name.return_value = "gemini-2.5-flash"
        
        mock_response = Mock()
        mock_response.text = '''[{
            "idea_index": 0,
            "critical_flaws": ["Major flaw", "Another issue"],
            "risks_challenges": ["High risk", "Challenge"],
            "questionable_assumptions": ["Bad assumption", "Questionable"],
            "missing_considerations": ["Forgot this", "Missing that"]
        }]'''
        
        mock_client.models.generate_content.return_value = mock_response
        
        ideas = [{"idea": "Test idea", "advocacy": "Good points"}]
        results, token_usage = criticize_ideas_batch(ideas, "Test", 0.5)
        
        assert isinstance(token_usage, int)
        assert "formatted" in results[0]
        formatted = results[0]["formatted"]
        assert "CRITICAL FLAWS:" in formatted
        assert "RISKS & CHALLENGES:" in formatted
        assert "QUESTIONABLE ASSUMPTIONS:" in formatted
        assert "MISSING CONSIDERATIONS:" in formatted
        assert "• Major flaw" in formatted
        assert "• High risk" in formatted
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', False)
    def test_criticize_ideas_batch_mock_mode(self):
        """Test batch skeptic in mock mode (no API key)."""
        ideas = [
            {"idea": "Test idea 1", "advocacy": "Good"},
            {"idea": "Test idea 2", "advocacy": "Better"}
        ]
        
        results, token_usage = criticize_ideas_batch(ideas, "Test context", 0.5)
        
        # Should return mock data
        assert len(results) == 2
        assert token_usage == 0
        for i, result in enumerate(results):
            assert result["idea_index"] == i
            assert len(result["critical_flaws"]) > 0
            assert len(result["risks_challenges"]) > 0
            assert "formatted" in result
    
    @patch('madspark.agents.skeptic.GENAI_AVAILABLE', True)
    def test_criticize_ideas_batch_no_client(self):
        """Test batch skeptic when client is None."""
        with patch('madspark.agents.skeptic.skeptic_client', None):
            ideas = [{"idea": "Test", "advocacy": "Test"}]
            
            # Should return mock results when client is None
            results, token_usage = criticize_ideas_batch(ideas, "Test", 0.5)
            assert len(results) == 1
            assert token_usage == 0
            assert "critical_flaws" in results[0]
    
    def test_criticize_ideas_batch_validates_input(self):
        """Test that input validation works correctly."""
        # Test with non-dict item
        with pytest.raises(ValueError, match="must be a dictionary"):
            criticize_ideas_batch(["not a dict"], "Test", 0.5)
        
        # Test with missing keys
        with pytest.raises(ValueError, match="must have 'idea' and 'advocacy' keys"):
            criticize_ideas_batch([{"idea": "Test"}], "Test", 0.5)