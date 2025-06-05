import os
import json
from typing import List, Dict, Any

# Ensure GOOGLE_API_KEY is set for the ADK
# In a real application, prefer to use a .env file or other secret management
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
# Attempt to load .env if python-dotenv is available and .env exists
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
        # Re-set GOOGLE_API_KEY if it was loaded from .env
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
except ImportError:
    print("python-dotenv not found, .env file will not be loaded.")


# Check if the API key is actually set, otherwise agents will fail.
if not os.environ.get("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY is not set. Agent calls will likely fail.")
    # Provide a dummy key for the ADK to initialize, actual calls would fail
    os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"


from mad_spark_multiagent.agent_defs import (
    idea_generator_agent,
    critic_agent,
    advocate_agent,
    skeptic_agent,
)


def run_multistep_workflow(
    theme: str, constraints: str, num_top_candidates: int = 2
) -> List[Dict[str, Any]]:
    """
    Runs a multi-step workflow involving idea generation, criticism,
    advocacy, and skepticism.
    """
    final_candidates_data = []
    raw_generated_ideas = ""
    parsed_ideas = []

    # 1. Generate Ideas
    try:
        print(f"Coordinator: Generating ideas for theme '{theme}'...")
        raw_generated_ideas = idea_generator_agent.call_tool(
            "generate_ideas", topic=theme, context=constraints
        )
        # Assuming ideas are returned as a newline-separated list
        parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]
        if not parsed_ideas:
            print("Coordinator: No ideas were generated.")
            return []
        print(f"Coordinator: Generated {len(parsed_ideas)} raw ideas.")
    except Exception as e:
        print(f"Coordinator: Error generating ideas: {e}")
        return []

    # 2. Evaluate Ideas
    # For simplicity, we'll ask the critic to rank or score.
    # A more robust implementation would involve structured output from the critic.
    critic_prompt_context = (
        "Please evaluate the following list of ideas. For each idea, provide a brief"
        " critique and a score from 1 (worst) to 10 (best). Present the results as a"
        " list, with each item starting with 'Idea: <idea text>', followed by"
        " 'Critique: <critique text>', and 'Score: <score>'. Rank the ideas from"
        " best to worst if possible."
    )
    raw_evaluations = ""
    evaluated_ideas_data = []

    try:
        print(f"Coordinator: Evaluating {len(parsed_ideas)} ideas...")
        raw_evaluations = critic_agent.call_tool(
            "evaluate_ideas",
            ideas="\n".join(parsed_ideas),
            criteria=constraints,
            context=f"{theme}\n{critic_prompt_context}",
        )
        print(f"Coordinator: Raw evaluations received:\n{raw_evaluations}")

        # Simplistic parsing of evaluations (assumes structure from prompt)
        current_idea_info = {}
        for line in raw_evaluations.split("\n"):
            line = line.strip()
            if line.startswith("Idea:"):
                if current_idea_info: # save previous idea
                    evaluated_ideas_data.append(current_idea_info)
                current_idea_info = {"text": line.replace("Idea:", "").strip(), "score": 0, "critique": ""}
            elif line.startswith("Critique:"):
                if current_idea_info:
                    current_idea_info["critique"] = line.replace("Critique:", "").strip()
            elif line.startswith("Score:"):
                if current_idea_info:
                    try:
                        current_idea_info["score"] = int(line.replace("Score:", "").strip())
                    except ValueError:
                        current_idea_info["score"] = 0 # Default score if parsing fails
        if current_idea_info: # Append last idea
            evaluated_ideas_data.append(current_idea_info)

        # Sort by score (descending) and filter out ideas that weren't parsed correctly
        evaluated_ideas_data.sort(key=lambda x: x.get("score", 0), reverse=True)
        # Ensure we only select ideas that were actually found in the critic's output
        top_candidates = [
            data for data in evaluated_ideas_data
            if data.get("text") and data.get("text") in parsed_ideas
        ][:num_top_candidates]

        if not top_candidates:
            print("Coordinator: No ideas were properly evaluated or scored.")
            # Fallback: if parsing failed, take the first N raw ideas if critic failed
            if not evaluated_ideas_data and parsed_ideas:
                 print(f"Coordinator: Falling back to using the first {num_top_candidates} raw ideas due to evaluation parsing failure.")
                 top_candidates = [{"text": idea, "critique": "N/A (evaluation parsing failed)", "score": 0} for idea in parsed_ideas[:num_top_candidates]]
            else:
                 return []


        print(f"Coordinator: Selected {len(top_candidates)} top candidates based on evaluation.")

    except Exception as e:
        print(f"Coordinator: Error evaluating ideas: {e}")
        # Fallback: if critic agent fails, take the first N raw ideas
        print(f"Coordinator: Falling back to using the first {num_top_candidates} raw ideas due to critic agent failure.")
        top_candidates = [{"text": idea, "critique": "N/A (critic agent failed)", "score": 0} for idea in parsed_ideas[:num_top_candidates]]
        if not top_candidates:
            return []


    # 3. Advocate and Criticize for top N candidates
    for candidate in top_candidates:
        idea_text = candidate.get("text", "Unknown Idea")
        evaluation_detail = candidate.get("critique", "N/A")
        advocacy_output = "N/A"
        skepticism_output = "N/A"

        print(f"\nCoordinator: Processing candidate: {idea_text}")

        # Advocate for the idea
        try:
            print(f"Coordinator: Advocating for idea: '{idea_text}'...")
            advocacy_output = advocate_agent.call_tool(
                "advocate_idea",
                idea=idea_text,
                evaluation=evaluation_detail,
                context=theme,
            )
        except Exception as e:
            print(f"Coordinator: Error advocating for idea '{idea_text}': {e}")
            advocacy_output = f"Error during advocacy: {e}"

        # Skeptic criticizes the idea + advocacy
        try:
            print(f"Coordinator: Skepticizing idea: '{idea_text}'...")
            skepticism_output = skeptic_agent.call_tool(
                "criticize_idea",
                idea=idea_text,
                advocacy=advocacy_output,
                context=theme,
            )
        except Exception as e:
            print(f"Coordinator: Error skepticizing idea '{idea_text}': {e}")
            skepticism_output = f"Error during skepticism: {e}"

        final_candidates_data.append({
            "idea": idea_text,
            "initial_score": candidate.get("score", 0),
            "initial_critique": evaluation_detail,
            "advocacy": advocacy_output,
            "skepticism": skepticism_output,
        })
        print(f"Coordinator: Finished processing for: {idea_text}")


    return final_candidates_data


