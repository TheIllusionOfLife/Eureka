"""Enhanced Reasoning System for Phase 2 MadSpark Multi-Agent System.

This module implements advanced reasoning capabilities including:
- Context awareness across agent interactions
- Logical inference chains
- Multi-dimensional evaluation metrics
- Agent memory and conversation tracking

COMPATIBILITY LAYER: This module now redirects to madspark.core.reasoning package.
"""
import logging

# Re-export from new package
from .reasoning import (
    ReasoningConfig,
    ContextData,
    InferenceStep,
    LogicalChain,
    ContextMemory,
    LogicalInference,
    MultiDimensionalEvaluator,
    AgentConversationTracker,
    ReasoningEngine
)

# Configure logging for enhanced reasoning (maintain backward compatibility)
reasoning_logger = logging.getLogger(__name__)

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