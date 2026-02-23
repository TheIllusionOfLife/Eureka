"""WorkflowOrchestrator for centralized workflow logic.

This module centralizes the multi-step workflow logic previously spread across
coordinator.py, coordinator_batch.py, and async_coordinator.py.

The WorkflowOrchestrator provides a unified set of workflow steps that can be
called by both synchronous and asynchronous coordinators, reducing code
duplication and improving maintainability.
"""
import asyncio
import logging
import time
from typing import List, Tuple, Dict, Any, Optional, Union, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from madspark.utils.batch_monitor import BatchMonitor
    from madspark.llm.router import LLMRouter

from madspark.config.workflow_constants import (
    FALLBACK_ADVOCACY,
    FALLBACK_SKEPTICISM,
    FALLBACK_CRITIQUE,
    FALLBACK_SCORE,
    STEP_IDEA_GENERATION,
    STEP_EVALUATION,
    STEP_ADVOCACY,
    STEP_SKEPTICISM,
    STEP_IMPROVEMENT,
    STEP_REEVALUATION,
    STEP_BUILD_RESULTS,
)
from madspark.utils.constants import (
    MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
    MEANINGFUL_IMPROVEMENT_SCORE_DELTA,
)
from madspark.core.types_and_logging import (
    EvaluatedIdea,
    CandidateData,
    log_verbose_step,
    log_agent_completion,
)
from madspark.utils.utils import parse_json_with_fallback
from madspark.utils.text_similarity import is_meaningful_improvement
from madspark.utils.temperature_control import TemperatureManager
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.agents.genai_client import get_model_name

# Import retry-wrapped versions and batch functions using compat helpers
from madspark.utils.compat_imports import (
    import_coordinator_batch_retry_wrappers,
    import_batch_functions,
)

_retry_wrappers = import_coordinator_batch_retry_wrappers()
call_idea_generator_with_retry = _retry_wrappers['call_idea_generator_with_retry']
call_critic_with_retry = _retry_wrappers['call_critic_with_retry']

_batch_functions = import_batch_functions()
advocate_ideas_batch = _batch_functions['advocate_ideas_batch']
criticize_ideas_batch = _batch_functions['criticize_ideas_batch']
improve_ideas_batch = _batch_functions['improve_ideas_batch']