if __name__ == "__main__":
    print("Starting Mad Spark Multi-Agent Workflow...")

    # Check for API key at the very beginning of the main execution
    if os.environ.get("GOOGLE_API_KEY") == "YOUR_API_KEY" or not os.environ.get("GOOGLE_API_KEY"):
        print("\nFATAL: GOOGLE_API_KEY is not set or is a placeholder.")
        print("Please set the GOOGLE_API_KEY environment variable to your actual API key.")
        print("You can set it in a .env file in the mad_spark_multiagent directory, for example:")
        print("GOOGLE_API_KEY='your_actual_api_key_here'")
        print("Ensure you have `python-dotenv` installed (`pip install python-dotenv`) for .env loading.")
        exit(1) # Exit if key is not set.

    sample_theme = "Sustainable Urban Living"
    sample_constraints = (
        "Ideas should be implementable within a typical city budget, focus on"
        " community involvement, and be technologically feasible within the next 5"
        " years. Ideas should also consider scalability and inclusivity."
    )
    num_ideas_to_process = 1 # Keep low for testing to avoid excessive API calls

    print(f"\nTheme: {sample_theme}")
    print(f"Constraints: {sample_constraints}")
    print(f"Number of top ideas to fully process: {num_ideas_to_process}\n")

    results = run_multistep_workflow(
        theme=sample_theme,
        constraints=sample_constraints,
        num_top_candidates=num_ideas_to_process
    )

    print("\n--- Final Results ---")
    if results:
        print(json.dumps(results, indent=2))
    else:
        print("No results were generated from the workflow.")

    print("\nMad Spark Multi-Agent Workflow Finished.")
