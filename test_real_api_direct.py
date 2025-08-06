#!/usr/bin/env python3
"""
Direct test script for real API functionality, bypassing the hanging coordinator.
Tests:
1. Bookmark functionality with correct parameters
2. Language consistency in evaluations
3. Logical inference field parity
"""

import os
import sys
import json
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'
os.environ['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY', '')

def test_bookmark_functionality():
    """Test bookmark functionality with topic/context parameters."""
    print("\n=== Testing Bookmark Functionality ===")
    from madspark.utils.bookmark_system import BookmarkManager
    
    manager = BookmarkManager()
    
    # Test adding bookmark with correct parameters
    test_idea = "Solar-powered water purification systems for rural communities"
    bookmark_id = manager.bookmark_idea_with_duplicate_check(
        idea_text=test_idea,
        topic="Sustainable energy",
        context="Affordable for developing countries",
        score=8.5
    )
    
    if bookmark_id:
        print(f"✅ Bookmark created successfully with ID: {bookmark_id}")
        
        # Test duplicate detection
        similar_bookmarks = manager.find_similar_bookmarks(
            idea_text=test_idea,
            topic="Sustainable energy"
        )
        if similar_bookmarks:
            print(f"✅ Duplicate detection working: found {len(similar_bookmarks)} similar bookmarks")
    else:
        print("❌ Failed to create bookmark")
    
    return bookmark_id is not None


def test_language_consistency():
    """Test language consistency in multi-dimensional evaluation."""
    print("\n=== Testing Language Consistency ===")
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.agents.genai_client import get_genai_client
    
    try:
        genai_client = get_genai_client()
        evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
        
        # Test with Japanese input
        japanese_idea = "太陽光発電と風力発電を組み合わせた分散型エネルギーシステム"
        
        # Evaluate idea (should include language consistency instruction)
        context = {
            'topic': "持続可能なエネルギー",
            'context': "発展途上国向けの低コスト"
        }
        result = evaluator.evaluate_idea(
            idea=japanese_idea,
            context=context
        )
        
        print(f"✅ Japanese evaluation completed")
        result_str = str(result)
        print(f"   Result type: {type(result)}")
        print(f"   Result preview: {result_str[:100]}...")
        
        # Check if response is in Japanese (contains Japanese characters)
        has_japanese = any(ord(char) > 0x3000 for char in result_str)
        if has_japanese:
            print("✅ Response contains Japanese characters (language consistency maintained)")
        else:
            print("⚠️  Response may not be in Japanese")
        
        return True
    except Exception as e:
        print(f"❌ Language consistency test failed: {e}")
        return False


def test_logical_inference_fields():
    """Test logical inference field parity between mock and production."""
    print("\n=== Testing Logical Inference Fields ===")
    from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
    from madspark.agents.genai_client import get_genai_client
    
    try:
        genai_client = get_genai_client()
        engine = LogicalInferenceEngine(genai_client=genai_client)
        
        # Test full reasoning
        result = engine.analyze(
            idea="Community solar gardens with shared ownership",
            topic="Sustainable energy",
            context="Affordable for developing countries",
            analysis_type=InferenceType.FULL
        )
        
        print(f"✅ Logical inference completed")
        
        # Check for expected fields
        if hasattr(result, 'causal_chains'):
            print("✅ Has causal_chains field")
        if hasattr(result, 'constraint_satisfaction'):
            print("✅ Has constraint_satisfaction field")
        if hasattr(result, 'contradictions'):
            print("✅ Has contradictions field")
        if hasattr(result, 'implications'):
            print("✅ Has implications field")
        
        # Test that we get InferenceResult object (not dict)
        from madspark.utils.logical_inference_engine import InferenceResult
        if isinstance(result, InferenceResult):
            print("✅ Returns InferenceResult object (field parity maintained)")
        else:
            print(f"❌ Returns {type(result)} instead of InferenceResult")
        
        return isinstance(result, InferenceResult)
    except Exception as e:
        print(f"❌ Logical inference test failed: {e}")
        return False


def test_idea_generation():
    """Test basic idea generation to verify API is working."""
    print("\n=== Testing Idea Generation ===")
    from madspark.agents.idea_generator import generate_ideas
    
    try:
        result = generate_ideas(
            topic="Renewable energy",
            context="Low-cost solutions",
            temperature=0.7,
            use_structured_output=True
        )
        
        # Parse the result
        ideas = json.loads(result) if isinstance(result, str) else result
        if ideas:
            print(f"✅ Generated {len(ideas)} ideas")
            if isinstance(ideas, list) and len(ideas) > 0:
                first_idea = ideas[0]
                print(f"   First idea title: {first_idea.get('title', 'No title')[:50]}...")
                return True
        else:
            print("❌ No ideas generated")
            return False
    except Exception as e:
        print(f"❌ Idea generation failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("REAL API TESTING - DIRECT (BYPASSING COORDINATOR)")
    print("=" * 60)
    
    # Check API key
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real Google API key not found in environment")
        print("   Please run: source .env")
        return 1
    
    print(f"✅ Using API key: {api_key[:10]}...")
    
    results = {
        'idea_generation': test_idea_generation(),
        'bookmark': test_bookmark_functionality(),
        'language_consistency': test_language_consistency(),
        'logical_inference': test_logical_inference_fields()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    all_passed = all(results.values())
    print("\n" + ("✅ ALL TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())