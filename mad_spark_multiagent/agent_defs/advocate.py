import os

from google.adk.agents import Agent
from google.adk.agents import Tool

advocate_agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
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
  """Advocates for an idea using its evaluation and context."""
  prompt = (
      "Here's an idea:\n{idea}\n\nHere's its evaluation:\n{evaluation}\n\nAnd"
      " the context:\n{context}\n\nBased on this, build a strong case for the"
      " idea, focusing on its strengths and potential benefits. Address any"
      " criticisms from the evaluation constructively."
  ).format(idea=idea, evaluation=evaluation, context=context)
  return advocate_agent.call(prompt=prompt)


advocate_agent.add_tools([advocate_idea])
