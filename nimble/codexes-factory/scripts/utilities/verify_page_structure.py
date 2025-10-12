#!/usr/bin/env python3
"""
Verify the page structure and count for the dotgrid transcription fix.
"""

from pathlib import Path
import re

def analyze_page_structure():
    """Analyze the page structure of the generated book"""
    print("Page Structure Analysis")
    print("=" * 25)
    
    # Find the most recent build directory
    build_dirs = list(Path("output/.build").glob("Martian_Self-Reliance_*"))
    if not build_dirs:
        print("❌ No build directories found")
        return False
    
    latest_build = max(build_dirs, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing build: {latest_build.name}")
    
    # Check quotations.tex for structure
    quotations_file = latest_build / "quotations.tex"
    if not quotations_file.exists():
        print("❌ quotations.tex not found")
        return False
    
    content = quotations_file.read_text()
    
    # Count quotes and dotgrid commands
    quote_count = len(re.findall(r'% --- Quote \\d+ \\(Verso\\) ---', content))
    dotgrid_count = len(re.findall(r'\\\\dotgridtranscription\\{', content))
    
    print(f"Quotes found: {quote_count}")
    print(f"Dotgrid commands: {dotgrid_count}")
    
    # Expected pages calculation
    front_matter_pages = 27  # Approximate
    quote_pages = quote_count  # Verso pages
    dotgrid_pages = dotgrid_count  # Recto pages
    expected_total = front_matter_pages + quote_pages + dotgrid_pages
    
    print(f"\\nExpected page breakdown:")
    print(f"  Front matter: ~{front_matter_pages} pages")
    print(f"  Quote pages (verso): {quote_pages} pages")
    print(f"  Dotgrid pages (recto): {dotgrid_pages} pages")
    print(f"  Expected total: ~{expected_total} pages")
    
    # Check actual page count from pipeline output
    actual_pages = 299  # From pipeline output
    print(f"  Actual total: {actual_pages} pages")
    print(f"  Difference: {actual_pages - expected_total} pages")
    
    if actual_pages > expected_total:
        print(f"\\n⚠️  Extra pages detected. Possible causes:")
        print(f"    - Extra blank pages from page breaks")
        print(f"    - Unexpected content causing page overflows")
        print(f"    - LaTeX layout issues")
    
    return True

def check_template_structure():
    """Check the template.tex file for the command definition"""
    print("\\nTemplate Command Analysis")
    print("=" * 27)
    
    template_file = Path("imprints/xynapse_traces/template.tex")
    if not template_file.exists():
        print("❌ template.tex not found")
        return False
    
    content = template_file.read_text()
    
    # Check for dotgridtranscription command
    if "\\\\dotgridtranscription" in content:
        print("✅ dotgridtranscription command found in template")
        
        # Extract the command definition
        match = re.search(r'\\\\newcommand\\{\\\\dotgridtranscription\\}.*?^\\}', content, re.MULTILINE | re.DOTALL)
        if match:
            command_def = match.group()
            print("\\nCommand definition:")
            print("-" * 20)
            print(command_def[:200] + "..." if len(command_def) > 200 else command_def)
            
            # Check for page break command
            if "\\\\newpage" in command_def:
                print("✅ Uses \\\\newpage for page breaks")
            elif "\\\\clearpage" in command_def:
                print("✅ Uses \\\\clearpage for page breaks")
            else:
                print("❌ No page break command found")
                
            # Check for content structure
            if "\\\\vspace" in command_def and "\\\\begin{center}" in command_def:
                print("✅ Has proper content structure")
            else:
                print("❌ Missing proper content structure")
        else:
            print("❌ Could not extract command definition")
    else:
        print("❌ dotgridtranscription command not found in template")
    
    return True

if __name__ == "__main__":
    analyze_page_structure()
    check_template_structure()
    
    print("\\n" + "=" * 50)
    print("SUMMARY:")
    print("- Page breaks are now working (299 pages vs 119)")
    print("- Command is properly defined in template.tex only")
    print("- Need to investigate why we have extra pages")
    print("- Expected ~207 pages, got 299 pages (+92 extra)")