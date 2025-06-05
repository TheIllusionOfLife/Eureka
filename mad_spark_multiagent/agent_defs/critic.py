from google.adk.agents import Agent, Tool


def evaluate_ideas(ideas: list) -> dict:
    """
    生成されたアイデア群を受け取り、LLM を使って各アイデアのスコア（面白さや独創度）を返す。
    ここではサンプルとして 1～5 のスコア付けを行う想定です。
    """
    evaluations = []
    for idea in ideas:
        prompt = (
            f"以下のアイデアを1～5のスケールで評価してください。\n"
            f"【アイデア】\n{idea}\n"
            f"・1: 全く面白くない\n"
            f"・5: 非常に面白く独創的\n"
            f"それぞれ、理由も簡単に教えてください。"
        )
        response = critic_agent.call({"prompt": prompt, "temperature": 0.3})
        score = 3  # ダミー実装（実際にはレスポンスからパースする）
        evaluations.append({
            "idea": idea, 
            "score": score, 
            "comment": response.get("choices", [{}])[0].get("text", "")
        })
    return {"status": "success", "evaluations": evaluations}


critic_agent = Agent(
    name="critic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア批評エージェント",
    instruction="提示されたアイデアを1～5のスケールで評価し、簡単な理由を返してください。",
    tools=[Tool(name="evaluate_ideas", func=evaluate_ideas)]
)