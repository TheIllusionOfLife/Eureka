"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
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
    from madspark.utils.constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.utils.errors import ConfigurationError
    from madspark.agents.genai_client import get_genai_client, get_model_name
except ImportError:
    # Fallback for local development/testing
    from constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from errors import ConfigurationError
    from .genai_client import get_genai_client, get_model_name

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    skeptic_client = get_genai_client()
    model_name = get_model_name()
else:
    skeptic_client = None
    model_name = "mock-model"


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
      LANGUAGE_CONSISTENCY_INSTRUCTION +
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
  
  if not GENAI_AVAILABLE:
    # Return mock criticism for CI/testing environments with language matching demo
    # Simple language detection for mock responses
    combined_text = idea + advocacy + context
    if any(char >= '\u3040' and char <= '\u309F' or char >= '\u30A0' and char <= '\u30FF' or char >= '\u4E00' and char <= '\u9FAF' for char in combined_text):
        return "重大な欠陥:\n• モック欠陥1\n• モック欠陥2\n\nリスクと課題:\n• モックリスク1\n• モックリスク2\n\n疑問のある仮定:\n• モック仮定1\n• モック仮定2\n\n見落とされた考慮事項:\n• モック欠落要因1\n• モック欠落要因2"
    elif any(char in 'àâäæéèêëïîôöùûüÿ' for char in combined_text.lower()):
        return "DÉFAUTS CRITIQUES:\n• Défaut factice 1\n• Défaut factice 2\n\nRISQUES ET DÉFIS:\n• Risque factice 1\n• Risque factice 2\n\nHYPOTHÈSES DOUTEUSES:\n• Hypothèse factice 1\n• Hypothèse factice 2\n\nCONSIDÉRATIONS MANQUANTES:\n• Facteur manquant factice 1\n• Facteur manquant factice 2"
    elif any(char in 'ñáíóúüç' for char in combined_text.lower()):
        return "FALLAS CRÍTICAS:\n• Falla simulada 1\n• Falla simulada 2\n\nRIESGOS Y DESAFÍOS:\n• Riesgo simulado 1\n• Riesgo simulado 2\n\nSUPOSICIONES CUESTIONABLES:\n• Suposición simulada 1\n• Suposición simulada 2\n\nCONSIDERACIONES FALTANTES:\n• Factor faltante simulado 1\n• Factor faltante simulado 2"
    elif any(char in 'äöüß' for char in combined_text.lower()):
        return "KRITISCHE SCHWÄCHEN:\n• Mock-Schwäche 1\n• Mock-Schwäche 2\n\nRISIKEN UND HERAUSFORDERUNGEN:\n• Mock-Risiko 1\n• Mock-Risiko 2\n\nFRAGWÜRDIGE ANNAHMEN:\n• Mock-Annahme 1\n• Mock-Annahme 2\n\nFEHLENDE ÜBERLEGUNGEN:\n• Mock-fehlender Faktor 1\n• Mock-fehlender Faktor 2"
    else:
        return "CRITICAL FLAWS:\n• Mock flaw 1\n• Mock flaw 2\n\nRISKS & CHALLENGES:\n• Mock risk 1\n• Mock risk 2\n\nQUESTIONABLE ASSUMPTIONS:\n• Mock assumption 1\n• Mock assumption 2\n\nMISSING CONSIDERATIONS:\n• Mock missing factor 1\n• Mock missing factor 2"
  
  if skeptic_client is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot criticize ideas")
  
  try:
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=SKEPTIC_SYSTEM_INSTRUCTION
    )
    response = skeptic_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API in criticize_idea: {e}", exc_info=True)
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return SKEPTIC_EMPTY_RESPONSE
  return agent_response


