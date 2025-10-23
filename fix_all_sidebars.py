#!/usr/bin/env python3
"""
Fix all pages to check sidebar_rendered flag before calling render_unified_sidebar.
This prevents duplicate sidebar rendering when main app already renders it.
"""

import re
from pathlib import Path

# Files to fix
files = [
    "nimble/codexes-factory/src/codexes/pages/1_Home.py",
    "nimble/codexes-factory/src/codexes/pages/10_Book_Pipeline.py",
    "nimble/codexes-factory/src/codexes/pages/11_Backmatter_Manager.py",
    "nimble/codexes-factory/src/codexes/pages/12_Bibliography_Shopping.py",
    "nimble/codexes-factory/src/codexes/pages/15_Ideation_and_Development.py",
    "nimble/codexes-factory/src/codexes/pages/16_Stage_Agnostic_UI.py",
    "nimble/codexes-factory/src/codexes/pages/17_Marketing_Generator.py",
    "nimble/codexes-factory/src/codexes/pages/18_Imprint_Administration.py",
    "nimble/codexes-factory/src/codexes/pages/18_Publication_Manager.py",
    "nimble/codexes-factory/src/codexes/pages/2_Annotated_Bibliography.py",
    "nimble/codexes-factory/src/codexes/pages/20_Enhanced_Imprint_Creator.py",
    "nimble/codexes-factory/src/codexes/pages/21_Imprint_Ideas_Tournament.py",
    "nimble/codexes-factory/src/codexes/pages/22_AI_Social_Feed.py",
    "nimble/codexes-factory/src/codexes/pages/23_ISBN_Schedule_Manager.py",
    "nimble/codexes-factory/src/codexes/pages/23_Profile_Home.py",
    "nimble/codexes-factory/src/codexes/pages/24_ISBN_Management.py",
    "nimble/codexes-factory/src/codexes/pages/25_Rights_Management.py",
    "nimble/codexes-factory/src/codexes/pages/25_Schedule_ISBN_Manager.py",
    "nimble/codexes-factory/src/codexes/pages/26_Rights_Analytics.py",
    "nimble/codexes-factory/src/codexes/pages/27_Max_Bialystok_Financial.py",
    "nimble/codexes-factory/src/codexes/pages/28_Leo_Bloom_Analytics.py",
    "nimble/codexes-factory/src/codexes/pages/29_Imprint_Financial_Dashboard.py",
    "nimble/codexes-factory/src/codexes/pages/3_Manuscript_Enhancement.py",
    "nimble/codexes-factory/src/codexes/pages/30_Books_In_Print_Financial.py",
    "nimble/codexes-factory/src/codexes/pages/30_Sales_Analysis.py",
    "nimble/codexes-factory/src/codexes/pages/32_PDF_Harvester.py",
    "nimble/codexes-factory/src/codexes/pages/4_Metadata_and_Distribution.py",
    "nimble/codexes-factory/src/codexes/pages/5_Settings_and_Commerce.py",
    "nimble/codexes-factory/src/codexes/pages/6_Bookstore.py",
    "nimble/codexes-factory/src/codexes/pages/7_Admin_Dashboard.py",
    "nimble/codexes-factory/src/codexes/pages/9_Imprint_Builder.py",
    "nimble/codexes-factory/src/codexes/pages/ideation_dashboard.py",
    "nimble/codexes-factory/src/codexes/pages/tournament_interface.py",
]

def fix_file(filepath):
    """Fix a single file to check sidebar_rendered flag."""
    path = Path(filepath)
    if not path.exists():
        print(f"⚠️  Skipping {filepath} - file not found")
        return False

    content = path.read_text()

    # Skip if already has the check
    if "sidebar_rendered" in content:
        print(f"✓ Skipping {path.name} - already has sidebar_rendered check")
        return False

    # Pattern to match render_unified_sidebar calls (with various indentation and parameters)
    # This matches the call and captures the indentation
    pattern = r'(\s*)render_unified_sidebar\('

    def replace_func(match):
        indent = match.group(1)
        # Add the conditional check before the call
        return (
            f"{indent}# Render unified sidebar only if not already rendered by main app\n"
            f"{indent}# Main app sets sidebar_rendered=True to prevent duplication\n"
            f"{indent}if not st.session_state.get('sidebar_rendered', False):\n"
            f"{indent}    render_unified_sidebar("
        )

    # Check if file contains render_unified_sidebar
    if "render_unified_sidebar(" not in content:
        print(f"⚠️  Skipping {path.name} - no render_unified_sidebar call found")
        return False

    # Replace the pattern
    new_content = re.sub(pattern, replace_func, content)

    # We also need to add extra indentation to the closing parenthesis and parameters
    # This is tricky, so let's do a more sophisticated approach
    # Split by lines and process
    lines = content.split('\n')
    new_lines = []
    in_render_call = False
    call_indent = ""

    for i, line in enumerate(lines):
        if 'render_unified_sidebar(' in line and 'sidebar_rendered' not in '\n'.join(lines[max(0,i-3):i]):
            # Found the start of a call that doesn't have the check
            call_indent = len(line) - len(line.lstrip())
            indent_str = ' ' * call_indent

            # Add the check
            new_lines.append(f"{indent_str}# Render unified sidebar only if not already rendered by main app")
            new_lines.append(f"{indent_str}# Main app sets sidebar_rendered=True to prevent duplication")
            new_lines.append(f"{indent_str}if not st.session_state.get('sidebar_rendered', False):")

            # Add the indented render call
            new_lines.append(' ' * 4 + line)
            in_render_call = True
        elif in_render_call:
            # Inside the function call - add extra indentation
            if line.strip() and not line.strip().startswith('#'):
                # Add 4 spaces of indentation
                new_lines.append(' ' * 4 + line)
                # Check if this is the closing parenthesis
                if ')' in line and line.strip().endswith(')'):
                    in_render_call = False
            else:
                # Empty line or comment - keep as is
                new_lines.append(line)
        else:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)

    # Write back
    path.write_text(new_content)
    print(f"✅ Fixed {path.name}")
    return True

def main():
    print("Fixing sidebar duplication in all pages...")
    print(f"Found {len(files)} files to check\n")

    fixed_count = 0
    for filepath in files:
        if fix_file(filepath):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")
    print(f"⚠️  Skipped {len(files) - fixed_count} files (already fixed or no render_unified_sidebar)")

if __name__ == "__main__":
    main()
