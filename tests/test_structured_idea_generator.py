"""Test structured idea generator implementation."""
import json
import pytest
from unittest.mock import Mock, patch

from madspark.agents.structured_idea_generator import (
    improve_idea_structured,
    generate_ideas_structured,
    _IMPROVEMENT_RESPONSE_GENAI_SCHEMA
)
from madspark.schemas.generation import ImprovementResponse


class TestStructuredIdeaGeneration:
    """Test structured idea generation functions."""
    
    def test_improvement_response_schema(self):
        """Test that response schema is correctly defined (Pydantic-generated)."""
        # Verify schema is generated from Pydantic model
        assert _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["type"] == "OBJECT"
        assert "improved_title" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["properties"]
        assert "improved_description" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["properties"]
        assert "key_improvements" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["properties"]

        # Check required fields from Pydantic model
        assert "improved_title" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["required"]
        assert "improved_description" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["required"]
        assert "key_improvements" in _IMPROVEMENT_RESPONSE_GENAI_SCHEMA["required"]

        # Verify Pydantic model structure via model_fields
        assert 'improved_title' in ImprovementResponse.model_fields
        assert 'improved_description' in ImprovementResponse.model_fields
        assert 'key_improvements' in ImprovementResponse.model_fields
    
    @patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', True)
    def test_improve_idea_structured_with_json_response(self):
        """Test improvement with JSON structured response."""
        mock_client = Mock()
        mock_response = Mock()
        
        # Mock a structured JSON response using new Pydantic schema fields
        structured_response = {
            "improved_title": "Blockchain-Powered Renewable Energy Marketplace",
            "improved_description": "A decentralized marketplace connecting renewable energy producers with consumers using blockchain for transparent tracking and automated transactions",
            "key_improvements": [
                "Added blockchain for transparency",
                "Enhanced scalability",
                "Improved user experience"
            ]
        }
        mock_response.text = json.dumps(structured_response)
        mock_client.models.generate_content.return_value = mock_response

        result = improve_idea_structured(
            original_idea="Solar panel sharing",
            critique="Needs better tracking",
            advocacy_points="Great community aspect",
            skeptic_points="Security concerns",
            topic="renewable energy solutions",
            context="renewable energy",
            genai_client=mock_client
        )

        # Should concatenate title and description (backward compatibility)
        assert "Blockchain-Powered Renewable Energy Marketplace" in result
        assert "decentralized marketplace" in result
        assert "improved version" not in result.lower()
        assert "enhanced concept" not in result.lower()
    
    @patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', True)
    def test_improve_idea_structured_fallback_to_text(self):
        """Test fallback when response is not JSON."""
        mock_client = Mock()
        mock_response = Mock()
        
        # Mock a plain text response (fallback case)
        mock_response.text = "A revolutionary solar panel sharing network"
        mock_client.models.generate_content.return_value = mock_response
        
        result = improve_idea_structured(
            original_idea="Solar panels",
            critique="Needs work",
            advocacy_points="Good start",
            skeptic_points="Some issues",
            topic="energy solutions",
            context="energy",
            genai_client=mock_client
        )
        
        # Should return the text as-is
        assert result == "A revolutionary solar panel sharing network"
    
    def test_improve_idea_structured_validation(self):
        """Test input validation."""
        with pytest.raises(Exception):  # ValidationError
            improve_idea_structured(
                original_idea="",  # Empty
                critique="Good",
                advocacy_points="Nice",
                skeptic_points="Issues",
                topic="test topic",
                context="test"
            )
    
    @patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', False)
    def test_improve_idea_structured_mock_mode(self):
        """Test mock mode response."""
        result = improve_idea_structured(
            original_idea="Test idea",
            critique="Needs improvement",
            advocacy_points="Has potential",
            skeptic_points="Some concerns",
            topic="innovation ideas",
            context="innovation"
        )
        
        # Should return mock response
        assert "revolutionary innovation solution" in result
        assert len(result) > 0
    
    @patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', True)
    def test_structured_config_includes_mime_type(self):
        """Test that config includes JSON mime type."""
        mock_client = Mock()
        mock_types = Mock()
        
        with patch('madspark.agents.structured_idea_generator.types', mock_types):
            # Capture the config passed to GenerateContentConfig
            config_capture = {}
            
            def capture_config(**kwargs):
                config_capture.update(kwargs)
                return Mock()
            
            mock_types.GenerateContentConfig.side_effect = capture_config
            
            # Make the call
            mock_response = Mock()
            mock_response.text = '{"improved_idea": "Test"}'
            mock_client.models.generate_content.return_value = mock_response
            
            improve_idea_structured(
                original_idea="Test",
                critique="Critique",
                advocacy_points="Advocacy",
                skeptic_points="Skeptic",
                topic="Test topic",
                context="Theme",
                genai_client=mock_client
            )
            
            # Verify JSON mime type was set
            assert config_capture.get("response_mime_type") == "application/json"
            assert "response_schema" in config_capture
    
    @patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_structured(self):
        """Test structured idea generation."""
        mock_client = Mock()
        mock_response = Mock()
        
        # Mock response with clean numbered list
        mock_response.text = """1. Solar-powered vertical farms
2. Community energy storage hubs
3. Peer-to-peer renewable energy trading
4. Smart grid optimization AI
5. Biodegradable solar panels"""
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = generate_ideas_structured(
            topic="renewable energy",
            context="urban environments",
            genai_client=mock_client
        )
        
        # Should return clean numbered list
        assert "1. Solar-powered vertical farms" in result
        assert "Here are some ideas" not in result
        assert "enhanced" not in result.lower()
    
    def test_prompt_excludes_meta_commentary_instructions(self):
        """Test that prompts explicitly exclude meta-commentary."""
        # Test the prompt building
        test_prompt = """Theme: test

Original Idea: original

Professional Evaluation: eval

Key Strengths: strengths

Critical Concerns: concerns

Task: Generate an improved version that:
1. Addresses ALL evaluation criteria
2. Maintains identified strengths
3. Provides solutions for each concern
4. Remains bold and creative

Write ONLY the improved idea. No introductions, no meta-commentary."""
        
        assert "Write ONLY the improved idea" in test_prompt
        assert "No introductions" in test_prompt
        assert "no meta-commentary" in test_prompt