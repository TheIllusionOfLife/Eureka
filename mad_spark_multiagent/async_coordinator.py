"""Async Coordinator for Mad Spark Multi-Agent Workflow - Phase 2.3

This module provides async execution capabilities for concurrent agent processing,
improving performance by running multiple agent calls in parallel.
"""
import asyncio
import logging
from typing import List, Optional, Callable, TypedDict, Awaitable, Dict, Any

from coordinator import (
    EvaluatedIdea,
    CandidateData,
    parse_json_with_fallback,
    validate_evaluation_json
)
from agent_defs.idea_generator import generate_ideas
from agent_defs.critic import evaluate_ideas
from agent_defs.advocate import advocate_idea
from agent_defs.skeptic import criticize_idea
from utils import exponential_backoff_retry
from novelty_filter import NoveltyFilter
from temperature_control import TemperatureManager
from enhanced_reasoning import ReasoningEngine
from cache_manager import CacheManager, CacheConfig
from constants import (
    DEFAULT_IDEA_TEMPERATURE,
    DEFAULT_EVALUATION_TEMPERATURE,
    DEFAULT_ADVOCACY_TEMPERATURE,
    DEFAULT_SKEPTICISM_TEMPERATURE,
    LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


# Type alias for progress callback
ProgressCallback = Callable[[str, float], Awaitable[None]]


# Create retry-wrapped versions of agent functions
@exponential_backoff_retry(max_retries=3, initial_delay=2.0)
def generate_ideas_with_retry(topic: str, context: str, temperature: float) -> str:
    """Generate ideas with retry logic."""
    return generate_ideas(topic, context, temperature)


@exponential_backoff_retry(max_retries=3, initial_delay=2.0)
def evaluate_ideas_with_retry(ideas: str, criteria: str, context: str, temperature: float) -> str:
    """Evaluate ideas with retry logic."""
    return evaluate_ideas(ideas, criteria, context, temperature)


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def advocate_idea_with_retry(idea: str, evaluation: str, context: str, temperature: float) -> str:
    """Advocate for idea with retry logic."""
    return advocate_idea(idea, evaluation, context, temperature)


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def criticize_idea_with_retry(idea: str, advocacy: str, context: str, temperature: float) -> str:
    """Criticize idea with retry logic."""
    return criticize_idea(idea, advocacy, context, temperature)


async def async_generate_ideas(topic: str, context: str, temperature: float = 0.9, cache_manager: Optional[CacheManager] = None) -> str:
    """Async wrapper for idea generation with retry logic.
    
    Runs the synchronous generate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    # Check cache first
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        cached = await cache_manager.get_cached_agent_response("idea_generator", prompt)
        if cached:
            logger.debug("Using cached idea generation response")
            return cached
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, 
        generate_ideas_with_retry,
        topic,
        context,
        temperature
    )
    
    # Cache the result
    if cache_manager:
        prompt = f"Topic: {topic}\nContext: {context}"
        await cache_manager.cache_agent_response("idea_generator", prompt, result)
    
    return result


async def async_evaluate_ideas(ideas: str, criteria: str, context: str, temperature: float = 0.3) -> str:
    """Async wrapper for idea evaluation with retry logic.
    
    Runs the synchronous evaluate_ideas function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        evaluate_ideas_with_retry,
        ideas,
        criteria,
        context,
        temperature
    )


async def async_advocate_idea(idea: str, evaluation: str, context: str, temperature: float = 0.5) -> str:
    """Async wrapper for idea advocacy with retry logic.
    
    Runs the synchronous advocate_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        advocate_idea_with_retry,
        idea,
        evaluation,
        context,
        temperature
    )


async def async_criticize_idea(idea: str, advocacy: str, context: str, temperature: float = 0.5) -> str:
    """Async wrapper for idea criticism/skepticism with retry logic.
    
    Runs the synchronous criticize_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        criticize_idea_with_retry,
        idea,
        advocacy,
        context,
        temperature
    )


