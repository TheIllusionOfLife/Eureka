"""Batch-optimized coordinator for Mad Spark Multi-Agent Workflow.

This is a refactored version of the coordinator that uses batch API calls
to significantly reduce the number of API calls from O(N) to O(1) for
advocate, skeptic, and improvement processing.
"""
import logging
import time
from typing import List, Optional

from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor
from madspark.utils.errors import ValidationError

from madspark.core.types_and_logging import (
    CandidateData, log_verbose_step, log_agent_completion
)
from madspark.utils.utils import parse_json_with_fallback
from madspark.utils.text_similarity import is_meaningful_improvement
from madspark.utils.constants import (
    MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
    MEANINGFUL_IMPROVEMENT_SCORE_DELTA
)
from madspark.utils.temperature_control import TemperatureManager
from madspark.utils.novelty_filter import NoveltyFilter
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.utils.constants import DEFAULT_TIMEOUT_SECONDS

# Import retry-wrapped versions of agent calls from shared module
try:
    from madspark.utils.agent_retry_wrappers import (
        call_idea_generator_with_retry,
        call_critic_with_retry
    )
    # Import batch functions
    from madspark.agents.advocate import advocate_ideas_batch
    from madspark.agents.skeptic import criticize_ideas_batch
    from madspark.agents.idea_generator import improve_ideas_batch
except ImportError:
    from ..utils.agent_retry_wrappers import (
        call_idea_generator_with_retry,
        call_critic_with_retry
    )
    # Import batch functions with relative imports
    from ..agents.advocate import advocate_ideas_batch
    from ..agents.skeptic import criticize_ideas_batch
    from ..agents.idea_generator import improve_ideas_batch


