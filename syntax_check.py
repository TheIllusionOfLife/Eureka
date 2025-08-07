#!/usr/bin/env python3
"""Syntax check for new refactoring files."""

import ast
import sys
import os

def check_syntax(file_path):
    """Check syntax of a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        print(f"✓ {file_path}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path}: Syntax Error at line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error: {e}")
        return False

def main():
    """Check syntax of all new refactoring files."""
    files_to_check = [
        'src/madspark/utils/import_manager.py',
        'src/madspark/utils/environment_manager.py',
        'src/madspark/utils/logging_manager.py',
        'src/madspark/utils/validation_decorators.py',
        'test_refactoring_imports.py'
    ]
    
    print("Checking syntax of refactoring files...")
    print("=" * 50)
    
    results = []
    for file_path in files_to_check:
        if os.path.exists(file_path):
            results.append(check_syntax(file_path))
        else:
            print(f"⚠️ {file_path}: File not found")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All {total} files have valid syntax")
        return 0
    else:
        failed = total - passed
        print(f"❌ {failed}/{total} files have syntax errors")
        return 1

if __name__ == "__main__":
    exit(main())