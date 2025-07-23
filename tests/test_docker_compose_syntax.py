#!/usr/bin/env python3
"""Test for deprecated docker-compose syntax in the codebase."""

import os
import sys
import re


def check_docker_compose_syntax(root_dir="."):
    """Check for deprecated docker-compose syntax in all files."""
    # Match docker-compose when used as a command (followed by command flags or subcommands)
    deprecated_pattern = re.compile(r'\bdocker-compose\s+(up|down|build|run|exec|ps|logs|pull|push|stop|start|restart|rm|config)\b')
    excluded_patterns = [
        r'\.git/',
        r'__pycache__',
        r'\.pytest_cache',
        r'node_modules/',
        r'venv/',
        r'\.env',
        r'build/',
        r'dist/',
        r'bandit-report\.json',
    ]
    
    errors = []
    files_checked = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(re.search(p, os.path.join(root, d)) for p in excluded_patterns)]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip excluded patterns
            if any(re.search(p, file_path) for p in excluded_patterns):
                continue
                
            # Skip binary files
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz')):
                continue
                
            # Check text files
            if file.endswith(('.md', '.yml', '.yaml', '.sh', '.py', '.txt', '.json', '.js', '.ts', '.tsx')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        files_checked += 1
                        
                        # Find all occurrences
                        for line_num, line in enumerate(content.splitlines(), 1):
                            if deprecated_pattern.search(line):
                                # Skip if it's a comment about the deprecated syntax
                                if 'deprecated' in line.lower() or 'old syntax' in line.lower():
                                    continue
                                # Skip if it's referring to filenames or in documentation explaining the issue
                                if any(x in line.lower() for x in ['docker-compose.yml', 'docker-compose.yaml', 
                                                                    'docker-compose syntax', 'docker-compose (v1',
                                                                    'check', 'test', 'hook', 'issue', 'change']):
                                    continue
                                # Skip if the line contains a filename pattern
                                if re.search(r'docker-compose[\w.-]*\.(yml|yaml|prod|dev|test)', line):
                                    continue
                                # Skip lines that are explaining the change from old to new syntax
                                if '→' in line or '->' in line:
                                    continue
                                # Skip if it's in a comment
                                if line.strip().startswith('#') or line.strip().startswith('//'):
                                    continue
                                # Skip if it's part of test/validation logic
                                if file_path.endswith(('test_docker_compose_syntax.py', '.pre-commit-config.yaml')):
                                    continue
                                errors.append(f"{file_path}:{line_num}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    # Skip files that can't be read
                    pass
    
    return errors, files_checked


def main():
    """Main function to run the syntax check."""
    print("Checking for deprecated docker-compose syntax...")
    
    errors, files_checked = check_docker_compose_syntax()
    
    print(f"Checked {files_checked} files")
    
    if errors:
        print(f"\n❌ Found {len(errors)} instances of deprecated 'docker-compose' syntax:")
        print("   Use 'docker compose' (with space) instead.\n")
        
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
            
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
            
        print("\nPlease update to the new 'docker compose' syntax.")
        return 1
    else:
        print("✅ No deprecated docker-compose syntax found!")
        return 0


if __name__ == "__main__":
    sys.exit(main())