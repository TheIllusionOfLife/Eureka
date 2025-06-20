from google.adk.agents import Agent, Tool
import google.generativeai as genai
from typing import Dict, Any


def advocate_idea(idea: str, temperature: float = 0.5) -> Dict[str, Any]:
    """Generate advocacy for an idea using Gemini API."""
    try:
        prompt = (
            f"以下のアイデアについて、擁護者としてその良い点・メリットを3つ挙げてください。\n"
            f"【アイデア】\n{idea}\n"
        )
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        return {"status": "success", "advocacy": response.text if response.text else ""}
    except Exception as e:
        return {"status": "error", "message": str(e)}


advocate_agent = Agent(
    name="advocate",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア擁護者エージェント",
    instruction="あなたはこのアイデアの良い点を擁護者として挙げてください。",
)
advocate_agent.add_tools([Tool(name="advocate_idea", func=advocate_idea)])
