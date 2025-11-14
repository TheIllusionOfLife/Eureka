#!/usr/bin/env python3
"""
Integration test script for Phase 2 Pydantic Schema Migration.

This script tests the complete workflow with real Gemini API to verify:
1. All migrated agents work correctly with actual API
2. Structured output schemas validate properly
3. No timeout/truncation/format issues
4. Complete workflow from generation through improvement

Requirements:
- GOOGLE_API_KEY environment variable must be set
- Run from project root: PYTHONPATH=src python scripts/test_phase2_integration.py

Usage:
    export GOOGLE_API_KEY=your_api_key_here
    PYTHONPATH=src python scripts/test_phase2_integration.py
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_api_key() -> bool:
    """Check if GOOGLE_API_KEY is configured."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        logger.error("Please set it: export GOOGLE_API_KEY=your_api_key")
        return False
    logger.info("✓ API key configured")
    return True


def test_idea_generation() -> Dict[str, Any]:
    """Test idea generation with real API using Pydantic GeneratedIdeas schema."""
    logger.info("\n=== Testing Idea Generation ===")

    from madspark.agents.idea_generator import generate_ideas

    topic = "sustainable urban agriculture solutions"
    context = "Focus on rooftop gardens and vertical farming with limited budget"

    logger.info(f"Topic: {topic}")
    logger.info(f"Context: {context}")

    try:
        # Generate ideas with structured output (uses Pydantic schema)
        result = generate_ideas(
            topic=topic,
            context=context,
            temperature=0.9,
            use_structured_output=True
        )

        # Parse JSON response
        ideas = json.loads(result)

        # Validate structure
        assert isinstance(ideas, list), "Result should be a list"
        assert len(ideas) > 0, "Should generate at least one idea"

        logger.info(f"✓ Generated {len(ideas)} ideas")

        # Validate each idea has required Pydantic fields
        for i, idea in enumerate(ideas, 1):
            assert 'idea_number' in idea, f"Idea {i} missing idea_number"
            assert 'title' in idea, f"Idea {i} missing title"
            assert 'description' in idea, f"Idea {i} missing description"
            logger.info(f"  {i}. {idea['title']}")

        logger.info("✓ All ideas have valid Pydantic schema structure")
        return {"success": True, "ideas": ideas}

    except json.JSONDecodeError as e:
        logger.error(f"✗ JSON parsing failed: {e}")
        return {"success": False, "error": str(e)}
    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Idea generation failed: {e}")
        return {"success": False, "error": str(e)}


def test_critic_evaluation(idea: str) -> Dict[str, Any]:
    """Test critic evaluation with real API using Pydantic CriticEvaluations schema."""
    logger.info("\n=== Testing Critic Evaluation ===")

    from madspark.utils.agent_retry_wrappers import call_critic_with_retry
    import json

    topic = "sustainable urban agriculture"
    context = "rooftop gardens with limited budget"

    try:
        # Evaluate with Pydantic schema (call_critic_with_retry uses evaluate_ideas)
        result_text = call_critic_with_retry(
            ideas=idea,
            topic=topic,
            context=context,
            temperature=0.7
        )

        # Parse JSON response
        evaluations = json.loads(result_text)

        assert isinstance(evaluations, list), "Result should be a list"
        assert len(evaluations) > 0, "Should return at least one evaluation"

        evaluation = evaluations[0]

        # Validate Pydantic schema fields
        assert 'score' in evaluation, "Missing score field"
        assert 'comment' in evaluation, "Missing comment field"
        assert isinstance(evaluation['score'], (int, float)), "Score should be numeric"
        assert 0 <= evaluation['score'] <= 10, "Score should be 0-10"

        logger.info(f"✓ Score: {evaluation['score']}/10")
        logger.info(f"✓ Comment: {evaluation['comment'][:100]}...")

        return {"success": True, "evaluation": evaluation, "token_count": 0}

    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Critic evaluation failed: {e}")
        return {"success": False, "error": str(e)}


