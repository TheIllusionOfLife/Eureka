#!/usr/bin/env python3
"""Test Runner with proper parameters."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk import Agent, Runner
    from google.adk.sessions import InMemorySessionService
    import google.adk.types as types
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
    
    # Check what's in types module
    print("Available types:")
    print([x for x in dir(types) if not x.startswith('_')])
    
    # Try to create Content object
    test_message = "Generate 3 creative ideas for transportation."
    
    # Try different Content formats
    content_formats = [
        types.Content(test_message),
        types.Content(text=test_message),
        types.Content(content=test_message),
    ]
    
    for i, content in enumerate(content_formats):
        try:
            print(f"\n=== Testing Content format {i+1} ===")
            print(f"Content: {content}")
            
            # Run the agent
            result = runner.run(
                user_id="test_user",
                session_id="test_session", 
                new_message=content
            )
            
            print(f"Result type: {type(result)}")
            print("Success! Collecting results...")
            
            # Collect all events
            full_response = ""
            for event in result:
                print(f"Event: {event}")
                print(f"Event type: {type(event)}")
                
                # Try to extract text from event
                if hasattr(event, 'content'):
                    full_response += str(event.content)
                elif hasattr(event, 'text'):
                    full_response += str(event.text)
                elif hasattr(event, 'message'):
                    full_response += str(event.message)
                else:
                    print(f"Event attributes: {[x for x in dir(event) if not x.startswith('_')]}")
            
            print(f"Full response: {full_response}")
            print("✅ ADK Runner approach works!")
            break
            
        except Exception as e:
            print(f"❌ Content format {i+1} failed: {e}")
            continue
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()