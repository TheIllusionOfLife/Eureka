"""Critic Agent.

This module defines the Critic agent and its associated tools.
The agent is responsible for evaluating ideas based on specified criteria
and context, providing scores and textual feedback.
"""
import os
from typing import Any
import google.generativeai as genai

# Configure the Google GenerativeAI client
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

if api_key:
    genai.configure(api_key=api_key)
    # Create the model instance
    critic_model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=(
            "You are an expert critic. Evaluate the given ideas based on the"
            " provided criteria and context. Provide constructive feedback and"
            " identify potential weaknesses."
        )
    )
else:
    critic_model = None


def evaluate_ideas(ideas: str, criteria: str, context: str, temperature: float = 0.3) -> str:
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
  
  if critic_model is None:
    raise RuntimeError("GOOGLE_API_KEY not configured - cannot evaluate ideas")
  
  try:
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = critic_model.generate_content(prompt, generation_config=generation_config)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Return empty string on any API error - coordinator will handle this
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


