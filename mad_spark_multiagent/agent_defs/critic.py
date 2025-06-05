from google.adk.agents import Agent, Tool


def evaluate_ideas(ideas: list) -> dict:
    """Evaluate ideas with a simple score."""
    evaluations = []
    for idea in ideas:
        prompt = (
            f"以下のアイデアを1～5のスケールで評価してください。\n"
            f"【アイデア】\n{idea}\n"
            "・1: 全く面白くない\n"
            "・5: 非常に面白く独創的\n"
            "それぞれ、理由も簡単に教えてください。"
        )
        response = critic_agent.call({"prompt": prompt, "temperature": 0.3})
        score = 3  # Dummy implementation
        comment = response.get("choices", [{}])[0].get("text", "")
        evaluations.append({"idea": idea, "score": score, "comment": comment})
    return {"status": "success", "evaluations": evaluations}


critic_agent = Agent(
    name="critic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア批評エージェント",
    instruction="提示されたアイデアを1～5のスケールで評価し、簡単な理由を返してください。",
    tools=[Tool(name="evaluate_ideas", func=evaluate_ideas)]
)
