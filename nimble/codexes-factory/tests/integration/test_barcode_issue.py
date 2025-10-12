#!/usr/bin/env python3
"""
Test script to reproduce the barcode_draw_command issue
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.covers.cover_generator import create_cover_latex

# Test data with 'nan' ISBN
test_data = {
    'title': 'Test Book',
    'author': 'Test Author',
    'isbn13': 'nan',  # This should trigger the issue
    'imprint': 'test imprint',
    'back_cover_text': 'Test back cover text'
}

# Test paths
output_dir = Path("test_output")
template_path = Path("templates/template.tex")  # This might not exist, but that's ok for this test
build_dir = Path("test_build")
replacements = {}

# Create directories
output_dir.mkdir(exist_ok=True)
build_dir.mkdir(exist_ok=True)

try:
    result = create_cover_latex(
        json_path=None,  # We're passing data directly
        output_dir=output_dir,
        template_path=template_path,
        build_dir=build_dir,
        replacements=replacements,
        debug_mode=True,
        data=test_data
    )
    print("✅ Test completed successfully")
except Exception as e:
    print(f"❌ Error occurred: {e}")
    import traceback
    traceback.print_exc()