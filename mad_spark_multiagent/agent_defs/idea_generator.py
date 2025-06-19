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
    model=os.environ.get("GOOGLE_GENAI_MODEL"), # type: ignore # Model type can be complex
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
  """
  prompt: str = build_generation_prompt(topic=topic, context=context)
  # Assuming agent.call() returns a string. If it's more complex,
  # the return type of agent.call and this function might need adjustment.
  agent_response: Any = idea_generator_agent.call(prompt=prompt)
  if not isinstance(agent_response, str):
    # Add basic handling if the response is not a string, as expected by type hint.
    # This depends on how ADK's agent.call() is typed and behaves.
    # For now, we'll assume it's meant to be a string or can be stringified.
    return str(agent_response)
  return agent_response


idea_generator_agent.add_tools([generate_ideas])
