#!/usr/bin/env python3
"""Test ADK Agent with Message class."""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_adk_with_message_class():
    try:
        from google.adk.agents import Agent
        import google.generativeai as genai
        
        # Try importing Message classes
        message_classes = []
        try:
            from google.adk.agents import Message
            message_classes.append(("Message", Message))
        except ImportError:
            pass
            
        try:
            from google.adk import Message
            message_classes.append(("Message", Message))
        except ImportError:
            pass
            
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            # Check if genai has message types
            if hasattr(genai.types, 'ContentDict'):
                message_classes.append(("ContentDict", genai.types.ContentDict))
        except ImportError:
            pass
        
        print(f"Found message classes: {[name for name, _ in message_classes]}")
        
        # Configure API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            print("✅ API key configured")
        else:
            print("❌ No API key found")
            return
        
        # Create a simple agent
        test_agent = Agent(
            name="test",
            model="gemini-2.0-flash",
            description="Test agent",
            instruction="You are a helpful assistant. Answer questions briefly."
        )
        
        # Try using message classes
        for name, MessageClass in message_classes:
            try:
                print(f"\n=== Testing with {name} ===")
                # Try different ways to create message
                message = MessageClass(content="What is 2+2?")
                print(f"Created message: {message}")
                
                async for chunk in test_agent.run_live(message):
                    print(f"Success! Chunk type: {type(chunk)}")
                    print(f"Chunk: {chunk}")
                    break
                    
                print(f"✅ {name} worked!")
                break
                
            except Exception as e:
                print(f"❌ {name} failed: {e}")
                continue
        
        # If no message classes work, try inspect the agent methods more
        print(f"\n=== Agent inspection ===")
        print(f"Agent type: {type(test_agent)}")
        
        # Check if there are any other methods that might work
        methods = [attr for attr in dir(test_agent) if not attr.startswith('_') and callable(getattr(test_agent, attr))]
        print(f"Callable methods: {methods}")
        
    except ImportError as e:
        print(f"ADK not available: {e}")
    except Exception as e:
        print(f"Error testing ADK: {e}")

if __name__ == "__main__":
    asyncio.run(test_adk_with_message_class())