"""Idea Generation Agent.

This module defines the Idea Generator agent and its associated tools.
The agent is responsible for generating novel ideas based on a given topic
and contextual information.
"""
import os
from typing import Any # For model type, if not specifically known

from google.adk.agents import Agent
from google.adk.agents import Tool


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


# The Idea Generator agent specializes in brainstorming and creating novel concepts.
idea_generator_agent: Agent = Agent(
    model=os.environ["GOOGLE_GENAI_MODEL"],
    instructions=(
        "You are an expert idea generator. Given a topic and some context,"
        " generate a list of diverse and creative ideas."
    ),
)


@Tool(
    name="generate_ideas",
    description=(
        "Generates a list of diverse and creative ideas on a given topic using"
        " the provided context."
    ),
)
def generate_ideas(topic: str, context: str) -> str:
  """Generates ideas based on a topic and context using the idea_generator_agent.

  This function is registered as a tool for the agent.

  Args:
    topic: The main topic for which ideas should be generated.
    context: Supporting context, constraints, or inspiration for the ideas.

  Returns:
    A string containing the generated ideas, typically newline-separated.
    Returns an empty string if the agent provides no content.
  Raises:
    ValueError: If topic or context are empty or invalid.
  """
  if not isinstance(topic, str) or not topic.strip():
    raise ValueError("Input 'topic' to generate_ideas must be a non-empty string.")
  if not isinstance(context, str) or not context.strip():
    raise ValueError("Input 'context' to generate_ideas must be a non-empty string.")

  prompt: str = build_generation_prompt(topic=topic, context=context)
  agent_response: Any = idea_generator_agent.call(prompt=prompt)

  if not isinstance(agent_response, str):
    agent_response = str(agent_response) # Ensure it's a string

  # If agent_response is empty or only whitespace, it will be returned as such.
  # The coordinator's parsing `parsed_ideas = [idea.strip() for idea in raw_generated_ideas.split("\n") if idea.strip()]`
  # will correctly result in an empty list if the response is effectively empty,
  # which is then handled by the coordinator.
  return agent_response


idea_generator_agent.add_tools([generate_ideas])
