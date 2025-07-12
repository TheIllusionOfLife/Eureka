"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
"""
import os
import logging
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
            " context, critically analyze the idea. List specific concerns, risks,"
            " and flaws as bullet points. Be direct and critical. Focus on concrete"
            " problems and potential failures."
        )
    )
else:
    skeptic_model = None


def criticize_idea(idea: str, advocacy: str, context: str, temperature: float = 0.5) -> str:
  """Critically analyzes an idea, playing devil's advocate, using the skeptic model.

  Args:
    idea: The idea to be critically analyzed.
    advocacy: The arguments previously made in favor of the idea.
    context: Additional context relevant for the critical analysis.
    temperature: Controls randomness in generation (0.0-1.0). Balanced for criticism.

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
      "Play devil's advocate. Format your critical analysis as follows:\n\n"
      "CRITICAL FLAWS:\n"
      "• [specific flaw 1]\n"
      "• [specific flaw 2]\n"
      "• [continue listing major problems]\n\n"
      "RISKS & CHALLENGES:\n"
      "• [risk 1 and its impact]\n"
      "• [risk 2 and its impact]\n"
      "• [continue listing risks]\n\n"
      "QUESTIONABLE ASSUMPTIONS:\n"
      "• [assumption 1 that may be wrong]\n"
      "• [assumption 2 that needs validation]\n"
      "• [continue challenging assumptions]\n\n"
      "MISSING CONSIDERATIONS:\n"
      "• [important factor not addressed]\n"
      "• [overlooked consequence]\n"
      "• [continue listing gaps]"
  )
  
  if skeptic_model is None:
    raise RuntimeError("GOOGLE_API_KEY not configured - cannot criticize ideas")
  
  try:
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = skeptic_model.generate_content(prompt, generation_config=generation_config)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API in criticize_idea: {e}", exc_info=True)
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return SKEPTIC_EMPTY_RESPONSE
  return agent_response


