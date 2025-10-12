#!/usr/bin/env python3
"""
Resource organization script for Codexes Factory cleanup.

This script organizes images and exported files into proper resource directories
as part of the dot-release cleanup process.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.core.resource_organizer import ResourceOrganizer


def setup_logging():
    """Set up logging for the resource organization process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/resource_organization.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main function to organize resources."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting resource organization process...")
    
    try:
        # Initialize the resource organizer
        organizer = ResourceOrganizer(".")
        
        # Step 1: Process images directory
        logger.info("Step 1: Processing images directory...")
        image_moves = organizer.process_images_directory()
        if image_moves:
            logger.info(f"Moved {len(image_moves)} image files:")
            for old_path, new_path in image_moves.items():
                logger.info(f"  {old_path} -> {new_path}")
        else:
            logger.info("No image files to move (directory empty or doesn't exist)")
            
        # Step 2: Organize exported files
        logger.info("Step 2: Organizing exported config files...")
        export_moves = organizer.organize_exported_files()
        if export_moves:
            logger.info(f"Moved {len(export_moves)} exported config files:")
            for old_path, new_path in export_moves.items():
                logger.info(f"  {old_path} -> {new_path}")
        else:
            logger.info("No exported config files to move")
            
        # Step 3: Update resource references
        logger.info("Step 3: Updating resource references in code and documentation...")
        all_moves = {**image_moves, **export_moves}
        if all_moves:
            organizer.update_resource_references(all_moves)
            logger.info("Updated resource references in files")
        else:
            logger.info("No resource references to update")
            
        # Step 4: Clean up empty directories
        logger.info("Step 4: Cleaning up empty directories...")
        removed_dirs = organizer.cleanup_empty_directories()
        if removed_dirs:
            logger.info(f"Removed {len(removed_dirs)} empty directories:")
            for dir_path in removed_dirs:
                logger.info(f"  {dir_path}")
        else:
            logger.info("No empty directories to remove")
            
        # Step 5: Validate organization
        logger.info("Step 5: Validating resource organization...")
        validation_results = organizer.validate_resource_organization()
        
        all_valid = all(validation_results.values())
        if all_valid:
            logger.info("✅ Resource organization completed successfully!")
            logger.info("Validation results:")
            for check, result in validation_results.items():
                logger.info(f"  {check}: {'✅ PASS' if result else '❌ FAIL'}")
        else:
            logger.error("❌ Resource organization completed with issues!")
            logger.error("Validation results:")
            for check, result in validation_results.items():
                logger.error(f"  {check}: {'✅ PASS' if result else '❌ FAIL'}")
                
        # Summary
        logger.info("\n" + "="*50)
        logger.info("RESOURCE ORGANIZATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Images moved: {len(image_moves)}")
        logger.info(f"Exported files moved: {len(export_moves)}")
        logger.info(f"Empty directories removed: {len(removed_dirs)}")
        logger.info(f"Total operations: {len(organizer.operations)}")
        logger.info(f"Overall success: {'✅ YES' if all_valid else '❌ NO'}")
        
        return 0 if all_valid else 1
        
    except Exception as e:
        logger.error(f"Resource organization failed: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())