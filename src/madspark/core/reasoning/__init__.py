"""Enhanced Reasoning System for MadSpark Multi-Agent System.

This package implements advanced reasoning capabilities including:
- Context awareness across agent interactions
- Logical inference chains
- Multi-dimensional evaluation metrics
- Agent memory and conversation tracking
"""

from .types import (
    ReasoningConfig,
    ContextData,
    InferenceStep,
    LogicalChain
)
from .context_memory import ContextMemory
from .inference import LogicalInference
from .evaluator import MultiDimensionalEvaluator
from .tracker import AgentConversationTracker
from .engine import ReasoningEngine

__all__ = [
    'ReasoningConfig',
    'ContextData',
    'InferenceStep',
    'LogicalChain',
    'ContextMemory',
    'LogicalInference',
    'MultiDimensionalEvaluator',
    'AgentConversationTracker',
    'ReasoningEngine'
]
