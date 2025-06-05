from google.adk.agents import Agent, Tool


def criticize_idea(idea: str) -> dict:
    """Point out problems or risks of the idea."""
    prompt = (
        f"以下のアイデアについて、懐疑者としてその問題点・リスクを3つ挙げてください。\n"
        f"【アイデア】\n{idea}\n"
    )
    response = skeptic_agent.call({"prompt": prompt, "temperature": 0.5})
    text = response.get("choices", [{}])[0].get("text", "")
    return {"status": "success", "criticism": text}


skeptic_agent = Agent(
    name="skeptic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア懐疑者エージェント",
    instruction="あなたはこのアイデアのリスクや問題点を懐疑的に指摘してください。",
    tools=[Tool(name="criticize_idea", func=criticize_idea)]
)
