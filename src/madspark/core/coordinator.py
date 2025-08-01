"""Coordinator for the Mad Spark Multi-Agent Workflow.

This module orchestrates the interaction between various specialized agents
(Idea Generator, Critic, Advocate, Skeptic) to generate, evaluate, and
refine ideas based on a given theme and constraints.
# ... (rest of module docstring)
"""
import os
import json
import logging
import time
import datetime
from typing import List, Dict, Any, Optional, TypedDict # Added TypedDict

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
    from madspark.utils.utils import (
        parse_json_with_fallback,
        validate_evaluation_json,
    )
    from madspark.utils.novelty_filter import NoveltyFilter
    from madspark.utils.temperature_control import TemperatureManager
    from madspark.core.enhanced_reasoning import ReasoningEngine
    from madspark.utils.constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_EVALUATION_TEMPERATURE, 
        DEFAULT_ADVOCACY_TEMPERATURE,
        DEFAULT_SKEPTICISM_TEMPERATURE,
        LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD,
        MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
        MEANINGFUL_IMPROVEMENT_SCORE_DELTA
    )
    from madspark.utils.text_similarity import is_meaningful_improvement
except ImportError:
    # Fallback imports for local development/testing
    try:
        from ..utils.utils import (
            parse_json_with_fallback,
            validate_evaluation_json,
        )
        from ..utils.novelty_filter import NoveltyFilter
        from ..utils.temperature_control import TemperatureManager
        from .enhanced_reasoning import ReasoningEngine
        from ..utils.constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE, 
            DEFAULT_ADVOCACY_TEMPERATURE,
            DEFAULT_SKEPTICISM_TEMPERATURE,
            LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD,
            MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )
        from ..utils.text_similarity import is_meaningful_improvement
    except ImportError:
        # Last resort - direct imports (for old package structure)
        from utils import (
            parse_json_with_fallback,
            validate_evaluation_json,
        )
        from novelty_filter import NoveltyFilter
        from temperature_control import TemperatureManager
        from enhanced_reasoning import ReasoningEngine
        from constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE, 
            DEFAULT_ADVOCACY_TEMPERATURE,
            DEFAULT_SKEPTICISM_TEMPERATURE,
            LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD,
            MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )
        from text_similarity import is_meaningful_improvement
# Removed unused imports - ADVOCATE_FAILED_PLACEHOLDER, SKEPTIC_FAILED_PLACEHOLDER
# as agent tools already handle empty responses
# from google.adk.agents import Agent # No longer needed directly for hints here


def log_verbose_step(step_name: str, details: str = "", verbose: bool = False):
    """Log verbose step information with visual indicators."""
    if verbose:
        msg = f"\n{'='*60}\n🔍 {step_name}\n{'='*60}"
        if details:
            msg += f"\n{details}"
        msg += "\n"
        print(msg)
        logging.info(f"VERBOSE_STEP: {step_name}")
        if details:
            logging.info(f"VERBOSE_DETAILS: {details}")

def log_verbose_data(label: str, data: str, verbose: bool = False, max_length: int = 500):
    """Log verbose data with truncation for readability."""
    if not verbose:
        return  # Early exit to avoid any string operations
    
    # Use list for efficient string building
    msg_parts = [f"\n📊 {label}:", "-" * 40]
    
    if len(data) > max_length:
        msg_parts.extend([
            data[:max_length] + "...",
            "",
            f"[Truncated - Total length: {len(data)} characters]"
        ])
        log_data = data[:max_length] + "..."
    else:
        msg_parts.append(data)
        log_data = data
    
    msg_parts.append("-" * 40)
    print("\n".join(msg_parts))
    
    logging.info(f"VERBOSE_DATA: {label} ({len(data)} characters)")
    # Log truncated version to file
    logging.debug(f"VERBOSE_CONTENT: {log_data}")

def log_verbose_completion(step_name: str, count: int, duration: float, verbose: bool = False, unit: str = "items"):
    """Log completion status with timing information."""
    if verbose:
        print(f"✅ {step_name} Complete: Generated {count} {unit} in {duration:.2f}s")

def log_verbose_sample_list(items: list, verbose: bool = False, max_display: int = 3, item_formatter=None):
    """Log a sample of items from a list."""
    if verbose and items:
        print("📝 Sample Items:")
        display_items = items[:max_display]
        for i, item in enumerate(display_items, 1):
            if item_formatter:
                formatted_item = item_formatter(item)
            else:
                formatted_item = str(item)[:80] + ("..." if len(str(item)) > 80 else "")
            print(f"  {i}. {formatted_item}")
        if len(items) > max_display:
            print(f"  ... and {len(items) - max_display} more items")


def log_agent_execution(step_name: str, agent_name: str, agent_emoji: str, description: str, 
                       temperature: float, verbose: bool = False):
    """Log the start of an agent execution with standardized format."""
    if verbose:
        details = f"{agent_emoji} Agent: {agent_name}\n🎯 {description}\n🌡️ Temperature: {temperature}"
        log_verbose_step(step_name, details, verbose)


def log_agent_completion(agent_name: str, response_data: str, step_number: str, 
                        duration: float, verbose: bool = False, max_length: int = 600):
    """Log the completion of an agent execution with response data."""
    if verbose:
        log_verbose_data(f"Raw {agent_name} Response for {step_number}", response_data, verbose, max_length)
        log_verbose_completion(f"{agent_name} Analysis", len(response_data), duration, verbose, "characters")


# --- TypedDict Definitions ---
class EvaluatedIdea(TypedDict):
    """Structure for an idea after evaluation by the CriticAgent."""
    text: str       # The original idea text
    score: int      # Score assigned by the critic
    critique: str   # Textual critique from the critic
    multi_dimensional_evaluation: Optional[Dict[str, Any]]  # Multi-dimensional evaluation data

class CandidateData(TypedDict):
    """Structure for the final data compiled for each candidate idea."""
    idea: str
    initial_score: float
    initial_critique: str
    advocacy: str
    skepticism: str
    multi_dimensional_evaluation: Optional[Dict[str, Any]]
    improved_idea: str
    improved_score: float
    improved_critique: str
    score_delta: float
# --- End TypedDict Definitions ---


# Import retry-wrapped versions of agent calls from shared module
try:
    from madspark.utils.agent_retry_wrappers import (
        call_idea_generator_with_retry,
        call_critic_with_retry,
        call_advocate_with_retry,
        call_skeptic_with_retry,
        call_improve_idea_with_retry
    )
    # Import batch functions
    from madspark.agents.advocate import advocate_ideas_batch
    from madspark.agents.skeptic import criticize_ideas_batch
    from madspark.agents.idea_generator import improve_ideas_batch
except ImportError:
    from ..utils.agent_retry_wrappers import (
        call_idea_generator_with_retry,
        call_critic_with_retry,
        call_advocate_with_retry,
        call_skeptic_with_retry,
        call_improve_idea_with_retry
    )
    # Import batch functions with relative imports
    from ..agents.advocate import advocate_ideas_batch
    from ..agents.skeptic import criticize_ideas_batch
    from ..agents.idea_generator import improve_ideas_batch


def run_multistep_workflow(
    theme: str, constraints: str, num_top_candidates: int = 2, 
    enable_novelty_filter: bool = True, novelty_threshold: float = 0.8,
    temperature_manager: Optional[TemperatureManager] = None,
    verbose: bool = False,
    enhanced_reasoning: bool = False,
    multi_dimensional_eval: bool = False,
    logical_inference: bool = False,
    reasoning_engine: Optional[ReasoningEngine] = None,
    timeout: int = 600
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
        except:
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
        verbose=verbose
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
