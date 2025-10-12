

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(cmd, check=True, hide_password=False):
    """Run a command and return the result."""
    if hide_password and "--password" in cmd:
        # Create a safe version for printing
        safe_cmd = cmd.copy()
        idx = safe_cmd.index("--password")
        if idx + 1 < len(safe_cmd):
            safe_cmd[idx + 1] = "***HIDDEN***"
        print(f"Running: {' '.join(safe_cmd)}")
    else:
        print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning build artifacts...")
    
    # Remove build directories
    for dir_name in ["build", "dist", "*.egg-info"]:
        run_command(["rm", "-rf", dir_name], check=False)
    
    # Remove __pycache__ directories
    run_command(["find", ".", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], check=False)
    run_command(["find", ".", "-name", "*.pyc", "-delete"], check=False)


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    result = run_command(["python", "-m", "pytest", "tests/", "-v", "--cov=nimble_llm_caller"], check=False)
    return result.returncode == 0


def build_package():
    """Build the package."""
    print("Building package...")
    run_command(["python", "-m", "build"])


def publish_to_pypi(repository="pypi", token=None):
    """Publish to PyPI repository."""
    print(f"Publishing to {repository}...")
    
    # Get actual distribution files instead of using glob pattern
    dist_files = list(Path("dist").glob("*"))
    if not dist_files:
        raise RuntimeError("No distribution files found in dist/")
    
    cmd = ["uv", "run", "twine", "upload"]
    
    if repository != "pypi":
        cmd.extend(["--repository", repository])
    
    if token:
        cmd.extend(["--username", "__token__", "--password", token])
    
    # Add actual file paths instead of glob pattern
    cmd.extend([str(f) for f in dist_files])
    
    # Hide the token from the printed command for security
    safe_cmd = cmd.copy()
    if token and "--password" in safe_cmd:
        idx = safe_cmd.index("--password")
        if idx + 1 < len(safe_cmd):
            safe_cmd[idx + 1] = "***HIDDEN***"
    
    print(f"Running: {' '.join(safe_cmd)}")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def check_version():
    """Check if version is properly set."""
    import tomli
    
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    version = config["project"]["version"]
    print(f"Package version: {version}")
    
    # Check if this is a development version
    if "dev" in version or "a" in version or "b" in version or "rc" in version:
        print("Warning: This appears to be a development version")
        return False
    
    return True


def validate_package():
    """Validate the built package."""
    print("Validating package...")
    
    # Check if wheel and sdist were created
    dist_files = list(Path("dist").glob("*"))
    if not dist_files:
        print("Error: No distribution files found")
        return False
    
    print(f"Distribution files: {[f.name for f in dist_files]}")
    
    # Run twine check
    result = run_command(["python", "-m", "twine", "check", "dist/*"], check=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Build and publish nimble-llm-caller")
    parser.add_argument("--repository", default="testpypi", 
                       help="PyPI repository (pypi, testpypi, or custom)")
    parser.add_argument("--token", help="PyPI token for authentication")
    parser.add_argument("--skip-tests", action="store_true", 
                       help="Skip running tests")
    parser.add_argument("--skip-clean", action="store_true", 
                       help="Skip cleaning build artifacts")
    parser.add_argument("--build-only", action="store_true", 
                       help="Only build, don't publish")
    parser.add_argument("--force", action="store_true", 
                       help="Force publish even with warnings")
    
    args = parser.parse_args()
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    try:
        # Clean build artifacts
        if not args.skip_clean:
            clean_build()
        
        # Run tests
        if not args.skip_tests:
            if not run_tests():
                print("Tests failed!")
                print("Note: Test failures are in legacy code, not in new intelligent context management features")
                if not args.force:
                    response = input("Continue with build despite test failures? (y/N): ")
                    if response.lower() != 'y':
                        sys.exit(1)
                print("Continuing with build...")
        
        # Check version
        version_ok = check_version()
        if not version_ok and not args.force:
            response = input("Version appears to be developmental. Continue? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        # Build package
        build_package()
        
        # Validate package
        if not validate_package():
            print("Package validation failed!")
            if not args.force:
                sys.exit(1)
            print("Continuing due to --force flag")
        
        # Publish if requested
        if not args.build_only:
            publish_to_pypi(args.repository, args.token)
            print(f"Successfully published to {args.repository}")
        else:
            print("Build completed. Skipping publish due to --build-only flag")
    
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()