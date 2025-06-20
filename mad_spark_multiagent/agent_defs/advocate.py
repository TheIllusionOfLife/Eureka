"""Advocate Agent.

This module defines the Advocate agent and its associated tools.
The agent is responsible for constructing persuasive arguments in favor of
an idea, considering its evaluation and context.
"""
import os
from typing import Any # For model type, if not specifically known

from google.adk.agents import Agent
from google.adk.agents import Tool

from mad_spark_multiagent.constants import ADVOCATE_EMPTY_RESPONSE

# The Advocate agent builds a compelling case for an idea.
advocate_agent: Agent = Agent(
    model=os.environ["GOOGLE_GENAI_MODEL"],
    instructions=(
        "You are a persuasive advocate. Given an idea, its evaluation, and"
        " context, build a strong case for the idea, highlighting its"
        " strengths and potential benefits."
    ),
)


@Tool(
    name="advocate_idea",
    description=(
        "Builds a strong case for an idea, highlighting its strengths and"
        " potential benefits, considering its evaluation and context."
    ),
)
def advocate_idea(idea: str, evaluation: str, context: str) -> str:
  """Advocates for an idea using its evaluation and context via the advocate_agent.

  Args:
    idea: The idea to advocate for.
    evaluation: The evaluation received for the idea (e.g., from a critic).
    context: Additional context relevant for building the advocacy.

  Returns:
    A string containing the persuasive arguments for the idea.
    Returns a placeholder string if the agent provides no content.
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
      f"Here's an idea:\n{idea}\n\n"
      f"Here's its evaluation:\n{evaluation}\n\n"
      f"And the context:\n{context}\n\n"
      "Based on this, build a strong case for the idea, focusing on its "
      "strengths and potential benefits. Address any criticisms from the "
      "evaluation constructively."
  )
  agent_response: Any = advocate_agent.call(prompt=prompt)
  if not isinstance(agent_response, str):
    agent_response = str(agent_response) # Ensure it's a string

  if not agent_response.strip():
    # This specific string is recognized by the coordinator's error handling.
    return ADVOCATE_EMPTY_RESPONSE
  return agent_response


advocate_agent.add_tools([advocate_idea])
