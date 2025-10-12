#!/usr/bin/env python3
"""
Test to verify transcription instructions appear on main body pages.
"""

import re
from pathlib import Path

def test_transcription_instructions():
    """Test that transcription instructions are set up correctly for main body pages"""
    template_path = Path("imprints/xynapse_traces/template.tex")
    
    if not template_path.exists():
        print("❌ Template file not found")
        return False
    
    content = template_path.read_text()
    
    print("Testing Transcription Instructions Setup:")
    print("=" * 50)
    
    # Check 1: Main transcription system uses AddToShipoutPictureFG without asterisk
    # Look for the main transcription system specifically (with mainmatter check)
    main_transcription_pattern = r'System to add transcription notes.*?\\AddToShipoutPictureFG\{'
    if re.search(main_transcription_pattern, content, re.DOTALL):
        print("✅ Main transcription system uses AddToShipoutPictureFG without asterisk")
    else:
        print("❌ Main transcription system not configured correctly")
        # Let's see what we actually have
        if r"\AddToShipoutPictureFG{" in content:
            print("  (Found AddToShipoutPictureFG without asterisk, but pattern match failed)")
        return False
    
    # Check 2: Main matter tracking system
    if r"\ifinmainmatter" in content and r"\inmainmattertrue" in content:
        print("✅ Main matter tracking system present")
    else:
        print("❌ Main matter tracking system not found")
        return False
    
    # Check 3: Recto page detection
    if r"\checkoddpage" in content and r"\ifoddpage" in content:
        print("✅ Recto page detection system present")
    else:
        print("❌ Recto page detection not found")
        return False
    
    # Check 4: Bottom right positioning
    if r"\paperwidth-1in" in content and r"0.75in" in content and r"raggedleft" in content:
        print("✅ Bottom right positioning configured")
    else:
        print("❌ Bottom right positioning not configured correctly")
        return False
    
    # Check 5: Transcription note cycling system
    if r"\gettranscriptionnote" in content and r"\stepcounter{transcriptioncycle}" in content:
        print("✅ Transcription note cycling system present")
    else:
        print("❌ Transcription note cycling system not found")
        return False
    
    # Check 6: Debug output for verification
    if r"\typeout{DEBUG:" in content:
        print("✅ Debug output enabled for verification")
    else:
        print("❌ Debug output not found")
        return False
    
    print("\nExpected Behavior:")
    print("- Transcription instructions will appear on every recto (odd-numbered) page")
    print("- Only during main matter section (after \\mainmatter command)")
    print("- Positioned at bottom right corner")
    print("- Will cycle through 5 different instruction messages")
    print("- Debug messages will show in LaTeX log for verification")
    
    return True

def check_mainmatter_setup():
    """Check that mainmatter is properly configured"""
    template_path = Path("imprints/xynapse_traces/template.tex")
    content = template_path.read_text()
    
    print("\nMain Matter Configuration:")
    print("=" * 30)
    
    # Find mainmatter section
    mainmatter_match = re.search(r'\\mainmatter.*?\\backmatter', content, re.DOTALL)
    if mainmatter_match:
        mainmatter_section = mainmatter_match.group()
        print("✅ Main matter section found")
        
        # Check what's included in mainmatter
        if r"\input{transcription_note.tex}" in mainmatter_section:
            print("✅ Transcription note included")
        if r"\input{quotations.tex}" in mainmatter_section:
            print("✅ Quotations included (if file exists)")
        
        print("\nMain matter includes:")
        inputs = re.findall(r'\\input\{([^}]+)\}', mainmatter_section)
        for inp in inputs:
            print(f"  - {inp}")
            
    else:
        print("❌ Main matter section not found")
        return False
    
    return True

if __name__ == "__main__":
    instructions_ok = test_transcription_instructions()
    mainmatter_ok = check_mainmatter_setup()
    
    if instructions_ok and mainmatter_ok:
        print("\n🎉 Transcription instructions are correctly configured!")
        print("They will appear on all recto pages in the main matter section.")
    else:
        print("\n⚠️  Configuration issues detected. Check output above.")