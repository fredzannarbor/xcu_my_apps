#!/usr/bin/env python3
"""
Comprehensive release validation script for arxiv-writer package.
This script performs all necessary checks before a PyPI release.
"""

import subprocess
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any
import time


def run_command(cmd: List[str], cwd=None, check=True, timeout=300) -> subprocess.CompletedProcess:
    """Run a command with timeout and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=check,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        raise


def validate_package_structure() -> Tuple[bool, str]:
    """Validate that the package has the correct structure."""
    print("\n--- Validating package structure ---")
    
    required_files = [
        "pyproject.toml",
        "README.md", 
        "LICENSE",
        "CHANGELOG.md",
        "src/arxiv_writer/__init__.py",
        "src/arxiv_writer/cli/__init__.py",
        "src/arxiv_writer/core/__init__.py",
        "src/arxiv_writer/llm/__init__.py",
        "src/arxiv_writer/config/__init__.py",
        "src/arxiv_writer/templates/__init__.py",
        "src/arxiv_writer/plugins/__init__.py",
        "src/arxiv_writer/utils/__init__.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing required files: {', '.join(missing_files)}"
    
    # Check that __init__.py files have proper imports
    init_file = Path("src/arxiv_writer/__init__.py")
    content = init_file.read_text()
    
    if "__version__" not in content:
        return False, "src/arxiv_writer/__init__.py missing __version__"
    
    return True, "Package structure is valid"


def validate_dependencies() -> Tuple[bool, str]:
    """Validate that all dependencies are properly specified and available."""
    print("\n--- Validating dependencies ---")
    
    try:
        # Install package in development mode
        run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev,latex]"])
        
        # Try importing all major components
        import_tests = [
            "import arxiv_writer",
            "from arxiv_writer.core.generator import ArxivPaperGenerator",
            "from arxiv_writer.config.loader import PaperConfig", 
            "from arxiv_writer.llm.caller import LLMCaller",
            "from arxiv_writer.templates.manager import TemplateManager",
            "from arxiv_writer.plugins.manager import PluginManager",
            "from arxiv_writer.cli.main import main",
        ]
        
        for import_test in import_tests:
            try:
                run_command([sys.executable, "-c", import_test])
            except subprocess.CalledProcessError:
                return False, f"Failed to import: {import_test}"
        
        return True, "All dependencies are valid and importable"
        
    except subprocess.CalledProcessError as e:
        return False, f"Dependency validation failed: {e}"


def validate_cli_functionality() -> Tuple[bool, str]:
    """Validate CLI functionality comprehensively."""
    print("\n--- Validating CLI functionality ---")
    
    cli_tests = [
        (["arxiv-writer", "--help"], "help command"),
        (["arxiv-writer", "--version"], "version command"),
        ([sys.executable, "-m", "arxiv_writer.cli", "--help"], "module invocation"),
    ]
    
    for cmd, description in cli_tests:
        try:
            result = run_command(cmd, timeout=30)
            if result.returncode != 0:
                return False, f"CLI {description} failed with exit code {result.returncode}"
        except subprocess.CalledProcessError:
            return False, f"CLI {description} failed"
        except subprocess.TimeoutExpired:
            return False, f"CLI {description} timed out"
    
    return True, "CLI functionality is working correctly"


def validate_test_coverage() -> Tuple[bool, str]:
    """Validate that test coverage meets requirements."""
    print("\n--- Validating test coverage ---")
    
    try:
        # Run tests with coverage
        result = run_command([
            sys.executable, "-m", "pytest", 
            "--cov=arxiv_writer", 
            "--cov-report=json",
            "--cov-report=term-missing",
            "-v"
        ], timeout=600)
        
        # Check coverage report
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data["totals"]["percent_covered"]
            if total_coverage < 90:
                return False, f"Test coverage too low: {total_coverage:.1f}% (minimum: 90%)"
            
            return True, f"Test coverage is adequate: {total_coverage:.1f}%"
        else:
            return False, "Coverage report not generated"
            
    except subprocess.CalledProcessError:
        return False, "Test suite failed"
    except subprocess.TimeoutExpired:
        return False, "Test suite timed out"


def validate_security() -> Tuple[bool, str]:
    """Run comprehensive security validation."""
    print("\n--- Running security validation ---")
    
    try:
        # Install security tools
        run_command([
            sys.executable, "-m", "pip", "install", 
            "safety", "bandit", "pip-audit"
        ])
        
        # Run safety check
        try:
            run_command([sys.executable, "-m", "safety", "check", "--json"])
            print("✓ Safety check passed")
        except subprocess.CalledProcessError:
            return False, "Safety check found security vulnerabilities"
        
        # Run bandit check
        try:
            run_command(["bandit", "-r", "src", "-f", "json", "-o", "bandit-report.json"])
            print("✓ Bandit security scan passed")
        except subprocess.CalledProcessError:
            # Check if it's just warnings
            if Path("bandit-report.json").exists():
                with open("bandit-report.json") as f:
                    bandit_data = json.load(f)
                
                high_severity = [r for r in bandit_data.get("results", []) 
                               if r.get("issue_severity") == "HIGH"]
                if high_severity:
                    return False, f"Bandit found {len(high_severity)} high-severity security issues"
                print("✓ Bandit found only low/medium severity issues (acceptable)")
            else:
                return False, "Bandit security scan failed"
        
        # Run pip-audit
        try:
            run_command([sys.executable, "-m", "pip_audit", "--format=json", "--output=audit-report.json"])
            print("✓ Pip audit passed")
        except subprocess.CalledProcessError:
            print("Warning: pip-audit found issues (review audit-report.json)")
        
        return True, "Security validation passed"
        
    except Exception as e:
        return False, f"Security validation failed: {e}"


def validate_build_and_install() -> Tuple[bool, str]:
    """Validate that the package builds and installs correctly."""
    print("\n--- Validating build and installation ---")
    
    try:
        # Clean previous builds
        for path in ["build", "dist"]:
            if Path(path).exists():
                shutil.rmtree(path)
        
        # Build package
        run_command([sys.executable, "-m", "build"], timeout=300)
        
        # Check build artifacts
        dist_path = Path("dist")
        wheel_files = list(dist_path.glob("*.whl"))
        sdist_files = list(dist_path.glob("*.tar.gz"))
        
        if not wheel_files:
            return False, "No wheel file generated"
        if not sdist_files:
            return False, "No source distribution generated"
        
        # Validate with twine
        run_command(["twine", "check", "dist/*"])
        
        # Test installation in clean environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_env"
            run_command([sys.executable, "-m", "venv", str(venv_path)])
            
            if os.name == 'nt':
                pip_exe = venv_path / "Scripts" / "pip.exe"
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                pip_exe = venv_path / "bin" / "pip"
                python_exe = venv_path / "bin" / "python"
            
            # Install from wheel
            wheel_file = wheel_files[0]
            run_command([str(pip_exe), "install", str(wheel_file)])
            
            # Test functionality
            test_script = '''
import sys
try:
    import arxiv_writer
    from arxiv_writer.core.generator import ArxivPaperGenerator
    from arxiv_writer.cli.main import main
    print("✓ Package installation test passed")
except Exception as e:
    print(f"✗ Package installation test failed: {e}")
    sys.exit(1)
'''
            run_command([str(python_exe), "-c", test_script])
        
        return True, "Build and installation validation passed"
        
    except subprocess.CalledProcessError as e:
        return False, f"Build/installation validation failed: {e}"
    except subprocess.TimeoutExpired:
        return False, "Build process timed out"


def validate_documentation() -> Tuple[bool, str]:
    """Validate documentation completeness and accuracy."""
    print("\n--- Validating documentation ---")
    
    try:
        # Check that Sphinx docs build without errors
        docs_path = Path("docs")
        if docs_path.exists():
            try:
                run_command(["make", "html"], cwd=docs_path, timeout=300)
                print("✓ Sphinx documentation builds successfully")
            except subprocess.CalledProcessError:
                return False, "Sphinx documentation build failed"
        
        # Validate README
        readme = Path("README.md")
        if readme.exists():
            content = readme.read_text()
            required_sections = ["Installation", "Usage", "License"]
            missing = [s for s in required_sections if s not in content]
            if missing:
                return False, f"README missing sections: {', '.join(missing)}"
        
        # Check CHANGELOG
        changelog = Path("CHANGELOG.md")
        if changelog.exists():
            content = changelog.read_text()
            # Should have recent version entries
            if "## [" not in content:
                return False, "CHANGELOG.md appears to be empty or malformed"
        
        return True, "Documentation validation passed"
        
    except Exception as e:
        return False, f"Documentation validation failed: {e}"


def generate_release_report(results: List[Tuple[str, bool, str]]) -> Dict[str, Any]:
    """Generate a comprehensive release report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "python_version": sys.version,
        "platform": sys.platform,
        "validation_results": [],
        "summary": {
            "total_checks": len(results),
            "passed": 0,
            "failed": 0,
            "overall_status": "UNKNOWN"
        },
        "artifacts": [],
        "recommendations": []
    }
    
    for check_name, passed, message in results:
        report["validation_results"].append({
            "check": check_name,
            "status": "PASS" if passed else "FAIL",
            "message": message
        })
        
        if passed:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["failed"] += 1
    
    # Overall status
    if report["summary"]["failed"] == 0:
        report["summary"]["overall_status"] = "READY_FOR_RELEASE"
    else:
        report["summary"]["overall_status"] = "NOT_READY"
    
    # List artifacts
    dist_path = Path("dist")
    if dist_path.exists():
        for artifact in dist_path.iterdir():
            if artifact.is_file():
                report["artifacts"].append({
                    "name": artifact.name,
                    "size": artifact.stat().st_size,
                    "path": str(artifact)
                })
    
    # Add recommendations
    if report["summary"]["failed"] > 0:
        report["recommendations"].append("Fix all failed validation checks before release")
    
    report["recommendations"].extend([
        "Review security scan reports for any issues",
        "Ensure all tests pass in CI/CD pipeline",
        "Create git tag for release version",
        "Test installation from Test PyPI before production release"
    ])
    
    return report


