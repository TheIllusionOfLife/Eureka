"""
Pydantic models for logical inference analysis.

These models replace the legacy InferenceResult dataclass and logical
inference schema dictionaries from response_schemas.py.
"""

from pydantic import Field, field_validator
from typing import List, Optional, Dict, Any
from .base import ConfidenceRated


class InferenceResult(ConfidenceRated):
    """
    Base result of logical inference analysis.

    Replaces: InferenceResult dataclass (logical_inference_engine.py:28-64)

    Extends ConfidenceRated to inherit confidence field with validation.
    Provides core fields used across all inference types.

    Fields:
        inference_chain: Step-by-step reasoning process
        conclusion: Final conclusion or result
        confidence: Confidence score 0.0-1.0 (inherited from ConfidenceRated)
        improvements: Optional suggestions for improvement

    Example:
        >>> result = InferenceResult(
        ...     inference_chain=["Premise: All ideas need validation", "Observation: This idea is untested"],
        ...     conclusion="Therefore, this idea requires market validation",
        ...     confidence=0.85,
        ...     improvements="Conduct customer interviews to validate assumptions"
        ... )
    """
    inference_chain: List[str] = Field(
        ...,
        min_length=1,
        description="Step-by-step reasoning process leading to conclusion"
    )
    conclusion: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Final conclusion or result of the analysis"
    )
    improvements: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional suggestions for improvement based on analysis"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inference_chain": [
                    "Premise: Market validation is essential for product-market fit",
                    "Observation: No customer interviews conducted yet",
                    "Inference: High risk of building wrong features"
                ],
                "conclusion": "Recommend conducting 20+ customer interviews before development",
                "confidence": 0.85,
                "improvements": "Consider using landing page tests to validate demand"
            }]
        }
    }


class CausalAnalysis(InferenceResult):
    """
    Causal analysis result identifying cause-effect relationships.

    Replaces: CAUSAL_ANALYSIS_SCHEMA (response_schemas.py)

    Extends InferenceResult with causal-specific fields for analyzing
    cause-effect chains, feedback loops, and root causes.

    Additional Fields:
        causal_chain: Sequence of cause-effect relationships
        feedback_loops: Identified positive or negative feedback loops
        root_cause: Fundamental root cause identified

    Example:
        >>> analysis = CausalAnalysis(
        ...     inference_chain=["Market analysis", "Competitor review"],
        ...     conclusion="High competition causes pricing pressure",
        ...     confidence=0.8,
        ...     causal_chain=["Market saturation → Price competition → Margin erosion"],
        ...     feedback_loops=["Lower prices → More customers → Economies of scale → Even lower prices"],
        ...     root_cause="Commoditization of core product features"
        ... )
    """
    causal_chain: Optional[List[str]] = Field(
        default=None,
        description="Sequence of cause-effect relationships identified"
    )
    feedback_loops: Optional[List[str]] = Field(
        default=None,
        description="Identified positive or negative feedback loops"
    )
    root_cause: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Fundamental root cause identified in the analysis"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inference_chain": ["Analyze market dynamics", "Identify competitive forces"],
                "conclusion": "Market saturation driving price competition",
                "confidence": 0.8,
                "causal_chain": [
                    "Market saturation → Increased competition",
                    "Increased competition → Price pressure",
                    "Price pressure → Margin erosion"
                ],
                "feedback_loops": [
                    "Lower prices → Higher volume → Economies of scale → Even lower prices (positive reinforcing)"
                ],
                "root_cause": "Commoditization of core product features driving race to bottom"
            }]
        }
    }


