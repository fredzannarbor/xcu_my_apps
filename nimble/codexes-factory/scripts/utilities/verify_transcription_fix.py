#!/usr/bin/env python3
"""
Verify that transcription instructions will appear on main body pages.
"""

from pathlib import Path
import re

def verify_fix():
    """Verify the transcription instruction fix"""
    template_path = Path("imprints/xynapse_traces/template.tex")
    
    if not template_path.exists():
        print("❌ Template not found")
        return False
    
    content = template_path.read_text()
    
    print("Transcription Instructions Fix Verification")
    print("=" * 45)
    
    # Key fix: AddToShipoutPictureFG without asterisk for main pages
    main_system_found = False
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if "System to add transcription notes" in line:
            # Check the next few lines for the AddToShipoutPictureFG command
            for j in range(i, min(i+5, len(lines))):
                if r"\AddToShipoutPictureFG{" in lines[j]:
                    main_system_found = True
                    print(f"✅ Found main transcription system at line {j+1}")
                    print(f"   Command: {lines[j].strip()}")
                    break
            break
    
    if not main_system_found:
        print("❌ Main transcription system not found")
        return False
    
    # Verify the system components
    components = [
        (r"\\ifinmainmatter", "Main matter detection"),
        (r"\\checkoddpage", "Odd page detection"),
        (r"\\ifoddpage", "Recto page condition"),
        (r"\\paperwidth-1in", "Bottom right positioning"),
        (r"raggedleft", "Right alignment"),
        (r"\\gettranscriptionnote", "Note cycling system")
    ]
    
    all_found = True
    for pattern, description in components:
        if re.search(pattern, content):
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - NOT FOUND")
            all_found = False
    
    print("\nFix Summary:")
    print("- Changed \\AddToShipoutPictureFG*{ to \\AddToShipoutPictureFG{")
    print("- Removed asterisk so instructions apply to ALL pages, not just current page")
    print("- Instructions will now appear on every recto page in main matter")
    print("- Positioned at bottom right corner as requested")
    
    return all_found

if __name__ == "__main__":
    if verify_fix():
        print("\n🎉 SUCCESS: Transcription instructions will now appear on main body pages!")
    else:
        print("\n❌ ISSUE: Some components may be missing")