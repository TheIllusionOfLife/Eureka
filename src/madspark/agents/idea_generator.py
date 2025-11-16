"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional, Union

from madspark.utils.utils import parse_batch_json_with_fallback
from madspark.utils.batch_exceptions import BatchParsingError
from madspark.utils.content_safety import GeminiSafetyHandler
from madspark.utils.multimodal_input import build_prompt_with_multimodal
from madspark.schemas.generation import GeneratedIdeas, ImprovementResponse
from madspark.schemas.adapters import pydantic_to_genai_schema

# Set up logger
logger = logging.getLogger(__name__)

# Optional import for Google GenAI - graceful fallback for CI/testing
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    # Mock classes for CI environments
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
    from madspark.utils.errors import ValidationError
except ImportError:
    # Fallback for local development/testing
    from errors import ValidationError

# Import prompt constants from constants module
try:
    from madspark.utils.constants import IDEA_GENERATION_INSTRUCTION, IDEA_GENERATOR_SYSTEM_INSTRUCTION as SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
except ImportError:
    # Fallback for local development/testing
    from constants import IDEA_GENERATION_INSTRUCTION, IDEA_GENERATOR_SYSTEM_INSTRUCTION as SYSTEM_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION

# Safety settings for constructive feedback generation
# Use centralized safety handler to avoid duplication
_safety_handler = GeminiSafetyHandler()
_IMPROVER_SAFETY_SETTINGS = _safety_handler.get_safety_settings()


def _validate_non_empty_string(value: Any, param_name: str) -> None:
  """Validates that a value is a non-empty string.

  Args:
    value: The value to validate.
    param_name: The parameter name for error messages.

  Raises:
    ValidationError: If the value is not a non-empty string.
  """
  if not isinstance(value, str) or not value.strip():
    raise ValidationError(f"Input '{param_name}' must be a non-empty string.")


def _should_use_router() -> bool:
    """
    Check if router should be used based on configuration.

    Note: Delegates to shared utility in madspark.llm.utils for DRY compliance.
    """
    if should_use_router is None:
        return False
    return should_use_router(LLM_ROUTER_AVAILABLE, get_router)


def build_generation_prompt(topic: str, context: str, use_structured_output: bool = False) -> str:
  """Builds a prompt for generating ideas based on user input and context.

  Args:
    topic: The user's prompt/request for idea generation (can be questions, 
           statements, requests, or simple topics).
    context: Additional context or constraints for the idea generation process.

  Returns:
    A formatted prompt string to be used by the idea generator agent.
  """
  # Detect broad/philosophical topics that need simplification
  broad_topic_keywords = ['humanity', 'future of', 'meaning of', 'philosophy', 'existence', 
                         'universe', 'consciousness', 'life', 'death', 'reality', 'truth']
  is_broad_topic = any(keyword in topic.lower() for keyword in broad_topic_keywords)
  
  # Add extra guidance for broad topics
  broad_topic_guidance = ""
  if is_broad_topic:
      broad_topic_guidance = """
SPECIAL GUIDANCE FOR BROAD TOPICS:
- Focus on CONCRETE, SPECIFIC ideas that people can actually implement
- Avoid philosophical abstractions or theoretical concepts
- Each idea should suggest a clear action, project, or initiative
- Think "What can someone DO about this?" rather than "What does this mean?"

"""
  
  # Use different prompts for structured vs unstructured output
  if use_structured_output:
    # Simpler prompt when using structured output - no formatting instructions needed
    prompt_template = f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Generate creative and innovative ideas based on the topic and context provided.
Focus on practical, actionable ideas that address the user's needs.
{broad_topic_guidance}
Topic:
{topic}

Context:
{context}

