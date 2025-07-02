#!/usr/bin/env python3
"""Test ADK Agent methods to find the correct one."""
import os
from dotenv import load_dotenv

load_dotenv()

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
        exit(1)
    
    # Create a simple agent
    test_agent = Agent(
        name="test",
        model="gemini-2.0-flash", 
        description="Test agent",
        instruction="You are a helpful assistant. Answer questions briefly."
    )
    
    test_prompt = "What is 2+2?"
    
    print(f"Testing agent methods with prompt: '{test_prompt}'")
    
    # Test run_live method
    try:
        print("\n=== Testing run_live method ===")
        result = test_agent.run_live(test_prompt)
        print(f"run_live result type: {type(result)}")
        print(f"run_live result: {result}")
        
        # Check if result has content attribute
        if hasattr(result, 'content'):
            print(f"result.content: {result.content}")
        if hasattr(result, 'text'):
            print(f"result.text: {result.text}")
        if hasattr(result, 'message'):
            print(f"result.message: {result.message}")
            
    except Exception as e:
        print(f"run_live failed: {e}")
    
    # Test run_async method (might need await)
    try:
        print("\n=== Testing run_async method ===")
        result = test_agent.run_async(test_prompt)
        print(f"run_async result type: {type(result)}")
        print(f"run_async result: {result}")
    except Exception as e:
        print(f"run_async failed: {e}")
        
except ImportError as e:
    print(f"ADK not available: {e}")
except Exception as e:
    print(f"Error testing ADK: {e}")