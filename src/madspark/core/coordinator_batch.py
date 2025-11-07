"""Batch-optimized coordinator for Mad Spark Multi-Agent Workflow.

This is a refactored version of the coordinator that uses batch API calls
to significantly reduce the number of API calls from O(N) to O(1) for
advocate, skeptic, and improvement processing.
"""
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from madspark.utils.batch_monitor import get_batch_monitor
from madspark.utils.errors import ValidationError

from madspark.core.types_and_logging import (
    CandidateData, log_verbose_step
)
from madspark.utils.text_similarity import is_meaningful_improvement
from madspark.utils.constants import (
    MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
    MEANINGFUL_IMPROVEMENT_SCORE_DELTA
)
from madspark.utils.temperature_control import TemperatureManager
from madspark.utils.novelty_filter import NoveltyFilter
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.utils.constants import DEFAULT_TIMEOUT_SECONDS
from madspark.core.workflow_orchestrator import WorkflowOrchestrator

# Import retry-wrapped versions and batch functions using compat helpers
from madspark.utils.compat_imports import (
    import_coordinator_batch_retry_wrappers,
    import_batch_functions
)

_retry_wrappers = import_coordinator_batch_retry_wrappers()
call_idea_generator_with_retry = _retry_wrappers['call_idea_generator_with_retry']
call_critic_with_retry = _retry_wrappers['call_critic_with_retry']

_batch_functions = import_batch_functions()
advocate_ideas_batch = _batch_functions['advocate_ideas_batch']
criticize_ideas_batch = _batch_functions['criticize_ideas_batch']
improve_ideas_batch = _batch_functions['improve_ideas_batch']


def run_multistep_workflow_batch(
    topic: str, 
    context: str, 
    num_top_candidates: int = 2,
    enable_reasoning: bool = True,
    multi_dimensional_eval: bool = False,
    temperature_manager: Optional[TemperatureManager] = None,
    novelty_filter: Optional[NoveltyFilter] = None,
    verbose: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> List[CandidateData]:
    """
    Batch-optimized version of the multi-agent workflow.
    
    Key optimization: Uses batch API calls for advocate, skeptic, and improvement
    processing, reducing API calls from O(N) to O(1) for these stages.
    
    Args:
        topic: Main topic/theme for idea generation
        context: Context/constraints for the ideas
        num_top_candidates: Number of top ideas to fully process
        enable_reasoning: Whether to use enhanced reasoning
        multi_dimensional_eval: Whether to use multi-dimensional evaluation
        temperature_manager: Optional temperature control
        novelty_filter: Optional novelty filtering
        verbose: Enable verbose logging
        reasoning_engine: Optional pre-initialized reasoning engine
        timeout: Maximum time allowed for the entire workflow in seconds
        
    Returns:
        List of fully processed candidate data
        
    Raises:
        TimeoutError: If the workflow exceeds the specified timeout
    """
    # Validate input parameters
    if not topic or not isinstance(topic, str) or topic.strip() == "":
        raise ValidationError("Topic must be a non-empty string")
    if context is None or not isinstance(context, str) or context.strip() == "":
        raise ValidationError("Context must be a non-empty string")
    
    # If timeout is specified and different from default, use ThreadPoolExecutor to enforce it
    if timeout is not None and timeout > 0 and timeout != DEFAULT_TIMEOUT_SECONDS:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _run_workflow_internal,
                topic, context, num_top_candidates, enable_reasoning,
                multi_dimensional_eval, temperature_manager, novelty_filter,
                verbose, reasoning_engine
            )
            try:
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                logging.error(f"Workflow timed out after {timeout} seconds")
                # Cancel the future if possible
                # Note: Cancellation may not interrupt already running operations
                future.cancel()
                raise TimeoutError(f"Workflow exceeded {timeout} second timeout")
    else:
        # Run without timeout
        return _run_workflow_internal(
            topic, context, num_top_candidates, enable_reasoning,
            multi_dimensional_eval, temperature_manager, novelty_filter,
            verbose, reasoning_engine
        )


