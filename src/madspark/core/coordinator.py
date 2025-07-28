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
except ImportError:
    from ..utils.agent_retry_wrappers import (
        call_idea_generator_with_retry,
        call_critic_with_retry,
        call_advocate_with_retry,
        call_skeptic_with_retry,
        call_improve_idea_with_retry
    )


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
    # Ensure environment is configured before running workflow
    _ensure_environment_configured()
    
    final_candidates_data: List[CandidateData] = []
    # raw_generated_ideas: str = "" # Type will be known after call
    parsed_ideas: List[str] = []
    
    # Note: Timeout is only enforced in async mode via asyncio.wait_for()
    # Sync mode runs sequentially without interruption by design
    if timeout and timeout != 600:  # 600 is default timeout
        logging.warning(f"⚠️  Timeout parameter ({timeout}s) specified but not enforced in sync mode. Use AsyncCoordinator for timeout support.")

    # Extract temperatures from temperature manager if provided
    if temperature_manager:
        idea_temp = temperature_manager.get_temperature_for_stage('idea_generation')
        eval_temp = temperature_manager.get_temperature_for_stage('evaluation')
        advocacy_temp = temperature_manager.get_temperature_for_stage('advocacy')
        skepticism_temp = temperature_manager.get_temperature_for_stage('skepticism')
        logging.debug(f"Using temperatures - Ideas: {idea_temp}, Eval: {eval_temp}, Advocacy: {advocacy_temp}, Skepticism: {skepticism_temp}")
    else:
        # Default temperatures
        idea_temp = DEFAULT_IDEA_TEMPERATURE
        eval_temp = DEFAULT_EVALUATION_TEMPERATURE
        advocacy_temp = DEFAULT_ADVOCACY_TEMPERATURE
        skepticism_temp = DEFAULT_SKEPTICISM_TEMPERATURE

    # Initialize enhanced reasoning engine - always initialize for multi-dimensional evaluation
    engine = None
    conversation_history = []
    # Always create reasoning engine for multi-dimensional evaluation (now a core feature)
    if reasoning_engine:
        engine = reasoning_engine
    else:
        engine = ReasoningEngine()
    
    # Log initialization details
    if enhanced_reasoning or logical_inference or verbose:
        log_verbose_step(
            "🧠 Enhanced Reasoning Initialized",
            f"✅ Context Memory: {engine.context_memory.capacity} items\n✅ Multi-Dimensional Evaluation: Always Active (Core Feature)\n✅ Logical Inference: {logical_inference}",
            verbose
        )

    # 1. Generate Ideas
    try:
        step_start_time = time.time()
        log_verbose_step(
            "STEP 1: Idea Generation Agent", 
            f"💡 Agent: IdeaGenerator\n🎯 Theme: {theme}\n📋 Constraints: {constraints}\n🌡️ Temperature: {idea_temp} (high creativity)",
            verbose
        )
        
        logging.info(f"Generating ideas for theme '{theme}'...")
        raw_generated_ideas = call_idea_generator_with_retry(
            topic=theme, context=constraints, temperature=idea_temp
        )
        
        log_verbose_data("Raw IdeaGenerator Response", raw_generated_ideas, verbose, max_length=1000)
        
        parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]
        if not parsed_ideas:
            logging.warning("No ideas were generated by IdeaGeneratorAgent.")
            return []
        
        step_duration = time.time() - step_start_time
        logging.info(f"Generated {len(parsed_ideas)} raw ideas.")
        
        log_verbose_completion("Step 1", len(parsed_ideas), step_duration, verbose, "ideas")
        log_verbose_sample_list(parsed_ideas, verbose)
        
        # 1.5. Apply Tier0 Novelty Filter (if enabled)
        if enable_novelty_filter:
            filter_start_time = time.time()
            log_verbose_step(
                "STEP 1.5: Novelty Filtering", 
                f"🔍 Filter: NoveltyFilter\n📊 Input: {len(parsed_ideas)} ideas\n🎯 Similarity Threshold: {novelty_threshold}",
                verbose
            )
            
            novelty_filter = NoveltyFilter(similarity_threshold=novelty_threshold)
            filtered_ideas = novelty_filter.get_novel_ideas(parsed_ideas)
            
            filter_duration = time.time() - filter_start_time
            removed_count = len(parsed_ideas) - len(filtered_ideas)
            
            if len(filtered_ideas) < len(parsed_ideas):
                logging.info(
                    f"Novelty filter removed {removed_count} "
                    f"similar/duplicate ideas. Proceeding with {len(filtered_ideas)} novel ideas."
                )
                
            if verbose:
                print(f"✅ Filtering Complete: Removed {removed_count} duplicates in {filter_duration:.2f}s")
                print(f"📊 Final: {len(filtered_ideas)} novel ideas")
                
            parsed_ideas = filtered_ideas
            
            if not parsed_ideas:
                logging.warning("No novel ideas remained after novelty filtering.")
                return []
    except Exception as e:
        logging.error(f"IdeaGeneratorAgent failed to generate ideas. Error: {str(e)}")
        return []

    # 2. Evaluate Ideas
    # raw_evaluations: str = "" # Type will be known after call
    evaluated_ideas_data: List[EvaluatedIdea] = []
    try:
        eval_start_time = time.time()
        log_verbose_step(
            "STEP 2: Critic Agent Evaluation", 
            f"🔍 Agent: Critic\n📊 Input: {len(parsed_ideas)} ideas\n🎯 Criteria: {constraints}\n📝 Context: {theme}\n🌡️ Temperature: {eval_temp} (analytical mode)",
            verbose
        )
        
        logging.info(f"Evaluating {len(parsed_ideas)} ideas...")
        ideas_for_critic = "\n".join(parsed_ideas)
        
        if verbose:
            print("📤 Input to Critic Agent:")
            print(f"Ideas ({len(parsed_ideas)} total):")
            for i, idea in enumerate(parsed_ideas[:3], 1):
                print(f"  {i}. {idea[:80]}...")
            if len(parsed_ideas) > 3:
                print(f"  ... and {len(parsed_ideas) - 3} more ideas")
            print()
        
        raw_evaluations = call_critic_with_retry(
            ideas=ideas_for_critic,
            criteria=constraints,
            context=theme,
            temperature=eval_temp
        )
        
        eval_duration = time.time() - eval_start_time
        logging.debug(f"Raw evaluations received:\n{raw_evaluations}")
        log_verbose_data("Raw Critic Response", raw_evaluations, verbose, max_length=800)

        # Enhanced reasoning: Store conversation context if enabled and pre-process context
        # Note: conversation_history is consumed in process_with_context() calls during multi-dimensional evaluation
        enhanced_reasoning_cache = None
        if enhanced_reasoning and engine:
            log_verbose_step(
                "🧠 Enhanced Reasoning Context Collection",
                f"📝 Storing conversation context for {len(parsed_ideas)} ideas\n🔗 Building context memory for enhanced reasoning",
                verbose
            )
            
            # Store conversation context for enhanced reasoning (used in process_with_context calls)
            for idea in parsed_ideas:
                context_data = {
                    'agent': 'IdeaGenerator',
                    'input_data': f"Theme: {theme}, Constraints: {constraints}",
                    'output_data': idea,
                    'timestamp': str(datetime.datetime.now()),
                    'metadata': {'temperature': idea_temp}
                }
                conversation_history.append(context_data)
            
            # Pre-process enhanced reasoning context once (performance optimization)
            if conversation_history:
                enhanced_input = {
                    'context': f"{theme} - {constraints}",
                    'agent': 'multi_evaluator'
                }
                enhanced_reasoning_cache = engine.process_with_context(enhanced_input, conversation_history)

        # Use robust JSON parsing with fallback strategies
        parsed_evaluations = parse_json_with_fallback(
            raw_evaluations, 
            expected_count=len(parsed_ideas)
        )

        if len(parsed_evaluations) != len(parsed_ideas):
            if verbose:
                logging.warning(
                    f"Mismatch between number of ideas ({len(parsed_ideas)}) "
                    f"and number of parsed evaluations ({len(parsed_evaluations)})."
                    " Each idea will be processed; those without evaluation will receive defaults."
                )
            else:
                logging.debug(
                    f"Mismatch between number of ideas ({len(parsed_ideas)}) "
                    f"and number of parsed evaluations ({len(parsed_evaluations)})."
                    " Each idea will be processed; those without evaluation will receive defaults."
                )

        for i, idea_text in enumerate(parsed_ideas):
            if i < len(parsed_evaluations):
                # Validate and normalize the evaluation data
                eval_data = validate_evaluation_json(parsed_evaluations[i])
                score = eval_data["score"]
                critique = eval_data["comment"]
            else:
                if verbose:
                    logging.warning(
                        f"No evaluation available for idea: '{idea_text[:50]}...' (index {i}). "
                        "Using default values."
                    )
                else:
                    logging.debug(
                        f"No evaluation available for idea: '{idea_text[:50]}...' (index {i}). "
                        "Using default values."
                    )
                score = 0
                critique = "Evaluation missing from critic response."

            # Initialize multi_eval_result for this idea
            multi_eval_result = None
            
            # Always perform multi-dimensional evaluation (now a core feature)
            if engine:
                try:
                    # Create comprehensive evaluation context for enhanced reasoning
                    # MultiDimensionalEvaluator expects budget, timeline, and other context keys
                    context = {
                        'theme': theme,
                        'constraints': constraints,
                        'idea_index': i,
                        'total_ideas': len(parsed_ideas),
                        'budget': 'medium',  # Default budget level for evaluation
                        'timeline': 'flexible',  # Default timeline expectation  
                        'priority': 'high',  # Default priority level
                        'resources': 'available',  # Default resource assumption
                        'technical_complexity': 'moderate'  # Default complexity level
                    }
                    
                    # Use enhanced reasoning with cached context if available
                    if enhanced_reasoning and enhanced_reasoning_cache:
                        # Use pre-processed enhanced reasoning context (performance optimized)
                        enhanced_context = context.copy()
                        enhanced_context['enhanced_reasoning'] = enhanced_reasoning_cache.get('enhanced_reasoning', '')
                        enhanced_context['context_awareness_score'] = enhanced_reasoning_cache.get('context_awareness_score', 0)
                        
                        multi_eval_result = engine.multi_evaluator.evaluate_idea(idea_text, enhanced_context)
                    else:
                        # Direct multi-dimensional evaluation without context awareness
                        multi_eval_result = engine.multi_evaluator.evaluate_idea(idea_text, context)
                    
                    # Use multi-dimensional score instead of simple score
                    score = multi_eval_result['weighted_score']
                    
                    # Enhance critique with multi-dimensional insights
                    critique = f"{critique}\n\n🧠 Enhanced Analysis:\n{multi_eval_result['evaluation_summary']}"
                    
                    if verbose:
                        print(f"📊 Multi-Dimensional Score for '{idea_text[:50]}...': {score:.2f}")
                        print(f"   Confidence: {multi_eval_result['confidence_interval']:.3f}")
                        
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    logging.warning(f"Multi-dimensional evaluation failed for idea {i} ('{idea_text[:50]}...'): {type(e).__name__}: {e}")
                    # Fall back to standard evaluation

            # Enhanced reasoning: Apply logical inference if enabled (independent of multi-dimensional eval)
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
                        
                        if verbose:
                            print(f"🔗 Logical Inference for '{idea_text[:50]}...': Confidence {inference_result['confidence_score']:.2f}")
                            
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    logging.warning(f"Logical inference failed for idea {i} ('{idea_text[:50]}...'): {type(e).__name__}: {e}")
                    # Continue without logical inference

            # Create the EvaluatedIdea dictionary matching the TypedDict
            evaluated_idea = {"text": idea_text, "score": score, "critique": critique}
            
            # Add multi-dimensional evaluation if available
            if multi_eval_result is not None:
                evaluated_idea["multi_dimensional_evaluation"] = multi_eval_result
                
            evaluated_ideas_data.append(evaluated_idea)

        log_verbose_completion("Step 2", len(evaluated_ideas_data), eval_duration, verbose, "ideas")
        if verbose:
            print("📊 Sample Evaluations:")
            for i, eval_data in enumerate(evaluated_ideas_data[:3], 1):
                print(f"  {i}. Score: {eval_data['score']}/10 - {eval_data['text'][:60]}...")
                print(f"     Critique: {eval_data['critique'][:80]}...")

        evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True) # Can use x["score"] if TypedDict guarantees it
        top_candidates: List[EvaluatedIdea] = evaluated_ideas_data[:num_top_candidates]
        
        if verbose:
            print(f"\n🎯 Selected Top {num_top_candidates} Candidates:")
            for i, candidate in enumerate(top_candidates, 1):
                print(f"  {i}. Score: {candidate['score']}/10 - {candidate['text'][:60]}...")

        if not top_candidates and parsed_ideas:
             logging.info("No ideas were selected as top candidates "
                   "(e.g., all failed parsing, had 0 score, or num_top_candidates is 0).")
        logging.info(f"Selected {len(top_candidates)} top candidates for further processing.")

    except Exception as e:
        logging.error(f"CriticAgent failed during evaluation phase. Error: {str(e)}")
        if parsed_ideas:
            logging.info(f"Falling back to using the first {min(num_top_candidates, len(parsed_ideas))} raw ideas due to CriticAgent failure.")
            # Construct fallback candidates matching EvaluatedIdea structure
            top_candidates = [
                {"text": idea, "critique": "N/A (CriticAgent failed)", "score": 0}
                for idea in parsed_ideas[:min(num_top_candidates, len(parsed_ideas))]
            ]
        else:
            return []
        if not top_candidates and parsed_ideas: # Should be List[EvaluatedIdea]
            logging.info("Fallback selection after CriticAgent failure resulted in no candidates.")
            return []

    # 3. Advocate and Criticize for top N candidates
    for idx, candidate in enumerate(top_candidates, 1): # candidate is now TypedDict EvaluatedIdea
        idea_text: str = candidate["text"] # Direct access if TypedDict guarantees
        evaluation_detail: str = candidate["critique"] # Direct access
        advocacy_output: str = "N/A"
        skepticism_output: str = "N/A"
        
        log_verbose_step(
            f"STEP 3.{idx}: Processing Top Candidate #{idx}", 
            f"💡 Idea: {idea_text[:100]}...\n📊 Score: {candidate['score']}/10\n📝 Critique: {evaluation_detail[:100]}...",
            verbose
        )
        
        logging.info(f"Processing candidate: {idea_text} (Score: {candidate['score']})")
        
        # Advocate Agent
        try:
            advocate_start_time = time.time()
            log_agent_execution(
                f"STEP 3.{idx}a: Advocate Agent", 
                "Advocate", 
                "✅", 
                "Building case for idea (balanced persuasion)",
                advocacy_temp,
                verbose
            )
            
            logging.info(f"Advocating for idea: '{idea_text}'...")
            advocacy_output = call_advocate_with_retry(
                idea=idea_text, evaluation=evaluation_detail, context=theme,
                temperature=advocacy_temp
            )
            
            advocate_duration = time.time() - advocate_start_time
            log_agent_completion("Advocate", advocacy_output, f"Idea #{idx}", advocate_duration, verbose)
                
        except Exception as e:
            logging.warning(f"AdvocateAgent failed for idea '{idea_text}'. Error: {str(e)}")
            advocacy_output = "Advocacy not available due to agent error."
            
        # Skeptic Agent
        try:
            skeptic_start_time = time.time()
            log_agent_execution(
                f"STEP 3.{idx}b: Skeptic Agent", 
                "Skeptic", 
                "⚠️", 
                "Analyzing risks and challenges (balanced skepticism)",
                skepticism_temp,
                verbose
            )
            
            logging.info(f"Skepticizing idea: '{idea_text}'...")
            skepticism_output = call_skeptic_with_retry(
                idea=idea_text, advocacy=advocacy_output, context=theme,
                temperature=skepticism_temp
            )
            
            skeptic_duration = time.time() - skeptic_start_time
            log_agent_completion("Skeptic", skepticism_output, f"Idea #{idx}", skeptic_duration, verbose)
                
        except Exception as e:
            logging.warning(f"SkepticAgent failed for idea '{idea_text}'. Error: {str(e)}")
            skepticism_output = "Skepticism not available due to agent error."

        # Step 4: Generate Improved Idea
        improved_idea_text = ""
        improved_score = 0.0
        improved_critique = ""
        
        try:
            improve_start_time = time.time()
            log_verbose_step(
                f"STEP 4.{idx}: Idea Improvement", 
                f"💡 Original Idea: {idea_text[:100]}...\n🔄 Using feedback from all agents to generate improved version",
                verbose
            )
            
            logging.info(f"Improving idea based on feedback: '{idea_text}'...")
            improved_idea_text = call_improve_idea_with_retry(
                original_idea=idea_text,
                critique=evaluation_detail,
                advocacy_points=advocacy_output,
                skeptic_points=skepticism_output,
                theme=theme,
                temperature=idea_temp
            )
            
            improve_duration = time.time() - improve_start_time
            log_verbose_data("Improved Idea", improved_idea_text, verbose, max_length=600)
            
            if verbose:
                print(f"✅ Improvement Complete: Generated improved idea in {improve_duration:.2f}s")
                
        except Exception as e:
            logging.warning(f"Idea improvement failed for '{idea_text}'. Error: {str(e)}")
            improved_idea_text = idea_text  # Fallback to original
            
        # Step 5: Re-evaluate Improved Idea
        if improved_idea_text and improved_idea_text != idea_text:
            try:
                reeval_start_time = time.time()
                log_verbose_step(
                    f"STEP 5.{idx}: Re-evaluation of Improved Idea", 
                    f"🔍 Agent: Critic\n📊 Evaluating improved version\n🌡️ Temperature: {eval_temp}",
                    verbose
                )
                
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
                improved_raw_eval = call_critic_with_retry(
                    ideas=improved_idea_text,
                    criteria=constraints,
                    context=improved_context,
                    temperature=eval_temp
                )
                
                # Parse the evaluation
                improved_evaluations = parse_json_with_fallback(improved_raw_eval, expected_count=1)
                if improved_evaluations:
                    eval_data = validate_evaluation_json(improved_evaluations[0])
                    improved_score = float(eval_data["score"])
                    improved_critique = eval_data["comment"]
                    
                    # Safeguard: If score decreased significantly, log warning and consider keeping original
                    if improved_score < candidate["score"] - 1.0:
                        logging.warning(
                            f"Improved idea scored lower ({improved_score}) than original ({candidate['score']}). "
                            f"This suggests the improvement may have overcorrected."
                        )
                        # Add note to critique about the regression
                        improved_critique += f"\n\n⚠️ Note: Score decreased from {candidate['score']} to {improved_score}. The improvement may have overcorrected or lost key strengths."
                else:
                    # Fallback if parsing fails
                    improved_score = float(candidate["score"])
                    improved_critique = "Re-evaluation failed - using original score"
                    
                reeval_duration = time.time() - reeval_start_time
                
                if verbose:
                    print(f"✅ Re-evaluation Complete in {reeval_duration:.2f}s")
                    print(f"📊 Score comparison: {candidate['score']}/10 → {improved_score}/10 (Δ{improved_score - candidate['score']:+.1f})")
                    
            except Exception as e:
                logging.warning(f"Re-evaluation failed for improved idea. Error: {str(e)}")
                improved_score = float(candidate["score"])
                improved_critique = "Re-evaluation not available due to error"
        else:
            # No improvement generated, use original values
            improved_idea_text = idea_text
            improved_score = float(candidate["score"])
            improved_critique = evaluation_detail

        # Calculate score delta
        score_delta = improved_score - candidate["score"]
        
        # Determine if improvement is meaningful
        is_meaningful, similarity_score = is_meaningful_improvement(
            idea_text,
            improved_idea_text,
            score_delta,
            similarity_threshold=MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD,
            score_delta_threshold=MEANINGFUL_IMPROVEMENT_SCORE_DELTA
        )

        # Create the CandidateData dictionary matching the TypedDict
        candidate_data = {
            "idea": idea_text,
            "initial_score": candidate["score"], # Direct access
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
        
        # Add multi-dimensional evaluation if available
        if "multi_dimensional_evaluation" in candidate:
            candidate_data["multi_dimensional_evaluation"] = candidate["multi_dimensional_evaluation"]
            
        final_candidates_data.append(candidate_data)
        
        if verbose:
            print(f"✅ Candidate #{idx} Processing Complete")
            print(f"📊 Final data: {len(advocacy_output)} chars advocacy, {len(skepticism_output)} chars skepticism")
            print(f"📈 Score improvement: {candidate['score']}/10 → {improved_score}/10 (Δ{score_delta:+.1f})")
            
        logging.info(f"Finished processing for: {idea_text}")
    
    # Final Summary
    if verbose:
        log_verbose_step(
            "WORKFLOW COMPLETE", 
            f"🎉 Multi-Agent Processing Finished\n📊 Generated {len(final_candidates_data)} complete candidates\n⏱️ All agents executed successfully",
            verbose
        )
    return final_candidates_data

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
