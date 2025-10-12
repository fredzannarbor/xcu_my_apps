#!/usr/bin/env python3
"""
ArXiv Submission Format Validation and Preparation Tools

This module provides comprehensive validation and preparation tools for arXiv submissions,
ensuring compliance with arXiv formatting requirements and submission standards.
"""

import os
import re
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import subprocess
import tempfile

@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: Optional[str] = None

@dataclass
class ArxivSubmissionPackage:
    """ArXiv submission package information."""
    main_tex_file: str
    source_files: List[str]
    figure_files: List[str]
    bibliography_files: List[str]
    metadata: Dict[str, Any]
    total_size_mb: float

class ArxivValidator:
    """Comprehensive arXiv submission validator."""
    
    # ArXiv requirements and limits
    MAX_FILE_SIZE_MB = 50
    MAX_TOTAL_SIZE_MB = 50
    ALLOWED_TEX_ENGINES = ['pdflatex', 'latex', 'xelatex', 'lualatex']
    REQUIRED_CATEGORIES = ['cs.AI', 'cs.HC', 'cs.CL', 'cs.LG']
    
    # ArXiv-specific document class requirements
    ARXIV_COMPATIBLE_CLASSES = [
        'article', 'revtex4-1', 'revtex4', 'amsart', 'elsarticle',
        'IEEEtran', 'sig-alternate', 'acm_proc_article-sp'
    ]
    
    def __init__(self, paper_dir: str):
        """Initialize validator with paper directory."""
        self.paper_dir = Path(paper_dir)
        self.latex_dir = self.paper_dir / "latex"
        self.results: List[ValidationResult] = []
        
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks."""
        self.results = []
        
        # Core validation checks
        self._validate_file_structure()
        self._validate_main_tex_file()
        self._validate_document_class()
        self._validate_packages()
        self._validate_bibliography()
        self._validate_figures()
        self._validate_file_sizes()
        self._validate_compilation()
        self._validate_metadata()
        self._validate_content_requirements()
        
        return self.results
    
    def _add_result(self, is_valid: bool, message: str, severity: str, suggestion: str = None):
        """Add a validation result."""
        self.results.append(ValidationResult(is_valid, message, severity, suggestion))
    
    def _validate_file_structure(self):
        """Validate required file structure."""
        required_files = ['main.tex', 'references.bib']
        
        for file in required_files:
            file_path = self.latex_dir / file
            if not file_path.exists():
                self._add_result(
                    False, 
                    f"Required file missing: {file}",
                    'error',
                    f"Create {file} in the latex directory"
                )
            else:
                self._add_result(
                    True,
                    f"Required file found: {file}",
                    'info'
                )
    
    def _validate_main_tex_file(self):
        """Validate main.tex file structure."""
        main_tex = self.latex_dir / "main.tex"
        if not main_tex.exists():
            return
            
        try:
            content = main_tex.read_text(encoding='utf-8')
            
            # Check for document structure
            if '\\begin{document}' not in content:
                self._add_result(
                    False,
                    "No \\begin{document} found in main.tex",
                    'error',
                    "Add \\begin{document} and \\end{document}"
                )
            else:
                self._add_result(
                    True,
                    "Document structure found in main.tex",
                    'info'
                )
            
            # Check for required elements across all tex files
            all_content = content
            
            # Include preamble content
            preamble_tex = self.latex_dir / "preamble.tex"
            if preamble_tex.exists():
                all_content += preamble_tex.read_text(encoding='utf-8')
            
            # Include title page content
            title_page_tex = self.latex_dir / "title_page.tex"
            if title_page_tex.exists():
                all_content += title_page_tex.read_text(encoding='utf-8')
            
            # Check for documentclass (in preamble or main)
            if '\\documentclass' not in all_content:
                self._add_result(
                    False,
                    "No \\documentclass found",
                    'error',
                    "Add \\documentclass declaration in preamble.tex or main.tex"
                )
            else:
                self._add_result(
                    True,
                    "Document class declaration found",
                    'info'
                )
            
            # Check for title (in any file)
            if '\\title{' not in all_content:
                self._add_result(
                    False,
                    "No \\title found",
                    'error',
                    "Add \\title{} declaration"
                )
            else:
                self._add_result(
                    True,
                    "Title declaration found",
                    'info'
                )
            
            # Check for author (in any file)
            if '\\author{' not in all_content:
                self._add_result(
                    False,
                    "No \\author found",
                    'error',
                    "Add \\author{} declaration"
                )
            else:
                self._add_result(
                    True,
                    "Author declaration found",
                    'info'
                )
            
            # Check for abstract
            abstract_tex = self.latex_dir / "abstract.tex"
            if '\\begin{abstract}' not in all_content and not abstract_tex.exists():
                self._add_result(
                    False,
                    "No abstract found",
                    'error',
                    "Add \\begin{abstract}...\\end{abstract} or create abstract.tex"
                )
            else:
                self._add_result(
                    True,
                    "Abstract found",
                    'info'
                )
            
        except Exception as e:
            self._add_result(
                False,
                f"Error reading main.tex: {str(e)}",
                'error'
            )
    
    def _validate_document_class(self):
        """Validate document class compatibility with arXiv."""
        # Check both main.tex and preamble.tex
        tex_files = [self.latex_dir / "main.tex", self.latex_dir / "preamble.tex"]
        
        for tex_file in tex_files:
            if not tex_file.exists():
                continue
                
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                # Extract document class
                class_match = re.search(r'\\documentclass(?:\[.*?\])?\{([^}]+)\}', content)
                if class_match:
                    doc_class = class_match.group(1)
                    if doc_class in self.ARXIV_COMPATIBLE_CLASSES:
                        self._add_result(
                            True,
                            f"Document class '{doc_class}' is arXiv compatible",
                            'info'
                        )
                    else:
                        self._add_result(
                            False,
                            f"Document class '{doc_class}' may not be arXiv compatible",
                            'warning',
                            f"Consider using one of: {', '.join(self.ARXIV_COMPATIBLE_CLASSES)}"
                        )
                    return  # Found document class, no need to check other files
                
            except Exception as e:
                self._add_result(
                    False,
                    f"Error validating document class in {tex_file.name}: {str(e)}",
                    'error'
                )
    
    def _validate_packages(self):
        """Validate LaTeX packages for arXiv compatibility."""
        # Packages that are problematic on arXiv
        problematic_packages = [
            'pstricks', 'pst-*', 'auto-pst-pdf', 'psfrag',
            'epsfig', 'subfigure', 'doublespace'
        ]
        
        # Recommended alternatives
        package_alternatives = {
            'subfigure': 'subcaption or subfig',
            'doublespace': 'setspace',
            'epsfig': 'graphicx'
        }
        
        tex_files = list(self.latex_dir.glob("*.tex"))
        
        for tex_file in tex_files:
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                for package in problematic_packages:
                    if f'\\usepackage{{{package}}}' in content or f'\\usepackage[' in content and package in content:
                        alternative = package_alternatives.get(package, "a compatible alternative")
                        self._add_result(
                            False,
                            f"Problematic package '{package}' found in {tex_file.name}",
                            'warning',
                            f"Consider using {alternative} instead"
                        )
                
            except Exception as e:
                self._add_result(
                    False,
                    f"Error checking packages in {tex_file.name}: {str(e)}",
                    'error'
                )
    
    def _validate_bibliography(self):
        """Validate bibliography files and citations."""
        bib_file = self.latex_dir / "references.bib"
        
        if not bib_file.exists():
            self._add_result(
                False,
                "Bibliography file references.bib not found",
                'error',
                "Create references.bib file with citations"
            )
            return
        
        try:
            bib_content = bib_file.read_text(encoding='utf-8')
            
            # Count entries
            entry_count = len(re.findall(r'@\w+\{', bib_content))
            
            if entry_count == 0:
                self._add_result(
                    False,
                    "No bibliography entries found",
                    'warning',
                    "Add bibliography entries to references.bib"
                )
            else:
                self._add_result(
                    True,
                    f"Found {entry_count} bibliography entries",
                    'info'
                )
            
            # Check for common BibTeX errors
            if bib_content.count('{') != bib_content.count('}'):
                self._add_result(
                    False,
                    "Unmatched braces in bibliography file",
                    'error',
                    "Check for missing opening or closing braces"
                )
            
        except Exception as e:
            self._add_result(
                False,
                f"Error validating bibliography: {str(e)}",
                'error'
            )
    
    def _validate_figures(self):
        """Validate figure files and references."""
        # Common figure extensions accepted by arXiv
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.eps', '.ps'}
        
        # Find figure files
        figure_files = []
        for ext in allowed_extensions:
            figure_files.extend(self.latex_dir.glob(f"*{ext}"))
        
        if figure_files:
            self._add_result(
                True,
                f"Found {len(figure_files)} figure files",
                'info'
            )
            
            # Check figure file sizes
            for fig_file in figure_files:
                size_mb = fig_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # Large figure warning
                    self._add_result(
                        False,
                        f"Large figure file: {fig_file.name} ({size_mb:.1f} MB)",
                        'warning',
                        "Consider compressing or optimizing the figure"
                    )
        else:
            self._add_result(
                True,
                "No figure files found (text-only paper)",
                'info'
            )
    
    def _validate_file_sizes(self):
        """Validate file sizes against arXiv limits."""
        total_size = 0
        large_files = []
        
        for file_path in self.latex_dir.rglob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                
                if size_mb > self.MAX_FILE_SIZE_MB:
                    large_files.append((file_path.name, size_mb))
        
        # Check individual file sizes
        for filename, size_mb in large_files:
            self._add_result(
                False,
                f"File too large: {filename} ({size_mb:.1f} MB > {self.MAX_FILE_SIZE_MB} MB)",
                'error',
                "Reduce file size or split into smaller files"
            )
        
        # Check total size
        if total_size > self.MAX_TOTAL_SIZE_MB:
            self._add_result(
                False,
                f"Total submission size too large: {total_size:.1f} MB > {self.MAX_TOTAL_SIZE_MB} MB",
                'error',
                "Reduce total file size by compressing figures or removing unnecessary files"
            )
        else:
            self._add_result(
                True,
                f"Total submission size: {total_size:.1f} MB (within limit)",
                'info'
            )
    
    def _validate_compilation(self):
        """Validate that the paper compiles successfully."""
        main_tex = self.latex_dir / "main.tex"
        if not main_tex.exists():
            return
        
        try:
            # Try to compile with lualatex (our preferred engine)
            result = subprocess.run(
                ['lualatex', '-interaction=nonstopmode', 'main.tex'],
                cwd=self.latex_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self._add_result(
                    True,
                    "Paper compiles successfully with lualatex",
                    'info'
                )
            else:
                self._add_result(
                    False,
                    "Paper compilation failed",
                    'error',
                    "Check LaTeX log file for compilation errors"
                )
                
        except subprocess.TimeoutExpired:
            self._add_result(
                False,
                "Paper compilation timed out",
                'error',
                "Check for infinite loops or excessive computation"
            )
        except FileNotFoundError:
            self._add_result(
                False,
                "LaTeX compiler not found",
                'warning',
                "Install LaTeX distribution (TeX Live, MiKTeX, etc.)"
            )
        except Exception as e:
            self._add_result(
                False,
                f"Compilation check failed: {str(e)}",
                'error'
            )
    
    def _validate_metadata(self):
        """Validate paper metadata for arXiv submission."""
        main_tex = self.latex_dir / "main.tex"
        if not main_tex.exists():
            return
            
        try:
            content = main_tex.read_text(encoding='utf-8')
            
            # Check for title
            title_match = re.search(r'\\title\{([^}]+)\}', content)
            if title_match:
                title = title_match.group(1)
                if len(title.strip()) < 10:
                    self._add_result(
                        False,
                        "Title appears too short",
                        'warning',
                        "Ensure title is descriptive and informative"
                    )
                else:
                    self._add_result(
                        True,
                        f"Title found: {title[:50]}...",
                        'info'
                    )
            
            # Check for author information
            author_match = re.search(r'\\author\{([^}]+)\}', content)
            if author_match:
                author = author_match.group(1)
                if '@' not in author:
                    self._add_result(
                        False,
                        "No email address found in author information",
                        'warning',
                        "Include email address for correspondence"
                    )
                else:
                    self._add_result(
                        True,
                        "Author information with email found",
                        'info'
                    )
            
        except Exception as e:
            self._add_result(
                False,
                f"Error validating metadata: {str(e)}",
                'error'
            )
    
    def _validate_content_requirements(self):
        """Validate content-specific requirements."""
        # Check for abstract
        abstract_file = self.latex_dir / "abstract.tex"
        if abstract_file.exists():
            try:
                abstract_content = abstract_file.read_text(encoding='utf-8')
                
                # Check abstract length
                word_count = len(abstract_content.split())
                if word_count < 50:
                    self._add_result(
                        False,
                        f"Abstract appears too short ({word_count} words)",
                        'warning',
                        "Expand abstract to better describe the work"
                    )
                elif word_count > 300:
                    self._add_result(
                        False,
                        f"Abstract appears too long ({word_count} words)",
                        'warning',
                        "Consider shortening abstract for better readability"
                    )
                else:
                    self._add_result(
                        True,
                        f"Abstract length appropriate ({word_count} words)",
                        'info'
                    )
                
                # Check for required opening text
                if "This paper presents" in abstract_content:
                    self._add_result(
                        True,
                        "Abstract contains required opening text",
                        'info'
                    )
                
            except Exception as e:
                self._add_result(
                    False,
                    f"Error validating abstract: {str(e)}",
                    'error'
                )
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        if not self.results:
            self.validate_all()
        
        report = []
        report.append("ArXiv Submission Validation Report")
        report.append("=" * 40)
        report.append("")
        
        # Summary
        errors = [r for r in self.results if r.severity == 'error']
        warnings = [r for r in self.results if r.severity == 'warning']
        info = [r for r in self.results if r.severity == 'info']
        
        report.append(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        report.append("")
        
        # Errors
        if errors:
            report.append("ERRORS (must fix before submission):")
            report.append("-" * 40)
            for result in errors:
                report.append(f"❌ {result.message}")
                if result.suggestion:
                    report.append(f"   💡 {result.suggestion}")
                report.append("")
        
        # Warnings
        if warnings:
            report.append("WARNINGS (recommended to fix):")
            report.append("-" * 40)
            for result in warnings:
                report.append(f"⚠️  {result.message}")
                if result.suggestion:
                    report.append(f"   💡 {result.suggestion}")
                report.append("")
        
        # Info
        if info:
            report.append("INFORMATION:")
            report.append("-" * 40)
            for result in info:
                report.append(f"ℹ️  {result.message}")
                report.append("")
        
        return "\n".join(report)
    
    def is_submission_ready(self) -> bool:
        """Check if submission is ready (no errors)."""
        if not self.results:
            self.validate_all()
        
        errors = [r for r in self.results if r.severity == 'error']
        return len(errors) == 0


class ArxivSubmissionPreparator:
    """Prepare arXiv submission package."""
    
    def __init__(self, paper_dir: str):
        """Initialize preparator with paper directory."""
        self.paper_dir = Path(paper_dir)
        self.latex_dir = self.paper_dir / "latex"
        
    def create_submission_package(self, output_dir: str) -> ArxivSubmissionPackage:
        """Create complete arXiv submission package."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all necessary files
        source_files = []
        figure_files = []
        bibliography_files = []
        
        # Copy LaTeX source files
        for tex_file in self.latex_dir.glob("*.tex"):
            dest_file = output_path / tex_file.name
            shutil.copy2(tex_file, dest_file)
            source_files.append(tex_file.name)
        
        # Copy bibliography files
        for bib_file in self.latex_dir.glob("*.bib"):
            dest_file = output_path / bib_file.name
            shutil.copy2(bib_file, dest_file)
            bibliography_files.append(bib_file.name)
        
        # Copy figure files
        figure_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.eps', '.ps']
        for ext in figure_extensions:
            for fig_file in self.latex_dir.glob(f"*{ext}"):
                dest_file = output_path / fig_file.name
                shutil.copy2(fig_file, dest_file)
                figure_files.append(fig_file.name)
        
        # Calculate total size
        total_size = sum(
            (output_path / f).stat().st_size 
            for f in source_files + figure_files + bibliography_files
        ) / (1024 * 1024)
        
        # Create metadata
        metadata = self._extract_metadata()
        
        # Create submission package info
        package = ArxivSubmissionPackage(
            main_tex_file="main.tex",
            source_files=source_files,
            figure_files=figure_files,
            bibliography_files=bibliography_files,
            metadata=metadata,
            total_size_mb=total_size
        )
        
        # Save package info
        package_info = {
            'main_tex_file': package.main_tex_file,
            'source_files': package.source_files,
            'figure_files': package.figure_files,
            'bibliography_files': package.bibliography_files,
            'metadata': package.metadata,
            'total_size_mb': package.total_size_mb,
            'created_at': str(Path().cwd()),
            'submission_ready': True
        }
        
        with open(output_path / "submission_info.json", 'w') as f:
            json.dump(package_info, f, indent=2)
        
        return package
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the paper."""
        metadata = {}
        
        main_tex = self.latex_dir / "main.tex"
        if main_tex.exists():
            try:
                content = main_tex.read_text(encoding='utf-8')
                
                # Extract title
                title_match = re.search(r'\\title\{([^}]+)\}', content)
                if title_match:
                    metadata['title'] = title_match.group(1)
                
                # Extract author
                author_match = re.search(r'\\author\{([^}]+)\}', content)
                if author_match:
                    metadata['author'] = author_match.group(1)
                
                # Extract categories from hyperref setup
                if 'cs.AI' in content:
                    metadata['primary_category'] = 'cs.AI'
                    metadata['categories'] = ['cs.AI', 'cs.HC']
                
            except Exception as e:
                metadata['extraction_error'] = str(e)
        
        return metadata
    
    def create_zip_package(self, output_dir: str, zip_filename: str = None) -> str:
        """Create a ZIP file for arXiv submission."""
        if zip_filename is None:
            zip_filename = "arxiv_submission.zip"
        
        output_path = Path(output_dir)
        zip_path = output_path / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the submission directory
            for file_path in output_path.iterdir():
                if file_path.is_file() and file_path.name != zip_filename:
                    zipf.write(file_path, file_path.name)
        
        return str(zip_path)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArXiv submission validator and preparator")
    parser.add_argument("paper_dir", help="Directory containing the paper")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument("--prepare", help="Prepare submission package in specified directory")
    parser.add_argument("--zip", action="store_true", help="Create ZIP package")
    
    args = parser.parse_args()
    
    if args.validate or not args.prepare:
        # Run validation
        validator = ArxivValidator(args.paper_dir)
        results = validator.validate_all()
        
        print(validator.generate_report())
        
        if validator.is_submission_ready():
            print("\n✅ Submission is ready for arXiv!")
        else:
            print("\n❌ Submission has errors that must be fixed.")
            return 1
    
    if args.prepare:
        # Prepare submission package
        preparator = ArxivSubmissionPreparator(args.paper_dir)
        package = preparator.create_submission_package(args.prepare)
        
        print(f"\n📦 Submission package created in: {args.prepare}")
        print(f"   Main file: {package.main_tex_file}")
        print(f"   Source files: {len(package.source_files)}")
        print(f"   Figure files: {len(package.figure_files)}")
        print(f"   Total size: {package.total_size_mb:.1f} MB")
        
        if args.zip:
            zip_path = preparator.create_zip_package(args.prepare)
            print(f"   ZIP package: {zip_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())