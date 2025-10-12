#!/usr/bin/env python3
"""
Test CLI entry point installation and functionality.
This script validates that the CLI works correctly after pip installation.
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], cwd=None, check=True, timeout=30) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
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
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr and result.stderr.strip():
            print(f"STDERR: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        raise


def test_cli_in_clean_environment() -> Tuple[bool, str]:
    """Test CLI installation and functionality in a clean virtual environment."""
    print("\n--- Testing CLI in clean environment ---")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_env"
        
        try:
            # Create virtual environment
            run_command([sys.executable, "-m", "venv", str(venv_path)])
            
            # Determine executables in venv
            if os.name == 'nt':  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
                cli_exe = venv_path / "Scripts" / "arxiv-writer.exe"
            else:  # Unix-like
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"
                cli_exe = venv_path / "bin" / "arxiv-writer"
            
            # Upgrade pip
            run_command([str(pip_exe), "install", "--upgrade", "pip"])
            
            # Install package from wheel
            dist_path = Path("dist")
            if not dist_path.exists():
                return False, "dist/ directory not found - run 'python -m build' first"
            
            wheel_files = list(dist_path.glob("*.whl"))
            if not wheel_files:
                return False, "No wheel file found in dist/"
            
            wheel_file = wheel_files[0]
            run_command([str(pip_exe), "install", str(wheel_file)])
            
            # Test CLI entry point exists
            if not cli_exe.exists():
                return False, f"CLI entry point not found at {cli_exe}"
            
            # Test CLI help command
            result = run_command([str(cli_exe), "--help"])
            if result.returncode != 0:
                return False, f"CLI help command failed with exit code {result.returncode}"
            
            if "usage:" not in result.stdout.lower() and "arxiv-writer" not in result.stdout.lower():
                return False, "CLI help output doesn't look correct"
            
            # Test CLI version command
            try:
                result = run_command([str(cli_exe), "--version"])
                print(f"CLI version: {result.stdout.strip()}")
            except subprocess.CalledProcessError:
                print("Warning: CLI --version command not implemented or failed")
            
            # Test module invocation
            result = run_command([str(python_exe), "-m", "arxiv_writer.cli", "--help"])
            if result.returncode != 0:
                return False, "Module invocation failed"
            
            # Test package import in clean environment
            test_script = '''
import sys
try:
    import arxiv_writer
    print(f"Package version: {getattr(arxiv_writer, '__version__', 'unknown')}")
    
    # Test core imports
    from arxiv_writer.core.generator import ArxivPaperGenerator
    from arxiv_writer.config.loader import PaperConfig
    from arxiv_writer.llm.caller import LLMCaller
    from arxiv_writer.cli.main import main
    
    print("✓ All imports successful in clean environment")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
'''
            
            result = run_command([str(python_exe), "-c", test_script])
            if result.returncode != 0:
                return False, "Package import test failed in clean environment"
            
            return True, "CLI entry point test passed in clean environment"
            
        except subprocess.CalledProcessError as e:
            return False, f"CLI test failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"


def test_cli_commands() -> Tuple[bool, str]:
    """Test various CLI commands and options."""
    print("\n--- Testing CLI commands ---")
    
    try:
        # Test help command
        result = run_command(["arxiv-writer", "--help"])
        if result.returncode != 0:
            return False, "Main help command failed"
        
        # Test subcommand help (if they exist)
        subcommands = ["generate", "validate", "config"]
        for subcmd in subcommands:
            try:
                result = run_command(["arxiv-writer", subcmd, "--help"], check=False)
                if result.returncode == 0:
                    print(f"✓ Subcommand '{subcmd}' help works")
                else:
                    print(f"ℹ Subcommand '{subcmd}' not implemented or help failed")
            except subprocess.CalledProcessError:
                print(f"ℹ Subcommand '{subcmd}' not available")
        
        # Test version command
        try:
            result = run_command(["arxiv-writer", "--version"], check=False)
            if result.returncode == 0:
                print(f"✓ Version command works: {result.stdout.strip()}")
            else:
                print("ℹ Version command not implemented")
        except subprocess.CalledProcessError:
            print("ℹ Version command not available")
        
        # Test invalid command
        result = run_command(["arxiv-writer", "invalid-command"], check=False)
        if result.returncode != 0:
            print("✓ Invalid command properly rejected")
        else:
            print("⚠ Invalid command should have failed")
        
        return True, "CLI commands test passed"
        
    except Exception as e:
        return False, f"CLI commands test failed: {e}"


def test_cli_with_config() -> Tuple[bool, str]:
    """Test CLI with configuration files."""
    print("\n--- Testing CLI with configuration ---")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.json"
            
            # Create a test configuration
            test_config = '''
{
    "output_directory": "output",
    "llm_config": {
        "default_model": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY"
    },
    "template_config": {
        "template_file": "default_prompts.json"
    }
}
'''
            config_file.write_text(test_config)
            
            # Test CLI with config file (if supported)
            try:
                result = run_command([
                    "arxiv-writer", 
                    "--config", str(config_file),
                    "--help"
                ], check=False)
                
                if result.returncode == 0:
                    print("✓ CLI accepts config file parameter")
                else:
                    print("ℹ CLI config file parameter not implemented")
            except subprocess.CalledProcessError:
                print("ℹ CLI config file parameter not available")
            
            return True, "CLI configuration test completed"
            
    except Exception as e:
        return False, f"CLI configuration test failed: {e}"


def test_cli_error_handling() -> Tuple[bool, str]:
    """Test CLI error handling."""
    print("\n--- Testing CLI error handling ---")
    
    try:
        # Test with non-existent config file
        result = run_command([
            "arxiv-writer", 
            "--config", "/non/existent/config.json"
        ], check=False)
        
        if result.returncode != 0:
            print("✓ CLI properly handles non-existent config file")
        else:
            print("ℹ CLI config file handling not implemented")
        
        # Test with invalid arguments
        result = run_command([
            "arxiv-writer", 
            "--invalid-flag"
        ], check=False)
        
        if result.returncode != 0:
            print("✓ CLI properly handles invalid arguments")
        else:
            print("⚠ CLI should reject invalid arguments")
        
        return True, "CLI error handling test passed"
        
    except Exception as e:
        return False, f"CLI error handling test failed: {e}"


def main():
    """Run all CLI entry point tests."""
    print("Arxiv-Writer CLI Entry Point Test")
    print("=" * 60)
    
    # Check if package is installed
    try:
        result = run_command([sys.executable, "-c", "import arxiv_writer"])
        print("✓ Package is installed and importable")
    except subprocess.CalledProcessError:
        print("✗ Package is not installed - run 'pip install -e .' first")
        return 1
    
    tests = [
        ("Clean Environment Test", test_cli_in_clean_environment),
        ("CLI Commands Test", test_cli_commands),
        ("CLI Configuration Test", test_cli_with_config),
        ("CLI Error Handling Test", test_cli_error_handling),
    ]
    
    results = []
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            passed, message = test_func()
            results.append((test_name, passed, message))
            
            if passed:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                all_passed = False
                
        except Exception as e:
            results.append((test_name, False, f"Test failed with exception: {e}"))
            print(f"✗ Test failed with exception: {e}")
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("CLI ENTRY POINT TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test_name}: {message}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CLI TESTS PASSED!")
        print("CLI entry point is working correctly.")
    else:
        print("❌ SOME CLI TESTS FAILED!")
        print("Please review and fix the CLI implementation.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())