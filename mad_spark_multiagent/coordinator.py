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
from typing import List, Dict, Any, Optional, TypedDict # Added TypedDict

# --- Logging Configuration ---
# Note: Logging configuration is now handled by CLI to avoid conflicts
# If running coordinator.py directly, basic logging will be set up below
# --- End Logging Configuration ---

# SECURITY NOTE: Storing API keys directly in environment variables is suitable for
# local development but not recommended for production.
# Consider using a dedicated secret management service for production deployments.

try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        logging.info("Coordinator: .env file found, loading environment variables.")
        load_dotenv()
    else:
        logging.info("Coordinator: .env file not found, relying on environment variables.")
except ImportError:
    logging.warning(
        "Coordinator: python-dotenv not found, .env file will not be loaded.\n"
        "Ensure GOOGLE_API_KEY and GOOGLE_GENAI_MODEL are set in your environment."
    )

api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
model_name: Optional[str] = os.getenv("GOOGLE_GENAI_MODEL")

if not api_key:
    logging.critical("\nFATAL: GOOGLE_API_KEY is not set in the environment or .env file.")
    # ... (rest of fatal error messages for API key)
    exit(1)
else:
    os.environ["GOOGLE_API_KEY"] = api_key

if not model_name:
    logging.critical("\nFATAL: GOOGLE_GENAI_MODEL is not set in the environment or .env file.")
    # ... (rest of fatal error messages for model name)
    exit(1)
else:
    os.environ["GOOGLE_GENAI_MODEL"] = model_name

try:
    from mad_spark_multiagent.agent_defs.idea_generator import generate_ideas
    from mad_spark_multiagent.agent_defs.critic import evaluate_ideas
    from mad_spark_multiagent.agent_defs.advocate import advocate_idea
    from mad_spark_multiagent.agent_defs.skeptic import criticize_idea
except ImportError:
    # Fallback for local development/testing
    from agent_defs.idea_generator import generate_ideas
    from agent_defs.critic import evaluate_ideas
    from agent_defs.advocate import advocate_idea
    from agent_defs.skeptic import criticize_idea
try:
    from mad_spark_multiagent.utils import (
        exponential_backoff_retry,
        parse_json_with_fallback,
        validate_evaluation_json,
    )
    from mad_spark_multiagent.novelty_filter import NoveltyFilter
    from mad_spark_multiagent.temperature_control import TemperatureManager
    from mad_spark_multiagent.constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_EVALUATION_TEMPERATURE, 
        DEFAULT_ADVOCACY_TEMPERATURE,
        DEFAULT_SKEPTICISM_TEMPERATURE
    )
except ImportError:
    # Fallback for local development/testing
    from utils import (
        exponential_backoff_retry,
        parse_json_with_fallback,
        validate_evaluation_json,
    )
    from novelty_filter import NoveltyFilter
    from temperature_control import TemperatureManager
    from constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_EVALUATION_TEMPERATURE, 
        DEFAULT_ADVOCACY_TEMPERATURE,
        DEFAULT_SKEPTICISM_TEMPERATURE
    )
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

class CandidateData(TypedDict):
    """Structure for the final data compiled for each candidate idea."""
    idea: str
    initial_score: int
    initial_critique: str
    advocacy: str
    skepticism: str
# --- End TypedDict Definitions ---


# Create retry-wrapped versions of agent calls
@exponential_backoff_retry(max_retries=3, initial_delay=2.0)
def call_idea_generator_with_retry(topic: str, context: str, temperature: float = 0.9) -> str:
    """Call idea generator with retry logic."""
    return generate_ideas(topic=topic, context=context, temperature=temperature)


@exponential_backoff_retry(max_retries=3, initial_delay=2.0)
def call_critic_with_retry(ideas: str, criteria: str, context: str, temperature: float = 0.3) -> str:
    """Call critic with retry logic."""
    return evaluate_ideas(ideas=ideas, criteria=criteria, context=context, temperature=temperature)


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def call_advocate_with_retry(idea: str, evaluation: str, context: str, temperature: float = 0.5) -> str:
    """Call advocate with retry logic."""
    return advocate_idea(idea=idea, evaluation=evaluation, context=context, temperature=temperature)


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def call_skeptic_with_retry(idea: str, advocacy: str, context: str, temperature: float = 0.5) -> str:
    """Call skeptic with retry logic."""
    return criticize_idea(idea=idea, advocacy=advocacy, context=context, temperature=temperature)


def run_multistep_workflow(
    theme: str, constraints: str, num_top_candidates: int = 2, 
    enable_novelty_filter: bool = True, novelty_threshold: float = 0.8,
    temperature_manager: Optional['TemperatureManager'] = None,
    verbose: bool = False
) -> List[CandidateData]:
    """
    Runs the multi-step idea generation and refinement workflow.
    # ... (rest of docstring)
    """
    final_candidates_data: List[CandidateData] = []
    # raw_generated_ideas: str = "" # Type will be known after call
    parsed_ideas: List[str] = []

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

        # Use robust JSON parsing with fallback strategies
        parsed_evaluations = parse_json_with_fallback(
            raw_evaluations, 
            expected_count=len(parsed_ideas)
        )

        if len(parsed_evaluations) != len(parsed_ideas):
            logging.warning(
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
                logging.warning(
                    f"No evaluation available for idea: '{idea_text[:50]}...' (index {i}). "
                    "Using default values."
                )
                score = 0
                critique = "Evaluation missing from critic response."

            # Create the EvaluatedIdea dictionary matching the TypedDict
            evaluated_ideas_data.append({"text": idea_text, "score": score, "critique": critique})

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

        # Create the CandidateData dictionary matching the TypedDict
        final_candidates_data.append({
            "idea": idea_text,
            "initial_score": candidate["score"], # Direct access
            "initial_critique": evaluation_detail,
            "advocacy": advocacy_output,
            "skepticism": skepticism_output,
        })
        
        if verbose:
            print(f"✅ Candidate #{idx} Processing Complete")
            print(f"📊 Final data: {len(advocacy_output)} chars advocacy, {len(skepticism_output)} chars skepticism")
            
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
