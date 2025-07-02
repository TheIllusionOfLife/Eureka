#!/usr/bin/env python3
"""Test ADK Agent async methods properly."""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_adk_methods():
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
        
        test_prompt = "What is 2+2?"
        
        print(f"Testing agent methods with prompt: '{test_prompt}'")
        
        # Test run_live method with async
        try:
            print("\n=== Testing run_live method (async) ===")
            async for chunk in test_agent.run_live(test_prompt):
                print(f"Chunk type: {type(chunk)}")
                print(f"Chunk: {chunk}")
                if hasattr(chunk, 'content'):
                    print(f"Content: {chunk.content}")
                if hasattr(chunk, 'text'):
                    print(f"Text: {chunk.text}")
                break  # Just get first chunk for testing
                
        except Exception as e:
            print(f"run_live failed: {e}")
        
        # Test run_async method
        try:
            print("\n=== Testing run_async method ===")
            async for chunk in test_agent.run_async(test_prompt):
                print(f"Chunk type: {type(chunk)}")
                print(f"Chunk: {chunk}")
                if hasattr(chunk, 'content'):
                    print(f"Content: {chunk.content}")
                if hasattr(chunk, 'text'):
                    print(f"Text: {chunk.text}")
                break  # Just get first chunk for testing
                
        except Exception as e:
            print(f"run_async failed: {e}")
            
    except ImportError as e:
        print(f"ADK not available: {e}")
    except Exception as e:
        print(f"Error testing ADK: {e}")

if __name__ == "__main__":
    asyncio.run(test_adk_methods())