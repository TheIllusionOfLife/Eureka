"""Tests for structured response schemas used by agents."""
import pytest
import json

# Import schemas (will be created next)
from madspark.agents.response_schemas import (
    IDEA_GENERATOR_SCHEMA,
    EVALUATOR_SCHEMA,
    ADVOCACY_SCHEMA,
    SKEPTICISM_SCHEMA,
    IMPROVER_SCHEMA,
    validate_response_against_schema
)


class TestResponseSchemas:
    """Test suite for agent response schemas."""
    
    def test_idea_generator_schema_structure(self):
        """Test that idea generator schema has correct structure."""
        assert IDEA_GENERATOR_SCHEMA["type"] == "ARRAY"
        assert "items" in IDEA_GENERATOR_SCHEMA
        
        item_schema = IDEA_GENERATOR_SCHEMA["items"]
        assert item_schema["type"] == "OBJECT"
        assert "properties" in item_schema
        
        props = item_schema["properties"]
        assert "idea_number" in props
        assert "title" in props
        assert "description" in props
        assert "key_features" in props
        
        # Check required fields
        assert "required" in item_schema
        assert "idea_number" in item_schema["required"]
        assert "title" in item_schema["required"]
        assert "description" in item_schema["required"]
    
    def test_evaluator_schema_structure(self):
        """Test that evaluator schema has correct structure."""
        assert EVALUATOR_SCHEMA["type"] == "OBJECT"
        assert "properties" in EVALUATOR_SCHEMA
        
        props = EVALUATOR_SCHEMA["properties"]
        assert "score" in props
        assert props["score"]["type"] == "NUMBER"
        assert "critique" in props
        assert "strengths" in props
        assert "weaknesses" in props
        
        # Check required fields
        assert "score" in EVALUATOR_SCHEMA["required"]
        assert "critique" in EVALUATOR_SCHEMA["required"]
    
    def test_advocacy_schema_structure(self):
        """Test that advocacy schema has correct structure."""
        assert ADVOCACY_SCHEMA["type"] == "OBJECT"
        assert "properties" in ADVOCACY_SCHEMA
        
        props = ADVOCACY_SCHEMA["properties"]
        assert "strengths" in props
        assert "opportunities" in props
        assert "addressing_concerns" in props
        
        # Check array structures
        assert props["strengths"]["type"] == "ARRAY"
        assert props["opportunities"]["type"] == "ARRAY"
        assert props["addressing_concerns"]["type"] == "ARRAY"
    
    def test_skepticism_schema_structure(self):
        """Test that skepticism schema has correct structure."""
        assert SKEPTICISM_SCHEMA["type"] == "OBJECT"
        assert "properties" in SKEPTICISM_SCHEMA
        
        props = SKEPTICISM_SCHEMA["properties"]
        assert "critical_flaws" in props
        assert "risks_and_challenges" in props
        assert "questionable_assumptions" in props
        assert "missing_considerations" in props
    
    def test_improver_schema_structure(self):
        """Test that improver schema has correct structure."""
        assert IMPROVER_SCHEMA["type"] == "OBJECT"
        assert "properties" in IMPROVER_SCHEMA
        
        props = IMPROVER_SCHEMA["properties"]
        assert "improved_title" in props
        assert "improved_description" in props
        assert "key_improvements" in props
        assert "implementation_steps" in props


class TestSchemaValidation:
    """Test schema validation functionality."""
    
    def test_validate_idea_generator_response(self):
        """Test validation of idea generator responses."""
        valid_response = [
            {
                "idea_number": 1,
                "title": "AI-Powered Learning Assistant",
                "description": "A personalized learning companion that adapts to individual learning styles",
                "key_features": [
                    "Adaptive learning algorithms",
                    "Multi-modal content delivery",
                    "Progress tracking"
                ],
                "category": "Education Technology"
            },
            {
                "idea_number": 2,
                "title": "Smart Garden System",
                "description": "Automated urban gardening solution for small spaces",
                "key_features": [
                    "IoT sensors",
                    "Automated watering",
                    "Mobile app control"
                ]
            }
        ]
        
        assert validate_response_against_schema(valid_response, IDEA_GENERATOR_SCHEMA) is True
        
        # Test invalid response (missing required field)
        invalid_response = [
            {
                "idea_number": 1,
                "title": "Missing Description"
                # Missing required 'description' field
            }
        ]
        
        assert validate_response_against_schema(invalid_response, IDEA_GENERATOR_SCHEMA) is False
    
    def test_validate_evaluator_response(self):
        """Test validation of evaluator responses."""
        valid_response = {
            "score": 8.5,
            "critique": "Strong concept with good market potential",
            "strengths": [
                "Innovative approach",
                "Clear value proposition"
            ],
            "weaknesses": [
                "High initial development cost",
                "Competitive market"
            ]
        }
        
        assert validate_response_against_schema(valid_response, EVALUATOR_SCHEMA) is True
        
        # Test invalid response (wrong type for score)
        invalid_response = {
            "score": "eight point five",  # Should be number
            "critique": "Good idea"
        }
        
        assert validate_response_against_schema(invalid_response, EVALUATOR_SCHEMA) is False
    
    def test_validate_advocacy_response(self):
        """Test validation of advocacy responses."""
        valid_response = {
            "strengths": [
                {
                    "title": "Market Demand",
                    "description": "Growing need for this solution in the market"
                },
                {
                    "title": "Technical Feasibility",
                    "description": "Can be built with existing technology"
                }
            ],
            "opportunities": [
                {
                    "title": "Partnership Potential",
                    "description": "Many companies would be interested in collaboration"
                }
            ],
            "addressing_concerns": [
                {
                    "concern": "Development time seems long",
                    "response": "Using agile methodology can accelerate delivery"
                }
            ]
        }
        
        assert validate_response_against_schema(valid_response, ADVOCACY_SCHEMA) is True


class TestStructuredOutputIntegration:
    """Integration tests for structured output with agents."""
    
    @pytest.mark.integration
    def test_idea_generator_structured_output(self):
        """Test that idea generator produces valid structured output."""
        from madspark.agents.idea_generator import generate_ideas
        
        # Skip if no API key (CI environment)
        import os
        if not os.getenv('GOOGLE_API_KEY') or os.getenv('MADSPARK_MODE') == 'mock':
            pytest.skip("Requires real API key for integration test")
        
        # Generate ideas with structured output
        response = generate_ideas(
            topic="sustainable urban farming",
            context="limited space, low budget",
            temperature=0.7,
            use_structured_output=True
        )
        
        # Response should be valid JSON
        ideas = json.loads(response)
        
        # Validate against schema
        assert validate_response_against_schema(ideas, IDEA_GENERATOR_SCHEMA)
        
        # Check content quality
        assert len(ideas) >= 3
        for idea in ideas:
            assert len(idea["title"]) > 0
            assert len(idea["description"]) > 20
            assert len(idea["key_features"]) >= 2