class ConstraintAnalysis(InferenceResult):
    """
    Constraint satisfaction analysis result.

    Replaces: CONSTRAINT_ANALYSIS_SCHEMA (response_schemas.py)

    Analyzes how well an idea satisfies various constraints (cost, time,
    resources, etc.) and identifies necessary trade-offs.

    Additional Fields:
        constraint_satisfaction: Dictionary mapping constraint names to satisfaction scores (0-1)
        overall_satisfaction: Overall constraint satisfaction score (0-1)
        trade_offs: Identified trade-offs between competing constraints

    Example:
        >>> analysis = ConstraintAnalysis(
        ...     inference_chain=["Evaluate cost constraints", "Evaluate time constraints"],
        ...     conclusion="Constraints partially satisfied with trade-offs",
        ...     confidence=0.75,
        ...     constraint_satisfaction={"cost": 0.8, "time": 0.6, "quality": 0.9},
        ...     overall_satisfaction=0.77,
        ...     trade_offs=["Fast delivery requires higher cost", "Low cost requires longer timeline"]
        ... )
    """
    constraint_satisfaction: Optional[Dict[str, float]] = Field(
        default=None,
        description="Dictionary mapping constraint names to satisfaction scores (0.0-1.0)"
    )
    overall_satisfaction: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall constraint satisfaction score (0.0-1.0)"
    )
    trade_offs: Optional[List[str]] = Field(
        default=None,
        description="Identified trade-offs between competing constraints"
    )

    @field_validator('overall_satisfaction')
    @classmethod
    def round_overall_satisfaction(cls, v: Optional[float]) -> Optional[float]:
        """Round overall satisfaction to 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inference_chain": ["Evaluate budget constraints", "Evaluate timeline constraints"],
                "conclusion": "Project feasible with trade-offs on scope",
                "confidence": 0.75,
                "constraint_satisfaction": {
                    "budget": 0.8,
                    "timeline": 0.6,
                    "quality": 0.9,
                    "resources": 0.7
                },
                "overall_satisfaction": 0.75,
                "trade_offs": [
                    "Accelerated timeline requires 30% higher budget",
                    "Maintaining budget requires extending timeline by 2 months",
                    "Full feature set conflicts with aggressive timeline"
                ]
            }]
        }
    }


class ContradictionAnalysis(InferenceResult):
    """
    Contradiction detection analysis result.

    Replaces: CONTRADICTION_ANALYSIS_SCHEMA (response_schemas.py)

    Identifies logical contradictions or inconsistencies in the idea
    and suggests resolutions.

    Additional Fields:
        contradictions: List of identified contradictions with details
        resolution: Suggested resolution for the contradictions

    Example:
        >>> analysis = ContradictionAnalysis(
        ...     inference_chain=["Review assumptions", "Check consistency"],
        ...     conclusion="Found contradiction in pricing model",
        ...     confidence=0.9,
        ...     contradictions=[
        ...         {"statement1": "Premium positioning", "statement2": "Budget pricing", "severity": "high"}
        ...     ],
        ...     resolution="Clarify target segment: premium for enterprise, budget for SMB"
        ... )
    """
    contradictions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of identified contradictions with statement pairs and severity"
    )
    resolution: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Suggested resolution for the identified contradictions"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inference_chain": [
                    "Analyze positioning statement",
                    "Compare with pricing strategy",
                    "Identify inconsistencies"
                ],
                "conclusion": "Fundamental contradiction between positioning and pricing",
                "confidence": 0.9,
                "contradictions": [
                    {
                        "statement1": "Premium brand positioning targeting enterprise customers",
                        "statement2": "Budget pricing strategy ($9/month)",
                        "severity": "high",
                        "impact": "Confuses market positioning and reduces perceived value"
                    }
                ],
                "resolution": "Align pricing with premium positioning ($99/month) or reposition as value player targeting SMBs"
            }]
        }
    }


class ImplicationsAnalysis(InferenceResult):
    """
    Implications and second-order effects analysis result.

    Replaces: IMPLICATIONS_ANALYSIS_SCHEMA (response_schemas.py)

    Identifies direct implications and second-order effects
    of implementing the idea.

    Additional Fields:
        implications: Direct implications of the idea
        second_order_effects: Indirect or second-order effects

    Example:
        >>> analysis = ImplicationsAnalysis(
        ...     inference_chain=["Analyze direct effects", "Project indirect effects"],
        ...     conclusion="Significant second-order effects on market dynamics",
        ...     confidence=0.85,
        ...     implications=["Market disruption", "Competitive response"],
        ...     second_order_effects=["Industry consolidation", "Regulatory attention"]
        ... )
    """
    implications: Optional[List[str]] = Field(
        default=None,
        description="Direct implications of implementing the idea"
    )
    second_order_effects: Optional[List[str]] = Field(
        default=None,
        description="Indirect or second-order effects that may occur"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inference_chain": [
                    "Project direct market impact",
                    "Analyze competitive dynamics",
                    "Consider regulatory implications"
                ],
                "conclusion": "Implementation triggers significant industry changes",
                "confidence": 0.85,
                "implications": [
                    "Market disruption in traditional distribution channels",
                    "Competitive response from incumbents within 6-12 months",
                    "Need for regulatory compliance framework"
                ],
                "second_order_effects": [
                    "Accelerated industry consolidation as smaller players exit",
                    "Increased regulatory scrutiny of entire sector",
                    "Emergence of new business models copying approach",
                    "Shift in customer expectations industry-wide"
                ]
            }]
        }
    }
