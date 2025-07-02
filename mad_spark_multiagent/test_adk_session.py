#!/usr/bin/env python3
"""Test ADK sessions and runner."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk import Agent, Runner
    import google.adk.sessions
    import google.generativeai as genai
    
    # Configure API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ API key configured")
    
    # Check available session services
    print("Available session services:")
    print(dir(google.adk.sessions))
    
    # Create agent
    test_agent = Agent(
        name="test_generator",
        model="gemini-2.0-flash",
        description="Test idea generator",
        instruction="You generate creative ideas based on themes."
    )
    
    # Try to find and create a session service
    session_service = None
    for attr_name in dir(google.adk.sessions):
        if 'Session' in attr_name and not attr_name.startswith('_'):
            try:
                SessionClass = getattr(google.adk.sessions, attr_name)
                if callable(SessionClass):
                    session_service = SessionClass()
                    print(f"✅ Created {attr_name}: {session_service}")
                    break
            except Exception as e:
                print(f"❌ Failed to create {attr_name}: {e}")
                continue
    
    if not session_service:
        print("No working session service found, trying with None")
        session_service = None
    
    # Create runner
    runner = Runner(
        app_name="test_app",
        agent=test_agent,
        session_service=session_service
    )
    print(f"✅ Runner created: {runner}")
    
    # Test the run method
    test_prompt = "Generate 3 creative ideas for transportation."
    print(f"Testing with prompt: {test_prompt}")
    
    result = runner.run(test_prompt)
    print(f"Runner.run result: {result}")
    print(f"Result type: {type(result)}")
    
    # Extract content
    if hasattr(result, 'content'):
        print(f"Content: {result.content}")
        print("✅ ADK Runner approach works!")
    elif hasattr(result, 'text'):
        print(f"Text: {result.text}")
        print("✅ ADK Runner approach works!")
    elif hasattr(result, 'message'):
        print(f"Message: {result.message}")
        print("✅ ADK Runner approach works!")
    elif isinstance(result, str):
        print(f"String result: {result}")
        print("✅ ADK Runner approach works!")
    else:
        print(f"Unknown result format: {result}")
        print("❌ Unexpected result format")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()