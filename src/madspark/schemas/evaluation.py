"""
Pydantic models for evaluation and critique agents.

These models replace the legacy EVALUATOR_SCHEMA, DIMENSION_SCORE_SCHEMA,
and CRITIC_SCHEMA dictionary definitions.
"""

from pydantic import BaseModel, Field, RootModel
from typing import List, Optional
from .base import Scored, ScoredEvaluation


class EvaluatorResponse(ScoredEvaluation):
    """
    Response from the Evaluator agent.

    Extends ScoredEvaluation with optional strengths and weaknesses arrays.
    Replaces: EVALUATOR_SCHEMA (response_schemas.py:60-83)

    Fields:
        score: Numerical rating 0-10 (inherited from ScoredEvaluation)
        critique: Detailed written evaluation (inherited)
        strengths: Optional list of positive aspects
        weaknesses: Optional list of concerns or limitations

    Example:
        >>> eval_obj = EvaluatorResponse(
        ...     score=7.5,
        ...     critique="Solid concept with room for improvement",
        ...     strengths=["Clear value proposition", "Large market"],
        ...     weaknesses=["High competition", "Complex implementation"]
        ... )
    """
    strengths: Optional[List[str]] = Field(
        default=None,
        description="List of positive aspects and advantages"
    )
    weaknesses: Optional[List[str]] = Field(
        default=None,
        description="List of concerns, limitations, or areas for improvement"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "score": 7.5,
                "critique": "Innovative approach with strong technical foundation but faces market challenges",
                "strengths": [
                    "Novel AI integration strategy",
                    "Clear monetization path",
                    "Strong technical team"
                ],
                "weaknesses": [
                    "Highly competitive market",
                    "Requires significant capital",
                    "Long development timeline"
                ]
            }]
        }
    }


class DimensionScore(BaseModel):
    """
    Score for a single evaluation dimension.

    Used in multi-dimensional evaluations where ideas are rated across
    multiple criteria (feasibility, impact, innovation, etc.).
    Replaces: DIMENSION_SCORE_SCHEMA (response_schemas.py:475-488)

    Fields:
        score: Numerical rating 0-10 with API-enforced bounds
        reasoning: Optional explanation for the score

    Example:
        >>> dim = DimensionScore(
        ...     score=8.5,
        ...     reasoning="High feasibility due to existing infrastructure"
        ... )
    """
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Numerical score from 0 (poor) to 10 (excellent)"
    )
    reasoning: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Explanation for the assigned score"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "score": 8.5,
                "reasoning": "Strong market fit with proven demand and minimal regulatory barriers"
            }]
        }
    }


class MultiDimensionalEvaluation(BaseModel):
    """
    Multi-dimensional evaluation for a single idea.

    Used in batch evaluation where multiple ideas are evaluated across
    all dimensions in a single API call for efficiency.

    Fields:
        idea_index: Index of the idea in the batch (0-based)
        feasibility: How realistic implementation is (0-10)
        innovation: How novel and creative the idea is (0-10)
        impact: Potential positive impact (0-10)
        cost_effectiveness: Cost vs benefit ratio (0-10)
        scalability: Ability to scale up (0-10)
        risk_assessment: Risk level - higher score = lower risk (0-10)
        timeline: Implementation timeline feasibility (0-10)

    Example:
        >>> eval_obj = MultiDimensionalEvaluation(
        ...     idea_index=0,
        ...     feasibility=8.5,
        ...     innovation=7.0,
        ...     impact=9.0,
        ...     cost_effectiveness=6.5,
        ...     scalability=7.5,
        ...     risk_assessment=6.0,
        ...     timeline=7.0
        ... )
    """
    idea_index: int = Field(
        ...,
        ge=0,
        description="Index of the idea being evaluated (0-based)"
    )
    feasibility: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Feasibility score: how realistic implementation is"
    )
    innovation: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Innovation score: how novel and creative the idea is"
    )
    impact: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Impact score: potential positive impact"
    )
    cost_effectiveness: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Cost-effectiveness score: cost vs benefit ratio"
    )
    scalability: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Scalability score: ability to scale up"
    )
    risk_assessment: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Risk assessment score: higher score means lower risk"
    )
    timeline: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Timeline score: implementation timeline feasibility"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "idea_index": 0,
                "feasibility": 8.5,
                "innovation": 7.0,
                "impact": 9.0,
                "cost_effectiveness": 6.5,
                "scalability": 7.5,
                "risk_assessment": 6.0,
                "timeline": 7.0
            }]
        }
    }