def test_advocate(idea: str, evaluation: str) -> Dict[str, Any]:
    """Test advocate agent with real API using Pydantic AdvocacyResponse schema."""
    logger.info("\n=== Testing Advocate Agent ===")

    from madspark.agents.advocate import advocate_ideas_batch

    topic = "sustainable urban agriculture"
    context = "rooftop gardens with limited budget"

    try:
        # Advocate with Pydantic schema
        results, token_count = advocate_ideas_batch(
            ideas_with_evaluations=[{"idea": idea, "evaluation": evaluation}],
            topic=topic,
            context=context,
            temperature=0.5
        )

        assert len(results) == 1, "Should return one advocacy"
        advocacy = results[0]

        # Validate Pydantic AdvocacyResponse fields
        assert 'strengths' in advocacy, "Missing strengths field"
        assert 'opportunities' in advocacy, "Missing opportunities field"
        assert 'addressing_concerns' in advocacy, "Missing addressing_concerns field"
        assert 'formatted' in advocacy, "Missing formatted field"

        assert isinstance(advocacy['strengths'], list), "Strengths should be a list"
        assert len(advocacy['strengths']) > 0, "Should have at least one strength"

        logger.info(f"✓ Strengths: {len(advocacy['strengths'])} items")
        logger.info(f"✓ Opportunities: {len(advocacy['opportunities'])} items")
        logger.info(f"✓ Concerns addressed: {len(advocacy['addressing_concerns'])} items")
        logger.info(f"✓ Token count: {token_count}")

        return {"success": True, "advocacy": advocacy, "token_count": token_count}

    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Advocate failed: {e}")
        return {"success": False, "error": str(e)}


def test_skeptic(idea: str, advocacy: str) -> Dict[str, Any]:
    """Test skeptic agent with real API using Pydantic SkepticismResponse schema."""
    logger.info("\n=== Testing Skeptic Agent ===")

    from madspark.agents.skeptic import criticize_ideas_batch

    topic = "sustainable urban agriculture"
    context = "rooftop gardens with limited budget"

    try:
        # Criticize with Pydantic schema
        results, token_count = criticize_ideas_batch(
            ideas_with_advocacies=[{"idea": idea, "advocacy": advocacy}],
            topic=topic,
            context=context,
            temperature=0.5
        )

        assert len(results) == 1, "Should return one skepticism"
        skepticism = results[0]

        # Validate Pydantic SkepticismResponse fields
        assert 'critical_flaws' in skepticism, "Missing critical_flaws field"
        assert 'risks_challenges' in skepticism, "Missing risks_challenges field"
        assert 'questionable_assumptions' in skepticism, "Missing questionable_assumptions field"
        assert 'missing_considerations' in skepticism, "Missing missing_considerations field"
        assert 'formatted' in skepticism, "Missing formatted field"

        assert isinstance(skepticism['critical_flaws'], list), "Flaws should be a list"

        logger.info(f"✓ Critical flaws: {len(skepticism['critical_flaws'])} items")
        logger.info(f"✓ Risks & challenges: {len(skepticism['risks_challenges'])} items")
        logger.info(f"✓ Questionable assumptions: {len(skepticism['questionable_assumptions'])} items")
        logger.info(f"✓ Missing considerations: {len(skepticism['missing_considerations'])} items")
        logger.info(f"✓ Token count: {token_count}")

        return {"success": True, "skepticism": skepticism, "token_count": token_count}

    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Skeptic failed: {e}")
        return {"success": False, "error": str(e)}


def test_logical_inference(idea: str) -> Dict[str, Any]:
    """Test logical inference with real API using Pydantic InferenceResult schema."""
    logger.info("\n=== Testing Logical Inference ===")

    from madspark.utils.logical_inference_engine import LogicalInferenceEngine
    from madspark.agents.genai_client import get_genai_client

    topic = "sustainable urban agriculture"
    context = "rooftop gardens with limited budget"

    try:
        client = get_genai_client()
        engine = LogicalInferenceEngine(client)

        # Test causal analysis with Pydantic schema
        result = engine.analyze(
            idea=idea,
            topic=topic,
            context=context,
            analysis_type="causal"
        )

        # Validate Pydantic InferenceResult fields
        assert hasattr(result, 'inference_chain') or 'inference_chain' in result.__dict__, "Missing inference_chain"
        assert hasattr(result, 'conclusion') or 'conclusion' in result.__dict__, "Missing conclusion"
        assert hasattr(result, 'confidence') or 'confidence' in result.__dict__, "Missing confidence"

        logger.info(f"✓ Inference steps: {len(result.inference_chain) if hasattr(result, 'inference_chain') else 'N/A'}")
        logger.info(f"✓ Conclusion: {result.conclusion[:100] if hasattr(result, 'conclusion') else 'N/A'}...")
        logger.info(f"✓ Confidence: {result.confidence if hasattr(result, 'confidence') else 'N/A'}")

        return {"success": True, "inference": result}

    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Logical inference failed: {e}")
        return {"success": False, "error": str(e)}


