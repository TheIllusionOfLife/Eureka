"""Test for fixing batch advocate JSON parsing with Japanese content."""
import pytest
from unittest.mock import Mock, patch
import json
import sys
import os
import logging

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.agents.advocate import advocate_ideas_batch
from madspark.utils.utils import parse_batch_json_with_fallback

# Set up logger
logger = logging.getLogger(__name__)


class TestBatchAdvocateJSONFix:
    """Test suite for batch advocate JSON parsing fix."""
    
    def test_parse_batch_json_with_fallback_handles_japanese(self):
        """Test that parse_batch_json_with_fallback can handle Japanese JSON responses."""
        # Simulated problematic Japanese response (missing comma)
        problematic_json = '''[
{
    "idea_index": 0,
    "strengths": ["省スペース設計", "低コスト実装"]
    "opportunities": ["市場拡大", "技術革新"],
    "addressing_concerns": ["段階的実装", "コスト最適化"]
}
]'''
        
        # This would fail with json.loads
        with pytest.raises(json.JSONDecodeError):
            json.loads(problematic_json)
            
        # But parse_batch_json_with_fallback should handle it
        result = parse_batch_json_with_fallback(problematic_json, expected_count=1)
        assert len(result) == 1
        assert result[0]["idea_index"] == 0
        assert len(result[0]["strengths"]) == 2
        
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    def test_advocate_batch_with_fallback_parsing(self, mock_advocate_client):
        """Test that advocate batch can use fallback parsing."""
        # Mock response with problematic JSON (missing comma after strengths)
        mock_response = Mock()
        mock_response.text = '''[
{
    "idea_index": 0,
    "strengths": ["強み1", "強み2"]
    "opportunities": ["機会1", "機会2"],
    "addressing_concerns": ["対策1", "対策2"]
}
]'''
        mock_response.usage_metadata = Mock(total_token_count=100)
        
        mock_advocate_client.models.generate_content.return_value = mock_response
        
        # Test batch advocacy with fallback parsing
        ideas_with_evaluations = [
            {"idea": "垂直農法システム", "evaluation": "良い評価"}
        ]
        
        # After the fix, this should work with fallback parsing
        result, token_count = advocate_ideas_batch(
            ideas_with_evaluations=ideas_with_evaluations,
            context="都市農業",
            temperature=0.5
        )
        
        # Verify results
        assert len(result) == 1
        assert result[0]["idea_index"] == 0
        assert len(result[0]["strengths"]) == 2
        assert len(result[0]["opportunities"]) == 2
        assert len(result[0]["addressing_concerns"]) == 2
        assert "formatted" in result[0]  # Should have formatted text
        assert token_count == 100
        
    @patch('madspark.agents.advocate.advocate_client')
    @patch('madspark.agents.advocate.GENAI_AVAILABLE', True)
    def test_advocate_batch_normal_json_still_works(self, mock_advocate_client):
        """Test that normal JSON responses still work correctly."""
        # Mock response with valid JSON
        mock_response = Mock()
        mock_response.text = json.dumps([
            {
                "idea_index": 0,
                "strengths": ["Strength 1", "Strength 2"],
                "opportunities": ["Opportunity 1"],
                "addressing_concerns": ["Mitigation 1"]
            }
        ])
        mock_response.usage_metadata = Mock(total_token_count=50)
        
        mock_advocate_client.models.generate_content.return_value = mock_response
        
        # Test batch advocacy
        result, token_count = advocate_ideas_batch(
            ideas_with_evaluations=[{"idea": "Test idea", "evaluation": "Good"}],
            context="Test context",
            temperature=0.5
        )
        
        # Verify results
        assert len(result) == 1
        assert result[0]["idea_index"] == 0
        assert len(result[0]["strengths"]) == 2
        assert token_count == 50