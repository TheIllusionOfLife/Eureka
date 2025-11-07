#!/usr/bin/env python3
"""Manual test script for WorkflowOrchestrator with real API.

This script tests the WorkflowOrchestrator directly with a real API key.
Run with: PYTHONPATH=src python tests/manual_test_orchestrator.py
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure PYTHONPATH includes src
# ruff: noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.workflow_orchestrator import WorkflowOrchestrator  # noqa: E402
from madspark.utils.temperature_control import TemperatureManager  # noqa: E402


def test_basic_workflow():
    """Test basic workflow with minimal configuration."""
    print("\n" + "="*60)
    print("TEST 1: Basic Workflow")
    print("="*60)

    # Create orchestrator
    temp_manager = TemperatureManager.from_base_temperature(0.7)
    orchestrator = WorkflowOrchestrator(
        temperature_manager=temp_manager,
        verbose=True
    )

    topic = "AI-powered productivity tools"
    context = "Focus on tools that help developers code faster"

    # Step 1: Generate ideas
    print("\n📝 Generating ideas...")
    ideas, tokens1 = orchestrator.generate_ideas(topic, context, num_ideas=3)
    print(f"✅ Generated {len(ideas)} ideas (tokens: {tokens1})")
    for i, idea in enumerate(ideas, 1):
        print(f"   {i}. {idea[:80]}...")

    # Step 2: Evaluate ideas
    print("\n📊 Evaluating ideas...")
    evaluated, tokens2 = orchestrator.evaluate_ideas(ideas, topic, context)
    print(f"✅ Evaluated {len(evaluated)} ideas (tokens: {tokens2})")
    for i, ev in enumerate(evaluated, 1):
        print(f"   {i}. Score: {ev['score']}, Critique: {ev['critique'][:60]}...")

    # Sort and select top 2
    evaluated.sort(key=lambda x: x['score'], reverse=True)
    top_candidates = evaluated[:2]

    # Convert to candidate format
    candidates = [
        {
            "idea": ev["text"],
            "initial_score": float(ev["score"]),
            "initial_critique": ev["critique"],
            "multi_dimensional_evaluation": None
        }
        for ev in top_candidates
    ]

    # Step 3: Process advocacy
    print("\n👥 Processing advocacy...")
    candidates, tokens3 = orchestrator.process_advocacy(candidates, topic, context)
    print(f"✅ Advocacy complete (tokens: {tokens3})")
    for i, cand in enumerate(candidates, 1):
        print(f"   {i}. Advocacy: {cand['advocacy'][:60]}...")

    # Step 4: Process skepticism
    print("\n🔍 Processing skepticism...")
    candidates, tokens4 = orchestrator.process_skepticism(candidates, topic, context)
    print(f"✅ Skepticism complete (tokens: {tokens4})")
    for i, cand in enumerate(candidates, 1):
        print(f"   {i}. Skepticism: {cand['skepticism'][:60]}...")

    # Step 5: Improve ideas
    print("\n💡 Improving ideas...")
    candidates, tokens5 = orchestrator.improve_ideas(candidates, topic, context)
    print(f"✅ Improvement complete (tokens: {tokens5})")
    for i, cand in enumerate(candidates, 1):
        print(f"   {i}. Improved: {cand['improved_idea'][:60]}...")

    # Step 6: Re-evaluate
    print("\n📊 Re-evaluating improved ideas...")
    candidates, tokens6 = orchestrator.reevaluate_ideas(candidates, topic, context)
    print(f"✅ Re-evaluation complete (tokens: {tokens6})")
    for i, cand in enumerate(candidates, 1):
        print(f"   {i}. New Score: {cand['improved_score']}, Critique: {cand['improved_critique'][:60]}...")

    # Step 7: Build final results
    print("\n🎯 Building final results...")
    final_results = orchestrator.build_final_results(candidates)
    print(f"✅ Final results built: {len(final_results)} candidates")

    # Display final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for i, result in enumerate(final_results, 1):
        print(f"\n🌟 Candidate {i}:")
        print(f"   Original: {result['idea'][:80]}...")
        print(f"   Initial Score: {result['initial_score']}")
        print(f"   Improved: {result['improved_idea'][:80]}...")
        print(f"   Improved Score: {result['improved_score']}")
        print(f"   Score Delta: {result['score_delta']}")
        print(f"   Meaningful Improvement: {result['is_meaningful_improvement']}")
        print(f"   Similarity: {result['similarity_score']:.2f}")

    total_tokens = tokens1 + tokens2 + tokens3 + tokens4 + tokens5 + tokens6
    print(f"\n📊 Total tokens used: {total_tokens}")
    print("\n✅ TEST 1 PASSED\n")

    return final_results


def main():
    """Run all manual tests."""
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not set")
        print("   Set your API key: export GOOGLE_API_KEY='your-key-here'")
        return 1

    print("\n🚀 Starting WorkflowOrchestrator Manual Tests")
    print(f"   API Key: {'*' * 20}{api_key[-10:]}")
    print(f"   MADSPARK_MODE: {os.getenv('MADSPARK_MODE', 'not set (will use real API)')}")

    try:
        # Test 1: Basic workflow
        results = test_basic_workflow()

        if not results:
            print("❌ No results generated")
            return 1

        if len(results) < 2:
            print(f"⚠️  Expected 2 results, got {len(results)}")

        # Check for required fields
        required_fields = [
            'idea', 'initial_score', 'initial_critique',
            'advocacy', 'skepticism',
            'improved_idea', 'improved_score', 'improved_critique',
            'score_delta', 'is_meaningful_improvement', 'similarity_score'
        ]

        for i, result in enumerate(results):
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                print(f"❌ Result {i+1} missing fields: {missing_fields}")
                return 1

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
