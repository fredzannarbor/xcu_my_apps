#!/usr/bin/env python3
"""
Comprehensive script to fix all formatting issues in Python files.
"""

import os
import re
from pathlib import Path

def fix_file_formatting(file_path):
    """Fix all formatting issues in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix embedded newlines that are causing syntax errors
        # Pattern 1: \\n in the middle of code
        content = re.sub(r'\\n\s*', '\n', content)
        
        # Fix embedded quotes
        content = content.replace('\\"', '"')
        
        # Fix malformed f-strings and string literals
        # Look for unterminated strings that span multiple lines incorrectly
        lines = content.split('\n')
        fixed_lines = []
        in_multiline_string = False
        string_delimiter = None
        
        for i, line in enumerate(lines):
            # Skip if we're in a docstring
            if '"""' in line or "'''" in line:
                fixed_lines.append(line)
                continue
                
            # Look for problematic patterns and fix them
            # Pattern: try:\n followed by code on same line
            if 'try:' in line and line.strip() != 'try:':
                # Split the line at try:
                parts = line.split('try:', 1)
                if len(parts) == 2 and parts[1].strip():
                    fixed_lines.append(parts[0] + 'try:')
                    # Add the rest as a new line with proper indentation
                    indent = len(parts[0]) + 4  # Add 4 spaces for try block
                    fixed_lines.append(' ' * indent + parts[1].strip())
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Additional fixes for common patterns
        # Fix except Exception as e:\n followed by code
        content = re.sub(r'except Exception as e:\\n\s*', 'except Exception as e:\n            ', content)
        
        # Fix return statements that got mangled
        content = re.sub(r'return \{\\n\s*', 'return {\n            ', content)
        
        # Fix dictionary definitions that got mangled
        content = re.sub(r'\{\\n\s*"', '{\n            "', content)
        
        # Write back if changed
        if content != original_content:
            print(f"Fixing {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix all Python files in the ideation module."""
    ideation_dir = Path("src/codexes/modules/ideation")
    
    if not ideation_dir.exists():
        print(f"Directory {ideation_dir} not found")
        return
    
    # Get all Python files
    py_files = list(ideation_dir.rglob("*.py"))
    print(f"Found {len(py_files)} Python files to check")
    
    fixed_count = 0
    for py_file in py_files:
        if fix_file_formatting(py_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    
    # Now test compilation
    print("\nTesting compilation of all files...")
    failed_files = []
    
    for py_file in py_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            failed_files.append((py_file, str(e)))
        except Exception as e:
            failed_files.append((py_file, f"Other error: {str(e)}"))
    
    if failed_files:
        print(f"\n❌ {len(failed_files)} files still have issues:")
        for file_path, error in failed_files[:10]:  # Show first 10
            print(f"  - {file_path.name}: {error}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    else:
        print("\n✅ All files compile successfully!")
    
    return len(failed_files) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)