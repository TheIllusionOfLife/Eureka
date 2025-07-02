#!/usr/bin/env python3
"""Test simple ADK approach with synchronous wrapper."""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

def run_adk_agent_sync(agent, prompt):
    """Synchronous wrapper for ADK agent execution."""
    async def _run():
        full_response = ""
        try:
            async for chunk in agent.run_live(prompt):
                # Try to extract text from chunk
                if hasattr(chunk, 'content'):
                    full_response += str(chunk.content)
                elif hasattr(chunk, 'text'):
                    full_response += str(chunk.text)
                elif isinstance(chunk, str):
                    full_response += chunk
                else:
                    full_response += str(chunk)
        except Exception as e:
            return f"Error: {e}"
        return full_response
    
    # Run the async function synchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run())
        return result
    finally:
        loop.close()

def test_simple_adk():
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
        
        # Create agent like in the actual code
        test_agent = Agent(
            name="test_generator",
            model="gemini-2.0-flash",
            description="Test idea generator",
            instruction="You generate creative ideas based on themes."
        )
        
        # Test with a simple prompt
        test_prompt = "Generate 3 creative ideas for space travel."
        print(f"Testing with prompt: {test_prompt}")
        
        result = run_adk_agent_sync(test_agent, test_prompt)
        print(f"Result: {result}")
        
        if "Error:" not in result:
            print("✅ ADK sync wrapper works!")
            return True
        else:
            print("❌ ADK sync wrapper failed")
            return False
            
    except ImportError as e:
        print(f"ADK not available: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_simple_adk()