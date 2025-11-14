"""
Pydantic models for evaluation and critique agents.

These models replace the legacy EVALUATOR_SCHEMA, DIMENSION_SCORE_SCHEMA,
and CRITIC_SCHEMA dictionary definitions.
"""

from pydantic import BaseModel, Field, RootModel
from typing import List, Optional
from .base import ScoredEvaluation


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


class CriticEvaluation(BaseModel):
    """
    Single evaluation item from the Critic agent.

    Identical to EvaluatorResponse but used in array context.
    This model represents one critic's evaluation within a batch.

    Note: When Critic agent returns multiple evaluations, they are
    wrapped in a CriticEvaluations array (see below).
    """
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Numerical score from 0 (poor) to 10 (excellent)"
    )
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
