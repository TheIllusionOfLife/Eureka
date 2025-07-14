#!/usr/bin/env python3
"""
Script to update import statements for the new package structure.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update mad_spark_multiagent imports to madspark
        content = re.sub(
            r'from mad_spark_multiagent\.([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'from madspark.\1',
            content
        )
        content = re.sub(
            r'import mad_spark_multiagent\.([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'import madspark.\1',
            content
        )
        
        # Update specific module mappings
        replacements = {
            'from madspark.utils.utils.errors': 'from madspark.utils.utils.errors',
            'from madspark.utils.utils.constants': 'from madspark.utils.utils.constants',
            'from madspark.utils.utils': 'from madspark.utils.utils.utils',
            'from madspark.utils.cache_manager': 'from madspark.utils.utils.cache_manager',
            'from madspark.utils.bookmark_system': 'from madspark.utils.utils.bookmark_system',
            'from madspark.utils.novelty_filter': 'from madspark.utils.utils.novelty_filter',
            'from madspark.utils.temperature_control': 'from madspark.utils.utils.temperature_control',
            'from madspark.utils.agent_retry_wrappers': 'from madspark.utils.utils.agent_retry_wrappers',
            'from madspark.utils.verbose_logger': 'from madspark.utils.utils.verbose_logger',
            'from madspark.utils.improved_idea_cleaner': 'from madspark.utils.utils.improved_idea_cleaner',
            'from madspark.utils.export_utils': 'from madspark.utils.utils.export_utils',
            'from madspark.core.coordinator': 'from madspark.core.coordinator',
            'from madspark.core.async_coordinator': 'from madspark.core.async_coordinator',
            'from madspark.core.enhanced_reasoning': 'from madspark.core.enhanced_reasoning',
            'from madspark.cli.cli': 'from madspark.cli.cli.cli',
            'from madspark.cli.interactive_mode': 'from madspark.cli.cli.interactive_mode',
            'from madspark.utils.batch_processor': 'from madspark.utils.utils.batch_processor',
        }
        
        for old_import, new_import in replacements.items():
            content = content.replace(old_import, new_import)
        
        # Update agent_defs references
        content = re.sub(
            r'from madspark\.agent_defs\.([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'from madspark.agents.\1',
            content
        )
        content = re.sub(
            r'import madspark\.agent_defs\.([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'import madspark.agents.\1',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated imports in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update imports in all Python files."""
    base_path = Path(__file__).parent.parent
    
    # Directories to process
    directories = [
        base_path / "src",
        base_path / "tests", 
        base_path / "tools",
        base_path / "scripts"
    ]
    
    updated_files = []
    
    for directory in directories:
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                if update_imports_in_file(py_file):
                    updated_files.append(py_file)
    
    print(f"\\nUpdated imports in {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()