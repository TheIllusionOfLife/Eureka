#!/usr/bin/env python3
"""Test ADK auth module."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.adk.auth
    import google.generativeai as genai
    
    print("ADK auth module contents:")
    print(dir(google.adk.auth))
    
    # Check if there are authentication functions
    for attr in dir(google.adk.auth):
        if not attr.startswith('_'):
            obj = getattr(google.adk.auth, attr)
            print(f"  {attr}: {type(obj)}")
            if callable(obj):
                try:
                    import inspect
                    print(f"    signature: {inspect.signature(obj)}")
                except:
                    pass
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"\nTesting auth with API key: {api_key[:10]}...")
        
        # Configure genai
        genai.configure(api_key=api_key)
        
        # Try to see if there's an authentication method
        if hasattr(google.adk.auth, 'configure'):
            try:
                google.adk.auth.configure(api_key=api_key)
                print("✅ ADK auth configured")
            except Exception as e:
                print(f"❌ ADK auth configure failed: {e}")
        
        # Test if ADK automatically inherits from genai
        print("\nTesting automatic inheritance...")
        from google.adk.agents import Agent
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai.types import Content
        
        # Create agent
        agent = Agent(
            name="test",
            model="gemini-2.0-flash",
            description="Test",
            instruction="You are a test assistant. Respond with 'Hello test!'"
        )
        
        # Create runner  
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="test_app",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = session_service.create_session_sync(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Create content
        content = Content(parts=[{"text": "Say hello"}])
        
        print("Testing if ADK can make API call...")
        try:
            result = runner.run(
                user_id="test_user",
                session_id="test_session",
                new_message=content
            )
            
            # Just check if we get a generator (meaning it's working)
            print(f"Result type: {type(result)}")
            
            # Try to get first event
            try:
                first_event = next(iter(result))
                print(f"First event type: {type(first_event)}")
                print("✅ ADK API call working!")
            except Exception as e:
                print(f"❌ ADK API call failed: {e}")
                
        except Exception as e:
            print(f"❌ Runner execution failed: {e}")
            
    else:
        print("No API key found")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()