def main():
    """Run comprehensive release validation."""
    print("Arxiv-Writer Release Validation")
    print("=" * 60)
    
    validation_checks = [
        ("Package Structure", validate_package_structure),
        ("Dependencies", validate_dependencies),
        ("CLI Functionality", validate_cli_functionality),
        ("Test Coverage", validate_test_coverage),
        ("Security Scans", validate_security),
        ("Build & Install", validate_build_and_install),
        ("Documentation", validate_documentation),
    ]
    
    results = []
    
    for check_name, check_func in validation_checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            passed, message = check_func()
            results.append((check_name, passed, message))
            
            if passed:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                
        except Exception as e:
            results.append((check_name, False, f"Validation failed with exception: {e}"))
            print(f"✗ Validation failed with exception: {e}")
    
    # Generate and save report
    report = generate_release_report(results)
    
    with open("release-validation-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("RELEASE VALIDATION SUMMARY")
    print("=" * 60)
    
    for check_name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {check_name}: {message}")
    
    summary = report["summary"]
    print(f"\nResults: {summary['passed']} passed, {summary['failed']} failed")
    print(f"Overall Status: {summary['overall_status']}")
    
    print(f"\nDetailed report saved to: release-validation-report.json")
    
    print("\n" + "=" * 60)
    if summary["overall_status"] == "READY_FOR_RELEASE":
        print("🎉 PACKAGE IS READY FOR RELEASE!")
        print("\nNext steps:")
        print("1. git tag v<version>")
        print("2. git push origin v<version>")
        print("3. GitHub Actions will handle PyPI release")
    else:
        print("❌ PACKAGE IS NOT READY FOR RELEASE!")
        print("\nPlease fix the failed validation checks.")
    print("=" * 60)
    
    return 0 if summary["overall_status"] == "READY_FOR_RELEASE" else 1


if __name__ == "__main__":
    sys.exit(main())