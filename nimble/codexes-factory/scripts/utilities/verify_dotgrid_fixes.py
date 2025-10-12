#!/usr/bin/env python3
"""
Verify that the dotgrid positioning fixes have been applied correctly.
"""

import re
from pathlib import Path

def verify_template_fixes():
    """Verify the template has the correct fixes applied"""
    template_path = Path("imprints/xynapse_traces/template.tex")
    
    if not template_path.exists():
        print("❌ Template file not found")
        return False
    
    content = template_path.read_text()
    
    fixes_verified = []
    
    # Check 1: Dotgrid positioned with top edge 1.5" from top (paperheight-4.5in for 6in image)
    if r"\paperheight-4.5in" in content:
        fixes_verified.append("✅ Dotgrid positioned 1.5\" from top paper edge")
    elif r"\paperheight-1.5in" in content:
        fixes_verified.append("⚠️  Dotgrid at reference point 1.5\" from top (may need adjustment)")
    else:
        fixes_verified.append("❌ Dotgrid positioning not found")
    
    # Check 2: Dotgrid horizontally centered (0.5\paperwidth)
    if r"0.5\paperwidth" in content and (r"\paperheight-4.5in" in content or r"\paperheight-1.5in" in content):
        fixes_verified.append("✅ Dotgrid horizontally centered")
    else:
        fixes_verified.append("❌ Dotgrid horizontal centering not found")
    
    # Check 3: Transcription instructions at bottom right on recto pages
    if r"\paperwidth-1in" in content and r"0.75in" in content and "raggedleft" in content:
        fixes_verified.append("✅ Transcription instructions positioned at bottom right")
    else:
        fixes_verified.append("❌ Transcription instruction positioning not found")
    
    # Check 4: Minipage structure removed from dotgrid command
    dotgrid_section = re.search(r'\\newcommand\{\\dotgridtranscription\}.*?^\}', content, re.MULTILINE | re.DOTALL)
    if dotgrid_section and "minipage" not in dotgrid_section.group():
        fixes_verified.append("✅ Minipage structure removed from dotgrid command")
    else:
        fixes_verified.append("❌ Minipage structure still present or command not found")
    
    # Check 5: Direct positioning used instead of vspace/centering
    if r"\AddToShipoutPictureBG*" in content and r"\AddToShipoutPictureFG*" in content:
        fixes_verified.append("✅ Direct positioning with AddToShipoutPicture used")
    else:
        fixes_verified.append("❌ Direct positioning not implemented")
    
    print("Dotgrid Template Fix Verification:")
    print("=" * 50)
    for fix in fixes_verified:
        print(f"  {fix}")
    
    # Summary
    success_count = sum(1 for fix in fixes_verified if fix.startswith("✅"))
    total_count = len(fixes_verified)
    
    print(f"\nSummary: {success_count}/{total_count} fixes verified")
    
    if success_count == total_count:
        print("🎉 All dotgrid fixes have been successfully applied!")
        return True
    else:
        print("⚠️  Some fixes may need attention")
        return False

def verify_positioning_logic():
    """Verify the positioning logic matches requirements"""
    print("\nPositioning Logic Verification:")
    print("=" * 50)
    
    # Expected positioning for 9in x 6in page
    page_height = 9.0  # inches
    dotgrid_from_top = 1.5  # inches (user requirement)
    
    # LaTeX coordinate (from bottom)
    latex_y_coord = page_height - dotgrid_from_top
    
    print(f"  Page height: {page_height}\"")
    print(f"  Dotgrid from top: {dotgrid_from_top}\"")
    print(f"  LaTeX Y coordinate: {latex_y_coord}\" (from bottom)")
    print(f"  Expected LaTeX command: \\put(\\LenToUnit{{0.5\\paperwidth}},\\LenToUnit{{\\paperheight-4.5in}})")
    print(f"  (Centers 6\" image with top edge 1.5\" from top)")
    
    # Verify this matches template
    template_path = Path("imprints/xynapse_traces/template.tex")
    if template_path.exists():
        content = template_path.read_text()
        if r"\paperheight-4.5in" in content:
            print("  ✅ Template uses correct positioning formula")
        else:
            print("  ❌ Template positioning formula incorrect")
    
    return True

if __name__ == "__main__":
    template_ok = verify_template_fixes()
    positioning_ok = verify_positioning_logic()
    
    if template_ok and positioning_ok:
        print("\n🎉 All verifications passed! The dotgrid fixes are correctly implemented.")
    else:
        print("\n⚠️  Some verifications failed. Please check the output above.")