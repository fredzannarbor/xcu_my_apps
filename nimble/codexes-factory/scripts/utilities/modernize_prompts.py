#!/usr/bin/env python3
"""
Convenience script to modernize all prompt files in the project.

This script finds all prompt JSON files and converts them from the old
"prompt" format to the modern "messages" format.

Usage:
    python modernize_prompts.py [--dry-run] [--verbose]
"""

import argparse
import sys
from pathlib import Path
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_prompt_files() -> list[Path]:
    """Find all prompt JSON files in the project."""
    prompt_files = []
    
    # Main prompts directory
    prompts_dir = Path("prompts")
    if prompts_dir.exists():
        prompt_files.extend(prompts_dir.glob("*.json"))
    
    # Imprint-specific prompts
    imprints_dir = Path("imprints")
    if imprints_dir.exists():
        prompt_files.extend(imprints_dir.glob("*/prompts.json"))
        prompt_files.extend(imprints_dir.glob("*/prompts/*.json"))
    
    return sorted(prompt_files)


def modernize_all_prompts(dry_run: bool = False, verbose: bool = False) -> None:
    """Modernize all prompt files in the project."""
    prompt_files = find_prompt_files()
    
    if not prompt_files:
        logger.warning("No prompt files found")
        return
    
    logger.info(f"Found {len(prompt_files)} prompt files:")
    for file_path in prompt_files:
        logger.info(f"  {file_path}")
    
    if dry_run:
        logger.info("Dry run mode - no files will be modified")
        return
    
    # Run the modernizer on each file
    modernizer_script = "src/codexes/utilities/prompt_modernizer.py"
    
    for file_path in prompt_files:
        logger.info(f"Processing {file_path}")
        
        cmd = ["python", modernizer_script, str(file_path)]
        if verbose:
            cmd.append("--verbose")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if verbose:
                logger.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to process {file_path}: {e}")
            if verbose:
                logger.error(f"stdout: {e.stdout}")
                logger.error(f"stderr: {e.stderr}")
    
    logger.info("✅ All prompt files processed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Modernize all prompt files in the project",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    modernize_all_prompts(dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()