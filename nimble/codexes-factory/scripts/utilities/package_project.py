#!/usr/bin/env python3
"""
Project Packaging Script for Codexes Factory

Creates a clean zip file of the project, excluding logs, temporary files,
outputs, and other generated content.
"""

import os
import zipfile
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Set, List


def setup_logging():
    """Configure logging for the packaging script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def get_excluded_patterns() -> Set[str]:
    """
    Returns a set of patterns/directories to exclude from the zip.
    """
    return {
        # Directories to exclude
        '__pycache__',
        '.git',
        '.pytest_cache',
        '.mypy_cache',
        '.venv',
        'venv',
        'ENV',
        'env',
        'node_modules',
        '.idea',
        '.vscode',

        # Temporary and output directories
        'temp_uploads',
        'output',
        'logs',
        'cache',
        'tmp',
        'temp',

        # File extensions to exclude
        '.log',
        '.pyc',
        '.pyo',
        '.pyd',
        '.so',
        '.egg-info',
        '.dist-info',
        '*.zip',

        # Specific files to exclude
        '.DS_Store',
        'Thumbs.db',
        '.env',
        '.env.local',
        '.env.production',
        '.env.development',
        'config.local.json',
        'secrets.json',

        # Common temporary file patterns
        '~',
        '.tmp',
        '.temp',
        '.bak',
        '.backup',
        '.swp',
        '.swo',
    }


def should_exclude_path(path: Path, excluded_patterns: Set[str]) -> bool:
    """
    Check if a path should be excluded based on patterns.
    """
    path_str = str(path)
    # Check if any part of the path matches excluded patterns
    for part in path.parts:
        if part in excluded_patterns:
            return True

    # Check file extensions and names
    if path.suffix in excluded_patterns or path.name in excluded_patterns:
        return True

    # Exclude hidden files/dirs (except .gitignore and .gitkeep)
    if path.name.startswith('.') and path.name not in {'.gitignore', '.gitkeep'}:
        return True

    return False


def should_include_python_only(path: Path) -> bool:
    """
    Check if a path should be included when using python-only mode.
    Only includes Python files and files in prompts/ and templates/ directories.
    Excludes virtual environment directories.
    """
    # Get all parts of the path for checking
    parts = path.parts

    # Exclude anything in virtual environment directories
    venv_dirs = {'.venv', 'venv', 'ENV', 'env', 'virtualenv'}
    if any(part in venv_dirs for part in parts):
        return False

    # Include Python files anywhere (but not in venv dirs, already checked above)
    if path.suffix == '.py':
        return True

    # Include anything in prompts/ or templates/ directories
    if 'prompts' in parts or 'templates' in parts:
        return True

    # Include common Python project files in root
    if len(parts) == 1 and path.name in {
        'requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg',
        'docs/readme/codexes_factory_ai_assisted_publishing_platform_v32.md', 'README.rst', 'LICENSE', 'MANIFEST.in'
    }:
        return True

    return False


def get_project_files(project_root: Path, excluded_patterns: Set[str], python_only: bool = False) -> List[Path]:
    """
    Get all files in the project that should be included in the zip.
    """
    included_files = []

    for item in project_root.rglob("*"):
        if item.is_file():
            # Get path relative to the project root for exclusion check
            relative_path = item.relative_to(project_root)

            if python_only:
                # Python-only mode: only include Python files and specific directories
                if should_include_python_only(relative_path):
                    included_files.append(item)
                    logging.debug(f"Including (Python-only): {relative_path}")
                else:
                    logging.debug(f"Excluding (Python-only): {relative_path}")
            else:
                # Normal mode: exclude based on patterns
                if not should_exclude_path(relative_path, excluded_patterns):
                    included_files.append(item)
                    logging.debug(f"Including: {relative_path}")
                else:
                    logging.debug(f"Excluding: {relative_path}")

    return included_files


def create_project_zip(project_root: str = ".", output_name: str = None, python_only: bool = False) -> str:
    """
    Create a zip file of the project.
    """
    project_path = Path(project_root).resolve()

    if output_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name_folder = project_path.name
        suffix = "_python_only" if python_only else "_package"
        output_name = f"{project_name_folder}{suffix}_{timestamp}.zip"

    # Save zip file one level up from the project directory
    output_path = project_path.parent / output_name

    excluded_patterns = get_excluded_patterns()
    files_to_include = get_project_files(project_path, excluded_patterns, python_only)

    mode_description = "Python files + prompts/ + templates/" if python_only else "full project"
    logging.info(f"Creating zip file: {output_path}")
    logging.info(f"Mode: {mode_description}")
    logging.info(f"Including {len(files_to_include)} files from {project_path}")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for file_path in files_to_include:
            archive_name = file_path.relative_to(project_path)
            zipf.write(file_path, archive_name)
            logging.debug(f"Added to zip: {archive_name}")

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logging.info(f"Zip file created successfully: {output_path} ({file_size_mb:.2f} MB)")
    return str(output_path)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Package Codexes Factory project into a zip file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python package_project.py                    # Package full project
  python package_project.py --python-only     # Package only Python files, prompts/, and templates/
  python package_project.py -o custom.zip     # Specify output filename
        """.strip()
    )

    parser.add_argument(
        '--python-only',
        action='store_true',
        help='Include only Python files and files in prompts/ and templates/ directories'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output zip filename (default: auto-generated with timestamp)'
    )

    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='Project directory to package (default: current directory)'
    )

    return parser.parse_args()


def main():
    """Main function to create the project package."""
    setup_logging()
    args = parse_arguments()

    logging.info("Starting Codexes project packaging...")

    try:
        zip_path = create_project_zip(
            project_root=args.project_dir,
            output_name=args.output,
            python_only=args.python_only
        )

        print(f"\n✅ Project packaged successfully!")
        print(f"📦 Zip file created at: {zip_path}")

        if args.python_only:
            print("🐍 Python-only mode: Included Python files + prompts/ + templates/ directories")

    except Exception as e:
        logging.error(f"Error creating project package: {e}", exc_info=True)


if __name__ == "__main__":
    main()