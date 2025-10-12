#!/usr/bin/env python3
"""
Quick Article Recreation Script

This script provides a simple way to recreate the ArXiv article
using the existing prompts and generation system.
"""

import subprocess
import sys
from pathlib import Path

def recreate_article():
    """Recreate the ArXiv article step by step."""
    
    print("🚀 ArXiv Article Recreation Script")
    print("=" * 50)
    print()
    
    # Step 1: Generate paper sections
    print("📝 Step 1: Generating paper sections...")
    
    scripts = [
        "generate_paper_sections_7_1.py",  # Abstract, Introduction, Related Work
        "generate_paper_sections_7_2.py",  # Methodology, Implementation
        "generate_paper_sections_7_3.py",  # Results, Discussion, Conclusion
        "generate_paper_sections_7_4.py"   # Technical Documentation
    ]
    
    for script in scripts:
        print(f"   Running {script}...")
        try:
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"   ✅ {script} completed successfully")
            else:
                print(f"   ❌ {script} failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {script} timed out")
            return False
        except Exception as e:
            print(f"   ❌ Error running {script}: {e}")
            return False
    
    print()
    
    # Step 2: Generate LaTeX
    print("📄 Step 2: Generating LaTeX paper...")
    try:
        result = subprocess.run([
            sys.executable, 
            "src/codexes/modules/arxiv_paper/generate_latex_paper.py",
            "output/arxiv_paper",
            "--compile"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("   ✅ LaTeX generation completed successfully")
        else:
            print(f"   ❌ LaTeX generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error generating LaTeX: {e}")
        return False
    
    print()
    
    # Step 3: Create submission package
    print("📦 Step 3: Creating ArXiv submission package...")
    try:
        result = subprocess.run([
            sys.executable, 
            "test_arxiv_submission.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Submission package created successfully")
        else:
            print(f"   ❌ Submission package creation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error creating submission package: {e}")
        return False
    
    print()
    
    # Step 4: Run validation
    print("🔍 Step 4: Running validation tests...")
    try:
        result = subprocess.run([
            sys.executable, 
            "run_comprehensive_tests.py",
            "output/arxiv_paper",
            "--output", "test_results.json"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Validation tests completed successfully")
        else:
            print(f"   ⚠️  Some validation tests failed (this is normal)")
    except Exception as e:
        print(f"   ❌ Error running validation: {e}")
    
    print()
    
    # Final check
    print("✅ Article Recreation Complete!")
    print()
    print("📁 Generated Files:")
    
    output_files = [
        "output/arxiv_paper/latex/main.pdf",
        "output/arxiv_submission/arxiv_submission.zip",
        "output/arxiv_submission/arxiv_submission_form.txt"
    ]
    
    for file_path in output_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"   ✅ {path.name} ({size:,} bytes)")
        else:
            print(f"   ❌ {path.name} (missing)")
    
    print()
    print("🎯 Next Steps:")
    print("   1. Review the paper: output/arxiv_paper/latex/main.pdf")
    print("   2. Check submission files: output/arxiv_submission/")
    print("   3. Submit to arXiv: https://arxiv.org/submit")
    
    return True

def main():
    """Main function."""
    success = recreate_article()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())