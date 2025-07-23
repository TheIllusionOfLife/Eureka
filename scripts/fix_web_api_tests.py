#!/usr/bin/env python3
"""Fix Web API test initialization issues."""
import os
import re


def add_test_initialization_support():
    """Add support for initializing components in test mode."""
    file_path = "web/backend/main.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add initialization function that can be called from tests
    init_function = '''
# Helper function for test initialization
def initialize_components_for_testing():
    """Initialize components for testing without running lifespan."""
    global temp_manager, reasoning_engine, bookmark_system, cache_manager
    
    if temp_manager is None:
        temp_manager = TemperatureManager()
    if reasoning_engine is None:
        reasoning_engine = ReasoningEngine()
    if bookmark_system is None:
        bookmark_system = BookmarkManager()
    
    # Set app start time for uptime calculation
    if not hasattr(app.state, 'start_time'):
        app.state.start_time = datetime.now()
    
    return {
        "temp_manager": temp_manager,
        "reasoning_engine": reasoning_engine,
        "bookmark_system": bookmark_system,
        "cache_manager": cache_manager
    }
'''

    # Find a good place to insert - after the lifespan function
    insertion_point = content.find('app = FastAPI(')
    if insertion_point != -1:
        # Insert before app creation
        content = content[:insertion_point] + init_function + '\n\n' + content[insertion_point:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Added test initialization support to main.py")
    
    # Update the test file to use the initialization
    update_test_file()


def update_test_file():
    """Update test file to properly initialize components."""
    test_file = "tests/test_web_api_fixes.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Add initialization at the top of each test that needs it
    init_code = '''
    # Initialize components for testing
    from web.backend.main import initialize_components_for_testing
    initialize_components_for_testing()
'''
    
    # Update bookmark tests to include initialization
    # Find bookmark test functions
    bookmark_test_pattern = r'(def test_bookmark.*?\(self\):.*?""".*?""")'
    
    def add_init_to_test(match):
        test_def = match.group(1)
        # Add initialization after docstring
        return test_def + init_code
    
    content = re.sub(bookmark_test_pattern, add_init_to_test, content, flags=re.DOTALL)
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated test file to initialize components")


def main():
    """Run all fixes."""
    print("🔧 Fixing Web API test initialization issues...")
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Apply fixes
    add_test_initialization_support()
    
    print("\n✨ Test initialization fixes applied!")


if __name__ == "__main__":
    main()