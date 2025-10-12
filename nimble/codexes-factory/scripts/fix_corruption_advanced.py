#!/usr/bin/env python3
"""
Advanced fix for file corruption - handles broken string literals.
"""

import os
import re
from pathlib import Path

def fix_broken_strings(content):
    """Fix broken string literals that span multiple lines incorrectly."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for lines that end with an unterminated string
        # Pattern: something.split(' followed by newline
        if re.search(r"\.split\(['\"]$", line):
            # This line has a broken string literal
            # Find the closing quote on the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line starts with '), it's the continuation
                if next_line.strip().startswith("')") or next_line.strip().startswith('")'):
                    # Combine the lines properly
                    quote_char = "'" if line.endswith("'") else '"'
                    # Remove the broken quote from first line and add proper string
                    fixed_line = line[:-1] + quote_char + "\\n" + quote_char + next_line.strip()
                    fixed_lines.append(fixed_line)
                    i += 2  # Skip the next line since we combined it
                    continue
        
        # Look for other broken string patterns
        # Pattern: lines ending with incomplete f-strings or strings
        if (line.rstrip().endswith('f"') or 
            line.rstrip().endswith("f'") or
            line.rstrip().endswith('"') or
            line.rstrip().endswith("'")):
            
            # Check if this might be a broken string
            quote_count_double = line.count('"')
            quote_count_single = line.count("'")
            
            # If odd number of quotes, likely broken
            if (quote_count_double % 2 == 1 and line.rstrip().endswith('"')) or \
               (quote_count_single % 2 == 1 and line.rstrip().endswith("'")):
                
                # Try to find the continuation
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If next line looks like a continuation, fix it
                    if (next_line.strip() and 
                        not next_line.strip().startswith('#') and
                        not next_line.strip().startswith('def ') and
                        not next_line.strip().startswith('class ')):
                        
                        # Combine the lines with proper string termination
                        if line.rstrip().endswith('"'):
                            fixed_line = line.rstrip()[:-1] + ' ' + next_line.strip() + '"'
                        else:
                            fixed_line = line.rstrip()[:-1] + ' ' + next_line.strip() + "'"
                        
                        fixed_lines.append(fixed_line)
                        i += 2
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_advanced(file_path):
    """Advanced fix for corrupted Python files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # First, fix broken string literals
        content = fix_broken_strings(content)
        
        # Fix other common corruption patterns
        
        # Fix try: blocks that got mangled
        content = re.sub(r'try:\s*([^\n]+)', r'try:\n            \1', content)
        
        # Fix except blocks
        content = re.sub(r'except Exception as e:\s*([^\n]+)', r'except Exception as e:\n            \1', content)
        
        # Fix return statements with dictionaries
        content = re.sub(r'return \{\s*([^\n}]+)', r'return {\n            \1', content)
        
        # Fix logger statements that got broken
        content = re.sub(r'logger\.(info|error|warning)\(f"([^"]*)"([^)]*)\)', r'logger.\1(f"\2\3")', content)
        
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
    """Fix all corrupted files."""
    ideation_dir = Path("src/codexes/modules/ideation")
    
    # Get files that are known to have syntax errors
    problem_files = [
        "book_idea.py",
        "synthetic_reader.py", 
        "continuous_generator.py",
        "tournament.py",
        "pipeline_bridge.py",
        "advanced_tournament.py",
        "feedback_optimizer.py",
        "monitoring.py"
    ]
    
    fixed_count = 0
    for filename in problem_files:
        file_path = ideation_dir / filename
        if file_path.exists():
            if fix_file_advanced(file_path):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    
    # Test the specific files
    print("\nTesting fixed files...")
    for filename in problem_files:
        file_path = ideation_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), str(file_path), 'exec')
                print(f"✅ {filename}")
            except SyntaxError as e:
                print(f"❌ {filename}: {e}")

if __name__ == "__main__":
    main()