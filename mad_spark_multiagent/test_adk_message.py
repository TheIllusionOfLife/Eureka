#!/usr/bin/env python3
"""Test ADK Agent with proper message format."""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_adk_with_message():
    try:
        from google.adk.agents import Agent
        import google.generativeai as genai
        
        # Configure API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            print("✅ API key configured")
        else:
            print("❌ No API key found")
            return
        
        # Create a simple agent
        test_agent = Agent(
            name="test",
            model="gemini-2.0-flash",
            description="Test agent",
            instruction="You are a helpful assistant. Answer questions briefly."
        )
        
        # Try different message formats
        test_inputs = [
            "What is 2+2?",  # Plain string
            {"content": "What is 2+2?"},  # Dict format
            {"message": "What is 2+2?"},  # Different dict format
            {"text": "What is 2+2?"},  # Another dict format
        ]
        
        for i, test_input in enumerate(test_inputs):
            print(f"\n=== Test {i+1}: {type(test_input)} ===")
            print(f"Input: {test_input}")
            
            try:
                async for chunk in test_agent.run_live(test_input):
                    print(f"Success! Chunk type: {type(chunk)}")
                    print(f"Chunk: {chunk}")
                    
                    # Try to extract content
                    content = None
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                    elif hasattr(chunk, 'text'):
                        content = chunk.text
                    elif hasattr(chunk, 'message'):
                        content = chunk.message
                    elif isinstance(chunk, str):
                        content = chunk
                    
                    print(f"Extracted content: {content}")
                    break  # Just get first chunk
                    
                print("✅ This format worked!")
                break  # Stop testing once we find a working format
                
            except Exception as e:
                print(f"❌ Failed with error: {e}")
                continue
                
    except ImportError as e:
        print(f"ADK not available: {e}")
    except Exception as e:
        print(f"Error testing ADK: {e}")

if __name__ == "__main__":
    asyncio.run(test_adk_with_message())