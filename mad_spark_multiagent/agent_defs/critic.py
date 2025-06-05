import os

from google.adk.agents import Agent
from google.adk.agents import Tool

critic_agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
    instructions=(
        "You are an expert critic. Evaluate the given ideas based on the"
        " provided criteria and context. Provide constructive feedback and"
        " identify potential weaknesses."
    ),
)


@Tool(
    name="evaluate_ideas",
    description=(
        "Evaluates a list of ideas based on given criteria and context,"
        " providing constructive feedback."
    ),
)
def evaluate_ideas(ideas: str, criteria: str, context: str) -> str:
  """Evaluates ideas based on criteria and context."""
  prompt = (
      "Please evaluate the following ideas:\n\n{ideas}\n\nBased on these"
      " criteria:\n{criteria}\n\nAnd this context:\n{context}\n\nProvide your"
      " evaluation:"
  ).format(ideas=ideas, criteria=criteria, context=context)
  return critic_agent.call(prompt=prompt)


critic_agent.add_tools([evaluate_ideas])
