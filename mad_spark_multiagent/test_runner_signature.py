#!/usr/bin/env python3
"""Test Runner method signatures."""
import os
import inspect
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk import Agent, Runner
    from google.adk.sessions import InMemorySessionService
    import google.generativeai as genai
    
    # Configure API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ API key configured")
    
    # Create agent and session service
    test_agent = Agent(
        name="test_generator",
        model="gemini-2.0-flash",
        description="Test idea generator",
        instruction="You generate creative ideas based on themes."
    )
    
    session_service = InMemorySessionService()
    
    # Create runner
    runner = Runner(
        app_name="test_app",
        agent=test_agent,
        session_service=session_service
    )
    
    # Inspect run method signature
    print("Runner.run signature:")
    print(inspect.signature(runner.run))
    
    # Check run method docstring
    print(f"\nRunner.run docstring:")
    print(runner.run.__doc__)
    
    # Try calling run without arguments
    print(f"\nTrying runner.run() with no arguments...")
    try:
        result = runner.run()
        print(f"No-arg result: {result}")
    except Exception as e:
        print(f"No-arg failed: {e}")
    
    # Try calling run with session_id
    print(f"\nTrying runner.run() with session_id...")
    try:
        result = runner.run(session_id="test_session")
        print(f"Session result: {result}")
    except Exception as e:
        print(f"Session failed: {e}")
        
    # Check if runner has other methods for sending messages
    print(f"\nRunner methods containing 'send' or 'message':")
    for method_name in dir(runner):
        if 'send' in method_name.lower() or 'message' in method_name.lower():
            method = getattr(runner, method_name)
            if callable(method):
                print(f"  {method_name}: {inspect.signature(method)}")
                
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()