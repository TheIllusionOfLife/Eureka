import os
import json
import re
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai
from .agent_defs.idea_generator import idea_generator_agent
from .agent_defs.critic import critic_agent
from .agent_defs.advocate import advocate_agent
from .agent_defs.skeptic import skeptic_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    logger.info("Google API key configured successfully")
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Please set it to use the system.")


def run_multistep_workflow(theme: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Run phase 1 workflow using proper ADK framework: generate, evaluate, debate."""
    try:
        # 1. Generate ideas using ADK agent invocation
        generation_prompt = build_generation_prompt(theme, constraints)
        gen_response = idea_generator_agent.invoke(generation_prompt)
        
        if not gen_response or not gen_response.content:
            return {"status": "error", "message": "アイデア生成に失敗しました。"}
        
        # Parse ideas from response
        ideas = parse_ideas_from_response(gen_response.content)
        if not ideas:
            return {"status": "error", "message": "生成されたアイデアを解析できませんでした。"}

        # 2. Evaluate ideas using ADK agent invocation
        evaluation_prompt = build_evaluation_prompt(ideas)
        eval_response = critic_agent.invoke(evaluation_prompt)
        
        if not eval_response or not eval_response.content:
            return {"status": "error", "message": "評価に失敗しました。"}
        
        # Parse evaluations from response
        evaluations = parse_evaluations_from_response(eval_response.content, ideas)
        
        # Sort by score and get top candidates
        sorted_by_score = sorted(evaluations, key=lambda x: x["score"], reverse=True)
        top_candidates = sorted_by_score[:3]

        # 3. Get advocacy and criticism using ADK agent invocation
        final_candidates = []
        for candidate in top_candidates:
            idea_text = candidate["idea"]
            
            # Get advocacy using ADK agent
            advocacy_prompt = f"以下のアイデアについて、擁護者としてその良い点・メリットを3つ挙げてください。\n【アイデア】\n{idea_text}"
            adv_response = advocate_agent.invoke(advocacy_prompt)
            
            # Get criticism using ADK agent
            criticism_prompt = f"以下のアイデアについて、懐疑者としてその問題点・リスクを3つ挙げてください。\n【アイデア】\n{idea_text}"
            skp_response = skeptic_agent.invoke(criticism_prompt)

            final_candidates.append({
                "idea": idea_text,
                "score": candidate["score"],
                "critic_comment": candidate["comment"],
                "advocacy": adv_response.content if adv_response else "",
                "criticism": skp_response.content if skp_response else ""
            })

        return {"status": "success", "results": final_candidates}
    except Exception as e:
        return {"status": "error", "message": f"ワークフロー実行エラー: {str(e)}"}


def build_generation_prompt(theme: str, constraints: Dict[str, Any]) -> str:
    """Build prompt for idea generation"""
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

def build_evaluation_prompt(ideas: List[str]) -> str:
    """Build prompt for idea evaluation"""
    ideas_text = "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])
    return (
        f"以下のアイデアを1～5のスケールで評価してください。各アイデアごとにスコアと理由を明記してください。\n"
        f"【アイデア一覧】\n{ideas_text}\n"
        f"・1: 全く面白くない\n"
        f"・5: 非常に面白く独創的\n"
        f"各アイデアについて「アイデア[番号]: スコア[数値]」の形式で始めてください。"
    )

def parse_ideas_from_response(response_text: str) -> List[str]:
    """Parse ideas from LLM response"""
    ideas = []
    if response_text:
        text = response_text.strip()
        idea_matches = re.split(r'\n\s*\d+\.?\s*', text)
        if len(idea_matches) > 1:
            ideas = [idea.strip() for idea in idea_matches[1:] if idea.strip()]
        else:
            idea_matches = re.split(r'\n\s*[•\-\*]\s*', text)
            if len(idea_matches) > 1:
                ideas = [idea.strip() for idea in idea_matches[1:] if idea.strip()]
            else:
                ideas = [idea.strip() for idea in text.split('\n\n') if idea.strip()]
        if not ideas and text:
            ideas = [text]
    return ideas

def parse_evaluations_from_response(response_text: str, ideas: List[str]) -> List[Dict[str, Any]]:
    """Parse evaluations from LLM response"""
    evaluations = []
    if response_text and ideas:
        for i, idea in enumerate(ideas, 1):
            score = 3  # default fallback
            comment = ""
            
            # Look for patterns like "アイデア1: スコア3" or "1. スコア: 4"
            pattern = rf'アイデア{i}[：:]?\s*スコア[：:]?\s*([1-5])'
            score_match = re.search(pattern, response_text)
            if not score_match:
                pattern = rf'{i}\.[^\n]*スコア[：:]?\s*([1-5])'
                score_match = re.search(pattern, response_text)
            
            if score_match:
                score = int(score_match.group(1))
            
            # Extract comment for this idea (rough approximation)
            lines = response_text.split('\n')
            for line in lines:
                if f'アイデア{i}' in line or (f'{i}.' in line and 'スコア' in line):
                    comment = line
                    break
            
            evaluations.append({
                "idea": idea,
                "score": score,
                "comment": comment or response_text[:100] + "..."
            })
    return evaluations

if __name__ == "__main__":
    test_theme = "未来の移動手段"
    test_constraints = {"mode": "逆転", "random_words": ["猫", "宇宙船"]}
    outcome = run_multistep_workflow(test_theme, test_constraints)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
