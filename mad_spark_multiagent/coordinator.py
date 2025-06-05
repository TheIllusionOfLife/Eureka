import os
import json
from agent_defs.idea_generator import idea_generator_agent
from agent_defs.critic import critic_agent
from agent_defs.advocate import advocate_agent
from agent_defs.skeptic import skeptic_agent

# 環境変数から API キーを読み込み
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")


def run_multistep_workflow(theme: str, constraints: dict):
    """
    1) IdeaGeneratorAgent → 2) CriticAgent → 3) Advocate/Skeptic → 最終候補リスト返却
    """
    # 1. アイデア生成
    gen_payload = {"theme": theme, "constraints": constraints}
    gen_result = idea_generator_agent.call_tool("generate_ideas", gen_payload)
    if gen_result.get("status") != "success":
        return {"status": "error", "message": "アイデア生成に失敗しました。"}
    ideas = gen_result["ideas"]  # 生成されたアイデアのリスト

    # 2. 一次評価（CriticAgent）
    eval_payload = {"ideas": ideas}
    eval_result = critic_agent.call_tool("evaluate_ideas", eval_payload)
    if eval_result.get("status") != "success":
        return {"status": "error", "message": "評価に失敗しました。"}
    evaluations = eval_result["evaluations"]

    # 評価スコアでソートし、上位 N 件をピックアップ（例: N=3）
    sorted_by_score = sorted(evaluations, key=lambda x: x["score"], reverse=True)
    top_candidates = sorted_by_score[:3]

    # 3. Advocate / Skeptic の意見を付与
    final_candidates = []
    for candidate in top_candidates:
        idea_text = candidate["idea"]
        # 擁護側の意見
        adv_res = advocate_agent.call_tool("advocate_idea", {"idea": idea_text})
        # 懐疑側の意見
        skp_res = skeptic_agent.call_tool("criticize_idea", {"idea": idea_text})

        final_candidates.append({
            "idea": idea_text,
            "score": candidate["score"],
            "critic_comment": candidate["comment"],
            "advocacy": adv_res.get("advocacy", ""),
            "criticism": skp_res.get("criticism", "")
        })

    # 4. 最終出力を構築して返却
    return {
        "status": "success",
        "results": final_candidates
    }


if __name__ == "__main__":
    # テスト用：コマンドラインからテーマと制約を渡して簡易実行
    test_theme = "未来の移動手段"
    test_constraints = {"mode": "逆転", "random_words": ["猫", "宇宙船"]}
    outcome = run_multistep_workflow(test_theme, test_constraints)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))