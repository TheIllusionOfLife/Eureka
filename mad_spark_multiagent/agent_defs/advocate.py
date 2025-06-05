from google.adk.agents import Agent, Tool


def advocate_idea(idea: str) -> dict:
    """
    擁護役として、アイデアの良い点や可能性を挙げる
    """
    prompt = (
        f"以下のアイデアについて、擁護者としてその良い点・メリットを3つ挙げてください。\n"
        f"【アイデア】\n{idea}\n"
    )
    response = advocate_agent.call({"prompt": prompt, "temperature": 0.5})
    return {"status": "success", "advocacy": response.get("choices", [])[0].get("text", "")}


advocate_agent = Agent(
    name="advocate",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア擁護者エージェント",
    instruction="あなたはこのアイデアの良い点を擁護者として挙げてください。",
    tools=[Tool(name="advocate_idea", func=advocate_idea)]
)