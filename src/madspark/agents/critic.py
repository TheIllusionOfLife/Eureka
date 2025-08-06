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


def evaluate_ideas(ideas: str, topic: str, context: str, temperature: float = DEFAULT_CRITIC_TEMPERATURE, use_structured_output: bool = True) -> str:
  """Evaluates ideas based on topic and context using the critic model.

  Args:
    ideas: A string containing the ideas to be evaluated, typically newline-separated.
    topic: The main topic/theme for the ideas.
    context: The constraints or additional context for evaluation.
    temperature: Controls randomness in generation (0.0-1.0). Lower values increase consistency.
    use_structured_output: Whether to use structured JSON output (default: True)

  Returns:
    A string from the LLM. If use_structured_output is True, returns JSON string.
    Otherwise, returns newline-separated JSON objects for backward compatibility.
    Returns an empty string if the model provides no content.
  Raises:
    ValueError: If ideas, topic, or context are empty or invalid.
  """
  if not isinstance(ideas, str) or not ideas.strip():
    raise ValueError("Input 'ideas' to evaluate_ideas must be a non-empty string.")
  if not isinstance(topic, str) or not topic.strip():
    raise ValueError("Input 'topic' to evaluate_ideas must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to evaluate_ideas must be a non-empty string.")

  prompt: str = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      "You will be provided with a list of ideas, topic, and context.\n"
      "For each idea, you MUST provide an evaluation in the form of a single-line JSON object string.\n"
      "Each JSON object must have exactly two keys: 'score' (an integer from 1 to 10, where 10 is best) "
      "and 'comment' (a detailed string thoroughly explaining your reasoning, analysis, and suggestions).\n"
      "Ensure your entire response consists ONLY of these JSON object strings, one per line, "
      "corresponding to each idea in the order they were presented.\n"
      "Do not include any other text, explanations, or formatting before or after the JSON strings.\n\n"
      f"Here are the ideas (one per line):\n{ideas}\n\n"
      f"Topic:\n{topic}\n\n"
      f"Context for evaluation:\n{context}\n\n"
      "Provide your JSON evaluations now (one per line, in the same order as the input ideas):"
  )
  
  if not GENAI_AVAILABLE or critic_client is None:
    # Return mock evaluation for CI/testing environments or when API key is not configured
    # Simple language detection for mock responses
    combined_text = ideas + topic + context
    
    if use_structured_output:
        # Return structured mock data
        import json
        ideas_list = [idea.strip() for idea in ideas.split('\n') if idea.strip()]
        mock_evaluations = []
        
        for i, idea in enumerate(ideas_list):
            if any(char >= '\u3040' and char <= '\u309F' or char >= '\u30A0' and char <= '\u30FF' or char >= '\u4E00' and char <= '\u9FAF' for char in combined_text):
                comment = "テスト用のモック評価"
            elif any(char in 'àâäæéèêëïîôöùûüÿ' for char in combined_text.lower()):
                comment = "Évaluation factice pour les tests"
            elif any(char in 'ñáíóúüç' for char in combined_text.lower()):
                comment = "Evaluación simulada para pruebas"
            elif any(char in 'äöüß' for char in combined_text.lower()):
                comment = "Mock-Bewertung für Tests"
            else:
                comment = "Mock evaluation for testing"
                
            mock_evaluations.append({
                "idea_index": i,
                "score": 8,
                "comment": comment,
                "dimensions": {
                    "feasibility": 8.0,
                    "innovation": 7.5,
                    "impact": 8.5
                }
            })
        
        return json.dumps(mock_evaluations)
    else:
        # Legacy text format for backward compatibility
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
    if use_structured_output:
        # Import the schema
        from madspark.agents.response_schemas import CRITIC_SCHEMA
        
        # Create the generation config with structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=CRITIC_SCHEMA,
            system_instruction=CRITIC_SYSTEM_INSTRUCTION
        )
    else:
        # Legacy config without structured output
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
  except (AttributeError, ValueError, RuntimeError) as e:
    # Return empty string on API/connection errors - coordinator will handle this
    logging.error(f"Error calling Gemini API in criticize_ideas: {e}", exc_info=True)
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


