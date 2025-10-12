#!/usr/bin/env python3
"""
Test dotgrid positioning to ensure it's 1.5" from top paper edge.
"""

import re
from pathlib import Path

def test_dotgrid_positioning():
    """Test that dotgrid is positioned correctly"""
    template_path = Path("imprints/xynapse_traces/template.tex")
    
    if not template_path.exists():
        print("❌ Template not found")
        return False
    
    content = template_path.read_text()
    
    print("Dotgrid Positioning Analysis")
    print("=" * 30)
    
    # Page specifications
    page_height = 9.0  # inches
    desired_top_margin = 1.5  # inches from top
    image_height = 6.0  # inches (as specified in template)
    
    print(f"Page height: {page_height}\"")
    print(f"Desired top margin: {desired_top_margin}\"")
    print(f"Image height: {image_height}\"")
    
    # Calculate where center should be
    image_center_from_top = desired_top_margin + (image_height / 2)
    image_center_from_bottom = page_height - image_center_from_top
    
    print(f"Image center should be {image_center_from_top}\" from top")
    print(f"Image center should be {image_center_from_bottom}\" from bottom")
    print(f"Expected LaTeX coordinate: \\paperheight-{image_center_from_top}in")
    
    # Check current positioning in template
    dotgrid_match = re.search(r'\\put\(\\LenToUnit\{0\.5\\paperwidth\},\\LenToUnit\{\\paperheight-([^}]+)\}\)', content)
    
    if dotgrid_match:
        current_position = dotgrid_match.group(1)
        print(f"\nCurrent template position: \\paperheight-{current_position}")
        
        if current_position == "4.5in":
            print("✅ Dotgrid positioned correctly for 1.5\" top margin")
        elif current_position == "1.5in":
            print("⚠️  Dotgrid positioned at reference point 1.5\" from top")
            print("   This may not account for image height properly")
        else:
            print(f"❓ Unexpected positioning: {current_position}")
    else:
        print("❌ Could not find dotgrid positioning in template")
        return False
    
    # Verify image dimensions
    image_match = re.search(r'includegraphics\[width=([^,]+),height=([^,]+),keepaspectratio\]', content)
    if image_match:
        width = image_match.group(1)
        height = image_match.group(2)
        print(f"\nImage dimensions in template: {width} × {height}")
        
        if height == "6in":
            print("✅ Image height matches calculation")
        else:
            print(f"⚠️  Image height ({height}) differs from expected (6in)")
    
    return True

if __name__ == "__main__":
    test_dotgrid_positioning()