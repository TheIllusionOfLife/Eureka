"""Async Coordinator for Mad Spark Multi-Agent Workflow - Phase 2.3

This module provides async execution capabilities for concurrent agent processing,
improving performance by running multiple agent calls in parallel.
"""
import asyncio
import atexit
import concurrent.futures
import logging
from typing import List, Optional, Callable, Awaitable

from .coordinator import (
    EvaluatedIdea,
    CandidateData
)
from .batch_operations_base import BatchOperationsBase
from .workflow_orchestrator import WorkflowOrchestrator
from ..utils.utils import parse_json_with_fallback, validate_evaluation_json
from ..utils.novelty_filter import NoveltyFilter
from ..utils.temperature_control import TemperatureManager
from .enhanced_reasoning import ReasoningEngine
from ..utils.logical_inference_engine import InferenceType
from ..utils.cache_manager import CacheManager
from ..utils.constants import (
    DEFAULT_IDEA_TEMPERATURE,
    DEFAULT_EVALUATION_TEMPERATURE,
    DEFAULT_ADVOCACY_TEMPERATURE,
    DEFAULT_SKEPTICISM_TEMPERATURE,
    LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD
)
from ..utils.compat_imports import import_agent_retry_wrappers

logger = logging.getLogger(__name__)

# Type alias for progress callback
ProgressCallback = Callable[[str, float], Awaitable[None]]


_retry_wrappers = import_agent_retry_wrappers()
generate_ideas_with_retry = _retry_wrappers['generate_ideas_with_retry']
evaluate_ideas_with_retry = _retry_wrappers['evaluate_ideas_with_retry']
advocate_idea_with_retry = _retry_wrappers['advocate_idea_with_retry']
criticize_idea_with_retry = _retry_wrappers['criticize_idea_with_retry']
improve_idea_with_retry = _retry_wrappers['improve_idea_with_retry']

# Create a shared thread pool executor for all async functions
# This avoids the overhead of creating/destroying executors repeatedly
_SHARED_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Ensure threads are cleaned up on interpreter exit
def _shutdown_shared_executor():
    _SHARED_EXECUTOR.shutdown(wait=False)

atexit.register(_shutdown_shared_executor)


async def async_generate_ideas(topic: str, context: str, temperature: float = 0.9, cache_manager: Optional[CacheManager] = None, use_structured_output: bool = True) -> str:
    """Async wrapper for idea generation with retry logic.
    
    Runs the synchronous generate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    
    Args:
        topic: The main topic for idea generation
        context: Context or constraints for the ideas
        temperature: Controls randomness (0.0-1.0)
        cache_manager: Optional cache manager for result caching
        use_structured_output: Whether to use structured JSON output (default: True)
    
    Returns:
        Generated ideas as JSON string (if structured) or newline-separated text
    """
    # Check cache first
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        cached = await cache_manager.get_cached_agent_response("idea_generator", prompt)
        if cached:
            logger.debug("Using cached idea generation response")
            return cached
    
    loop = asyncio.get_running_loop()
    # Use shared executor to avoid hanging issues in some environments
    result = await loop.run_in_executor(
        _SHARED_EXECUTOR, 
        generate_ideas_with_retry,
        topic,
        context,
        temperature,
        use_structured_output
    )
    
    # Cache the result
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        await cache_manager.cache_agent_response("idea_generator", prompt, result)
    
    return result


async def async_evaluate_ideas(ideas: str, topic: str, context: str, temperature: float = 0.3, use_structured_output: bool = True) -> str:
    """Async wrapper for idea evaluation with retry logic.
    
    Runs the synchronous evaluate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        evaluate_ideas_with_retry,
        ideas,
        topic,
        context,
        temperature,
        use_structured_output
    )


async def async_advocate_idea(idea: str, evaluation: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
    """Async wrapper for idea advocacy with retry logic.
    
    Runs the synchronous advocate_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        advocate_idea_with_retry,
        idea,
        evaluation,
        topic,
        context,
        temperature,
        use_structured_output
    )


async def async_criticize_idea(idea: str, advocacy: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
    """Async wrapper for idea criticism/skepticism with retry logic.
    
    Runs the synchronous criticize_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        criticize_idea_with_retry,
        idea,
        advocacy,
        topic,
        context,
        temperature,
        use_structured_output
    )


async def async_improve_idea(
    original_idea: str, 
    critique: str, 
    advocacy_points: str, 
    skeptic_points: str, 
    topic: str,
    context: str,
    temperature: float = 0.9
) -> str:
    """Async wrapper for idea improvement with retry logic.
    
    Runs the synchronous improve_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _SHARED_EXECUTOR,
        improve_idea_with_retry,
        original_idea,
        critique,
        advocacy_points,
        skeptic_points,
        topic,
        context,
        temperature
    )