def test_improvement(idea: str, critique: str, advocacy: str, skepticism: str) -> Dict[str, Any]:
    """Test idea improvement with real API using Pydantic ImprovementResponse schema."""
    logger.info("\n=== Testing Idea Improvement ===")

    from madspark.agents.idea_generator import improve_idea

    topic = "sustainable urban agriculture"
    context = "rooftop gardens with limited budget"

    try:
        # Improve with Pydantic schema (delegates to structured_idea_generator)
        improved = improve_idea(
            original_idea=idea,
            critique=critique,
            advocacy_points=advocacy,
            skeptic_points=skepticism,
            topic=topic,
            context=context,
            temperature=0.9
        )

        # Validate result is non-empty and meaningful
        assert improved, "Improved idea should not be empty"
        assert len(improved) > 50, "Improved idea should be substantial"
        assert not improved.startswith("Mock"), "Should not be mock response"

        # Check for title/description concatenation (new Pydantic schema format)
        has_structure = "\n\n" in improved or len(improved.split('\n')) > 1

        logger.info(f"✓ Improved idea length: {len(improved)} characters")
        logger.info(f"✓ Has structure: {has_structure}")
        logger.info(f"✓ Preview: {improved[:150]}...")

        return {"success": True, "improved_idea": improved}

    except AssertionError as e:
        logger.error(f"✗ Validation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"✗ Improvement failed: {e}")
        return {"success": False, "error": str(e)}


def run_integration_tests() -> bool:
    """Run complete integration test workflow."""
    logger.info("=" * 70)
    logger.info("Phase 2 Pydantic Schema Integration Testing")
    logger.info("=" * 70)

    # Check API key
    if not check_api_key():
        return False

    all_passed = True
    total_tokens = 0

    # Test 1: Idea Generation
    gen_result = test_idea_generation()
    if not gen_result["success"]:
        logger.error("✗ Idea generation failed - stopping tests")
        return False

    # Use first generated idea for remaining tests
    test_idea = gen_result["ideas"][0]
    idea_text = f"{test_idea['title']}: {test_idea['description']}"

    # Test 2: Critic Evaluation
    eval_result = test_critic_evaluation(idea_text)
    if eval_result["success"]:
        total_tokens += eval_result.get("token_count", 0)
    else:
        all_passed = False

    # Test 3: Advocate
    if eval_result["success"]:
        adv_result = test_advocate(
            idea_text,
            eval_result["evaluation"]["comment"]
        )
        if adv_result["success"]:
            total_tokens += adv_result.get("token_count", 0)
        else:
            all_passed = False

    # Test 4: Skeptic
    if eval_result["success"] and adv_result["success"]:
        skep_result = test_skeptic(
            idea_text,
            adv_result["advocacy"]["formatted"]
        )
        if skep_result["success"]:
            total_tokens += skep_result.get("token_count", 0)
        else:
            all_passed = False

    # Test 5: Logical Inference
    infer_result = test_logical_inference(idea_text)
    if not infer_result["success"]:
        all_passed = False

    # Test 6: Improvement
    if all([eval_result["success"], adv_result["success"], skep_result["success"]]):
        improve_result = test_improvement(
            idea_text,
            eval_result["evaluation"]["comment"],
            adv_result["advocacy"]["formatted"],
            skep_result["skepticism"]["formatted"]
        )
        if not improve_result["success"]:
            all_passed = False

    # Summary
    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ ALL INTEGRATION TESTS PASSED")
    else:
        logger.info("✗ SOME INTEGRATION TESTS FAILED")
    logger.info(f"Total tokens used: ~{total_tokens}")
    logger.info("=" * 70)

    return all_passed


if __name__ == "__main__":
    try:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
