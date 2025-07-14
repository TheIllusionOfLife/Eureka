"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
"""
import os
import logging
from typing import Any

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
    from madspark.utils.constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.utils.errors import ConfigurationError
    from madspark.agents.genai_client import get_genai_client, get_model_name
except ImportError:
    # Fallback for local development/testing
    from constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from errors import ConfigurationError
    from .genai_client import get_genai_client, get_model_name

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    advocate_client = get_genai_client()
    model_name = get_model_name()
else:
    advocate_client = None
    model_name = "mock-model"


def advocate_idea(idea: str, evaluation: str, context: str, temperature: float = 0.5) -> str:
  """Advocates for an idea using its evaluation and context via the advocate model.

  Args:
    idea: The idea to advocate for.
    evaluation: The evaluation received for the idea (e.g., from a critic).
    context: Additional context relevant for building the advocacy.
    temperature: Controls randomness in generation (0.0-1.0). Balanced for argumentation.

  Returns:
    A string containing the persuasive arguments for the idea.
    Returns a placeholder string if the model provides no content.
  Raises:
    ValueError: If idea, evaluation, or context are empty or invalid.
  """
  if not isinstance(idea, str) or not idea.strip():
    raise ValueError("Input 'idea' to advocate_idea must be a non-empty string.")
  if not isinstance(evaluation, str) or not evaluation.strip():
    raise ValueError("Input 'evaluation' to advocate_idea must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to advocate_idea must be a non-empty string.")

  prompt: str = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Here's an idea:\n{idea}\n\n"
      f"Here's its evaluation:\n{evaluation}\n\n"
      f"And the context:\n{context}\n\n"
      "Build a strong case for this idea. Format your response as follows:\n\n"
      "STRENGTHS:\n"
      "• [specific strength 1]\n"
      "• [specific strength 2]\n"
      "• [continue listing key strengths]\n\n"
      "OPPORTUNITIES:\n"
      "• [opportunity 1]\n"
      "• [opportunity 2]\n"
      "• [continue listing potential opportunities]\n\n"
      "ADDRESSING CONCERNS:\n"
      "• [how criticism 1 can be mitigated]\n"
      "• [how criticism 2 can be addressed]\n"
      "• [continue addressing key concerns from the evaluation]"
  )
  
  if not GENAI_AVAILABLE:
    # Return mock advocacy for CI/testing environments
    return "STRENGTHS:\n• Mock strength 1\n• Mock strength 2\n\nOPPORTUNITIES:\n• Mock opportunity 1\n• Mock opportunity 2\n\nADDRESSING CONCERNS:\n• Mock mitigation 1\n• Mock mitigation 2"
  
  if advocate_client is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot advocate ideas")
  
  try:
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=ADVOCATE_SYSTEM_INSTRUCTION
    )
    response = advocate_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API in advocate_idea: {e}", exc_info=True)
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return ADVOCATE_EMPTY_RESPONSE
  return agent_response


