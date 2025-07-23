"""Test to ensure all files use 'docker compose' V2 syntax."""
import os
import re
from pathlib import Path
from typing import List, Tuple


def find_docker_compose_references(root_dir: str = ".") -> List[Tuple[str, int, str]]:
    """
    Find all references to 'docker-compose' (old syntax) in the codebase.
    
    Returns:
        List of tuples (filepath, line_number, line_content)
    """
    findings = []
    
    # File extensions to check
    extensions = {'.py', '.md', '.yml', '.yaml', '.sh', '.txt', '.rst', '.json'}
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', 
                 'htmlcov', '.mypy_cache', 'venv', '.venv', 'build', 'dist'}
    
    for root, dirs, files in os.walk(root_dir):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            filepath = Path(root) / file
            
            # Skip files without relevant extensions and this test file itself
            if filepath.suffix not in extensions or filepath.name == 'test_docker_compose_syntax.py':
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # Look for 'docker-compose' (case-insensitive)
                        if re.search(r'docker-compose', line, re.IGNORECASE):
                            findings.append((str(filepath), line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue
    
    return findings


def test_no_hyphenated_docker_compose():
    """Ensure no files contain 'docker-compose' (old syntax)."""
    findings = find_docker_compose_references()
    
    if findings:
        error_msg = ["Found 'docker-compose' (old syntax) in the following locations:"]
        error_msg.append("")
        
        for filepath, line_num, line_content in findings:
            error_msg.append(f"  {filepath}:{line_num}")
            error_msg.append(f"    {line_content}")
            error_msg.append("")
        
        error_msg.append(f"Total occurrences: {len(findings)}")
        error_msg.append("")
        error_msg.append("Please update to 'docker compose' (Docker Compose V2 syntax)")
        
        # This will fail and show all locations that need updating
        assert False, "\n".join(error_msg)


if __name__ == "__main__":
    # Allow running directly to see findings
    findings = find_docker_compose_references()
    if findings:
        print(f"Found {len(findings)} occurrences of 'docker-compose':")
        for filepath, line_num, line_content in findings:
            print(f"  {filepath}:{line_num} - {line_content}")
    else:
        print("✓ No 'docker-compose' references found")