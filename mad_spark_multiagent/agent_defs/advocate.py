from google.adk.agents import Agent, Tool


def advocate_idea(idea: str) -> dict:
    """Return a simple advocacy statement."""
    text = f"Positive aspects of '{idea}' presented."
    return {"status": "success", "advocacy": text}


advocate_agent = Agent(
    name="advocate",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア擁護者エージェント",
    instruction="あなたはこのアイデアの良い点を擁護者として挙げてください。",
)
advocate_agent.add_tools([Tool(name="advocate_idea", func=advocate_idea)])
