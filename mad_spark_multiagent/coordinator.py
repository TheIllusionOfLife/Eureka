import os
import json
import re
import logging
import uuid
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai
from agent_defs import idea_generator_agent, critic_agent, advocate_agent, skeptic_agent
from agent_defs.idea_generator import generate_ideas
from agent_defs.critic import evaluate_ideas
from agent_defs.advocate import advocate_idea
from agent_defs.skeptic import criticize_idea

# ADK imports for the correct method
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content
    from google.adk.auth import AuthCredential, AuthCredentialTypes
    ADK_RUNNER_AVAILABLE = True
except ImportError:
    ADK_RUNNER_AVAILABLE = False
    Runner = None
    InMemorySessionService = None
    Content = None
    AuthCredential = None
    AuthCredentialTypes = None

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


def run_multistep_workflow(theme: str, constraints: Dict[str, Any], temperature: float = 0.7, use_adk: bool = True, mock_mode: bool = False) -> Dict[str, Any]:
    """Run phase 1 workflow with hybrid approach: ADK agents or direct function calls."""
    try:
        if mock_mode:
            return _run_workflow_mock(theme, constraints, temperature)
        elif use_adk:
            return _run_workflow_with_adk(theme, constraints, temperature)
        else:
            return _run_workflow_direct(theme, constraints, temperature)
    except Exception as e:
        return {"status": "error", "message": f"ワークフロー実行エラー: {str(e)}"}