Generate 5 diverse ideas that are innovative, practical, and directly address the topic within the given context."""
  else:
    # Legacy prompt with formatting instructions for text output
    prompt_template = f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Use the user's main prompt and context below to {IDEA_GENERATION_INSTRUCTION}.
Make sure the ideas are actionable and innovative.

IMPORTANT FORMAT REQUIREMENTS:
- Generate exactly 5 diverse ideas
- Start your response directly with "1." (no introductory text)
- Keep each idea concise (2-3 sentences maximum)
- Number each idea clearly (1., 2., 3., 4., 5.)
- For broad or philosophical topics, focus on specific, actionable ideas
{broad_topic_guidance}
User's main prompt:
{topic}

Context:
{context}

Start your response here with idea #1:
"""
  return prompt_template


# Configure the Google GenAI client
if GENAI_AVAILABLE:
    try:
        from madspark.agents.genai_client import get_genai_client, get_model_name
    except ImportError:
        # Fallback for local development/testing
        from .genai_client import get_genai_client, get_model_name

    idea_generator_client = get_genai_client()
    model_name = get_model_name()
else:
    # Mock client for CI environments without genai
    idea_generator_client = None
    model_name = "mock-model"

# Convert Pydantic models to GenAI schema format at module level (cached)
_IDEA_GENERATOR_GENAI_SCHEMA = pydantic_to_genai_schema(GeneratedIdeas)
_IMPROVER_GENAI_SCHEMA = pydantic_to_genai_schema(ImprovementResponse)


