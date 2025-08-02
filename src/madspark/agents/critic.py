"""Critic Agent.

This module defines the Critic agent and its associated tools.
The agent is responsible for evaluating ideas based on specified criteria
and context, providing scores and textual feedback.
"""
import logging

# Optional import for Google GenAI - graceful fallback for CI/testing
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

try:
    from madspark.agents.genai_client import get_genai_client, get_model_name
    from madspark.utils.constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE, LANGUAGE_CONSISTENCY_INSTRUCTION
except ImportError:
    # Fallback for local development/testing
    from .genai_client import get_genai_client, get_model_name
    from constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE, LANGUAGE_CONSISTENCY_INSTRUCTION

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    critic_client = get_genai_client()
    model_name = get_model_name()
else:
    critic_client = None
    model_name = "mock-model"


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
      LANGUAGE_CONSISTENCY_INSTRUCTION +
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
  
  if not GENAI_AVAILABLE or critic_client is None:
    # Return mock evaluation for CI/testing environments or when API key is not configured
    # Simple language detection for mock responses
    combined_text = ideas + criteria + context
    if any(char >= '\u3040' and char <= '\u309F' or char >= '\u30A0' and char <= '\u30FF' or char >= '\u4E00' and char <= '\u9FAF' for char in combined_text):
        return '{"score": 8, "comment": "テスト用のモック評価"}'
    elif any(char in 'àâäæéèêëïîôöùûüÿ' for char in combined_text.lower()):
        return '{"score": 8, "comment": "Évaluation factice pour les tests"}'
    elif any(char in 'ñáíóúüç' for char in combined_text.lower()):
        return '{"score": 8, "comment": "Evaluación simulada para pruebas"}'
    elif any(char in 'äöüß' for char in combined_text.lower()):
        return '{"score": 8, "comment": "Mock-Bewertung für Tests"}'
    else:
        return '{"score": 8, "comment": "Mock evaluation for testing"}'
  
  if critic_client is None:
    from madspark.utils.errors import ConfigurationError
    raise ConfigurationError("Critic client is not configured but GENAI is enabled")
  
  try:
    config = genai.types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=CRITIC_SYSTEM_INSTRUCTION
    )
    response = critic_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except (AttributeError, ValueError, RuntimeError) as e:
    # Return empty string on API/connection errors - coordinator will handle this
    logging.error(f"Error calling Gemini API in criticize_ideas: {e}", exc_info=True)
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


