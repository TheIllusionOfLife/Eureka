"""
Pydantic models for idea generation and improvement agents.

These models replace the legacy IDEA_GENERATOR_SCHEMA and IMPROVER_SCHEMA
dictionary definitions from response_schemas.py.
"""

from pydantic import BaseModel, Field, RootModel
from typing import List, Optional


class IdeaItem(BaseModel):
    """
    Single generated idea from the Idea Generator agent.

    Replaces: IDEA_GENERATOR_SCHEMA items (response_schemas.py:9-39)

    Fields:
        idea_number: Sequential number for the idea (1-indexed)
        title: Concise title for the idea
        description: Detailed explanation of the idea
        key_features: Optional list of key features or capabilities
        category: Optional categorization tag

    Example:
        >>> idea = IdeaItem(
        ...     idea_number=1,
        ...     title="AI-powered fitness coach",
        ...     description="Intelligent personal trainer app with real-time feedback",
        ...     key_features=["Voice guidance", "Progress tracking"],
        ...     category="Health & Fitness"
        ... )
    """
    idea_number: int = Field(
        ...,
        ge=1,
        description="Sequential idea number (1-indexed)"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Concise title for the idea"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed explanation of the idea"
    )
    key_features: Optional[List[str]] = Field(
        default=None,
        description="List of key features or capabilities"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional category tag for the idea"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "idea_number": 1,
                "title": "Smart home energy optimizer",
                "description": "AI-powered system that learns usage patterns and optimizes energy consumption",
                "key_features": ["Machine learning", "Real-time monitoring", "Automated scheduling"],
                "category": "Smart Home"
            }]
        }
    }


class GeneratedIdeas(RootModel[List[IdeaItem]]):
    """
    Array wrapper for multiple generated ideas.

    Replaces: IDEA_GENERATOR_SCHEMA (response_schemas.py:9-39)

    The Idea Generator agent returns an array of ideas when generating
    multiple concepts. This RootModel handles array responses while
    maintaining type safety.

    Usage:
        >>> ideas = GeneratedIdeas([
        ...     IdeaItem(idea_number=1, title="Idea 1", description="Description 1"),
        ...     IdeaItem(idea_number=2, title="Idea 2", description="Description 2")
        ... ])
        >>> len(ideas)
        2
        >>> ideas[0].title
        'Idea 1'

    Note: RootModel is used for array responses. Access items via .root
    or use __iter__ and __getitem__ for direct indexing.
    """

    def __iter__(self):
        """Allow iteration over ideas."""
        return iter(self.root)

    def __getitem__(self, item):
        """Allow indexing into ideas."""
        return self.root[item]

    def __len__(self):
        """Return number of ideas."""
        return len(self.root)

    model_config = {
        "json_schema_extra": {
            "examples": [[
                {
                    "idea_number": 1,
                    "title": "Blockchain supply chain tracker",
                    "description": "Transparent tracking system using blockchain for supply chain verification",
                    "key_features": ["Immutable records", "Real-time tracking"],
                    "category": "Logistics"
                },
                {
                    "idea_number": 2,
                    "title": "VR meditation app",
                    "description": "Virtual reality guided meditation with immersive environments",
                    "key_features": ["3D environments", "Biometric feedback"],
                    "category": "Health & Wellness"
                }
            ]]
        }
    }


class ImprovementResponse(BaseModel):
    """
    Response from the Idea Improver agent.

    Replaces: IMPROVER_SCHEMA (response_schemas.py:283-312)

    Fields:
        improved_title: Enhanced version of the original title
        improved_description: Expanded and refined description
        key_improvements: List of specific improvements made
        implementation_steps: Optional step-by-step implementation guide
        differentiators: Optional unique selling points or differentiators

    Example:
        >>> improved = ImprovementResponse(
        ...     improved_title="AI-Powered Personal Fitness Coach with Real-Time Biometric Feedback",
        ...     improved_description="Advanced fitness app with computer vision and biometric sensors",
        ...     key_improvements=["Added biometric integration", "Enhanced AI algorithms"],
        ...     implementation_steps=["Develop ML model", "Integrate sensors", "Test with users"],
        ...     differentiators=["Patent-pending pose detection", "Medical-grade accuracy"]
        ... )
    """
    improved_title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Enhanced version of the original title"
    )
    improved_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Expanded and refined description with more detail"
    )
    key_improvements: List[str] = Field(
        ...,
        min_length=1,
        description="List of specific improvements made to the original idea"
    )
    implementation_steps: Optional[List[str]] = Field(
        default=None,
        description="Optional step-by-step implementation guide"
    )
    differentiators: Optional[List[str]] = Field(
        default=None,
        description="Optional unique selling points or competitive differentiators"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "improved_title": "Enterprise-Grade AI Supply Chain Optimization Platform",
                "improved_description": "Comprehensive supply chain management system leveraging machine learning for predictive analytics, real-time optimization, and automated decision-making across logistics, inventory, and procurement",
                "key_improvements": [
                    "Added predictive analytics using ML",
                    "Integrated real-time optimization algorithms",
                    "Expanded to cover full supply chain lifecycle"
                ],
                "implementation_steps": [
                    "Design scalable microservices architecture",
                    "Develop ML models for demand forecasting",
                    "Build real-time data pipeline",
                    "Implement optimization engine",
                    "Conduct pilot with enterprise customers"
                ],
                "differentiators": [
                    "Industry-leading 95% forecast accuracy",
                    "Real-time optimization across 10,000+ SKUs",
                    "Seamless ERP integration"
                ]
            }]
        }
    }
