#!/usr/bin/env python3
"""
Test the fixed multi-dimensional evaluation summary for language consistency.
"""

import os
import sys
import time
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_fixed_summary():
    """Test that the summary is now in Japanese."""
    print("\n" + "="*60)
    print("TESTING FIXED MULTI-DIMENSIONAL EVALUATION SUMMARY")
    print("="*60)
    
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available")
        return False
    
    evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
    
    # Japanese input
    japanese_idea = "地域住民が共同で管理する屋上農園システム"
    
    context = {
        'topic': '持続可能な都市農業',
        'context': '低コストで実現可能な解決策'
    }
    
    print(f"入力アイデア: {japanese_idea}")
    print(f"トピック: {context['topic']}")
    print(f"コンテキスト: {context['context']}")
    print("\n評価を実行中...")
    
    start_time = time.time()
    result = evaluator.evaluate_idea(idea=japanese_idea, context=context)
    elapsed = time.time() - start_time
    
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Check the evaluation_summary
    if isinstance(result, dict) and 'evaluation_summary' in result:
        summary = result['evaluation_summary']
        print("\n" + "="*40)
        print("評価サマリー:")
        print("="*40)
        print(summary)
        print("="*40)
        
        # Check for Japanese characters
        has_japanese = any('\u3000' <= char <= '\u9fff' or '\uff00' <= char <= '\uffef' 
                          for char in summary)
        
        if has_japanese:
            print("\n✅ SUCCESS: Summary is now in Japanese!")
            return True
        else:
            print("\n❌ FAILED: Summary is still in English")
            return False
    else:
        print("\n❌ ERROR: No evaluation_summary in result")
        return False


def main():
    """Run the test."""
    print("="*60)
    print("MULTI-DIMENSIONAL EVALUATION SUMMARY FIX TEST")
    print("="*60)
    
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real API key not found")
        return 1
    
    print(f"✅ API key: {api_key[:10]}...")
    
    success = test_fixed_summary()
    
    if success:
        print("\n✅ FIX CONFIRMED: Multi-dimensional evaluation summary now responds in Japanese!")
    else:
        print("\n❌ FIX FAILED: Summary is still not in Japanese")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())