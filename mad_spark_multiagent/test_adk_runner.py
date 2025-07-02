#!/usr/bin/env python3
"""Test ADK with Runner class."""
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
    
    # Try using Runner
    print(f"Runner methods: {[x for x in dir(Runner) if not x.startswith('_')]}")
    
    # Test different Runner approaches
    runner = Runner()
    print(f"Runner created: {runner}")
    print(f"Runner methods: {[x for x in dir(runner) if not x.startswith('_')]}")
    
    # Try running with runner
    test_prompt = "Generate 3 creative ideas."
    print(f"Testing with prompt: {test_prompt}")
    
    # Look for sync methods on runner
    if hasattr(runner, 'run'):
        result = runner.run(test_agent, test_prompt)
        print(f"Runner.run result: {result}")
    elif hasattr(runner, 'execute'):
        result = runner.execute(test_agent, test_prompt)
        print(f"Runner.execute result: {result}")
    else:
        print("No obvious sync methods found on Runner")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()