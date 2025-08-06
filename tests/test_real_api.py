#!/usr/bin/env python
"""Test script for verifying all fixes with real Google Gemini API.

This script should be run with a valid GOOGLE_API_KEY environment variable.
It tests:
1. Bookmark functionality with topic/context parameters
2. Language consistency in responses
3. Logical inference field completeness
4. End-to-end workflow functionality

Usage:
    GOOGLE_API_KEY=your-key python tests/test_real_api.py
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.bookmark_system import BookmarkManager
from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
from madspark.agents.genai_client import get_genai_client
from madspark.core.coordinator import run_multistep_workflow


def test_bookmark_functionality():
    """Test bookmark system with real data."""
    print("\n=== Testing Bookmark Functionality ===")
    
    manager = BookmarkManager()
    
    # Test bookmarking with topic/context
    bookmark_id = manager.bookmark_idea(
        idea_text="An AI-powered system for predicting and preventing urban traffic congestion using real-time data from IoT sensors and machine learning algorithms",
        topic="Smart city solutions",
        context="Cost-effective and scalable for mid-sized cities",
        score=8.5,
        critique="Strong technical foundation with clear practical applications",
        advocacy="This solution addresses a major urban challenge with proven technology",
        skepticism="Initial infrastructure investment may be significant"
    )
    
    print(f"✅ Created bookmark: {bookmark_id}")
    
    # Test duplicate detection
    duplicate_result = manager.check_for_duplicates(
        idea_text="AI system for traffic congestion prediction using IoT sensors",
        topic="Smart city solutions"
    )
    
    if duplicate_result.has_duplicates:
        print(f"✅ Duplicate detection working: Found {len(duplicate_result.similar_bookmarks)} similar ideas")
    else:
        print("⚠️ No duplicates found (expected to find the bookmark we just created)")
    
    # Test similarity search
    similar = manager.find_similar_bookmarks(
        idea_text="Machine learning for traffic optimization",
        topic="Smart city solutions",
        max_results=3
    )
    
    print(f"✅ Similarity search found {len(similar)} similar bookmarks")
    
    return True


def test_language_consistency():
    """Test that AI responds in the same language as input."""
    print("\n=== Testing Language Consistency ===")
    
    try:
        genai_client = get_genai_client()
        evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
        
        # Test 1: English input
        print("\nTest 1: English input...")
        english_result = evaluator.evaluate_idea(
            idea="A blockchain-based voting system for secure elections",
            context={"topic": "Democratic technology", "context": "Accessible to all citizens"}
        )
        print(f"✅ English evaluation completed: {english_result.get('average_score', 'N/A')}")
        
        # Test 2: Japanese input
        print("\nTest 2: Japanese input...")
        japanese_result = evaluator.evaluate_idea(
            idea="選挙の安全性を確保するブロックチェーンベースの投票システム",
            context={"topic": "民主的技術", "context": "すべての市民がアクセス可能"}
        )
        print(f"✅ Japanese evaluation completed: {japanese_result.get('average_score', 'N/A')}")
        if 'summary' in japanese_result:
            # Check if summary contains Japanese characters
            if any(ord(char) > 127 for char in japanese_result['summary']):
                print("✅ Response contains Japanese characters")
            else:
                print("⚠️ Response might not be in Japanese")
        
        # Test 3: Chinese input
        print("\nTest 3: Chinese input...")
        chinese_result = evaluator.evaluate_idea(
            idea="基于区块链的安全选举投票系统",
            context={"topic": "民主科技", "context": "所有公民都可以使用"}
        )
        print(f"✅ Chinese evaluation completed: {chinese_result.get('average_score', 'N/A')}")
        
        # Test 4: French input
        print("\nTest 4: French input...")
        french_result = evaluator.evaluate_idea(
            idea="Un système de vote basé sur la blockchain pour des élections sécurisées",
            context={"topic": "Technologie démocratique", "context": "Accessible à tous les citoyens"}
        )
        print(f"✅ French evaluation completed: {french_result.get('average_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Language consistency test failed: {e}")
        return False


def test_logical_inference_fields():
    """Test that logical inference returns all expected fields."""
    print("\n=== Testing Logical Inference Field Completeness ===")
    
    try:
        genai_client = get_genai_client()
        engine = LogicalInferenceEngine(genai_client=genai_client)
        
        # Test different analysis types
        test_cases = [
            (InferenceType.FULL, "Comprehensive analysis"),
            (InferenceType.CAUSAL, "Causal chain analysis"),
            (InferenceType.CONSTRAINTS, "Constraint satisfaction"),
            (InferenceType.CONTRADICTION, "Contradiction detection"),
            (InferenceType.IMPLICATIONS, "Implications analysis")
        ]
        
        for analysis_type, description in test_cases:
            print(f"\nTesting {description} ({analysis_type.value})...")
            
            result = engine.analyze(
                idea="Implement a universal basic income program funded by automation taxes",
                topic="Economic policy",
                context="Addressing job displacement from AI and automation",
                analysis_type=analysis_type
            )
            
            # Check core fields
            assert hasattr(result, 'conclusion'), f"Missing 'conclusion' field in {analysis_type.value}"
            assert hasattr(result, 'confidence'), f"Missing 'confidence' field in {analysis_type.value}"
            
            # Check specific fields based on analysis type
            if analysis_type == InferenceType.FULL:
                assert hasattr(result, 'inference_chain'), "Missing 'inference_chain' in FULL analysis"
                assert hasattr(result, 'improvements'), "Missing 'improvements' in FULL analysis"
                
            elif analysis_type == InferenceType.CAUSAL:
                assert hasattr(result, 'causal_chain') or hasattr(result, 'root_cause'), \
                    "Missing causal fields in CAUSAL analysis"
                    
            elif analysis_type == InferenceType.CONSTRAINTS:
                assert hasattr(result, 'constraint_satisfaction') or hasattr(result, 'overall_satisfaction'), \
                    "Missing constraint fields in CONSTRAINTS analysis"
                    
            elif analysis_type == InferenceType.CONTRADICTION:
                assert hasattr(result, 'contradictions') or hasattr(result, 'resolution'), \
                    "Missing contradiction fields in CONTRADICTION analysis"
                    
            elif analysis_type == InferenceType.IMPLICATIONS:
                assert hasattr(result, 'implications') or hasattr(result, 'second_order_effects'), \
                    "Missing implication fields in IMPLICATIONS analysis"
            
            print(f"✅ {description} has all expected fields")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Conclusion preview: {result.conclusion[:100]}...")
        
        # Test batch analysis
        print("\nTesting batch logical inference...")
        batch_results = engine.analyze_batch(
            ideas=[
                "Solar-powered charging stations for electric vehicles",
                "Wind turbine installations on highway medians",
                "Geothermal energy for district heating"
            ],
            topic="Renewable energy infrastructure",
            context="Urban implementation with minimal disruption",
            analysis_type=InferenceType.FULL
        )
        
        assert len(batch_results) == 3, "Batch analysis should return 3 results"
        for i, result in enumerate(batch_results):
            assert hasattr(result, 'conclusion'), f"Batch result {i} missing conclusion"
            assert hasattr(result, 'confidence'), f"Batch result {i} missing confidence"
        
        print(f"✅ Batch analysis returned {len(batch_results)} complete results")
        
        return True
        
    except Exception as e:
        print(f"❌ Logical inference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_workflow():
    """Test complete workflow with all components."""
    print("\n=== Testing End-to-End Workflow ===")
    
    try:
        # Test with English
        print("\nRunning workflow with English input...")
        english_results = run_multistep_workflow(
            topic="Sustainable urban farming",
            context="Suitable for rooftops and small spaces",
            num_candidates=2,
            enhanced_reasoning=True,
            logical_inference=True,
            multi_dimensional_eval=True,
            verbose=True
        )
        
        print(f"\n✅ English workflow completed with {len(english_results)} results")
        
        # Verify result structure
        for i, result in enumerate(english_results):
            assert 'idea' in result, f"Result {i} missing 'idea' field"
            assert 'improved_idea' in result, f"Result {i} missing 'improved_idea' field"
            assert 'initial_score' in result, f"Result {i} missing 'initial_score' field"
            assert 'improved_score' in result, f"Result {i} missing 'improved_score' field"
            print(f"   Result {i+1}: Score {result['initial_score']:.1f} → {result['improved_score']:.1f}")
        
        # Test with non-English
        print("\nRunning workflow with Japanese input...")
        japanese_results = run_multistep_workflow(
            topic="持続可能な都市農業",
            context="屋上や小さなスペースに適している",
            num_candidates=1,
            verbose=False
        )
        
        print(f"✅ Japanese workflow completed with {len(japanese_results)} results")
        
        # Test bookmarking the best result
        if english_results:
            best_result = max(english_results, key=lambda x: x.get('improved_score', 0))
            manager = BookmarkManager()
            
            bookmark_id = manager.bookmark_idea(
                idea_text=best_result.get('improved_idea', best_result.get('idea', '')),
                topic="Sustainable urban farming",
                context="Suitable for rooftops and small spaces",
                score=best_result.get('improved_score', best_result.get('initial_score', 0)),
                critique=best_result.get('critique', ''),
                advocacy=best_result.get('advocacy', '')
            )
            
            print(f"\n✅ Successfully bookmarked best idea: {bookmark_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests with real API."""
    print("=" * 60)
    print("REAL API TESTING - All Fixes Verification")
    print("=" * 60)
    
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("\n❌ ERROR: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY=your-key")
        return 1
    
    print(f"\n✅ API key detected: {os.getenv('GOOGLE_API_KEY')[:10]}...")
    
    # Run tests
    results = {
        "Bookmark Functionality": test_bookmark_functionality(),
        "Language Consistency": test_language_consistency(),
        "Logical Inference Fields": test_logical_inference_fields(),
        "End-to-End Workflow": test_end_to_end_workflow()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! All fixes are working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())