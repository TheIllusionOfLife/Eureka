"""Workflow execution command handler."""

import argparse
import asyncio
import logging
import os
from typing import List, Dict, Any

from .base import CommandHandler, CommandResult

# Import MadSpark components with fallback for local development
try:
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.core.async_coordinator import AsyncCoordinator
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.cli.cli import determine_num_candidates
except ImportError:
    from coordinator import run_multistep_workflow
    from async_coordinator import AsyncCoordinator
    from cache_manager import CacheManager, CacheConfig
    from cli import determine_num_candidates


class WorkflowExecutor(CommandHandler):
    """Executes the main MadSpark workflow.

    This handler is responsible for:
    - Determining sync vs async execution mode
    - Executing the workflow via coordinator
    - Handling progress messages and cache management
    """

    def __init__(self, args: argparse.Namespace, logger: logging.Logger, temp_manager):
        """Initialize workflow executor.

        Args:
            args: Parsed command-line arguments
            logger: Logger instance
            temp_manager: Temperature manager instance from validation
        """
        super().__init__(args, logger)
        self.temp_manager = temp_manager

    def execute(self) -> CommandResult:
        """Execute workflow and return results.

        Returns:
            CommandResult with success status and results data
        """
        try:
            # Show progress message to user (unless in mock mode)
            if os.getenv("MADSPARK_MODE") != "mock":
                # Note: Currently agents use Gemini directly (Phase 1)
                # Phase 2 will route through madspark.llm for provider selection
                print("\n🚀 Generating ideas with AI model...")
                print("⏳ This may take 30-60 seconds for quality results...\n")

            # Determine number of candidates and execution mode
            num_candidates = determine_num_candidates(self.args)
            use_async = self._should_use_async(num_candidates)

            # Execute workflow
            if use_async:
                results = self._run_async_workflow(num_candidates)
            else:
                results = self._run_sync_workflow(num_candidates)

            # Validate results
            if not results:
                self.log_error("No ideas were generated")
                print("No ideas were generated. Check the logs for details.")
                return CommandResult(success=False, exit_code=1, message="No results generated")

            return CommandResult(success=True, data=results)

        except Exception as e:
            self.log_error(f"Workflow execution failed: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))

    def _should_use_async(self, num_candidates: int) -> bool:
        """Determine if async execution should be used.

        Args:
            num_candidates: Number of candidates to generate

        Returns:
            True if async execution should be used
        """
        # Auto-enable async for multiple ideas or if explicitly requested
        explicit_async = hasattr(self.args, 'async') and getattr(self.args, 'async')
        return explicit_async or (num_candidates > 1)

    def _run_sync_workflow(self, num_candidates: int) -> List[Dict[str, Any]]:
        """Execute workflow synchronously.

        Args:
            num_candidates: Number of candidates to generate

        Returns:
            List of workflow results
        """
        self.log_info("Using synchronous execution")

        workflow_kwargs = self._build_workflow_kwargs(num_candidates)
        return run_multistep_workflow(**workflow_kwargs)

    def _run_async_workflow(self, num_candidates: int) -> List[Dict[str, Any]]:
        """Execute workflow asynchronously.

        Args:
            num_candidates: Number of candidates to generate

        Returns:
            List of workflow results
        """
        if num_candidates > 1:
            self.log_info(f"Auto-enabling async mode for {num_candidates} ideas (estimated time: up to 5 minutes)")
            print(f"⚡ Processing {num_candidates} ideas in parallel for faster results...")
        else:
            self.log_info("Using async execution for better performance")

        return asyncio.run(self._run_async_workflow_impl(num_candidates))

    async def _run_async_workflow_impl(self, num_candidates: int):
        """Async implementation of workflow execution.

        Args:
            num_candidates: Number of candidates to generate

        Returns:
            List of workflow results
        """
        # Initialize cache manager if enabled
        cache_manager = None
        if hasattr(self.args, 'enable_cache') and self.args.enable_cache:
            cache_config = CacheConfig(
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                ttl_seconds=int(os.getenv("CACHE_TTL", "3600"))
            )
            cache_manager = CacheManager(cache_config)
            await cache_manager.initialize()
            self.log_info("Cache enabled for async execution")

        # Progress callback for user feedback during multiple ideas processing
        async def progress_callback(message: str, progress: float):
            if num_candidates > 1:
                print(f"[{progress:.0%}] {message}")

        # Create async coordinator
        async_coordinator = AsyncCoordinator(
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
            progress_callback=progress_callback if num_candidates > 1 else None,
            cache_manager=cache_manager
        )

        try:
            workflow_kwargs = self._build_workflow_kwargs(num_candidates)
            return await async_coordinator.run_workflow(**workflow_kwargs)
        finally:
            if cache_manager:
                await cache_manager.close()

    def _build_workflow_kwargs(self, num_candidates: int) -> Dict[str, Any]:
        """Build workflow arguments dictionary.

        Args:
            num_candidates: Number of candidates to generate

        Returns:
            Dictionary of workflow keyword arguments
        """
        # Combine files and images into single list for multi-modal inputs
        files = getattr(self.args, 'multimodal_files', None) or []
        images = getattr(self.args, 'multimodal_images', None) or []
        multimodal_files = files + images

        return {
            "topic": self.args.theme,  # Map theme to topic for consistency
            "context": self.args.constraints,  # Map constraints to context for consistency
            "num_top_candidates": num_candidates,
            "enable_novelty_filter": not self.args.disable_novelty_filter,
            "novelty_threshold": self.args.similarity_threshold if self.args.similarity_threshold is not None else self.args.novelty_threshold,
            "temperature_manager": self.temp_manager,
            "verbose": self.args.verbose,
            "enhanced_reasoning": self.args.enhanced_reasoning,
            "multi_dimensional_eval": True,  # Always enabled as a core feature
            "logical_inference": self.args.logical_inference,
            "timeout": self.args.timeout,
            # Multi-modal inputs
            "multimodal_files": multimodal_files if multimodal_files else None,
            "multimodal_urls": getattr(self.args, 'multimodal_urls', None) or None,
        }
