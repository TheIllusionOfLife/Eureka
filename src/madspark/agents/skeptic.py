"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
"""
import json
import logging
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

from madspark.utils.utils import parse_batch_json_with_fallback
from madspark.utils.batch_exceptions import BatchParsingError

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
    from madspark.llm import get_router, should_use_router
    from madspark.llm.exceptions import AllProvidersFailedError
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLM_ROUTER_AVAILABLE = False
    get_router = None  # type: ignore
    should_use_router = None  # type: ignore
    AllProvidersFailedError = Exception  # type: ignore

try:
    from madspark.utils.constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.agents.genai_client import get_genai_client, get_model_name
    from madspark.schemas.skepticism import SkepticismResponse, SkepticismBatchResponse
    from madspark.schemas.adapters import pydantic_to_genai_schema
except ImportError:
    # Fallback for local development/testing
    from constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from .genai_client import get_genai_client, get_model_name
    from ..schemas.skepticism import SkepticismResponse, SkepticismBatchResponse
    from ..schemas.adapters import pydantic_to_genai_schema

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    skeptic_client = get_genai_client()
    model_name = get_model_name()
else:
    skeptic_client = None
    model_name = "mock-model"

# Convert Pydantic model to GenAI schema format at module level (cached)
_SKEPTIC_GENAI_SCHEMA = pydantic_to_genai_schema(SkepticismResponse)


def _should_use_router() -> bool:
    """
    Check if router should be used based on configuration.

    Note: Delegates to shared utility in madspark.llm.utils for DRY compliance.
    """
    if should_use_router is None:
        return False
    return should_use_router(LLM_ROUTER_AVAILABLE, get_router)


def criticize_idea(idea: str, advocacy: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True, use_router: bool = True, router: Optional["LLMRouter"] = None) -> str:
  """Critically analyzes an idea, playing devil's advocate, using the skeptic model.

  When use_router=True and LLM Router is available, routes through the
  multi-provider abstraction layer for automatic fallback and caching.

  Args:
    idea: The idea to be critically analyzed.
    advocacy: The arguments previously made in favor of the idea.
    topic: The main topic or theme being explored.
    context: Additional constraints or criteria for evaluation.
    temperature: Controls randomness in generation (0.0-1.0). Balanced for criticism.
    use_structured_output: Whether to use structured JSON output (default: True).
        Note: When routing through LLM Router, always returns structured JSON regardless
        of this flag, as router enforces Pydantic schema validation for type safety.
    use_router: Whether to use LLM Router for provider abstraction (default: True)
    router: Optional LLMRouter instance for request-scoped routing (Phase 2).
        If provided, uses this router instead of calling get_router().
        Enables thread-safe concurrent operation in backend environments.

  Returns:
    A string containing the critical analysis, counterarguments, and identified risks.
    If use_structured_output is True, returns JSON string. Otherwise, returns formatted text.
    Returns a placeholder string if the model provides no content.
  Raises:
    ValueError: If idea, advocacy, topic, or context are empty or invalid.
  """
  if not isinstance(idea, str) or not idea.strip():
    raise ValueError("Input 'idea' to criticize_idea must be a non-empty string.")
  if not isinstance(advocacy, str) or not advocacy.strip():
    # Advocacy might be a placeholder like "Advocacy not available..." which is fine.
    # This check ensures it's not an empty string from an unexpected source.
    raise ValueError("Input 'advocacy' to criticize_idea must be a non-empty string.")
  if not isinstance(topic, str) or not topic.strip():
    raise ValueError("Input 'topic' to criticize_idea must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to criticize_idea must be a non-empty string.")

  prompt: str = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Topic: {topic}\n"
      f"Context/Constraints: {context}\n\n"
      f"Here's an idea:\n{idea}\n\n"
      f"Here's the case made for it:\n{advocacy}\n\n"
      "Play devil's advocate considering the topic and context. Format your critical analysis as follows:\n\n"
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

  # Try LLM Router first if available and configured
  # Router only used when use_structured_output=True since router inherently returns structured JSON
  should_route = use_router and use_structured_output and LLM_ROUTER_AVAILABLE and (router is not None or get_router is not None)
  if should_route and _should_use_router():
      try:
          # Use provided router or fall back to singleton (backward compatible)
          router_instance = router if router is not None else get_router()
          validated, response = router_instance.generate_structured(
              prompt=prompt,
              schema=SkepticismResponse,
              system_instruction=SKEPTIC_SYSTEM_INSTRUCTION,
              temperature=temperature,
          )

          logger.info(f"Router generated skepticism via {response.provider} ({response.tokens_used} tokens)")
          return json.dumps(validated.model_dump())

      except AllProvidersFailedError as e:
          logger.warning(f"LLM Router failed, falling back to direct API: {e}")
      except Exception as e:
          logger.warning(f"Router error, falling back to direct API: {e}")

  if not GENAI_AVAILABLE or skeptic_client is None:
    # Return mock criticism for CI/testing environments or when API key is not configured
    if use_structured_output:
        # Return structured mock data
        mock_skepticism = {
            "critical_flaws": [
                {"title": "Implementation Complexity", "description": "Mock flaw: Implementation complexity may be underestimated"},
                {"title": "Resource Requirements", "description": "Mock flaw: Resource requirements not fully considered"}
            ],
            "risks_and_challenges": [
                {"title": "Market Adoption", "description": "Mock risk: Market adoption challenges"},
                {"title": "Technical Scalability", "description": "Mock risk: Technical scalability concerns"}
            ],
            "questionable_assumptions": [
                {"assumption": "User behavior prediction", "concern": "Mock assumption: May not match reality"},
                {"assumption": "Technology maturity", "concern": "Mock assumption: May be overestimated"}
            ],
            "missing_considerations": [
                {"aspect": "Regulatory compliance", "importance": "Mock missing: Critical for market entry"},
                {"aspect": "Long-term maintenance", "importance": "Mock missing: Affects total cost of ownership"}
            ]
        }
        return json.dumps(mock_skepticism)
    else:
        # Legacy text format for backward compatibility
        from madspark.utils.mock_language_utils import get_mock_response
        combined_text = idea + advocacy + context
        return get_mock_response('skeptic', combined_text)
  
  if skeptic_client is None:
    from madspark.utils.errors import ConfigurationError
    raise ConfigurationError("Skeptic client is not configured but GENAI is enabled")
  
  
  try:
    if use_structured_output:
        # Create the generation config with pre-computed structured output schema
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=_SKEPTIC_GENAI_SCHEMA,
            system_instruction=SKEPTIC_SYSTEM_INSTRUCTION
        )
    else:
        # Legacy config without structured output
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


def criticize_ideas_batch(
    ideas_with_advocacies: List[Dict[str, str]],
    topic: str,
    context: str,
    temperature: float = 0.5,
    router: Optional[Any] = None
) -> Tuple[List[Dict[str, Any]], int]:
  """Batch critical analysis for multiple ideas in a single API call.

  This function significantly reduces API calls by processing all ideas
  in one request instead of making N separate calls.

  Args:
    ideas_with_advocacies: List of dicts with 'idea' and 'advocacy' keys
    topic: The main topic or theme being explored
    context: Additional constraints or criteria for evaluation
    temperature: Generation temperature (0.0-1.0)
    router: Optional LLMRouter for request-scoped configuration (currently unused,
            batch operations use direct Gemini API for efficiency)
    
  Returns:
    List of skeptic responses with structured format including:
    - idea_index: Index of the idea
    - critical_flaws: List of major problems
    - risks_challenges: List of risks and their impacts
    - questionable_assumptions: List of assumptions that may be wrong
    - missing_considerations: List of overlooked factors
    - formatted: Human-readable formatted string
    
  Raises:
    ValueError: If input format is invalid or JSON parsing fails
    RuntimeError: If API call fails
  """
  if not ideas_with_advocacies:
    return [], 0
  
  # Validate input format
  for i, item in enumerate(ideas_with_advocacies):
    if not isinstance(item, dict):
      raise ValueError(f"Item {i} must be a dictionary")
    if 'idea' not in item or 'advocacy' not in item:
      raise ValueError(f"Item {i} must have 'idea' and 'advocacy' keys")
  
  # Build batch prompt
  items_text = []
  for i, item in enumerate(ideas_with_advocacies):
    items_text.append(
      f"IDEA {i+1}:\n{item['idea']}\n\n"
      f"ADVOCACY:\n{item['advocacy']}"
    )
  
  # Define newline for use in f-string
  newline = '\n'
  prompt = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Topic: {topic}\n"
      f"Context/Constraints: {context}\n\n"
      f"{newline.join(items_text)}\n\n"
      "For EACH idea above, play devil's advocate considering the topic and context and provide criticism in this exact JSON format:\n"
      "{\n"
      '  "idea_index": <0-based index>,\n'
      '  "critical_flaws": ["flaw1", "flaw2", ...],\n'
      '  "risks_challenges": ["risk1 and impact", "risk2 and impact", ...],\n'
      '  "questionable_assumptions": ["assumption1", "assumption2", ...],\n'
      '  "missing_considerations": ["missing1", "missing2", ...]\n'
      "}\n\n"
      "Return ONLY a JSON array containing one object per idea, in order.\n"
      "Each object must contain all five fields. Be thorough and critical."
  )
  
  # Router path: Use LLM router for Ollama-only or multi-provider support
  # Check router FIRST before falling back to mock mode
  if router is not None and _should_use_router():
    try:
      logger.info(f"Using LLM router for batch skepticism of {len(ideas_with_advocacies)} ideas")

      # Use the same prompt we built above, but with batch schema
      validated, response = router.generate_structured(
          prompt=prompt,
          schema=SkepticismBatchResponse,
          system_instruction=SKEPTIC_SYSTEM_INSTRUCTION + " Return a JSON array of critical analyses.",
          temperature=temperature
      )

      # Convert Pydantic batch response to existing dict format
      results = []
      newline = '\n'
      for item in validated.root:
        formatted = (
          f"CRITICAL FLAWS:\n"
          f"{newline.join(f'• {f}' for f in item.critical_flaws)}\n\n"
          f"RISKS & CHALLENGES:\n"
          f"{newline.join(f'• {r}' for r in item.risks_challenges)}\n\n"
          f"QUESTIONABLE ASSUMPTIONS:\n"
          f"{newline.join(f'• {a}' for a in item.questionable_assumptions)}\n\n"
          f"MISSING CONSIDERATIONS:\n"
          f"{newline.join(f'• {m}' for m in item.missing_considerations)}"
        )
        results.append({
          "idea_index": item.idea_index,
          "critical_flaws": item.critical_flaws,
          "risks_challenges": item.risks_challenges,
          "questionable_assumptions": item.questionable_assumptions,
          "missing_considerations": item.missing_considerations,
          "formatted": formatted
        })

      # Sort by idea_index to ensure correct order
      results.sort(key=lambda x: x['idea_index'])

      logger.info(f"Router batch skepticism completed: {len(results)} items, {response.tokens_used} tokens")
      return results, response.tokens_used

    except AllProvidersFailedError as e:
      logger.warning(f"Router failed for batch skepticism, falling back to direct API: {e}")
      # Fall through to direct Gemini API below

  # Mock mode: Return mock skepticism when no API is available
  if not GENAI_AVAILABLE or skeptic_client is None:
    # Return mock skepticism for CI/testing
    mock_results = []
    for i in range(len(ideas_with_advocacies)):
      mock_results.append({
        "idea_index": i,
        "critical_flaws": ["Mock flaw 1", "Mock flaw 2"],
        "risks_challenges": ["Mock risk 1", "Mock risk 2"],
        "questionable_assumptions": ["Mock assumption 1", "Mock assumption 2"],
        "missing_considerations": ["Mock missing factor 1", "Mock missing factor 2"],
        "formatted": "CRITICAL FLAWS:\n• Mock flaw 1\n• Mock flaw 2\n\n"
                    "RISKS & CHALLENGES:\n• Mock risk 1\n• Mock risk 2\n\n"
                    "QUESTIONABLE ASSUMPTIONS:\n• Mock assumption 1\n• Mock assumption 2\n\n"
                    "MISSING CONSIDERATIONS:\n• Mock missing factor 1\n• Mock missing factor 2"
      })
    return mock_results, 0  # Return tuple for consistency

  try:

    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        system_instruction=SKEPTIC_SYSTEM_INSTRUCTION + " Return a JSON array of critical analyses."
    )
    
    response = skeptic_client.models.generate_content(
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
        raise ValueError("API returned None response text")
      criticisms = json.loads(response.text)
    except json.JSONDecodeError as e:
      # Try fallback parsing for problematic JSON (especially with Japanese content)
      try:
        logger.warning(f"JSON decode error, attempting fallback parsing: {e}")
        criticisms = parse_batch_json_with_fallback(response.text, expected_count=len(ideas_with_advocacies))
        logger.info(f"Fallback parsing successful, recovered {len(criticisms)} items")
      except Exception as fallback_error:
        raise BatchParsingError(
          f"Invalid JSON response from API: {e}. Fallback parsing also failed: {fallback_error}",
          batch_type="skeptic",
          items_count=len(ideas_with_advocacies),
          raw_response=response.text,
          parse_error=e
        )
    
    # Validate and format results
    if not isinstance(criticisms, list):
      raise ValueError("Response must be a JSON array")
    
    if len(criticisms) != len(ideas_with_advocacies):
      raise ValueError(f"Expected {len(ideas_with_advocacies)} criticisms, got {len(criticisms)}")
    
    # Process results and add formatted text
    results = []
    newline = '\n'  # Define for use in f-strings
    for criticism in criticisms:
      # Validate structure
      required = {'idea_index', 'critical_flaws', 'risks_challenges', 
                 'questionable_assumptions', 'missing_considerations'}
      if not all(field in criticism for field in required):
        missing = required - set(criticism.keys())
        raise ValueError(f"Missing required fields: {missing}")
      
      # Create formatted text
      formatted = (
        f"CRITICAL FLAWS:\n"
        f"{newline.join(f'• {f}' for f in criticism['critical_flaws'])}\n\n"
        f"RISKS & CHALLENGES:\n"
        f"{newline.join(f'• {r}' for r in criticism['risks_challenges'])}\n\n"
        f"QUESTIONABLE ASSUMPTIONS:\n"
        f"{newline.join(f'• {a}' for a in criticism['questionable_assumptions'])}\n\n"
        f"MISSING CONSIDERATIONS:\n"
        f"{newline.join(f'• {m}' for m in criticism['missing_considerations'])}"
      )
      
      criticism['formatted'] = formatted
      results.append(criticism)
    
    # Sort by idea_index to ensure order
    results.sort(key=lambda x: x['idea_index'])
    
    # Always return tuple for consistent API
    return results, token_usage if isinstance(token_usage, (int, float)) else 0
    
  except Exception as e:
    logging.error(f"Batch skeptic failed: {e}", exc_info=True)
    raise RuntimeError(f"Batch skeptic failed: {e}")


