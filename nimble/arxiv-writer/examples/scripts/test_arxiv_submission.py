#!/usr/bin/env python3
"""
Test script for arXiv submission preparation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.arxiv_paper.arxiv_validator import ArxivValidator, ArxivSubmissionPreparator
from codexes.modules.arxiv_paper.arxiv_metadata_generator import ArxivMetadataGenerator

def test_arxiv_submission():
    """Test the arXiv submission preparation."""
    paper_dir = "output/arxiv_paper"
    output_dir = "output/arxiv_submission"
    
    print("🚀 Testing arXiv submission preparation...")
    print(f"   Paper directory: {paper_dir}")
    print(f"   Output directory: {output_dir}")
    print()
    
    # Test validation
    print("📋 Testing validation...")
    validator = ArxivValidator(paper_dir)
    results = validator.validate_all()
    
    errors = [r for r in results if r.severity == 'error']
    warnings = [r for r in results if r.severity == 'warning']
    
    print(f"   Found {len(errors)} errors, {len(warnings)} warnings")
    
    if errors:
        print("   Errors:")
        for error in errors:
            print(f"      ❌ {error.message}")
    
    if warnings:
        print("   Warnings:")
        for warning in warnings:
            print(f"      ⚠️  {warning.message}")
    
    print()
    
    # Test metadata generation
    print("📝 Testing metadata generation...")
    metadata_gen = ArxivMetadataGenerator(paper_dir)
    metadata = metadata_gen.extract_metadata_from_latex()
    
    print(f"   Title: {metadata.title}")
    print(f"   Authors: {len(metadata.authors)}")
    print(f"   Categories: {metadata.categories}")
    print(f"   Keywords: {len(metadata.keywords)}")
    print()
    
    # Test package creation
    print("📦 Testing package creation...")
    preparator = ArxivSubmissionPreparator(paper_dir)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    package = preparator.create_submission_package(output_dir)
    
    print(f"   Main file: {package.main_tex_file}")
    print(f"   Source files: {len(package.source_files)}")
    print(f"   Figure files: {len(package.figure_files)}")
    print(f"   Bibliography files: {len(package.bibliography_files)}")
    print(f"   Total size: {package.total_size_mb:.1f} MB")
    print()
    
    # Generate metadata files
    print("📄 Generating metadata files...")
    
    # Submission form
    form_text = metadata_gen.generate_arxiv_submission_form(metadata)
    form_file = Path(output_dir) / "arxiv_submission_form.txt"
    form_file.write_text(form_text, encoding='utf-8')
    print(f"   ✅ {form_file}")
    
    # JSON metadata
    import json
    json_metadata = metadata_gen.generate_submission_metadata_json(metadata)
    json_file = Path(output_dir) / "submission_metadata.json"
    json_file.write_text(json.dumps(json_metadata, indent=2), encoding='utf-8')
    print(f"   ✅ {json_file}")
    
    # ArXiv abstract
    arxiv_abstract = metadata_gen.create_arxiv_ready_abstract(metadata)
    abstract_file = Path(output_dir) / "arxiv_abstract.txt"
    abstract_file.write_text(arxiv_abstract, encoding='utf-8')
    print(f"   ✅ {abstract_file}")
    
    # Validation report
    validation_report = validator.generate_report()
    report_file = Path(output_dir) / "validation_report.txt"
    report_file.write_text(validation_report, encoding='utf-8')
    print(f"   ✅ {report_file}")
    
    # Create ZIP
    zip_path = preparator.create_zip_package(output_dir)
    print(f"   ✅ {zip_path}")
    
    print()
    print("🎉 ArXiv submission preparation completed!")
    print(f"   📁 Files in: {output_dir}")
    
    # List created files
    output_path = Path(output_dir)
    files = list(output_path.iterdir())
    print(f"   📄 Created {len(files)} files:")
    for file in sorted(files):
        size = file.stat().st_size if file.is_file() else 0
        print(f"      - {file.name} ({size} bytes)")

if __name__ == "__main__":
    test_arxiv_submission()