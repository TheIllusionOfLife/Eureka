from google.adk.agents import Agent, Tool


def build_generation_prompt(theme: str, constraints: dict) -> str:
    """Build prompt for idea generation."""
    base = (
        f"あなたはMadSparkのアイデア生成エージェントです。\n"
        f"ユーザーのテーマ: 「{theme}」\n"
        "以下の制約に従い、突飛で奇抜なアイデアを5件生成してください。\n"
    )
    if constraints.get("mode") == "逆転":
        base += "・逆転の発想で考えてください。\n"
    if random_words := constraints.get("random_words"):
        if len(random_words) >= 2:
            w1, w2 = random_words[:2]
            base += f"・「{w1}」と「{w2}」を必ず組み合わせてください。\n"
        else:
            joined = "、".join(random_words)
            base += f"・以下のキーワードを絡めてください: {joined}\n"
    base += "・ありきたりなアイデアは出さないでください。\n"
    return base


def generate_ideas(theme: str, constraints: dict) -> dict:
    """Generate a few placeholder ideas without calling an LLM."""
    prompt = build_generation_prompt(theme, constraints)
    random_words = constraints.get("random_words", [])
    ideas = []
    for i in range(5):
        idea = f"{theme} idea {i + 1}"
        if random_words:
            idea += f" with {random_words[i % len(random_words)]}"
        ideas.append(idea)
    return {"status": "success", "ideas": ideas}


idea_generator_agent = Agent(
    name="idea_generator",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア生成エージェント",
    instruction="ユーザーから渡されたテーマと制約に基づき、突飛なアイデアを複数生成します。",
)
idea_generator_agent.add_tools([Tool(name="generate_ideas", func=generate_ideas)])
