#!/usr/bin/env python3
"""Test global ADK configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.adk
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"Testing with API key: {api_key[:10]}...")
        
        # Configure genai first
        genai.configure(api_key=api_key)
        print("✅ genai configured")
        
        # Check if there's a global ADK configuration
        print("\nADK module attributes:")
        for attr in dir(google.adk):
            if 'config' in attr.lower() or 'auth' in attr.lower() or 'key' in attr.lower():
                print(f"  {attr}: {getattr(google.adk, attr)}")
        
        # Check if genai configuration affects ADK
        print("\nTesting agent creation after genai.configure:")
        from google.adk.agents import Agent
        
        agent = Agent(
            name="test",
            model="gemini-2.0-flash",
            description="Test",
            instruction="Test instruction"
        )
        
        print(f"Agent created: {agent}")
        print(f"Agent model: {agent.model}")
        
        # Check if the agent has access to API configuration
        if hasattr(agent, 'generate_content_config'):
            print(f"Agent config: {agent.generate_content_config}")
        
        # Check what happens when we try to access the model
        try:
            # Try to see if there's a way to check if API key is configured
            # Look for any model-related attributes
            for attr in dir(agent):
                if 'model' in attr.lower() or 'api' in attr.lower() or 'config' in attr.lower():
                    print(f"Agent.{attr}: {getattr(agent, attr)}")
        except Exception as e:
            print(f"Error inspecting agent: {e}")
            
    else:
        print("No API key found")
        
except ImportError as e:
    print(f"ADK not available: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()