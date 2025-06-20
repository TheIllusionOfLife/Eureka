from google.adk.agents import Agent, Tool
import google.generativeai as genai
import re
from typing import Dict, Any, List


def evaluate_ideas(ideas: List[str], temperature: float = 0.3) -> Dict[str, Any]:
    """Evaluate ideas using Gemini API."""
    evaluations = []
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        for idea in ideas:
            prompt = (
                f"以下のアイデアを1～5のスケールで評価してください。スコアと理由を明記してください。\n"
                f"【アイデア】\n{idea}\n"
                f"・1: 全く面白くない\n"
                f"・5: 非常に面白く独創的\n"
                f"スコア: [数値]の形式で始めてください。"
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )
            
            # Extract score from response
            score = 3  # default fallback
            if response.text:
                score_match = re.search(r'スコア:?\s*([1-5])', response.text)
                if score_match:
                    score = int(score_match.group(1))
            
            evaluations.append({
                "idea": idea, 
                "score": score, 
                "comment": response.text if response.text else ""
            })
        return {"status": "success", "evaluations": evaluations}
    except Exception as e:
        return {"status": "error", "message": str(e)}


critic_agent = Agent(
    name="critic",
    model="gemini-2.0-flash",
    description="MadSparkのアイデア批評エージェント",
    instruction="提示されたアイデアを1～5のスケールで評価し、簡単な理由を返してください。",
)
critic_agent.add_tools([Tool(name="evaluate_ideas", func=evaluate_ideas)])
