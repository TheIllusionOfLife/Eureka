#!/usr/bin/env python3
"""Test how to configure API key for ADK agents."""
import os
from dotenv import load_dotenv
import inspect

load_dotenv()

try:
    from google.adk.agents import Agent
    import google.generativeai as genai
    
    # Check Agent constructor parameters
    print("Agent constructor signature:")
    print(inspect.signature(Agent.__init__))
    
    # Check if Agent has API key related parameters
    print("\nAgent parameters:")
    sig = inspect.signature(Agent.__init__)
    for param_name, param in sig.parameters.items():
        if 'key' in param_name.lower() or 'auth' in param_name.lower() or 'config' in param_name.lower():
            print(f"  {param_name}: {param}")
    
    # Check all parameters
    print("\nAll Agent parameters:")
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation}")
    
    # Try to create agent with different configurations
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"\nTesting with API key: {api_key[:10]}...")
        
        # Test basic agent
        try:
            agent = Agent(
                name="test",
                model="gemini-2.0-flash",
                description="Test",
                instruction="Test instruction"
            )
            print("✅ Basic agent created")
        except Exception as e:
            print(f"❌ Basic agent failed: {e}")
        
        # Test with generate_content_config
        try:
            # Configure genai first
            genai.configure(api_key=api_key)
            
            agent = Agent(
                name="test",
                model="gemini-2.0-flash",
                description="Test",
                instruction="Test instruction",
                generate_content_config=genai.types.GenerationConfig(temperature=0.7)
            )
            print("✅ Agent with config created")
        except Exception as e:
            print(f"❌ Agent with config failed: {e}")
            
    else:
        print("No API key found")
        
except ImportError as e:
    print(f"ADK not available: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()