# Set up logger
logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates multi-step workflow execution for idea refinement.

    The WorkflowOrchestrator centralizes workflow logic including:
    - Idea generation
    - Idea evaluation
    - Advocacy processing
    - Skepticism processing
    - Idea improvement
    - Re-evaluation
    - Final results building

    This class provides workflow steps that can be used by both synchronous
    and asynchronous coordinators, maintaining consistent behavior while
    reducing code duplication.
    """

    def __init__(
        self,
        temperature_manager: Optional[TemperatureManager] = None,
        reasoning_engine: Optional[ReasoningEngine] = None,
        verbose: bool = False,
        router: Optional["LLMRouter"] = None
    ):
        """Initialize the WorkflowOrchestrator.

        Args:
            temperature_manager: Optional temperature manager for agent controls.
                                If None, creates default manager with base temp 0.7.
            reasoning_engine: Optional reasoning engine for enhanced evaluation.
                            If None and needed, will create default engine.
            verbose: Enable verbose logging throughout workflow steps.
            router: Optional LLMRouter instance for request-scoped routing.
                   If None, uses global singleton (backward compatibility).
        """
        self.verbose = verbose
        self.router = router  # Store router for agent calls

        # Initialize or use provided temperature manager
        if temperature_manager:
            self.temperature_manager = temperature_manager
        else:
            self.temperature_manager = TemperatureManager.from_base_temperature(0.7)

        # Store reasoning engine (may be None, created on-demand if needed)
        self.reasoning_engine = reasoning_engine

        # Get model name for monitoring
        self.model_name = get_model_name()

    def _get_or_create_reasoning_engine(self) -> Optional[ReasoningEngine]:
        """Get or create reasoning engine on-demand.

        Returns:
            ReasoningEngine instance, or None if creation fails.
        """
        if self.reasoning_engine is not None:
            return self.reasoning_engine

        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            self.reasoning_engine = ReasoningEngine(genai_client=genai_client)
            return self.reasoning_engine
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.warning(f"Could not create reasoning engine: {e}")
            # Fallback to basic initialization
            self.reasoning_engine = ReasoningEngine()
            return self.reasoning_engine

    def generate_ideas(
        self,
        topic: str,
        context: str,
        num_ideas: int,
        multimodal_files: Optional[List[Union[str, Path]]] = None,
        multimodal_urls: Optional[List[str]] = None
    ) -> Tuple[List[str], int]:
        """Generate initial ideas for the given topic and context.

        Args:
            topic: Main topic/theme for idea generation.
            context: Context/constraints for the ideas.
            num_ideas: Number of ideas to generate.
            multimodal_files: Optional list of file paths (images, PDFs, documents).
            multimodal_urls: Optional list of URLs for context.

        Returns:
            Tuple of (list of idea strings, token count).

        Raises:
            Exception: If idea generation fails completely.
        """
        # Extract temperature for idea generation
        idea_temp = self.temperature_manager.get_temperature_for_stage('idea_generation')

        log_verbose_step(
            STEP_IDEA_GENERATION,
            f"🧠 Generating ideas for topic: {topic[:50]}...\n🌡️ Temperature: {idea_temp}",
            self.verbose
        )

        start_time = time.time()

        # Call idea generator with retry
        ideas_text = call_idea_generator_with_retry(
            topic=topic,
            context=context,
            temperature=idea_temp,
            use_structured_output=True,
            multimodal_files=multimodal_files,
            multimodal_urls=multimodal_urls,
            router=self.router  # Pass request-scoped router
        )

        duration = time.time() - start_time
        log_agent_completion("IdeaGenerator", ideas_text, f"{topic[:20]}...", duration, self.verbose)

        # Parse ideas using shared utility
        from madspark.utils.json_parsers import parse_idea_generator_response
        parsed_ideas = parse_idea_generator_response(ideas_text)

        if not parsed_ideas:
            logger.warning("No ideas were generated.")
            return [], 0

        logger.info(f"Generated {len(parsed_ideas)} ideas")

        # TODO: Replace with actual API token counts from response metadata
        # Currently using rough estimation based on text length (characters / 4)
        token_count = len(ideas_text) // 4  # Rough tokens-to-chars ratio

        return parsed_ideas, token_count

    def evaluate_ideas(
        self,
        ideas: List[str],
        topic: str,
        context: str
    ) -> Tuple[List[EvaluatedIdea], int]:
        """Evaluate ideas using the critic agent.

        Args:
            ideas: List of idea strings to evaluate.
            topic: Topic/theme for context.
            context: Context/constraints for evaluation.

        Returns:
            Tuple of (list of evaluated ideas with scores/critiques, token count).
        """
        eval_temp = self.temperature_manager.get_temperature_for_stage('evaluation')

        log_verbose_step(
            STEP_EVALUATION,
            f"📊 Evaluating {len(ideas)} ideas\n🌡️ Temperature: {eval_temp}",
            self.verbose
        )

        # Reconstruct ideas_text for critic (since critic expects full text)
        ideas_text = "\n".join([f"Idea {i+1}: {idea}" for i, idea in enumerate(ideas)])

        try:
            evaluation_output, token_count = call_critic_with_retry(
                ideas=ideas_text,
                topic=topic,
                context=context,
                temperature=eval_temp,
                use_structured_output=True,
                router=self.router  # Pass request-scoped router
            )

            # Parse evaluations
            evaluation_results = parse_json_with_fallback(
                evaluation_output,
                expected_count=len(ideas)
            )

            # Debug logging for score flow tracing
            logger.debug(f"Parsed {len(evaluation_results)} evaluation results for {len(ideas)} ideas")
            for i, result in enumerate(evaluation_results):
                logger.debug(f"Parsed eval {i+1}: score={result.get('score', 'N/A')}")

            # Create evaluated ideas
            evaluated_ideas_data: List[EvaluatedIdea] = []
            for i, idea in enumerate(ideas):
                if i < len(evaluation_results):
                    eval_data = evaluation_results[i]
                    score = eval_data.get("score", FALLBACK_SCORE)
                    critique = eval_data.get("comment", "No critique available")
                    logger.debug(f"Idea {i+1} assigned score={score}")
                else:
                    score = FALLBACK_SCORE
                    critique = FALLBACK_CRITIQUE
                    logger.warning(f"Idea {i+1} missing evaluation, using FALLBACK_SCORE={FALLBACK_SCORE}")

                evaluated_idea: EvaluatedIdea = {
                    "text": idea,
                    "score": score,
                    "critique": critique,
                    "multi_dimensional_evaluation": None
                }
                evaluated_ideas_data.append(evaluated_idea)

            return evaluated_ideas_data, token_count

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Return ideas with fallback values
            evaluated_ideas_data = []
            for idea in ideas:
                fallback_idea: EvaluatedIdea = {
                    "text": idea,
                    "score": FALLBACK_SCORE,
                    "critique": f"{FALLBACK_CRITIQUE}: {str(e)}",
                    "multi_dimensional_evaluation": None
                }
                evaluated_ideas_data.append(fallback_idea)
            return evaluated_ideas_data, 0

    def process_advocacy(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Process advocacy for candidate ideas using batch processing.

        Args:
            candidates: List of candidate dictionaries with 'idea' and 'initial_critique'.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates with 'advocacy' field, token count).
        """
        advocacy_temp = self.temperature_manager.get_temperature_for_stage('advocacy')

        log_verbose_step(
            STEP_ADVOCACY,
            f"👥 Processing {len(candidates)} candidates\n🌡️ Temperature: {advocacy_temp}",
            self.verbose
        )

        # Prepare batch input for advocate
        advocate_input = []
        for candidate in candidates:
            advocate_input.append({
                "idea": candidate.get("idea", candidate.get("text", "")),
                "evaluation": candidate.get("initial_critique", candidate.get("critique", ""))
            })

        try:
            # Single API call for all advocacies
            advocacy_results, token_usage = advocate_ideas_batch(
                advocate_input,
                topic,
                context,
                advocacy_temp,
                router=self.router  # Pass request-scoped router
            )

            # Map results back to candidates
            for i, advocacy in enumerate(advocacy_results):
                if i < len(candidates):
                    candidates[i]["advocacy"] = advocacy.get("formatted", "N/A")

            return candidates, token_usage

        except Exception as e:
            logger.error(f"Batch advocate failed: {e}")
            # Fallback: mark all as N/A
            for candidate in candidates:
                candidate["advocacy"] = FALLBACK_ADVOCACY
            return candidates, 0

    def process_skepticism(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Process skepticism for candidate ideas using batch processing.

        Args:
            candidates: List of candidate dictionaries with 'idea' and 'advocacy'.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates with 'skepticism' field, token count).
        """
        skepticism_temp = self.temperature_manager.get_temperature_for_stage('skepticism')

        log_verbose_step(
            STEP_SKEPTICISM,
            f"🔍 Processing {len(candidates)} candidates\n🌡️ Temperature: {skepticism_temp}",
            self.verbose
        )

        # Prepare batch input for skeptic
        skeptic_input = []
        for candidate in candidates:
            skeptic_input.append({
                "idea": candidate.get("idea", candidate.get("text", "")),
                "advocacy": candidate.get("advocacy", "N/A")
            })

        try:
            # Single API call for all skepticisms
            skepticism_results, token_usage = criticize_ideas_batch(
                skeptic_input,
                topic,
                context,
                skepticism_temp,
                router=self.router  # Pass request-scoped router
            )

            # Map results back to candidates
            for i, skepticism in enumerate(skepticism_results):
                if i < len(candidates):
                    candidates[i]["skepticism"] = skepticism.get("formatted", "N/A")

            return candidates, token_usage

        except Exception as e:
            logger.error(f"Batch skeptic failed: {e}")
            # Fallback: mark all as N/A
            for candidate in candidates:
                candidate["skepticism"] = FALLBACK_SKEPTICISM
            return candidates, 0

    def _format_logical_inference_for_prompt(
        self,
        logical_inference: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Format logical inference data for inclusion in improvement prompt.

        Args:
            logical_inference: Dict with confidence, conclusion, inference_chain, improvements.

        Returns:
            Formatted string for prompt or None if not available.
        """
        if not logical_inference:
            return None

        parts = []
        if logical_inference.get("confidence"):
            parts.append(f"Confidence: {logical_inference['confidence']:.0%}")
        if logical_inference.get("conclusion"):
            parts.append(f"Conclusion: {logical_inference['conclusion']}")
        if logical_inference.get("inference_chain"):
            chain = logical_inference["inference_chain"]
            if isinstance(chain, list):
                # Limit to 5 steps max to avoid prompt bloat
                limited_chain = chain[:5]
                parts.append("Logical Steps: " + " -> ".join(limited_chain))
        if logical_inference.get("improvements"):
            parts.append(f"Suggested Improvements: {logical_inference['improvements']}")

        return "\n".join(parts) if parts else None

    def improve_ideas(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Improve ideas based on advocacy and skepticism feedback.

        Args:
            candidates: List of candidate dictionaries with idea, critique, advocacy, skepticism.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates with 'improved_idea' field, token count).
        """
        idea_temp = self.temperature_manager.get_temperature_for_stage('idea_generation')

        log_verbose_step(
            STEP_IMPROVEMENT,
            f"💡 Improving {len(candidates)} candidates\n🌡️ Temperature: {idea_temp}",
            self.verbose
        )

        # Prepare batch input for improvement with enhanced evaluation data
        improve_input = []
        for candidate in candidates:
            # Extract dimension_scores from multi_dimensional_evaluation if present
            multi_dim_eval = candidate.get("multi_dimensional_evaluation")
            dimension_scores = None
            if multi_dim_eval and isinstance(multi_dim_eval, dict):
                dimension_scores = multi_dim_eval.get("dimension_scores")

            # Format logical inference for prompt
            logical_inference_formatted = self._format_logical_inference_for_prompt(
                candidate.get("logical_inference")
            )

            improve_input.append({
                "idea": candidate.get("idea", candidate.get("text", "")),
                "critique": candidate.get("initial_critique", candidate.get("critique", "")),
                "advocacy": candidate.get("advocacy", "N/A"),
                "skepticism": candidate.get("skepticism", "N/A"),
                # NEW: Enhanced evaluation data (Issue #219)
                "initial_score": candidate.get("initial_score", candidate.get("score")),
                "dimension_scores": dimension_scores,
                "logical_inference": logical_inference_formatted
            })

        try:
            # Single API call for all improvements
            improvement_results, token_usage = improve_ideas_batch(
                improve_input,
                topic,
                context,
                idea_temp,
                router=self.router  # Pass request-scoped router
            )

            # Map results back to candidates
            for i, improvement in enumerate(improvement_results):
                if i < len(candidates):
                    improved_text = improvement.get("improved_idea", "")
                    # Fallback to original if improvement failed
                    if not improved_text or improved_text.strip() == "":
                        improved_text = candidates[i].get("idea", candidates[i].get("text", ""))
                    candidates[i]["improved_idea"] = improved_text

            return candidates, token_usage

        except Exception as e:
            logger.error(f"Batch improve failed: {e}")
            # Fallback: use original ideas
            for candidate in candidates:
                candidate["improved_idea"] = candidate.get("idea", candidate.get("text", ""))
            return candidates, 0

    def reevaluate_ideas(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Re-evaluate improved ideas using the critic agent.

        CRITICAL: Uses original context to prevent bias inflation.

        Args:
            candidates: List of candidate dictionaries with 'improved_idea'.
            topic: Topic/theme for context.
            context: Original context (NOT from candidate, to avoid bias).

        Returns:
            Tuple of (updated candidates with 'improved_score'/'improved_critique', token count).
        """
        eval_temp = self.temperature_manager.get_temperature_for_stage('evaluation')

        log_verbose_step(
            STEP_REEVALUATION,
            f"📊 Re-evaluating {len(candidates)} improved ideas\n🌡️ Temperature: {eval_temp}",
            self.verbose
        )

        # Reconstruct improved ideas text for critic
        improved_ideas = [candidate.get("improved_idea", "") for candidate in candidates]
        ideas_text = "\n".join([f"Idea {i+1}: {idea}" for i, idea in enumerate(improved_ideas)])

        try:
            # Use ORIGINAL context to prevent bias (not from candidate)
            evaluation_output, token_count = call_critic_with_retry(
                ideas=ideas_text,
                topic=topic,
                context=context,  # Original context, not from candidate
                temperature=eval_temp,
                use_structured_output=True,
                router=self.router  # Pass request-scoped router
            )

            # Parse evaluations
            evaluation_results = parse_json_with_fallback(
                evaluation_output,
                expected_count=len(candidates)
            )

            # Update candidates with re-evaluation results
            for i, candidate in enumerate(candidates):
                if i < len(evaluation_results):
                    eval_data = evaluation_results[i]
                    candidate["improved_score"] = float(eval_data.get("score", candidate.get("initial_score", FALLBACK_SCORE)))
                    candidate["improved_critique"] = eval_data.get("comment", "No critique available")
                else:
                    # Fallback to original score
                    candidate["improved_score"] = float(candidate.get("initial_score", FALLBACK_SCORE))
                    candidate["improved_critique"] = FALLBACK_CRITIQUE

            return candidates, token_count

        except Exception as e:
            logger.error(f"Re-evaluation failed: {e}")
            # Fallback: use original scores
            for candidate in candidates:
                candidate["improved_score"] = float(candidate.get("initial_score", FALLBACK_SCORE))
                candidate["improved_critique"] = f"{FALLBACK_CRITIQUE}: {str(e)}"
            return candidates, 0

    def build_final_results(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[CandidateData]:
        """Build final results with meaningful improvement detection.

        Args:
            candidates: List of candidate dictionaries with all fields populated.

        Returns:
            List of CandidateData dictionaries with complete results.
        """
        log_verbose_step(
            STEP_BUILD_RESULTS,
            f"🎯 Building final results for {len(candidates)} candidates",
            self.verbose
        )

        final_results: List[CandidateData] = []

        for candidate in candidates:
            original_idea = candidate.get("idea", candidate.get("text", ""))
            improved_idea = candidate.get("improved_idea", original_idea)
            initial_score = float(candidate.get("initial_score", candidate.get("score", FALLBACK_SCORE)))
            improved_score = float(candidate.get("improved_score", initial_score))

            # Calculate score delta
            score_delta = improved_score - initial_score

            # Check if improvement is meaningful
            is_meaningful, similarity_score = is_meaningful_improvement(
                original_idea,
                improved_idea,
                score_delta,
                similarity_threshold=MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
                score_delta_threshold=MEANINGFUL_IMPROVEMENT_SCORE_DELTA
            )

            # Build final candidate data
            result: CandidateData = {
                "idea": original_idea,
                "initial_score": initial_score,
                "initial_critique": candidate.get("initial_critique", candidate.get("critique", "")),
                "advocacy": candidate.get("advocacy", "N/A"),
                "skepticism": candidate.get("skepticism", "N/A"),
                "multi_dimensional_evaluation": candidate.get("multi_dimensional_evaluation"),
                "improved_idea": improved_idea,
                "improved_score": improved_score,
                "improved_critique": candidate.get("improved_critique", ""),
                "score_delta": score_delta,
                "is_meaningful_improvement": is_meaningful,
                "similarity_score": similarity_score
            }

            final_results.append(result)

        return final_results

    # ========================================================================
    # MONITORING-INTEGRATED METHODS (Phase 3.2a)
    # ========================================================================

    def generate_ideas_with_monitoring(
        self,
        topic: str,
        context: str,
        num_ideas: int,
        monitor: Optional['BatchMonitor'] = None,
        multimodal_files: Optional[List[Union[str, Path]]] = None,
        multimodal_urls: Optional[List[str]] = None
    ) -> Tuple[List[str], int]:
        """Generate ideas with batch monitoring integration.

        Args:
            topic: Main topic/theme for idea generation.
            context: Context/constraints for the ideas.
            num_ideas: Number of ideas to generate.
            monitor: Optional BatchMonitor instance for tracking.
            multimodal_files: Optional list of file paths (images, PDFs, documents).
            multimodal_urls: Optional list of URLs for context.

        Returns:
            Tuple of (list of idea strings, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("idea_generation", num_ideas, monitor) as monitor_ctx:
            try:
                ideas, token_count = self.generate_ideas(
                    topic, context, num_ideas,
                    multimodal_files=multimodal_files,
                    multimodal_urls=multimodal_urls
                )

                # Set monitoring metadata
                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return ideas, token_count

            except Exception as e:
                logger.error(f"Idea generation with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                raise

    def evaluate_ideas_with_monitoring(
        self,
        ideas: List[str],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Evaluate ideas with batch monitoring integration.

        Args:
            ideas: List of idea strings to evaluate.
            topic: Topic/theme for context.
            context: Context/constraints.
            monitor: Optional BatchMonitor instance.

        Returns:
            Tuple of (evaluated ideas, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("evaluation", len(ideas), monitor) as monitor_ctx:
            try:
                evaluated, token_count = self.evaluate_ideas(ideas, topic, context)

                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return evaluated, token_count

            except Exception as e:
                logger.error(f"Evaluation with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                raise

    def process_advocacy_with_monitoring(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Process advocacy with batch monitoring integration.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            monitor: Optional BatchMonitor instance.

        Returns:
            Tuple of (updated candidates, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("advocate", len(candidates), monitor) as monitor_ctx:
            try:
                updated, token_count = self.process_advocacy(candidates, topic, context)

                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return updated, token_count

            except Exception as e:
                logger.error(f"Advocacy with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                # Return candidates with fallback values
                for candidate in candidates:
                    if "advocacy" not in candidate:
                        candidate["advocacy"] = FALLBACK_ADVOCACY
                return candidates, 0

    def process_skepticism_with_monitoring(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Process skepticism with batch monitoring integration.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            monitor: Optional BatchMonitor instance.

        Returns:
            Tuple of (updated candidates, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("skeptic", len(candidates), monitor) as monitor_ctx:
            try:
                updated, token_count = self.process_skepticism(candidates, topic, context)

                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return updated, token_count

            except Exception as e:
                logger.error(f"Skepticism with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                # Return candidates with fallback values
                for candidate in candidates:
                    if "skepticism" not in candidate:
                        candidate["skepticism"] = FALLBACK_SKEPTICISM
                return candidates, 0

    def improve_ideas_with_monitoring(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Improve ideas with batch monitoring integration.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            monitor: Optional BatchMonitor instance.

        Returns:
            Tuple of (updated candidates, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("improve", len(candidates), monitor) as monitor_ctx:
            try:
                updated, token_count = self.improve_ideas(candidates, topic, context)

                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return updated, token_count

            except Exception as e:
                logger.error(f"Improvement with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                # Return candidates with fallback (original ideas)
                for candidate in candidates:
                    if "improved_idea" not in candidate:
                        candidate["improved_idea"] = candidate.get("idea", candidate.get("text", ""))
                return candidates, 0

    def reevaluate_ideas_with_monitoring(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Re-evaluate ideas with batch monitoring integration.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints (original context, to prevent bias).
            monitor: Optional BatchMonitor instance.

        Returns:
            Tuple of (updated candidates, token count).
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("reevaluation", len(candidates), monitor) as monitor_ctx:
            try:
                updated, token_count = self.reevaluate_ideas(candidates, topic, context)

                if token_count > 0:
                    monitor_ctx.set_tokens_used(token_count)
                monitor_ctx.set_model_name(self.model_name)

                return updated, token_count

            except Exception as e:
                logger.error(f"Re-evaluation with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                # Return candidates with fallback scores
                for candidate in candidates:
                    if "improved_score" not in candidate:
                        candidate["improved_score"] = candidate.get("initial_score", FALLBACK_SCORE)
                    if "improved_critique" not in candidate:
                        candidate["improved_critique"] = FALLBACK_CRITIQUE
                return candidates, 0

    # ========================================================================
    # ASYNC METHOD VARIANTS (Phase 3.2a)
    # ========================================================================

    async def _run_async(self, func, *args, **kwargs):
        """Helper to run synchronous methods in the default executor."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def generate_ideas_async(
        self,
        topic: str,
        context: str,
        num_ideas: int,
        multimodal_files: Optional[List[Union[str, Path]]] = None,
        multimodal_urls: Optional[List[str]] = None
    ) -> Tuple[List[str], int]:
        """Async variant of generate_ideas.

        Args:
            topic: Main topic/theme for idea generation.
            context: Context/constraints for the ideas.
            num_ideas: Number of ideas to generate.
            multimodal_files: Optional list of file paths (images, PDFs, documents).
            multimodal_urls: Optional list of URLs for context.

        Returns:
            Tuple of (list of idea strings, token count).
        """
        return await self._run_async(
            self.generate_ideas,
            topic=topic,
            context=context,
            num_ideas=num_ideas,
            multimodal_files=multimodal_files,
            multimodal_urls=multimodal_urls
        )

    async def evaluate_ideas_async(
        self,
        ideas: List[str],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Async variant of evaluate_ideas.

        Args:
            ideas: List of idea strings to evaluate.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (evaluated ideas, token count).
        """
        return await self._run_async(
            self.evaluate_ideas,
            ideas,
            topic,
            context
        )

    async def process_advocacy_async(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Async variant of process_advocacy.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates, token count).
        """
        return await self._run_async(
            self.process_advocacy,
            candidates,
            topic,
            context
        )

    async def process_skepticism_async(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Async variant of process_skepticism.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates, token count).
        """
        return await self._run_async(
            self.process_skepticism,
            candidates,
            topic,
            context
        )

    async def improve_ideas_async(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Async variant of improve_ideas.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.

        Returns:
            Tuple of (updated candidates, token count).
        """
        return await self._run_async(
            self.improve_ideas,
            candidates,
            topic,
            context
        )

    async def reevaluate_ideas_async(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Async variant of reevaluate_ideas.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints (original, to prevent bias).

        Returns:
            Tuple of (updated candidates, token count).
        """
        return await self._run_async(
            self.reevaluate_ideas,
            candidates,
            topic,
            context
        )

    # ========================================================================
    # MULTI-DIMENSIONAL EVALUATION SUPPORT (Phase 3.2a)
    # ========================================================================

    def add_multi_dimensional_evaluation(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Add multi-dimensional evaluation to candidates.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            text_key: Key to use for extracting text to evaluate (default: "text").
                     Falls back to "idea" if key not found or if value is empty.

        Returns:
            Updated candidates with multi_dimensional_evaluation field.
        """
        if not self.reasoning_engine:
            logger.warning("ReasoningEngine not available, skipping multi-dimensional evaluation")
            return candidates

        if not hasattr(self.reasoning_engine, 'multi_evaluator') or not self.reasoning_engine.multi_evaluator:
            logger.warning("Multi-evaluator not available, skipping multi-dimensional evaluation")
            return candidates

        try:
            # Extract ideas for batch evaluation using specified key
            ideas_for_eval = []
            for candidate in candidates:
                # Try primary key, then fallback to "idea" or "text" if not found
                text = candidate.get(text_key) or candidate.get("idea") or candidate.get("text") or ""
                ideas_for_eval.append(text)

            eval_context = {"topic": topic, "context": context}

            # Batch evaluate all dimensions for all ideas
            multi_eval_results = self.reasoning_engine.multi_evaluator.evaluate_ideas_batch(
                ideas_for_eval, eval_context
            )

            # Add results to candidates
            for i, result in enumerate(multi_eval_results):
                if i < len(candidates):
                    candidates[i]["multi_dimensional_evaluation"] = result

            logger.info(f"Added multi-dimensional evaluation to {len(candidates)} candidates")

        except Exception as e:
            logger.warning(f"Multi-dimensional evaluation failed: {e}")
            # Don't crash, just leave multi_dimensional_evaluation as None

        return candidates

    def add_multi_dimensional_evaluation_with_monitoring(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        monitor: Optional['BatchMonitor'] = None,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Add multi-dimensional evaluation with monitoring.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            monitor: Optional BatchMonitor instance.
            text_key: Key to use for extracting text to evaluate.

        Returns:
            Updated candidates with multi_dimensional_evaluation field.
        """
        from madspark.utils.batch_monitor import batch_call_context, get_batch_monitor

        if monitor is None:
            monitor = get_batch_monitor()

        with batch_call_context("multi_dimensional", len(candidates), monitor) as monitor_ctx:
            try:
                updated = self.add_multi_dimensional_evaluation(
                    candidates, topic, context, text_key=text_key
                )
                monitor_ctx.set_model_name(self.model_name)
                return updated

            except Exception as e:
                logger.error(f"Multi-dimensional evaluation with monitoring failed: {e}")
                monitor_ctx.set_fallback_used(str(e))
                return candidates

    async def add_multi_dimensional_evaluation_async(
        self,
        candidates: List[Dict[str, Any]],
        topic: str,
        context: str,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Async variant of add_multi_dimensional_evaluation.

        Args:
            candidates: List of candidate dictionaries.
            topic: Topic/theme for context.
            context: Context/constraints.
            text_key: Key to use for extracting text to evaluate.

        Returns:
            Updated candidates with multi_dimensional_evaluation field.
        """
        return await self._run_async(
            self.add_multi_dimensional_evaluation,
            candidates=candidates,
            topic=topic,
            context=context,
            text_key=text_key
        )