class AsyncCoordinator:
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
            
    async def run_workflow(
        self,
        theme: str,
        constraints: str,
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
        """Run the complete async workflow.
        
        This is the async equivalent of run_multistep_workflow from coordinator.py
        """
        # Check cache first if enabled
        if self.cache_manager:
            cache_options = {
                "num_top_candidates": num_top_candidates,
                "enable_novelty_filter": enable_novelty_filter,
                "novelty_threshold": novelty_threshold,
                "enhanced_reasoning": enhanced_reasoning,
                "multi_dimensional_eval": multi_dimensional_eval,
                "logical_inference": logical_inference,
                "temperature": temperature_manager.get_overall_temperature() if temperature_manager else DEFAULT_IDEA_TEMPERATURE
            }
            
            cached_result = await self.cache_manager.get_cached_workflow(
                theme, constraints, cache_options
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
                engine = reasoning_engine or ReasoningEngine()
                
            # Step 1: Generate Ideas (async)
            await self._send_progress("Generating ideas...", 0.1)
            try:
                raw_generated_ideas = await async_generate_ideas(
                    topic=theme,
                    context=constraints,
                    temperature=idea_temp,
                    cache_manager=self.cache_manager
                )
                
                parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]
                if not parsed_ideas:
                    logger.warning("No ideas were generated")
                    return []
                    
                await self._send_progress(f"Generated {len(parsed_ideas)} ideas", 0.3)
                
            except Exception as e:
                logger.error(f"Idea generation failed: {e}")
                raise
                
            # Step 1.5: Apply novelty filter if enabled
            if enable_novelty_filter:
                novelty_filter = NoveltyFilter(similarity_threshold=novelty_threshold)
                filtered_ideas = novelty_filter.get_novel_ideas(parsed_ideas)
                if len(filtered_ideas) < len(parsed_ideas):
                    logger.info(f"Novelty filter removed {len(parsed_ideas) - len(filtered_ideas)} duplicates")
                parsed_ideas = filtered_ideas
                
            # Step 2: Evaluate Ideas (async)
            await self._send_progress("Evaluating ideas...", 0.4)
            try:
                ideas_for_critic = "\n".join(parsed_ideas)
                raw_evaluations = await async_evaluate_ideas(
                    ideas=ideas_for_critic,
                    criteria=constraints,
                    context=theme,
                    temperature=eval_temp
                )
                
                # Parse evaluations
                parsed_evaluations = parse_json_with_fallback(
                    raw_evaluations,
                    expected_count=len(parsed_ideas)
                )
                
                # Build evaluated ideas list
                evaluated_ideas_data: List[EvaluatedIdea] = []
                for i, idea_text in enumerate(parsed_ideas):
                    if i < len(parsed_evaluations):
                        eval_data = validate_evaluation_json(parsed_evaluations[i])
                        score = eval_data["score"]
                        critique = eval_data["comment"]
                    else:
                        score = 0
                        critique = "Evaluation missing"
                        
                    # Enhanced reasoning: Apply multi-dimensional evaluation if enabled
                    if multi_dimensional_eval and engine:
                        try:
                            multi_eval_result = engine.multi_dimensional_evaluate(
                                idea=idea_text,
                                context={"theme": theme, "constraints": constraints},
                                prior_score=score
                            )
                            
                            # Use multi-dimensional score instead of simple score
                            score = multi_eval_result['weighted_score']
                            
                            # Enhance critique with multi-dimensional insights
                            critique = f"{critique}\n\n🧠 Enhanced Analysis:\n{multi_eval_result['evaluation_summary']}"
                            
                        except (AttributeError, KeyError, TypeError, ValueError) as e:
                            logger.warning(f"Multi-dimensional evaluation failed for idea {i}: {e}")
                            # Fall back to standard evaluation
                    
                    # Enhanced reasoning: Apply logical inference if enabled
                    if logical_inference and engine:
                        try:
                            # Create logical premises from the evaluation
                            premises = [
                                f"The idea '{idea_text}' addresses {theme}",
                                f"The constraints are: {constraints}",
                                f"The evaluation score is {score}/10"
                            ]
                            
                            # Apply logical inference
                            inference_result = engine.generate_inference_chain(
                                premises, 
                                f"Therefore, this idea is suitable for {theme}"
                            )
                            
                            if inference_result and inference_result.get('confidence_score', 0) > LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD:
                                # Enhance the critique with logical reasoning insights
                                critique = f"{critique}\n\n🔗 Logical Analysis:\nConfidence: {inference_result['confidence_score']:.2f}\nReasoning: {inference_result.get('inference_conclusion', 'Applied formal logical inference')}"
                                
                        except (AttributeError, KeyError, TypeError, ValueError) as e:
                            logger.warning(f"Logical inference failed for idea {i}: {e}")
                            # Continue without logical inference
                    
                    evaluated_ideas_data.append({
                        "text": idea_text,
                        "score": score,
                        "critique": critique
                    })
                    
                # Sort and select top candidates
                evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True)
                top_candidates = evaluated_ideas_data[:num_top_candidates]
                
                await self._send_progress(f"Selected {len(top_candidates)} top candidates", 0.6)
                
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                raise
                
            # Step 3: Process top candidates with advocacy and skepticism
            final_candidates = await self.process_top_candidates(
                top_candidates,
                theme,
                advocacy_temp,
                skepticism_temp,
                active_tasks
            )
            
            await self._send_progress("Workflow completed successfully!", 1.0)
            
            # Cache the result if cache manager is available
            if self.cache_manager:
                # Reuse the cache_options from the beginning of the method
                await self.cache_manager.cache_workflow_result(
                    theme,
                    constraints,
                    cache_options,
                    {"candidates": final_candidates}
                )
            
            return final_candidates
            
        except asyncio.CancelledError:
            # Clean up any pending tasks
            logger.info("Workflow cancelled, cleaning up pending tasks...")
            for task in active_tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to complete cancellation
            await asyncio.gather(*active_tasks, return_exceptions=True)
            raise
        except Exception as e:
            # Log the error but don't cancel other tasks unless it's a cancellation
            logger.error(f"Workflow failed with error: {e}")
            raise
        
    async def process_top_candidates(
        self,
        candidates: List[EvaluatedIdea],
        theme: str,
        advocacy_temp: float = DEFAULT_ADVOCACY_TEMPERATURE,
        skepticism_temp: float = DEFAULT_SKEPTICISM_TEMPERATURE,
        active_tasks: Optional[List[asyncio.Task]] = None
    ) -> List[CandidateData]:
        """Process top candidates with parallel advocacy and skepticism.
        
        This runs advocacy and skepticism for all candidates in parallel,
        significantly improving performance.
        """
        final_candidates: List[CandidateData] = []
        
        # Create tasks for all candidates
        tasks = []
        for candidate in candidates:
            task = asyncio.create_task(
                self._process_single_candidate(
                    candidate,
                    theme,
                    advocacy_temp,
                    skepticism_temp
                )
            )
            tasks.append(task)
            # Track in active_tasks if provided (for cancellation cleanup)
            if active_tasks is not None:
                active_tasks.append(task)
            
        # Run all tasks concurrently with semaphore limiting
        processed_candidates = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any None results or exceptions
        for result in processed_candidates:
            if isinstance(result, Exception):
                logger.error(f"Candidate processing failed with exception: {result}")
            elif result is not None:
                final_candidates.append(result)
        
        return final_candidates
        
    async def _process_single_candidate(
        self,
        candidate: EvaluatedIdea,
        theme: str,
        advocacy_temp: float,
        skepticism_temp: float
    ) -> Optional[CandidateData]:
        """Process a single candidate with advocacy and skepticism."""
        idea_text = candidate["text"]
        evaluation_detail = candidate["critique"]
        partial_failures = []
        
        # Run advocacy first, then skepticism (sequential for single candidate)
        advocacy_task = self._run_with_semaphore(
            async_advocate_idea(
                idea=idea_text,
                evaluation=evaluation_detail,
                context=theme,
                temperature=advocacy_temp
            )
        )
        
        # For skepticism, we need the advocacy result first
        # But we can start it as soon as advocacy completes
        try:
            advocacy_output = await advocacy_task
        except Exception as e:
            logger.warning(f"Advocacy failed for idea '{idea_text[:50]}...': {e}")
            advocacy_output = "Advocacy not available due to error"
            partial_failures.append({
                "stage": "advocacy",
                "error": str(e),
                "error_type": type(e).__name__
            })
            
        # Now run skepticism with the advocacy output
        try:
            skepticism_output = await self._run_with_semaphore(
                async_criticize_idea(
                    idea=idea_text,
                    advocacy=advocacy_output,
                    context=theme,
                    temperature=skepticism_temp
                )
            )
        except Exception as e:
            logger.warning(f"Skepticism failed for idea '{idea_text[:50]}...': {e}")
            skepticism_output = "Skepticism not available due to error"
            partial_failures.append({
                "stage": "skepticism",
                "error": str(e),
                "error_type": type(e).__name__
            })
            
        # Build the final candidate data with partial failure tracking
        result = {
            "idea": idea_text,
            "initial_score": candidate["score"],
            "initial_critique": evaluation_detail,
            "advocacy": advocacy_output,
            "skepticism": skepticism_output
        }
        
        # Only include partial_failures if there were any
        if partial_failures:
            result["partial_failures"] = partial_failures
            
        return result


async def run_async_workflow(
    theme: str,
    constraints: str,
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
        theme=theme,
        constraints=constraints,
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
            theme="Sustainable Urban Living",
            constraints="Budget-friendly and community-focused",
            num_top_candidates=2,
            progress_callback=progress_callback
        )
        
        print("\nResults:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['idea']}")
            print(f"   Score: {result['initial_score']}/10")
            
    asyncio.run(main())