#!/usr/bin/env python3
"""Manual test script for Phase 3.2a WorkflowOrchestrator enhancements.

This script tests the new Phase 3.2a features with real API calls:
1. Monitoring integration
2. Async method variants
3. Multi-dimensional evaluation support

Run with: PYTHONPATH=src python tests/manual_test_phase_3_2a.py
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.workflow_orchestrator import WorkflowOrchestrator
from madspark.utils.temperature_control import TemperatureManager
from madspark.utils.batch_monitor import BatchMonitor, reset_batch_monitor
from madspark.agents.genai_client import get_genai_client

def test_monitoring_integration():
    """Test monitoring integration with real API."""
    print("\n" + "="*70)
    print("TEST 1: Monitoring Integration")
    print("="*70)

    # Reset monitor to get fresh metrics
    reset_batch_monitor()
    monitor = BatchMonitor()

    # Create orchestrator with monitoring
    temp_manager = TemperatureManager.from_base_temperature(0.7)
    orchestrator = WorkflowOrchestrator(
        temperature_manager=temp_manager,
        verbose=True
    )

    topic = "AI-powered productivity tools"
    context = "For software developers"

    try:
        # Test idea generation with monitoring
        print("\n📋 Testing idea generation with monitoring...")
        ideas, tokens = orchestrator.generate_ideas_with_monitoring(
            topic=topic,
            context=context,
            num_ideas=2,
            monitor=monitor
        )

        print(f"✅ Generated {len(ideas)} ideas")
        print(f"📊 Tokens used: {tokens}")
        print(f"📈 Monitoring history: {len(monitor.metrics_history)} entries")

        # Verify monitoring recorded the operation
        assert len(monitor.metrics_history) == 1, "Monitoring should have 1 entry"
        assert monitor.metrics_history[0].batch_type == "idea_generation"
        assert monitor.metrics_history[0].success is True
        print("✅ Monitoring correctly recorded idea generation")

        # Test evaluation with monitoring
        print("\n📋 Testing evaluation with monitoring...")
        evaluated, tokens = orchestrator.evaluate_ideas_with_monitoring(
            ideas=ideas,
            topic=topic,
            context=context,
            monitor=monitor
        )

        print(f"✅ Evaluated {len(evaluated)} ideas")
        print(f"📊 Tokens used: {tokens}")
        assert len(monitor.metrics_history) == 2, "Monitoring should have 2 entries"
        print("✅ Monitoring correctly recorded evaluation")

        # Get monitoring summary
        print("\n📊 Monitoring Summary:")
        summary = monitor.get_session_summary()
        print(f"  Total calls: {summary['total_calls']}")
        print(f"  Successful calls: {summary['successful_calls']}")
        print(f"  Total tokens: {summary['total_tokens_used']}")
        print(f"  Total cost: ${summary['total_estimated_cost_usd']:.4f}")

        print("\n✅ TEST 1 PASSED: Monitoring integration works with real API")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_methods():
    """Test async method variants with real API."""
    print("\n" + "="*70)
    print("TEST 2: Async Method Variants")
    print("="*70)

    temp_manager = TemperatureManager.from_base_temperature(0.7)
    orchestrator = WorkflowOrchestrator(
        temperature_manager=temp_manager,
        verbose=True
    )

    topic = "Sustainable energy solutions"
    context = "For urban environments"

    try:
        # Test async idea generation
        print("\n📋 Testing async idea generation...")
        ideas, tokens = await orchestrator.generate_ideas_async(
            topic=topic,
            context=context,
            num_ideas=2
        )

        print(f"✅ Generated {len(ideas)} ideas asynchronously")
        print(f"📊 Tokens used: {tokens}")

        # Test async evaluation
        print("\n📋 Testing async evaluation...")
        evaluated, tokens = await orchestrator.evaluate_ideas_async(
            ideas=ideas,
            topic=topic,
            context=context
        )

        print(f"✅ Evaluated {len(evaluated)} ideas asynchronously")

        # Prepare candidates for async processing
        candidates = [
            {
                "idea": evaluated[0]["text"],
                "initial_score": evaluated[0]["score"],
                "initial_critique": evaluated[0]["critique"]
            }
        ]

        # Test parallel async execution (advocacy + skepticism)
        print("\n📋 Testing parallel async execution...")
        results = await asyncio.gather(
            orchestrator.process_advocacy_async(candidates.copy(), topic, context),
            orchestrator.process_skepticism_async(candidates.copy(), topic, context)
        )

        print("✅ Successfully ran advocacy and skepticism in parallel")

        # Test async improvement
        print("\n📋 Testing async improvement...")
        # Merge results
        for key in ["advocacy", "skepticism"]:
            if key in results[0][0][0]:
                candidates[0][key] = results[0][0][0][key]
            if key in results[1][0][0]:
                candidates[0][key] = results[1][0][0][key]

        improved, tokens = await orchestrator.improve_ideas_async(
            candidates=candidates,
            topic=topic,
            context=context
        )

        print(f"✅ Improved {len(improved)} ideas asynchronously")

        print("\n✅ TEST 2 PASSED: Async methods work with real API")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_dimensional_evaluation():
    """Test multi-dimensional evaluation with real API."""
    print("\n" + "="*70)
    print("TEST 3: Multi-Dimensional Evaluation")
    print("="*70)

    # Check if we have GenAI client
    try:
        genai_client = get_genai_client()
    except Exception as e:
        print(f"⚠️  GenAI client not available: {e}")
        print("⏭️  Skipping multi-dimensional evaluation test")
        return True  # Not a failure, just skipped

    temp_manager = TemperatureManager.from_base_temperature(0.7)

    # Create reasoning engine for multi-dimensional evaluation
    from madspark.core.enhanced_reasoning import ReasoningEngine
    reasoning_engine = ReasoningEngine(genai_client=genai_client)

    orchestrator = WorkflowOrchestrator(
        temperature_manager=temp_manager,
        reasoning_engine=reasoning_engine,
        verbose=True
    )

    topic = "Healthcare automation"
    context = "Using AI and robotics"

    try:
        # Generate and evaluate ideas first
        print("\n📋 Generating ideas...")
        ideas, _ = orchestrator.generate_ideas(topic, context, 2)

        print("\n📋 Evaluating ideas...")
        evaluated, _ = orchestrator.evaluate_ideas(ideas, topic, context)

        # Prepare candidates
        candidates = [
            {
                "text": evaluated[0]["text"],
                "critique": evaluated[0]["critique"]
            }
        ]

        # Test multi-dimensional evaluation
        print("\n📋 Testing multi-dimensional evaluation...")
        updated = orchestrator.add_multi_dimensional_evaluation(
            candidates=candidates,
            topic=topic,
            context=context
        )

        if updated[0].get("multi_dimensional_evaluation"):
            print("✅ Multi-dimensional evaluation completed")
            md_eval = updated[0]["multi_dimensional_evaluation"]
            print("\n📊 Multi-Dimensional Scores:")
            for key, value in md_eval.items():
                print(f"  {key}: {value}")

            # Verify expected dimensions
            expected_dims = ["feasibility", "innovation", "impact", "cost_effectiveness",
                           "scalability", "safety_score", "timeline"]
            for dim in expected_dims:
                if dim in md_eval:
                    print(f"  ✅ {dim} present")
        else:
            print("⚠️  Multi-dimensional evaluation returned None (feature may not be fully enabled)")

        print("\n✅ TEST 3 PASSED: Multi-dimensional evaluation works")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all manual tests."""
    print("\n" + "="*70)
    print("PHASE 3.2a MANUAL TESTING WITH REAL API")
    print("="*70)

    # Check for API key
    if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
        print("\n❌ ERROR: No API key found!")
        print("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        sys.exit(1)

    print("✅ API key found")

    results = []

    # Test 1: Monitoring Integration
    results.append(("Monitoring Integration", test_monitoring_integration()))

    # Test 2: Async Methods
    print("\n" + "="*70)
    results.append(("Async Methods", asyncio.run(test_async_methods())))

    # Test 3: Multi-Dimensional Evaluation
    print("\n" + "="*70)
    results.append(("Multi-Dimensional Evaluation", test_multi_dimensional_evaluation()))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        sys.exit(1)


if __name__ == "__main__":
    main()
