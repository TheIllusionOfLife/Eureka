#!/usr/bin/env python3
"""
Test script to verify Japanese language output in detailed results.
This bypasses the coordinator to test the actual language consistency.
"""

import os
import sys
import asyncio
import json
import time
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_japanese_multidimensional_evaluation():
    """Test that multi-dimensional evaluation returns Japanese when given Japanese input."""
    print("\n" + "="*60)
    print("Testing Multi-Dimensional Evaluation with Japanese Input")
    print("="*60)
    
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available. Check API key.")
        return False
    
    evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
    
    # Japanese input
    japanese_idea = """
    地域住民が共同で管理する屋上農園システム。
    各建物の屋上を活用し、IoTセンサーで水分と栄養を自動管理。
    収穫物は地域で共有し、余剰分は地元市場で販売。
    """
    
    context = {
        'topic': '持続可能な都市農業',
        'context': '低コストで実現可能な解決策'
    }
    
    print(f"入力アイデア: {japanese_idea[:50]}...")
    print(f"トピック: {context['topic']}")
    print(f"コンテキスト: {context['context']}")
    print("\n評価を実行中... (これには時間がかかる場合があります)")
    
    start_time = time.time()
    
    # Evaluate the idea
    result = evaluator.evaluate_idea(idea=japanese_idea, context=context)
    
    elapsed = time.time() - start_time
    print(f"\n✅ 評価完了 (所要時間: {elapsed:.1f}秒)")
    
    # Check the result
    if elapsed < 5:
        print("⚠️ WARNING: Completed too quickly. Might be using mock mode!")
        
    # Analyze the result
    print("\n=== 結果分析 ===")
    print(f"Result type: {type(result)}")
    
    if isinstance(result, dict):
        # Check summary
        if 'summary' in result:
            summary = result['summary']
            print(f"\nSummary preview: {summary[:200]}...")
            
            # Check for Japanese characters
            has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' for char in summary)
            if has_japanese:
                print("✅ Summary contains Japanese characters")
            else:
                print("❌ Summary does NOT contain Japanese characters")
                print(f"Full summary:\n{summary}")
        
        # Check dimension evaluations
        if 'dimension_scores' in result:
            print(f"\nDimension scores found: {list(result['dimension_scores'].keys())}")
            
        if 'dimension_evaluations' in result:
            print("\n=== Dimension Evaluations ===")
            for dim, eval_text in result['dimension_evaluations'].items():
                eval_preview = str(eval_text)[:100]
                print(f"\n{dim}: {eval_preview}...")
                
                # Check for Japanese
                has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' for char in str(eval_text))
                if has_japanese:
                    print(f"  ✅ {dim} evaluation is in Japanese")
                else:
                    print(f"  ❌ {dim} evaluation is NOT in Japanese")
    
    return True


def test_japanese_logical_inference():
    """Test that logical inference returns Japanese when given Japanese input."""
    print("\n" + "="*60)
    print("Testing Logical Inference with Japanese Input")
    print("="*60)
    
    from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available. Check API key.")
        return False
        
    engine = LogicalInferenceEngine(genai_client=genai_client)
    
    # Japanese input
    japanese_idea = "太陽光パネルを備えた移動式浄水システムで、災害時にも使用可能"
    
    print(f"入力アイデア: {japanese_idea}")
    print(f"トピック: 持続可能なエネルギー")
    print(f"コンテキスト: 発展途上国向けの低コスト")
    print("\n論理推論を実行中... (これには時間がかかる場合があります)")
    
    start_time = time.time()
    
    # Analyze with logical inference
    result = engine.analyze(
        idea=japanese_idea,
        topic="持続可能なエネルギー",
        context="発展途上国向けの低コスト",
        analysis_type=InferenceType.FULL
    )
    
    elapsed = time.time() - start_time
    print(f"\n✅ 推論完了 (所要時間: {elapsed:.1f}秒)")
    
    if elapsed < 5:
        print("⚠️ WARNING: Completed too quickly. Might be using mock mode!")
    
    # Check the result
    print("\n=== 結果分析 ===")
    print(f"Result type: {type(result)}")
    
    # Check each field for Japanese content
    fields_to_check = ['causal_chains', 'constraint_satisfaction', 'contradictions', 'implications']
    
    for field in fields_to_check:
        if hasattr(result, field):
            value = getattr(result, field)
            if value:
                print(f"\n{field}:")
                preview = str(value)[:200]
                print(f"  Preview: {preview}...")
                
                # Check for Japanese characters
                has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' for char in str(value))
                if has_japanese:
                    print(f"  ✅ {field} contains Japanese")
                else:
                    print(f"  ❌ {field} does NOT contain Japanese")
                    if len(str(value)) < 500:
                        print(f"  Full content: {value}")
    
    return True


