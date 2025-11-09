"""Workflow orchestration constants for MadSpark.

This module contains constants specific to the WorkflowOrchestrator,
including fallback values for error handling and operation-specific timeouts.

NOTE: Timeout constants are re-exported from execution_constants.TimeoutConfig.
For new code, prefer importing from execution_constants.TimeoutConfig directly
for centralized configuration management. This file is maintained for backward
compatibility only.
"""
import warnings

from .execution_constants import TimeoutConfig

# Emit deprecation warning when this module is imported
warnings.warn(
    "workflow_constants module is deprecated. "
    "Use execution_constants.TimeoutConfig for timeout values instead.",
    DeprecationWarning,
    stacklevel=2
)

# Fallback values for error handling
# These are used when agent calls fail to ensure workflow can continue
FALLBACK_ADVOCACY = "N/A (Batch advocate failed)"
FALLBACK_SKEPTICISM = "N/A (Batch skeptic failed)"
FALLBACK_CRITIQUE = "N/A (Evaluation failed)"
FALLBACK_SCORE = 0

# Operation-specific timeouts (in seconds)
# Re-exported from execution_constants for backward compatibility
IDEA_GENERATION_TIMEOUT = TimeoutConfig.IDEA_GENERATION_TIMEOUT
EVALUATION_TIMEOUT = TimeoutConfig.EVALUATION_TIMEOUT
ADVOCACY_TIMEOUT = TimeoutConfig.ADVOCACY_TIMEOUT
SKEPTICISM_TIMEOUT = TimeoutConfig.SKEPTICISM_TIMEOUT
IMPROVEMENT_TIMEOUT = TimeoutConfig.IMPROVEMENT_TIMEOUT
REEVALUATION_TIMEOUT = TimeoutConfig.REEVALUATION_TIMEOUT
MULTI_DIMENSIONAL_EVAL_TIMEOUT = TimeoutConfig.MULTI_DIMENSIONAL_EVAL_TIMEOUT
LOGICAL_INFERENCE_TIMEOUT = TimeoutConfig.LOGICAL_INFERENCE_TIMEOUT

# Workflow step names (for logging and monitoring)
STEP_IDEA_GENERATION = "Idea Generation"
STEP_EVALUATION = "Evaluation"
STEP_ADVOCACY = "Advocacy"
STEP_SKEPTICISM = "Skepticism"
STEP_IMPROVEMENT = "Improvement"
STEP_REEVALUATION = "Re-evaluation"
STEP_MULTI_DIMENSIONAL_EVAL = "Multi-dimensional Evaluation"
STEP_LOGICAL_INFERENCE = "Logical Inference"
STEP_BUILD_RESULTS = "Build Final Results"
