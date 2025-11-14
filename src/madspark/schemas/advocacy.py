"""
Pydantic models for the Advocate agent.

These models replace the legacy ADVOCACY_SCHEMA dictionary definition
from response_schemas.py.
"""

from pydantic import BaseModel, Field
from typing import List
from .base import TitledItem


class StrengthItem(TitledItem):
    """
    Single strength identified by the Advocate agent.

    Directly inherits title and description fields from TitledItem base class.
    Represents a positive aspect or advantage of the idea.

    Example:
        >>> strength = StrengthItem(
        ...     title="Market Opportunity",
        ...     description="Growing demand in enterprise sector with 25% CAGR"
        ... )
    """
    pass


class OpportunityItem(TitledItem):
    """
    Single opportunity identified by the Advocate agent.

    Directly inherits title and description fields from TitledItem base class.
    Represents a potential future benefit or expansion possibility.

    Example:
        >>> opportunity = OpportunityItem(
        ...     title="Strategic Partnerships",
        ...     description="Potential collaboration with industry leaders in adjacent markets"
        ... )
    """
    pass


class ConcernResponse(BaseModel):
    """
    Concern-response pair from the Advocate agent.

    Represents addressing a potential concern or objection with a thoughtful response.

    Fields:
        concern: The concern or objection being addressed
        response: How the concern is addressed or mitigated

    Example:
        >>> cr = ConcernResponse(
        ...     concern="High development cost estimated at $500K",
        ...     response="Can be mitigated through MVP approach and phased rollout"
        ... )
    """
    concern: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The concern or objection being addressed"
    )
    response: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="How the concern is addressed or mitigated"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "concern": "High development cost estimated at $500K",
                "response": "Can be mitigated through MVP approach, starting with core features and validating market fit before full investment"
            }]
        }
    }


class AdvocacyResponse(BaseModel):
    """
    Complete response from the Advocate agent.

    Replaces: ADVOCACY_SCHEMA (response_schemas.py:123-182)

    Fields:
        strengths: List of positive aspects and advantages
        opportunities: List of potential benefits and expansion possibilities
        addressing_concerns: List of concerns with responses addressing them

    Example:
        >>> from madspark.schemas.advocacy import (
        ...     AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse
        ... )
        >>> advocacy = AdvocacyResponse(
        ...     strengths=[
        ...         StrengthItem(
        ...             title="Strong Team",
        ...             description="Experienced founders with track record"
        ...         )
        ...     ],
        ...     opportunities=[
        ...         OpportunityItem(
        ...             title="Market Expansion",
        ...             description="Easy to expand to adjacent markets"
        ...         )
        ...     ],
        ...     addressing_concerns=[
        ...         ConcernResponse(
        ...             concern="High competition",
        ...             response="Differentiated through unique AI technology"
        ...         )
        ...     ]
        ... )
    """
    strengths: List[StrengthItem] = Field(
        ...,
        min_length=1,
        description="List of positive aspects and advantages of the idea"
    )
    opportunities: List[OpportunityItem] = Field(
        ...,
        min_length=1,
        description="List of potential benefits and expansion possibilities"
    )
    addressing_concerns: List[ConcernResponse] = Field(
        ...,
        min_length=1,
        description="List of concerns with thoughtful responses addressing them"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "strengths": [
                    {
                        "title": "Market Timing",
                        "description": "Perfect timing as industry shifts to AI-first approaches"
                    },
                    {
                        "title": "Technical Feasibility",
                        "description": "Built on proven open-source frameworks with strong community support"
                    }
                ],
                "opportunities": [
                    {
                        "title": "Enterprise Expansion",
                        "description": "Clear path to enterprise sales with recurring revenue model"
                    },
                    {
                        "title": "Platform Play",
                        "description": "Can become ecosystem with third-party integrations"
                    }
                ],
                "addressing_concerns": [
                    {
                        "concern": "Regulatory uncertainty in key markets",
                        "response": "Proactive engagement with regulators and compliance-first design ensures adaptability"
                    },
                    {
                        "concern": "Significant capital requirements",
                        "response": "Phased approach with MVP validation reduces initial burn and attracts investors"
                    }
                ]
            }]
        }
    }
