import os
import json
from agent_defs.idea_generator import idea_generator_agent
from agent_defs.critic import critic_agent
from agent_defs.advocate import advocate_agent
from agent_defs.skeptic import skeptic_agent

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError("GOOGLE_API_KEY is not set")


def run_multistep_workflow(theme: str, constraints: dict) -> dict:
    """Run phase 1 workflow: generate, evaluate, debate."""
    gen_payload = {"theme": theme, "constraints": constraints}
    gen_result = idea_generator_agent.call_tool("generate_ideas", gen_payload)
    if gen_result.get("status") != "success":
        return {"status": "error", "message": "アイデア生成に失敗しました。"}
    ideas = gen_result["ideas"]

    eval_payload = {"ideas": ideas}
    eval_result = critic_agent.call_tool("evaluate_ideas", eval_payload)
    if eval_result.get("status") != "success":
        return {"status": "error", "message": "評価に失敗しました。"}
    evaluations = eval_result["evaluations"]

    sorted_by_score = sorted(evaluations, key=lambda x: x["score"], reverse=True)
    top_candidates = sorted_by_score[:3]

    final_candidates = []
    for candidate in top_candidates:
        idea_text = candidate["idea"]
        adv_res = advocate_agent.call_tool("advocate_idea", {"idea": idea_text})
        skp_res = skeptic_agent.call_tool("criticize_idea", {"idea": idea_text})
        final_candidates.append({
            "idea": idea_text,
            "score": candidate["score"],
            "critic_comment": candidate["comment"],
            "advocacy": adv_res.get("advocacy", ""),
            "criticism": skp_res.get("criticism", "")
        })

    return {"status": "success", "results": final_candidates}


if __name__ == "__main__":
    test_theme = "未来の移動手段"
    test_constraints = {"mode": "逆転", "random_words": ["猫", "宇宙船"]}
    outcome = run_multistep_workflow(test_theme, test_constraints)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
