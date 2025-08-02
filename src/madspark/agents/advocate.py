"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
"""
import json
import logging
from typing import List, Dict, Any, Tuple

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


def advocate_idea(idea: str, evaluation: str, context: str, temperature: float = 0.5, use_structured_output: bool = True) -> str:
  """Advocates for an idea using its evaluation and context via the advocate model.

  Args:
    idea: The idea to advocate for.
    evaluation: The evaluation received for the idea (e.g., from a critic).
    context: Additional context relevant for building the advocacy.
    temperature: Controls randomness in generation (0.0-1.0). Balanced for argumentation.
    use_structured_output: Whether to use structured JSON output (default: True)

  Returns:
    A string containing the persuasive arguments for the idea. If use_structured_output is True,
    returns JSON string. Otherwise, returns formatted text for backward compatibility.
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
    # Return mock advocacy for CI/testing environments or when API key is not configured
    if use_structured_output:
        # Return structured mock data
        import json
        mock_advocacy = {
            "strengths": ["Mock strength: Strong foundational concept", "Mock strength: Clear practical applications"],
            "opportunities": ["Mock opportunity: Market potential", "Mock opportunity: Scalability options"],
            "addressing_concerns": ["Mock mitigation: Address feasibility through phased approach", "Mock mitigation: Cost optimization strategies"]
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
        # Import the schema
        from madspark.agents.response_schemas import ADVOCATE_SCHEMA
        
        # Create the generation config with structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=ADVOCATE_SCHEMA,
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
    logging.error(f"Error calling Gemini API in advocate_idea: {e}", exc_info=True)
    agent_response = ""

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return ADVOCATE_EMPTY_RESPONSE
  return agent_response


def advocate_ideas_batch(
    ideas_with_evaluations: List[Dict[str, str]], 
    context: str, 
    temperature: float = 0.5
) -> Tuple[List[Dict[str, Any]], int]:
  """Batch advocate for multiple ideas in a single API call.
  
  This function significantly reduces API calls by processing all ideas
  in one request instead of making N separate calls.
  
  Args:
    ideas_with_evaluations: List of dicts with 'idea' and 'evaluation' keys
    context: Theme/context for all ideas
    temperature: Generation temperature (0.0-1.0)
    
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
      f"Context: {context}\n\n"
      f"{newline.join(items_text)}\n\n"
      "For EACH idea above, provide advocacy in this exact JSON format:\n"
      "{\n"
      '  "idea_index": <0-based index>,\n'
      '  "strengths": ["strength1", "strength2", ...],\n'
      '  "opportunities": ["opportunity1", "opportunity2", ...],\n'
      '  "addressing_concerns": ["mitigation1", "mitigation2", ...]\n'
      "}\n\n"
      "Return ONLY a JSON array containing one object per idea, in order.\n"
      "Each object must contain all four fields."
  )
  
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
      from madspark.utils.batch_exceptions import BatchParsingError
      raise BatchParsingError(
        f"Invalid JSON response from API: {e}",
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
      from madspark.utils.batch_exceptions import BatchValidationError
      raise BatchValidationError(
        f"Expected {len(ideas_with_evaluations)} advocacies, got {len(advocacies)}",
        batch_type="advocate",
        items_count=len(ideas_with_evaluations),
        expected_count=len(ideas_with_evaluations),
        actual_count=len(advocacies)
      )
    
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
    logging.error(f"Batch advocate validation failed: {e}", exc_info=True)
    raise BatchValidationError(
        str(e),
        batch_type="advocate", 
        items_count=len(ideas_with_evaluations)
    )
  except Exception as e:
    from madspark.utils.batch_exceptions import BatchAPIError
    logging.error(f"Batch advocate API call failed: {e}", exc_info=True)
    raise BatchAPIError(
        f"Batch advocate failed: {e}",
        batch_type="advocate",
        items_count=len(ideas_with_evaluations)
    )


