"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
"""
import json
import logging
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

from madspark.utils.utils import parse_batch_json_with_fallback
from madspark.utils.compat_imports import import_genai_and_constants

# Set up logger
logger = logging.getLogger(__name__)

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
    from madspark.llm import get_router, should_use_router, batch_generate_with_router
    from madspark.llm.exceptions import AllProvidersFailedError
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLM_ROUTER_AVAILABLE = False
    get_router = None  # type: ignore
    should_use_router = None  # type: ignore
    batch_generate_with_router = None  # type: ignore
    AllProvidersFailedError = Exception  # type: ignore

# Import constants directly (not in compat_imports yet)
try:
    from madspark.utils.constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.schemas.advocacy import AdvocacyResponse, AdvocacyBatchResponse
    from madspark.schemas.adapters import pydantic_to_genai_schema
except ImportError:
    from ..utils.constants import ADVOCATE_EMPTY_RESPONSE, ADVOCATE_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from ..schemas.advocacy import AdvocacyResponse, AdvocacyBatchResponse
    from ..schemas.adapters import pydantic_to_genai_schema

# Import genai_client using compat helper
_genai_imports = import_genai_and_constants()
get_genai_client = _genai_imports['get_genai_client']

# get_model_name not in compat_imports, import separately
try:
    from madspark.agents.genai_client import get_model_name
except ImportError:
    from .genai_client import get_model_name

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    advocate_client = get_genai_client()
    model_name = get_model_name()
else:
    advocate_client = None
    model_name = "mock-model"

# Convert Pydantic model to GenAI schema format at module level (cached)
_ADVOCATE_GENAI_SCHEMA = pydantic_to_genai_schema(AdvocacyResponse)


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


def advocate_idea(idea: str, evaluation: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True, use_router: bool = True, router: Optional["LLMRouter"] = None) -> str:
  """Advocates for an idea using its evaluation, topic, and context via the advocate model.

  When use_router=True and LLM Router is available, routes through the
  multi-provider abstraction layer for automatic fallback and caching.

  Args:
    idea: The idea to advocate for.
    evaluation: The evaluation received for the idea (e.g., from a critic).
    topic: The main topic or theme being explored.
    context: Additional constraints or criteria for evaluation.
    temperature: Controls randomness in generation (0.0-2.0). Balanced for argumentation.
    use_structured_output: Whether to use structured JSON output (default: True).
        Note: When routing through LLM Router, always returns structured JSON regardless
        of this flag, as router enforces Pydantic schema validation for type safety.
    use_router: Whether to use LLM Router for provider abstraction (default: True)
    router: Optional LLMRouter instance for request-scoped routing (Phase 2).
        If provided, uses this router instead of calling get_router().
        Enables thread-safe concurrent operation in backend environments.

  Returns:
    A string containing the persuasive arguments for the idea. If use_structured_output is True,
    returns JSON string. Otherwise, returns formatted text for backward compatibility.
    Returns a placeholder string if the model provides no content.
  Raises:
    ValueError: If idea, evaluation, topic, or context are empty or invalid.
  """
  if not isinstance(idea, str) or not idea.strip():
    raise ValueError("Input 'idea' to advocate_idea must be a non-empty string.")
  if not isinstance(evaluation, str) or not evaluation.strip():
    raise ValueError("Input 'evaluation' to advocate_idea must be a non-empty string.")
  if not isinstance(topic, str) or not topic.strip():
    raise ValueError("Input 'topic' to advocate_idea must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to advocate_idea must be a non-empty string.")

  prompt: str = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Topic: {topic}\n"
      f"Context/Constraints: {context}\n\n"
      f"Here's an idea:\n{idea}\n\n"
      f"Here's its evaluation:\n{evaluation}\n\n"
      "Build a strong case for this idea considering the topic and context. Format your response as follows:\n\n"
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

  # Try LLM Router first if available and configured
  # Router only used when use_structured_output=True since router inherently returns structured JSON
  should_route = use_router and use_structured_output and LLM_ROUTER_AVAILABLE and (router is not None or get_router is not None)
  if should_route and _should_use_router():
      try:
          # Use provided router or fall back to singleton (backward compatible)
          router_instance = router if router is not None else get_router()
          # Router generates structured output with automatic provider selection
          validated, response = router_instance.generate_structured(
              prompt=prompt,
              schema=AdvocacyResponse,
              system_instruction=ADVOCATE_SYSTEM_INSTRUCTION,
              temperature=temperature,
          )

          # Successfully got structured response via router
          logger.info(f"Router generated advocacy via {response.provider} ({response.tokens_used} tokens)")

          # Convert validated Pydantic model to JSON string for backward compatibility
          return json.dumps(validated.model_dump())

      except AllProvidersFailedError as e:
          logger.warning(f"LLM Router failed, falling back to direct API: {e}")
          # Fall through to direct API call
      except Exception as e:
          logger.warning(f"Router error, falling back to direct API: {e}")
          # Fall through to direct API call

  if not GENAI_AVAILABLE or advocate_client is None:
    # Return mock advocacy for CI/testing environments or when API key is not configured
    if use_structured_output:
        # Return structured mock data
        mock_advocacy = {
            "strengths": [
                {"title": "Strong Foundation", "description": "Mock strength: Strong foundational concept"},
                {"title": "Clear Applications", "description": "Mock strength: Clear practical applications"}
            ],
            "opportunities": [
                {"title": "Market Potential", "description": "Mock opportunity: Market potential"},
                {"title": "Scalability", "description": "Mock opportunity: Scalability options"}
            ],
            "addressing_concerns": [
                {"concern": "Feasibility", "response": "Mock mitigation: Address feasibility through phased approach"},
                {"concern": "Cost", "response": "Mock mitigation: Cost optimization strategies"}
            ]
        }
        return json.dumps(mock_advocacy)
    else:
        # Legacy text format for backward compatibility
        from madspark.utils.mock_language_utils import get_mock_response
        combined_text = idea + evaluation + context
        return get_mock_response('advocate', combined_text)
  
  if advocate_client is None:
    from madspark.utils.errors import ConfigurationError
    raise ConfigurationError("Advocate client is not configured but GENAI is enabled")
  
  try:
    if use_structured_output:
        # Create the generation config with pre-computed structured output schema
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=_ADVOCATE_GENAI_SCHEMA,
            system_instruction=ADVOCATE_SYSTEM_INSTRUCTION
        )
    else:
        # Legacy config without structured output
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
    logger.error(f"Error calling Gemini API in advocate_idea: {e}", exc_info=True)
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return ADVOCATE_EMPTY_RESPONSE
  return agent_response


def advocate_ideas_batch(
    ideas_with_evaluations: List[Dict[str, str]],
    topic: str,
    context: str,
    temperature: float = 0.5,
    router: Optional[Any] = None
) -> Tuple[List[Dict[str, Any]], int]:
  """Batch advocate for multiple ideas in a single API call.

  This function significantly reduces API calls by processing all ideas
  in one request instead of making N separate calls.

  Args:
    ideas_with_evaluations: List of dicts with 'idea' and 'evaluation' keys
    topic: The main topic or theme being explored
    context: Additional constraints or criteria for evaluation
    temperature: Generation temperature (0.0-1.0)
    router: Optional LLMRouter for request-scoped configuration (currently unused,
            batch operations use direct Gemini API for efficiency)
    
  Returns:
    List of advocacy responses with structured format including:
    - idea_index: Index of the idea
    - strengths: List of key strengths
    - opportunities: List of opportunities
    - addressing_concerns: List of ways to address concerns
    - formatted: Human-readable formatted string
    
  Raises:
    ValueError: If input format is invalid or JSON parsing fails
    RuntimeError: If API call fails
  """
  if not ideas_with_evaluations:
    return [], 0
  
  # Validate input format
  for i, item in enumerate(ideas_with_evaluations):
    if not isinstance(item, dict):
      raise ValueError(f"Item {i} must be a dictionary")
    if 'idea' not in item or 'evaluation' not in item:
      raise ValueError(f"Item {i} must have 'idea' and 'evaluation' keys")
  
  # Build batch prompt
  items_text = []
  for i, item in enumerate(ideas_with_evaluations):
    items_text.append(
      f"IDEA {i+1}:\n{item['idea']}\n\n"
      f"EVALUATION:\n{item['evaluation']}"
    )
  
  # Define newline for use in f-string
  newline = '\n'
  prompt = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Topic: {topic}\n"
      f"Context/Constraints: {context}\n\n"
      f"{newline.join(items_text)}\n\n"
      "For EACH idea above, provide advocacy considering the topic and context in this exact JSON format:\n"
      "{\n"
      '  "idea_index": <0-based index>,\n'
      '  "strengths": ["strength1", "strength2", ...],\n'
      '  "opportunities": ["opportunity1", "opportunity2", ...],\n'
      '  "addressing_concerns": ["mitigation1", "mitigation2", ...]\n'
      "}\n\n"
      f"CRITICAL: You MUST return EXACTLY {len(ideas_with_evaluations)} objects in a JSON array.\n"
      f"There are {len(ideas_with_evaluations)} ideas above, so return {len(ideas_with_evaluations)} advocacy objects.\n"
      "Return ONLY a JSON array containing one object per idea, in order.\n"
      "Each object must contain all four fields.\n"
      "DO NOT skip any idea - provide advocacy for ALL ideas listed above."
  )
  
  # Router path: Use LLM router for Ollama-only or multi-provider support
  # Check router FIRST before falling back to mock mode
  if router is not None and _should_use_router() and batch_generate_with_router is not None:
    validated, tokens_used = batch_generate_with_router(
        router=router,
        prompt=prompt,
        schema=AdvocacyBatchResponse,
        system_instruction=ADVOCATE_SYSTEM_INSTRUCTION + " Return a JSON array of advocacy responses.",
        temperature=temperature,
        batch_type="advocacy",
        item_count=len(ideas_with_evaluations),
    )

    if validated is not None:
      # Convert Pydantic batch response to existing dict format
      results = []
      newline = '\n'
      for item in validated.root:
        formatted = (
          f"STRENGTHS:\n"
          f"{newline.join(f'• {s}' for s in item.strengths)}\n\n"
          f"OPPORTUNITIES:\n"
          f"{newline.join(f'• {o}' for o in item.opportunities)}\n\n"
          f"ADDRESSING CONCERNS:\n"
          f"{newline.join(f'• {c}' for c in item.addressing_concerns)}"
        )
        results.append({
          "idea_index": item.idea_index,
          "strengths": item.strengths,
          "opportunities": item.opportunities,
          "addressing_concerns": item.addressing_concerns,
          "formatted": formatted
        })

      # Sort by idea_index to ensure correct order
      results.sort(key=lambda x: x['idea_index'])
      return results, tokens_used

    # validated is None means router failed, fall through to direct API

  # Mock mode: Return mock advocacy when no API is available
  if not GENAI_AVAILABLE or advocate_client is None:
    # Return mock advocacy for CI/testing
    mock_results = []
    for i in range(len(ideas_with_evaluations)):
      mock_results.append({
        "idea_index": i,
        "strengths": ["Mock strength 1", "Mock strength 2"],
        "opportunities": ["Mock opportunity 1", "Mock opportunity 2"],
        "addressing_concerns": ["Mock mitigation 1", "Mock mitigation 2"],
        "formatted": "STRENGTHS:\n• Mock strength 1\n• Mock strength 2\n\n"
                    "OPPORTUNITIES:\n• Mock opportunity 1\n• Mock opportunity 2\n\n"
                    "ADDRESSING CONCERNS:\n• Mock mitigation 1\n• Mock mitigation 2"
      })
    return mock_results, 0  # Return tuple for consistency

  try:

    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        system_instruction=ADVOCATE_SYSTEM_INSTRUCTION + " Return a JSON array of advocacy responses."
    )
    
    response = advocate_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    
    # Extract token usage if available
    token_usage = None
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        token_usage = response.usage_metadata.total_token_count
    
    # Parse JSON response
    try:
      if response.text is None:
        from madspark.utils.batch_exceptions import BatchParsingError
        raise BatchParsingError(
          "API returned None response text",
          batch_type="advocate",
          items_count=len(ideas_with_evaluations),
          raw_response=None
        )
      advocacies = json.loads(response.text)
    except json.JSONDecodeError as e:
      # Try fallback parsing for problematic JSON (especially with Japanese content)
      try:
        logger.warning(f"JSON decode error, attempting fallback parsing: {e}")
        advocacies = parse_batch_json_with_fallback(response.text, expected_count=len(ideas_with_evaluations))
        logger.info(f"Fallback parsing successful, recovered {len(advocacies)} items")
      except Exception as fallback_error:
        from madspark.utils.batch_exceptions import BatchParsingError
        raise BatchParsingError(
          f"Invalid JSON response from API: {e}. Fallback parsing also failed: {fallback_error}",
          batch_type="advocate",
          items_count=len(ideas_with_evaluations),
          raw_response=response.text,
          parse_error=e
        )
    
    # Validate and format results
    if not isinstance(advocacies, list):
      from madspark.utils.batch_exceptions import BatchValidationError
      raise BatchValidationError(
        "Response must be a JSON array",
        batch_type="advocate",
        items_count=len(ideas_with_evaluations),
        actual_count=1 if advocacies else 0
      )
    
    if len(advocacies) != len(ideas_with_evaluations):
      # If we got fewer results, try to fill in missing ones
      logger.warning(
        f"Expected {len(ideas_with_evaluations)} advocacies, got {len(advocacies)}. "
        "Attempting to recover missing items."
      )
      
      # Check which indices are missing
      received_indices = {adv.get('idea_index', -1) for adv in advocacies}
      expected_indices = set(range(len(ideas_with_evaluations)))
      missing_indices = expected_indices - received_indices
      
      if missing_indices:
        logger.warning(f"Missing advocacy for indices: {sorted(missing_indices)}")
        
        # Add placeholder advocacy for missing items
        for idx in missing_indices:
          placeholder = {
            "idea_index": idx,
            "strengths": [
              "This idea addresses the stated context effectively",
              "Shows potential for practical implementation"
            ],
            "opportunities": [
              "Could lead to innovative solutions in this domain",
              "May inspire further development and refinement"
            ],
            "addressing_concerns": [
              "Implementation challenges can be addressed through phased approach",
              "Resource requirements can be optimized through careful planning"
            ]
          }
          advocacies.append(placeholder)
        
        # Re-sort to ensure correct order
        advocacies.sort(key=lambda x: x.get('idea_index', 0))
        logger.info(f"Successfully recovered {len(missing_indices)} missing advocacies with placeholders")
    
    # Process results and add formatted text
    results = []
    newline = '\n'  # Define for use in f-strings
    for advocacy in advocacies:
      # Validate structure
      required = {'idea_index', 'strengths', 'opportunities', 'addressing_concerns'}
      if not all(field in advocacy for field in required):
        missing = required - set(advocacy.keys())
        from madspark.utils.batch_exceptions import BatchValidationError
        raise BatchValidationError(
          f"Missing required fields in response: {missing}",
          batch_type="advocate",
          items_count=len(ideas_with_evaluations)
        )
      
      # Create formatted text
      formatted = (
        f"STRENGTHS:\n"
        f"{newline.join(f'• {s}' for s in advocacy['strengths'])}\n\n"
        f"OPPORTUNITIES:\n"
        f"{newline.join(f'• {o}' for o in advocacy['opportunities'])}\n\n"
        f"ADDRESSING CONCERNS:\n"
        f"{newline.join(f'• {c}' for c in advocacy['addressing_concerns'])}"
      )
      
      advocacy['formatted'] = formatted
      results.append(advocacy)
    
    # Sort by idea_index to ensure order
    results.sort(key=lambda x: x['idea_index'])
    
    # Always return tuple for consistent API
    return results, token_usage if isinstance(token_usage, (int, float)) else 0
    
  except ValueError as e:
    from madspark.utils.batch_exceptions import BatchValidationError
    logger.error(f"Batch advocate validation failed: {e}", exc_info=True)
    raise BatchValidationError(
        str(e),
        batch_type="advocate", 
        items_count=len(ideas_with_evaluations)
    )
  except Exception as e:
    from madspark.utils.batch_exceptions import BatchAPIError
    logger.error(f"Batch advocate API call failed: {e}", exc_info=True)
    raise BatchAPIError(
        f"Batch advocate failed: {e}",
        batch_type="advocate",
        items_count=len(ideas_with_evaluations)
    )