def generate_ideas(
    topic: str,
    context: str,
    temperature: float = 0.9,
    use_structured_output: bool = True,
    multimodal_files: Optional[List[Union[str, Path]]] = None,
    multimodal_urls: Optional[List[str]] = None,
    use_router: bool = True
) -> str:
  """Generates ideas based on a topic and context using the idea generator model.

  When use_router=True and LLM Router is available, routes through the
  multi-provider abstraction layer for automatic fallback and caching.

  Args:
    topic: The main topic for which ideas should be generated.
    context: Supporting context, constraints, or inspiration for the ideas.
    temperature: Controls randomness in generation (0.0-1.0). Higher values increase creativity.
    use_structured_output: Whether to use structured JSON output (default: True).
        Note: When routing through LLM Router, always returns structured JSON regardless
        of this flag, as router enforces Pydantic schema validation for type safety.
        Multimodal inputs (files/URLs) bypass router and use direct GenAI API.
    multimodal_files: Optional list of file paths (images, PDFs, documents) for context.
    multimodal_urls: Optional list of URLs for context.
    use_router: Whether to use LLM Router for provider abstraction (default: True)

  Returns:
    A string containing the generated ideas. If use_structured_output is True,
    returns JSON string. Otherwise, returns newline-separated text.
    Returns an empty string if the model provides no content.
  Raises:
    ValueError: If topic or context are empty or invalid, or if file/URL validation fails.
    FileNotFoundError: If specified file doesn't exist.
  """
  _validate_non_empty_string(topic, 'topic')
  _validate_non_empty_string(context, 'context')

  # Build base text prompt
  text_prompt: str = build_generation_prompt(topic=topic, context=context, use_structured_output=use_structured_output)

  # Process multi-modal inputs if provided
  contents = build_prompt_with_multimodal(
      text_prompt=text_prompt,
      multimodal_files=multimodal_files,
      multimodal_urls=multimodal_urls
  )

  # Try LLM Router first if available and configured
  # Note: Router doesn't support multimodal yet, so skip if multimodal inputs are present
  has_multimodal = bool(multimodal_files or multimodal_urls)
  should_route = use_router and LLM_ROUTER_AVAILABLE and get_router is not None and not has_multimodal
  if should_route and _should_use_router():
      try:
          router = get_router()
          validated, response = router.generate_structured(
              prompt=text_prompt,
              schema=GeneratedIdeas,
              system_instruction=SYSTEM_INSTRUCTION,
              temperature=temperature,
          )

          logger.info(f"Router generated ideas via {response.provider} ({response.tokens_used} tokens)")
          return json.dumps([idea.model_dump() for idea in validated.root])

      except AllProvidersFailedError as e:
          logger.warning(f"LLM Router failed, falling back to direct API: {e}")
      except Exception as e:
          logger.warning(f"Router error, falling back to direct API: {e}")

  if not GENAI_AVAILABLE or idea_generator_client is None:
    # Return mock response for CI/testing environments or when API key is not configured
    if use_structured_output:
        # Return structured mock data
        mock_ideas = [
            {
                "idea_number": 1,
                "title": f"Mock Idea for {topic}",
                "description": f"A mock idea generated for testing with context: {context}",
                "key_features": ["Feature 1", "Feature 2", "Feature 3"],
                "category": "Mock Category"
            },
            {
                "idea_number": 2,
                "title": f"Alternative Mock for {topic}",
                "description": f"Another mock idea with temperature {temperature}",
                "key_features": ["Feature A", "Feature B"],
                "category": "Mock Category"
            }
        ]
        return json.dumps(mock_ideas)
    else:
        # Legacy text format for backward compatibility
        # Simple language detection for mock responses
        if any(char >= '\u3040' and char <= '\u309F' or char >= '\u30A0' and char <= '\u30FF' or char >= '\u4E00' and char <= '\u9FAF' for char in topic + context):
            return f"モック生成されたアイデア '{topic}' のトピックで '{context}' のコンテキスト (温度 {temperature})"
        elif any(char in 'àâäæéèêëïîôöùûüÿ' for char in (topic + context).lower()):
            return f"Idée factice générée pour le sujet '{topic}' avec le contexte '{context}' à la température {temperature}"
        elif any(char in 'ñáíóúüç' for char in (topic + context).lower()):
            return f"Idea simulada generada para el tema '{topic}' con contexto '{context}' a temperatura {temperature}"
        elif any(char in 'äöüß' for char in (topic + context).lower()):
            return f"Mock-Idee generiert für Thema '{topic}' mit Kontext '{context}' bei Temperatur {temperature}"
        else:
            return f"Mock idea generated for topic '{topic}' with context '{context}' at temperature {temperature}"
  
  if idea_generator_client is None:
    from madspark.utils.errors import ConfigurationError
    raise ConfigurationError("Idea generator client is not configured but GENAI is enabled")
  
  try:
    if use_structured_output:
        # Create the generation config with pre-computed structured output schema
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=_IDEA_GENERATOR_GENAI_SCHEMA,
            system_instruction=SYSTEM_INSTRUCTION
        )
    else:
        # Legacy config without structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=SYSTEM_INSTRUCTION
        )

    response = idea_generator_client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config
    )
    agent_response = response.text if response.text else ""
  except (AttributeError, TypeError) as e:
    # Handle API response structure errors
    logging.error(f"API response structure error: {e}", exc_info=True)
    agent_response = ""
  except Exception as e:
    # Log other unexpected errors
    logging.error(f"Unexpected error calling Gemini API: {e}", exc_info=True)
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing `parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]`
  # will correctly result in an empty list if the response is effectively empty,
  # which is then handled by the coordinator.
  return agent_response


