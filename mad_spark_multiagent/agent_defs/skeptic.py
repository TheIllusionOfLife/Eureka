"""Skeptic Agent.

This module defines the Skeptic agent (Devil's Advocate) and its tools.
The agent is responsible for critically analyzing ideas, challenging assumptions,
and identifying potential flaws or risks.
"""
import os
from typing import Any # For model type, if not specifically known

from google.adk.agents import Agent
from google.adk.agents import Tool

# The Skeptic agent plays devil's advocate, critically analyzing ideas.
skeptic_agent: Agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"), # type: ignore
    instructions=(
        "You are a devil's advocate. Given an idea, the arguments for it, and"
        " context, critically analyze the idea. Identify potential flaws,"
        " risks, and unintended consequences. Challenge assumptions and present"
        " counterarguments."
    ),
)


@Tool(
    name="criticize_idea",
    description=(
        "Critically analyzes an idea, playing devil's advocate. Identifies"
        " potential flaws, risks, and unintended consequences. Challenges"
        " assumptions and presents counterarguments."
    ),
)
def criticize_idea(idea: str, advocacy: str, context: str) -> str:
  """Critically analyzes an idea, playing devil's advocate, using the skeptic_agent.

  Args:
    idea: The idea to be critically analyzed.
    advocacy: The arguments previously made in favor of the idea.
    context: Additional context relevant for the critical analysis.

  Returns:
    A string containing the critical analysis, counterarguments, and identified risks.
  """
  prompt: str = (
      f"Here's an idea:\n{idea}\n\n"
      f"Here's the case made for it:\n{advocacy}\n\n"
      f"And the context:\n{context}\n\n"
      "Play devil's advocate. Critically analyze the idea, identify "
      "potential flaws, risks, and unintended consequences. Challenge "
      "assumptions and present counterarguments."
  )
  agent_response: Any = skeptic_agent.call(prompt=prompt)
  if not isinstance(agent_response, str):
    return str(agent_response)
  return agent_response


skeptic_agent.add_tools([criticize_idea])
