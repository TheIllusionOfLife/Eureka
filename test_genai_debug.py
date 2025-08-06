#!/usr/bin/env python3
"""
Debug the GenAI client response for multi-dimensional evaluation summary.
"""

import os
import sys
sys.path.insert(0, 'src')

# Set environment for real API
os.environ['MADSPARK_MODE'] = 'api'

def test_direct_genai_call():
    """Test direct GenAI client call."""
    print("\n" + "="*60)
    print("TESTING DIRECT GENAI CLIENT CALL")
    print("="*60)
    
    from madspark.agents.genai_client import get_genai_client, get_model_name
    from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
    
    genai_client = get_genai_client()
    if not genai_client:
        print("❌ ERROR: GenAI client not available")
        return False
    
    model_name = get_model_name()
    print(f"Model name: {model_name}")
    
    # Test simple prompt
    prompt = f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}

Based on the multi-dimensional evaluation scores below, provide a concise summary of the evaluation.

Idea: 地域住民が共同で管理する屋上農園システム

Evaluation Scores:
- Average Score: 6.5/10
- Strongest Dimension: cost_effectiveness (score: 8.0)
- Weakest Dimension: risk_assessment (score: 3.0)
- All Scores: feasibility: 7.0, innovation: 6.0, impact: 7.0, cost_effectiveness: 8.0, scalability: 5.0, risk_assessment: 3.0, timeline: 6.0

Provide a brief 1-2 sentence summary that captures the overall assessment, highlighting the strongest aspect and area for improvement.
"""
    
    print(f"\nPrompt (first 200 chars):\n{prompt[:200]}...")
    
    try:
        # Try with genai types
        from google import genai
        
        config = genai.types.GenerateContentConfig(
            temperature=0.3,
            candidate_count=1,
            max_output_tokens=200
        )
        
        print("\nCalling generate_content...")
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        print(f"Response type: {type(response)}")
        print(f"Has text attr: {hasattr(response, 'text')}")
        
        if hasattr(response, 'text'):
            print(f"Response text type: {type(response.text)}")
            print(f"Response text: {response.text}")
            
            if response.text:
                # Check for Japanese
                has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' 
                            for c in response.text)
                print(f"Has Japanese: {has_jp}")
                return has_jp
        else:
            print("Response has no 'text' attribute")
            print(f"Response dir: {dir(response)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return False


def test_without_config():
    """Test without GenerateContentConfig."""
    print("\n" + "="*60)
    print("TESTING WITHOUT CONFIG")
    print("="*60)
    
    from madspark.agents.genai_client import get_genai_client, get_model_name
    
    genai_client = get_genai_client()
    model_name = get_model_name()
    
    prompt = """日本語で答えてください。

アイデア: 地域住民が共同で管理する屋上農園システム

このアイデアの評価を1-2文で要約してください。"""
    
    print(f"Simple prompt: {prompt}")
    
    try:
        # Simple call without config
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        if hasattr(response, 'text') and response.text:
            print(f"\nResponse: {response.text}")
            has_jp = any('\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef' 
                        for c in response.text)
            print(f"Has Japanese: {has_jp}")
            return has_jp
        else:
            print("No text in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False


def main():
    """Run debug tests."""
    print("="*60)
    print("GENAI CLIENT DEBUG")
    print("="*60)
    
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key or api_key == 'test_api_key':
        print("❌ ERROR: Real API key not found")
        return 1
    
    print(f"✅ API key: {api_key[:10]}...")
    
    # Test with config
    success1 = test_direct_genai_call()
    
    # Test without config
    success2 = test_without_config()
    
    if success1 or success2:
        print("\n✅ At least one test succeeded in getting Japanese response")
    else:
        print("\n❌ Both tests failed to get Japanese response")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())