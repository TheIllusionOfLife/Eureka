#!/usr/bin/env python3
"""Apply pytest markers to test files."""
import re
import os

# Define which tests get which markers
MARKER_MAPPINGS = {
    'test_integration.py': {
        'test_workflow_with_novelty_filtering': ['@pytest.mark.integration'],
        'test_workflow_with_agent_failures': ['@pytest.mark.integration'],
        'test_workflow_with_invalid_parameters': ['@pytest.mark.integration'],
        'test_workflow_network_resilience': ['@pytest.mark.integration', '@pytest.mark.slow'],
        'test_async_workflow_performance': ['@pytest.mark.slow'],  # already has asyncio
        'test_workflow_memory_usage': ['@pytest.mark.slow'],
        'test_workflow_data_consistency': ['@pytest.mark.integration'],
        'test_workflow_output_structure': ['@pytest.mark.integration'],
    },
    'test_system_integration.py': {
        'test_cli_to_core_integration': ['@pytest.mark.integration'],
        'test_end_to_end_workflow': ['@pytest.mark.integration', '@pytest.mark.slow'],
        'test_docker_integration': ['@pytest.mark.integration', '@pytest.mark.slow'],
        'test_web_api_integration': ['@pytest.mark.integration'],
        'test_workflow_with_agent_failures': ['@pytest.mark.integration'],
        'test_workflow_network_resilience': ['@pytest.mark.integration', '@pytest.mark.slow'],
        'test_workflow_execution_time': ['@pytest.mark.slow'],
        'test_workflow_memory_usage': ['@pytest.mark.slow'],
        'test_workflow_data_consistency': ['@pytest.mark.integration'],
    },
    'test_coordinators.py': {
        'test_run_multistep_workflow_success': ['@pytest.mark.integration'],
        'test_run_multistep_workflow_idea_generation_failure': ['@pytest.mark.integration'],
        'test_run_multistep_workflow_partial_failure': ['@pytest.mark.integration'],
        'test_run_workflow_success': ['@pytest.mark.integration'],  # async
        'test_async_workflow_timeout': ['@pytest.mark.slow'],  # async
        'test_async_workflow_with_exception': ['@pytest.mark.integration'],  # async
        'test_workflow_with_bookmarks': ['@pytest.mark.integration'],
        'test_workflow_with_temperature_presets': ['@pytest.mark.integration'],
        'test_workflow_error_propagation': ['@pytest.mark.integration'],
    },
    'test_cli.py': {
        'test_cli_full_workflow_integration': ['@pytest.mark.integration'],
        'test_cli_error_handling_integration': ['@pytest.mark.integration'],
    },
    'test_docker_compose_syntax.py': {
        'ALL': ['@pytest.mark.integration'],
    },
    'test_web_api_fixes.py': {
        'ALL': ['@pytest.mark.integration'],
    },
}


def add_markers_to_file(filepath, test_markers):
    """Add markers to specific tests in a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    modified = False
    
    for test_name, markers in test_markers.items():
        if test_name == 'ALL':
            # Mark all test methods
            pattern = r'(\n    )(def test_|async def test_)'
            replacement = r'\n    ' + '\n    '.join(markers) + r'\n    \2'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                modified = True
        else:
            # Find the test method
            # Handle both def and async def
            pattern = rf'(\n    )((?:async )?def {test_name}\()'
            
            # Check if markers already exist
            check_pattern = rf'\n    @pytest\.mark\.\w+\n    (?:async )?def {test_name}\('
            if re.search(check_pattern, content):
                print(f"  {test_name} already has markers, checking if all needed...")
                # Add missing markers
                for marker in markers:
                    if marker not in content:
                        # Find the last marker before the test
                        marker_pattern = rf'(\n(?:    @pytest\.mark\.\w+\n)+)(    (?:async )?def {test_name}\()'
                        replacement = rf'\1    {marker}\n\2'
                        new_content = re.sub(marker_pattern, replacement, content)
                        if new_content != content:
                            content = new_content
                            modified = True
                            print(f"    Added {marker} to {test_name}")
            else:
                # Add all markers
                replacement = r'\n    ' + '\n    '.join(markers) + r'\n    \2'
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True
                    print(f"  Added markers to {test_name}")
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Updated {filepath}")
    else:
        print(f"  No changes needed for {filepath}")
    
    return modified


def main():
    """Apply markers to all test files."""
    print("Applying pytest markers to test files...")
    
    tests_dir = "tests"
    total_modified = 0
    
    for filename, test_markers in MARKER_MAPPINGS.items():
        filepath = os.path.join(tests_dir, filename)
        if os.path.exists(filepath):
            print(f"\nProcessing {filename}...")
            if add_markers_to_file(filepath, test_markers):
                total_modified += 1
        else:
            print(f"\nWarning: {filepath} not found")
    
    print(f"\n✓ Modified {total_modified} files")


if __name__ == "__main__":
    main()