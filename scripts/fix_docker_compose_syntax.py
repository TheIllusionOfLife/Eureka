#!/usr/bin/env python3
"""Script to update docker-compose to docker compose syntax throughout the codebase."""
import os
import re
from pathlib import Path
from typing import List, Tuple


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    skip_patterns = [
        'test_docker_compose_syntax.py',  # Our test file
        'fix_docker_compose_syntax.py',   # This script
        '.git',
        '__pycache__',
        'node_modules',
        '.pytest_cache',
        'htmlcov',
    ]
    
    for pattern in skip_patterns:
        if pattern in str(filepath):
            return True
    
    return False


def fix_docker_compose_in_file(filepath: Path) -> Tuple[bool, int]:
    """
    Fix docker-compose references in a single file.
    
    Returns:
        Tuple of (was_modified, number_of_replacements)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacement_count = 0
        
        # Pattern replacements - be careful with different contexts
        replacements = [
            # Command usage: docker-compose -> docker compose
            (r'\bdocker-compose\s+', 'docker compose '),
            
            # Special case: -f docker-compose.yml should become -f docker-compose.yml (no change to filename)
            # But docker-compose -f should become docker compose -f
            (r'docker compose -f docker-compose', 'docker compose -f docker-compose'),  # Fix double replacement
            
            # In JSON strings with escaped newlines
            (r'docker-compose(?=\\n|")', 'docker compose'),
            
            # In conditionals checking for docker-compose command
            (r'command -v docker-compose', 'command -v docker'),
            
            # GitHub Actions - Test docker-compose -> Test docker compose  
            (r'(- name: Test )docker-compose', r'\1docker compose'),
            
            # Note: We intentionally keep docker-compose in:
            # - File names (docker-compose.yml, docker-compose.prod.yml)
            # - Find patterns looking for such files
            # - Conditionals checking for such file names
        ]
        
        for pattern, replacement in replacements:
            content, count = re.subn(pattern, replacement, content)
            replacement_count += count
        
        # Write back if modified
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, replacement_count
        
        return False, 0
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0


def main():
    """Main function to fix all docker-compose references."""
    print("Fixing docker-compose syntax to docker compose V2...")
    
    # File extensions to check
    extensions = {'.py', '.md', '.yml', '.yaml', '.sh', '.txt', '.rst', '.json'}
    
    modified_files = []
    total_replacements = 0
    
    for root, dirs, files in os.walk('.'):
        # Don't skip .github or .claude directories - we need to update those too
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', '.pytest_cache']]
        
        for file in files:
            filepath = Path(root) / file
            
            if should_skip_file(filepath):
                continue
            
            if filepath.suffix in extensions:
                was_modified, count = fix_docker_compose_in_file(filepath)
                if was_modified:
                    modified_files.append((str(filepath), count))
                    total_replacements += count
    
    # Report results
    if modified_files:
        print(f"\nModified {len(modified_files)} files with {total_replacements} replacements:")
        for filepath, count in sorted(modified_files):
            print(f"  {filepath} ({count} replacements)")
    else:
        print("\nNo files needed modification.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()