def test_idea_improvement_language():
    """Test that idea improvements maintain language consistency."""
    print("\n" + "="*60)
    print("Testing Idea Improvement Language Consistency")
    print("="*60)
    
    from madspark.agents.idea_generator import improve_idea
    
    # Japanese input
    original_idea = "ソーラーパネル付き浄水器"
    critique = "技術的には実現可能だが、初期コストが高い"
    advocacy = "環境に優しく、長期的にはコスト削減"
    skepticism = "メンテナンスが困難な地域では持続性に課題"
    
    print(f"Original idea: {original_idea}")
    print(f"Critique: {critique}")
    print("\n改善を実行中...")
    
    start_time = time.time()
    
    improved = improve_idea(
        original_idea=original_idea,
        critique=critique,
        advocacy_points=advocacy,
        skeptic_points=skepticism,
        topic="持続可能なエネルギー",
        context="低コスト",
        temperature=0.7
    )
    
    elapsed = time.time() - start_time
    print(f"\n✅ 改善完了 (所要時間: {elapsed:.1f}秒)")
    
    print(f"\nImproved idea preview: {improved[:200]}...")
    
    # Check for Japanese
    has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' for char in improved)
    if has_japanese:
        print("✅ Improved idea is in Japanese")
    else:
        print("❌ Improved idea is NOT in Japanese")
        print(f"Full improved idea:\n{improved}")
    
    return has_japanese


def main():
    """Run all Japanese language tests."""
    print("="*60)
    print("JAPANESE LANGUAGE OUTPUT TESTING")
    print("="*60)
    
    # Check API key
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real Google API key not found")
        return 1
    
    print(f"✅ Using API key: {api_key[:10]}...")
    print("\n⚠️ NOTE: Each test may take several minutes with real API.")
    print("If tests complete in seconds, it's using mock mode!\n")
    
    # Run tests
    tests_passed = []
    
    # Test 1: Multi-dimensional evaluation
    try:
        result = test_japanese_multidimensional_evaluation()
        tests_passed.append(('Multi-dimensional Evaluation', result))
    except Exception as e:
        print(f"❌ Multi-dimensional evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        tests_passed.append(('Multi-dimensional Evaluation', False))
    
    # Test 2: Logical inference
    try:
        result = test_japanese_logical_inference()
        tests_passed.append(('Logical Inference', result))
    except Exception as e:
        print(f"❌ Logical inference test failed: {e}")
        import traceback
        traceback.print_exc()
        tests_passed.append(('Logical Inference', False))
    
    # Test 3: Idea improvement
    try:
        result = test_idea_improvement_language()
        tests_passed.append(('Idea Improvement', result))
    except Exception as e:
        print(f"❌ Idea improvement test failed: {e}")
        import traceback
        traceback.print_exc()
        tests_passed.append(('Idea Improvement', False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in tests_passed:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} : {status}")
    
    all_passed = all(result for _, result in tests_passed)
    if all_passed:
        print("\n✅ ALL TESTS PASSED - Japanese output confirmed!")
    else:
        print("\n❌ SOME TESTS FAILED - Language consistency issues detected!")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())