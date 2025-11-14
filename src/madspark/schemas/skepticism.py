"""
Pydantic models for the Skeptic agent.

These models replace the legacy SKEPTICISM_SCHEMA dictionary definition
from response_schemas.py.
"""

from pydantic import BaseModel, Field
from typing import List
from .base import TitledItem


class CriticalFlaw(TitledItem):
    """
    Single critical flaw identified by the Skeptic agent.

    Directly inherits title and description fields from TitledItem base class.
    Represents a fundamental problem or weakness in the idea.

    Example:
        >>> flaw = CriticalFlaw(
        ...     title="Scalability Concerns",
        ...     description="Current architecture cannot handle more than 1000 concurrent users"
        ... )
    """
    pass


class RiskChallenge(TitledItem):
    """
    Single risk or challenge identified by the Skeptic agent.

    Directly inherits title and description fields from TitledItem base class.
    Represents a potential problem or obstacle that needs addressing.

    Example:
        >>> risk = RiskChallenge(
        ...     title="Regulatory Uncertainty",
        ...     description="Unclear regulations in key markets may delay launch by 6-12 months"
        ... )
    """
    pass


class QuestionableAssumption(BaseModel):
    """
    Questionable assumption identified by the Skeptic agent.

    Represents an assumption made in the idea that may not hold true,
    paired with a concern explaining why it's questionable.

    Fields:
        assumption: The assumption being questioned
        concern: Why this assumption is problematic or uncertain

    Example:
        >>> qa = QuestionableAssumption(
        ...     assumption="Users will pay $99/month premium pricing",
        ...     concern="Market research shows strong price sensitivity in target demographic"
        ... )
    """
    assumption: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The assumption being questioned"
    )
    concern: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Why this assumption is problematic or uncertain"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "assumption": "Users will organically adopt the platform without marketing spend",
                "concern": "Historical data shows similar B2C products required $50K+ in marketing for initial traction"
            }]
        }
    }


class MissingConsideration(BaseModel):
    """
    Missing consideration identified by the Skeptic agent.

    Represents an important aspect or factor that hasn't been adequately
    addressed in the idea, along with why it's important.

    Fields:
        aspect: The missing aspect or consideration
        importance: Why this aspect is important and needs addressing

    Example:
        >>> mc = MissingConsideration(
        ...     aspect="Data Privacy Compliance",
        ...     importance="GDPR compliance is critical for EU market entry and carries hefty penalties"
        ... )
    """
    aspect: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="The missing aspect or consideration"
    )
    importance: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Why this aspect is important and needs addressing"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "aspect": "Customer Support Infrastructure",
                "importance": "Scaling to 10K users will require 24/7 support team, significantly impacting unit economics"
            }]
        }
    }


class SkepticismResponse(BaseModel):
    """
    Complete response from the Skeptic agent.

    Replaces: SKEPTICISM_SCHEMA (response_schemas.py:202-279)

    Fields:
        critical_flaws: List of fundamental problems or weaknesses
        risks_and_challenges: List of potential problems or obstacles
        questionable_assumptions: List of questionable assumptions with concerns
        missing_considerations: List of missing aspects with importance explanations

    Example:
        >>> from madspark.schemas.skepticism import (
        ...     SkepticismResponse, CriticalFlaw, RiskChallenge,
        ...     QuestionableAssumption, MissingConsideration
        ... )
        >>> skepticism = SkepticismResponse(
        ...     critical_flaws=[
        ...         CriticalFlaw(
        ...             title="Unproven Business Model",
        ...             description="No clear path to monetization demonstrated"
        ...         )
        ...     ],
        ...     risks_and_challenges=[
        ...         RiskChallenge(
        ...             title="Market Saturation",
        ...             description="Highly competitive space with entrenched players"
        ...         )
        ...     ],
        ...     questionable_assumptions=[
        ...         QuestionableAssumption(
        ...             assumption="Viral growth will occur naturally",
        ...             concern="Similar products failed to achieve viral adoption"
        ...         )
        ...     ],
        ...     missing_considerations=[
        ...         MissingConsideration(
        ...             aspect="Regulatory Compliance",
        ...             importance="Industry-specific regulations require expensive compliance"
        ...         )
        ...     ]
        ... )
    """
    critical_flaws: List[CriticalFlaw] = Field(
        ...,
        min_length=1,
        description="List of fundamental problems or weaknesses in the idea"
    )
    risks_and_challenges: List[RiskChallenge] = Field(
        ...,
        min_length=1,
        description="List of potential problems or obstacles that need addressing"
    )
    questionable_assumptions: List[QuestionableAssumption] = Field(
        ...,
        min_length=1,
        description="List of questionable assumptions with concerns explaining why"
    )
    missing_considerations: List[MissingConsideration] = Field(
        ...,
        min_length=1,
        description="List of important aspects not adequately addressed"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "critical_flaws": [
                    {
                        "title": "Technology Readiness",
                        "description": "Core technology still in prototype stage with no proven reliability at scale"
                    },
                    {
                        "title": "Market Timing",
                        "description": "Target market showing declining interest based on Google Trends data"
                    }
                ],
                "risks_and_challenges": [
                    {
                        "title": "Funding Requirements",
                        "description": "Estimated $2M burn before revenue, difficult market for early-stage fundraising"
                    },
                    {
                        "title": "Technical Complexity",
                        "description": "Requires expertise in AI/ML, data engineering, and domain knowledge"
                    }
                ],
                "questionable_assumptions": [
                    {
                        "assumption": "Enterprise customers will switch from incumbents",
                        "concern": "High switching costs and long sales cycles typical in enterprise SaaS"
                    },
                    {
                        "assumption": "Team can build and scale in 12 months",
                        "concern": "Similar products took 24-36 months to reach market fit"
                    }
                ],
                "missing_considerations": [
                    {
                        "aspect": "Intellectual Property Protection",
                        "importance": "Patents essential for defensibility but expensive and time-consuming"
                    },
                    {
                        "aspect": "Go-to-Market Strategy",
                        "importance": "No clear channel strategy or customer acquisition plan outlined"
                    }
                ]
            }]
        }
    }
