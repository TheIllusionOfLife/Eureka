#!/usr/bin/env python3
"""Test ADK Agent input schema."""
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
    
    # Create a simple agent
    test_agent = Agent(
        name="test",
        model="gemini-2.0-flash",
        description="Test agent",
        instruction="You are a helpful assistant."
    )
    
    print(f"Agent input schema:")
    if hasattr(test_agent, 'input_schema'):
        print(test_agent.input_schema)
    
    print(f"\nAgent schema:")
    if hasattr(test_agent, 'schema'):
        schema = test_agent.schema()
        print(schema)
    
    print(f"\nAgent model fields:")
    if hasattr(test_agent, 'model_fields'):
        print(test_agent.model_fields)
    
    # Try to find message-related modules in ADK
    import google.adk
    print(f"\nADK submodules:")
    for attr in dir(google.adk):
        if not attr.startswith('_'):
            try:
                module = getattr(google.adk, attr)
                print(f"  {attr}: {type(module)}")
                if hasattr(module, '__all__'):
                    print(f"    exports: {module.__all__}")
            except:
                pass
                
except ImportError as e:
    print(f"ADK not available: {e}")
except Exception as e:
    print(f"Error: {e}")