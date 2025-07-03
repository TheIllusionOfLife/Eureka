"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
"""
import os
from typing import Any
import google.generativeai as genai

try:
    from mad_spark_multiagent.constants import ADVOCATE_EMPTY_RESPONSE
except ImportError:
    # Fallback for local development/testing
    from constants import ADVOCATE_EMPTY_RESPONSE

# Configure the Google GenerativeAI client
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

if api_key:
    genai.configure(api_key=api_key)
    # Create the model instance
    advocate_model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=(
            "You are a persuasive advocate. Given an idea, its evaluation, and"
            " context, build a strong case for the idea, highlighting its"
            " strengths and potential benefits."
        )
    )
else:
    advocate_model = None


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
      f"Here's an idea:\n{idea}\n\n"
      f"Here's its evaluation:\n{evaluation}\n\n"
      f"And the context:\n{context}\n\n"
      "Based on this, build a strong case for the idea, focusing on its "
      "strengths and potential benefits. Address any criticisms from the "
      "evaluation constructively."
  )
  
  if advocate_model is None:
    raise RuntimeError("GOOGLE_API_KEY not configured - cannot advocate ideas")
  
  try:
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = advocate_model.generate_content(prompt, generation_config=generation_config)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Return empty string on any API error - coordinator will handle this
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return ADVOCATE_EMPTY_RESPONSE
  return agent_response


