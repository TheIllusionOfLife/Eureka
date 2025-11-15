"""
Pydantic schema models for MadSpark agents.

This package provides type-safe schema definitions that replace the legacy
dict-based response_schemas. All models support:
- Automatic validation with clear error messages
- Field constraints (min/max for numbers, length for strings)
- IDE autocomplete and type checking
- Conversion to Google GenAI schema format via adapters
"""

from .base import TitledItem, ConfidenceRated, Scored, ScoredEvaluation
from .evaluation import (
    EvaluatorResponse,
    DimensionScore,
    CriticEvaluation,
    CriticEvaluations,
)
from .generation import (
    IdeaItem,
    GeneratedIdeas,
    ImprovementResponse,
)
from .advocacy import (
    StrengthItem,
    OpportunityItem,
    ConcernResponse,
    AdvocacyResponse,
)
from .skepticism import (
    CriticalFlaw,
    RiskChallenge,
    QuestionableAssumption,
    MissingConsideration,
    SkepticismResponse,
)
from .logical_inference import (
    InferenceResult,
    CausalAnalysis,
    ConstraintAnalysis,
    ContradictionAnalysis,
    ImplicationsAnalysis,
)
from .adapters import pydantic_to_genai_schema, genai_response_to_pydantic

__all__ = [
    # Base models
    "TitledItem",
    "ConfidenceRated",
    "Scored",
    "ScoredEvaluation",
    # Evaluation models
    "EvaluatorResponse",
    "DimensionScore",
    "CriticEvaluation",
    "CriticEvaluations",
    # Generation models
    "IdeaItem",
    "GeneratedIdeas",
    "ImprovementResponse",
    # Advocacy models
    "StrengthItem",
    "OpportunityItem",
    "ConcernResponse",
    "AdvocacyResponse",
    # Skepticism models
    "CriticalFlaw",
    "RiskChallenge",
    "QuestionableAssumption",
    "MissingConsideration",
    "SkepticismResponse",
    # Logical inference models
    "InferenceResult",
    "CausalAnalysis",
    "ConstraintAnalysis",
    "ContradictionAnalysis",
    "ImplicationsAnalysis",
    # Utilities
    "pydantic_to_genai_schema",
    "genai_response_to_pydantic",
]
