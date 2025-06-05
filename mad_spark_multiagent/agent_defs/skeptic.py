import os

from google.adk.agents import Agent
from google.adk.agents import Tool

skeptic_agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
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
  """Critically analyzes an idea, playing devil's advocate."""
  prompt = (
      "Here's an idea:\n{idea}\n\nHere's the case made for it:\n{advocacy}\n\nAnd"
      " the context:\n{context}\n\nPlay devil's advocate. Critically analyze"
      " the idea, identify potential flaws, risks, and unintended"
      " consequences. Challenge assumptions and present counterarguments."
  ).format(idea=idea, advocacy=advocacy, context=context)
  return skeptic_agent.call(prompt=prompt)


skeptic_agent.add_tools([criticize_idea])
