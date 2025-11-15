"""
Tests for generation Pydantic schemas (idea generation and improvement).

Following TDD approach - these tests are written BEFORE implementation.
Tests cover validation, constraints, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError


class TestIdeaItem:
    """Tests for IdeaItem model (single generated idea)."""

    def test_idea_item_valid_minimal(self):
        """Valid IdeaItem with only required fields."""
        from madspark.schemas.generation import IdeaItem

        idea = IdeaItem(
            idea_number=1,
            title="AI-powered fitness coach",
            description="An intelligent personal trainer app that adapts to user progress"
        )

        assert idea.idea_number == 1
        assert idea.title == "AI-powered fitness coach"
        assert len(idea.description) > 10
        assert idea.key_features is None
        assert idea.category is None

    def test_idea_item_valid_full(self):
        """Valid IdeaItem with all optional fields."""
        from madspark.schemas.generation import IdeaItem

        idea = IdeaItem(
            idea_number=2,
            title="Smart home automation",
            description="Centralized control system for all home devices with AI optimization",
            key_features=["Voice control", "Energy optimization", "Security monitoring"],
            category="Smart Home"
        )

        assert idea.idea_number == 2
        assert len(idea.key_features) == 3
        assert idea.category == "Smart Home"

    def test_idea_item_number_validation_negative(self):
        """Idea number must be >= 1."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=0,
                title="Test",
                description="Test description here"
            )
        assert "greater than or equal to 1" in str(exc_info.value).lower()

    def test_idea_item_title_empty(self):
        """Title cannot be empty."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=1,
                title="",
                description="Valid description here"
            )
        assert "title" in str(exc_info.value).lower()

    def test_idea_item_title_too_long(self):
        """Title cannot exceed 200 characters."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=1,
                title="A" * 201,
                description="Valid description here"
            )
        assert "200" in str(exc_info.value)

    def test_idea_item_description_too_short(self):
        """Description must be at least 10 characters."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=1,
                title="Valid title",
                description="Short"
            )
        assert "10" in str(exc_info.value)

    def test_idea_item_description_too_long(self):
        """Description cannot exceed 2000 characters."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=1,
                title="Valid title",
                description="A" * 2001
            )
        assert "2000" in str(exc_info.value)

    def test_idea_item_category_too_long(self):
        """Category cannot exceed 100 characters."""
        from madspark.schemas.generation import IdeaItem

        with pytest.raises(ValidationError) as exc_info:
            IdeaItem(
                idea_number=1,
                title="Valid title",
                description="Valid description here",
                category="A" * 101
            )
        assert "100" in str(exc_info.value)

    def test_idea_item_unicode_support(self):
        """IdeaItem supports unicode characters."""
        from madspark.schemas.generation import IdeaItem

        idea = IdeaItem(
            idea_number=1,
            title="日本語タイトル",
            description="これは日本語の説明文です。十分な長さが必要です。",
            category="テクノロジー"
        )

        assert "日本語" in idea.title
        assert "説明文" in idea.description

    def test_idea_item_serialization(self):
        """IdeaItem can be serialized to dict."""
        from madspark.schemas.generation import IdeaItem

        idea = IdeaItem(
            idea_number=1,
            title="Test idea",
            description="Test description here with enough length"
        )

        data = idea.model_dump()
        assert isinstance(data, dict)
        assert data["idea_number"] == 1
        assert data["title"] == "Test idea"
        assert data["key_features"] is None