class AsyncCoordinator(BatchOperationsBase):
    """Async coordinator for managing concurrent agent execution."""
    
    def __init__(
        self,
        max_concurrent_agents: int = 10,
        progress_callback: Optional[ProgressCallback] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """Initialize the async coordinator.
        
        Args:
            max_concurrent_agents: Maximum number of concurrent agent calls
            progress_callback: Optional async callback for progress updates
            cache_manager: Optional cache manager for result caching
        """
        super().__init__()  # Initialize batch operations
        self.max_concurrent_agents = max_concurrent_agents
        self.progress_callback = progress_callback
        self.semaphore = asyncio.Semaphore(max_concurrent_agents)
        self.cache_manager = cache_manager
        
    async def _send_progress(self, message: str, progress: float):
        """Send progress update if callback is configured."""
        if self.progress_callback:
            await self.progress_callback(message, progress)
            
    async def _run_with_semaphore(self, coro):
        """Run a coroutine with semaphore limiting concurrency."""
        async with self.semaphore:
            return await coro

    @staticmethod
    def _normalize_candidate_fields(candidates: List[dict]) -> List[dict]:
        """Normalize field names for compatibility between orchestrator and async_coordinator.

        WorkflowOrchestrator uses "idea" field, AsyncCoordinator uses "text" field.
        This ensures both fields exist for compatibility during gradual migration.

        Pattern from Phase 3.2b (coordinator_batch.py:205-218).
        """
        for candidate in candidates:
            # Ensure both "text" and "idea" fields exist
            if "idea" in candidate and "text" not in candidate:
                candidate["text"] = candidate["idea"]
            elif "text" in candidate and "idea" not in candidate:
                candidate["idea"] = candidate["text"]

            # Add both "score" and "initial_score" if score exists
            if "score" in candidate and "initial_score" not in candidate:
                candidate["initial_score"] = candidate["score"]

            # Add both "critique" and "initial_critique" if critique exists
            if "critique" in candidate and "initial_critique" not in candidate:
                candidate["initial_critique"] = candidate["critique"]

        return candidates


    async def _process_candidates_with_batch_advocacy(
        self, candidates: List[EvaluatedIdea], topic: str, context: str, temperature: float
    ) -> List[EvaluatedIdea]:
        """Process all candidates with batch advocacy in a single API call.

        Phase 3.2c: Delegates to WorkflowOrchestrator.process_advocacy_async()

        Args:
            candidates: List of evaluated ideas
            topic: Overall topic for the ideas
            context: Additional constraints or criteria
            temperature: Generation temperature (unused, orchestrator manages temperatures)

        Returns:
            Updated candidates with advocacy data
        """
        try:
            # Phase 3.2c: Use WorkflowOrchestrator for centralized workflow logic
            from .workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(
                temperature_manager=None,  # Uses internal defaults
                reasoning_engine=None,
                verbose=False
            )

            updated_candidates, _ = await orchestrator.process_advocacy_async(
                candidates=candidates,
                topic=topic,
                context=context
            )

            return updated_candidates

        except Exception as e:
            logger.error(f"Batch advocate failed: {e}")
            # Fallback: mark all as N/A
            for candidate in candidates:
                candidate["advocacy"] = "N/A (Batch advocate failed)"
            return candidates
    
    async def _process_candidates_with_batch_skepticism(
        self, candidates: List[EvaluatedIdea], topic: str, context: str, temperature: float
    ) -> List[EvaluatedIdea]:
        """Process all candidates with batch skepticism in a single API call.

        Phase 3.2c: Delegates to WorkflowOrchestrator.process_skepticism_async()
        """
        try:
            # Phase 3.2c: Use WorkflowOrchestrator for centralized workflow logic
            from .workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(
                temperature_manager=None,  # Uses internal defaults
                reasoning_engine=None,
                verbose=False
            )

            updated_candidates, _ = await orchestrator.process_skepticism_async(
                candidates=candidates,
                topic=topic,
                context=context
            )

            return updated_candidates

        except Exception as e:
            logger.error(f"Batch skeptic failed: {e}")
            # Fallback: mark all as N/A
            for candidate in candidates:
                candidate["skepticism"] = "N/A (Batch skeptic failed)"
            return candidates
    
    async def _process_candidates_with_batch_improvement(
        self, candidates: List[EvaluatedIdea], topic: str, context: str, temperature: float
    ) -> List[EvaluatedIdea]:
        """Process all candidates with batch improvement in a single API call.

        Phase 3.2c: Delegates to WorkflowOrchestrator.improve_ideas_async()
        """
        try:
            # Phase 3.2c: Use WorkflowOrchestrator for centralized workflow logic
            from .workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(
                temperature_manager=None,  # Uses internal defaults
                reasoning_engine=None,
                verbose=False
            )

            updated_candidates, _ = await orchestrator.improve_ideas_async(
                candidates=candidates,
                topic=topic,
                context=context
            )

            return updated_candidates

        except Exception as e:
            logger.error(f"Batch improvement failed: {e}")
            # Fallback: use original ideas
            for candidate in candidates:
                candidate["improved_idea"] = candidate["text"]
            return candidates
    
    async def process_candidates_parallel_advocacy_skepticism(
        self,
        candidates: List[EvaluatedIdea],
        topic: str,
        context: str,
        advocacy_temp: float,
        skepticism_temp: float,
        timeout: float = 60
    ) -> List[EvaluatedIdea]:
        """Process advocacy and skepticism in parallel for better performance.
        
        Args:
            candidates: List of evaluated ideas
            topic: Overall topic for the ideas
            context: Additional constraints or criteria
            advocacy_temp: Temperature for advocacy
            skepticism_temp: Temperature for skepticism
            timeout: Timeout for parallel operations
            
        Returns:
            Updated candidates with advocacy and skepticism data
        """
        # Create tasks for parallel execution
        advocacy_task = asyncio.create_task(
            self._process_candidates_with_batch_advocacy(
                candidates.copy(),  # Copy to avoid race conditions
                topic,
                context,
                advocacy_temp
            )
        )
        
        skepticism_task = asyncio.create_task(
            self._process_candidates_with_batch_skepticism(
                candidates.copy(),  # Copy to avoid race conditions
                topic,
                context,
                skepticism_temp
            )
        )
        
        try:
            # Wait for both tasks with timeout
            advocacy_results, skepticism_results = await asyncio.wait_for(
                asyncio.gather(advocacy_task, skepticism_task, return_exceptions=True),
                timeout=timeout
            )
            
            # Handle advocacy results
            if isinstance(advocacy_results, Exception):
                logger.error(f"Advocacy task failed: {advocacy_results}")
                # Apply fallback
                for candidate in candidates:
                    candidate["advocacy"] = "N/A (Advocacy failed)"
            else:
                # Copy advocacy results to main candidates
                for i, candidate in enumerate(candidates):
                    if i < len(advocacy_results):
                        candidate["advocacy"] = advocacy_results[i].get("advocacy", "N/A")
            
            # Handle skepticism results
            if isinstance(skepticism_results, Exception):
                logger.error(f"Skepticism task failed: {skepticism_results}")
                # Apply fallback
                for candidate in candidates:
                    candidate["skepticism"] = "N/A (Skepticism failed)"
            else:
                # Copy skepticism results to main candidates
                for i, candidate in enumerate(candidates):
                    if i < len(skepticism_results):
                        candidate["skepticism"] = skepticism_results[i].get("skepticism", "N/A")
            
            return candidates
            
        except asyncio.TimeoutError:
            logger.error(f"Parallel operations timed out after {timeout} seconds")
            # Cancel pending tasks
            advocacy_task.cancel()
            skepticism_task.cancel()
            raise
    
    async def process_candidates_parallel_improvement_evaluation(
        self,
        candidates: List[EvaluatedIdea],
        topic: str,
        context: str,
        idea_temp: float,
        eval_temp: float
    ) -> List[EvaluatedIdea]:
        """Process improvement and re-evaluation with proper dependencies.
        
        Improvement must complete before re-evaluation starts, but both
        can leverage batch processing for efficiency.
        
        Args:
            candidates: List of candidates with advocacy and skepticism
            topic: Overall topic
            context: Constraints/criteria  
            idea_temp: Temperature for improvement
            eval_temp: Temperature for evaluation
            
        Returns:
            Updated candidates with improvements and re-evaluation scores
        """
        # Step 1: Improvement (depends on advocacy/skepticism being complete)
        candidates = await self._process_candidates_with_batch_improvement(
            candidates, topic, context, idea_temp
        )
        
        # Step 2: Re-evaluation (depends on improvement being complete)
        # Collect improved ideas for re-evaluation
        improved_ideas = []
        for candidate in candidates:
            improved_idea = candidate.get("improved_idea", candidate["text"])
            improved_ideas.append(improved_idea)
        
        improved_ideas_text = "\n\n".join(improved_ideas)
        
        try:
            # Single API call for all re-evaluations with original context
            re_eval_output = await async_evaluate_ideas(
                ideas=improved_ideas_text,
                topic=topic,
                context=context,  # Use original context to avoid bias
                temperature=eval_temp,
                use_structured_output=True
            )
            
            # Parse re-evaluations
            import json
            re_eval_results = json.loads(re_eval_output)
            
            # Update candidates with re-evaluation scores
            for i, candidate in enumerate(candidates):
                if i < len(re_eval_results):
                    candidate["improved_score"] = re_eval_results[i].get("score", 0)
                    candidate["improved_critique"] = re_eval_results[i].get(
                        "comment", "No critique available"
                    )
                else:
                    candidate["improved_score"] = candidate["score"]
                    candidate["improved_critique"] = "Re-evaluation unavailable"
                    
        except Exception as e:
            logger.error(f"Re-evaluation failed: {e}")
            # Fallback: use original scores
            for candidate in candidates:
                candidate["improved_score"] = candidate["score"]
                candidate["improved_critique"] = "Re-evaluation failed"
        
        return candidates
    
    async def _process_candidates_with_batch_advocacy_safe(
        self, candidates: List[EvaluatedIdea], topic: str, context: str, temperature: float
    ) -> List[EvaluatedIdea]:
        """Process candidates with batch advocacy, with fallback on error."""
        try:
            return await self._process_candidates_with_batch_advocacy(
                candidates, topic, context, temperature
            )
        except Exception as e:
            logger.error(f"Batch advocacy failed, using fallback: {e}")
            # Provide fallback advocacy for all candidates
            for candidate in candidates:
                candidate["advocacy"] = (
                    f"This idea shows strong potential in addressing {topic}. "
                    "Key strengths include practical implementation approach "
                    f"and alignment with {context}."
                )
            return candidates
    
    async def _run_batch_advocacy(
        self, candidates: List[EvaluatedIdea], topic: str, context: str, temperature: float
    ):
        """Run batch advocacy operation."""
        return await self._process_candidates_with_batch_advocacy(
            candidates, topic, context, temperature
        )
    
    async def _run_batch_logical_inference(
        self, 
        ideas: List[str], 
        topic: str, 
        context: str,
        analysis_type: InferenceType = InferenceType.FULL
    ):
        """
        Run batch logical inference operation using the actual inference engine.
        
        This method reduces API calls from O(N) to O(1) by processing all ideas
        in a single batch request to the logical inference engine.
        
        Args:
            ideas: List of idea strings to analyze
            topic: Original topic
            context: Constraints and requirements
            analysis_type: Type of logical analysis to perform
            
        Returns:
            List of InferenceResult objects with confidence scores and analysis
        """
        if not ideas:
            return []
        
        # Check if reasoning engine is available
        if not hasattr(self, 'reasoning_engine') or not self.reasoning_engine:
            logger.warning("No reasoning engine available for batch logical inference")
            return []
        
        if not hasattr(self.reasoning_engine, 'logical_inference_engine') or not self.reasoning_engine.logical_inference_engine:
            logger.warning("Logical inference engine not available, returning empty results")
            return []
        
        try:
            # Run batch logical inference - this is the key optimization
            # Single API call processes all ideas at once
            inference_results = await asyncio.to_thread(
                self.reasoning_engine.logical_inference_engine.analyze_batch,
                ideas,
                topic,
                context,
                analysis_type
            )
            
            return inference_results
            
        except Exception as e:
            logger.error(f"Batch logical inference failed: {e}")
            return []
    
            
    async def run_workflow(
        self,
        topic: str,
        context: str,
        num_top_candidates: int = 2,
        enable_novelty_filter: bool = True,
        novelty_threshold: float = 0.8,
        temperature_manager: Optional[TemperatureManager] = None,
        verbose: bool = False,
        enhanced_reasoning: bool = False,
        multi_dimensional_eval: bool = False,
        logical_inference: bool = False,
        reasoning_engine: Optional[ReasoningEngine] = None,
        timeout: int = 1200
    ) -> List[CandidateData]:
        """Run the complete async workflow with timeout support.
        
        This is the async equivalent of run_multistep_workflow from coordinator.py
        with added timeout functionality.
        
        Args:
            ... (same as run_multistep_workflow)
            timeout: Maximum time allowed for the entire workflow in seconds
            
        Returns:
            List of CandidateData containing processed ideas with evaluations
            
        Raises:
            asyncio.TimeoutError: If the workflow exceeds the specified timeout
        """
        try:
            # Wrap the actual workflow in a timeout
            return await asyncio.wait_for(
                self._run_workflow_internal(
                    topic=topic,
                    context=context,
                    num_top_candidates=num_top_candidates,
                    enable_novelty_filter=enable_novelty_filter,
                    novelty_threshold=novelty_threshold,
                    temperature_manager=temperature_manager,
                    verbose=verbose,
                    enhanced_reasoning=enhanced_reasoning,
                    multi_dimensional_eval=multi_dimensional_eval,
                    logical_inference=logical_inference,
                    reasoning_engine=reasoning_engine
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Workflow timed out after {timeout} seconds")
            await self._send_progress(f"Workflow timed out after {timeout} seconds", 0.0)
            raise
            
    async def _run_workflow_internal(
        self,
        topic: str,
        context: str,
        num_top_candidates: int = 2,
        enable_novelty_filter: bool = True,
        novelty_threshold: float = 0.8,
        temperature_manager: Optional[TemperatureManager] = None,
        verbose: bool = False,
        enhanced_reasoning: bool = False,
        multi_dimensional_eval: bool = False,
        logical_inference: bool = False,
        reasoning_engine: Optional[ReasoningEngine] = None
    ) -> List[CandidateData]:
        """Internal workflow implementation without timeout wrapper."""
        # Define cache options upfront to avoid potential NameError
        cache_options = {
            "num_top_candidates": num_top_candidates,
            "enable_novelty_filter": enable_novelty_filter,
            "novelty_threshold": novelty_threshold,
            "enhanced_reasoning": enhanced_reasoning,
            "multi_dimensional_eval": multi_dimensional_eval,
            "logical_inference": logical_inference,
            "temperature": temperature_manager.get_overall_temperature() if temperature_manager else DEFAULT_IDEA_TEMPERATURE
        }
        
        # Check cache first if enabled
        if self.cache_manager:
            cached_result = await self.cache_manager.get_cached_workflow(
                topic, context, cache_options
            )
            
            if cached_result:
                await self._send_progress("Retrieved from cache", 1.0)
                return cached_result.get("candidates", [])
        
        # Track all tasks for cleanup in case of cancellation
        active_tasks = []
        
        try:
            await self._send_progress("Starting multi-agent workflow", 0.0)
            
            # Extract temperatures
            if temperature_manager:
                idea_temp = temperature_manager.get_temperature_for_stage('idea_generation')
                eval_temp = temperature_manager.get_temperature_for_stage('evaluation')
                advocacy_temp = temperature_manager.get_temperature_for_stage('advocacy')
                skepticism_temp = temperature_manager.get_temperature_for_stage('skepticism')
            else:
                idea_temp = DEFAULT_IDEA_TEMPERATURE
                eval_temp = DEFAULT_EVALUATION_TEMPERATURE
                advocacy_temp = DEFAULT_ADVOCACY_TEMPERATURE
                skepticism_temp = DEFAULT_SKEPTICISM_TEMPERATURE
                
            # Initialize enhanced reasoning if needed
            engine = None
            if enhanced_reasoning or multi_dimensional_eval or logical_inference:
                if reasoning_engine:
                    engine = reasoning_engine
                else:
                    # Create ReasoningEngine with proper config and GenAI client
                    try:
                        from madspark.agents.genai_client import get_genai_client
                        genai_client = get_genai_client()
                        config = {"use_logical_inference": logical_inference} if logical_inference else None
                        engine = ReasoningEngine(config=config, genai_client=genai_client)
                        logger.info(f"Created ReasoningEngine with logical_inference={logical_inference}")
                    except (ImportError, AttributeError, RuntimeError):
                        # Fallback to creating without genai_client
                        config = {"use_logical_inference": logical_inference} if logical_inference else None
                        engine = ReasoningEngine(config=config)

            # Phase 3.2c: Initialize WorkflowOrchestrator for centralized workflow logic
            orchestrator = WorkflowOrchestrator(
                temperature_manager=temperature_manager,
                reasoning_engine=engine,
                verbose=verbose
            )

            # Step 1: Generate Ideas (async) - Phase 3.2c: Using WorkflowOrchestrator
            await self._send_progress("Generating ideas...", 0.1)
            try:
                # Add timeout to idea generation to prevent hanging
                parsed_ideas, _ = await asyncio.wait_for(
                    orchestrator.generate_ideas_async(
                        topic=topic,
                        context=context,
                        num_ideas=10  # Default number of ideas to generate
                    ),
                    timeout=60.0  # 60 second timeout for initial idea generation
                )

                if not parsed_ideas:
                    logger.warning("No ideas were generated")
                    return []

                await self._send_progress(f"Generated {len(parsed_ideas)} ideas", 0.3)

            except asyncio.TimeoutError:
                logger.error("Idea generation timed out after 60 seconds")
                await self._send_progress("Idea generation timed out. Please try again.", 0.0)
                raise asyncio.TimeoutError("Idea generation timed out - please check your API configuration")
            except Exception as e:
                logger.error(f"Idea generation failed: {e}")
                await self._send_progress(f"Idea generation failed: {str(e)}", 0.0)
                raise
                
            # Step 1.5: Apply novelty filter if enabled
            if enable_novelty_filter:
                novelty_filter = NoveltyFilter(similarity_threshold=novelty_threshold)
                filtered_ideas = novelty_filter.get_novel_ideas(parsed_ideas)
                if len(filtered_ideas) < len(parsed_ideas):
                    logger.info(f"Novelty filter removed {len(parsed_ideas) - len(filtered_ideas)} duplicates")
                parsed_ideas = filtered_ideas
                
            # Step 2: Evaluate Ideas (async) - Phase 3.2c: Using WorkflowOrchestrator
            await self._send_progress("Evaluating ideas...", 0.4)
            try:
                # Delegate evaluation to orchestrator
                evaluated_ideas_data, _ = await asyncio.wait_for(
                    orchestrator.evaluate_ideas_async(
                        ideas=parsed_ideas,
                        topic=topic,
                        context=context
                    ),
                    timeout=30.0  # 30 second timeout for evaluation
                )

                # Normalize fields for compatibility (orchestrator uses "idea", async_coordinator uses "text")
                evaluated_ideas_data = self._normalize_candidate_fields(evaluated_ideas_data)

                # Add multi-dimensional evaluation if enabled
                if multi_dimensional_eval:
                    evaluated_ideas_data = await asyncio.wait_for(
                        orchestrator.add_multi_dimensional_evaluation_async(
                            candidates=evaluated_ideas_data,
                            topic=topic,
                            context=context
                        ),
                        timeout=45.0  # 45 second timeout for multi-dimensional eval
                    )

                # Sort and select top candidates
                evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True)
                top_candidates = evaluated_ideas_data[:num_top_candidates]

                await self._send_progress(f"Selected {len(top_candidates)} top candidates", 0.6)

            except asyncio.TimeoutError:
                logger.error("Evaluation timed out")
                await self._send_progress("Evaluation timed out. Please try again.", 0.0)
                raise
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                raise
            
            # Step 2.5: Batch Logical Inference Processing (if enabled)
            if logical_inference and engine and engine.logical_inference_engine:
                try:
                    await self._send_progress("Performing batch logical inference analysis...", 0.65)
                    logger.info(f"Starting batch logical inference for {len(top_candidates)} candidates")
                    
                    # Store engine in self for _run_batch_logical_inference to access
                    self.reasoning_engine = engine
                    
                    # Extract ideas from candidates for batch processing
                    ideas_for_inference = [candidate["text"] for candidate in top_candidates]
                    
                    # Use the batch logical inference method - key optimization: O(N) → O(1) API calls
                    batch_results = await self._run_batch_logical_inference(
                        ideas_for_inference,
                        topic,
                        context,
                        InferenceType.FULL
                    )
                    
                    # Add logical inference data to candidates
                    for i, (candidate, inference_result) in enumerate(zip(top_candidates, batch_results)):
                        if inference_result and hasattr(inference_result, 'confidence'):
                            confidence = getattr(inference_result, 'confidence', 0.0)
                            if confidence > LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD:
                                # Convert InferenceResult to dictionary for storage
                                candidate["logical_inference"] = {
                                    "confidence": inference_result.confidence,
                                    "inference": inference_result.conclusion,
                                    "inference_chain": inference_result.inference_chain,
                                    "improvements": inference_result.improvements
                                }
                                logger.info(f"Added logical inference data to candidate {i+1} with confidence {confidence}")
                            else:
                                logger.info(f"Skipped logical inference for candidate {i+1} due to low confidence ({confidence})")
                    
                    logger.info(f"Batch logical inference completed for {len(top_candidates)} candidates")
                    
                except Exception as e:
                    logger.warning(f"Batch logical inference failed: {e}")
                    # Continue without logical inference
                
            # Step 3: Process top candidates with complete feedback loop
            await self._send_progress(f"Processing {len(top_candidates)} candidates with complete feedback loop...", 0.7)
            final_candidates = await self.process_top_candidates(
                top_candidates,
                topic,
                context,
                advocacy_temp,
                skepticism_temp,
                idea_temp,
                eval_temp,
                active_tasks,
                multi_dimensional_eval,
                engine,
                enhanced_reasoning
            )
            
            await self._send_progress("Workflow completed successfully!", 1.0)
            
            # Cache the result if cache manager is available
            if self.cache_manager:
                # Reuse the cache_options from the beginning of the method
                await self.cache_manager.cache_workflow_result(
                    topic,
                    context,
                    cache_options,
                    {"candidates": final_candidates}
                )
            
            return final_candidates
            
        except asyncio.CancelledError:
            # Clean up any pending tasks
            logger.info("Workflow cancelled, cleaning up pending tasks...")
            await self._send_progress("Workflow cancelled by user", 0.0)
            for task in active_tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to complete cancellation
            await asyncio.gather(*active_tasks, return_exceptions=True)
            raise
        except asyncio.TimeoutError:
            logger.error("Workflow timed out")
            await self._send_progress("Workflow timed out", 0.0)
            raise
        except Exception as e:
            # Log the error with full details for debugging
            import traceback
            error_details = {
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            logger.error(f"Workflow failed with error: {error_details}")
            await self._send_progress(f"Workflow failed: {str(e)}", 0.0)
            raise
        
    async def process_top_candidates(
        self,
        candidates: List[EvaluatedIdea],
        topic: str,
        context: str,
        advocacy_temp: float = DEFAULT_ADVOCACY_TEMPERATURE,
        skepticism_temp: float = DEFAULT_SKEPTICISM_TEMPERATURE,
        idea_temp: float = DEFAULT_IDEA_TEMPERATURE,
        eval_temp: float = DEFAULT_EVALUATION_TEMPERATURE,
        active_tasks: Optional[List[asyncio.Task]] = None,
        multi_dimensional_eval: bool = False,
        reasoning_engine = None,
        enhanced_reasoning: bool = False
    ) -> List[CandidateData]:
        """Process top candidates with batch operations for efficiency.
        
        This method uses batch API calls to process all candidates at once,
        significantly reducing API calls and execution time.
        """
        await self._send_progress("Processing candidates with batch operations...", 0.7)
        
        # Step 1: Parallel Batch Advocacy and Skepticism Processing (only if enhanced_reasoning is enabled)
        if enhanced_reasoning:
            await self._send_progress("Running parallel advocacy and skepticism analysis...", 0.72)
            candidates = await self.process_candidates_parallel_advocacy_skepticism(
                candidates, topic, context, advocacy_temp, skepticism_temp
            )
        else:
            # Don't include advocacy/skepticism fields when enhanced reasoning is disabled
            # This ensures the frontend won't show empty sections
            pass
        
        # Step 2: Batch Improvement Processing (depends on advocacy/skepticism)
        await self._send_progress("Running batch idea improvement...", 0.78)
        candidates = await self._process_candidates_with_batch_improvement(
            candidates, topic, context, idea_temp
        )
        
        # Step 4: Batch Re-evaluation - Phase 3.2c: Using WorkflowOrchestrator
        await self._send_progress("Running batch re-evaluation...", 0.82)

        try:
            # Phase 3.2c: Use WorkflowOrchestrator for centralized workflow logic
            from .workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(
                temperature_manager=None,  # Uses internal defaults
                reasoning_engine=None,
                verbose=False
            )

            # Delegate re-evaluation to orchestrator
            updated_candidates, _ = await orchestrator.reevaluate_ideas_async(
                candidates=candidates,
                topic=topic,
                context=context  # Use original context to avoid bias
            )

            # Update candidates with improved scores and critiques
            # Note: orchestrator returns "improved_score" and "improved_critique" fields
            for i, updated in enumerate(updated_candidates):
                if i < len(candidates):
                    candidates[i]["improved_score"] = updated.get(
                        "improved_score",
                        updated.get("score", candidates[i]["score"])
                    )
                    candidates[i]["improved_critique"] = updated.get(
                        "improved_critique",
                        updated.get("critique", "N/A")
                    )

        except Exception as e:
            logger.error(f"Batch re-evaluation failed: {e}")
            # Fallback: use original scores
            for candidate in candidates:
                candidate["improved_score"] = candidate["score"]
                candidate["improved_critique"] = "Re-evaluation failed"
        
        # Step 5: Build final candidate data - Phase 3.2c: Using WorkflowOrchestrator
        await self._send_progress("Building final results...", 0.88)

        # Phase 3.2c: Use WorkflowOrchestrator for centralized results building
        from .workflow_orchestrator import WorkflowOrchestrator
        orchestrator = WorkflowOrchestrator(
            temperature_manager=None,  # Uses internal defaults
            reasoning_engine=None,
            verbose=False
        )

        # Delegate results building to orchestrator
        final_candidates = orchestrator.build_final_results(candidates)

        # Preserve logical inference data if available (async-specific feature)
        for i, candidate in enumerate(candidates):
            if "logical_inference" in candidate and i < len(final_candidates):
                final_candidates[i]["logical_inference"] = candidate["logical_inference"]

        await self._send_progress(f"Completed batch processing of {len(final_candidates)} candidates", 0.9)

        return final_candidates
        
    async def _process_single_candidate(
        self,
        candidate: EvaluatedIdea,
        topic: str,
        advocacy_temp: float,
        skepticism_temp: float,
        idea_temp: float = 0.9,
        eval_temp: float = 0.3,
        context: str = "",
        multi_dimensional_eval: bool = False,
        reasoning_engine = None
    ) -> Optional[CandidateData]:
        """Process a single candidate with complete feedback loop: advocacy → skepticism → improvement → re-evaluation."""
        idea_text = candidate["text"]
        evaluation_detail = candidate["critique"]
        partial_failures = []
        
        # Steps 1 & 2: Run advocacy and skepticism in parallel
        # Both depend only on the original idea, so they can run concurrently
        advocacy_task = asyncio.create_task(
            asyncio.wait_for(
                self._run_with_semaphore(
                    async_advocate_idea(
                        idea=idea_text,
                        evaluation=evaluation_detail,
                        topic=topic,
                        context=context,
                        temperature=advocacy_temp,
                        use_structured_output=True
                    )
                ),
                timeout=30.0
            )
        )
        
        skepticism_task = asyncio.create_task(
            asyncio.wait_for(
                self._run_with_semaphore(
                    async_criticize_idea(
                        idea=idea_text,
                        advocacy=evaluation_detail,  # Use evaluation instead of advocacy output
                        topic=topic,
                        context=context,
                        temperature=skepticism_temp,
                        use_structured_output=True
                    )
                ),
                timeout=30.0
            )
        )
        
        # Wait for both to complete in parallel
        try:
            advocacy_output, skepticism_output = await asyncio.gather(
                advocacy_task, skepticism_task, return_exceptions=True
            )
        except Exception as e:
            logger.warning(f"Parallel advocacy/skepticism failed: {e}")
            advocacy_output = Exception("Parallel processing failed")
            skepticism_output = Exception("Parallel processing failed")
        
        # Handle advocacy result
        if isinstance(advocacy_output, asyncio.TimeoutError):
            logger.warning(f"Advocacy timed out for idea '{idea_text[:50]}...'. Using fallback.")
            advocacy_output = f"This idea shows strong potential in addressing {topic}. Key strengths include practical implementation approach and alignment with constraints."
            partial_failures.append({
                "stage": "advocacy",
                "error": "Timeout after 30 seconds",
                "error_type": "TimeoutError"
            })
        elif isinstance(advocacy_output, Exception):
            logger.warning(f"Advocacy failed for idea '{idea_text[:50]}...': {advocacy_output}")
            advocacy_fallback = "Advocacy not available due to error"
            partial_failures.append({
                "stage": "advocacy",
                "error": str(advocacy_output),
                "error_type": type(advocacy_output).__name__
            })
            advocacy_output = advocacy_fallback
        
        # Handle skepticism result  
        if isinstance(skepticism_output, asyncio.TimeoutError):
            logger.warning(f"Skepticism timed out for idea '{idea_text[:50]}...'. Using fallback.")
            skepticism_output = "Key concerns to consider: implementation complexity, resource requirements, and scalability challenges. Further analysis needed for practical deployment."
            partial_failures.append({
                "stage": "skepticism",
                "error": "Timeout after 30 seconds",
                "error_type": "TimeoutError"
            })
        elif isinstance(skepticism_output, Exception):
            logger.warning(f"Skepticism failed for idea '{idea_text[:50]}...': {skepticism_output}")
            skepticism_fallback = "Skepticism not available due to error"
            partial_failures.append({
                "stage": "skepticism",
                "error": str(skepticism_output),
                "error_type": type(skepticism_output).__name__
            })
            skepticism_output = skepticism_fallback

        # Step 3: Generate Improved Idea
        improved_idea_text = ""
        improved_score = 0.0
        improved_critique = ""
        
        try:
            logger.info(f"Improving idea based on feedback: '{idea_text[:50]}...'")
            improved_idea_text = await asyncio.wait_for(
                self._run_with_semaphore(
                    async_improve_idea(
                        original_idea=idea_text,
                        critique=evaluation_detail,
                        advocacy_points=advocacy_output,
                        skeptic_points=skepticism_output,
                        topic=topic,
                        context=context,
                        temperature=idea_temp
                    )
                ),
                timeout=45.0  # 45 second timeout for improvement (longer due to complexity)
            )
        except asyncio.TimeoutError:
            logger.warning(f"Idea improvement timed out for '{idea_text[:50]}...'. Using fallback improvement.")
            improved_idea_text = f"Enhanced: {idea_text}\n\nOptimizations based on feedback:\n- Improved feasibility and implementation approach\n- Better resource utilization\n- Enhanced scalability and user experience"
            partial_failures.append({
                "stage": "improvement",
                "error": "Timeout after 45 seconds",
                "error_type": "TimeoutError"
            })
        except Exception as e:
            logger.warning(f"Idea improvement failed for '{idea_text[:50]}...': {e}")
            improved_idea_text = idea_text  # Fallback to original
            partial_failures.append({
                "stage": "improvement",
                "error": str(e),
                "error_type": type(e).__name__
            })

        # Step 4: Re-evaluate Improved Idea
        if improved_idea_text and improved_idea_text != idea_text:
            try:
                # Call critic with improved idea using original context
                
                # Create parallel tasks for standard and multi-dimensional evaluation
                standard_eval_task = asyncio.create_task(
                    asyncio.wait_for(
                        self._run_with_semaphore(
                            async_evaluate_ideas(
                                ideas=improved_idea_text,
                                topic=topic,
                                context=context,  # Use original context to avoid bias
                                temperature=eval_temp,
                                use_structured_output=True
                            )
                        ),
                        timeout=30.0  # 30 second timeout for re-evaluation
                    )
                )
                
                multi_eval_task = None
                if multi_dimensional_eval and reasoning_engine:
                    multi_eval_task = asyncio.create_task(
                        asyncio.wait_for(
                            reasoning_engine.multi_evaluator.evaluate_idea(
                                idea=improved_idea_text,
                                context={"topic": topic, "context": context}
                            ),
                            timeout=30.0  # 30 second timeout for multi-dimensional evaluation
                        )
                    )
                
                # Wait for evaluations to complete in parallel
                if multi_eval_task:
                    improved_raw_eval, improved_multi_eval_result = await asyncio.gather(
                        standard_eval_task, multi_eval_task, return_exceptions=True
                    )
                else:
                    improved_raw_eval = await standard_eval_task
                    improved_multi_eval_result = None
                
                # Parse the evaluation based on format
                try:
                    # Try to parse as JSON first (structured output)
                    import json
                    improved_evaluations_json = json.loads(improved_raw_eval)
                    
                    # Extract evaluations from structured format
                    improved_evaluations = []
                    
                    # Handle different response formats (same logic as above)
                    if isinstance(improved_evaluations_json, list):
                        # Array of evaluation objects
                        for eval_obj in improved_evaluations_json:
                            if isinstance(eval_obj, dict):
                                improved_evaluations.append({
                                    "score": eval_obj.get("score", 0),
                                    "comment": eval_obj.get("comment", eval_obj.get("critique", "No comment available"))
                                })
                            else:
                                # Fallback for unexpected format
                                improved_evaluations.append({
                                    "score": 0,
                                    "comment": str(eval_obj)
                                })
                    elif isinstance(improved_evaluations_json, dict):
                        # Single evaluation object - wrap in array
                        improved_evaluations.append({
                            "score": improved_evaluations_json.get("score", 0),
                            "comment": improved_evaluations_json.get("comment", improved_evaluations_json.get("critique", "No comment available"))
                        })
                    else:
                        # Unexpected format - convert to string
                        improved_evaluations.append({
                            "score": 0,
                            "comment": str(improved_evaluations_json)
                        })
                        
                except (json.JSONDecodeError, TypeError, KeyError, AttributeError):
                    # Fall back to legacy parsing for backward compatibility
                    improved_evaluations = parse_json_with_fallback(improved_raw_eval, expected_count=1)
                
                improved_multi_eval_data = None
                
                # Handle parallel evaluation results
                if isinstance(improved_raw_eval, Exception):
                    logger.warning(f"Standard re-evaluation failed: {improved_raw_eval}")
                    improved_raw_eval = '{"evaluations": [{"score": 5.0, "comment": "Re-evaluation failed - using fallback score"}]}'
                
                if multi_eval_task and isinstance(improved_multi_eval_result, Exception):
                    logger.warning(f"Multi-dimensional re-evaluation failed: {improved_multi_eval_result}")
                    improved_multi_eval_result = None
                elif improved_multi_eval_result:
                    improved_multi_eval_data = improved_multi_eval_result
                
                if improved_evaluations:
                    eval_data = validate_evaluation_json(improved_evaluations[0])
                    improved_score = float(eval_data["score"])
                    improved_critique = eval_data["comment"]
                    
                    # Use multi-dimensional score if available (parallel result)
                    if improved_multi_eval_data:
                        improved_score = improved_multi_eval_data['weighted_score']
                        improved_critique = f"{improved_critique}\n\n📊 Multi-dimensional Analysis:\n{improved_multi_eval_data['evaluation_summary']}"
                    
                    # Safeguard: If score decreased significantly, log warning
                    if improved_score < candidate["score"] - 1.0:
                        logger.warning(
                            f"Improved idea scored lower ({improved_score}) than original ({candidate['score']}). "
                            f"This suggests the improvement may have overcorrected."
                        )
                        improved_critique += f"\n\n⚠️ Note: Score decreased from {candidate['score']} to {improved_score}. The improvement may have overcorrected or lost key strengths."
                else:
                    # Fallback if parsing fails - estimate improvement
                    improved_score = min(float(candidate["score"]) + 0.5, 10.0)  # Small improvement
                    improved_critique = "Re-evaluation parsing failed - estimated improvement applied"
                    logger.warning("Re-evaluation parsing failed, using estimated improvement")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Re-evaluation timed out for improved idea '{idea_text[:50]}...'. Using estimated score.")
                improved_score = min(float(candidate["score"]) + 0.3, 10.0)  # Conservative improvement
                improved_critique = "Re-evaluation timed out - estimated improvement based on feedback integration"
                partial_failures.append({
                    "stage": "re-evaluation",
                    "error": "Timeout after 30 seconds",
                    "error_type": "TimeoutError"
                })
            except Exception as e:
                logger.warning(f"Re-evaluation failed for improved idea '{idea_text[:50]}...': {e}")
                improved_score = min(float(candidate["score"]) + 0.2, 10.0)  # Minimal improvement
                improved_critique = "Re-evaluation failed - estimated improvement based on feedback"
                partial_failures.append({
                    "stage": "re-evaluation",
                    "error": str(e),
                    "error_type": type(e).__name__
                })
        else:
            # No improvement generated, use original values
            improved_idea_text = idea_text
            improved_score = float(candidate["score"])
            improved_critique = evaluation_detail

        # Calculate score delta
        score_delta = improved_score - candidate["score"]
        
        # Determine if improvement is meaningful
        from ..utils.text_similarity import is_meaningful_improvement
        from ..utils.constants import (
            MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )
        
        is_meaningful, similarity_score = is_meaningful_improvement(
            idea_text,
            improved_idea_text,
            score_delta,
            similarity_threshold=MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            score_delta_threshold=MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )
        
        logger.info(f"Finished processing for: {idea_text[:50]}...")
        if improved_idea_text != idea_text:
            logger.info(f"Score change: {candidate['score']}/10 → {improved_score}/10 (Δ{score_delta:+.1f})")
            
        # Build the final candidate data with complete feedback loop
        result = {
            "idea": idea_text,
            "initial_score": candidate["score"],
            "initial_critique": evaluation_detail,
            "advocacy": advocacy_output,
            "skepticism": skepticism_output,
            "improved_idea": improved_idea_text,
            "improved_score": improved_score,
            "improved_critique": improved_critique,
            "score_delta": score_delta,
            "is_meaningful_improvement": is_meaningful,
            "similarity_score": similarity_score
        }
        
        # Add multi-dimensional evaluation if present
        if "multi_dimensional_evaluation" in candidate:
            result["multi_dimensional_evaluation"] = candidate["multi_dimensional_evaluation"]
            
        # Add improved multi-dimensional evaluation if available
        if 'improved_multi_eval_data' in locals() and improved_multi_eval_data:
            result["improved_multi_dimensional_evaluation"] = improved_multi_eval_data
        
        # Add logical inference data if present
        if "logical_inference" in candidate:
            result["logical_inference"] = candidate["logical_inference"]
        
        # Only include partial_failures if there were any
        if partial_failures:
            result["partial_failures"] = partial_failures
            
        return result


async def run_async_workflow(
    topic: str,
    context: str,
    num_top_candidates: int = 2,
    enable_novelty_filter: bool = True,
    novelty_threshold: float = 0.8,
    temperature_manager: Optional[TemperatureManager] = None,
    verbose: bool = False,
    enhanced_reasoning: bool = False,
    multi_dimensional_eval: bool = False,
    logical_inference: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None,
    progress_callback: Optional[ProgressCallback] = None,
    max_concurrent_agents: int = 10
) -> List[CandidateData]:
    """Convenience function to run the async workflow.
    
    This is the main entry point for async execution, equivalent to
    run_multistep_workflow but with async/parallel execution.
    """
    coordinator = AsyncCoordinator(
        max_concurrent_agents=max_concurrent_agents,
        progress_callback=progress_callback
    )
    
    return await coordinator.run_workflow(
        topic=topic,
        context=context,
        num_top_candidates=num_top_candidates,
        enable_novelty_filter=enable_novelty_filter,
        novelty_threshold=novelty_threshold,
        temperature_manager=temperature_manager,
        verbose=verbose,
        enhanced_reasoning=enhanced_reasoning,
        multi_dimensional_eval=multi_dimensional_eval,
        logical_inference=logical_inference,
        reasoning_engine=reasoning_engine
    )


# Example usage
if __name__ == "__main__":
    async def main():
        """Example async workflow execution."""
        logging.basicConfig(level=logging.INFO)
        
        # Example progress callback
        async def progress_callback(message: str, progress: float):
            print(f"[{progress:.0%}] {message}")
            
        results = await run_async_workflow(
            topic="Sustainable Urban Living",
            context="Budget-friendly and community-focused",
            num_top_candidates=2,
            progress_callback=progress_callback
        )
        
        print("\nResults:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['idea']}")
            print(f"   Score: {result['initial_score']}/10")
            
    asyncio.run(main())