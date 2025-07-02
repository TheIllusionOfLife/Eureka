#!/usr/bin/env python3
"""Test session creation methods."""
import inspect
from google.adk.sessions import InMemorySessionService

# Create session service
session_service = InMemorySessionService()

# Check create_session signature
print("create_session signature:")
print(inspect.signature(session_service.create_session))

# Check what methods are available
print("\nAvailable methods:")
methods = [method for method in dir(session_service) if not method.startswith('_') and callable(getattr(session_service, method))]
for method in methods:
    print(f"  {method}: {inspect.signature(getattr(session_service, method))}")

# Try to create a session
try:
    session = session_service.create_session()
    print(f"\nCreated session: {session}")
    print(f"Session type: {type(session)}")
    print(f"Session attributes: {[x for x in dir(session) if not x.startswith('_')]}")
    
    # Check if session has an ID
    if hasattr(session, 'id'):
        print(f"Session ID: {session.id}")
    if hasattr(session, 'session_id'):
        print(f"Session ID: {session.session_id}")
        
except Exception as e:
    print(f"Error creating session: {e}")
    import traceback
    traceback.print_exc()