class TestGeneratedIdeas:
    """Tests for GeneratedIdeas array wrapper (RootModel)."""

    def test_generated_ideas_array(self):
        """GeneratedIdeas wraps array of IdeaItem."""
        from madspark.schemas.generation import IdeaItem, GeneratedIdeas

        ideas = GeneratedIdeas([
            IdeaItem(idea_number=1, title="Idea 1", description="Description one here"),
            IdeaItem(idea_number=2, title="Idea 2", description="Description two here")
        ])

        assert len(ideas) == 2
        assert ideas[0].idea_number == 1
        assert ideas[1].title == "Idea 2"

    def test_generated_ideas_iteration(self):
        """GeneratedIdeas supports iteration."""
        from madspark.schemas.generation import IdeaItem, GeneratedIdeas

        ideas = GeneratedIdeas([
            IdeaItem(idea_number=i, title=f"Idea {i}", description=f"Description {i} here")
            for i in range(1, 4)
        ])

        count = 0
        for idea in ideas:
            count += 1
            assert idea.idea_number == count

        assert count == 3

    def test_generated_ideas_empty_array(self):
        """GeneratedIdeas can be empty array."""
        from madspark.schemas.generation import GeneratedIdeas

        ideas = GeneratedIdeas([])
        assert len(ideas) == 0

    def test_generated_ideas_single_item(self):
        """GeneratedIdeas can contain single item."""
        from madspark.schemas.generation import IdeaItem, GeneratedIdeas

        ideas = GeneratedIdeas([
            IdeaItem(idea_number=1, title="Only idea", description="Only description here")
        ])

        assert len(ideas) == 1
        assert ideas[0].title == "Only idea"

    def test_generated_ideas_serialization(self):
        """GeneratedIdeas can be serialized to list of dicts."""
        from madspark.schemas.generation import IdeaItem, GeneratedIdeas

        ideas = GeneratedIdeas([
            IdeaItem(idea_number=1, title="Idea 1", description="Description one here"),
            IdeaItem(idea_number=2, title="Idea 2", description="Description two here")
        ])

        data = ideas.model_dump()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["idea_number"] == 1


