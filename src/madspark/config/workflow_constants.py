"""Workflow orchestration constants for MadSpark.

This module contains constants specific to the WorkflowOrchestrator,
including fallback values for error handling and operation-specific timeouts.

NOTE: Timeout constants in this file are duplicated in execution_constants.py.
For new code, prefer importing from execution_constants.TimeoutConfig for
centralized configuration management. This file is maintained for backward
compatibility.
"""

# Fallback values for error handling
# These are used when agent calls fail to ensure workflow can continue
FALLBACK_ADVOCACY = "N/A (Batch advocate failed)"
FALLBACK_SKEPTICISM = "N/A (Batch skeptic failed)"
FALLBACK_CRITIQUE = "N/A (Evaluation failed)"
FALLBACK_SCORE = 0

# Operation-specific timeouts (in seconds)
# These can be used for finer-grained timeout control per workflow step
IDEA_GENERATION_TIMEOUT = 60  # 1 minute for idea generation
EVALUATION_TIMEOUT = 60  # 1 minute for evaluation
ADVOCACY_TIMEOUT = 90  # 1.5 minutes for advocacy
SKEPTICISM_TIMEOUT = 90  # 1.5 minutes for skepticism
IMPROVEMENT_TIMEOUT = 120  # 2 minutes for improvement
REEVALUATION_TIMEOUT = 60  # 1 minute for re-evaluation
MULTI_DIMENSIONAL_EVAL_TIMEOUT = 120  # 2 minutes for multi-dimensional evaluation
LOGICAL_INFERENCE_TIMEOUT = 90  # 1.5 minutes for logical inference

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
