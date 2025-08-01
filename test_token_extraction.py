"""Test token usage extraction from Gemini API responses."""
from madspark.agents.genai_client import get_genai_client, get_model_name
from google.genai import types

# Test API response structure
client = get_genai_client()
model_name = get_model_name()

if client:
    print('🔍 Testing Gemini API response structure')
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Generate a short test response about urban planning.",
            config=types.GenerateContentConfig(temperature=0.3)
        )
        
        print(f'✅ Response received')
        print(f'📝 Text length: {len(response.text) if response.text else 0} chars')
        
        # Check for usage metadata
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            print(f'🔤 Usage metadata found:')
            print(f'   Input tokens: {usage.prompt_token_count if hasattr(usage, "prompt_token_count") else "N/A"}')
            print(f'   Output tokens: {usage.candidates_token_count if hasattr(usage, "candidates_token_count") else "N/A"}')
            print(f'   Total tokens: {usage.total_token_count if hasattr(usage, "total_token_count") else "N/A"}')
        else:
            print('⚠️  No usage_metadata found in response')
            print(f'📋 Available attributes: {[attr for attr in dir(response) if not attr.startswith("_")]}')
            
        # Check candidates for usage info
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f'📊 Candidate attributes: {[attr for attr in dir(candidate) if not attr.startswith("_")]}')
            
    except Exception as e:
        print(f'❌ API test failed: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ No API client available')