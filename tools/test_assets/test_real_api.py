#!/usr/bin/env python3
"""
Real API Testing for Multi-Modal Features.

This script tests the multi-modal functionality with real Gemini API calls.
It validates that file uploads, URL context, and mixed inputs work correctly.

Usage: PYTHONPATH=src python tools/test_assets/test_real_api.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from madspark.agents.idea_generator import generate_ideas, improve_idea  # noqa: E402


def test_single_file_context():
    """Test 1: Generate ideas with single file context."""
    print("\n" + "="*70)
    print("TEST 1: Single File Context (UI Diagram)")
    print("="*70)

    diagram_file = Path(__file__).parent / "test_diagram.txt"

    print(f"📄 Using file: {diagram_file}")
    print("📊 Topic: UI/UX improvements")

    try:
        result = generate_ideas(
            topic="UI/UX improvements",
            context="Modern web application design",
            multimodal_files=[str(diagram_file)],
            temperature=0.8,
            use_structured_output=True
        )

        print("\n✅ API Call Successful!")
        print(f"📝 Result length: {len(result)} characters")
        print("\n🎯 Generated Ideas (first 500 chars):")
        print("-" * 70)
        print(result[:500])
        print("..." if len(result) > 500 else "")

        # Validate result
        assert len(result) > 0, "Result should not be empty"
        assert "idea" in result.lower() or "{" in result, "Result should contain ideas"

        print("\n✅ Test 1 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_context():
    """Test 2: Generate ideas with URL context."""
    print("\n" + "="*70)
    print("TEST 2: URL Context")
    print("="*70)

    test_urls = ["https://www.example.com"]

    print(f"🔗 Using URLs: {test_urls}")
    print("📊 Topic: Website improvement ideas")

    try:
        result = generate_ideas(
            topic="Website improvement ideas",
            context="User experience optimization",
            multimodal_urls=test_urls,
            temperature=0.8,
            use_structured_output=True
        )

        print("\n✅ API Call Successful!")
        print(f"📝 Result length: {len(result)} characters")
        print("\n🎯 Generated Ideas (first 500 chars):")
        print("-" * 70)
        print(result[:500])
        print("..." if len(result) > 500 else "")

        # Validate result
        assert len(result) > 0, "Result should not be empty"
        assert "idea" in result.lower() or "{" in result, "Result should contain ideas"

        print("\n✅ Test 2 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_multimodal():
    """Test 3: Generate ideas with both file and URL."""
    print("\n" + "="*70)
    print("TEST 3: Mixed Multi-Modal (File + URL)")
    print("="*70)

    diagram_file = Path(__file__).parent / "test_diagram.txt"
    test_urls = ["https://www.example.com"]

    print(f"📄 Using file: {diagram_file}")
    print(f"🔗 Using URLs: {test_urls}")
    print("📊 Topic: Comprehensive design improvements")

    try:
        result = generate_ideas(
            topic="Comprehensive design improvements",
            context="Combining best practices from examples and diagrams",
            multimodal_files=[str(diagram_file)],
            multimodal_urls=test_urls,
            temperature=0.8,
            use_structured_output=True
        )

        print("\n✅ API Call Successful!")
        print(f"📝 Result length: {len(result)} characters")
        print("\n🎯 Generated Ideas (first 500 chars):")
        print("-" * 70)
        print(result[:500])
        print("..." if len(result) > 500 else "")

        # Validate result
        assert len(result) > 0, "Result should not be empty"
        assert "idea" in result.lower() or "{" in result, "Result should contain ideas"

        print("\n✅ Test 3 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_improve_idea_with_file():
    """Test 4: Improve idea with file context."""
    print("\n" + "="*70)
    print("TEST 4: Improve Idea with File Context")
    print("="*70)

    diagram_file = Path(__file__).parent / "test_diagram.txt"

    print(f"📄 Using file: {diagram_file}")

    try:
        result = improve_idea(
            original_idea="A responsive UI with cards layout",
            critique="Good foundation but needs more specific features",
            advocacy_points="Clear visual hierarchy, modern approach",
            skeptic_points="Lacks interactivity details, no accessibility mentions",
            topic="UI Component Design",
            context="Web application interface",
            multimodal_files=[str(diagram_file)],
            temperature=0.8
        )

        print("\n✅ API Call Successful!")
        print(f"📝 Result length: {len(result)} characters")
        print("\n🎯 Improved Idea (first 500 chars):")
        print("-" * 70)
        print(result[:500])
        print("..." if len(result) > 500 else "")

        # Validate result
        assert len(result) > 0, "Result should not be empty"
        assert len(result) > 20, "Improved idea should be substantive"

        print("\n✅ Test 4 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test 5: Validate error handling for invalid inputs."""
    print("\n" + "="*70)
    print("TEST 5: Error Handling")
    print("="*70)

    # Test invalid file
    print("\n📋 Sub-test 5a: Invalid file path")
    try:
        generate_ideas(
            topic="Test",
            context="Test",
            multimodal_files=["/nonexistent/file.png"]
        )
        print("❌ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError:
        print("✅ Correctly raised FileNotFoundError")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}")
        return False

    # Test invalid URL
    print("\n📋 Sub-test 5b: Invalid URL")
    try:
        generate_ideas(
            topic="Test",
            context="Test",
            multimodal_urls=["not-a-valid-url"]
        )
        print("❌ Should have raised ValueError")
        return False
    except ValueError as e:
        if "Invalid URL" in str(e):
            print("✅ Correctly raised ValueError for invalid URL")
        else:
            print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}")
        return False

    print("\n✅ Test 5 PASSED")
    return True


def main():
    """Run all real API tests."""
    print("="*70)
    print("REAL API TESTING - Multi-Modal Features")
    print("="*70)

    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not set!")
        print("   Please set it in .env file")
        sys.exit(1)

    print(f"✅ API Key found: {api_key[:10]}...")

    # Run tests
    results = {
        'single_file': test_single_file_context(),
        'url_context': test_url_context(),
        'mixed_multimodal': test_mixed_multimodal(),
        'improve_with_file': test_improve_idea_with_file(),
        'error_handling': test_error_handling()
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
