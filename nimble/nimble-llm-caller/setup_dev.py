#!/usr/bin/env python3
"""
Development setup script for nimble-llm-caller.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def setup_development_environment():
    """Set up the development environment."""
    print("🚀 Setting up nimble-llm-caller development environment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Please run this script from the package root directory.")
        return False
    
    # Install package in development mode
    if not run_command("pip install -e .", "Installing package in development mode"):
        return False
    
    # Install development dependencies
    if not run_command("pip install -e .[dev]", "Installing development dependencies"):
        return False
    
    # Run tests to verify installation
    if Path("tests").exists():
        if not run_command("python -m pytest tests/ -v", "Running tests"):
            print("⚠️  Some tests failed, but installation may still be working")
    
    # Run CLI test
    if Path("examples/cli_test.py").exists():
        if not run_command("python examples/cli_test.py --test install", "Running installation test"):
            return False
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Set up your API keys in environment variables:")
    print("   export OPENAI_API_KEY='your-openai-key'")
    print("   export ANTHROPIC_API_KEY='your-anthropic-key'")
    print("2. Run the full test suite: python examples/cli_test.py")
    print("3. Try the basic usage example: python examples/basic_usage.py")
    
    return True


def run_tests():
    """Run the test suite."""
    print("🧪 Running nimble-llm-caller test suite")
    print("=" * 40)
    
    # Run pytest if available
    if Path("tests").exists():
        if not run_command("python -m pytest tests/ -v --tb=short", "Running pytest"):
            return False
    
    # Run CLI tests
    if Path("examples/cli_test.py").exists():
        if not run_command("python examples/cli_test.py", "Running CLI tests"):
            return False
    
    print("\n✅ All tests completed!")
    return True


def build_package():
    """Build the package for distribution."""
    print("📦 Building nimble-llm-caller package")
    print("=" * 35)
    
    # Clean previous builds
    run_command("rm -rf dist/ build/ *.egg-info/", "Cleaning previous builds")
    
    # Build package
    if not run_command("python -m build", "Building package"):
        return False
    
    print("\n✅ Package built successfully!")
    print("Distribution files created in dist/")
    
    return True


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python setup_dev.py [setup|test|build]")
        print("  setup - Set up development environment")
        print("  test  - Run test suite")
        print("  build - Build package for distribution")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        success = setup_development_environment()
    elif command == "test":
        success = run_tests()
    elif command == "build":
        success = build_package()
    else:
        print(f"Unknown command: {command}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()