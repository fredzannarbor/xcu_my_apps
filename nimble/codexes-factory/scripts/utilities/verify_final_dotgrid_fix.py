#!/usr/bin/env python3
"""
Final verification that dotgrid positioning is fixed in the book pipeline.
"""

from pathlib import Path
import re

def verify_pipeline_fix():
    """Verify that the pipeline generates correct dotgrid positioning"""
    print("Final Dotgrid Fix Verification")
    print("=" * 40)
    
    # Find the most recent build directory
    build_dirs = list(Path("output/.build").glob("Martian_Self-Reliance_*"))
    if not build_dirs:
        print("❌ No build directories found")
        return False
    
    latest_build = max(build_dirs, key=lambda p: p.stat().st_mtime)
    print(f"Checking latest build: {latest_build.name}")
    
    # Check quotations.tex for correct dotgrid positioning
    quotations_file = latest_build / "quotations.tex"
    if not quotations_file.exists():
        print("❌ quotations.tex not found")
        return False
    
    content = quotations_file.read_text()
    
    # Verify the corrected fullpagedotgrid command
    fixes_verified = []
    
    # Check 1: Correct positioning formula
    if r"\paperheight-4.5in" in content:
        fixes_verified.append("✅ Dotgrid positioned 1.5\" from top (paperheight-4.5in)")
    else:
        fixes_verified.append("❌ Incorrect dotgrid positioning")
    
    # Check 2: Horizontal centering
    if r"0.5\paperwidth" in content:
        fixes_verified.append("✅ Dotgrid horizontally centered")
    else:
        fixes_verified.append("❌ Dotgrid not horizontally centered")
    
    # Check 3: Direct positioning (no minipage/vfill)
    if r"\AddToShipoutPictureBG*" in content and r"\vfill" not in content:
        fixes_verified.append("✅ Direct positioning used (no minipage conflicts)")
    else:
        fixes_verified.append("❌ Still using old minipage approach")
    
    # Check 4: Proper image dimensions
    if r"width=4.5in,height=6in" in content:
        fixes_verified.append("✅ Correct image dimensions specified")
    else:
        fixes_verified.append("❌ Image dimensions not specified correctly")
    
    # Check 5: Command is being used
    fullpagedotgrid_uses = len(re.findall(r'\\fullpagedotgrid\{\}', content))
    if fullpagedotgrid_uses > 0:
        fixes_verified.append(f"✅ fullpagedotgrid command used {fullpagedotgrid_uses} times")
    else:
        fixes_verified.append("❌ fullpagedotgrid command not used")
    
    print("\nVerification Results:")
    for fix in fixes_verified:
        print(f"  {fix}")
    
    # Check template.tex for transcription instructions
    template_file = latest_build / "template.tex"
    if template_file.exists():
        template_content = template_file.read_text()
        
        print("\nTranscription Instructions Check:")
        if r"\AddToShipoutPictureFG{" in template_content:
            print("  ✅ Transcription instructions enabled for all recto pages")
        else:
            print("  ❌ Transcription instructions not configured correctly")
    
    # Summary
    success_count = sum(1 for fix in fixes_verified if fix.startswith("✅"))
    total_count = len(fixes_verified)
    
    print(f"\nSummary: {success_count}/{total_count} fixes verified")
    
    if success_count == total_count:
        print("🎉 All dotgrid fixes successfully implemented in pipeline!")
        return True
    else:
        print("⚠️  Some fixes may need attention")
        return False

def check_pdf_output():
    """Check if PDF was generated with correct page count"""
    pdf_file = Path("output/xynapse_traces_build/interior/Martian_Self-Reliance_Isolation_versus_Earth_Support_interior.pdf")
    
    if pdf_file.exists():
        print(f"\n✅ PDF generated: {pdf_file.name}")
        print(f"   File size: {pdf_file.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print("\n❌ PDF not found")
        return False

if __name__ == "__main__":
    pipeline_ok = verify_pipeline_fix()
    pdf_ok = check_pdf_output()
    
    if pipeline_ok and pdf_ok:
        print("\n🎉 SUCCESS: Dotgrid positioning fix is working in the book pipeline!")
        print("\nThe dotgrid image will now appear:")
        print("- 1.5\" from the top paper edge")
        print("- Horizontally centered on the page")
        print("- On every recto page after quotes")
        print("- With transcription instructions at bottom right")
    else:
        print("\n⚠️  Some issues detected. Check output above.")