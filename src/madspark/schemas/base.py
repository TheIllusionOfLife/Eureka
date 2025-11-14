"""
Base Pydantic models providing common patterns across MadSpark schemas.

These base classes encapsulate shared validation logic and field constraints
that are inherited by agent-specific schema models.
"""

from pydantic import BaseModel, Field, field_validator


class TitledItem(BaseModel):
    """
    Base model for items with title and description.

    Used across multiple agents (Advocate, Skeptic) for representing
    structured feedback items like strengths, risks, opportunities, etc.

    Examples:
        >>> item = TitledItem(
        ...     title="Innovation Potential",
        ...     description="Leverages emerging AI capabilities"
        ... )
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Concise title for the item"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed explanation of the item"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "title": "Market Opportunity",
                "description": "Growing demand in enterprise sector with 25% CAGR"
            }]
        }
    }


class ConfidenceRated(BaseModel):
    """
    Base model for responses that include a confidence score.

    Used in logical inference and analysis schemas where the agent
    expresses certainty in its conclusions (0.0 = no confidence, 1.0 = certain).

    Features:
        - Enforces 0.0 to 1.0 range via Gemini API (new feature!)
        - Rounds to 2 decimal places for consistency

    Examples:
        >>> analysis = ConfidenceRated(confidence=0.85)
        >>> analysis.confidence
        0.85
    """
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 (uncertain) to 1.0 (certain)"
    )

    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Round confidence to 2 decimal places for consistency."""
        return round(v, 2)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "confidence": 0.85
            }]
        }
    }


class Scored(BaseModel):
    """
    Base model for items with a numerical score.

    Provides the core scoring field and rounding validator used across
    multiple evaluation models.

    Features:
        - Enforces 0.0 to 10.0 range via Gemini API (new feature!)
        - Rounds to 1 decimal place for readability

    Examples:
        >>> scored = Scored(score=8.567)
        >>> scored.score
        8.6
    """
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Numerical score from 0 (poor) to 10 (excellent)"
    )

    @field_validator('score')
    @classmethod
    def round_score(cls, v: float) -> float:
        """Round score to 1 decimal place for readability."""
        return round(v, 1)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "score": 8.5
            }]
        }
    }


class ScoredEvaluation(Scored):
    """
    Base model for evaluations with a numerical score and critique.

    Used by Critic and Evaluator agents to provide quantitative assessments
    of ideas on a 0-10 scale.

    Features:
        - Inherits score field and rounding from Scored base class
        - Requires minimum critique length to ensure quality feedback

    Examples:
        >>> eval_obj = ScoredEvaluation(
        ...     score=8.5,
        ...     critique="Strong concept with clear market fit"
        ... )
    """
    critique: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed written evaluation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "score": 8.5,
                "critique": "Innovative approach with strong technical foundation and clear market need"
            }]
        }
    }
