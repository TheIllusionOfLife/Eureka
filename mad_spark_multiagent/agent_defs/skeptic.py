from google.adk.agents import Agent, Tool


def criticize_idea(idea: str) -> dict:
    """Return a simple criticism statement."""
    text = f"Potential issues with '{idea}' highlighted."
    return {"status": "success", "criticism": text}


skeptic_agent = Agent(
    name="skeptic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア懐疑者エージェント",
    instruction="あなたはこのアイデアのリスクや問題点を懐疑的に指摘してください。",
)
skeptic_agent.add_tools([Tool(name="criticize_idea", func=criticize_idea)])
