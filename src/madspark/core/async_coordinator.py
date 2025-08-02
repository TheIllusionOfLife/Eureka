"""Async Coordinator for Mad Spark Multi-Agent Workflow - Phase 2.3

This module provides async execution capabilities for concurrent agent processing,
improving performance by running multiple agent calls in parallel.
"""
import asyncio
import logging
from typing import List, Optional, Callable, Awaitable

from .coordinator import (
    EvaluatedIdea,
    CandidateData
)
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

logger = logging.getLogger(__name__)


# Type alias for progress callback
ProgressCallback = Callable[[str, float], Awaitable[None]]


# Import retry-wrapped versions of agent functions from shared module
try:
    from madspark.utils.agent_retry_wrappers import (
        generate_ideas_with_retry,
        evaluate_ideas_with_retry,
        advocate_idea_with_retry,
        criticize_idea_with_retry,
        improve_idea_with_retry
    )
except ImportError:
    from ..utils.agent_retry_wrappers import (
        generate_ideas_with_retry,
        evaluate_ideas_with_retry,
        advocate_idea_with_retry,
        criticize_idea_with_retry,
        improve_idea_with_retry
    )


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
    result = await loop.run_in_executor(
        None, 
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


async def async_evaluate_ideas(ideas: str, criteria: str, context: str, temperature: float = 0.3, use_structured_output: bool = True) -> str:
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
        temperature,
        use_structured_output
    )


async def async_advocate_idea(idea: str, evaluation: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
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
        temperature,
        use_structured_output
    )


async def async_criticize_idea(idea: str, advocacy: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
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
        temperature,
        use_structured_output
    )


