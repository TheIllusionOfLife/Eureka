"""
Pydantic schema models for MadSpark agents.

This package provides type-safe schema definitions that replace the legacy
dict-based response_schemas. All models support:
- Automatic validation with clear error messages
- Field constraints (min/max for numbers, length for strings)
- IDE autocomplete and type checking
- Conversion to Google GenAI schema format via adapters
"""

from .base import TitledItem, ConfidenceRated, ScoredEvaluation
from .evaluation import (
    EvaluatorResponse,
    DimensionScore,
    CriticEvaluation,
    CriticEvaluations,
)
from .adapters import pydantic_to_genai_schema, genai_response_to_pydantic

__all__ = [
    # Base models
    "TitledItem",
    "ConfidenceRated",
    "ScoredEvaluation",
    # Evaluation models
    "EvaluatorResponse",
    "DimensionScore",
    "CriticEvaluation",
    "CriticEvaluations",
    # Utilities
    "pydantic_to_genai_schema",
    "genai_response_to_pydantic",
]
