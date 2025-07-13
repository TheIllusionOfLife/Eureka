"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import os
import logging
from typing import Any
from google import genai
from google.genai import types
try:
    from mad_spark_multiagent.errors import IdeaGenerationError, ValidationError, ConfigurationError
except ImportError:
    # Fallback for local development/testing
    from errors import IdeaGenerationError, ValidationError, ConfigurationError

# Import prompt constants from constants module
try:
    from mad_spark_multiagent.constants import IDEA_GENERATION_INSTRUCTION, IDEA_GENERATOR_SYSTEM_INSTRUCTION as SYSTEM_INSTRUCTION
except ImportError:
    # Fallback for local development/testing
    from constants import IDEA_GENERATION_INSTRUCTION, IDEA_GENERATOR_SYSTEM_INSTRUCTION as SYSTEM_INSTRUCTION

# Safety settings for constructive feedback generation
# These relaxed thresholds are necessary to prevent overly aggressive content
# filtering when processing critical feedback and improvement suggestions
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
  """Builds a prompt for generating ideas based on a topic and context.

  Args:
    topic: The main topic for idea generation.
    context: Additional context or constraints for the idea generation process.

  Returns:
    A formatted prompt string to be used by the idea generator agent.
  """
  return (
      f"Use the context below to {IDEA_GENERATION_INSTRUCTION}"
      f" on the topic of {topic}. Make sure the ideas are actionable and"
      f" innovative.\n\nContext:\n{context}\n\nIdeas:"
  )


# Configure the Google GenAI client
try:
    from mad_spark_multiagent.agent_defs.genai_client import get_genai_client, get_model_name
except ImportError:
    # Fallback for local development/testing
    from agent_defs.genai_client import get_genai_client, get_model_name

idea_generator_client = get_genai_client()
model_name = get_model_name()


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
  
  if idea_generator_client is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot generate ideas")
  
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
      f"You are helping to enhance an innovative idea based on comprehensive feedback.\n\n"
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
      f"ENHANCED CONCEPT:"
  )


def improve_idea(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    theme: str,
    temperature: float = 0.9
) -> str:
  """Improves an idea based on feedback from multiple agents.
  
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
  
  if idea_generator_client is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot improve ideas")
  
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
        agent_response = f"Enhanced version of: {original_idea}\n\nKey improvements based on multi-agent feedback:\n- Preserved strengths: {advocacy_points[:100]}{'...' if len(advocacy_points) > 100 else ''}\n- Incorporated professional insights for enhancement\n- Enhanced practical implementation approach\n- Addressed thoughtful considerations with solutions"
      elif finish_reason == 3:  # RECITATION (potential copyright issues)
        logging.warning("Gemini API response was blocked for recitation. Using fallback improvement.")
        agent_response = f"Refined approach: {original_idea}\n\nOptimizations based on feedback:\n- Leveraged identified strengths\n- Incorporated professional insights\n- Enhanced practical implementation\n- Improved scalability and resource efficiency"
      elif response.text:
        agent_response = response.text
      else:
        logging.warning("Gemini API returned empty response. Using fallback improvement.")
        agent_response = f"Improved: {original_idea}\n\nEnhancements based on analysis:\n- Built upon positive strengths\n- Incorporated professional insights\n- Optimized implementation approach\n- Enhanced cost-effectiveness and viability"
    else:
      logging.warning("Gemini API returned no candidates. Using fallback improvement.")
      agent_response = f"Enhanced: {original_idea}\n\nKey improvements from multi-agent analysis:\n- Preserved core innovation strengths\n- Addressed thoughtful considerations\n- Enhanced practical implementation\n- Improved scalability and cost optimization"
      
  except ValueError as e:
    # Handle specific content filtering errors
    if "response.text" in str(e) and "finish_reason" in str(e):
      logging.warning(f"Gemini API content filtered: {e}. Using fallback improvement.")
      agent_response = f"Optimized version: {original_idea}\n\nImprovements based on multi-agent feedback:\n- Enhanced feasibility with thoughtful considerations\n- Better resource efficiency from positive insights\n- Practical implementation approach incorporating professional analysis"
    else:
      logging.error(f"Gemini API ValueError: {e}", exc_info=True)
      agent_response = f"Modified: {original_idea}\n\nEnhancements from feedback synthesis:\n- Improved approach based on professional insights\n- Better implementation incorporating strengths\n- Enhanced viability addressing opportunities"
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API: {e}", exc_info=True)
    agent_response = f"Updated: {original_idea}\n\nImprovements from multi-agent analysis:\n- Refined implementation based on professional insights\n- Enhanced approach incorporating positive strengths\n- Better execution strategy addressing thoughtful considerations"
  
  return agent_response


