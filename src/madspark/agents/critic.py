"""Critic Agent.

This module defines the Critic agent and its associated tools.
The agent is responsible for evaluating ideas based on specified criteria
and context, providing scores and textual feedback.
"""
import json
import logging
from typing import Optional, TYPE_CHECKING

# Set up logger
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

# Optional import for Google GenAI - graceful fallback for CI/testing
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

# Optional LLM Router import
try:
    from madspark.llm import get_router, should_use_router
    from madspark.llm.exceptions import AllProvidersFailedError
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLM_ROUTER_AVAILABLE = False
    get_router = None  # type: ignore
    should_use_router = None  # type: ignore
    AllProvidersFailedError = Exception  # type: ignore

try:
    from madspark.agents.genai_client import get_genai_client, get_model_name
    from madspark.utils.constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.schemas.evaluation import CriticEvaluations
    from madspark.schemas.adapters import pydantic_to_genai_schema
except ImportError:
    # Fallback for local development/testing
    from .genai_client import get_genai_client, get_model_name
    from constants import CRITIC_SYSTEM_INSTRUCTION, DEFAULT_CRITIC_TEMPERATURE, LANGUAGE_CONSISTENCY_INSTRUCTION
    from schemas.evaluation import CriticEvaluations
    from schemas.adapters import pydantic_to_genai_schema

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    critic_client = get_genai_client()
    model_name = get_model_name()
else:
    critic_client = None
    model_name = "mock-model"

# Convert Pydantic model to GenAI schema format at module level (cached)
_CRITIC_GENAI_SCHEMA = pydantic_to_genai_schema(CriticEvaluations)


def _should_use_router() -> bool:
    """
    Check if router should be used based on configuration.

    Returns True if:
    - LLM Router is available
    - User explicitly configured provider via env var (e.g., --provider flag)
    - Any router-related flag is set

    Note: Delegates to shared utility in madspark.llm.utils for DRY compliance.
    """
    if should_use_router is None:
        return False
    return should_use_router(LLM_ROUTER_AVAILABLE, get_router)


def evaluate_ideas(ideas: str, topic: str, context: str, temperature: float = DEFAULT_CRITIC_TEMPERATURE, use_structured_output: bool = True, use_router: bool = True, router: Optional["LLMRouter"] = None) -> str:
  """Evaluates ideas based on topic and context using the critic model.

  When use_router=True and LLM Router is available, routes through the
  multi-provider abstraction layer for automatic fallback and caching.

  Args:
    ideas: A string containing the ideas to be evaluated, typically newline-separated.
    topic: The main topic/theme for the ideas.
    context: The constraints or additional context for evaluation.
    temperature: Controls randomness in generation (0.0-1.0). Lower values increase consistency.
    use_structured_output: Whether to use structured JSON output (default: True).
        Note: When routing through LLM Router, always returns structured JSON regardless
        of this flag, as router enforces Pydantic schema validation for type safety.
    use_router: Whether to use LLM Router for provider abstraction (default: True)
    router: Optional LLMRouter instance for request-scoped routing (Phase 2).
        If provided, uses this router instead of calling get_router().
        Enables thread-safe concurrent operation in backend environments.

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

  # Count ideas to tell the model exactly how many evaluations to produce
  # Ideas are formatted as "Idea 1: ...\nIdea 2: ..." by the orchestrator
  ideas_lines = [line.strip() for line in ideas.split('\n') if line.strip()]
  num_ideas = len(ideas_lines)

  # Legacy prompt for NDJSON format (direct API without structured output)
  legacy_prompt: str = (
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

  # Structured output prompt for JSON array format (router with Pydantic schema)
  structured_prompt: str = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"You will be provided with {num_ideas} ideas, a topic, and context.\n"
      f"You MUST evaluate ALL {num_ideas} ideas and return a JSON array with EXACTLY {num_ideas} evaluation objects.\n"
      "Each evaluation object must have:\n"
      "  - 'score': an integer from 1 to 10 (10 = excellent, 1 = poor)\n"
      "  - 'comment': a detailed critique explaining your reasoning and suggestions\n\n"
      f"Here are the {num_ideas} ideas to evaluate:\n{ideas}\n\n"
      f"Topic:\n{topic}\n\n"
      f"Context for evaluation:\n{context}\n\n"
      f"IMPORTANT: You MUST return an array with EXACTLY {num_ideas} evaluations, one for each idea in order."
  )

  # Try LLM Router first if available and configured
  # Router only used when use_structured_output=True since router inherently returns structured JSON
  should_route = use_router and use_structured_output and LLM_ROUTER_AVAILABLE and (router is not None or get_router is not None)
  if should_route and _should_use_router():
      try:
          # Use provided router or fall back to singleton (backward compatible)
          router_instance = router if router is not None else get_router()
          # Router generates structured output with automatic provider selection
          # Use structured_prompt that explicitly asks for a JSON array
          validated, response = router_instance.generate_structured(
              prompt=structured_prompt,
              schema=CriticEvaluations,
              system_instruction=CRITIC_SYSTEM_INSTRUCTION,
              temperature=temperature,
          )

          # Successfully got structured response via router
          logger.info(f"Router generated evaluation via {response.provider} ({response.tokens_used} tokens)")

          # Log detailed evaluation results for debugging
          num_returned = len(validated.root)
          logger.debug(f"Expected {num_ideas} evaluations, received {num_returned}")
          for i, eval_item in enumerate(validated.root):
              logger.debug(f"Eval {i+1}: score={eval_item.score}, comment_len={len(eval_item.comment)}")

          if num_returned != num_ideas:
              logger.warning(f"Evaluation count mismatch! Expected {num_ideas}, got {num_returned}")

          # Convert validated Pydantic model to JSON string for backward compatibility
          # CriticEvaluations is a RootModel containing list[CriticEvaluation]
          return json.dumps([eval_item.model_dump() for eval_item in validated.root])

      except AllProvidersFailedError as e:
          logger.warning(f"LLM Router failed, falling back to direct API: {e}")
          # Fall through to direct API call
      except Exception as e:
          logger.warning(f"Router error, falling back to direct API: {e}")
          # Fall through to direct API call

  if not GENAI_AVAILABLE or critic_client is None:
    # Return mock evaluation for CI/testing environments or when API key is not configured
    # Simple language detection for mock responses
    combined_text = ideas + topic + context
    
    if use_structured_output:
        # Return structured mock data
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
        # Create the generation config with pre-computed structured output schema
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=_CRITIC_GENAI_SCHEMA,
            system_instruction=CRITIC_SYSTEM_INSTRUCTION
        )
        # Use structured_prompt for JSON array format
        api_prompt = structured_prompt
    else:
        # Legacy config without structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=CRITIC_SYSTEM_INSTRUCTION
        )
        # Use legacy_prompt for NDJSON format
        api_prompt = legacy_prompt

    response = critic_client.models.generate_content(
        model=model_name,
        contents=api_prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except (AttributeError, ValueError, RuntimeError) as e:
    # Return empty string on API/connection errors - coordinator will handle this
    logger.error(f"Error calling Gemini API in criticize_ideas: {e}", exc_info=True)
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing of json_evaluation_lines will correctly result
  # in an empty list, leading to default "Evaluation not available" critiques.
  return agent_response


