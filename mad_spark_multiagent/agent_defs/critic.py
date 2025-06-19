"""Critic Agent.

This module defines the Critic agent and its associated tools.
The agent is responsible for evaluating ideas based on specified criteria
and context, providing scores and textual feedback.
"""
import os
from typing import Any # For model type, if not specifically known

from google.adk.agents import Agent
from google.adk.agents import Tool

# The Critic agent evaluates ideas, providing scores and constructive feedback.
critic_agent: Agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"), # type: ignore
    instructions=(
        "You are an expert critic. Evaluate the given ideas based on the"
        " provided criteria and context. Provide constructive feedback and"
        " identify potential weaknesses."
    ),
)


@Tool(
    name="evaluate_ideas",
    description=(
        "Evaluates a list of ideas based on given criteria and context,"
        " providing constructive feedback in a structured JSON format."
    ),
)
def evaluate_ideas(ideas: str, criteria: str, context: str) -> str:
  """Evaluates ideas based on criteria and context using the critic_agent.

  The agent is prompted to return a newline-separated list of JSON strings.
  Each JSON string should contain 'score' and 'comment' for an idea,
  corresponding to the input order.

  Args:
    ideas: A string containing the ideas to be evaluated, typically newline-separated.
    criteria: The criteria against which the ideas should be evaluated.
    context: Additional context relevant for the evaluation.

  Returns:
    A string from the LLM, expected to be newline-separated JSON objects,
    each representing an evaluation for an idea. Returns an empty string if
    the agent provides no content.
  Raises:
    ValueError: If ideas, criteria, or context are empty or invalid.
  """
  if not isinstance(ideas, str) or not ideas.strip():
    raise ValueError("Input 'ideas' to evaluate_ideas must be a non-empty string.")
  if not isinstance(criteria, str) or not criteria.strip():
    raise ValueError("Input 'criteria' to evaluate_ideas must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to evaluate_ideas must be a non-empty string.")

  prompt: str = (
      "You will be provided with a list of ideas, evaluation criteria, and context.\n"
      "For each idea, you MUST provide an evaluation in the form of a single-line JSON object string.\n"
      "Each JSON object must have exactly two keys: 'score' (an integer from 1 to 10, where 10 is best) "
      "and 'comment' (a concise string explaining your reasoning).\n"
      "Ensure your entire response consists ONLY of these JSON object strings, one per line, "
      "corresponding to each idea in the order they were presented.\n"
      "Do not include any other text, explanations, or formatting before or after the JSON strings.\n\n"
      f"Here are the ideas (one per line):\n{ideas}\n\n"
      f"Evaluation Criteria:\n{criteria}\n\n"
      f"Context for evaluation:\n{context}\n\n"
      "Provide your JSON evaluations now (one per line, in the same order as the input ideas):"
  )
  agent_response: Any = critic_agent.call(prompt=prompt)
  if not isinstance(agent_response, str):
    agent_response = str(agent_response) # Ensure it's a string

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


critic_agent.add_tools([evaluate_ideas])