def build_improvement_prompt(
    original_idea: str, 
    critique: str, 
    advocacy_points: str, 
    skeptic_points: str, 
    topic: str,
    context: str,
    logical_inference: Optional[str] = None
) -> str:
  """Builds a prompt for improving an idea based on feedback.
  
  Args:
    original_idea: The original idea to improve.
    critique: The critic's evaluation of the idea.
    advocacy_points: The advocate's structured bullet points.
    skeptic_points: The skeptic's structured concerns.
    topic: The main topic/theme for the idea.
    context: The constraints or additional context for improvement.
    logical_inference: Optional logical analysis results to inform improvement.
    
  Returns:
    A formatted prompt string for idea improvement.
  """
  # Build logical inference section if provided
  logical_section = ""
  if logical_inference:
    logical_section = f"LOGICAL INFERENCE ANALYSIS:\n{logical_inference}\n\n"
  
  # Build logical inference guidance if provided
  logical_guidance = ""
  if logical_inference:
    logical_guidance = "- Use logical reasoning insights to enhance coherence and address any logical gaps\n"
  
  # Build logical inference instruction if provided
  logical_instruction = ""
  if logical_inference:
    logical_instruction = "6. Incorporates insights from the logical inference analysis\n"
  
  return (
      "You are helping to enhance an innovative idea based on comprehensive feedback.\n" +
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"TOPIC: {topic}\n"
      f"CONTEXT: {context}\n\n"
      f"ORIGINAL IDEA:\n{original_idea}\n\n"
      f"EVALUATION CRITERIA AND FEEDBACK:\n{critique}\n"
      f"Pay special attention to the specific scores and criteria mentioned above. "
      f"Your improved version should directly address any low-scoring areas while maintaining high-scoring aspects.\n\n"
      f"{logical_section}"
      f"STRENGTHS TO PRESERVE AND BUILD UPON:\n{advocacy_points}\n\n"
      f"CONCERNS TO ADDRESS WITH SOLUTIONS:\n{skeptic_points}\n\n"
      f"Generate an IMPROVED version of this idea that:\n"
      f"1. SPECIFICALLY addresses each evaluation criterion from the professional review\n"
      f"2. Maintains and amplifies the identified strengths\n"
      f"3. Provides concrete solutions for each concern raised\n"
      f"4. Remains bold, creative, and ambitious\n"
      f"5. Shows clear improvements in the areas that scored lower\n"
      f"{logical_instruction}\n"
      f"IMPORTANT GUIDELINES:\n"
      f"- If feasibility scored low, add specific implementation steps\n"
      f"- If innovation scored low, add unique differentiating features\n"
      f"- If cost-effectiveness scored low, optimize resource usage\n"
      f"- If scalability scored low, design for growth\n"
      f"- Keep all positive aspects while fixing weaknesses\n"
      f"{logical_guidance}"
      f"FORMAT REQUIREMENTS:\n"
      f"- Start directly with your improved idea (no meta-commentary)\n"
      f"- Present the idea in 2-3 clear, focused paragraphs\n"
      f"- Keep the total response under 500 words\n"
      f"- Make the first sentence compelling and complete\n\n"
      f"Present your improved idea below:"
  )


def _generate_fallback_improvement(original_idea: str, reason: str, advocacy_points: str = "") -> str:
  """Generate a fallback improvement message based on the reason for fallback.
  
  Args:
    original_idea: The original idea to improve.
    reason: The reason for using fallback ('safety', 'recitation', 'empty', etc.).
    advocacy_points: Optional advocacy points to include in some templates.
    
  Returns:
    A formatted fallback improvement message.
  """
  templates = {
      "safety": f"Enhanced version of: {original_idea}\n\nKey improvements based on multi-agent feedback:\n- Preserved strengths: {advocacy_points[:100]}{'...' if len(advocacy_points) > 100 else ''}\n- Incorporated professional insights for enhancement\n- Enhanced practical implementation approach\n- Addressed thoughtful considerations with solutions",
      "recitation": f"Refined approach: {original_idea}\n\nOptimizations based on feedback:\n- Leveraged identified strengths\n- Incorporated professional insights\n- Enhanced practical implementation\n- Improved scalability and resource efficiency",
      "empty": f"Improved: {original_idea}\n\nEnhancements based on analysis:\n- Built upon positive strengths\n- Incorporated professional insights\n- Optimized implementation approach\n- Enhanced cost-effectiveness and viability",
      "no_candidates": f"Enhanced: {original_idea}\n\nKey improvements from multi-agent analysis:\n- Preserved core innovation strengths\n- Addressed thoughtful considerations\n- Enhanced practical implementation\n- Improved scalability and cost optimization",
      "content_filtered": f"Optimized version: {original_idea}\n\nImprovements based on multi-agent feedback:\n- Enhanced feasibility with thoughtful considerations\n- Better resource efficiency from positive insights\n- Practical implementation approach incorporating professional analysis",
      "value_error": f"Modified: {original_idea}\n\nEnhancements from feedback synthesis:\n- Improved approach based on professional insights\n- Better implementation incorporating strengths\n- Enhanced viability addressing opportunities",
      "general_error": f"Updated: {original_idea}\n\nImprovements from multi-agent analysis:\n- Refined implementation based on professional insights\n- Enhanced approach incorporating positive strengths\n- Better execution strategy addressing thoughtful considerations"
  }
  return templates.get(reason, templates["general_error"])


