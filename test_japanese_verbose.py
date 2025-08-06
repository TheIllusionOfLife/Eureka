#!/usr/bin/env python3
"""
Verbose test to capture all Japanese output details.
"""

import os
import sys
import time
import json
from pprint import pprint
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_multidimensional_with_debug():
    """Test with full debug output."""
    print("\n" + "="*60)
    print("VERBOSE: Multi-Dimensional Evaluation")
    print("="*60)
    
    from madspark.core.enhanced_reasoning import MultiDimensionalEvaluator
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        return False
    
    evaluator = MultiDimensionalEvaluator(genai_client=genai_client)
    
    # Japanese input
    japanese_idea = "地域住民が共同で管理する屋上農園システム"
    
    context = {
        'topic': '持続可能な都市農業',
        'context': '低コストで実現可能'
    }
    
    print(f"Input: {japanese_idea}")
    start_time = time.time()
    result = evaluator.evaluate_idea(idea=japanese_idea, context=context)
    elapsed = time.time() - start_time
    print(f"Completed in {elapsed:.1f}s")
    
    print("\n--- Full Result Structure ---")
    print(f"Type: {type(result)}")
    
    if isinstance(result, dict):
        print(f"Keys: {list(result.keys())}")
        
        # Check summary
        if 'summary' in result:
            summary = result['summary']
            print(f"\n--- Summary (length: {len(summary)}) ---")
            print(summary[:500])
            if len(summary) > 500:
                print(f"... ({len(summary) - 500} more characters)")
            
            # Language check
            jp_chars = sum(1 for c in summary if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
            print(f"\nJapanese characters: {jp_chars}/{len(summary)} ({jp_chars*100//len(summary) if summary else 0}%)")
        else:
            print("\n⚠️ No 'summary' key in result")
        
        # Check dimensions
        if 'dimension_evaluations' in result:
            print(f"\n--- Dimension Evaluations ---")
            for dim, text in result['dimension_evaluations'].items():
                print(f"\n{dim}:")
                print(f"  First 200 chars: {str(text)[:200]}")
                jp_chars = sum(1 for c in str(text) if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
                print(f"  Japanese chars: {jp_chars}")
        else:
            print("\n⚠️ No 'dimension_evaluations' key")
    else:
        print(f"\n⚠️ Result is not a dict: {result}")
    
    return True


def test_logical_inference_with_debug():
    """Test logical inference with debug output."""
    print("\n" + "="*60)
    print("VERBOSE: Logical Inference")
    print("="*60)
    
    from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
    from madspark.agents.genai_client import get_genai_client
    
    genai_client = get_genai_client()
    if not genai_client:
        return False
        
    engine = LogicalInferenceEngine(genai_client=genai_client)
    
    japanese_idea = "太陽光発電付き移動式浄水器"
    
    print(f"Input: {japanese_idea}")
    start_time = time.time()
    result = engine.analyze(
        idea=japanese_idea,
        topic="持続可能エネルギー",
        context="低コスト",
        analysis_type=InferenceType.FULL
    )
    elapsed = time.time() - start_time
    print(f"Completed in {elapsed:.1f}s")
    
    print("\n--- Result Structure ---")
    print(f"Type: {type(result)}")
    print(f"Has causal_chains: {hasattr(result, 'causal_chains')}")
    print(f"Has constraint_satisfaction: {hasattr(result, 'constraint_satisfaction')}")
    print(f"Has contradictions: {hasattr(result, 'contradictions')}")
    print(f"Has implications: {hasattr(result, 'implications')}")
    
    # Check each field
    for field in ['causal_chains', 'constraint_satisfaction', 'contradictions', 'implications']:
        if hasattr(result, field):
            value = getattr(result, field)
            if value:
                print(f"\n--- {field} ---")
                text = str(value)
                print(f"Length: {len(text)}")
                print(f"First 300 chars: {text[:300]}")
                jp_chars = sum(1 for c in text if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
                print(f"Japanese chars: {jp_chars} ({jp_chars*100//len(text) if text else 0}%)")
            else:
                print(f"\n{field}: Empty/None")
    
    return True


def test_web_api_simulation():
    """Simulate what the web API would do with Japanese input."""
    print("\n" + "="*60)
    print("VERBOSE: Web API Simulation")
    print("="*60)
    
    # Test the same flow the web API would use
    from madspark.agents.idea_generator import generate_ideas
    from madspark.agents.critic import evaluate_ideas_batch
    
    topic = "持続可能な都市農業"
    context = "低コスト解決策"
    
    print(f"Topic: {topic}")
    print(f"Context: {context}")
    
    # Generate ideas
    print("\nGenerating ideas...")
    ideas_json = generate_ideas(
        topic=topic,
        context=context,
        temperature=0.7,
        use_structured_output=True
    )
    
    ideas = json.loads(ideas_json) if isinstance(ideas_json, str) else ideas_json
    if ideas:
        first_idea = ideas[0]
        print(f"\nFirst idea title: {first_idea.get('title', '')}")
        print(f"Description preview: {first_idea.get('description', '')[:200]}")
        
        # Check language
        text = f"{first_idea.get('title', '')} {first_idea.get('description', '')}"
        jp_chars = sum(1 for c in text if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
        print(f"Japanese characters: {jp_chars} ({jp_chars*100//len(text) if text else 0}%)")
        
        # Now evaluate
        print("\nEvaluating ideas...")
        eval_result = evaluate_ideas_batch(
            ideas=[first_idea.get('description', '')],
            topic=topic,
            context=context,
            temperature=0.7
        )
        
        print(f"\nEvaluation result type: {type(eval_result)}")
        if eval_result:
            print(f"First evaluation: {eval_result[0] if isinstance(eval_result, list) else eval_result}")
    
    return True


def main():
    """Run verbose tests."""
    print("="*60)
    print("VERBOSE JAPANESE OUTPUT TESTING")
    print("="*60)
    
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real API key not found")
        return 1
    
    print(f"✅ API key: {api_key[:10]}...")
    
    # Run tests
    test_multidimensional_with_debug()
    test_logical_inference_with_debug()
    test_web_api_simulation()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())