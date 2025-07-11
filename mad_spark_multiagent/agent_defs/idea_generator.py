"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import os
import logging
from typing import Any
import google.generativeai as genai
try:
    from mad_spark_multiagent.errors import IdeaGenerationError, ValidationError, ConfigurationError
except ImportError:
    # Fallback for local development/testing
    from errors import IdeaGenerationError, ValidationError, ConfigurationError

# Prompt constants to avoid duplication
IDEA_GENERATION_INSTRUCTION = "generate a list of diverse and creative ideas"
SYSTEM_INSTRUCTION = f"You are an expert idea generator. Given a topic and some context, {IDEA_GENERATION_INSTRUCTION}."


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


# Configure the Google GenerativeAI client
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

if api_key:
    genai.configure(api_key=api_key)
    # Create the model instance
    idea_generator_model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_INSTRUCTION
    )
else:
    idea_generator_model = None


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
  
  if idea_generator_model is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot generate ideas")
  
  try:
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = idea_generator_model.generate_content(prompt, generation_config=generation_config)
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
      f"You are tasked with improving an idea based on comprehensive feedback.\n\n"
      f"ORIGINAL THEME: {theme}\n\n"
      f"ORIGINAL IDEA:\n{original_idea}\n\n"
      f"CRITIC'S EVALUATION:\n{critique}\n\n"
      f"ADVOCATE'S POINTS:\n{advocacy_points}\n\n"
      f"SKEPTIC'S CONCERNS:\n{skeptic_points}\n\n"
      f"Generate an IMPROVED version of this idea that:\n"
      f"1. Maintains the core innovation and strengths highlighted by the Advocate\n"
      f"2. Directly addresses the specific concerns raised by the Skeptic\n"
      f"3. Incorporates the Critic's suggestions for improvement\n"
      f"4. Remains bold, creative, and ambitious (don't over-correct into boring)\n"
      f"5. Provides concrete solutions to identified problems\n\n"
      f"IMPORTANT: The goal is to ENHANCE the idea, not replace it. Build upon what works.\n"
      f"- Keep all the positive aspects that earned the original score\n"
      f"- Add solutions and safeguards for the identified weaknesses\n"
      f"- Make it more feasible without sacrificing innovation\n\n"
      f"Present the improved idea as a clear, actionable concept. "
      f"Focus on making it more robust while preserving its innovative spirit.\n\n"
      f"IMPROVED IDEA:"
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
    Returns an empty string if the model provides no content.
    
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
  
  if idea_generator_model is None:
    raise ConfigurationError("GOOGLE_API_KEY not configured - cannot improve ideas")
  
  try:
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = idea_generator_model.generate_content(prompt, generation_config=generation_config)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Log the full error for better debugging
    logging.error(f"Error calling Gemini API: {e}", exc_info=True)
    agent_response = ""
  
  return agent_response


