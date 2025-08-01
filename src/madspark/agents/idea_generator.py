"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import logging
from typing import Any

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
# These relaxed thresholds are necessary to prevent overly aggressive content
# filtering when processing critical feedback and improvement suggestions
if GENAI_AVAILABLE and types:
    _IMPROVER_SAFETY_SETTINGS = [
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH", 
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH"
        )
    ]
else:
    _IMPROVER_SAFETY_SETTINGS = []


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


def build_generation_prompt(topic: str, context: str) -> str:
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
  
  # Use a clean template-based approach for better readability (KISS principle)
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


def generate_ideas(topic: str, context: str, temperature: float = 0.9) -> str:
  """Generates ideas based on a topic and context using the idea generator model.

  Args:
    topic: The main topic for which ideas should be generated.
    context: Supporting context, constraints, or inspiration for the ideas.
    temperature: Controls randomness in generation (0.0-1.0). Higher values increase creativity.

  Returns:
    A string containing the generated ideas, typically newline-separated.
    Returns an empty string if the model provides no content.
  Raises:
    ValueError: If topic or context are empty or invalid.
  """
  _validate_non_empty_string(topic, 'topic')
  _validate_non_empty_string(context, 'context')

  prompt: str = build_generation_prompt(topic=topic, context=context)
  
  if not GENAI_AVAILABLE or idea_generator_client is None:
    # Return mock response for CI/testing environments or when API key is not configured
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
    # Create the generation config with system instruction
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=SYSTEM_INSTRUCTION
    )
    response = idea_generator_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API: {e}", exc_info=True)
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
    theme: str
) -> str:
  """Builds a prompt for improving an idea based on feedback.
  
  Args:
    original_idea: The original idea to improve.
    critique: The critic's evaluation of the idea.
    advocacy_points: The advocate's structured bullet points.
    skeptic_points: The skeptic's structured concerns.
    theme: The original theme/topic for context.
    
  Returns:
    A formatted prompt string for idea improvement.
  """
  return (
      "You are helping to enhance an innovative idea based on comprehensive feedback.\n" +
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"ORIGINAL THEME: {theme}\n\n"
      f"ORIGINAL IDEA:\n{original_idea}\n\n"
      f"EVALUATION CRITERIA AND FEEDBACK:\n{critique}\n"
      f"Pay special attention to the specific scores and criteria mentioned above. "
      f"Your improved version should directly address any low-scoring areas while maintaining high-scoring aspects.\n\n"
      f"STRENGTHS TO PRESERVE AND BUILD UPON:\n{advocacy_points}\n\n"
      f"CONCERNS TO ADDRESS WITH SOLUTIONS:\n{skeptic_points}\n\n"
      f"Generate an IMPROVED version of this idea that:\n"
      f"1. SPECIFICALLY addresses each evaluation criterion from the professional review\n"
      f"2. Maintains and amplifies the identified strengths\n"
      f"3. Provides concrete solutions for each concern raised\n"
      f"4. Remains bold, creative, and ambitious\n"
      f"5. Shows clear improvements in the areas that scored lower\n\n"
      f"IMPORTANT GUIDELINES:\n"
      f"- If feasibility scored low, add specific implementation steps\n"
      f"- If innovation scored low, add unique differentiating features\n"
      f"- If cost-effectiveness scored low, optimize resource usage\n"
      f"- If scalability scored low, design for growth\n"
      f"- Keep all positive aspects while fixing weaknesses\n\n"
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
    theme: str,
    temperature: float = 0.9
) -> str:
  """Improves an idea based on feedback from multiple agents.
  
  This function now uses structured output to ensure clean responses
  without meta-commentary.
  
  Args:
    original_idea: The original idea to improve.
    critique: The critic's evaluation.
    advocacy_points: The advocate's bullet points.
    skeptic_points: The skeptic's concerns.
    theme: The original theme for context.
    temperature: Controls randomness in generation (0.0-1.0). 
                 Default 0.9 to maintain creativity.
    
  Returns:
    An improved version of the idea that addresses feedback.
    Returns a fallback improvement if the model provides no content or is filtered.
    
  Raises:
    ValidationError: If any required input is empty or invalid.
    ConfigurationError: If API key is not configured.
  """
  # Try to import and use structured version
  try:
    from madspark.agents.structured_idea_generator import improve_idea_structured
    # Use structured output version if available
    return improve_idea_structured(
        original_idea=original_idea,
        critique=critique,
        advocacy_points=advocacy_points,
        skeptic_points=skeptic_points,
        theme=theme,
        temperature=temperature,
        genai_client=idea_generator_client,
        model_name=model_name
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
  _validate_non_empty_string(theme, 'theme')
  
  prompt: str = build_improvement_prompt(
      original_idea=original_idea,
      critique=critique,
      advocacy_points=advocacy_points,
      skeptic_points=skeptic_points,
      theme=theme
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
        contents=prompt,
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
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API: {e}", exc_info=True)
    agent_response = _generate_fallback_improvement(original_idea, "general_error")
  
  return agent_response


