#!/usr/bin/env python3
"""Script to inspect Google ADK Agent methods."""

try:
    from google.adk.agents import Agent
    
    # Create a simple agent to inspect
    test_agent = Agent(
        name="test",
        model="gemini-2.0-flash",
        description="Test agent for method inspection",
        instruction="This is a test agent."
    )
    
    print("Available methods on ADK Agent:")
    methods = [method for method in dir(test_agent) if not method.startswith('_')]
    for method in sorted(methods):
        print(f"  {method}")
    
    print("\nTrying common method names:")
    common_methods = ['invoke', 'call', 'run', 'execute', 'generate', 'chat', 'send']
    for method_name in common_methods:
        if hasattr(test_agent, method_name):
            method = getattr(test_agent, method_name)
            print(f"  ✅ {method_name}: {type(method)}")
        else:
            print(f"  ❌ {method_name}: not found")
    
    # Get class info
    print(f"\nAgent class: {type(test_agent)}")
    print(f"Agent class MRO: {type(test_agent).__mro__}")
    
except ImportError as e:
    print(f"ADK not available: {e}")
except Exception as e:
    print(f"Error inspecting ADK: {e}")