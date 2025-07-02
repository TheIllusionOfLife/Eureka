#!/usr/bin/env python3
"""Test ADK with properly configured Runner."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk import Agent, Runner
    import google.generativeai as genai
    
    # Configure API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ API key configured")
    else:
        print("❌ No API key found")
        exit(1)
    
    # Create agent
    test_agent = Agent(
        name="test_generator",
        model="gemini-2.0-flash",
        description="Test idea generator",
        instruction="You generate creative ideas based on themes."
    )
    
    print(f"Agent created: {test_agent}")
    
    # Try to understand Runner constructor
    print("Trying different Runner configurations...")
    
    # Try minimal Runner setup
    try:
        # Check if we can import session services
        from google.adk.sessions import MemorySessionService
        session_service = MemorySessionService()
        
        runner = Runner(
            app_name="test_app",
            agent=test_agent,
            session_service=session_service
        )
        print(f"✅ Runner created successfully: {runner}")
        
        # Test the run method
        test_prompt = "Generate 3 creative ideas."
        print(f"Testing with prompt: {test_prompt}")
        
        result = runner.run(test_prompt)
        print(f"Runner.run result: {result}")
        print(f"Result type: {type(result)}")
        
        # Try to extract content
        if hasattr(result, 'content'):
            print(f"Content: {result.content}")
        elif hasattr(result, 'text'):
            print(f"Text: {result.text}")
        elif hasattr(result, 'message'):
            print(f"Message: {result.message}")
        
        print("✅ ADK Runner approach works!")
        
    except ImportError as e:
        print(f"Session service import failed: {e}")
        # Try without session service
        try:
            runner = Runner(
                app_name="test_app",
                agent=test_agent,
                session_service=None
            )
            print("Runner created with None session_service")
        except Exception as e2:
            print(f"Runner creation failed: {e2}")
            
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()