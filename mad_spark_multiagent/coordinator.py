"""Coordinator for the Mad Spark Multi-Agent Workflow.

This module orchestrates the interaction between various specialized agents
(Idea Generator, Critic, Advocate, Skeptic) to generate, evaluate, and
refine ideas based on a given theme and constraints.
# ... (rest of module docstring)
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, TypedDict # Added TypedDict

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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

from mad_spark_multiagent.agent_defs import (
    idea_generator_agent,
    critic_agent,
    advocate_agent,
    skeptic_agent,
)
from mad_spark_multiagent.utils import (
    exponential_backoff_retry,
    parse_json_with_fallback,
    validate_evaluation_json,
)
from mad_spark_multiagent.constants import (
    ADVOCATE_FAILED_PLACEHOLDER,
    SKEPTIC_FAILED_PLACEHOLDER,
)
# from google.adk.agents import Agent # No longer needed directly for hints here


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
def call_idea_generator_with_retry(topic: str, context: str) -> Any:
    """Call idea generator agent with retry logic."""
    return idea_generator_agent.call_tool("generate_ideas", topic=topic, context=context)


@exponential_backoff_retry(max_retries=3, initial_delay=2.0)
def call_critic_with_retry(ideas: str, criteria: str, context: str) -> str:
    """Call critic agent with retry logic."""
    return critic_agent.call_tool(
        "evaluate_ideas", ideas=ideas, criteria=criteria, context=context
    )


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def call_advocate_with_retry(idea: str, evaluation: str, context: str) -> Any:
    """Call advocate agent with retry logic."""
    return advocate_agent.call_tool(
        "advocate_idea", idea=idea, evaluation=evaluation, context=context
    )


@exponential_backoff_retry(max_retries=2, initial_delay=1.0)
def call_skeptic_with_retry(idea: str, advocacy: str, context: str) -> Any:
    """Call skeptic agent with retry logic."""
    return skeptic_agent.call_tool(
        "criticize_idea", idea=idea, advocacy=advocacy, context=context
    )


def run_multistep_workflow(
    theme: str, constraints: str, num_top_candidates: int = 2
) -> List[CandidateData]:
    """
    Runs the multi-step idea generation and refinement workflow.
    # ... (rest of docstring)
    """
    final_candidates_data: List[CandidateData] = []
    # raw_generated_ideas: str = "" # Type will be known after call
    parsed_ideas: List[str] = []

    # 1. Generate Ideas
    try:
        logging.info(f"Generating ideas for theme '{theme}'...")
        agent_response_ideas: Any = call_idea_generator_with_retry(
            topic=theme, context=constraints
        )
        # Ensure the response is treated as a string, as expected from generate_ideas tool
        raw_generated_ideas: str = str(agent_response_ideas)

        parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]
        if not parsed_ideas:
            logging.warning("No ideas were generated by IdeaGeneratorAgent.")
            return []
        logging.info(f"Generated {len(parsed_ideas)} raw ideas.")
    except Exception as e:
        logging.error(f"IdeaGeneratorAgent failed to generate ideas. Error: {str(e)}")
        return []

    # 2. Evaluate Ideas
    # raw_evaluations: str = "" # Type will be known after call
    evaluated_ideas_data: List[EvaluatedIdea] = []
    try:
        logging.info(f"Evaluating {len(parsed_ideas)} ideas...")
        agent_response_evals: Any = call_critic_with_retry(
            ideas="\n".join(parsed_ideas),
            criteria=constraints,
            context=theme
        )
        # Ensure the response is treated as a string, as expected from evaluate_ideas tool
        raw_evaluations: str = str(agent_response_evals)
        logging.debug(f"Raw evaluations received:\n{raw_evaluations}")

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


        evaluated_ideas_data.sort(key=lambda x: x["score"], reverse=True) # Can use x["score"] if TypedDict guarantees it
        top_candidates: List[EvaluatedIdea] = evaluated_ideas_data[:num_top_candidates]

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
    for candidate in top_candidates: # candidate is now TypedDict EvaluatedIdea
        idea_text: str = candidate["text"] # Direct access if TypedDict guarantees
        evaluation_detail: str = candidate["critique"] # Direct access
        advocacy_output: str = "N/A"
        skepticism_output: str = "N/A"
        logging.info(f"Processing candidate: {idea_text} (Score: {candidate['score']})")
        try:
            logging.info(f"Advocating for idea: '{idea_text}'...")
            agent_advocate_response: Any = call_advocate_with_retry(
                idea=idea_text, evaluation=evaluation_detail, context=theme
            )
            # Ensure the response is treated as a string
            advocacy_output = str(agent_advocate_response)
            if not advocacy_output.strip():
                 advocacy_output = ADVOCATE_FAILED_PLACEHOLDER
        except Exception as e:
            logging.warning(f"AdvocateAgent failed for idea '{idea_text}'. Error: {str(e)}")
            advocacy_output = "Advocacy not available due to agent error."
        try:
            logging.info(f"Skepticizing idea: '{idea_text}'...")
            agent_skeptic_response: Any = call_skeptic_with_retry(
                idea=idea_text, advocacy=advocacy_output, context=theme
            )
            # Ensure the response is treated as a string
            skepticism_output = str(agent_skeptic_response)
            if not skepticism_output.strip():
                skepticism_output = SKEPTIC_FAILED_PLACEHOLDER
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
        logging.info(f"Finished processing for: {idea_text}")
    return final_candidates_data

if __name__ == "__main__":
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
