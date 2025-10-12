#!/usr/bin/env python3
"""
Release checklist script for arxiv-writer package.
This script validates that all requirements are met before releasing to PyPI.
"""

import subprocess
import sys
import os
import json
import toml
from pathlib import Path
from typing import Dict, List, Tuple


def run_command(cmd: List[str], cwd=None, check=True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        check=check
    )
    return result


def check_version_consistency() -> Tuple[bool, str]:
    """Check that version is consistent across all files."""
    print("\n--- Checking version consistency ---")
    
    # Read version from pyproject.toml
    try:
        with open("pyproject.toml", "r") as f:
            config = toml.load(f)
        pyproject_version = config["project"]["version"]
        print(f"pyproject.toml version: {pyproject_version}")
    except Exception as e:
        return False, f"Could not read version from pyproject.toml: {e}"
    
    # Read version from __init__.py
    try:
        init_file = Path("src/arxiv_writer/__init__.py")
        if init_file.exists():
            content = init_file.read_text()
            for line in content.split('\n'):
                if line.startswith('__version__'):
                    init_version = line.split('=')[1].strip().strip('"\'')
                    print(f"__init__.py version: {init_version}")
                    break
            else:
                return False, "__version__ not found in __init__.py"
        else:
            return False, "__init__.py not found"
    except Exception as e:
        return False, f"Could not read version from __init__.py: {e}"
    
    # Check CHANGELOG.md has entry for current version
    try:
        changelog = Path("CHANGELOG.md")
        if changelog.exists():
            content = changelog.read_text()
            if pyproject_version in content:
                print(f"✓ Version {pyproject_version} found in CHANGELOG.md")
            else:
                return False, f"Version {pyproject_version} not found in CHANGELOG.md"
        else:
            return False, "CHANGELOG.md not found"
    except Exception as e:
        return False, f"Could not check CHANGELOG.md: {e}"
    
    # Verify versions match
    if pyproject_version != init_version:
        return False, f"Version mismatch: pyproject.toml={pyproject_version}, __init__.py={init_version}"
    
    return True, f"Version {pyproject_version} is consistent across all files"


def check_git_status() -> Tuple[bool, str]:
    """Check git repository status."""
    print("\n--- Checking git status ---")
    
    try:
        # Check if we're in a git repository
        result = run_command(["git", "rev-parse", "--git-dir"])
        
        # Check for uncommitted changes
        result = run_command(["git", "status", "--porcelain"])
        if result.stdout.strip():
            return False, "There are uncommitted changes in the repository"
        
        # Check if we're on main branch
        result = run_command(["git", "branch", "--show-current"])
        current_branch = result.stdout.strip()
        if current_branch not in ["main", "master"]:
            return False, f"Not on main/master branch (current: {current_branch})"
        
        # Check if we're up to date with remote
        try:
            run_command(["git", "fetch"])
            result = run_command(["git", "status", "-uno"])
            if "behind" in result.stdout:
                return False, "Local branch is behind remote"
        except subprocess.CalledProcessError:
            print("Warning: Could not check remote status")
        
        return True, "Git repository is clean and up to date"
        
    except subprocess.CalledProcessError as e:
        return False, f"Git check failed: {e}"


def check_tests_pass() -> Tuple[bool, str]:
    """Check that all tests pass."""
    print("\n--- Running test suite ---")
    
    try:
        result = run_command([
            sys.executable, "-m", "pytest", 
            "-v", 
            "--cov=arxiv_writer", 
            "--cov-report=term-missing",
            "--tb=short"
        ])
        return True, "All tests passed"
    except subprocess.CalledProcessError:
        return False, "Test suite failed"


def check_security_scans() -> Tuple[bool, str]:
    """Run security scans."""
    print("\n--- Running security scans ---")
    
    try:
        # Install security tools
        run_command([sys.executable, "-m", "pip", "install", "safety", "bandit"])
        
        # Run safety check
        try:
            run_command([sys.executable, "-m", "safety", "check"])
            print("✓ Safety check passed")
        except subprocess.CalledProcessError:
            return False, "Safety check failed - security vulnerabilities found"
        
        # Run bandit check
        try:
            run_command(["bandit", "-r", "src", "-ll"])
            print("✓ Bandit security scan passed")
        except subprocess.CalledProcessError:
            return False, "Bandit security scan failed"
        
        return True, "All security scans passed"
        
    except subprocess.CalledProcessError as e:
        return False, f"Security scan setup failed: {e}"


