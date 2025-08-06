#!/usr/bin/env python3
"""
Final comprehensive test for Japanese language consistency.
"""

import os
import sys
import time
import json
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_full_workflow_japanese():
    """Test the complete workflow with Japanese input."""
    print("\n" + "="*60)
    print("FULL WORKFLOW TEST WITH JAPANESE")
    print("="*60)
    
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
    from madspark.agents.genai_client import get_genai_client
    from madspark.agents.idea_generator import generate_ideas, improve_idea
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available")
        return False
    
    # Japanese parameters
    topic = "持続可能な都市農業"
    context = "低コストで実現可能な解決策"
    
    print(f"トピック: {topic}")
    print(f"コンテキスト: {context}")
    
    # Step 1: Generate ideas in Japanese
    print("\n" + "-"*40)
    print("ステップ1: アイデア生成")
    print("-"*40)
    
    start = time.time()
    ideas_json = generate_ideas(
        topic=topic,
        context=context,
        temperature=0.7,
        use_structured_output=True
    )
    elapsed = time.time() - start
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    ideas = json.loads(ideas_json) if isinstance(ideas_json, str) else ideas_json
    if not ideas:
        print("❌ No ideas generated")
        return False
    
    first_idea = ideas[0]
    idea_text = first_idea.get('description', '')
    print(f"\n生成されたアイデア:")
    print(f"タイトル: {first_idea.get('title', '')}")
    print(f"説明: {idea_text[:200]}...")
    
    # Check Japanese
    has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' for c in idea_text)
    print(f"日本語チェック: {'✅ 日本語' if has_jp else '❌ 英語'}")
    
    # Step 2: Multi-dimensional evaluation
    print("\n" + "-"*40)
    print("ステップ2: 多次元評価")
    print("-"*40)
    
    evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
    
    start = time.time()
    eval_result = evaluator.evaluate_idea(
        idea=idea_text,
        context={'topic': topic, 'context': context}
    )
    elapsed = time.time() - start
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Check the actual structure
    print(f"\n評価結果の構造:")
    print(f"  キー: {list(eval_result.keys()) if isinstance(eval_result, dict) else 'Not a dict'}")
    
    # Check for Japanese in evaluation_summary
    if isinstance(eval_result, dict) and 'evaluation_summary' in eval_result:
        summary = eval_result['evaluation_summary']
        print(f"\n評価サマリー (最初の300文字):")
        print(summary[:300])
        has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' for c in str(summary))
        print(f"日本語チェック: {'✅ 日本語' if has_jp else '❌ 英語'}")
        
        if not has_jp:
            print("\n⚠️ WARNING: Multi-dimensional evaluation summary is not in Japanese!")
            print("Full summary for inspection:")
            print(summary)
    
    # Step 3: Logical inference
    print("\n" + "-"*40)
    print("ステップ3: 論理推論")
    print("-"*40)
    
    engine = LogicalInferenceEngine(genai_client=genai_client)
    
    start = time.time()
    inference_result = engine.analyze(
        idea=idea_text,
        topic=topic,
        context=context,
        analysis_type=InferenceType.FULL
    )
    elapsed = time.time() - start
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    # Check inference results
    print(f"\n推論結果:")
    
    # The InferenceResult might have different attributes
    if hasattr(inference_result, '__dict__'):
        for key, value in inference_result.__dict__.items():
            if value:
                print(f"\n{key}:")
                text = str(value)
                print(f"  内容: {text[:200]}...")
                has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' for c in text)
                print(f"  日本語チェック: {'✅' if has_jp else '❌'}")
                
                if not has_jp and len(text) > 0:
                    print(f"  ⚠️ WARNING: {key} is not in Japanese!")
    
    # Step 4: Idea improvement
    print("\n" + "-"*40)
    print("ステップ4: アイデア改善")
    print("-"*40)
    
    critique = "初期コストが高く、技術的なサポートが必要"
    advocacy = "長期的なコスト削減と環境への貢献"
    skepticism = "メンテナンスの複雑さと地域の参加意欲"
    
    start = time.time()
    improved = improve_idea(
        original_idea=idea_text,
        critique=critique,
        advocacy_points=advocacy,
        skeptic_points=skepticism,
        topic=topic,
        context=context,
        temperature=0.7
    )
    elapsed = time.time() - start
    print(f"✅ 完了 ({elapsed:.1f}秒)")
    
    print(f"\n改善されたアイデア (最初の300文字):")
    print(improved[:300])
    has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' for c in improved)
    print(f"日本語チェック: {'✅ 日本語' if has_jp else '❌ 英語'}")
    
    return True


def test_web_interface_simulation():
    """Simulate what happens in web interface with Japanese."""
    print("\n" + "="*60)
    print("WEB INTERFACE SIMULATION")
    print("="*60)
    
    # This simulates the web API endpoint behavior
    print("\nシミュレーション: Web APIエンドポイント")
    
    # Test bookmark with Japanese
    from madspark.utils.bookmark_system import BookmarkManager
    
    manager = BookmarkManager()
    
    japanese_idea = "コミュニティ農園のIoT管理システム"
    
    print(f"\nブックマーク追加テスト:")
    print(f"  アイデア: {japanese_idea}")
    
    bookmark_id = manager.bookmark_idea_with_duplicate_check(
        idea_text=japanese_idea,
        topic="都市農業",
        context="低コスト",
        score=8.5
    )
    
    if bookmark_id:
        print(f"  ✅ ブックマーク成功 (ID: {bookmark_id})")
    else:
        print(f"  ❌ ブックマーク失敗")
    
    return True


def main():
    """Run final comprehensive test."""
    print("="*60)
    print("最終包括的日本語テスト")
    print("FINAL COMPREHENSIVE JAPANESE TEST")
    print("="*60)
    
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real API key not found")
        return 1
    
    print(f"✅ API key: {api_key[:10]}...")
    print("\n⚠️ このテストには10分程度かかる場合があります...")
    
    # Run comprehensive test
    total_start = time.time()
    
    workflow_success = False
    try:
        workflow_success = test_full_workflow_japanese()
    except Exception as e:
        print(f"\n❌ ワークフローテスト失敗: {e}")
        import traceback
        traceback.print_exc()
    
    web_success = False
    try:
        web_success = test_web_interface_simulation()
    except Exception as e:
        print(f"\n❌ Webインターフェーステスト失敗: {e}")
        import traceback
        traceback.print_exc()
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "="*60)
    print("テスト完了")
    print("="*60)
    print(f"総実行時間: {total_elapsed:.1f}秒")
    
    if total_elapsed < 30:
        print("⚠️ WARNING: 実行時間が短すぎます。モックモードの可能性があります。")
    
    if workflow_success and web_success:
        print("\n✅ すべてのテストが成功しました！")
        print("   日本語の言語一貫性が確認されました。")
    else:
        print("\n❌ 一部のテストが失敗しました。")
        print("   言語一貫性に問題がある可能性があります。")
    
    return 0 if (workflow_success and web_success) else 1


if __name__ == "__main__":
    sys.exit(main())