def _run_workflow_internal(
    topic: str,
    context: str,
    num_top_candidates: int = 2,
    enable_reasoning: bool = True,
    multi_dimensional_eval: bool = False,
    temperature_manager: Optional[TemperatureManager] = None,
    novelty_filter: Optional[NoveltyFilter] = None,
    verbose: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None
) -> List[CandidateData]:
    """Internal workflow implementation using WorkflowOrchestrator.

    This function uses WorkflowOrchestrator for all workflow steps while
    preserving batch-specific features like novelty filtering.
    """
    final_candidates_data: List[CandidateData] = []

    # Initialize temperature manager
    if not temperature_manager:
        temperature_manager = TemperatureManager.from_base_temperature(0.7)

    # Initialize enhanced reasoning if needed
    engine = reasoning_engine
    if (enable_reasoning or multi_dimensional_eval) and engine is None:
        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            engine = ReasoningEngine(genai_client=genai_client)
        except (ImportError, AttributeError, RuntimeError):
            engine = ReasoningEngine()

    # Create WorkflowOrchestrator instance
    orchestrator = WorkflowOrchestrator(
        temperature_manager=temperature_manager,
        reasoning_engine=engine,
        verbose=verbose
    )

    # Get batch monitor for monitoring
    monitor = get_batch_monitor()

    # Step 1: Idea Generation using orchestrator
    parsed_ideas, _ = orchestrator.generate_ideas_with_monitoring(
        topic=topic,
        context=context,
        num_ideas=10,  # Generate 10 ideas initially
        monitor=monitor
    )

    if not parsed_ideas:
        logging.warning("No ideas were generated.")
        return []

    logging.info(f"Generated {len(parsed_ideas)} ideas")
    
    # Apply novelty filtering if enabled
    if novelty_filter:
        log_verbose_step("STEP 1.5: Novelty Filtering", 
                        f"🔍 Filtering {len(parsed_ideas)} ideas for novelty", 
                        verbose)
        
        filtered_ideas = novelty_filter.filter_ideas(parsed_ideas)
        novel_ideas = [fi.text for fi in filtered_ideas if fi.is_novel]
        
        if verbose:
            filtered_count = len(parsed_ideas) - len(novel_ideas)
            if filtered_count > 0:
                logging.info(f"Filtered out {filtered_count} non-novel ideas")
                for fi in filtered_ideas:
                    if not fi.is_novel:
                        logging.debug(
                            f"Filtered: {fi.text[:50]}... "
                            f"(similarity: {fi.similarity_score:.2f} to: {fi.similar_to[:50]}...)"
                        )
        
        # Use only novel ideas for evaluation
        parsed_ideas = novel_ideas
        
        if not parsed_ideas:
            logging.warning("All ideas were filtered out as non-novel.")
            return []
    
    # Step 2: Evaluate Ideas using orchestrator
    try:
        evaluated_ideas_data, _ = orchestrator.evaluate_ideas_with_monitoring(
            ideas=parsed_ideas,
            topic=topic,
            context=context,
            monitor=monitor
        )

        # Add field normalization for compatibility with rest of workflow
        # TODO: Technical debt - field normalization creates redundant fields
        # This compatibility layer maintains both "text"/"idea", "score"/"initial_score",
        # and "critique"/"initial_critique" pairs during gradual migration.
        # Future work: Unify data model to use single canonical field names.
        # Reference: gemini-code-assist review comment (PR #181)
        for idea_data in evaluated_ideas_data:
            # Ensure both "text" and "idea" fields exist
            idea_data["idea"] = idea_data.get("text", "")
            # Add both "score" and "initial_score"
            idea_data["initial_score"] = idea_data["score"]
            # Add both "critique" and "initial_critique"
            idea_data["initial_critique"] = idea_data["critique"]
            # Add context for information flow (re-evaluation bias prevention)
            idea_data["context"] = context

        # Sort and select top candidates
        evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = evaluated_ideas_data[:num_top_candidates]

        logging.info(f"Selected {len(top_candidates)} top candidates for further processing.")

    except ValidationError:
        raise
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        # Fallback handling
        top_candidates = [
            {"text": idea, "idea": idea, "critique": "N/A (Evaluation failed)",
             "initial_critique": "N/A", "score": 0, "initial_score": 0, "context": context}
            for idea in parsed_ideas[:num_top_candidates]
        ]

    if not top_candidates:
        logging.info("No candidates selected for processing.")
        return []
    
    # Step 2.5: Multi-Dimensional Evaluation using orchestrator
    if multi_dimensional_eval and orchestrator.reasoning_engine:
        top_candidates = orchestrator.add_multi_dimensional_evaluation_with_monitoring(
            candidates=top_candidates,
            topic=topic,
            context=context,
            monitor=monitor
        )
    
    # Step 3: Advocacy Processing using orchestrator
    top_candidates, _ = orchestrator.process_advocacy_with_monitoring(
        candidates=top_candidates,
        topic=topic,
        context=context,
        monitor=monitor
    )

    # Step 4: Skepticism Processing using orchestrator
    top_candidates, _ = orchestrator.process_skepticism_with_monitoring(
        candidates=top_candidates,
        topic=topic,
        context=context,
        monitor=monitor
    )
    
    # Step 5: Improvement Processing using orchestrator
    top_candidates, _ = orchestrator.improve_ideas_with_monitoring(
        candidates=top_candidates,
        topic=topic,
        context=context,
        monitor=monitor
    )
    
    # Step 6: Re-evaluation using orchestrator
    top_candidates, _ = orchestrator.reevaluate_ideas_with_monitoring(
        candidates=top_candidates,
        topic=topic,
        context=context,  # Use original context to avoid bias
        monitor=monitor
    )

    # Step 6.5: Multi-Dimensional Re-evaluation using orchestrator (if enabled)
    if multi_dimensional_eval and orchestrator.reasoning_engine:
        # Temporarily swap fields to evaluate improved_idea instead of text
        for candidate in top_candidates:
            candidate["_original_text"] = candidate.get("text", candidate.get("idea", ""))
            candidate["text"] = candidate.get("improved_idea", candidate["_original_text"])

        top_candidates = orchestrator.add_multi_dimensional_evaluation_with_monitoring(
            candidates=top_candidates,
            topic=topic,
            context=context,
            monitor=monitor
        )

        # TODO: Technical debt - field swapping pattern adds complexity
        # This pattern temporarily mutates candidate["text"] to evaluate improved ideas,
        # then restores the original and stores improved eval separately.
        # Future work: Enhance orchestrator method with evaluation_field parameter
        # to support evaluating arbitrary fields without temporary mutation.
        # Reference: gemini-code-assist review comment (PR #181)
        # Restore original text and move multi-dimensional eval to improved field
        for candidate in top_candidates:
            candidate["text"] = candidate["_original_text"]
            candidate["improved_multi_dimensional_evaluation"] = candidate.pop("multi_dimensional_evaluation", None)
            del candidate["_original_text"]
    
    # Step 9: Build final results
    log_verbose_step("STEP 7: Building Final Results", 
                    f"📦 Packaging {len(top_candidates)} complete candidates", 
                    verbose)
    
    for i, candidate in enumerate(top_candidates):
        # Calculate score delta
        initial_score = candidate["score"]
        improved_score = candidate.get("improved_score", initial_score)
        score_delta = improved_score - initial_score
        
        # Check if improvement is meaningful
        is_meaningful, similarity_score = is_meaningful_improvement(
            candidate["text"],
            candidate.get("improved_idea", candidate["text"]),
            score_delta,
            similarity_threshold=MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            score_delta_threshold=MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )
        
        # Build candidate data
        candidate_data = {
            "idea": candidate["text"],
            "initial_score": initial_score,
            "initial_critique": candidate["critique"],
            "advocacy": candidate.get("advocacy", "N/A"),
            "skepticism": candidate.get("skepticism", "N/A"),
            "improved_idea": candidate.get("improved_idea", candidate["text"]),
            "improved_score": improved_score,
            "improved_critique": candidate.get("improved_critique", "N/A"),
            "score_delta": score_delta,
            "is_meaningful_improvement": is_meaningful,
            "similarity_score": similarity_score
        }
        
        # Add multi-dimensional evaluation if available
        if "multi_dimensional_evaluation" in candidate:
            candidate_data["multi_dimensional_evaluation"] = candidate["multi_dimensional_evaluation"]
        
        if "improved_multi_dimensional_evaluation" in candidate:
            candidate_data["improved_multi_dimensional_evaluation"] = candidate["improved_multi_dimensional_evaluation"]
        
        final_candidates_data.append(candidate_data)
    
    # Generate monitoring summary
    monitor = get_batch_monitor()
    session_summary = monitor.get_session_summary()
    cost_analysis = monitor.analyze_cost_effectiveness()
    
    log_verbose_step("WORKFLOW COMPLETE", 
                    f"🎉 Batch processing finished\n📊 {len(final_candidates_data)} candidates processed\n🚀 API calls significantly reduced!", 
                    verbose)
    
    # Log performance summary
    if session_summary.get("total_calls", 0) > 0:
        logging.info(
            f"Batch Performance: {session_summary['successful_calls']}/{session_summary['total_calls']} calls successful, "
            f"{session_summary['total_items_processed']} items in {session_summary['total_processing_time_seconds']:.2f}s"
        )
        
        if session_summary.get("total_estimated_cost_usd"):
            logging.info(f"Estimated cost: ${session_summary['total_estimated_cost_usd']:.4f}")
    
    # Log cost-effectiveness analysis if verbose
    if verbose and cost_analysis.get("recommendations"):
        logging.info("Batch Cost Analysis:")
        for recommendation in cost_analysis["recommendations"]:
            logging.info(f"  • {recommendation}")
    
    return final_candidates_data


# For backward compatibility, expose the batch version as the main function
run_multistep_workflow = run_multistep_workflow_batch