def check_documentation() -> Tuple[bool, str]:
    """Check documentation completeness."""
    print("\n--- Checking documentation ---")
    
    required_files = [
        "README.md",
        "LICENSE", 
        "CHANGELOG.md",
        "docs/installation.rst",
        "docs/quickstart.rst",
        "docs/api/core.rst"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing documentation files: {', '.join(missing_files)}"
    
    # Check README has basic content
    readme = Path("README.md").read_text()
    required_sections = ["Installation", "Usage", "License"]
    missing_sections = [section for section in required_sections if section not in readme]
    
    if missing_sections:
        return False, f"README.md missing sections: {', '.join(missing_sections)}"
    
    return True, "Documentation is complete"


def check_package_metadata() -> Tuple[bool, str]:
    """Check package metadata in pyproject.toml."""
    print("\n--- Checking package metadata ---")
    
    try:
        with open("pyproject.toml", "r") as f:
            config = toml.load(f)
        
        project = config.get("project", {})
        required_fields = [
            "name", "version", "description", "readme", 
            "license", "authors", "classifiers", "dependencies"
        ]
        
        missing_fields = [field for field in required_fields if field not in project]
        if missing_fields:
            return False, f"Missing required fields in pyproject.toml: {', '.join(missing_fields)}"
        
        # Check that we have proper classifiers
        classifiers = project.get("classifiers", [])
        required_classifier_prefixes = [
            "Development Status ::",
            "Intended Audience ::",
            "License ::",
            "Programming Language :: Python :: 3"
        ]
        
        for prefix in required_classifier_prefixes:
            if not any(c.startswith(prefix) for c in classifiers):
                return False, f"Missing classifier starting with '{prefix}'"
        
        return True, "Package metadata is complete"
        
    except Exception as e:
        return False, f"Could not validate package metadata: {e}"


def check_build_artifacts() -> Tuple[bool, str]:
    """Check that build artifacts exist and are valid."""
    print("\n--- Checking build artifacts ---")
    
    dist_path = Path("dist")
    if not dist_path.exists():
        return False, "dist/ directory not found - run 'python -m build' first"
    
    # Check for wheel and source distribution
    wheel_files = list(dist_path.glob("*.whl"))
    sdist_files = list(dist_path.glob("*.tar.gz"))
    
    if not wheel_files:
        return False, "No wheel (.whl) file found in dist/"
    
    if not sdist_files:
        return False, "No source distribution (.tar.gz) file found in dist/"
    
    # Validate with twine
    try:
        run_command(["twine", "check", "dist/*"])
        return True, f"Build artifacts are valid: {len(wheel_files)} wheel(s), {len(sdist_files)} sdist(s)"
    except subprocess.CalledProcessError:
        return False, "twine check failed - build artifacts are invalid"


def check_cli_functionality() -> Tuple[bool, str]:
    """Check that CLI functionality works."""
    print("\n--- Checking CLI functionality ---")
    
    try:
        # Test CLI help
        result = run_command([sys.executable, "-m", "arxiv_writer.cli", "--help"])
        if "--help" not in result.stdout:
            return False, "CLI help output seems invalid"
        
        # Test CLI version
        try:
            result = run_command([sys.executable, "-m", "arxiv_writer.cli", "--version"])
            print(f"CLI version output: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print("Warning: CLI --version command failed (may not be implemented)")
        
        return True, "CLI functionality works"
        
    except subprocess.CalledProcessError:
        return False, "CLI functionality test failed"


def main():
    """Run all release checks."""
    print("Arxiv-Writer Release Checklist")
    print("=" * 60)
    
    checks = [
        ("Version Consistency", check_version_consistency),
        ("Git Status", check_git_status),
        ("Package Metadata", check_package_metadata),
        ("Documentation", check_documentation),
        ("Test Suite", check_tests_pass),
        ("Security Scans", check_security_scans),
        ("Build Artifacts", check_build_artifacts),
        ("CLI Functionality", check_cli_functionality),
    ]
    
    results = []
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            passed, message = check_func()
            results.append((check_name, passed, message))
            if passed:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                all_passed = False
        except Exception as e:
            results.append((check_name, False, f"Check failed with exception: {e}"))
            print(f"✗ Check failed with exception: {e}")
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("RELEASE CHECKLIST SUMMARY")
    print("=" * 60)
    
    for check_name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {check_name}: {message}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Package is ready for release.")
        print("\nNext steps:")
        print("1. Create a git tag: git tag v<version>")
        print("2. Push the tag: git push origin v<version>")
        print("3. The GitHub Actions workflow will handle the rest")
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues before releasing.")
        print("\nFailed checks need to be resolved before the package can be released.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())