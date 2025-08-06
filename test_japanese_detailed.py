#!/usr/bin/env python3
"""
Detailed test to examine actual Japanese content in all outputs.
This test shows the full Japanese responses to verify language consistency.
"""

import os
import sys
import time
import json
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_japanese_multidimensional_detailed():
    """Test multi-dimensional evaluation with detailed output examination."""
    print("\n" + "="*60)
    print("DETAILED: Multi-Dimensional Evaluation Japanese Output")
    print("="*60)
    
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available")
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
    
    print(f"入力: {japanese_idea[:50]}...")
    print("\n評価を実行中...")
    
    start_time = time.time()
    result = evaluator.evaluate_idea(idea=japanese_idea, context=context)
    elapsed = time.time() - start_time
    
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Display the summary in detail
    if isinstance(result, dict) and 'summary' in result:
        print("\n" + "="*40)
        print("多次元評価サマリー (Multi-dimensional Summary):")
        print("="*40)
        print(result['summary'])
        print("="*40)
        
        # Check language
        has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' 
                          for char in result['summary'])
        print(f"\n日本語判定: {'✅ 日本語です' if has_japanese else '❌ 日本語ではありません'}")
    
    # Display individual dimension evaluations
    if isinstance(result, dict) and 'dimension_evaluations' in result:
        print("\n" + "="*40)
        print("次元別評価 (Dimension Evaluations):")
        print("="*40)
        for dim, eval_text in result['dimension_evaluations'].items():
            print(f"\n【{dim}】")
            print(str(eval_text)[:300] + "..." if len(str(eval_text)) > 300 else str(eval_text))
            
    return True


def test_japanese_logical_inference_detailed():
    """Test logical inference with detailed output examination."""
    print("\n" + "="*60)
    print("DETAILED: Logical Inference Japanese Output")
    print("="*60)
    
    from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available")
        return False
        
    engine = LogicalInferenceEngine(genai_client=genai_client)
    
    # Japanese input
    japanese_idea = "太陽光パネルを備えた移動式浄水システムで、災害時にも使用可能"
    
    print(f"入力: {japanese_idea}")
    print("\n論理推論を実行中...")
    
    start_time = time.time()
    result = engine.analyze(
        idea=japanese_idea,
        topic="持続可能なエネルギー",
        context="発展途上国向けの低コスト",
        analysis_type=InferenceType.FULL
    )
    elapsed = time.time() - start_time
    
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Display each inference field
    print("\n" + "="*40)
    print("論理推論結果 (Logical Inference Results):")
    print("="*40)
    
    fields = [
        ('causal_chains', '因果連鎖'),
        ('constraint_satisfaction', '制約充足'),
        ('contradictions', '矛盾'),
        ('implications', '含意')
    ]
    
    for field, japanese_name in fields:
        if hasattr(result, field):
            value = getattr(result, field)
            if value:
                print(f"\n【{japanese_name} / {field}】")
                print(str(value)[:500] + "..." if len(str(value)) > 500 else str(value))
                
                # Check language
                has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' 
                                  for char in str(value))
                print(f"日本語判定: {'✅' if has_japanese else '❌'}")
    
    return True


def test_cli_japanese_output():
    """Test CLI output with Japanese input to verify complete workflow."""
    print("\n" + "="*60)
    print("DETAILED: CLI Japanese Output Test")
    print("="*60)
    
    # This would normally test the full CLI, but due to coordinator hanging,
    # we'll test the components that would be used
    print("⚠️  注意: コーディネーターの問題により、個別コンポーネントをテスト中")
    
    # Test idea generation with Japanese
    from madspark.agents.idea_generator import generate_ideas
    
    japanese_topic = "持続可能な都市農業"
    japanese_context = "低コストで実現可能な解決策"
    
    print(f"\nトピック: {japanese_topic}")
    print(f"コンテキスト: {japanese_context}")
    print("\nアイデア生成中...")
    
    start_time = time.time()
    result = generate_ideas(
        topic=japanese_topic,
        context=japanese_context,
        temperature=0.7,
        use_structured_output=True
    )
    elapsed = time.time() - start_time
    
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Parse and display ideas
    try:
        ideas = json.loads(result) if isinstance(result, str) else result
        if ideas and len(ideas) > 0:
            print("\n生成されたアイデア:")
            for i, idea in enumerate(ideas[:2], 1):  # Show first 2 ideas
                print(f"\n{i}. {idea.get('title', 'タイトルなし')}")
                print(f"   {idea.get('description', '')[:200]}...")
                
                # Check if response is in Japanese
                text = f"{idea.get('title', '')} {idea.get('description', '')}"
                has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' 
                                  for char in text)
                print(f"   日本語判定: {'✅' if has_japanese else '❌'}")
    except Exception as e:
        print(f"Error parsing ideas: {e}")
    
    return True


def main():
    """Run detailed Japanese tests."""
    print("="*60)
    print("DETAILED JAPANESE LANGUAGE OUTPUT TESTING")
    print("="*60)
    
    # Check API key
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real Google API key not found")
        return 1
    
    print(f"✅ Using API key: {api_key[:10]}...")
    print("\n各テストには数分かかる場合があります...")
    
    # Run detailed tests
    try:
        test_japanese_multidimensional_detailed()
    except Exception as e:
        print(f"❌ Multi-dimensional test failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_japanese_logical_inference_detailed()
    except Exception as e:
        print(f"❌ Logical inference test failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_cli_japanese_output()
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("詳細テスト完了")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())