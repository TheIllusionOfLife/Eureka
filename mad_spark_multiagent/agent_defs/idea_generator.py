import google.generativeai as genai
import re
from typing import Dict, Any

# Optional ADK import for production use
try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    Agent = None


def build_generation_prompt(theme: str, constraints: Dict[str, Any]) -> str:
    """Build prompt for idea generation."""
    base = (
        f"あなたはMadSparkのアイデア生成エージェントです。\n"
        f"ユーザーのテーマ: 「{theme}」\n"
        "以下の制約に従い、突飛で奇抜なアイデアを5件生成してください。\n"
        "必ず番号付きリスト形式（1. 2. 3. 4. 5.）で出力してください。\n"
    )
    if constraints.get("mode") == "逆転":
        base += "・逆転の発想で考えてください。\n"
    if random_words := constraints.get("random_words"):
        if random_words and len(random_words) >= 2:
            w1, w2 = random_words[:2]
            base += f"・「{w1}」と「{w2}」を必ず組み合わせてください。\n"
        elif random_words:
            joined = "、".join(random_words)
            base += f"・以下のキーワードを絡めてください: {joined}\n"
    base += "・ありきたりなアイデアは出さないでください。\n"
    return base


def generate_ideas(theme: str, constraints: Dict[str, Any], temperature: float = 0.9) -> Dict[str, Any]:
    """Generate ideas using Gemini API."""
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


# ADK agent setup (optional, for production use)
if ADK_AVAILABLE:
    import os
    
    # Configure API key for ADK if available
    api_key = os.getenv("GOOGLE_API_KEY")
    generate_content_config = None
    if api_key:
        # Configure genai to make API key available to ADK
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        generate_content_config = genai.types.GenerationConfig(temperature=0.9)
    
    idea_generator_agent = Agent(
        name="idea_generator",
        model="gemini-2.0-flash",
        description="MadSparkのアイデア生成エージェント",
        instruction="ユーザーから渡されたテーマと制約に基づき、突飛なアイデアを複数生成します。",
        generate_content_config=generate_content_config
    )
    # Note: Tool class not available in current ADK version
    # Function can be called directly instead
else:
    idea_generator_agent = None
