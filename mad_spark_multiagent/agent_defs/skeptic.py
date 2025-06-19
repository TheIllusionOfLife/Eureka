from google.adk.agents import Agent, Tool
import google.generativeai as genai


def criticize_idea(idea: str, temperature: float = 0.5) -> dict:
    """
    懐疑役として、アイデアの問題点や改善点を3つ挙げる
    """
    try:
        prompt = (
            f"以下のアイデアについて、懐疑者としてその問題点・リスクを3つ挙げてください。\n"
            f"【アイデア】\n{idea}\n"
        )
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        return {"status": "success", "criticism": response.text if response.text else ""}
    except Exception as e:
        return {"status": "error", "message": str(e)}


skeptic_agent = Agent(
    name="skeptic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア懐疑者エージェント",
    instruction="あなたはこのアイデアのリスクや問題点を懐疑的に指摘してください。",
    tools=[Tool(name="criticize_idea", func=criticize_idea)]
)