from google.adk.agents import Agent, Tool
import os
import re
import google.generativeai as genai


def build_generation_prompt(theme: str, constraints: dict) -> str:
    """
    MadSpark の「暴走」プロンプトを組み立てる関数。
    constraints にはたとえば {'mode': '逆転発想', 'random_words': [...]} のような情報が入る想定。
    """
    base = (
        f"あなたはMadSparkのアイデア生成エージェントです。\n"
        f"ユーザーのテーマ: 「{theme}」\n"
        f"以下の制約に従い、突飛で奇抜なアイデアを5件生成してください。\n"
        f"必ず番号付きリスト形式（1. 2. 3. 4. 5.）で出力してください。\n"
    )
    if constraints.get("mode") == "逆転":
        base += "・逆転の発想で考えてください。\n"
    if random_words := constraints.get("random_words"):
        if random_words and len(random_words) >= 2:
            w1, w2 = random_words[:2]
            base += f"・「{w1}」と「{w2}」を必ず組み合わせてください。\n"
    base += "・ありきたりなアイデアは出さないでください。\n"
    return base


def generate_ideas(theme: str, constraints: dict, temperature: float = 0.9) -> dict:
    """
    Gemini API を呼び出して実際にアイデアを生成するツール関数。
    """
    try:
        prompt = build_generation_prompt(theme, constraints)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        # Parse response text into individual ideas
        ideas = []
        if response.text:
            # Split response by numbered items or bullet points
            text = response.text.strip()
            # Try to split by numbered patterns like "1.", "2.", etc.
            idea_matches = re.split(r'\n\s*\d+\.?\s*', text)
            if len(idea_matches) > 1:
                # Remove empty first element if it exists
                ideas = [idea.strip() for idea in idea_matches[1:] if idea.strip()]
            else:
                # Fallback: split by bullet points or newlines
                idea_matches = re.split(r'\n\s*[•\-\*]\s*', text)
                if len(idea_matches) > 1:
                    ideas = [idea.strip() for idea in idea_matches[1:] if idea.strip()]
                else:
                    # Last fallback: split by double newlines
                    ideas = [idea.strip() for idea in text.split('\n\n') if idea.strip()]
            
            # Ensure we have at least one idea
            if not ideas and text:
                ideas = [text]
        
        return {"status": "success", "ideas": ideas}
    except Exception as e:
        return {"status": "error", "message": str(e)}


idea_generator_agent = Agent(
    name="idea_generator",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア生成エージェント",
    instruction="ユーザーから渡されたテーマと制約に基づき、突飛なアイデアを複数生成します。",
    tools=[Tool(name="generate_ideas", func=generate_ideas)]
)