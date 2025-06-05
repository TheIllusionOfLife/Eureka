from google.adk.agents import Agent, Tool


def advocate_idea(idea: str) -> dict:
    """Provide positive points about the idea."""
    prompt = (
        f"以下のアイデアについて、擁護者としてその良い点・メリットを3つ挙げてください。\n"
        f"【アイデア】\n{idea}\n"
    )
    response = advocate_agent.call({"prompt": prompt, "temperature": 0.5})
    text = response.get("choices", [{}])[0].get("text", "")
    return {"status": "success", "advocacy": text}


advocate_agent = Agent(
    name="advocate",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア擁護者エージェント",
    instruction="あなたはこのアイデアの良い点を擁護者として挙げてください。",
    tools=[Tool(name="advocate_idea", func=advocate_idea)]
)
