#!/usr/bin/env python3
"""
Comprehensive build and test script for arxiv-writer package.
This script handles building, testing, and validating the package for distribution.
"""

import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path
import json


def run_command(cmd, cwd=None, check=True, capture_output=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=capture_output, 
        text=True, 
        check=check
    )
    if capture_output:
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    return result


def clean_build_artifacts():
    """Clean previous build artifacts."""
    print("\n" + "="*50)
    print("Cleaning build artifacts...")
    print("="*50)
    
    artifacts = ["build", "dist", "*.egg-info", "__pycache__", ".pytest_cache"]
    for pattern in artifacts:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            else:
                path.unlink()
                print(f"Removed file: {path}")


def run_security_checks():
    """Run security checks on the codebase."""
    print("\n" + "="*50)
    print("Running security checks...")
    print("="*50)
    
    # Install security tools if not present
    try:
        run_command([sys.executable, "-m", "pip", "install", "safety", "bandit", "semgrep"])
    except subprocess.CalledProcessError:
        print("Warning: Could not install security tools")
        return False
    
    # Run safety check
    try:
        print("\n--- Running safety check ---")
        run_command([sys.executable, "-m", "safety", "check"])
        print("✓ Safety check passed")
    except subprocess.CalledProcessError:
        print("✗ Safety check failed")
        return False
    
    # Run bandit check
    try:
        print("\n--- Running bandit security scan ---")
        run_command(["bandit", "-r", "src", "-f", "json", "-o", "bandit-report.json"])
        run_command(["bandit", "-r", "src"])
        print("✓ Bandit security scan passed")
    except subprocess.CalledProcessError:
        print("✗ Bandit security scan failed")
        return False
    
    # Run semgrep check
    try:
        print("\n--- Running semgrep security scan ---")
        run_command(["semgrep", "--config=auto", "src", "--json", "--output=semgrep-report.json"])
        print("✓ Semgrep security scan passed")
    except subprocess.CalledProcessError:
        print("Warning: Semgrep scan had issues (may be expected)")
    
    return True


def run_tests():
    """Run the test suite."""
    print("\n" + "="*50)
    print("Running test suite...")
    print("="*50)
    
    try:
        run_command([
            sys.executable, "-m", "pytest", 
            "-v", 
            "--cov=arxiv_writer", 
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml"
        ])
        print("✓ Test suite passed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Test suite failed")
        return False


def run_linting():
    """Run code linting and formatting checks."""
    print("\n" + "="*50)
    print("Running linting and formatting checks...")
    print("="*50)
    
    # Check formatting with black
    try:
        print("\n--- Checking code formatting ---")
        run_command(["black", "--check", "src", "tests"])
        print("✓ Code formatting check passed")
    except subprocess.CalledProcessError:
        print("✗ Code formatting check failed")
        return False
    
    # Run ruff linting
    try:
        print("\n--- Running ruff linting ---")
        run_command(["ruff", "check", "src", "tests"])
        print("✓ Ruff linting passed")
    except subprocess.CalledProcessError:
        print("✗ Ruff linting failed")
        return False
    
    # Run mypy type checking
    try:
        print("\n--- Running mypy type checking ---")
        run_command(["mypy", "src"])
        print("✓ Type checking passed")
    except subprocess.CalledProcessError:
        print("✗ Type checking failed")
        return False
    
    return True


def build_package():
    """Build the package."""
    print("\n" + "="*50)
    print("Building package...")
    print("="*50)
    
    try:
        # Install build dependencies
        run_command([sys.executable, "-m", "pip", "install", "build", "twine"])
        
        # Build package
        run_command([sys.executable, "-m", "build"])
        print("✓ Package built successfully")
        
        # Check package
        run_command(["twine", "check", "dist/*"])
        print("✓ Package check passed")
        
        return True
    except subprocess.CalledProcessError:
        print("✗ Package build failed")
        return False


