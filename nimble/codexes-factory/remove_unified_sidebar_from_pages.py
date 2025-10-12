#!/usr/bin/env python3
"""
Remove render_unified_sidebar() calls from individual pages.
The main entry point (codexes-factory-home-ui.py) now handles this.
"""

import re
from pathlib import Path

# Find all Python files in pages directory
pages_dir = Path(__file__).parent / "src/codexes/pages"
page_files = list(pages_dir.glob("*.py"))

print(f"Found {len(page_files)} page files")

for page_file in page_files:
    print(f"\nProcessing: {page_file.name}")

    # Read the file
    content = page_file.read_text()
    original_content = content

    # Remove the import line for render_unified_sidebar
    content = re.sub(
        r'from shared\.ui import render_unified_sidebar\n?',
        '',
        content
    )

    # Remove the render_unified_sidebar() call and its arguments
    # Pattern matches multi-line function call
    content = re.sub(
        r'render_unified_sidebar\s*\([^)]*\)\s*\n?',
        '',
        content,
        flags=re.MULTILINE
    )

    # More aggressive pattern for multi-line calls
    content = re.sub(
        r'render_unified_sidebar\s*\(\s*\n.*?^\)\s*$',
        '',
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    # Clean up any double blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)

    # Check if anything changed
    if content != original_content:
        # Backup original
        backup_file = page_file.with_suffix('.py.sidebar_backup')
        backup_file.write_text(original_content)

        # Write updated content
        page_file.write_text(content)
        print(f"  ✓ Updated (backup: {backup_file.name})")
    else:
        print(f"  - No changes needed")

print("\n✅ Done! All pages updated.")
print("Backups saved with .sidebar_backup extension")