def run_multistep_workflow_batch(
    theme: str, 
    constraints: str, 
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
        theme: Main topic or theme for idea generation
        constraints: Specific constraints or requirements
        num_top_candidates: Number of top ideas to fully process
        enable_reasoning: Whether to use enhanced reasoning
        multi_dimensional_eval: Whether to use multi-dimensional evaluation
        temperature_manager: Optional temperature control
        novelty_filter: Optional novelty filtering
        verbose: Enable verbose logging
        reasoning_engine: Optional pre-initialized reasoning engine
        timeout: Maximum time allowed for the entire workflow in seconds (not implemented in sync mode)
        
    Returns:
        List of fully processed candidate data
    """
    final_candidates_data: List[CandidateData] = []
    
    # Warn about timeout not being implemented in sync mode
    if timeout != DEFAULT_TIMEOUT_SECONDS:  # Only warn if non-default timeout specified
        logging.warning("Timeout parameter is not implemented in sync mode and will be ignored")
    
    # Get temperature settings
    temp_manager = temperature_manager or TemperatureManager()
    idea_temp = temp_manager.get_temperature_for_stage("idea_generation")
    eval_temp = temp_manager.get_temperature_for_stage("evaluation")
    advocacy_temp = temp_manager.get_temperature_for_stage("advocacy")
    skepticism_temp = temp_manager.get_temperature_for_stage("skepticism")
    
    # Initialize reasoning engine if enabled
    engine = reasoning_engine  # Use passed engine if available
    if enable_reasoning and engine is None:
        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            engine = ReasoningEngine(genai_client)
        except (ImportError, AttributeError, RuntimeError):
            engine = ReasoningEngine()
    
    # Step 1: Generate Ideas (unchanged)
    log_verbose_step("STEP 1: Idea Generation", 
                    f"🎯 Theme: {theme}\n📋 Constraints: {constraints}\n🌡️ Temperature: {idea_temp}", 
                    verbose)
    
    start_time = time.time()
    ideas_text = call_idea_generator_with_retry(
        topic=theme, 
        context=constraints, 
        temperature=idea_temp
    )
    
    idea_gen_duration = time.time() - start_time
    log_agent_completion("IdeaGenerator", ideas_text, f"{theme[:20]}...", idea_gen_duration, verbose)
    
    # Parse ideas
    parsed_ideas = [idea.strip() for idea in ideas_text.split('\n') if idea.strip()]
    
    if not parsed_ideas:
        logging.warning("No ideas were generated.")
        return []
    
    logging.info(f"Generated {len(parsed_ideas)} ideas")
    
    # Step 2: Evaluate Ideas (already batched)
    log_verbose_step("STEP 2: Idea Evaluation", 
                    f"📊 Evaluating {len(parsed_ideas)} ideas\n🌡️ Temperature: {eval_temp}", 
                    verbose)
    
    try:
        evaluation_output = call_critic_with_retry(
            ideas=ideas_text,
            criteria=constraints,
            context=theme,
            temperature=eval_temp
        )
        
        # Parse evaluations
        evaluation_results = parse_json_with_fallback(
            evaluation_output,
            expected_count=len(parsed_ideas)
        )
                
        # Create evaluated ideas
        evaluated_ideas_data = []
        for i, idea in enumerate(parsed_ideas):
            if i < len(evaluation_results):
                eval_data = evaluation_results[i]
                score = eval_data.get("score", 0)
                critique = eval_data.get("comment", "No critique available")
                
                evaluated_idea = {
                    "text": idea,
                    "score": score,
                    "critique": critique
                }
                
                # Add multi-dimensional evaluation if enabled
                if multi_dimensional_eval and engine:
                    try:
                        # This will be batched later
                        evaluated_idea["multi_dimensional_evaluation"] = None
                    except (AttributeError, KeyError):
                        pass
                
                evaluated_ideas_data.append(evaluated_idea)
        
        # Sort and select top candidates
        evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = evaluated_ideas_data[:num_top_candidates]
        
        logging.info(f"Selected {len(top_candidates)} top candidates for further processing.")
        
    except ValidationError:
        # Re-raise validation errors immediately
        raise
    except Exception as e:
        logging.error(f"CriticAgent failed: {e}")
        # Fallback handling
        top_candidates = [
            {"text": idea, "critique": "N/A (CriticAgent failed)", "score": 0}
            for idea in parsed_ideas[:num_top_candidates]
        ]
    
    if not top_candidates:
        logging.info("No candidates selected for processing.")
        return []
    
    # Step 3: Batch Multi-Dimensional Evaluation (if enabled)
    if multi_dimensional_eval and engine and engine.multi_evaluator:
        log_verbose_step("STEP 2.5: Multi-Dimensional Evaluation (Batch)", 
                        f"🎯 Evaluating {len(top_candidates)} candidates across 7 dimensions", 
                        verbose)
        
        with batch_call_context("multi_dimensional", len(top_candidates)) as monitor_ctx:
            try:
                # Extract ideas for batch evaluation
                ideas_for_eval = [candidate["text"] for candidate in top_candidates]
                context = {"theme": theme, "constraints": constraints}
                
                # Batch evaluate all dimensions for all ideas
                multi_eval_results = engine.multi_evaluator.evaluate_ideas_batch(
                    ideas_for_eval, context
                )
                
                # Add results to candidates
                for i, result in enumerate(multi_eval_results):
                    if i < len(top_candidates):
                        top_candidates[i]["multi_dimensional_evaluation"] = result
                        
            except Exception as e:
                logging.warning(f"Multi-dimensional batch evaluation failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
    
    # Step 4: Batch Advocate Processing
    log_verbose_step("STEP 3: Batch Advocate Processing", 
                    f"👥 Processing {len(top_candidates)} candidates\n🌡️ Temperature: {advocacy_temp}", 
                    verbose)
    
    # Prepare batch input for advocate
    advocate_input = []
    for candidate in top_candidates:
        advocate_input.append({
            "idea": candidate["text"],
            "evaluation": candidate["critique"]
        })
    
    with batch_call_context("advocate", len(top_candidates)) as monitor_ctx:
        try:
            # Single API call for all advocacies
            advocacy_results, token_usage = advocate_ideas_batch(
                advocate_input, 
                theme, 
                advocacy_temp
            )
            
            # Set token usage for monitoring
            if token_usage > 0:
                monitor_ctx.set_tokens_used(token_usage)
            
            # Map results back to candidates
            for i, advocacy in enumerate(advocacy_results):
                if i < len(top_candidates):
                    top_candidates[i]["advocacy"] = advocacy.get("formatted", "N/A")
                    
        except Exception as e:
            logging.error(f"Batch advocate failed: {e}")
            monitor_ctx.set_fallback_used(str(e))
            # Fallback: mark all as N/A
            for candidate in top_candidates:
                candidate["advocacy"] = "N/A (Batch advocate failed)"
    
    # Step 5: Batch Skeptic Processing
    log_verbose_step("STEP 4: Batch Skeptic Processing", 
                    f"🔍 Processing {len(top_candidates)} candidates\n🌡️ Temperature: {skepticism_temp}", 
                    verbose)
    
    # Prepare batch input for skeptic
    skeptic_input = []
    for candidate in top_candidates:
        skeptic_input.append({
            "idea": candidate["text"],
            "advocacy": candidate.get("advocacy", "N/A")
        })
    
    with batch_call_context("skeptic", len(top_candidates)) as monitor_ctx:
        try:
            # Single API call for all skepticisms
            skepticism_results, token_usage = criticize_ideas_batch(
                skeptic_input,
                theme,
                skepticism_temp
            )
            
            # Set token usage for monitoring
            if token_usage > 0:
                monitor_ctx.set_tokens_used(token_usage)
            
            # Map results back to candidates
            for i, skepticism in enumerate(skepticism_results):
                if i < len(top_candidates):
                    top_candidates[i]["skepticism"] = skepticism.get("formatted", "N/A")
                    
        except Exception as e:
            logging.error(f"Batch skeptic failed: {e}")
            monitor_ctx.set_fallback_used(str(e))
            # Fallback: mark all as N/A
            for candidate in top_candidates:
                candidate["skepticism"] = "N/A (Batch skeptic failed)"
    
    # Step 6: Batch Improvement Processing
    log_verbose_step("STEP 5: Batch Idea Improvement", 
                    f"💡 Improving {len(top_candidates)} candidates\n🌡️ Temperature: {idea_temp}", 
                    verbose)
    
    # Prepare batch input for improvement
    improve_input = []
    for candidate in top_candidates:
        improve_input.append({
            "idea": candidate["text"],
            "critique": candidate["critique"],
            "advocacy": candidate.get("advocacy", "N/A"),
            "skepticism": candidate.get("skepticism", "N/A")
        })
    
    with batch_call_context("improve", len(top_candidates)) as monitor_ctx:
        try:
            # Single API call for all improvements
            improvement_results, token_usage = improve_ideas_batch(
                improve_input,
                theme,
                idea_temp
            )
            
            # Set token usage for monitoring
            if token_usage > 0:
                monitor_ctx.set_tokens_used(token_usage)
            
            # Map results back to candidates
            for i, improvement in enumerate(improvement_results):
                if i < len(top_candidates):
                    top_candidates[i]["improved_idea"] = improvement.get(
                        "improved_idea", 
                        top_candidates[i]["text"]  # Fallback to original
                    )
                    
        except Exception as e:
            logging.error(f"Batch improvement failed: {e}")
            monitor_ctx.set_fallback_used(str(e))
            # Fallback: use original ideas
            for candidate in top_candidates:
                candidate["improved_idea"] = candidate["text"]
    
    # Step 7: Batch Re-evaluation
    log_verbose_step("STEP 6: Batch Re-evaluation", 
                    f"📊 Re-evaluating {len(top_candidates)} improved ideas", 
                    verbose)
    
    # Collect improved ideas for re-evaluation
    improved_ideas_text = "\n".join([
        candidate.get("improved_idea", candidate["text"]) 
        for candidate in top_candidates
    ])
    
    try:
        # Single API call for all re-evaluations
        re_eval_output = call_critic_with_retry(
            ideas=improved_ideas_text,
            criteria=constraints,
            context=theme,
            temperature=eval_temp
        )
        
        # Parse re-evaluations
        re_eval_results = parse_json_with_fallback(
            re_eval_output,
            expected_count=len(top_candidates)
        )
        
        for i, parsed_eval in enumerate(re_eval_results):
            if i < len(top_candidates):
                top_candidates[i]["improved_score"] = parsed_eval.get("score", 0)
                top_candidates[i]["improved_critique"] = parsed_eval.get(
                    "comment", 
                    "No critique available"
                )
                
    except Exception as e:
        logging.error(f"Batch re-evaluation failed: {e}")
        # Fallback: use original scores
        for candidate in top_candidates:
            candidate["improved_score"] = candidate["score"]
            candidate["improved_critique"] = "Re-evaluation failed"
    
    # Step 8: Batch Multi-Dimensional Re-evaluation (if enabled)
    if multi_dimensional_eval and engine and engine.multi_evaluator:
        log_verbose_step("STEP 6.5: Multi-Dimensional Re-evaluation (Batch)", 
                        f"🎯 Re-evaluating {len(top_candidates)} improved ideas", 
                        verbose)
        
        with batch_call_context("multi_dimensional_improved", len(top_candidates)) as monitor_ctx:
            try:
                # Extract improved ideas for batch evaluation
                improved_ideas = [
                    candidate.get("improved_idea", candidate["text"]) 
                    for candidate in top_candidates
                ]
                
                # Batch evaluate all dimensions for all improved ideas
                improved_multi_eval_results = engine.multi_evaluator.evaluate_ideas_batch(
                    improved_ideas, context
                )
                
                # Add results to candidates
                for i, result in enumerate(improved_multi_eval_results):
                    if i < len(top_candidates):
                        top_candidates[i]["improved_multi_dimensional_evaluation"] = result
                        
            except Exception as e:
                logging.warning(f"Multi-dimensional re-evaluation failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
    
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