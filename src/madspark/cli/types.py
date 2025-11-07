"""Type definitions for MadSpark CLI module.

This module contains TypedDict definitions and Literal types used across
the CLI components to improve type safety and IDE support.
"""

from typing import TypedDict, Literal, Optional, List


# Output format types
OutputFormat = Literal['brief', 'simple', 'detailed', 'summary', 'json', 'text']
ExportFormat = Literal['json', 'csv', 'markdown', 'pdf', 'all']


class WorkflowConfig(TypedDict, total=False):
    """Configuration for workflow execution.

    All fields are optional (total=False) to allow partial configurations.
    """
    num_top_candidates: int
    enable_novelty_filter: bool
    novelty_threshold: float
    enhanced_reasoning: bool
    multi_dimensional_eval: bool
    logical_inference: bool
    async_mode: bool  # Note: 'async' is reserved keyword, use 'async_mode'
    enable_cache: bool
    output_format: OutputFormat
    export: Optional[ExportFormat]
    export_dir: str
    bookmark_results: bool
    bookmark_tags: List[str]
    verbose: bool


class SessionData(TypedDict):
    """Data returned from interactive session.

    Required fields for session results.
    """
    theme: str
    constraints: str
    config: WorkflowConfig


class MetricsData(TypedDict, total=False):
    """Batch operation metrics data.

    All fields are optional as metrics may vary by operation type.
    """
    timestamp: str
    batch_type: str
    items_count: int
    duration_seconds: float
    success: bool
    fallback_used: bool
    estimated_cost_usd: Optional[float]
    tokens_used: Optional[int]
    error_message: Optional[str]
