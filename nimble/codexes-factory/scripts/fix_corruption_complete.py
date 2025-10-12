#!/usr/bin/env python3
"""
Complete fix for file corruption in ideation modules.
Root cause: Files contain literal \\n and \\" instead of actual newlines and quotes.
"""

import os
import re
from pathlib import Path

def fix_file_completely(file_path):
    """Completely fix a corrupted Python file."""
    try:
        # Read as binary to see the actual bytes
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Convert to string
        content_str = content.decode('utf-8', errors='replace')
        
        # Check if file needs fixing
        if '\\n' not in content_str and '\\"' not in content_str:
            return False
        
        print(f"Fixing {file_path}")
        
        # Fix embedded newlines - replace \\n with actual newlines
        content_str = content_str.replace('\\n', '\n')
        
        # Fix embedded quotes - replace \\" with actual quotes
        content_str = content_str.replace('\\"', '"')
        
        # Additional fixes for common patterns that got corrupted
        
        # Fix try blocks that got mangled
        content_str = re.sub(r'try:\s*\n\s*#', 'try:\n            #', content_str)
        
        # Fix except blocks
        content_str = re.sub(r'except Exception as e:\s*\n\s*logger\.error', 'except Exception as e:\n            logger.error', content_str)
        
        # Fix return statements
        content_str = re.sub(r'return \{\s*\n\s*"', 'return {\n            "', content_str)
        
        # Fix dictionary formatting
        content_str = re.sub(r'(\s+)"([^"]+)":\s*([^,\n}]+),?\s*\n', r'\1"\2": \3,\n', content_str)
        
        # Fix function definitions that got split
        content_str = re.sub(r'def ([^(]+)\([^)]*\)\s*->\s*([^:]+):\s*\n\s*"""', r'def \1() -> \2:\n        """', content_str)
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_str)
        
        return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all corrupted files in the ideation module."""
    ideation_dir = Path("src/codexes/modules/ideation")
    
    if not ideation_dir.exists():
        print(f"Directory {ideation_dir} not found")
        return False
    
    # Get all Python files
    py_files = list(ideation_dir.rglob("*.py"))
    print(f"Checking {len(py_files)} Python files for corruption...")
    
    fixed_count = 0
    for py_file in py_files:
        if fix_file_completely(py_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} corrupted files")
    
    # Test compilation of all files
    print("\nTesting compilation...")
    failed_files = []
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            failed_files.append((py_file, str(e)))
        except Exception as e:
            failed_files.append((py_file, f"Other error: {str(e)}"))
    
    if failed_files:
        print(f"\n❌ {len(failed_files)} files still have syntax errors:")
        for file_path, error in failed_files[:5]:  # Show first 5
            print(f"  - {file_path.name}: {error}")
        if len(failed_files) > 5:
            print(f"  ... and {len(failed_files) - 5} more")
        return False
    else:
        print("\n✅ All files compile successfully!")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)