"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
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
    from madspark.utils.constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.agents.genai_client import get_genai_client, get_model_name
except ImportError:
    # Fallback for local development/testing
    from constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
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
  
  if not GENAI_AVAILABLE or advocate_client is None:
    # Return mock advocacy for CI/testing environments with language matching demo
    # Simple language detection for mock responses
    combined_text = idea + evaluation + context
    if any(char >= '\u3040' and char <= '\u309F' or char >= '\u30A0' and char <= '\u30FF' or char >= '\u4E00' and char <= '\u9FAF' for char in combined_text):
        return "強み:\n• モック強み1\n• モック強み2\n\n機会:\n• モック機会1\n• モック機会2\n\n懸念への対処:\n• モック軽減策1\n• モック軽減策2"
    elif any(char in 'àâäæéèêëïîôöùûüÿ' for char in combined_text.lower()):
        return "FORCES:\n• Force factice 1\n• Force factice 2\n\nOPPORTUNITÉS:\n• Opportunité factice 1\n• Opportunité factice 2\n\nRÉPONSE AUX PRÉOCCUPATIONS:\n• Atténuation factice 1\n• Atténuation factice 2"
    elif any(char in 'ñáíóúç' for char in combined_text.lower()):
        return "FORTALEZAS:\n• Fortaleza simulada 1\n• Fortaleza simulada 2\n\nOPORTUNIDADES:\n• Oportunidad simulada 1\n• Oportunidad simulada 2\n\nABORDANDO PREOCUPACIONES:\n• Mitigación simulada 1\n• Mitigación simulada 2"
    elif any(char in 'äöüß' for char in combined_text.lower()):
        return "STÄRKEN:\n• Mock-Stärke 1\n• Mock-Stärke 2\n\nCHANCEN:\n• Mock-Chance 1\n• Mock-Chance 2\n\nBEDENKEN ANSPRECHEN:\n• Mock-Milderung 1\n• Mock-Milderung 2"
    else:
        return "STRENGTHS:\n• Mock strength 1\n• Mock strength 2\n\nOPPORTUNITIES:\n• Mock opportunity 1\n• Mock opportunity 2\n\nADDRESSING CONCERNS:\n• Mock mitigation 1\n• Mock mitigation 2"
  
  if advocate_client is None:
    from madspark.utils.errors import ConfigurationError
    raise ConfigurationError("Advocate client is not configured but GENAI is enabled")
  
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


