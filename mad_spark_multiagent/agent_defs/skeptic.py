"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
"""
import os
from typing import Any
import google.generativeai as genai

try:
    from mad_spark_multiagent.constants import SKEPTIC_EMPTY_RESPONSE
except ImportError:
    # Fallback for local development/testing
    from constants import SKEPTIC_EMPTY_RESPONSE

# Configure the Google GenerativeAI client
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

if api_key:
    genai.configure(api_key=api_key)
    # Create the model instance
    skeptic_model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=(
            "You are a devil's advocate. Given an idea, the arguments for it, and"
            " context, critically analyze the idea. Identify potential flaws,"
            " risks, and unintended consequences. Challenge assumptions and present"
            " counterarguments."
        )
    )
else:
    skeptic_model = None


def criticize_idea(idea: str, advocacy: str, context: str) -> str:
  """Critically analyzes an idea, playing devil's advocate, using the skeptic model.

  Args:
    idea: The idea to be critically analyzed.
    advocacy: The arguments previously made in favor of the idea.
    context: Additional context relevant for the critical analysis.

  Returns:
    A string containing the critical analysis, counterarguments, and identified risks.
    Returns a placeholder string if the model provides no content.
  Raises:
    ValueError: If idea, advocacy, or context are empty or invalid.
  """
  if not isinstance(idea, str) or not idea.strip():
    raise ValueError("Input 'idea' to criticize_idea must be a non-empty string.")
  if not isinstance(advocacy, str) or not advocacy.strip():
    # Advocacy might be a placeholder like "Advocacy not available..." which is fine.
    # This check ensures it's not an empty string from an unexpected source.
    raise ValueError("Input 'advocacy' to criticize_idea must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to criticize_idea must be a non-empty string.")

  prompt: str = (
      f"Here's an idea:\n{idea}\n\n"
      f"Here's the case made for it:\n{advocacy}\n\n"
      f"And the context:\n{context}\n\n"
      "Play devil's advocate. Critically analyze the idea, identify "
      "potential flaws, risks, and unintended consequences. Challenge "
      "assumptions and present counterarguments."
  )
  
  if skeptic_model is None:
    raise RuntimeError("GOOGLE_API_KEY not configured - cannot criticize ideas")
  
  try:
    response = skeptic_model.generate_content(prompt)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Return empty string on any API error - coordinator will handle this
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return SKEPTIC_EMPTY_RESPONSE
  return agent_response


