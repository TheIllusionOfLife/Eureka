#!/usr/bin/env python3
"""
Manual test script for critic.py with Pydantic schemas using real Gemini API.

Run this script with your GOOGLE_GENAI_API_KEY environment variable set.
This script tests multiple scenarios as per TDD requirements:
- Single idea evaluation
- Multiple ideas evaluation
- Score validation (should be within 0-10 due to Pydantic constraints)
- Response format validation
- No timeout, truncation, or errors

Usage:
    GOOGLE_GENAI_API_KEY=your_key python tools/test_pydantic_critic_real_api.py
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.agents.critic import evaluate_ideas


def test_single_idea():
    """Test evaluation of a single idea."""
    print("\n" + "="*80)
    print("TEST 1: Single Idea Evaluation")
    print("="*80)

    idea = "AI-powered personal fitness coach that adapts to user progress and provides real-time guidance"
    topic = "Health and Fitness Tech"
    context = "Consumer mobile apps for 2025"

    print(f"\nIdea: {idea}")
    print(f"Topic: {topic}")
    print(f"Context: {context}")

    result, token_count = evaluate_ideas(
        ideas=idea,
        topic=topic,
        context=context,
        temperature=0.7,
        use_structured_output=True
    )

    print(f"\n--- Raw API Response ---")
    print(result)
    print(f"Token count: {token_count}")

    # Parse and validate
    try:
        evaluations = json.loads(result)
        print(f"\n--- Parsed Evaluations ---")
        print(json.dumps(evaluations, indent=2))

        # Validation checks
        assert isinstance(evaluations, list), "Response should be a list"
        assert len(evaluations) >= 1, "Should have at least one evaluation"

        for i, eval_item in enumerate(evaluations):
            score = eval_item.get('score')
            comment = eval_item.get('comment')

            # Validate score bounds (Pydantic should enforce this)
            assert score is not None, "Score must be present"
            assert 0 <= score <= 10, f"Score {score} outside valid range [0, 10]"

            # Validate comment type and length
            assert isinstance(comment, str), "Comment must be a non-empty string"
            assert len(comment) >= 10, f"Comment too short: {len(comment)} chars"

            # Build preview after validation
            preview = comment[:100] + ("..." if len(comment) > 100 else "")
            print(f"\n✓ Evaluation {i+1}:")
            print(f"  Score: {score}")
            print(f"  Comment: {preview}")

        print("\n✅ Single idea test PASSED")
        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing failed: {e}")
        return False
    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        return False


def test_multiple_ideas():
    """Test evaluation of multiple ideas."""
    print("\n" + "="*80)
    print("TEST 2: Multiple Ideas Evaluation")
    print("="*80)

    ideas = """AI-powered code review assistant with automated bug detection
Blockchain-based supply chain transparency platform
Virtual reality remote collaboration workspace"""

    topic = "Innovative Startups"
    context = "Tech entrepreneurship in 2025, focusing on B2B SaaS"

    print(f"\nIdeas:")
    for i, idea in enumerate(ideas.split('\n'), 1):
        print(f"  {i}. {idea}")
    print(f"\nTopic: {topic}")
    print(f"Context: {context}")

    result, token_count = evaluate_ideas(
        ideas=ideas,
        topic=topic,
        context=context,
        temperature=0.7,
        use_structured_output=True
    )

    print(f"\n--- Raw API Response ---")
    print(result)
    print(f"Token count: {token_count}")

    # Parse and validate
    try:
        evaluations = json.loads(result)
        print(f"\n--- Parsed Evaluations ---")
        print(json.dumps(evaluations, indent=2))

        # Validation checks
        assert isinstance(evaluations, list), "Response should be a list"
        assert len(evaluations) == 3, f"Expected 3 evaluations, got {len(evaluations)}"

        for i, eval_item in enumerate(evaluations):
            score = eval_item.get('score')
            comment = eval_item.get('comment')

            # Validate score bounds
            assert score is not None, f"Evaluation {i+1}: Score must be present"
            assert 0 <= score <= 10, f"Evaluation {i+1}: Score {score} outside valid range"

            # Validate comment type and length
            assert isinstance(comment, str), f"Evaluation {i+1}: Comment must be a string"
            assert len(comment) >= 10, f"Evaluation {i+1}: Comment too short"

            # Check for truncation (common API issue)
            assert not comment.endswith("..."), f"Evaluation {i+1}: Comment appears truncated"

            # Build preview after validation
            preview = comment[:100] + ("..." if len(comment) > 100 else "")
            print(f"\n✓ Evaluation {i+1}:")
            print(f"  Score: {score}")
            print(f"  Comment: {preview}")

        print("\n✅ Multiple ideas test PASSED")
        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing failed: {e}")
        return False
    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        return False


def test_score_bounds_enforcement():
    """Test that Pydantic/Gemini API enforces score bounds."""
    print("\n" + "="*80)
    print("TEST 3: Score Bounds Enforcement (New Gemini API Feature)")
    print("="*80)

    # Test with extreme ideas that might normally produce out-of-bounds scores
    ideas = """Perfect revolutionary idea that solves all world problems
Terrible idea that makes no sense and is completely unfeasible"""

    topic = "Extreme Test Cases"
    context = "Testing score validation"

    print(f"\nTesting extreme cases to verify API enforces 0-10 bounds...")

    result, _ = evaluate_ideas(
        ideas=ideas,
        topic=topic,
        context=context,
        temperature=0.7,
        use_structured_output=True
    )

    try:
        evaluations = json.loads(result)

        all_valid = True
        for i, eval_item in enumerate(evaluations):
            score = eval_item.get('score')
            print(f"\n  Idea {i+1} score: {score}")

            if score < 0 or score > 10:
                print(f"    ❌ INVALID: Score {score} outside [0, 10]")
                all_valid = False
            else:
                print(f"    ✓ Valid score within bounds")

        if all_valid:
            print("\n✅ Score bounds test PASSED - API enforces constraints")
            return True
        else:
            print("\n❌ Score bounds test FAILED - found out-of-bounds scores")
            return False

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Pydantic Critic Schema - Real API Integration Tests")
    print("="*80)

    # Check for API key
    if not os.getenv('GOOGLE_GENAI_API_KEY'):
        print("\n❌ ERROR: GOOGLE_GENAI_API_KEY environment variable not set")
        print("Usage: GOOGLE_GENAI_API_KEY=your_key python tools/test_pydantic_critic_real_api.py")
        sys.exit(1)

    results = []

    # Run tests
    results.append(("Single Idea", test_single_idea()))
    results.append(("Multiple Ideas", test_multiple_ideas()))
    results.append(("Score Bounds", test_score_bounds_enforcement()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED")
        sys.exit(1)


if __name__ == '__main__':
    main()
