#!/usr/bin/env python3
"""
UV Project Template Setup Script

This script creates a UV project template with predefined directory structure
and configuration files.

Usage:
    python uv_project_setup.py <project_name>
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def setup_uv_project(project_name):
    """Set up a UV project with the specified name and directory structure."""
    # Create project directory
    project_dir = Path(project_name)

    if project_dir.exists():
        print(f"Error: Directory '{project_name}' already exists.")
        return False

    project_dir.mkdir()
    os.chdir(project_dir)

    # Initialize UV project
    print("Initializing UV project...")
    subprocess.run(["uv", "init"], check=True)

    # Create directory structure
    directories = [
        "data",
        "doc",
        "notes_and_reports",
        "resources",
        "resources/images",
        "resources/json",
        "resources/data_tables",
        "resources/sources_of_truth"
    ]

    print("Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Copy .gitignore and .env files
    source_dir = Path.home() / "nimble" / "repos" / "codex-libraries"

    if source_dir.exists():
        print("Copying configuration files...")
        try:
            # Copy .gitignore
            gitignore_src = source_dir / ".gitignore"
            if gitignore_src.exists():
                shutil.copy(gitignore_src, ".")
            else:
                print(f"Warning: {gitignore_src} not found. Creating a basic .gitignore...")
                with open(".gitignore", "w") as f:
                    f.write(".env\n.venv\n__pycache__/\n*.py[cod]\n*$py.class\n")

            # Copy .env file
            env_src = source_dir / ".env"
            if env_src.exists():
                shutil.copy(env_src, ".")
            else:
                print(f"Warning: {env_src} not found. Creating an empty .env file...")
                with open(".env", "w") as f:
                    f.write("# Environment variables\n")
        except Exception as e:
            print(f"Error copying files: {e}")
    else:
        print(f"Warning: Source directory {source_dir} not found. Creating basic files...")
        # Create basic .gitignore
        with open(".gitignore", "w") as f:
            f.write(".env\n.venv\n__pycache__/\n*.py[cod]\n*$py.class\n")

        # Create empty .env file
        with open(".env", "w") as f:
            f.write("# Environment variables\n")

    # Ensure .env is in .gitignore
    with open(".gitignore", "r") as f:
        content = f.read()

    if ".env" not in content:
        with open(".gitignore", "a") as f:
            f.write("\n# Environment variables\n.env\n")

    # Initialize git repository
    print(f"Initializing git repository named '{project_name}'...")
    subprocess.run(["git", "init"], check=True)

    # Initial commit
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with UV project template"], check=True)

    print(f"\nUV project '{project_name}' successfully created!")
    print(f"Project location: {os.path.abspath(project_name)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Set up a UV project template with predefined structure")
    parser.add_argument("project_name", help="Name of the project to create")

    args = parser.parse_args()

    if setup_uv_project(args.project_name):
        print("\nProject setup completed successfully.")
    else:
        print("\nProject setup failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()