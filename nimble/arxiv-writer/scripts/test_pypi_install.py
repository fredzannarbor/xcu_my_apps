#!/usr/bin/env python3
"""
Script to test PyPI installation and functionality.
This script tests both Test PyPI and production PyPI installations.
"""

import subprocess
import sys
import tempfile
import os
import time
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        check=check
    )
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    return result


def test_installation(package_name, index_url=None, extra_index_url=None):
    """Test package installation from PyPI."""
    print(f"\n{'='*60}")
    print(f"Testing installation of {package_name}")
    if index_url:
        print(f"From index: {index_url}")
    print(f"{'='*60}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create virtual environment
        venv_path = Path(temp_dir) / "test_env"
        run_command([sys.executable, "-m", "venv", str(venv_path)])
        
        # Determine python executable in venv
        if os.name == 'nt':  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:  # Unix-like
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Upgrade pip
        run_command([str(pip_exe), "install", "--upgrade", "pip"])
        
        # Install package
        install_cmd = [str(pip_exe), "install"]
        if index_url:
            install_cmd.extend(["--index-url", index_url])
        if extra_index_url:
            install_cmd.extend(["--extra-index-url", extra_index_url])
        install_cmd.append(package_name)
        
        try:
            run_command(install_cmd)
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False
        
        # Test CLI entry point
        try:
            result = run_command([str(python_exe), "-m", "arxiv_writer.cli", "--help"])
            print("✓ CLI module import successful")
        except subprocess.CalledProcessError:
            print("✗ CLI module import failed")
            return False
        
        # Test direct CLI command
        try:
            if os.name == 'nt':
                cli_exe = venv_path / "Scripts" / "arxiv-writer.exe"
            else:
                cli_exe = venv_path / "bin" / "arxiv-writer"
            
            if cli_exe.exists():
                run_command([str(cli_exe), "--help"])
                print("✓ CLI entry point successful")
            else:
                print("✗ CLI entry point not found")
                return False
        except subprocess.CalledProcessError:
            print("✗ CLI entry point failed")
            return False
        
        # Test package import
        test_script = '''
import sys
try:
    import arxiv_writer
    print(f"✓ Package imported successfully: {arxiv_writer.__version__}")
    
    # Test core imports
    from arxiv_writer.core.generator import ArxivPaperGenerator
    from arxiv_writer.config.loader import PaperConfig
    from arxiv_writer.llm.caller import LLMCaller
    print("✓ Core classes imported successfully")
    
    # Test CLI import
    from arxiv_writer.cli.main import main
    print("✓ CLI main function imported successfully")
    
    print("✓ All imports successful")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
'''
        
        try:
            result = run_command([str(python_exe), "-c", test_script])
            print("✓ Package functionality test passed")
        except subprocess.CalledProcessError:
            print("✗ Package functionality test failed")
            return False
        
        print(f"✓ Installation test for {package_name} passed!")
        return True


def main():
    """Main test function."""
    print("PyPI Installation Test Script")
    print("=" * 60)
    
    # Test Test PyPI installation
    print("\n1. Testing Test PyPI installation...")
    test_pypi_success = test_installation(
        "arxiv-writer",
        index_url="https://test.pypi.org/simple/",
        extra_index_url="https://pypi.org/simple/"
    )
    
    if not test_pypi_success:
        print("Test PyPI installation failed!")
        return 1
    
    # Wait a bit before testing production PyPI
    print("\nWaiting 30 seconds before testing production PyPI...")
    time.sleep(30)
    
    # Test production PyPI installation
    print("\n2. Testing production PyPI installation...")
    prod_pypi_success = test_installation("arxiv-writer")
    
    if not prod_pypi_success:
        print("Production PyPI installation failed!")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All PyPI installation tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())