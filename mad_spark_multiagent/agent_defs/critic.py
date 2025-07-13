"""Critic Agent.

This module defines the Critic agent and its associated tools.
The agent is responsible for evaluating ideas based on specified criteria
and context, providing scores and textual feedback.
"""
import os
from typing import Any
from google import genai
from google.genai import types

try:
    from mad_spark_multiagent.errors import ConfigurationError
    from mad_spark_multiagent.agent_defs.genai_client import get_genai_client, get_model_name
    from mad_spark_multiagent.constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE
except ImportError:
    # Fallback for local development/testing
    from errors import ConfigurationError
    from agent_defs.genai_client import get_genai_client, get_model_name
    from constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE

# Configure the Google GenAI client
critic_client = get_genai_client()
model_name = get_model_name()


def evaluate_ideas(ideas: str, criteria: str, context: str, temperature: float = DEFAULT_CRITIC_TEMPERATURE) -> str:
  """Evaluates ideas based on criteria and context using the critic model.

  The model is prompted to return a newline-separated list of JSON strings.
  Each JSON string should contain 'score' and 'comment' for an idea,
  corresponding to the input order.

  Args:
    ideas: A string containing the ideas to be evaluated, typically newline-separated.
    criteria: The criteria against which the ideas should be evaluated.
    context: Additional context relevant for the evaluation.
    temperature: Controls randomness in generation (0.0-1.0). Lower values increase consistency.

  Returns:
    A string from the LLM, expected to be newline-separated JSON objects,
    each representing an evaluation for an idea. Returns an empty string if
    the model provides no content.
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
  
  if critic_client is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot evaluate ideas")
  
  try:
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=CRITIC_SYSTEM_INSTRUCTION
    )
    response = critic_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Return empty string on any API error - coordinator will handle this
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


