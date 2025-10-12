#!/usr/bin/env python3
"""
Validation script for resource organization.

This script validates that the resource organization was completed successfully
and provides a comprehensive report.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.core.resource_organizer import ResourceOrganizer


def main():
    """Main validation function."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Validating resource organization...")
    
    organizer = ResourceOrganizer(".")
    
    # Check 1: Verify exports directory exists and contains files
    exports_dir = Path("exports")
    if exports_dir.exists():
        export_files = list(exports_dir.glob("exported_config_*.json"))
        logger.info(f"✅ Exports directory exists with {len(export_files)} files")
        for file in export_files:
            logger.info(f"   - {file.name}")
    else:
        logger.error("❌ Exports directory does not exist")
        
    # Check 2: Verify no exported config files remain in root
    root_exports = list(Path(".").glob("exported_config_*.json"))
    if not root_exports:
        logger.info("✅ No exported config files remain in root directory")
    else:
        logger.error(f"❌ {len(root_exports)} exported config files still in root:")
        for file in root_exports:
            logger.error(f"   - {file.name}")
            
    # Check 3: Verify images directory was removed or is empty
    images_dir = Path("images")
    if not images_dir.exists():
        logger.info("✅ Images directory was successfully removed")
    elif images_dir.is_dir():
        image_files = list(images_dir.rglob("*"))
        image_files = [f for f in image_files if f.is_file()]
        if not image_files:
            logger.info("✅ Images directory exists but is empty")
        else:
            logger.error(f"❌ Images directory contains {len(image_files)} files:")
            for file in image_files:
                logger.error(f"   - {file}")
                
    # Check 4: Verify resources/images directory exists
    resources_images = Path("resources/images")
    if resources_images.exists():
        logger.info("✅ Resources/images directory exists")
    else:
        logger.error("❌ Resources/images directory does not exist")
        
    # Run full validation
    validation_results = organizer.validate_resource_organization()
    
    logger.info("\nFull validation results:")
    all_passed = True
    for check, result in validation_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {check}: {status}")
        if not result:
            all_passed = False
            
    if all_passed:
        logger.info("\n🎉 Resource organization validation PASSED!")
        return 0
    else:
        logger.error("\n❌ Resource organization validation FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())