"""Test coordinator using WorkflowOrchestrator directly.

This is a simplified coordinator for testing the WorkflowOrchestrator
with real API calls. It demonstrates how coordinators can use the
orchestrator while maintaining their own timeout/monitoring logic.
"""
import logging
from typing import List, Optional

from madspark.core.workflow_orchestrator import WorkflowOrchestrator
from madspark.core.types_and_logging import CandidateData
from madspark.utils.temperature_control import TemperatureManager
from madspark.utils.novelty_filter import NoveltyFilter
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.utils.constants import DEFAULT_TIMEOUT_SECONDS
from madspark.utils.errors import ValidationError


def run_workflow_with_orchestrator(
    topic: str,
    context: str,
    num_top_candidates: int = 2,
    enable_novelty_filter: bool = True,
    novelty_threshold: float = 0.8,
    temperature_manager: Optional[TemperatureManager] = None,
    verbose: bool = False,
    enhanced_reasoning: bool = False,
    multi_dimensional_eval: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> List[CandidateData]:
    """Run workflow using WorkflowOrchestrator.

    This function demonstrates how to use the WorkflowOrchestrator
    to execute a complete workflow. It's simplified for testing but
    shows the integration pattern.

    Args:
        topic: Main topic/theme for idea generation.
        context: Context/constraints for the ideas.
        num_top_candidates: Number of top ideas to process.
        enable_novelty_filter: Whether to filter duplicate ideas.
        novelty_threshold: Similarity threshold for novelty.
        temperature_manager: Optional temperature control.
        verbose: Enable verbose logging.
        enhanced_reasoning: Enable enhanced reasoning.
        multi_dimensional_eval: Enable multi-dimensional evaluation.
        reasoning_engine: Optional pre-initialized reasoning engine.
        timeout: Maximum time for workflow (not implemented in this test version).

    Returns:
        List of CandidateData with complete results.

    Raises:
        ValidationError: If input parameters are invalid.
    """
    # Validate inputs
    if not topic or not isinstance(topic, str) or topic.strip() == "":
        raise ValidationError("Topic must be a non-empty string")
    if context is None or not isinstance(context, str) or context.strip() == "":
        raise ValidationError("Context must be a non-empty string")

    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        temperature_manager=temperature_manager,
        reasoning_engine=reasoning_engine,
        verbose=verbose
    )

    # Step 1: Generate ideas
    ideas, _ = orchestrator.generate_ideas(
        topic=topic,
        context=context,
        num_ideas=max(5, num_top_candidates + 2)
    )

    if not ideas:
        logging.warning("No ideas generated")
        return []

    # Apply novelty filtering if enabled
    if enable_novelty_filter:
        novelty_filter = NoveltyFilter(similarity_threshold=novelty_threshold)
        filtered = novelty_filter.filter_ideas(ideas)
        ideas = [fi.text for fi in filtered if fi.is_novel]

        if not ideas:
            logging.warning("All ideas filtered out as non-novel")
            return []

    # Step 2: Evaluate ideas
    evaluated, _ = orchestrator.evaluate_ideas(
        ideas=ideas,
        topic=topic,
        context=context
    )

    # Sort and select top candidates
    evaluated.sort(key=lambda x: x["score"], reverse=True)
    top_evaluated = evaluated[:num_top_candidates]

    # Convert to candidate format
    candidates = [
        {
            "idea": ev["text"],
            "initial_score": float(ev["score"]),
            "initial_critique": ev["critique"],
            "multi_dimensional_evaluation": None
        }
        for ev in top_evaluated
    ]

    if not candidates:
        logging.warning("No candidates selected")
        return []

    # Step 3-4: Process advocacy and skepticism
    candidates, _ = orchestrator.process_advocacy(candidates, topic, context)
    candidates, _ = orchestrator.process_skepticism(candidates, topic, context)

    # Step 5: Improve ideas
    candidates, _ = orchestrator.improve_ideas(candidates, topic, context)

    # Step 6: Re-evaluate
    candidates, _ = orchestrator.reevaluate_ideas(candidates, topic, context)

    # Step 7: Build final results
    final_results = orchestrator.build_final_results(candidates)

    return final_results