def _run_workflow_with_adk(theme: str, constraints: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    """Run workflow using ADK Runner (correct ADK approach)."""
    if not ADK_RUNNER_AVAILABLE:
        return {"status": "error", "message": "ADK Runner not available. Install google-adk."}
    
    try:
        # Create session service and runners for each agent
        session_service = InMemorySessionService()
        
        # Create runners for each agent
        idea_runner = Runner(
            app_name="madspark_idea",
            agent=idea_generator_agent,
            session_service=session_service
        )
        
        critic_runner = Runner(
            app_name="madspark_critic",
            agent=critic_agent,
            session_service=session_service
        )
        
        advocate_runner = Runner(
            app_name="madspark_advocate",
            agent=advocate_agent,
            session_service=session_service
        )
        
        skeptic_runner = Runner(
            app_name="madspark_skeptic",
            agent=skeptic_agent,
            session_service=session_service
        )
        
        # 1. Generate ideas using ADK Runner
        generation_prompt = build_generation_prompt(theme, constraints)
        gen_response_text = _run_adk_agent(idea_runner, generation_prompt)
        
        if not gen_response_text or gen_response_text.startswith("ERROR:"):
            error_msg = gen_response_text if gen_response_text.startswith("ERROR:") else "Empty response from ADK agent"
            return {"status": "error", "message": f"アイデア生成に失敗しました: {error_msg}"}
        
        # Parse ideas from response
        ideas = parse_ideas_from_response(gen_response_text)
        if not ideas:
            return {"status": "error", "message": "生成されたアイデアを解析できませんでした。"}

        # 2. Evaluate ideas using ADK Runner
        evaluation_prompt = build_evaluation_prompt(ideas)
        eval_response_text = _run_adk_agent(critic_runner, evaluation_prompt)
        
        if not eval_response_text:
            return {"status": "error", "message": "評価に失敗しました。"}
        
        # Parse evaluations from response
        evaluations = parse_evaluations_from_response(eval_response_text, ideas)
        
        # Sort by score and get top candidates
        sorted_by_score = sorted(evaluations, key=lambda x: x["score"], reverse=True)
        top_candidates = sorted_by_score[:3]

        # 3. Get advocacy and criticism using ADK Runner
        final_candidates = []
        for candidate in top_candidates:
            idea_text = candidate["idea"]
            
            # Get advocacy using ADK Runner
            advocacy_prompt = f"以下のアイデアについて、擁護者としてその良い点・メリットを3つ挙げてください。\n【アイデア】\n{idea_text}"
            advocacy_text = _run_adk_agent(advocate_runner, advocacy_prompt)
            
            # Get criticism using ADK Runner
            criticism_prompt = f"以下のアイデアについて、懐疑者としてその問題点・リスクを3つ挙げてください。\n【アイデア】\n{idea_text}"
            criticism_text = _run_adk_agent(skeptic_runner, criticism_prompt)

            final_candidates.append({
                "idea": idea_text,
                "score": candidate["score"],
                "critic_comment": candidate["comment"],
                "advocacy": advocacy_text or "",
                "criticism": criticism_text or ""
            })

        return {"status": "success", "results": final_candidates}
        
    except Exception as e:
        return {"status": "error", "message": f"ADK実行エラー: {str(e)}"}


def _run_workflow_mock(theme: str, constraints: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    """Run workflow with mock responses for testing without API costs."""
    # Generate mock ideas based on theme
    mock_ideas = [
        f"{theme}のための革新的なアイデア1: 逆転の発想を活用",
        f"{theme}に関する創造的なアイデア2: 新しい技術の組み合わせ", 
        f"{theme}向けの斬新なアイデア3: 既存概念の再構築",
        f"{theme}のための未来的なアイデア4: 持続可能性を重視",
        f"{theme}に対する画期的なアイデア5: ユーザー体験の向上"
    ]
    
    # Mock evaluations with random scores
    import random
    evaluations = []
    for i, idea in enumerate(mock_ideas):
        score = random.randint(3, 5)  # Realistic scores
        evaluations.append({
            "idea": idea,
            "score": score,
            "comment": f"アイデア{i+1}: スコア{score} - {'創造性が高い' if score >= 4 else '実用性がある'}"
        })
    
    # Sort by score and get top 3
    sorted_evaluations = sorted(evaluations, key=lambda x: x["score"], reverse=True)
    top_candidates = sorted_evaluations[:3]
    
    # Add mock advocacy and criticism
    final_candidates = []
    for candidate in top_candidates:
        final_candidates.append({
            "idea": candidate["idea"],
            "score": candidate["score"],
            "critic_comment": candidate["comment"],
            "advocacy": "このアイデアは実装可能性が高く、ユーザーにとって価値のある解決策を提供します。",
            "criticism": "技術的な実装コストと市場での受容性について詳細な検討が必要です。"
        })
    
    return {"status": "success", "results": final_candidates}


def _run_adk_agent(runner, prompt: str) -> str:
    """Helper function to run ADK agent and extract text response."""
    try:
        # Create unique session for this call
        session_id = str(uuid.uuid4())
        user_id = "madspark_user"
        
        logger.info(f"Creating ADK session: {session_id}")
        
        # Try different session creation methods
        session = None
        try:
            # Method 1: Try sync session creation
            session = runner.session_service.create_session_sync(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
        except AttributeError as e1:
            logger.warning(f"create_session_sync not available: {e1}")
            try:
                # Method 2: Try regular session creation
                session = runner.session_service.create_session(
                    app_name=runner.app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            except Exception as e2:
                logger.error(f"Session creation failed with both methods: {e1}, {e2}")
                return f"ERROR: Session creation failed - {e2}"
        
        # Create content object with different approaches
        content = None
        try:
            # Method 1: Standard Content structure
            content = Content(parts=[{"text": prompt}])
        except Exception as e1:
            try:
                # Method 2: Simple text content
                content = Content(text=prompt)
            except Exception as e2:
                logger.error(f"Content creation failed: {e1}, {e2}")
                return f"ERROR: Content creation failed - {e2}"
        
        logger.info(f"Running ADK agent with prompt length: {len(prompt)}")
        
        # Run the agent
        result = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )
        
        # Collect response text with detailed logging
        response_text = ""
        event_count = 0
        for event in result:
            event_count += 1
            logger.debug(f"Processing event {event_count}: {type(event)}")
            
            if hasattr(event, 'content') and event.content:
                response_text += str(event.content)
            elif hasattr(event, 'text') and event.text:
                response_text += str(event.text)
            elif hasattr(event, 'delta') and event.delta:
                response_text += str(event.delta)
            elif hasattr(event, 'data') and event.data:
                response_text += str(event.data)
            else:
                logger.debug(f"Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
        
        logger.info(f"Processed {event_count} events, response length: {len(response_text)}")
        
        if not response_text.strip():
            return "ERROR: No response text extracted from ADK agent"
        
        return response_text.strip()
    
    except Exception as e:
        logger.error(f"ADK agent execution failed: {type(e).__name__}: {e}")
        return f"ERROR: ADK execution failed - {e}"


def _run_workflow_direct(theme: str, constraints: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    """Run workflow using direct function calls (PR #44 approach)."""
    # 1. Generate ideas using direct function call
    gen_result = generate_ideas(theme, constraints, temperature)
    
    if gen_result["status"] != "success" or not gen_result.get("ideas"):
        return {"status": "error", "message": "アイデア生成に失敗しました。"}
    
    ideas = gen_result["ideas"]

    # 2. Evaluate ideas using direct function call
    eval_result = evaluate_ideas(ideas, temperature=0.3)
    
    if eval_result["status"] != "success" or not eval_result.get("evaluations"):
        return {"status": "error", "message": "評価に失敗しました。"}
    
    evaluations = eval_result["evaluations"]
    
    # Sort by score and get top candidates
    sorted_by_score = sorted(evaluations, key=lambda x: x["score"], reverse=True)
    top_candidates = sorted_by_score[:3]

    # 3. Get advocacy and criticism using direct function calls
    final_candidates = []
    for candidate in top_candidates:
        idea_text = candidate["idea"]
        
        # Get advocacy using direct function call
        adv_result = advocate_idea(idea_text, temperature=0.5)
        advocacy_text = adv_result.get("advocacy", "") if adv_result["status"] == "success" else ""
        
        # Get criticism using direct function call
        crit_result = criticize_idea(idea_text, temperature=0.5)
        criticism_text = crit_result.get("criticism", "") if crit_result["status"] == "success" else ""

        final_candidates.append({
            "idea": idea_text,
            "score": candidate["score"],
            "critic_comment": candidate["comment"],
            "advocacy": advocacy_text,
            "criticism": criticism_text
        })

    return {"status": "success", "results": final_candidates}


def build_generation_prompt(theme: str, constraints: Dict[str, Any]) -> str:
    """Build prompt for idea generation (from PR #42)."""
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


def build_evaluation_prompt(ideas: List[str]) -> str:
    """Build prompt for idea evaluation (from PR #42)."""
    ideas_text = "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])
    return (
        f"以下のアイデアを1～5のスケールで評価してください。各アイデアごとにスコアと理由を明記してください。\n"
        f"【アイデア一覧】\n{ideas_text}\n"
        f"・1: 全く面白くない\n"
        f"・5: 非常に面白く独創的\n"
        f"各アイデアについて「アイデア[番号]: スコア[数値]」の形式で始めてください。"
    )


def parse_ideas_from_response(response_text: str) -> List[str]:
    """Parse ideas from LLM response (from PR #42)."""
    ideas = []
    if response_text:
        text = response_text.strip()
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
    return ideas


def parse_evaluations_from_response(response_text: str, ideas: List[str]) -> List[Dict[str, Any]]:
    """Parse evaluations from LLM response (from PR #42)."""
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
    
    print("Testing hybrid approach...")
    
    # Test mock mode first (no API costs)
    print("\n=== Mock Mode (No API costs) ===")
    outcome_mock = run_multistep_workflow(test_theme, test_constraints, temperature=0.8, mock_mode=True)
    print(json.dumps(outcome_mock, ensure_ascii=False, indent=2))
    
    # Only test API modes if mock mode works
    if outcome_mock["status"] == "success":
        print("\n=== ADK Approach (PR #42 style) ===")
        outcome_adk = run_multistep_workflow(test_theme, test_constraints, temperature=0.8, use_adk=True)
        print(json.dumps(outcome_adk, ensure_ascii=False, indent=2))
        
        print("\n=== Direct Function Approach (PR #44 style) ===")
        outcome_direct = run_multistep_workflow(test_theme, test_constraints, temperature=0.8, use_adk=False)
        print(json.dumps(outcome_direct, ensure_ascii=False, indent=2))
    else:
        print("Mock mode failed, skipping API tests")
