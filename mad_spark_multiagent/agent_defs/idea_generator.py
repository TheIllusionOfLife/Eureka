"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import os
from typing import Any
import google.generativeai as genai


def build_generation_prompt(topic: str, context: str) -> str:
  """Builds a prompt for generating ideas based on a topic and context.

  Args:
    topic: The main topic for idea generation.
    context: Additional context or constraints for the idea generation process.

  Returns:
    A formatted prompt string to be used by the idea generator agent.
  """
  return (
      f"Use the context below to generate a list of diverse and creative ideas"
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
        system_instruction=(
            "You are an expert idea generator. Given a topic and some context,"
            " generate a list of diverse and creative ideas."
        )
    )
else:
    idea_generator_model = None


def generate_ideas(topic: str, context: str) -> str:
  """Generates ideas based on a topic and context using the idea generator model.

  Args:
    topic: The main topic for which ideas should be generated.
    context: Supporting context, constraints, or inspiration for the ideas.

  Returns:
    A string containing the generated ideas, typically newline-separated.
    Returns an empty string if the model provides no content.
  Raises:
    ValueError: If topic or context are empty or invalid.
  """
  if not isinstance(topic, str) or not topic.strip():
    raise ValueError("Input 'topic' to generate_ideas must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to generate_ideas must be a non-empty string.")

  prompt: str = build_generation_prompt(topic=topic, context=context)
  
  if idea_generator_model is None:
    raise RuntimeError("GOOGLE_API_KEY not configured - cannot generate ideas")
  
  try:
    response = idea_generator_model.generate_content(prompt)
    agent_response = response.text if response.text else ""
  except Exception as e:
    # Return empty string on any API error - coordinator will handle this
    agent_response = ""

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing `parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]`
  # will correctly result in an empty list if the response is effectively empty,
  # which is then handled by the coordinator.
  return agent_response


