from google.adk.agents import Agent, Tool
import os


def build_generation_prompt(theme: str, constraints: dict) -> str:
    """
    MadSpark の「暴走」プロンプトを組み立てる関数。
    constraints にはたとえば {'mode': '逆転発想', 'random_words': [...]} のような情報が入る想定。
    """
    base = (
        f"あなたはMadSparkのアイデア生成エージェントです。\n"
        f"ユーザーのテーマ: 「{theme}」\n"
        f"以下の制約に従い、突飛で奇抜なアイデアを5件生成してください。\n"
    )
    if constraints.get("mode") == "逆転":
        base += "・逆転の発想で考えてください。\n"
    if random_words := constraints.get("random_words"):
        w1, w2 = random_words
        base += f"・「{w1}」と「{w2}」を必ず組み合わせてください。\n"
    base += "・ありきたりなアイデアは出さないでください。\n"
    return base


def generate_ideas(theme: str, constraints: dict) -> dict:
    """
    Gemini API を呼び出して実際にアイデアを生成するツール関数。
    """
    prompt = build_generation_prompt(theme, constraints)
    response = idea_generator_agent.call({"prompt": prompt, "temperature": 0.9})
    return {"status": "success", "ideas": response.get("choices", [])}


idea_generator_agent = Agent(
    name="idea_generator",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア生成エージェント",
    instruction="ユーザーから渡されたテーマと制約に基づき、突飛なアイデアを複数生成します。",
    tools=[Tool(name="generate_ideas", func=generate_ideas)]
)