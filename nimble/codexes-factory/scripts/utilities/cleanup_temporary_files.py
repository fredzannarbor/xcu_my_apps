#!/usr/bin/env python3
"""
Temporary File Cleanup Script

This script provides a command-line interface for safely cleaning up temporary
files in the repository using the TemporaryFileCleaner class.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.core.temporary_file_cleaner import TemporaryFileCleaner
from codexes.core.file_analysis_engine import FileAnalysisEngine


def main():
    """Main function for temporary file cleanup."""
    parser = argparse.ArgumentParser(description="Clean up temporary files in the repository")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Perform a dry run without actually removing files (default)")
    parser.add_argument("--execute", action="store_true",
                       help="Actually remove files (overrides --dry-run)")
    parser.add_argument("--category", type=str, choices=[
        "exported_configs", "python_cache", "system_files", 
        "latex_temp", "log_files", "build_artifacts", "all"
    ], default="all", help="Category of temporary files to clean")
    parser.add_argument("--update-gitignore", action="store_true",
                       help="Update .gitignore with patterns to prevent future accumulation")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set up logging level
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize cleaner
    print("Initializing temporary file cleaner...")
    cleaner = TemporaryFileCleaner()
    
    # Scan and categorize files
    print("Scanning repository for temporary files...")
    categorized_files = cleaner.categorize_temp_files()
    
    # Display findings
    total_files = sum(len(files) for files in categorized_files.values())
    print(f"\nFound {total_files} temporary files in {len(categorized_files)} categories:")
    
    for category, files in categorized_files.items():
        if files:
            category_info = cleaner.temp_categories.get(category)
            description = category_info.description if category_info else "Unknown category"
            print(f"  {category}: {len(files)} files - {description}")
            
            if args.verbose:
                for file_path in files[:5]:  # Show first 5 files
                    print(f"    - {file_path}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
    
    if total_files == 0:
        print("No temporary files found. Repository is clean!")
        return
    
    # Determine which files to process
    files_to_process = []
    if args.category == "all":
        for files in categorized_files.values():
            files_to_process.extend(files)
    else:
        files_to_process = categorized_files.get(args.category, [])
    
    if not files_to_process:
        print(f"No files found in category '{args.category}'")
        return
    
    print(f"\nProcessing {len(files_to_process)} files...")
    
    # Determine if this is a dry run
    dry_run = not args.execute
    if dry_run:
        print("DRY RUN MODE: No files will actually be removed")
    else:
        print("EXECUTION MODE: Files will be permanently removed")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != "yes":
            print("Operation cancelled")
            return
    
    # Clean files
    results = cleaner.clean_temporary_files(files_to_process, dry_run=dry_run)
    
    # Display results
    print(f"\nCleanup Results:")
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for file_path, result in results.items():
        if result.startswith("REMOVED"):
            success_count += 1
            if args.verbose:
                print(f"  ✓ {file_path}: {result}")
        elif result.startswith("ERROR"):
            error_count += 1
            print(f"  ✗ {file_path}: {result}")
        else:
            skip_count += 1
            if args.verbose:
                print(f"  - {file_path}: {result}")
    
    print(f"\nSummary:")
    print(f"  Successfully processed: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Skipped: {skip_count}")
    
    # Update gitignore if requested
    if args.update_gitignore:
        print("\nUpdating .gitignore...")
        patterns = cleaner.identify_temp_patterns()
        cleaner.update_gitignore(patterns)
        print("✓ .gitignore updated with temporary file patterns")


if __name__ == "__main__":
    main()