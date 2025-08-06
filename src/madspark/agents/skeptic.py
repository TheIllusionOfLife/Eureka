"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
"""
import json
import logging
from typing import List, Dict, Any, Tuple

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

try:
    from madspark.utils.constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from madspark.agents.genai_client import get_genai_client, get_model_name
except ImportError:
    # Fallback for local development/testing
    from constants import SKEPTIC_EMPTY_RESPONSE, SKEPTIC_SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
    from .genai_client import get_genai_client, get_model_name

# Configure the Google GenAI client
if GENAI_AVAILABLE:
    skeptic_client = get_genai_client()
    model_name = get_model_name()
else:
    skeptic_client = None
    model_name = "mock-model"


def criticize_idea(idea: str, advocacy: str, topic: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
  """Critically analyzes an idea, playing devil's advocate, using the skeptic model.

  Args:
    idea: The idea to be critically analyzed.
    advocacy: The arguments previously made in favor of the idea.
    topic: The main topic or theme being explored.
    context: Additional constraints or criteria for evaluation.
    temperature: Controls randomness in generation (0.0-1.0). Balanced for criticism.
    use_structured_output: Whether to use structured JSON output (default: True)

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
  
  if not GENAI_AVAILABLE or skeptic_client is None:
    # Return mock criticism for CI/testing environments or when API key is not configured
    if use_structured_output:
        # Return structured mock data
        import json
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
        # Import the schema
        from madspark.agents.response_schemas import SKEPTIC_SCHEMA
        
        # Create the generation config with structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=SKEPTIC_SCHEMA,
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
    temperature: float = 0.5
) -> Tuple[List[Dict[str, Any]], int]:
  """Batch critical analysis for multiple ideas in a single API call.
  
  This function significantly reduces API calls by processing all ideas
  in one request instead of making N separate calls.
  
  Args:
    ideas_with_advocacies: List of dicts with 'idea' and 'advocacy' keys
    topic: The main topic or theme being explored
    context: Additional constraints or criteria for evaluation
    temperature: Generation temperature (0.0-1.0)
    
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


