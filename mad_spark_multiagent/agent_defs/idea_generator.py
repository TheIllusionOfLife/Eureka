import os

from google.adk.agents import Agent
from google.adk.agents import Tool


def build_generation_prompt(topic: str, context: str) -> str:
  """Builds a prompt for generating ideas based on a topic and context."""
  return (
      "Use the context below to generate a list of diverse and creative ideas"
      f" on the topic of {topic}. Make sure the ideas are actionable and"
      " innovative.\n\nContext:\n{context}\n\nIdeas:"
  )


idea_generator_agent = Agent(
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
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
  """Generates ideas based on a topic and context."""
  prompt = build_generation_prompt(topic=topic, context=context)
  return idea_generator_agent.call(prompt=prompt)


idea_generator_agent.add_tools([generate_ideas])