def improve_idea(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    topic: str,
    context: str,
    logical_inference: Optional[str] = None,
    temperature: float = 0.9,
    multimodal_files: Optional[List[Union[str, Path]]] = None,
    multimodal_urls: Optional[List[str]] = None
) -> str:
  """Improves an idea based on feedback from multiple agents.

  This function now uses structured output to ensure clean responses
  without meta-commentary.

  Args:
    original_idea: The original idea to improve.
    critique: The critic's evaluation.
    advocacy_points: The advocate's bullet points.
    skeptic_points: The skeptic's concerns.
    topic: The main topic/theme for the idea.
    context: The constraints or additional context for improvement.
    logical_inference: Optional logical analysis results to inform improvement.
    temperature: Controls randomness in generation (0.0-1.0).
                 Default 0.9 to maintain creativity.
    multimodal_files: Optional list of file paths (images, PDFs, documents) for context.
    multimodal_urls: Optional list of URLs for context.

  Returns:
    An improved version of the idea that addresses feedback.
    Returns a fallback improvement if the model provides no content or is filtered.
    
  Raises:
    ValidationError: If any required input is empty or invalid.
    ConfigurationError: If API key is not configured.
  """
  # Try to import and use structured version
  try:
    from madspark.agents.structured_idea_generator import improve_idea_structured, _should_use_router
    # When CLI flags indicate router should be used, pass None for genai_client
    # so the router takes over instead of using direct Gemini API
    client_to_use = None if _should_use_router() else idea_generator_client
    # Use structured output version if available
    return improve_idea_structured(
        original_idea=original_idea,
        critique=critique,
        advocacy_points=advocacy_points,
        skeptic_points=skeptic_points,
        topic=topic,
        context=context,
        logical_inference=logical_inference,
        temperature=temperature,
        genai_client=client_to_use,
        model_name=model_name,
        multimodal_files=multimodal_files,
        multimodal_urls=multimodal_urls
    )
  except (ImportError, Exception) as e:
    # Fall back to original implementation on any error
    # This ensures consistent behavior whether structured output fails to import
    # or raises an exception during execution
    if not isinstance(e, ImportError):
        logging.warning(f"Structured output failed, falling back to original: {e}")
    pass  # Continue with original implementation below
  
  # Original implementation as fallback
  # Validate inputs
  _validate_non_empty_string(original_idea, 'original_idea')
  _validate_non_empty_string(critique, 'critique')
  _validate_non_empty_string(advocacy_points, 'advocacy_points')
  _validate_non_empty_string(skeptic_points, 'skeptic_points')
  _validate_non_empty_string(topic, 'topic')
  _validate_non_empty_string(context, 'context')

  # Build base text prompt
  text_prompt: str = build_improvement_prompt(
      original_idea=original_idea,
      critique=critique,
      advocacy_points=advocacy_points,
      skeptic_points=skeptic_points,
      topic=topic,
      context=context,
      logical_inference=logical_inference
  )

  # Process multi-modal inputs if provided
  contents = build_prompt_with_multimodal(
      text_prompt=text_prompt,
      multimodal_files=multimodal_files,
      multimodal_urls=multimodal_urls
  )
  
  if not GENAI_AVAILABLE or idea_generator_client is None:
    # Return mock improvement for CI/testing environments
    return f"Improved version of: {original_idea}\n\nEnhancements based on feedback:\n- Addressed critique points\n- Incorporated advocacy strengths\n- Resolved skeptical concerns"
  
  try:
    # Create the generation config with module-level safety settings
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=SYSTEM_INSTRUCTION,
        safety_settings=_IMPROVER_SAFETY_SETTINGS
    )

    response = idea_generator_client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config
    )
    
    # Check for content filtering or blocked responses
    if hasattr(response, 'candidates') and response.candidates:
      candidate = response.candidates[0]
      finish_reason = getattr(candidate, 'finish_reason', None)
      
      if finish_reason == 1:  # SAFETY (content filtered)
        logging.warning("Gemini API response was filtered for safety. Using fallback improvement.")
        agent_response = _generate_fallback_improvement(original_idea, "safety", advocacy_points)
      elif finish_reason == 3:  # RECITATION (potential copyright issues)
        logging.warning("Gemini API response was blocked for recitation. Using fallback improvement.")
        agent_response = _generate_fallback_improvement(original_idea, "recitation")
      elif response.text:
        agent_response = response.text
      else:
        logging.warning("Gemini API returned empty response. Using fallback improvement.")
        agent_response = _generate_fallback_improvement(original_idea, "empty")
    else:
      logging.warning("Gemini API returned no candidates. Using fallback improvement.")
      agent_response = _generate_fallback_improvement(original_idea, "no_candidates")
      
  except ValueError as e:
    # Handle specific content filtering errors
    if "response.text" in str(e) and "finish_reason" in str(e):
      logging.warning(f"Gemini API content filtered: {e}. Using fallback improvement.")
      agent_response = _generate_fallback_improvement(original_idea, "content_filtered")
    else:
      logging.error(f"Gemini API ValueError: {e}", exc_info=True)
      agent_response = _generate_fallback_improvement(original_idea, "value_error")
  except (AttributeError, TypeError) as e:
    # Handle API response structure errors
    logging.error(f"API response structure error in improve_idea: {e}", exc_info=True)
    agent_response = _generate_fallback_improvement(original_idea, "general_error")
  except Exception as e:
    # Log other unexpected errors
    logging.error(f"Unexpected error calling Gemini API: {e}", exc_info=True)
    agent_response = _generate_fallback_improvement(original_idea, "general_error")
  
  return agent_response


