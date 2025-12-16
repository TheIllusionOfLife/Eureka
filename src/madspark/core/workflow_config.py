"""Shared workflow configuration for CLI and web interfaces.

This module provides a unified way to build workflow parameters,
ensuring consistency between CLI and web interfaces.
"""

from typing import Any, Dict, List, Optional

# Try importing TemperatureManager with fallback
try:
    from madspark.utils.temperature_control import TemperatureManager
except ImportError:
    TemperatureManager = None  # type: ignore


class WorkflowConfig:
    """Shared workflow configuration builder.

    This class provides static methods to build workflow parameters
    that are consistent between CLI and web interfaces.

    IMPORTANT: The reasoning_engine parameter is intentionally NOT included.
    Let async_coordinator create its own engine with the router for proper
    batch operation support.
    """

    @staticmethod
    def build_workflow_params(
        topic: str,
        context: str = "",
        num_candidates: int = 3,
        temperature_manager: Optional[Any] = None,
        enable_novelty_filter: bool = True,
        novelty_threshold: float = 0.3,
        verbose: bool = False,
        enhanced_reasoning: bool = True,
        multi_dimensional_eval: bool = True,
        logical_inference: bool = False,
        timeout: int = 1200,
        multimodal_files: Optional[List[str]] = None,
        multimodal_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build unified workflow parameters for async_coordinator.run_workflow().

        Args:
            topic: The main topic or question to explore
            context: Additional context for the topic
            num_candidates: Number of top candidate ideas to return
            temperature_manager: Temperature manager for controlling LLM creativity
            enable_novelty_filter: Whether to filter out similar ideas
            novelty_threshold: Similarity threshold for novelty filtering (0.0-1.0)
            verbose: Whether to enable verbose output
            enhanced_reasoning: Whether to enable enhanced reasoning with advocacy/skepticism
            multi_dimensional_eval: Whether to enable multi-dimensional evaluation
            logical_inference: Whether to enable logical inference analysis
            timeout: Timeout in seconds for the workflow
            multimodal_files: List of file paths for multimodal inputs
            multimodal_urls: List of URLs for multimodal inputs

        Returns:
            Dictionary of keyword arguments for async_coordinator.run_workflow()

        Note:
            This method intentionally does NOT include reasoning_engine.
            The async_coordinator will create its own engine with the router,
            which is required for batch operations to work correctly.
        """
        # Create default temperature manager if not provided
        if temperature_manager is None and TemperatureManager is not None:
            temperature_manager = TemperatureManager()

        return {
            "topic": topic,
            "context": context,
            "num_top_candidates": num_candidates,
            "enable_novelty_filter": enable_novelty_filter,
            "novelty_threshold": novelty_threshold,
            "temperature_manager": temperature_manager,
            "verbose": verbose,
            "enhanced_reasoning": enhanced_reasoning,
            "multi_dimensional_eval": multi_dimensional_eval,
            "logical_inference": logical_inference,
            "timeout": timeout,
            "multimodal_files": multimodal_files,
            "multimodal_urls": multimodal_urls,
            # NOTE: reasoning_engine is intentionally NOT included
            # Let async_coordinator create it with the router
        }