async def async_improve_idea(
    original_idea: str, 
    critique: str, 
    advocacy_points: str, 
    skeptic_points: str, 
    theme: str,
    temperature: float = 0.9,
    use_structured_output: bool = True
) -> str:
    """Async wrapper for idea improvement with retry logic.
    
    Runs the synchronous improve_idea function in a thread pool to avoid blocking.
    Includes exponential backoff retry for resilience.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        improve_idea_with_retry,
        original_idea,
        critique,
        advocacy_points,
        skeptic_points,
        theme,
        temperature,
        use_structured_output
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
        reasoning_engine: Optional[ReasoningEngine] = None,
        timeout: int = 600
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
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Workflow timed out after {timeout} seconds")
            await self._send_progress(f"Workflow timed out after {timeout} seconds", 0.0)
            raise
            
    async def _run_workflow_internal(
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
                
            # Step 1: Generate Ideas (async)
            await self._send_progress("Generating ideas...", 0.1)
            try:
                # Add timeout to idea generation to prevent hanging
                raw_generated_ideas = await asyncio.wait_for(
                    async_generate_ideas(
                        topic=theme,
                        context=constraints,
                        temperature=idea_temp,
                        cache_manager=self.cache_manager,
                        use_structured_output=True
                    ),
                    timeout=60.0  # 60 second timeout for initial idea generation
                )
                
                # Parse ideas based on format
                try:
                    # Try to parse as JSON first (structured output)
                    import json
                    ideas_json = json.loads(raw_generated_ideas)
                    
                    # Extract ideas from structured format
                    parsed_ideas = []
                    for idea_obj in ideas_json:
                        # Build a formatted idea string from the structured data
                        idea_number = idea_obj.get('idea_number')
                        title = idea_obj.get('title', 'Untitled')
                        description = idea_obj.get('description', 'No description provided')
                        
                        # Format based on whether we have an idea number
                        if idea_number:
                            idea_text = f"{idea_number}. {title}: {description}"
                        else:
                            idea_text = f"{title}: {description}"
                            
                        if 'key_features' in idea_obj and idea_obj['key_features']:
                            # Add key features as a formatted list
                            features = " Key features: " + ", ".join(idea_obj['key_features'])
                            idea_text += features
                        parsed_ideas.append(idea_text.strip())
                except (json.JSONDecodeError, TypeError):
                    # Fall back to text parsing for backward compatibility
                    parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]
                
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
                
            # Step 2: Evaluate Ideas (async)
            await self._send_progress("Evaluating ideas...", 0.4)
            try:
                ideas_for_critic = "\n".join(parsed_ideas)
                raw_evaluations = await async_evaluate_ideas(
                    ideas=ideas_for_critic,
                    criteria=constraints,
                    context=theme,
                    temperature=eval_temp,
                    use_structured_output=True
                )
                
                # Parse evaluations based on format
                try:
                    # Try to parse as JSON first (structured output)
                    import json
                    evaluations_json = json.loads(raw_evaluations)
                    
                    # Extract evaluations from structured format
                    parsed_evaluations = []
                    
                    # Handle different response formats
                    if isinstance(evaluations_json, list):
                        # Array of evaluation objects
                        for eval_obj in evaluations_json:
                            if isinstance(eval_obj, dict):
                                parsed_evaluations.append({
                                    "score": eval_obj.get("score", 0),
                                    "comment": eval_obj.get("comment", eval_obj.get("critique", "No comment available"))
                                })
                            else:
                                # Fallback for unexpected format
                                parsed_evaluations.append({
                                    "score": 0,
                                    "comment": str(eval_obj)
                                })
                    elif isinstance(evaluations_json, dict):
                        # Single evaluation object - wrap in array
                        parsed_evaluations.append({
                            "score": evaluations_json.get("score", 0),
                            "comment": evaluations_json.get("comment", evaluations_json.get("critique", "No comment available"))
                        })
                    else:
                        # Unexpected format - convert to string
                        parsed_evaluations.append({
                            "score": 0,
                            "comment": str(evaluations_json)
                        })
                        
                except (json.JSONDecodeError, TypeError, KeyError, AttributeError):
                    # Fall back to legacy parsing for backward compatibility
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
                    multi_eval_data = None
                    if multi_dimensional_eval and engine:
                        try:
                            multi_eval_result = engine.multi_evaluator.evaluate_idea(
                                idea=idea_text,
                                context={"theme": theme, "constraints": constraints}
                            )
                            
                            # Store the multi-dimensional evaluation data
                            multi_eval_data = multi_eval_result
                            
                            # Use multi-dimensional score instead of simple score
                            score = multi_eval_result['weighted_score']
                            
                            # Enhance critique with multi-dimensional insights
                            critique = f"{critique}\n\n🧠 Enhanced Analysis:\n{multi_eval_result['evaluation_summary']}"
                            
                        except (AttributeError, KeyError, TypeError, ValueError) as e:
                            logger.warning(f"Multi-dimensional evaluation failed for idea {i}: {e}")
                            # Fall back to standard evaluation
                    
                    # Enhanced reasoning: Apply logical inference if enabled
                    logical_inference_data = None
                    if logical_inference and engine and engine.logical_inference_engine:
                        try:
                            # Use the new LogicalInferenceEngine directly for better analysis
                            inference_engine = engine.logical_inference_engine
                            logger.info(f"Applying logical inference analysis to idea {i}")
                            
                            # Perform logical analysis on the idea
                            inference_result = inference_engine.analyze(
                                idea=idea_text,
                                theme=theme,
                                context=constraints,
                                analysis_type=InferenceType.FULL  # Use full analysis for comprehensive reasoning
                            )
                            
                            if inference_result.confidence > LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD:
                                # Store logical inference data separately
                                # Use the to_dict method to get all available data
                                logical_inference_data = inference_result.to_dict()
                                logger.info(f"Stored logical inference data for idea {i} with confidence {inference_result.confidence}")
                                
                        except (AttributeError, KeyError, TypeError, ValueError) as e:
                            logger.warning(f"Logical inference failed for idea {i}: {e}")
                            # Continue without logical inference
                    
                    # Build the evaluated idea data
                    evaluated_idea = {
                        "text": idea_text,
                        "score": score,
                        "critique": critique
                    }
                    
                    # Add multi-dimensional evaluation data if available
                    if multi_eval_data:
                        evaluated_idea["multi_dimensional_evaluation"] = multi_eval_data
                    
                    # Add logical inference data if available
                    if logical_inference_data:
                        evaluated_idea["logical_inference"] = logical_inference_data
                    
                    evaluated_ideas_data.append(evaluated_idea)
                    
                # Sort and select top candidates
                evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True)
                top_candidates = evaluated_ideas_data[:num_top_candidates]
                
                await self._send_progress(f"Selected {len(top_candidates)} top candidates", 0.6)
                
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                raise
                
            # Step 3: Process top candidates with complete feedback loop
            await self._send_progress(f"Processing {len(top_candidates)} candidates with complete feedback loop...", 0.7)
            final_candidates = await self.process_top_candidates(
                top_candidates,
                theme,
                constraints,
                advocacy_temp,
                skepticism_temp,
                idea_temp,
                eval_temp,
                active_tasks,
                multi_dimensional_eval,
                engine
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
        theme: str,
        constraints: str,
        advocacy_temp: float = DEFAULT_ADVOCACY_TEMPERATURE,
        skepticism_temp: float = DEFAULT_SKEPTICISM_TEMPERATURE,
        idea_temp: float = DEFAULT_IDEA_TEMPERATURE,
        eval_temp: float = DEFAULT_EVALUATION_TEMPERATURE,
        active_tasks: Optional[List[asyncio.Task]] = None,
        multi_dimensional_eval: bool = False,
        reasoning_engine = None
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
                    skepticism_temp,
                    idea_temp,
                    eval_temp,
                    constraints,
                    multi_dimensional_eval,
                    reasoning_engine
                )
            )
            tasks.append(task)
            # Track in active_tasks if provided (for cancellation cleanup)
            if active_tasks is not None:
                active_tasks.append(task)
            
        # Run all tasks concurrently with semaphore limiting
        await self._send_progress(f"Running complete feedback loop for {len(tasks)} candidates...", 0.8)
        try:
            # Add timeout to prevent entire candidate processing from hanging
            processed_candidates = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300.0  # 5 minute timeout for all candidate processing
            )
        except asyncio.TimeoutError:
            logger.error("Candidate processing timed out after 5 minutes")
            await self._send_progress("Candidate processing timed out - using partial results", 0.85)
            # Return partial results if any completed
            processed_candidates = []
            for task in tasks:
                if task.done() and not task.exception():
                    processed_candidates.append(task.result())
                else:
                    processed_candidates.append(None)
        
        # Filter out any None results or exceptions
        successful_candidates = 0
        for result in processed_candidates:
            if isinstance(result, Exception):
                logger.error(f"Candidate processing failed with exception: {result}")
            elif result is not None:
                final_candidates.append(result)
                successful_candidates += 1
        
        await self._send_progress(f"Completed processing {successful_candidates} candidates", 0.9)
        
        return final_candidates
        
    async def _process_single_candidate(
        self,
        candidate: EvaluatedIdea,
        theme: str,
        advocacy_temp: float,
        skepticism_temp: float,
        idea_temp: float = 0.9,
        eval_temp: float = 0.3,
        constraints: str = "",
        multi_dimensional_eval: bool = False,
        reasoning_engine = None
    ) -> Optional[CandidateData]:
        """Process a single candidate with complete feedback loop: advocacy → skepticism → improvement → re-evaluation."""
        idea_text = candidate["text"]
        evaluation_detail = candidate["critique"]
        partial_failures = []
        
        # Step 1: Run advocacy first
        try:
            advocacy_output = await asyncio.wait_for(
                self._run_with_semaphore(
                    async_advocate_idea(
                        idea=idea_text,
                        evaluation=evaluation_detail,
                        context=theme,
                        temperature=advocacy_temp,
                        use_structured_output=True
                    )
                ),
                timeout=30.0  # 30 second timeout for advocacy
            )
        except asyncio.TimeoutError:
            logger.warning(f"Advocacy timed out for idea '{idea_text[:50]}...'. Using fallback.")
            advocacy_output = f"This idea shows strong potential in addressing {theme}. Key strengths include practical implementation approach and alignment with constraints."
            partial_failures.append({
                "stage": "advocacy",
                "error": "Timeout after 30 seconds",
                "error_type": "TimeoutError"
            })
        except Exception as e:
            logger.warning(f"Advocacy failed for idea '{idea_text[:50]}...': {e}")
            advocacy_output = "Advocacy not available due to error"
            partial_failures.append({
                "stage": "advocacy",
                "error": str(e),
                "error_type": type(e).__name__
            })
            
        # Step 2: Run skepticism with the advocacy output
        try:
            skepticism_output = await asyncio.wait_for(
                self._run_with_semaphore(
                    async_criticize_idea(
                        idea=idea_text,
                        advocacy=advocacy_output,
                        context=theme,
                        temperature=skepticism_temp,
                        use_structured_output=True
                    )
                ),
                timeout=30.0  # 30 second timeout for skepticism
            )
        except asyncio.TimeoutError:
            logger.warning(f"Skepticism timed out for idea '{idea_text[:50]}...'. Using fallback.")
            skepticism_output = "Key concerns to consider: implementation complexity, resource requirements, and scalability challenges. Further analysis needed for practical deployment."
            partial_failures.append({
                "stage": "skepticism",
                "error": "Timeout after 30 seconds",
                "error_type": "TimeoutError"
            })
        except Exception as e:
            logger.warning(f"Skepticism failed for idea '{idea_text[:50]}...': {e}")
            skepticism_output = "Skepticism not available due to error"
            partial_failures.append({
                "stage": "skepticism",
                "error": str(e),
                "error_type": type(e).__name__
            })

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
                        theme=theme,
                        temperature=idea_temp,
                        use_structured_output=True
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
                # Call critic with improved idea
                improved_context = (
                    f"{theme}\n"
                    f"[This is an IMPROVED version that addresses previous concerns]\n"
                    f"Original score: {candidate['score']}/10\n"
                    f"Key improvements made:\n"
                    f"- Addressed skeptic's concerns about feasibility\n"
                    f"- Incorporated advocate's strengths\n"
                    f"- Applied critic's suggestions"
                )
                
                # Add timeout to prevent hanging
                improved_raw_eval = await asyncio.wait_for(
                    self._run_with_semaphore(
                        async_evaluate_ideas(
                            ideas=improved_idea_text,
                            criteria=constraints,
                            context=improved_context,
                            temperature=eval_temp,
                            use_structured_output=True
                        )
                    ),
                    timeout=30.0  # 30 second timeout for re-evaluation
                )
                
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
                
                if improved_evaluations:
                    eval_data = validate_evaluation_json(improved_evaluations[0])
                    improved_score = float(eval_data["score"])
                    improved_critique = eval_data["comment"]
                    
                    # Apply multi-dimensional evaluation to improved idea if enabled
                    if multi_dimensional_eval and reasoning_engine:
                        try:
                            # Re-evaluate with multi-dimensional analysis
                            improved_multi_eval_result = reasoning_engine.multi_evaluator.evaluate_idea(
                                idea=improved_idea_text,
                                context={"theme": theme, "constraints": constraints}
                            )
                            
                            # Store the improved multi-dimensional evaluation data
                            improved_multi_eval_data = improved_multi_eval_result
                            
                            # Use multi-dimensional score for improved idea
                            improved_score = improved_multi_eval_result['weighted_score']
                            
                            # Enhance critique with multi-dimensional insights
                            improved_critique = f"{improved_critique}\n\n🧠 Enhanced Analysis:\n{improved_multi_eval_result['evaluation_summary']}"
                            
                        except (AttributeError, KeyError, TypeError, ValueError) as e:
                            logger.warning(f"Multi-dimensional evaluation failed for improved idea: {e}")
                            # Continue with standard evaluation
                    
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