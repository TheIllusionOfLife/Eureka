import google.generativeai as genai
from typing import Dict, Any

# Optional ADK import for production use
try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    Agent = None


def criticize_idea(idea: str, temperature: float = 0.5) -> Dict[str, Any]:
    """Generate criticism for an idea using Gemini API."""
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


# ADK agent setup (optional, for production use)
if ADK_AVAILABLE:
    skeptic_agent = Agent(
        name="skeptic",
        model="gemini-2.0-flash",
        description="MadSparkのアイデア懐疑者エージェント",
        instruction="あなたはこのアイデアのリスクや問題点を懐疑的に指摘してください。",
    )
else:
    skeptic_agent = None
