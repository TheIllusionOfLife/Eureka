import json
import pytest
import importlib.util
import sys
import os

# Import the module directly by file path to avoid triggering package initialization
# and recursive dependencies (like google.genai).
file_path = os.path.abspath("src/madspark/utils/json_parsers.py")
spec = importlib.util.spec_from_file_location("json_parsers", file_path)
json_parsers = importlib.util.module_from_spec(spec)
sys.modules["json_parsers"] = json_parsers
spec.loader.exec_module(json_parsers)

parse_idea_generator_response = json_parsers.parse_idea_generator_response

class TestParseIdeaGeneratorResponse:
    """Tests for parse_idea_generator_response function."""

    def test_parse_structured_format_with_ideas_key(self):
        """Test parsing JSON dict with 'ideas' key."""
        json_input = json.dumps({
            "ideas": [
                {"idea_number": 1, "title": "Idea 1", "description": "Desc 1"},
                {"idea_number": 2, "title": "Idea 2", "description": "Desc 2"}
            ]
        })
        result = parse_idea_generator_response(json_input)
        assert len(result) == 2
        assert result[0] == "1. Idea 1: Desc 1"
        assert result[1] == "2. Idea 2: Desc 2"

    def test_parse_list_format(self):
        """Test parsing JSON list of ideas."""
        json_input = json.dumps([
            {"idea_number": 1, "title": "Idea 1", "description": "Desc 1"},
            {"idea_number": 2, "title": "Idea 2", "description": "Desc 2"}
        ])
        result = parse_idea_generator_response(json_input)
        assert len(result) == 2
        assert result[0] == "1. Idea 1: Desc 1"
        assert result[1] == "2. Idea 2: Desc 2"

    def test_parse_single_object(self):
        """Test parsing single JSON object."""
        json_input = json.dumps({
            "idea_number": 1, "title": "Idea 1", "description": "Desc 1"
        })
        result = parse_idea_generator_response(json_input)
        assert len(result) == 1
        assert result[0] == "1. Idea 1: Desc 1"

    def test_parse_with_key_features(self):
        """Test parsing ideas with key features."""
        json_input = json.dumps({
            "ideas": [
                {
                    "idea_number": 1,
                    "title": "Idea 1",
                    "description": "Desc 1",
                    "key_features": ["Feature A", "Feature B"]
                }
            ]
        })
        result = parse_idea_generator_response(json_input)
        assert len(result) == 1
        assert "Key features: Feature A, Feature B" in result[0]

    def test_parse_with_key_features_as_string(self):
        """Test parsing ideas where key_features is a string (legacy/malformed)."""
        json_input = json.dumps({
            "ideas": [
                {
                    "title": "Idea 1",
                    "key_features": "Feature A, Feature B"
                }
            ]
        })
        result = parse_idea_generator_response(json_input)
        assert len(result) == 1
        assert "Key features: Feature A, Feature B" in result[0]
        # Should NOT be F, e, a, t...
        assert "Key features: F, e, a, t" not in result[0]

    def test_parse_missing_fields(self):
        """Test parsing with missing optional fields."""
        json_input = json.dumps({
            "ideas": [
                {"title": "Idea 1"} # Missing description and idea_number
            ]
        })
        result = parse_idea_generator_response(json_input)
        assert len(result) == 1
        # Expecting "Title: Description" format when idea_number is missing
        assert result[0] == "Idea 1: No description provided"

    def test_parse_malformed_json(self):
        """Test fallback to text parsing with malformed JSON."""
        text_input = "Idea 1: Desc 1\nIdea 2: Desc 2"
        # Not a valid JSON
        result = parse_idea_generator_response(text_input)
        assert len(result) == 2
        assert result[0] == "Idea 1: Desc 1"
        assert result[1] == "Idea 2: Desc 2"

    def test_parse_invalid_structure_list_of_strings(self):
        """Test handling of list of strings (should handle gracefully)."""
        json_input = json.dumps(["Just a string", "Another string"])

        result = parse_idea_generator_response(json_input)

        # Verify it returns the strings as is, thanks to explicit handling
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == "Just a string"
        assert result[1] == "Another string"

    def test_parse_invalid_structure_random_dict(self):
        """Test handling of random dict without 'ideas' key."""
        # Treated as single object.
        json_input = json.dumps({"foo": "bar", "baz": 123})
        # It will try idea_obj.get('title') -> 'Untitled'
        # idea_obj.get('description') -> 'No description provided'
        result = parse_idea_generator_response(json_input)
        assert len(result) == 1
        assert "Untitled: No description provided" in result[0]
