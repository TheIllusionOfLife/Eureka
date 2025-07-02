#!/usr/bin/env python3
"""Find Content class in ADK."""

# Try different import paths for Content
import_paths = [
    "google.adk.types",
    "google.adk.sessions.types", 
    "google.adk.events.types",
    "google.adk.runners.types",
    "google.generativeai.types",
]

for path in import_paths:
    try:
        module = __import__(path, fromlist=['Content'])
        if hasattr(module, 'Content'):
            Content = module.Content
            print(f"✅ Found Content in {path}: {Content}")
            
            # Try to create Content instance
            try:
                content = Content("test message")
                print(f"✅ Content instance created: {content}")
                break
            except Exception as e:
                print(f"❌ Failed to create Content instance: {e}")
        else:
            print(f"❌ No Content in {path}")
    except ImportError as e:
        print(f"❌ Cannot import {path}: {e}")

# Also check if Content is available directly from google.adk
try:
    import google.adk
    if hasattr(google.adk, 'Content'):
        print(f"✅ Content available directly: {google.adk.Content}")
    else:
        print("❌ No Content directly in google.adk")
        
    # Look for all classes containing 'Content'
    for attr_name in dir(google.adk):
        if 'content' in attr_name.lower():
            print(f"Found content-related: {attr_name}")
except Exception as e:
    print(f"Error checking google.adk: {e}")

# Try looking through all submodules
try:
    import google.adk
    for module_name in dir(google.adk):
        if not module_name.startswith('_'):
            try:
                module = getattr(google.adk, module_name)
                if hasattr(module, '__path__'):  # It's a package
                    submodule = __import__(f'google.adk.{module_name}', fromlist=[''])
                    if hasattr(submodule, 'Content'):
                        print(f"✅ Found Content in google.adk.{module_name}")
            except:
                pass
except Exception as e:
    print(f"Error searching modules: {e}")