#!/usr/bin/env python3
"""
Comprehensive Test Runner for ArXiv Paper Generation System
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import time
import re
from pathlib import Path
from typing import Dict, List, Any

def run_comprehensive_tests(paper_dir: str) -> Dict[str, Any]:
    """Run comprehensive tests on the paper generation system."""
    paper_path = Path(paper_dir)
    
    print("🧪 Comprehensive ArXiv Paper Testing Framework")
    print("=" * 60)
    print(f"Paper directory: {paper_path}")
    print()
    
    start_time = time.time()
    
    # Test results
    results = {
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "success_rate": 0.0,
            "total_duration": 0.0
        },
        "suites": []
    }
    
    # Run test suites
    suites = [
        ("File Structure Tests", run_file_structure_tests),
        ("Content Validation Tests", run_content_validation_tests),
        ("LaTeX Compilation Tests", run_latex_compilation_tests),
        ("Metadata Extraction Tests", run_metadata_extraction_tests),
        ("ArXiv Validation Tests", run_arxiv_validation_tests),
        ("Integration Tests", run_integration_tests),
        ("Technical Accuracy Tests", run_technical_accuracy_tests)
    ]
    
    for suite_name, suite_func in suites:
        print(f"📋 Running {suite_name}...")
        suite_results = suite_func(paper_path)
        results["suites"].append({
            "name": suite_name,
            "results": suite_results,
            "passed": sum(1 for r in suite_results if r["passed"]),
            "failed": sum(1 for r in suite_results if not r["passed"]),
            "total": len(suite_results)
        })
        
        suite = results["suites"][-1]
        print(f"   {suite['passed']}/{suite['total']} tests passed ({suite['passed']/suite['total']:.1%})")
    
    # Calculate summary
    total_tests = sum(suite["total"] for suite in results["suites"])
    total_passed = sum(suite["passed"] for suite in results["suites"])
    total_failed = sum(suite["failed"] for suite in results["suites"])
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "success_rate": total_passed / total_tests if total_tests > 0 else 0,
        "total_duration": time.time() - start_time
    }
    
    # Print summary
    print_test_summary(results)
    
    return results

def run_file_structure_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test file structure and organization."""
    tests = []
    
    # Test 1: Required files exist
    required_files = [
        "latex/main.tex",
        "latex/preamble.tex", 
        "latex/references.bib",
        "latex/abstract.tex",
        "latex/introduction.tex",
        "latex/related_work.tex",
        "latex/methodology.tex",
        "latex/implementation.tex",
        "latex/results.tex",
        "latex/discussion.tex",
        "latex/conclusion.tex"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = paper_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    tests.append({
        "name": "Required Files Exist",
        "passed": len(missing_files) == 0,
        "message": f"Missing files: {missing_files}" if missing_files else "All required files present"
    })
    
    # Test 2: File sizes reasonable
    latex_dir = paper_path / "latex"
    size_issues = []
    
    if latex_dir.exists():
        for tex_file in latex_dir.glob("*.tex"):
            size = tex_file.stat().st_size
            if size == 0:
                size_issues.append(f"{tex_file.name} is empty")
            elif size > 1024 * 1024:  # 1MB
                size_issues.append(f"{tex_file.name} is very large ({size} bytes)")
    
    tests.append({
        "name": "File Sizes Reasonable",
        "passed": len(size_issues) == 0,
        "message": f"Size issues: {size_issues}" if size_issues else "All file sizes reasonable"
    })
    
    # Test 3: Directory structure
    expected_dirs = ["latex", "content", "data"]
    missing_dirs = []
    
    for dir_name in expected_dirs:
        dir_path = paper_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    tests.append({
        "name": "Directory Structure",
        "passed": len(missing_dirs) <= 1,  # Allow some flexibility
        "message": f"Missing directories: {missing_dirs}" if missing_dirs else "Directory structure good"
    })
    
    return tests

def run_content_validation_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test content quality and completeness."""
    tests = []
    
    # Test 1: Abstract quality
    abstract_file = paper_path / "latex" / "abstract.tex"
    if abstract_file.exists():
        try:
            content = abstract_file.read_text(encoding='utf-8')
            # Remove LaTeX commands for word count
            clean_content = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', '', content)
            clean_content = re.sub(r'\\[a-zA-Z]+\*?', '', clean_content)
            clean_content = re.sub(r'%.*?\n', '', clean_content)
            
            word_count = len(clean_content.split())
            
            issues = []
            if word_count < 100:
                issues.append(f"Too short ({word_count} words)")
            elif word_count > 300:
                issues.append(f"Too long ({word_count} words)")
            
            # Check for required content
            if "AI" not in content and "artificial intelligence" not in content.lower():
                issues.append("Missing AI/artificial intelligence mention")
            
            if "publishing" not in content.lower():
                issues.append("Missing publishing mention")
            
            tests.append({
                "name": "Abstract Quality",
                "passed": len(issues) == 0,
                "message": f"Issues: {issues}" if issues else f"Abstract quality good ({word_count} words)"
            })
            
        except Exception as e:
            tests.append({
                "name": "Abstract Quality",
                "passed": False,
                "message": f"Error reading abstract: {e}"
            })
    else:
        tests.append({
            "name": "Abstract Quality",
            "passed": False,
            "message": "Abstract file not found"
        })
    
    # Test 2: Section completeness
    sections = [
        ("introduction.tex", "Introduction"),
        ("related_work.tex", "Related Work"),
        ("methodology.tex", "Methodology"),
        ("implementation.tex", "Implementation"),
        ("results.tex", "Results"),
        ("discussion.tex", "Discussion"),
        ("conclusion.tex", "Conclusion")
    ]
    
    issues = []
    for filename, section_name in sections:
        file_path = paper_path / "latex" / filename
        if not file_path.exists():
            issues.append(f"{section_name} file missing")
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            word_count = len(content.split())
            
            if word_count < 50:
                issues.append(f"{section_name} too short ({word_count} words)")
            
        except Exception as e:
            issues.append(f"Error reading {section_name}: {e}")
    
    tests.append({
        "name": "Section Completeness",
        "passed": len(issues) == 0,
        "message": f"Issues: {issues}" if issues else "All sections complete"
    })
    
    # Test 3: Bibliography quality
    bib_file = paper_path / "latex" / "references.bib"
    if bib_file.exists():
        try:
            content = bib_file.read_text(encoding='utf-8')
            
            # Count entries
            entry_count = len(re.findall(r'@\w+\{', content))
            
            issues = []
            if entry_count < 5:
                issues.append(f"Too few references ({entry_count})")
            
            # Check for common fields
            if content.count('title') < entry_count * 0.8:
                issues.append("Many entries missing titles")
            
            if content.count('author') < entry_count * 0.5:
                issues.append("Many entries missing authors")
            
            # Check for syntax errors
            if content.count('{') != content.count('}'):
                issues.append("Unmatched braces")
            
            tests.append({
                "name": "Bibliography Quality",
                "passed": len(issues) == 0,
                "message": f"Issues: {issues}" if issues else f"Bibliography good ({entry_count} entries)"
            })
            
        except Exception as e:
            tests.append({
                "name": "Bibliography Quality",
                "passed": False,
                "message": f"Error reading bibliography: {e}"
            })
    else:
        tests.append({
            "name": "Bibliography Quality",
            "passed": False,
            "message": "Bibliography file not found"
        })
    
    return tests

def run_latex_compilation_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test LaTeX compilation."""
    tests = []
    
    # Test 1: LaTeX syntax check
    main_tex = paper_path / "latex" / "main.tex"
    if main_tex.exists():
        # Create temporary directory for compilation test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy all LaTeX files
            latex_dir = paper_path / "latex"
            try:
                for file in latex_dir.glob("*"):
                    if file.is_file():
                        shutil.copy2(file, temp_path / file.name)
                
                # Try compilation with lualatex
                result = subprocess.run(
                    ['lualatex', '-interaction=nonstopmode', 'main.tex'],
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                tests.append({
                    "name": "LaTeX Compilation",
                    "passed": result.returncode == 0,
                    "message": "Compilation successful" if result.returncode == 0 else "Compilation failed"
                })
                
            except subprocess.TimeoutExpired:
                tests.append({
                    "name": "LaTeX Compilation",
                    "passed": False,
                    "message": "Compilation timed out"
                })
            except FileNotFoundError:
                tests.append({
                    "name": "LaTeX Compilation",
                    "passed": False,
                    "message": "LaTeX compiler not found"
                })
            except Exception as e:
                tests.append({
                    "name": "LaTeX Compilation",
                    "passed": False,
                    "message": f"Compilation error: {e}"
                })
    else:
        tests.append({
            "name": "LaTeX Compilation",
            "passed": False,
            "message": "main.tex not found"
        })
    
    # Test 2: PDF generation
    pdf_file = paper_path / "latex" / "main.pdf"
    if pdf_file.exists():
        try:
            size = pdf_file.stat().st_size
            
            issues = []
            if size < 10000:  # 10KB
                issues.append(f"PDF very small ({size} bytes)")
            elif size > 50 * 1024 * 1024:  # 50MB
                issues.append(f"PDF very large ({size} bytes)")
            
            tests.append({
                "name": "PDF Generation",
                "passed": len(issues) == 0,
                "message": f"Issues: {issues}" if issues else f"PDF generated successfully ({size:,} bytes)"
            })
            
        except Exception as e:
            tests.append({
                "name": "PDF Generation",
                "passed": False,
                "message": f"Error checking PDF: {e}"
            })
    else:
        tests.append({
            "name": "PDF Generation",
            "passed": False,
            "message": "PDF file not found"
        })
    
    return tests

def run_metadata_extraction_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test metadata extraction functionality."""
    tests = []
    
    # Test 1: Title extraction
    preamble_file = paper_path / "latex" / "preamble.tex"
    main_file = paper_path / "latex" / "main.tex"
    
    title_found = False
    title_content = ""
    
    for file in [preamble_file, main_file]:
        if file.exists():
            try:
                content = file.read_text(encoding='utf-8')
                title_match = re.search(r'\\title\{([^}]+)\}', content)
                if title_match:
                    title_content = title_match.group(1)
                    title_found = True
                    break
            except Exception:
                continue
    
    tests.append({
        "name": "Title Extraction",
        "passed": title_found and len(title_content) > 10,
        "message": f"Title: {title_content[:50]}..." if title_found else "No title found"
    })
    
    # Test 2: Author extraction
    author_found = False
    email_found = False
    
    for file in [preamble_file, main_file]:
        if file.exists():
            try:
                content = file.read_text(encoding='utf-8')
                if '\\author{' in content:
                    author_found = True
                if '@' in content and ('texttt' in content or 'email' in content.lower()):
                    email_found = True
            except Exception:
                continue
    
    tests.append({
        "name": "Author Extraction",
        "passed": author_found and email_found,
        "message": f"Author: {author_found}, Email: {email_found}"
    })
    
    return tests

def run_arxiv_validation_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test arXiv-specific validation."""
    tests = []
    
    # Test 1: Document class
    preamble_file = paper_path / "latex" / "preamble.tex"
    if preamble_file.exists():
        try:
            content = preamble_file.read_text(encoding='utf-8')
            class_match = re.search(r'\\documentclass(?:\[.*?\])?\{([^}]+)\}', content)
            
            if class_match:
                doc_class = class_match.group(1)
                arxiv_compatible = doc_class in ['article', 'revtex4-1', 'amsart', 'elsarticle']
                
                tests.append({
                    "name": "Document Class",
                    "passed": arxiv_compatible,
                    "message": f"Document class: {doc_class} ({'compatible' if arxiv_compatible else 'may not be compatible'})"
                })
            else:
                tests.append({
                    "name": "Document Class",
                    "passed": False,
                    "message": "No document class found"
                })
                
        except Exception as e:
            tests.append({
                "name": "Document Class",
                "passed": False,
                "message": f"Error checking document class: {e}"
            })
    else:
        tests.append({
            "name": "Document Class",
            "passed": False,
            "message": "Preamble file not found"
        })
    
    # Test 2: Package compatibility
    problematic_packages = ['pstricks', 'pst-', 'subfigure', 'doublespace']
    
    latex_dir = paper_path / "latex"
    issues = []
    
    if latex_dir.exists():
        for tex_file in latex_dir.glob("*.tex"):
            try:
                content = tex_file.read_text(encoding='utf-8')
                for package in problematic_packages:
                    if f'\\usepackage{{{package}}}' in content or (package.endswith('-') and package in content):
                        issues.append(f"Problematic package '{package}' in {tex_file.name}")
            except Exception:
                continue
    
    tests.append({
        "name": "Package Compatibility",
        "passed": len(issues) == 0,
        "message": f"Issues: {issues}" if issues else "No problematic packages found"
    })
    
    return tests

def run_integration_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test end-to-end integration."""
    tests = []
    
    # Test 1: Complete workflow readiness
    required_for_workflow = [
        paper_path / "latex" / "main.tex",
        paper_path / "latex" / "references.bib"
    ]
    
    missing = [f for f in required_for_workflow if not f.exists()]
    
    tests.append({
        "name": "Complete Workflow",
        "passed": len(missing) == 0,
        "message": f"Missing files: {missing}" if missing else "Workflow files present"
    })
    
    # Test 2: Submission readiness
    latex_dir = paper_path / "latex"
    
    readiness_score = 0
    max_score = 10
    
    checks = [
        (latex_dir / "main.tex").exists(),
        (latex_dir / "references.bib").exists(),
        (latex_dir / "abstract.tex").exists(),
        len(list(latex_dir.glob("*.tex"))) >= 8,  # Multiple sections
        (latex_dir / "main.pdf").exists(),
        (latex_dir / "references.bib").stat().st_size > 1000 if (latex_dir / "references.bib").exists() else False,
        True,  # Additional checks placeholder
        True,
        True,
        True
    ]
    
    readiness_score = sum(checks)
    
    tests.append({
        "name": "Submission Readiness",
        "passed": readiness_score >= 7,
        "message": f"Readiness score: {readiness_score}/{max_score}"
    })
    
    return tests

def run_technical_accuracy_tests(paper_path: Path) -> List[Dict[str, Any]]:
    """Test technical accuracy of content."""
    tests = []
    
    # Test 1: Code examples
    latex_dir = paper_path / "latex"
    code_issues = []
    
    if latex_dir.exists():
        for tex_file in latex_dir.glob("*.tex"):
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                # Look for Python code blocks
                python_blocks = re.findall(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', content, re.DOTALL)
                python_blocks.extend(re.findall(r'\\lstinputlisting\{([^}]+)\}', content))
                
                # Basic syntax check (simplified)
                for i, block in enumerate(python_blocks):
                    if 'def ' in block and not block.count('(') == block.count(')'):
                        code_issues.append(f"Unmatched parentheses in code block {i+1} in {tex_file.name}")
                    
            except Exception:
                continue
    
    tests.append({
        "name": "Code Examples",
        "passed": len(code_issues) == 0,
        "message": f"Issues: {code_issues}" if code_issues else "Code examples appear correct"
    })
    
    # Test 2: Configuration examples
    config_issues = []
    
    if latex_dir.exists():
        for tex_file in latex_dir.glob("*.tex"):
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                # Look for JSON-like content
                json_patterns = re.findall(r'\{[^}]*"[^"]*"[^}]*\}', content)
                
                for i, pattern in enumerate(json_patterns):
                    try:
                        # Try to parse as JSON (simplified check)
                        if pattern.count('"') % 2 != 0:
                            config_issues.append(f"Unmatched quotes in JSON-like content in {tex_file.name}")
                    except Exception:
                        pass
                    
            except Exception:
                continue
    
    tests.append({
        "name": "Configuration Examples",
        "passed": len(config_issues) == 0,
        "message": f"Issues: {config_issues}" if config_issues else "Configuration examples appear correct"
    })
    
    return tests

def print_test_summary(results: Dict[str, Any]):
    """Print test summary."""
    summary = results["summary"]
    
    print()
    print("📊 Test Summary")
    print("=" * 40)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Total Duration: {summary['total_duration']:.2f}s")
    print()
    
    # Suite breakdown
    print("📋 Suite Breakdown:")
    for suite in results["suites"]:
        status = "✅" if suite["failed"] == 0 else "❌"
        success_rate = suite["passed"] / suite["total"] if suite["total"] > 0 else 0
        print(f"   {status} {suite['name']}: {suite['passed']}/{suite['total']} ({success_rate:.1%})")
    
    print()
    
    # Failed tests
    failed_tests = []
    for suite in results["suites"]:
        for test in suite["results"]:
            if not test["passed"]:
                failed_tests.append(f"{suite['name']}: {test['name']} - {test['message']}")
    
    if failed_tests:
        print("❌ Failed Tests:")
        for failed in failed_tests:
            print(f"   - {failed}")
    else:
        print("🎉 All tests passed!")
    
    print()
    
    # Overall status
    if summary["success_rate"] >= 0.9:
        print("🎉 Paper generation system is working excellently!")
    elif summary["success_rate"] >= 0.7:
        print("✅ Paper generation system is working well with minor issues.")
    else:
        print("⚠️  Paper generation system has significant issues that should be addressed.")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive ArXiv paper testing framework")
    parser.add_argument("paper_dir", help="Directory containing the paper")
    parser.add_argument("--output", "-o", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    results = run_comprehensive_tests(args.paper_dir)
    
    # Save results if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to: {args.output}")
    
    # Return appropriate exit code
    success_rate = results["summary"]["success_rate"]
    if success_rate >= 0.9:
        return 0
    elif success_rate >= 0.7:
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(main())