class TestImprovementResponse:
    """Tests for ImprovementResponse model (improved idea output)."""

    def test_improvement_response_valid_minimal(self):
        """Valid ImprovementResponse with only required fields."""
        from madspark.schemas.generation import ImprovementResponse

        improved = ImprovementResponse(
            improved_title="Enhanced AI fitness coach",
            improved_description="An advanced intelligent personal trainer app with real-time feedback",
            key_improvements=["Added real-time feedback", "Enhanced AI algorithms"]
        )

        assert improved.improved_title == "Enhanced AI fitness coach"
        assert len(improved.improved_description) > 10
        assert len(improved.key_improvements) == 2
        assert improved.implementation_steps is None
        assert improved.differentiators is None

    def test_improvement_response_valid_full(self):
        """Valid ImprovementResponse with all optional fields."""
        from madspark.schemas.generation import ImprovementResponse

        improved = ImprovementResponse(
            improved_title="Enhanced AI fitness coach",
            improved_description="An advanced intelligent personal trainer app with comprehensive features",
            key_improvements=["Real-time feedback", "AI algorithms", "Social features"],
            implementation_steps=["Design UI", "Implement backend", "Test with users"],
            differentiators=["Patent-pending AI", "Exclusive partnerships"]
        )

        assert len(improved.implementation_steps) == 3
        assert len(improved.differentiators) == 2

    def test_improvement_response_title_empty(self):
        """Improved title cannot be empty."""
        from madspark.schemas.generation import ImprovementResponse

        with pytest.raises(ValidationError) as exc_info:
            ImprovementResponse(
                improved_title="",
                improved_description="Valid description here",
                key_improvements=["Improvement 1"]
            )
        assert "improved_title" in str(exc_info.value).lower()

    def test_improvement_response_title_too_long(self):
        """Improved title cannot exceed 200 characters."""
        from madspark.schemas.generation import ImprovementResponse

        with pytest.raises(ValidationError) as exc_info:
            ImprovementResponse(
                improved_title="A" * 201,
                improved_description="Valid description here",
                key_improvements=["Improvement 1"]
            )
        assert "200" in str(exc_info.value)

    def test_improvement_response_description_too_short(self):
        """Improved description must be at least 10 characters."""
        from madspark.schemas.generation import ImprovementResponse

        with pytest.raises(ValidationError) as exc_info:
            ImprovementResponse(
                improved_title="Valid title",
                improved_description="Short",
                key_improvements=["Improvement 1"]
            )
        assert "10" in str(exc_info.value)

    def test_improvement_response_description_too_long(self):
        """Improved description cannot exceed 5000 characters."""
        from madspark.schemas.generation import ImprovementResponse

        with pytest.raises(ValidationError) as exc_info:
            ImprovementResponse(
                improved_title="Valid title",
                improved_description="A" * 5001,
                key_improvements=["Improvement 1"]
            )
        assert "5000" in str(exc_info.value)

    def test_improvement_response_empty_improvements_array(self):
        """Key improvements array cannot be empty."""
        from madspark.schemas.generation import ImprovementResponse

        with pytest.raises(ValidationError) as exc_info:
            ImprovementResponse(
                improved_title="Valid title",
                improved_description="Valid description here",
                key_improvements=[]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_improvement_response_unicode_support(self):
        """ImprovementResponse supports unicode."""
        from madspark.schemas.generation import ImprovementResponse

        improved = ImprovementResponse(
            improved_title="改善されたアイデア",
            improved_description="これは改善された説明文です。十分な長さが必要です。",
            key_improvements=["改善点1", "改善点2"]
        )

        assert "改善" in improved.improved_title
        assert len(improved.key_improvements) == 2

    def test_improvement_response_serialization(self):
        """ImprovementResponse can be serialized to dict."""
        from madspark.schemas.generation import ImprovementResponse

        improved = ImprovementResponse(
            improved_title="Enhanced idea",
            improved_description="Enhanced description with enough length here",
            key_improvements=["Improvement 1", "Improvement 2"]
        )

        data = improved.model_dump()
        assert isinstance(data, dict)
        assert data["improved_title"] == "Enhanced idea"
        assert len(data["key_improvements"]) == 2
        assert data["implementation_steps"] is None


class TestGenerationAdapters:
    """Tests for adapter conversions with generation schemas."""

    def test_idea_item_to_genai_schema(self):
        """IdeaItem converts to GenAI schema format."""
        from madspark.schemas.generation import IdeaItem
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(IdeaItem)

        assert schema["type"] == "OBJECT"
        assert "idea_number" in schema["properties"]
        assert schema["properties"]["idea_number"]["type"] == "INTEGER"
        assert "title" in schema["properties"]
        assert schema["properties"]["title"]["type"] == "STRING"
        assert "required" in schema
        assert "idea_number" in schema["required"]

    def test_generated_ideas_to_genai_schema(self):
        """GeneratedIdeas converts to GenAI array schema."""
        from madspark.schemas.generation import GeneratedIdeas
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(GeneratedIdeas)

        assert schema["type"] == "ARRAY"
        assert "items" in schema
        assert schema["items"]["type"] == "OBJECT"

    def test_improvement_response_to_genai_schema(self):
        """ImprovementResponse converts to GenAI schema."""
        from madspark.schemas.generation import ImprovementResponse
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(ImprovementResponse)

        assert schema["type"] == "OBJECT"
        assert "improved_title" in schema["properties"]
        assert "key_improvements" in schema["properties"]
        assert schema["properties"]["key_improvements"]["type"] == "ARRAY"

    def test_genai_response_to_idea_item(self):
        """GenAI JSON response parses to IdeaItem."""
        from madspark.schemas.generation import IdeaItem
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "idea_number": 1,
            "title": "Test idea",
            "description": "Test description with enough length here"
        })

        idea = genai_response_to_pydantic(response_text, IdeaItem)

        assert isinstance(idea, IdeaItem)
        assert idea.idea_number == 1
        assert idea.title == "Test idea"

    def test_genai_response_to_generated_ideas(self):
        """GenAI JSON array response parses to GeneratedIdeas."""
        from madspark.schemas.generation import GeneratedIdeas
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps([
            {"idea_number": 1, "title": "Idea 1", "description": "Description one here"},
            {"idea_number": 2, "title": "Idea 2", "description": "Description two here"}
        ])

        ideas = genai_response_to_pydantic(response_text, GeneratedIdeas)

        assert isinstance(ideas, GeneratedIdeas)
        assert len(ideas) == 2
        assert ideas[0].title == "Idea 1"

    def test_genai_response_to_improvement(self):
        """GenAI JSON response parses to ImprovementResponse."""
        from madspark.schemas.generation import ImprovementResponse
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "improved_title": "Enhanced idea",
            "improved_description": "Enhanced description with enough length",
            "key_improvements": ["Improvement 1", "Improvement 2"]
        })

        improved = genai_response_to_pydantic(response_text, ImprovementResponse)

        assert isinstance(improved, ImprovementResponse)
        assert improved.improved_title == "Enhanced idea"
        assert len(improved.key_improvements) == 2
