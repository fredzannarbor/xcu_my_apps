#!/usr/bin/env python3
"""
Test script to verify dotgrid positioning fixes.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.prepress.dotgrid_layout_manager import DotgridLayoutManager, PageSpecs

def test_dotgrid_fixes():
    """Test the dotgrid positioning fixes"""
    print("Testing dotgrid positioning fixes...")
    
    # Initialize the layout manager
    layout_manager = DotgridLayoutManager()
    
    # Get standard page specs for xynapse_traces
    page_specs = layout_manager.get_standard_page_specs("xynapse_traces")
    print(f"Page specs: {page_specs}")
    
    # Calculate dotgrid position
    position = layout_manager.calculate_dotgrid_position(page_specs)
    print(f"Calculated position: x={position.x}, y={position.y}")
    
    # Validate spacing requirements
    is_valid = layout_manager.validate_spacing_requirements(position, page_specs)
    print(f"Spacing validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Test template update (dry run)
    template_path = "imprints/xynapse_traces/template.tex"
    if Path(template_path).exists():
        print(f"Template exists at: {template_path}")
        
        # Read template to verify changes
        with open(template_path, 'r') as f:
            content = f.read()
            
        # Check for the fixes
        fixes_applied = []
        
        # Check dotgrid horizontal centering
        if "0.5\\paperwidth" in content and "1.5in" in content:
            fixes_applied.append("✓ Dotgrid horizontal centering and vertical positioning")
        else:
            fixes_applied.append("✗ Dotgrid positioning not found")
            
        # Check transcription notes on every recto page
        if "every recto page in main matter (DEBUG MODE)" in content:
            fixes_applied.append("✓ Transcription notes set to every recto page")
        else:
            fixes_applied.append("✗ Transcription notes not updated")
            
        # Check transcription note positioning at bottom
        if "0.75in" in content and "\\small\\itshape" in content:
            fixes_applied.append("✓ Transcription notes positioned at bottom")
        else:
            fixes_applied.append("✗ Transcription note positioning not found")
            
        print("\nTemplate fixes status:")
        for fix in fixes_applied:
            print(f"  {fix}")
    else:
        print(f"Template not found at: {template_path}")
    
    print("\nFixes summary:")
    print("1. Dotgrid on recto pages moved down 0.5\" (from 2.0in to 1.5in)")
    print("2. Dotgrid horizontally centered (from 0.05\\paperwidth to 0.5\\paperwidth)")
    print("3. Transcription notes now print on every recto page at bottom (0.75in from bottom)")

if __name__ == "__main__":
    test_dotgrid_fixes()