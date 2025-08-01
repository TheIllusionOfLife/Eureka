"""Coordinator for the Mad Spark Multi-Agent Workflow.

This module orchestrates the interaction between various specialized agents
(Idea Generator, Critic, Advocate, Skeptic) to generate, evaluate, and
refine ideas based on a given theme and constraints.
# ... (rest of module docstring)
"""
import os
import json
import logging
from typing import List, Optional

# Import shared types and logging functions
from madspark.core.types_and_logging import CandidateData, EvaluatedIdea  # noqa: F401

# --- Logging Configuration ---
# Note: Logging configuration is now handled by CLI to avoid conflicts
# If running coordinator.py directly, basic logging will be set up below
# --- End Logging Configuration ---

# SECURITY NOTE: Storing API keys directly in environment variables is suitable for
# local development but not recommended for production.
# Consider using a dedicated key management service for production deployments (test: not hardcoded).

try:
    from dotenv import load_dotenv, find_dotenv
    # Use find_dotenv to search up the directory tree for root .env
    env_file = find_dotenv()
    if env_file:
        logging.info(f"Coordinator: Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        logging.info("Coordinator: .env file not found, relying on environment variables.")
except ImportError:
    logging.warning(
        "Coordinator: Unable to load .env file automatically.\n"
        "Please ensure GOOGLE_API_KEY and GOOGLE_GENAI_MODEL are set in your environment.\n"
        "Tip: Run 'mad_spark config' to configure your API key."
    )

def _ensure_environment_configured():
    """Ensure environment variables are properly configured."""
    # Get API key and model AFTER loading .env
    api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")  # Environment variable, not hardcoded secret (test safe)
    model_name: Optional[str] = os.getenv("GOOGLE_GENAI_MODEL")

    # Set defaults to allow import without API keys (for testing/CI)
    if api_key:  # test: Environment variable check
        os.environ["GOOGLE_API_KEY"] = api_key  # test: Environment variable assignment
    else:
        # Only warn if not in mock mode
        if os.getenv("MADSPARK_MODE") != "mock":
            logging.warning("GOOGLE_API_KEY not set - will run in mock mode only")

    if model_name:
        os.environ["GOOGLE_GENAI_MODEL"] = model_name
    else:
        # Set default model name
        os.environ["GOOGLE_GENAI_MODEL"] = "gemini-2.5-flash"
        logging.info("GOOGLE_GENAI_MODEL not set - using default: gemini-2.5-flash")

# Agent functions are accessed via retry wrappers from agent_retry_wrappers module
try:
    # Primary imports for package installation
    from madspark.utils.novelty_filter import NoveltyFilter
    from madspark.utils.temperature_control import TemperatureManager
    from madspark.core.enhanced_reasoning import ReasoningEngine
    from madspark.utils.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_NOVELTY_THRESHOLD
except ImportError:
    # Fallback imports for local development/testing
    try:
        from ..utils.novelty_filter import NoveltyFilter
        from ..utils.temperature_control import TemperatureManager
        from .enhanced_reasoning import ReasoningEngine
        from ..utils.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_NOVELTY_THRESHOLD
    except ImportError:
        # Last resort - direct imports (for old package structure)
        from madspark.utils.novelty_filter import NoveltyFilter
        from madspark.utils.temperature_control import TemperatureManager
        from madspark.core.enhanced_reasoning import ReasoningEngine
        # Constants will use defaults if import fails
        DEFAULT_TIMEOUT_SECONDS = 600
        DEFAULT_NOVELTY_THRESHOLD = 0.8
# Removed unused imports - ADVOCATE_FAILED_PLACEHOLDER, SKEPTIC_FAILED_PLACEHOLDER
# as agent tools already handle empty responses
# from google.adk.agents import Agent # No longer needed directly for hints here




# Import retry-wrapped versions of agent calls from shared module
# Only import what's used - batch functions are used by coordinator_batch module


def run_multistep_workflow(
    theme: str, constraints: str, num_top_candidates: int = 2, 
    enable_novelty_filter: bool = True, novelty_threshold: float = DEFAULT_NOVELTY_THRESHOLD,
    temperature_manager: Optional[TemperatureManager] = None,
    verbose: bool = False,
    enhanced_reasoning: bool = False,
    multi_dimensional_eval: bool = False,
    logical_inference: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> List[CandidateData]:
    """
    Runs the multi-step idea generation and refinement workflow.
    
    This function now redirects to the batch-optimized version which provides
    50% fewer API calls while maintaining full backward compatibility.
    
    Args:
        theme: The main topic/theme for idea generation
        constraints: Constraints or requirements for the ideas
        num_top_candidates: Number of top ideas to select for detailed analysis
        enable_novelty_filter: Whether to filter duplicate/similar ideas
        novelty_threshold: Similarity threshold for novelty filtering
        temperature_manager: Manager for controlling creativity levels
        verbose: Enable verbose logging for detailed workflow visibility
        enhanced_reasoning: Enable enhanced reasoning capabilities (Phase 2.1)
        multi_dimensional_eval: Use multi-dimensional evaluation instead of simple scoring
        logical_inference: Enable logical inference chains for enhanced reasoning
        reasoning_engine: Pre-initialized reasoning engine (optional)
        timeout: Maximum time allowed for the entire workflow in seconds
        
    Returns:
        List of CandidateData containing processed ideas with evaluations
    """
    # Import the batch-optimized version
    from .coordinator_batch import run_multistep_workflow_batch
    
    # Configure novelty filter
    novelty_filter = None
    if enable_novelty_filter:
        novelty_filter = NoveltyFilter(similarity_threshold=novelty_threshold)
    
    # Initialize reasoning engine if needed
    engine = reasoning_engine
    if enhanced_reasoning and engine is None:
        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            config = {"use_logical_inference": logical_inference} if logical_inference else None
            engine = ReasoningEngine(config=config, genai_client=genai_client)
        except (ImportError, AttributeError, RuntimeError):
            config = {"use_logical_inference": logical_inference} if logical_inference else None
            engine = ReasoningEngine(config=config)
    
    # Call the batch-optimized version
    # Note: The batch version handles novelty filtering internally for now
    # This ensures all existing functionality works while gaining performance benefits
    return run_multistep_workflow_batch(
        theme=theme,
        constraints=constraints,
        num_top_candidates=num_top_candidates,
        enable_reasoning=enhanced_reasoning,
        multi_dimensional_eval=multi_dimensional_eval,
        temperature_manager=temperature_manager,
        novelty_filter=novelty_filter,
        verbose=verbose,
        reasoning_engine=engine,
        timeout=timeout
    )


if __name__ == "__main__":
    # Set up basic logging when running coordinator directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Ensure environment is configured
    _ensure_environment_configured()
    
    logging.info("Starting Mad Spark Multi-Agent Workflow...")
    sample_theme: str = "Sustainable Urban Living"
    sample_constraints: str = (
        "Ideas should be implementable within a typical city budget, focus on "
        "community involvement, and be technologically feasible within the next 5 "
        "years. Ideas should also consider scalability and inclusivity."
    )
    num_ideas_to_process: int = 1
    logging.info(f"Theme: {sample_theme}")
    logging.info(f"Constraints: {sample_constraints}")
    logging.info(f"Number of top ideas to fully process: {num_ideas_to_process}")

    results: List[CandidateData] = run_multistep_workflow(
        theme=sample_theme, constraints=sample_constraints, num_top_candidates=num_ideas_to_process
    )
    logging.info("--- Final Results ---")
    if results:
        print(json.dumps(results, indent=2))
    else:
        logging.info("No results were generated from the workflow.")
    logging.info("Mad Spark Multi-Agent Workflow Finished.")
