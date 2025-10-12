#!/usr/bin/env python3
"""
Test script to verify the Codexes Factory configuration in all_applications_runner.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def test_config_loading():
    """Test that the configuration loads correctly."""
    print("🧪 Testing configuration loading...")

    try:
        with open('apps_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration file loaded successfully")

        # Check Codexes Factory specifically
        codexes_app = config['organizations']['nimble_books']['apps']['codexes_factory']
        print(f"✅ Codexes Factory config found: {codexes_app['name']}")

        return codexes_app
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return None

def test_file_existence(codexes_app):
    """Test that required files exist."""
    print("\n🧪 Testing file existence...")

    app_path = codexes_app['path']
    entry_file = codexes_app['entry']

    # Check application directory
    if os.path.exists(app_path):
        print(f"✅ Application directory exists: {app_path}")
    else:
        print(f"❌ Application directory missing: {app_path}")
        return False

    # Check entry file
    entry_path = os.path.join(app_path, entry_file)
    if os.path.exists(entry_path):
        print(f"✅ Entry file exists: {entry_file}")
        return True
    else:
        print(f"❌ Entry file missing: {entry_file}")
        return False

def test_startup_command_dry_run(codexes_app):
    """Test the startup command in dry-run mode."""
    print("\n🧪 Testing startup command (dry run)...")

    app_path = codexes_app['path']
    entry_file = codexes_app['entry']

    try:
        # Change to the application directory
        original_cwd = os.getcwd()
        os.chdir(app_path)

        # Test that uv is available
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ UV available: {result.stdout.strip()}")
        else:
            print("❌ UV not available")
            return False

        # Test that the Python path setup works
        test_cmd = [
            'uv', 'run', 'python', '-c',
            f"import sys, os; sys.path.insert(0, 'src'); print('Python path setup works'); print(f'Entry file exists: {{os.path.exists(\"{entry_file}\")}}')"
        ]

        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ Startup command environment test passed")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print("❌ Startup command environment test failed")
            print(f"   Error: {result.stderr}")
            return False

        return True

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Command test failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def main():
    """Run all tests."""
    print("🚀 Testing Codexes Factory Configuration for all_applications_runner\n")

    # Test 1: Configuration loading
    codexes_app = test_config_loading()
    if not codexes_app:
        print("\n❌ Configuration test failed. Exiting.")
        return False

    # Test 2: File existence
    if not test_file_existence(codexes_app):
        print("\n❌ File existence test failed. Exiting.")
        return False

    # Test 3: Startup command dry run
    if not test_startup_command_dry_run(codexes_app):
        print("\n❌ Startup command test failed. Exiting.")
        return False

    print("\n🎉 All tests passed! Codexes Factory should work with all_applications_runner.")
    print("\n📋 Configuration Summary:")
    print(f"   App: {codexes_app['name']}")
    print(f"   Port: {codexes_app['port']}")
    print(f"   Path: {codexes_app['path']}")
    print(f"   Entry: {codexes_app['entry']}")
    print(f"   Command: {codexes_app['startup_command']}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)