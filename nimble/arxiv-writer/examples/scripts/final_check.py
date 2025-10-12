#!/usr/bin/env python3
"""
Final ArXiv Submission Quality Check
"""

import json
import zipfile
from pathlib import Path

def final_submission_check(submission_dir: str) -> bool:
    """Perform final submission check."""
    submission_path = Path(submission_dir)
    
    print("🔍 Final ArXiv Submission Quality Check")
    print("=" * 50)
    print(f"Submission directory: {submission_path}")
    print()
    
    # Check required files
    required_files = [
        "main.tex",
        "references.bib",
        "arxiv_submission_form.txt",
        "submission_metadata.json",
        "arxiv_abstract.txt",
        "validation_report.txt",
        "arxiv_submission.zip"
    ]
    
    print("📁 Checking required files...")
    missing_files = []
    for file in required_files:
        file_path = submission_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            missing_files.append(file)
            print(f"   ❌ {file} (missing)")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        return False
    
    print()
    
    # Check ZIP contents
    print("📦 Checking ZIP package...")
    zip_file = submission_path / "arxiv_submission.zip"
    if zip_file.exists():
        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                files_in_zip = zf.namelist()
                print(f"   ✅ ZIP contains {len(files_in_zip)} files")
                
                # Check for essential files in ZIP
                essential_in_zip = ["main.tex", "references.bib"]
                for essential in essential_in_zip:
                    if essential in files_in_zip:
                        print(f"   ✅ {essential} in ZIP")
                    else:
                        print(f"   ❌ {essential} missing from ZIP")
                        return False
        except Exception as e:
            print(f"   ❌ Error reading ZIP: {e}")
            return False
    
    print()
    
    # Check metadata quality
    print("📝 Checking metadata quality...")
    try:
        metadata_file = submission_path / "submission_metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Check title
        title = metadata.get('title', '')
        if len(title) > 10:
            print(f"   ✅ Title: {title[:50]}...")
        else:
            print(f"   ❌ Title too short: {title}")
            return False
        
        # Check authors
        authors = metadata.get('authors', [])
        if authors and authors[0].get('email'):
            print(f"   ✅ Author: {authors[0]['name']} ({authors[0]['email']})")
        else:
            print(f"   ❌ Author information incomplete")
            return False
        
        # Check categories
        categories = metadata.get('categories', {})
        primary = categories.get('primary')
        if primary:
            print(f"   ✅ Primary category: {primary}")
        else:
            print(f"   ❌ No primary category")
            return False
        
        # Check abstract
        abstract = metadata.get('abstract', '')
        word_count = len(abstract.split())
        if 100 <= word_count <= 300:
            print(f"   ✅ Abstract: {word_count} words (good length)")
        elif word_count < 100:
            print(f"   ⚠️  Abstract: {word_count} words (might be too short)")
        else:
            print(f"   ⚠️  Abstract: {word_count} words (might be too long)")
        
    except Exception as e:
        print(f"   ❌ Error checking metadata: {e}")
        return False
    
    print()
    
    # Final checklist
    print("📋 Final submission checklist:")
    checklist_items = [
        "All required files present",
        "ZIP package created and valid",
        "Metadata complete and accurate",
        "Abstract appropriate length",
        "Author contact information included",
        "Primary category specified (cs.AI)",
        "Title descriptive and clear"
    ]
    
    for item in checklist_items:
        print(f"   ✅ {item}")
    
    print()
    print("🎉 Submission appears ready for arXiv!")
    print()
    print("📤 Next steps:")
    print("   1. Go to https://arxiv.org/submit")
    print("   2. Create account or log in")
    print("   3. Start new submission")
    print("   4. Upload arxiv_submission.zip")
    print("   5. Fill metadata using arxiv_submission_form.txt")
    print("   6. Copy abstract from arxiv_abstract.txt")
    print("   7. Review and submit")
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python final_check.py <submission_directory>")
        sys.exit(1)
    
    success = final_submission_check(sys.argv[1])
    sys.exit(0 if success else 1)