def improve_ideas_batch(
    ideas_with_feedback: List[Dict[str, str]], 
    topic: str,
    context: str, 
    temperature: float = 0.9
) -> Tuple[List[Dict[str, Any]], int]:
  """Batch improvement for multiple ideas in a single API call.
  
  This function significantly reduces API calls by processing all ideas
  in one request instead of making N separate calls.
  
  Args:
    ideas_with_feedback: List of dicts with 'idea', 'critique', 'advocacy', 'skepticism' keys
                        and optional 'logical_inference' key
    topic: The main topic/theme for the ideas
    context: The constraints or additional context for improvement
    temperature: Generation temperature (0.0-1.0)
    
  Returns:
    List of improvement responses with structured format including:
    - idea_index: Index of the idea
    - improved_idea: The enhanced version of the idea
    - key_improvements: List of key improvements made (optional)
    
  Raises:
    ValueError: If input format is invalid or JSON parsing fails
    RuntimeError: If API call fails
  """
  if not ideas_with_feedback:
    return [], 0
  
  # Validate input format
  for i, item in enumerate(ideas_with_feedback):
    if not isinstance(item, dict):
      raise ValueError(f"Item {i} must be a dictionary")
    required_keys = {'idea', 'critique', 'advocacy', 'skepticism'}
    if not all(key in item for key in required_keys):
      raise ValueError(f"Item {i} must have 'idea', 'critique', 'advocacy', and 'skepticism' keys")
  
  # Build batch prompt
  items_text = []
  for i, item in enumerate(ideas_with_feedback):
    # Build logical inference section if available
    logical_section = ""
    if item.get('logical_inference'):
      logical_section = f"\n\nLOGICAL INFERENCE ANALYSIS:\n{item['logical_inference']}"
    
    items_text.append(
      f"IDEA {i+1}:\n{item['idea']}\n\n"
      f"CRITIQUE:\n{item['critique']}\n\n"
      f"ADVOCACY:\n{item['advocacy']}\n\n"
      f"SKEPTICISM:\n{item['skepticism']}{logical_section}"
    )
  
  # Define newline for use in f-string
  newline = '\n'
  prompt = (
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"Topic: {topic}\n"
      f"Context: {context}\n\n"
      f"{newline.join(items_text)}\n\n"
      "For EACH idea above, create an improved version that:\n"
      "1. Addresses ALL critique points\n"
      "2. Maintains the advocated strengths\n"
      "3. Provides solutions for skeptic concerns\n"
      "4. Incorporates insights from logical inference analysis (when provided)\n"
      "5. Remains bold and creative\n\n"
      "Return improvements in this exact JSON format:\n"
      "{\n"
      '  "idea_index": <0-based index>,\n'
      '  "improved_idea": "The complete improved idea text",\n'
      '  "key_improvements": ["improvement1", "improvement2", ...] (optional)\n'
      "}\n\n"
      "Return ONLY a JSON array containing one object per idea, in order.\n"
      "Write only the improved ideas, no meta-commentary."
  )
  
  if not GENAI_AVAILABLE or idea_generator_client is None:
    # Return mock improvements for CI/testing
    mock_results = []
    for i, item in enumerate(ideas_with_feedback):
      mock_results.append({
        "idea_index": i,
        "improved_idea": f"Mock improved version of: {item['idea'][:50]}... "
                        f"This addresses the critique and maintains strengths.",
        "key_improvements": ["Mock improvement 1", "Mock improvement 2"]
      })
    return mock_results, 0  # Return tuple for consistency
  
  try:
    
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        system_instruction=SYSTEM_INSTRUCTION + " Return a JSON array of improved ideas."
    )
    
    response = idea_generator_client.models.generate_content(
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
      improvements = json.loads(response.text)
    except json.JSONDecodeError as e:
      # Try fallback parsing for problematic JSON (especially with Japanese content)
      try:
        logger.warning(f"JSON decode error, attempting fallback parsing: {e}")
        improvements = parse_batch_json_with_fallback(response.text, expected_count=len(ideas_with_feedback))
        logger.info(f"Fallback parsing successful, recovered {len(improvements)} items")
      except Exception as fallback_error:
        raise BatchParsingError(
          f"Invalid JSON response from API: {e}. Fallback parsing also failed: {fallback_error}",
          batch_type="idea_improvement",
          items_count=len(ideas_with_feedback),
          raw_response=response.text,
          parse_error=e
        )
    
    # Validate and process results
    if not isinstance(improvements, list):
      raise ValueError("Response must be a JSON array")
    
    if len(improvements) != len(ideas_with_feedback):
      raise ValueError(f"Expected {len(ideas_with_feedback)} improvements, got {len(improvements)}")
    
    # Process results
    results = []
    for improvement in improvements:
      # Validate structure
      if 'idea_index' not in improvement or 'improved_idea' not in improvement:
        raise ValueError(f"Missing required fields in improvement: {improvement}")
      
      # key_improvements is optional
      result = {
        "idea_index": improvement["idea_index"],
        "improved_idea": improvement["improved_idea"]
      }
      
      if "key_improvements" in improvement:
        result["key_improvements"] = improvement["key_improvements"]
      
      results.append(result)
    
    # Sort by idea_index to ensure order
    results.sort(key=lambda x: x['idea_index'])
    
    # Always return tuple for consistent API
    return results, token_usage if isinstance(token_usage, (int, float)) else 0
    
  except json.JSONDecodeError as e:
    logging.error(f"JSON parsing error in batch improvement: {e}", exc_info=True)
    raise ValueError(f"Invalid JSON response: {e}")
  except (AttributeError, TypeError, KeyError) as e:
    logging.error(f"Data structure error in batch improvement: {e}", exc_info=True)
    raise RuntimeError(f"Batch improvement data error: {e}")
  except Exception as e:
    logging.error(f"Unexpected batch improvement failure: {e}", exc_info=True)
    raise RuntimeError(f"Batch improvement failed: {e}")


