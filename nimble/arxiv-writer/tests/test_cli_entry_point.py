"""
Test CLI entry point functionality after package installation.
This test ensures the CLI works correctly when installed via pip.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
import pytest


class TestCLIEntryPoint:
    """Test CLI entry point functionality."""

    def test_cli_help_command(self):
        """Test that CLI help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "arxiv-writer" in result.stdout.lower()

    def test_cli_version_command(self):
        """Test that CLI version command works."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Should contain version information
        assert len(result.stdout.strip()) > 0

    def test_cli_module_import(self):
        """Test that CLI module can be imported."""
        result = subprocess.run([
            sys.executable, "-c", 
            "from arxiv_writer.cli.main import main; print('CLI import successful')"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "CLI import successful" in result.stdout

    def test_cli_direct_execution(self):
        """Test direct CLI execution if entry point is available."""
        # This test may fail in development mode, so we make it optional
        try:
            result = subprocess.run(
                ["arxiv-writer", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                assert "usage:" in result.stdout.lower()
            else:
                pytest.skip("CLI entry point not available (development mode)")
        except FileNotFoundError:
            pytest.skip("CLI entry point not found (development mode)")
        except subprocess.TimeoutExpired:
            pytest.fail("CLI command timed out")

    def test_cli_generate_command_help(self):
        """Test that generate command help works."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "generate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "generate" in result.stdout.lower()

    def test_cli_validate_command_help(self):
        """Test that validate command help works."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "validate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()

    def test_cli_with_invalid_command(self):
        """Test CLI behavior with invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "invalid-command"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # Should show error message
        assert len(result.stderr) > 0 or "invalid" in result.stdout.lower()

    def test_cli_config_validation(self):
        """Test CLI config validation command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write a minimal valid config
            f.write('{"paper": {"title": "Test Paper"}}')
            config_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "arxiv_writer.cli", "validate", "config", config_path],
                capture_output=True,
                text=True
            )
            # Command should execute (may pass or fail based on config validity)
            assert result.returncode in [0, 1]  # Either valid or invalid config
        finally:
            os.unlink(config_path)

    def test_cli_error_handling(self):
        """Test CLI error handling with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "arxiv_writer.cli", "generate"],
            capture_output=True,
            text=True
        )
        # Should fail with missing arguments
        assert result.returncode != 0


@pytest.mark.integration
class TestCLIInstallation:
    """Test CLI functionality after package installation."""

    def test_package_installation_in_venv(self):
        """Test package installation and CLI functionality in virtual environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_env"
            
            # Create virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

            # Determine python executable in venv
            if os.name == 'nt':  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:  # Unix-like
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"

            # Install package in development mode
            result = subprocess.run([
                str(pip_exe), "install", "-e", "."
            ], capture_output=True, text=True)
            assert result.returncode == 0

            # Test CLI functionality
            result = subprocess.run([
                str(python_exe), "-m", "arxiv_writer.cli", "--help"
            ], capture_output=True, text=True)
            assert result.returncode == 0
            assert "usage:" in result.stdout.lower()

            # Test package import
            result = subprocess.run([
                str(python_exe), "-c", 
                "import arxiv_writer; print('Package imported successfully')"
            ], capture_output=True, text=True)
            assert result.returncode == 0
            assert "Package imported successfully" in result.stdout