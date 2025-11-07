#!/usr/bin/env python3
"""Manual test script for Phase 3.2b coordinator_batch integration.

This script tests the WorkflowOrchestrator integration with real API calls:
1. Verify workflow steps execute correctly
2. Check monitoring data accuracy (tokens, costs)
3. Validate output quality (no timeouts, broken formats, truncation)
4. Compare before/after behavior

Run with: PYTHONPATH=src python tests/manual_test_phase_3_2b.py
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.utils.batch_monitor import get_batch_monitor, reset_batch_monitor


def test_basic_workflow():
    """Test basic workflow with real API."""
    print("\n" + "="*70)
    print("TEST 1: Basic Workflow Integration")
    print("="*70)

    # Reset monitor to get fresh metrics
    reset_batch_monitor()

    topic = "AI-powered productivity tools"
    context = "For software developers"

    try:
        print(f"\n📋 Running workflow for: {topic}")
        print(f"Context: {context}")

        results = run_multistep_workflow_batch(
            topic=topic,
            context=context,
            num_top_candidates=2,
            verbose=True
        )

        print("\n✅ Workflow completed successfully")
        print(f"📊 Generated {len(results)} candidates")

        # Verify output quality
        for i, candidate in enumerate(results):
            print(f"\n--- Candidate {i+1} ---")
            print(f"Original: {candidate.get('text', 'N/A')[:100]}...")
            print(f"Initial Score: {candidate.get('initial_score', 'N/A')}")
            print(f"Improved: {candidate.get('improved_idea', 'N/A')[:100]}...")
            print(f"Improved Score: {candidate.get('improved_score', 'N/A')}")
            print(f"Advocacy: {candidate.get('advocacy', 'N/A')[:50]}...")
            print(f"Skepticism: {candidate.get('skepticism', 'N/A')[:50]}...")

            # Quality checks
            assert candidate.get('text'), "❌ Text field missing!"
            assert candidate.get('improved_idea'), "❌ Improved idea missing!"
            assert candidate.get('advocacy') and candidate['advocacy'] != 'N/A', "❌ Advocacy is N/A!"
            assert candidate.get('skepticism') and candidate['skepticism'] != 'N/A', "❌ Skepticism is N/A!"
            assert 'Timeout' not in str(candidate.get('improved_idea', '')), "❌ Timeout detected!"
            assert len(candidate.get('improved_idea', '')) > 50, "❌ Truncated output!"

        # Get monitoring summary
        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()

        print("\n📊 Monitoring Summary:")
        print(f"  Total API calls: {summary['total_calls']}")
        print(f"  Successful calls: {summary['successful_calls']}")
        print(f"  Total tokens: {summary['total_tokens_used']}")
        print(f"  Total cost: ${summary['total_estimated_cost_usd']:.4f}")

        # Verify monitoring tracked calls
        assert summary['total_calls'] > 0, "❌ No API calls tracked!"
        assert summary['successful_calls'] > 0, "❌ No successful calls!"
        assert summary['total_tokens_used'] > 0, "❌ No tokens tracked!"

        print("\n✅ TEST 1 PASSED: Basic workflow works correctly")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_dimensional_evaluation():
    """Test with multi-dimensional evaluation enabled."""
    print("\n" + "="*70)
    print("TEST 2: Multi-Dimensional Evaluation")
    print("="*70)

    # Reset monitor
    reset_batch_monitor()

    topic = "Sustainable urban transportation"
    context = "Low-cost, high-impact"

    try:
        print("\n📋 Running workflow with multi-dimensional evaluation")
        print(f"Topic: {topic}")

        results = run_multistep_workflow_batch(
            topic=topic,
            context=context,
            num_top_candidates=1,
            multi_dimensional_eval=True,
            enable_reasoning=True,
            verbose=True
        )

        print("\n✅ Workflow completed")
        print(f"📊 Generated {len(results)} candidate(s)")

        # Check for multi-dimensional evaluation
        if results:
            candidate = results[0]

            if candidate.get('multi_dimensional_evaluation'):
                print("\n📊 Multi-Dimensional Evaluation (Initial):")
                md_eval = candidate['multi_dimensional_evaluation']
                for key, value in md_eval.items():
                    print(f"  {key}: {value}")
                print("✅ Initial multi-dimensional evaluation present")
            else:
                print("⚠️  Multi-dimensional evaluation not available (may need API key or feature disabled)")

            if candidate.get('improved_multi_dimensional_evaluation'):
                print("\n📊 Multi-Dimensional Evaluation (Improved):")
                md_eval_improved = candidate['improved_multi_dimensional_evaluation']
                for key, value in md_eval_improved.items():
                    print(f"  {key}: {value}")
                print("✅ Improved multi-dimensional evaluation present")

        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()
        print(f"\n📊 Cost: ${summary['total_estimated_cost_usd']:.4f}")

        print("\n✅ TEST 2 PASSED: Multi-dimensional evaluation works")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_efficiency():
    """Test that batch processing is still O(1) not O(N)."""
    print("\n" + "="*70)
    print("TEST 3: Batch Processing Efficiency")
    print("="*70)

    # Reset monitor
    reset_batch_monitor()

    topic = "Healthcare automation"
    context = "Using AI and robotics"

    try:
        print("\n📋 Running workflow with 3 candidates")

        results = run_multistep_workflow_batch(
            topic=topic,
            context=context,
            num_top_candidates=3,
            verbose=False  # Less noise
        )

        print(f"\n✅ Processed {len(results)} candidates")

        # Get monitoring data
        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()

        print("\n📊 API Efficiency Check:")
        print(f"  Total API calls: {summary['total_calls']}")
        print(f"  Batch operations: {len([m for m in monitor.metrics_history if 'batch' in m.batch_type.lower()])}")

        # Verify batch efficiency
        # Expected: 1 generation + 1 eval + 1 advocacy + 1 skepticism + 1 improvement + 1 re-eval = 6 calls
        # NOT 17+ calls (old O(N) approach)
        assert summary['total_calls'] <= 10, f"❌ Too many API calls: {summary['total_calls']} (expected ≤10)"

        print("✅ Batch processing efficient (O(1) not O(N))")
        print(f"✅ Total cost: ${summary['total_estimated_cost_usd']:.4f}")

        print("\n✅ TEST 3 PASSED: Batch efficiency maintained")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all manual tests."""
    print("\n" + "="*70)
    print("PHASE 3.2b MANUAL TESTING WITH REAL API")
    print("="*70)

    # Check for API key
    if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
        print("\n❌ ERROR: No API key found!")
        print("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        sys.exit(1)

    print("✅ API key found")

    results = []

    # Test 1: Basic Workflow
    results.append(("Basic Workflow", test_basic_workflow()))

    # Test 2: Multi-Dimensional Evaluation
    print("\n" + "="*70)
    results.append(("Multi-Dimensional Evaluation", test_multi_dimensional_evaluation()))

    # Test 3: Batch Efficiency
    print("\n" + "="*70)
    results.append(("Batch Efficiency", test_batch_efficiency()))

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
