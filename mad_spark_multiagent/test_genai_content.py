#!/usr/bin/env python3
"""Test with google.genai.types.Content."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk import Agent, Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content
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
    
    # Test message
    test_message = "Generate 3 creative ideas for future transportation."
    
    # Try different ways to create Content
    content_attempts = [
        lambda: Content(test_message),
        lambda: Content(text=test_message),
        lambda: Content(content=test_message),
        lambda: Content(parts=[test_message]),
        lambda: Content(parts=[{"text": test_message}]),
    ]
    
    for i, create_content in enumerate(content_attempts):
        try:
            print(f"\n=== Content attempt {i+1} ===")
            content = create_content()
            print(f"Content created: {content}")
            print(f"Content type: {type(content)}")
            
            # Run the agent
            print("Running agent...")
            result = runner.run(
                user_id="test_user",
                session_id="test_session",
                new_message=content
            )
            
            print(f"Result type: {type(result)}")
            print("✅ Success! Collecting events...")
            
            # Collect events
            full_response = ""
            event_count = 0
            for event in result:
                event_count += 1
                print(f"Event {event_count}: {type(event)}")
                
                # Extract text from event
                event_text = ""
                if hasattr(event, 'content'):
                    event_text = str(event.content)
                elif hasattr(event, 'text'):
                    event_text = str(event.text)
                elif hasattr(event, 'message'):
                    event_text = str(event.message)
                elif hasattr(event, 'delta'):
                    event_text = str(event.delta)
                elif hasattr(event, 'data'):
                    event_text = str(event.data)
                else:
                    print(f"  Event attributes: {[x for x in dir(event) if not x.startswith('_')]}")
                    event_text = str(event)
                
                if event_text and event_text.strip():
                    print(f"  Text: {event_text}")
                    full_response += event_text
                
                # Limit events for testing
                if event_count > 10:
                    print("  ... (limiting events for testing)")
                    break
            
            print(f"\n📝 Full response: {full_response}")
            print("✅ ADK Runner approach working!")
            
            # Now create a reusable function
            print("\n=== Creating reusable function ===")
            
            def run_adk_agent_sync(agent, prompt):
                """Synchronous wrapper for ADK agent using Runner."""
                try:
                    # Create content
                    content = Content(parts=[{"text": prompt}])
                    
                    # Run agent
                    result = runner.run(
                        user_id="user",
                        session_id="session",
                        new_message=content
                    )
                    
                    # Collect response
                    response_text = ""
                    for event in result:
                        if hasattr(event, 'content'):
                            response_text += str(event.content)
                        elif hasattr(event, 'text'):
                            response_text += str(event.text)
                        elif hasattr(event, 'delta'):
                            response_text += str(event.delta)
                        elif hasattr(event, 'data'):
                            response_text += str(event.data)
                    
                    return {"content": response_text.strip()}
                    
                except Exception as e:
                    return {"error": str(e)}
            
            # Test the function
            test_result = run_adk_agent_sync(test_agent, "What is 2+2?")
            print(f"Function test result: {test_result}")
            
            if "content" in test_result:
                print("🎉 ADK solution complete!")
            
            break  # Success, stop trying other formats
            
        except Exception as e:
            print(f"❌ Content attempt {i+1} failed: {e}")
            import traceback
            traceback.print_exc()
            continue
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()