class MultiDimensionalEvaluations(RootModel[List[MultiDimensionalEvaluation]]):
    """
    Array of multi-dimensional evaluations for batch processing.

    Used when evaluating multiple ideas in a single API call for efficiency.
    Each evaluation contains scores across all 7 dimensions.

    Usage:
        >>> evals = MultiDimensionalEvaluations([
        ...     MultiDimensionalEvaluation(idea_index=0, feasibility=8.5, ...),
        ...     MultiDimensionalEvaluation(idea_index=1, feasibility=7.0, ...)
        ... ])
        >>> len(evals)
        2
        >>> evals[0].feasibility
        8.5
    """

    def __iter__(self):
        """Allow iteration over evaluations."""
        return iter(self.root)

    def __getitem__(self, item):
        """Allow indexing into evaluations."""
        return self.root[item]

    def __len__(self):
        """Return number of evaluations."""
        return len(self.root)

    model_config = {
        "json_schema_extra": {
            "examples": [[
                {
                    "idea_index": 0,
                    "feasibility": 8.5,
                    "innovation": 7.0,
                    "impact": 9.0,
                    "cost_effectiveness": 6.5,
                    "scalability": 7.5,
                    "risk_assessment": 6.0,
                    "timeline": 7.0
                },
                {
                    "idea_index": 1,
                    "feasibility": 7.0,
                    "innovation": 8.5,
                    "impact": 8.0,
                    "cost_effectiveness": 7.5,
                    "scalability": 6.5,
                    "risk_assessment": 7.0,
                    "timeline": 6.0
                }
            ]]
        }
    }


class CriticEvaluation(Scored):
    """
    Single evaluation item from the Critic agent.

    Inherits score field and rounding validator from Scored base class.
    This model represents one critic's evaluation within a batch.

    Note: When Critic agent returns multiple evaluations, they are
    wrapped in a CriticEvaluations array (see below).
    """
    comment: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed written evaluation"
    )
    strengths: Optional[List[str]] = Field(
        default=None,
        description="List of positive aspects"
    )
    weaknesses: Optional[List[str]] = Field(
        default=None,
        description="List of concerns or limitations"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "score": 6.5,
                "comment": "Interesting concept but execution challenges remain",
                "strengths": ["Innovative", "Clear need"],
                "weaknesses": ["Expensive", "Complex"]
            }]
        }
    }


class CriticEvaluations(RootModel[List[CriticEvaluation]]):
    """
    Array wrapper for multiple critic evaluations.

    Replaces: CRITIC_SCHEMA (response_schemas.py:94-120)

    The Critic agent returns an array of evaluations when processing
    multiple ideas in batch mode. This RootModel handles array responses
    while maintaining type safety.

    Usage:
        >>> evals = CriticEvaluations([
        ...     CriticEvaluation(score=8, comment="Excellent idea"),
        ...     CriticEvaluation(score=6, comment="Needs work")
        ... ])
        >>> len(evals.root)
        2
        >>> evals[0].score
        8.0

    Note: RootModel is used for array responses. Access items via .root
    or implement __iter__ and __getitem__ for direct indexing.
    """

    def __iter__(self):
        """Allow iteration over evaluations."""
        return iter(self.root)

    def __getitem__(self, item):
        """Allow indexing into evaluations."""
        return self.root[item]

    def __len__(self):
        """Return number of evaluations."""
        return len(self.root)

    model_config = {
        "json_schema_extra": {
            "examples": [[
                {
                    "score": 8.5,
                    "comment": "Strong innovative concept with clear execution path",
                    "strengths": ["Novel approach", "Large market"],
                    "weaknesses": ["High initial cost"]
                },
                {
                    "score": 6.0,
                    "comment": "Interesting but faces significant challenges",
                    "strengths": ["Addresses real need"],
                    "weaknesses": ["Competitive market", "Regulatory hurdles"]
                }
            ]]
        }
    }
