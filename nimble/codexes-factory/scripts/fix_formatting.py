#!/usr/bin/env python3
"""
Script to fix embedded newline characters in Python files.
"""

import os
import re
from pathlib import Path

def fix_embedded_newlines(file_path):
    """Fix embedded \\n characters in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has embedded newlines
        if '\\n' in content:
            print(f"Fixing {file_path}")
            
            # Replace embedded newlines with actual newlines
            # This is a simple fix - more complex cases might need manual review
            fixed_content = content.replace('\\n', '\n')
            
            # Also fix embedded quotes that might be causing issues
            fixed_content = fixed_content.replace('\\"', '"')
            
            # Write back the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Main function to fix all Python files in the ideation module."""
    ideation_dir = Path("src/codexes/modules/ideation")
    
    if not ideation_dir.exists():
        print(f"Directory {ideation_dir} not found")
        return
    
    fixed_files = []
    
    # Find all Python files
    for py_file in ideation_dir.rglob("*.py"):
        if fix_embedded_newlines(py_file):
            fixed_files.append(py_file)
    
    print(f"\nFixed {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    print("\nNow testing compilation...")
    
    # Test compilation of fixed files
    failed_files = []
    for py_file in ideation_dir.rglob("*.py"):
        try:
            compile(open(py_file).read(), py_file, 'exec')
        except SyntaxError as e:
            failed_files.append((py_file, str(e)))
    
    if failed_files:
        print(f"\n{len(failed_files)} files still have syntax errors:")
        for file_path, error in failed_files:
            print(f"  - {file_path}: {error}")
    else:
        print("\n✅ All files compile successfully!")

if __name__ == "__main__":
    main()