def test_package_installation():
    """Test package installation in isolated environment."""
    print("\n" + "="*50)
    print("Testing package installation...")
    print("="*50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_env"
        
        # Create virtual environment
        run_command([sys.executable, "-m", "venv", str(venv_path)])
        
        # Determine python executable in venv
        if os.name == 'nt':  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:  # Unix-like
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        try:
            # Upgrade pip
            run_command([str(pip_exe), "install", "--upgrade", "pip"])
            
            # Install built package
            wheel_files = list(Path("dist").glob("*.whl"))
            if not wheel_files:
                print("✗ No wheel file found")
                return False
            
            wheel_file = wheel_files[0]
            run_command([str(pip_exe), "install", str(wheel_file)])
            
            # Test CLI entry point
            test_script = '''
import sys
try:
    # Test package import
    import arxiv_writer
    print(f"Package version: {getattr(arxiv_writer, '__version__', 'unknown')}")
    
    # Test core imports
    from arxiv_writer.core.generator import ArxivPaperGenerator
    from arxiv_writer.config.loader import PaperConfig
    from arxiv_writer.llm.caller import LLMCaller
    print("Core classes imported successfully")
    
    # Test CLI import
    from arxiv_writer.cli.main import main
    print("CLI main function imported successfully")
    
    print("✓ Package installation test passed")
    
except Exception as e:
    print(f"✗ Package installation test failed: {e}")
    sys.exit(1)
'''
            
            run_command([str(python_exe), "-c", test_script])
            
            # Test CLI command
            if os.name == 'nt':
                cli_exe = venv_path / "Scripts" / "arxiv-writer.exe"
            else:
                cli_exe = venv_path / "bin" / "arxiv-writer"
            
            if cli_exe.exists():
                run_command([str(cli_exe), "--help"])
                print("✓ CLI entry point test passed")
            else:
                print("✗ CLI entry point not found")
                return False
            
            print("✓ Package installation test passed")
            return True
            
        except subprocess.CalledProcessError:
            print("✗ Package installation test failed")
            return False


def generate_build_report():
    """Generate a build report with all artifacts and test results."""
    print("\n" + "="*50)
    print("Generating build report...")
    print("="*50)
    
    report = {
        "build_info": {
            "python_version": sys.version,
            "platform": sys.platform,
        },
        "artifacts": [],
        "test_results": {},
        "security_reports": []
    }
    
    # List build artifacts
    dist_path = Path("dist")
    if dist_path.exists():
        for artifact in dist_path.iterdir():
            report["artifacts"].append({
                "name": artifact.name,
                "size": artifact.stat().st_size,
                "path": str(artifact)
            })
    
    # Check for test reports
    if Path("coverage.xml").exists():
        report["test_results"]["coverage_report"] = "coverage.xml"
    if Path("htmlcov").exists():
        report["test_results"]["html_coverage"] = "htmlcov/"
    
    # Check for security reports
    for report_file in ["safety-report.json", "bandit-report.json", "semgrep-report.json"]:
        if Path(report_file).exists():
            report["security_reports"].append(report_file)
    
    # Write report
    with open("build-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("✓ Build report generated: build-report.json")


def main():
    """Main build and test function."""
    print("Arxiv-Writer Package Build and Test Script")
    print("=" * 60)
    
    success = True
    
    # Clean previous artifacts
    clean_build_artifacts()
    
    # Run linting and formatting checks
    if not run_linting():
        success = False
        print("Linting failed - continuing with build...")
    
    # Run tests
    if not run_tests():
        success = False
        print("Tests failed - continuing with build...")
    
    # Run security checks
    if not run_security_checks():
        success = False
        print("Security checks failed - continuing with build...")
    
    # Build package
    if not build_package():
        success = False
        print("Package build failed!")
        return 1
    
    # Test package installation
    if not test_package_installation():
        success = False
        print("Package installation test failed!")
    
    # Generate build report
    generate_build_report()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All build and test steps completed successfully!")
        print("Package is ready for distribution.")
    else:
        print("✗ Some build and test steps failed.")
        print("Please review the output and fix issues before distribution.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())