from google.adk.agents import Agent, Tool


def evaluate_ideas(ideas: list) -> dict:
    """Score ideas using a simple heuristic."""
    evaluations = []
    for idea in ideas:
        score = len(idea) % 5 + 1
        comment = f"Auto-evaluated score {score}."
        evaluations.append({"idea": idea, "score": score, "comment": comment})
    return {"status": "success", "evaluations": evaluations}


critic_agent = Agent(
    name="critic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア批評エージェント",
    instruction="提示されたアイデアを1～5のスケールで評価し、簡単な理由を返してください。",
)
critic_agent.add_tools([Tool(name="evaluate_ideas", func=evaluate_ideas)])
