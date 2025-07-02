#!/usr/bin/env python3
"""Deep search for Content class."""
import pkgutil
import google.adk

def find_content_class():
    """Recursively search for Content class in google.adk."""
    
    # Search all modules recursively
    for importer, modname, ispkg in pkgutil.walk_packages(
        google.adk.__path__, 
        google.adk.__name__ + ".",
        onerror=lambda x: None
    ):
        try:
            module = importer.find_module(modname).load_module(modname)
            if hasattr(module, 'Content'):
                Content = module.Content
                print(f"✅ Found Content in {modname}: {Content}")
                
                # Try to create instance
                try:
                    content = Content("test")
                    print(f"✅ Content instance: {content}")
                    return modname, Content
                except Exception as e:
                    print(f"❌ Failed to create Content: {e}")
                    
            # Also look for any class with 'Content' in name
            for attr_name in dir(module):
                if 'Content' in attr_name and not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr):
                        print(f"Found Content-related class: {modname}.{attr_name}")
                        
        except Exception as e:
            # Skip modules that can't be imported
            pass
    
    return None, None

# Also check the Runner itself to see what it expects
try:
    from google.adk import Runner
    print(f"Runner class: {Runner}")
    print(f"Runner module: {Runner.__module__}")
    
    # Import the runner module and look for Content there
    runner_module = __import__(Runner.__module__, fromlist=[''])
    print(f"Runner module contents: {[x for x in dir(runner_module) if not x.startswith('_')]}")
    
    if hasattr(runner_module, 'Content'):
        print(f"Content in runner module: {runner_module.Content}")
    elif hasattr(runner_module, 'types'):
        print(f"Types in runner module: {runner_module.types}")
        types_module = runner_module.types
        if hasattr(types_module, 'Content'):
            print(f"Content in types: {types_module.Content}")
            
except Exception as e:
    print(f"Error checking Runner: {e}")

# Run the search
print("Searching for Content class...")
module_name, Content = find_content_class()

if Content:
    print(f"\n✅ SUCCESS: Content found in {module_name}")
else:
    print("\n❌ FAILED: Could not find Content class")