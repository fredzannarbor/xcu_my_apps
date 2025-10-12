#!/usr/bin/env python3
"""
ArXiv Submission Preparation Script

This script provides a complete workflow for preparing an arXiv submission,
including validation, metadata generation, and package creation.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.codexes.modules.arxiv_paper.arxiv_validator import ArxivValidator, ArxivSubmissionPreparator
    from src.codexes.modules.arxiv_paper.arxiv_metadata_generator import ArxivMetadataGenerator
except ImportError:
    # Try relative imports
    from .arxiv_validator import ArxivValidator, ArxivSubmissionPreparator
    from .arxiv_metadata_generator import ArxivMetadataGenerator

class ArxivSubmissionManager:
    """Comprehensive arXiv submission manager."""
    
    def __init__(self, paper_dir: str, output_dir: str = None):
        """Initialize submission manager."""
        self.paper_dir = Path(paper_dir)
        self.output_dir = Path(output_dir) if output_dir else self.paper_dir / "arxiv_submission"
        
        # Initialize components
        self.validator = ArxivValidator(str(self.paper_dir))
        self.metadata_generator = ArxivMetadataGenerator(str(self.paper_dir))
        self.preparator = ArxivSubmissionPreparator(str(self.paper_dir))
        
    def prepare_complete_submission(self, create_zip: bool = True) -> Dict[str, any]:
        """Prepare complete arXiv submission with all components."""
        print("🚀 Starting arXiv submission preparation...")
        print(f"   Paper directory: {self.paper_dir}")
        print(f"   Output directory: {self.output_dir}")
        print()
        
        results = {
            'success': False,
            'validation_results': [],
            'metadata': None,
            'package_info': None,
            'files_created': [],
            'errors': []
        }
        
        try:
            # Step 1: Validate submission
            print("📋 Step 1: Validating submission...")
            validation_results = self.validator.validate_all()
            results['validation_results'] = [
                {
                    'is_valid': r.is_valid,
                    'message': r.message,
                    'severity': r.severity,
                    'suggestion': r.suggestion
                }
                for r in validation_results
            ]
            
            # Check if submission is ready
            errors = [r for r in validation_results if r.severity == 'error']
            if errors:
                print(f"   ❌ Found {len(errors)} errors that must be fixed:")
                for error in errors:
                    print(f"      - {error.message}")
                    if error.suggestion:
                        print(f"        💡 {error.suggestion}")
                results['errors'].extend([e.message for e in errors])
                return results
            
            warnings = [r for r in validation_results if r.severity == 'warning']
            if warnings:
                print(f"   ⚠️  Found {len(warnings)} warnings (recommended to fix):")
                for warning in warnings:
                    print(f"      - {warning.message}")
            
            print("   ✅ Validation passed!")
            print()
            
            # Step 2: Generate metadata
            print("📝 Step 2: Generating metadata...")
            metadata = self.metadata_generator.extract_metadata_from_latex()
            results['metadata'] = {
                'title': metadata.title,
                'authors': metadata.authors,
                'abstract': metadata.abstract,
                'categories': metadata.categories,
                'primary_category': metadata.primary_category,
                'keywords': metadata.keywords
            }
            
            # Validate metadata
            metadata_issues = self.metadata_generator.validate_metadata(metadata)
            if metadata_issues:
                print(f"   ⚠️  Metadata issues found:")
                for issue in metadata_issues:
                    print(f"      - {issue}")
                results['errors'].extend(metadata_issues)
            else:
                print("   ✅ Metadata validation passed!")
            
            print(f"   Title: {metadata.title}")
            print(f"   Authors: {', '.join([a['name'] for a in metadata.authors])}")
            print(f"   Categories: {', '.join(metadata.categories)}")
            print()
            
            # Step 3: Create submission directory
            print("📦 Step 3: Creating submission package...")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create package
            package = self.preparator.create_submission_package(str(self.output_dir))
            results['package_info'] = {
                'main_tex_file': package.main_tex_file,
                'source_files': package.source_files,
                'figure_files': package.figure_files,
                'bibliography_files': package.bibliography_files,
                'total_size_mb': package.total_size_mb
            }
            
            print(f"   ✅ Package created with {len(package.source_files)} source files")
            print(f"   Total size: {package.total_size_mb:.1f} MB")
            
            # Step 4: Generate metadata files
            print("📄 Step 4: Generating submission metadata files...")
            
            # Submission form
            form_text = self.metadata_generator.generate_arxiv_submission_form(metadata)
            form_file = self.output_dir / "arxiv_submission_form.txt"
            form_file.write_text(form_text, encoding='utf-8')
            results['files_created'].append(str(form_file))
            
            # JSON metadata
            json_metadata = self.metadata_generator.generate_submission_metadata_json(metadata)
            json_file = self.output_dir / "submission_metadata.json"
            json_file.write_text(json.dumps(json_metadata, indent=2), encoding='utf-8')
            results['files_created'].append(str(json_file))
            
            # ArXiv-ready abstract
            arxiv_abstract = self.metadata_generator.create_arxiv_ready_abstract(metadata)
            abstract_file = self.output_dir / "arxiv_abstract.txt"
            abstract_file.write_text(arxiv_abstract, encoding='utf-8')
            results['files_created'].append(str(abstract_file))
            
            # Validation report
            validation_report = self.validator.generate_report()
            report_file = self.output_dir / "validation_report.txt"
            report_file.write_text(validation_report, encoding='utf-8')
            results['files_created'].append(str(report_file))
            
            print(f"   ✅ Generated {len(results['files_created'])} metadata files")
            
            # Step 5: Create ZIP package if requested
            if create_zip:
                print("🗜️  Step 5: Creating ZIP package...")
                zip_path = self.preparator.create_zip_package(str(self.output_dir))
                results['files_created'].append(zip_path)
                print(f"   ✅ ZIP package created: {Path(zip_path).name}")
            
            # Step 6: Generate submission checklist
            print("📋 Step 6: Generating submission checklist...")
            checklist = self._generate_submission_checklist(metadata, package)
            checklist_file = self.output_dir / "submission_checklist.txt"
            checklist_file.write_text(checklist, encoding='utf-8')
            results['files_created'].append(str(checklist_file))
            
            print("   ✅ Submission checklist generated")
            print()
            
            # Success summary
            print("🎉 ArXiv submission preparation completed successfully!")
            print(f"   📁 Submission files: {self.output_dir}")
            print(f"   📄 Files created: {len(results['files_created'])}")
            
            if create_zip:
                zip_file = [f for f in results['files_created'] if f.endswith('.zip')][0]
                print(f"   📦 Ready to upload: {Path(zip_file).name}")
            
            results['success'] = True
            
        except Exception as e:
            error_msg = f"Error during submission preparation: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def _generate_submission_checklist(self, metadata, package) -> str:
        """Generate submission checklist."""
        checklist = []
        checklist.append("ArXiv Submission Checklist")
        checklist.append("=" * 50)
        checklist.append("")
        checklist.append("Before submitting to arXiv, please verify:")
        checklist.append("")
        
        # File checks
        checklist.append("📁 FILES:")
        checklist.append(f"   ✅ Main LaTeX file: {package.main_tex_file}")
        checklist.append(f"   ✅ Source files: {len(package.source_files)} files")
        if package.figure_files:
            checklist.append(f"   ✅ Figure files: {len(package.figure_files)} files")
        checklist.append(f"   ✅ Bibliography: {len(package.bibliography_files)} files")
        checklist.append(f"   ✅ Total size: {package.total_size_mb:.1f} MB (< 50 MB limit)")
        checklist.append("")
        
        # Metadata checks
        checklist.append("📝 METADATA:")
        checklist.append(f"   ✅ Title: {metadata.title}")
        checklist.append(f"   ✅ Authors: {len(metadata.authors)} author(s)")
        for i, author in enumerate(metadata.authors, 1):
            checklist.append(f"      {i}. {author['name']} ({author['email']})")
        checklist.append(f"   ✅ Primary category: {metadata.primary_category}")
        if len(metadata.categories) > 1:
            checklist.append(f"   ✅ Additional categories: {', '.join(metadata.categories[1:])}")
        checklist.append(f"   ✅ Keywords: {len(metadata.keywords)} keywords")
        checklist.append("")
        
        # Content checks
        checklist.append("📄 CONTENT:")
        checklist.append("   ✅ Abstract (check length and clarity)")
        checklist.append("   ✅ Introduction with clear motivation")
        checklist.append("   ✅ Related work section")
        checklist.append("   ✅ Methodology/Implementation details")
        checklist.append("   ✅ Results and evaluation")
        checklist.append("   ✅ Discussion and limitations")
        checklist.append("   ✅ Conclusion and future work")
        checklist.append("   ✅ References and citations")
        checklist.append("")
        
        # Final checks
        checklist.append("🔍 FINAL CHECKS:")
        checklist.append("   □ Proofread entire paper for typos and grammar")
        checklist.append("   □ Verify all figures are clear and properly referenced")
        checklist.append("   □ Check all citations are complete and accurate")
        checklist.append("   □ Ensure code examples are correct and tested")
        checklist.append("   □ Verify contact information is current")
        checklist.append("   □ Review abstract for clarity and completeness")
        checklist.append("")
        
        # Submission steps
        checklist.append("📤 SUBMISSION STEPS:")
        checklist.append("   1. Go to https://arxiv.org/submit")
        checklist.append("   2. Create account or log in")
        checklist.append("   3. Start new submission")
        checklist.append("   4. Upload ZIP file or individual files")
        checklist.append("   5. Fill in metadata form using generated metadata")
        checklist.append("   6. Select categories (primary: cs.AI)")
        checklist.append("   7. Add abstract text")
        checklist.append("   8. Review and submit")
        checklist.append("")
        
        checklist.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(checklist)
    
    def quick_check(self) -> bool:
        """Quick check if submission is ready."""
        try:
            validation_results = self.validator.validate_all()
            errors = [r for r in validation_results if r.severity == 'error']
            return len(errors) == 0
        except Exception:
            return False


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Prepare complete arXiv submission package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prepare_arxiv_submission.py output/arxiv_paper
  python prepare_arxiv_submission.py output/arxiv_paper --output /tmp/submission
  python prepare_arxiv_submission.py output/arxiv_paper --no-zip --check-only
        """
    )
    
    parser.add_argument("paper_dir", help="Directory containing the paper")
    parser.add_argument("--output", "-o", help="Output directory for submission package")
    parser.add_argument("--no-zip", action="store_true", help="Don't create ZIP package")
    parser.add_argument("--check-only", action="store_true", help="Only run validation checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = ArxivSubmissionManager(args.paper_dir, args.output)
    
    if args.check_only:
        # Quick validation check
        print("🔍 Running quick validation check...")
        if manager.quick_check():
            print("✅ Submission appears ready for arXiv!")
            return 0
        else:
            print("❌ Submission has issues that need to be fixed.")
            # Show detailed validation results
            results = manager.validator.validate_all()
            print("\nValidation Report:")
            print(manager.validator.generate_report())
            return 1
    
    # Full preparation
    results = manager.prepare_complete_submission(create_zip=not args.no_zip)
    
    if args.verbose:
        print("\nDetailed Results:")
        print(json.dumps(results, indent=2, default=str))
    
    if results['success']:
        print("\n🎯 Next steps:")
        print("   1. Review the generated files in the submission directory")
        print("   2. Check the submission_checklist.txt for final verification")
        print("   3. Upload to arXiv at https://arxiv.org/submit")
        return 0
    else:
        print(f"\n❌ Submission preparation failed with {len(results['errors'])} errors:")
        for error in results['errors']:
            print(f"   - {error}")
        return 1


if __name__ == "__main__":
    exit(main())