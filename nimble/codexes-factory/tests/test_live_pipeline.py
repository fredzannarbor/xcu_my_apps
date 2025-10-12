#!/usr/bin/env python3

"""
Test Live Pipeline with Xynapse Traces Data

This script runs a real pipeline task with live data from xynapse_traces,
processing 1 book with LLM enhancement enabled to test all the bug fixes.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.enhanced_logging_simple import setup_logging

def setup_test_logging():
    """Set up enhanced logging for the test."""
    loggers = setup_logging(debug_mode=True, log_dir="logs/test_live_pipeline")
    return loggers["app"]

def create_test_metadata():
    """Create test metadata for xynapse_traces book."""
    metadata = CodexMetadata()
    
    # Basic book information
    metadata.title = "Martian Self-Reliance: Isolation versus Earth Support"
    metadata.author = "Dr. Elena Rodriguez"
    metadata.isbn13 = "9781234567890"
    metadata.publisher = "Xynapse Traces Publishing"
    metadata.imprint = "xynapse_traces"
    
    # Physical specifications
    metadata.page_count = 248
    metadata.binding_type = "paperback"
    metadata.paper_color = "cream"
    metadata.interior_color = "BW"
    metadata.trim_size = "6 x 9"
    
    # Pricing
    metadata.list_price_usd = 24.95
    
    # Content information
    metadata.short_description = "An exploration of human psychology and survival strategies in the context of Mars colonization, examining the balance between self-reliance and Earth-based support systems."
    metadata.long_description = "This comprehensive study examines the psychological and practical challenges facing future Mars colonists, with particular focus on the tension between developing self-reliant communities and maintaining connections with Earth. Drawing from historical examples of isolated communities and cutting-edge research in space psychology, Dr. Rodriguez presents a framework for understanding how humans might adapt to life on Mars while preserving their humanity and connection to their home planet."
    
    # Categories
    metadata.bisac_category = "SCI075000"  # Science / Space Science
    metadata.bisac_category_2 = "PSY031000"  # Psychology / Social Psychology
    
    # Additional metadata
    metadata.language = "en"
    metadata.country_of_publication = "US"
    metadata.copyright_year = 2024
    metadata.publication_date = "2024-03-15"
    
    return metadata

def test_spine_width_calculation(generator, metadata, logger):
    """Test the spine width calculation functionality."""
    logger.info("Testing spine width calculation...")
    
    # Test the spine width calculation
    original_spine_width = getattr(metadata, 'spine_width', None)
    logger.info(f"Original spine width: {original_spine_width}")
    
    # Apply spine width calculation
    updated_metadata = generator._calculate_and_override_spine_width(metadata)
    
    calculated_spine_width = getattr(updated_metadata, 'spine_width', None)
    logger.info(f"Calculated spine width: {calculated_spine_width}")
    
    return updated_metadata

def test_contributor_role_validation(metadata, logger):
    """Test contributor role validation."""
    logger.info("Testing contributor role validation...")
    
    from codexes.modules.distribution.contributor_role_fixer import fix_contributor_roles_in_metadata
    
    # Create metadata dict for testing
    metadata_dict = {
        'Author': metadata.author,
        'Author Role': '',  # Test blank role with non-blank name
        'Editor': '',
        'Editor Role': 'B01',  # Test non-blank role with blank name
    }
    
    logger.info(f"Before contributor role fix: {metadata_dict}")
    
    # Fix contributor roles
    fixed_metadata = fix_contributor_roles_in_metadata(metadata_dict)
    
    logger.info(f"After contributor role fix: {fixed_metadata}")
    
    return fixed_metadata

def test_file_path_generation(metadata, logger):
    """Test file path generation."""
    logger.info("Testing file path generation...")
    
    from codexes.modules.distribution.file_path_generator import generate_file_paths_for_metadata
    
    # Create metadata dict
    metadata_dict = {
        'title': metadata.title,
        'author': metadata.author,
        'isbn': metadata.isbn13
    }
    
    # Generate file paths
    result = generate_file_paths_for_metadata(metadata_dict, "output/xynapse_traces_build")
    
    logger.info(f"Generated file paths:")
    logger.info(f"  Interior: {result.interior_path}")
    logger.info(f"  Cover: {result.cover_path}")
    logger.info(f"  Base filename: {result.base_filename}")
    
    if result.validation_issues:
        logger.warning(f"Validation issues: {result.validation_issues}")
    
    return result

def test_reserved_fields_management(logger):
    """Test reserved fields management."""
    logger.info("Testing reserved fields management...")
    
    from codexes.modules.distribution.reserved_fields_manager import ensure_reserved_fields_blank
    
    # Create test metadata with some reserved fields populated
    test_metadata = {
        'Title': 'Test Book',
        'Author': 'Test Author',
        'Reserved 1': 'Should be blank',  # This should be cleared
        'Reserved 2': '',  # This is already blank
        'Future Use 1': 'Accidentally populated',  # This should be cleared
        'Normal Field': 'Should remain'  # This should remain
    }
    
    logger.info(f"Before reserved fields cleanup: {test_metadata}")
    
    # Clean reserved fields
    cleaned_metadata = ensure_reserved_fields_blank(test_metadata)
    
    logger.info(f"After reserved fields cleanup: {cleaned_metadata}")
    
    return cleaned_metadata

def test_field_validation(metadata, logger):
    """Test comprehensive field validation."""
    logger.info("Testing comprehensive field validation...")
    
    from codexes.modules.distribution.lsi_field_validator import LSIFieldValidator
    
    # Create metadata dict for validation
    metadata_dict = {
        'Title': metadata.title,
        'ISBN': metadata.isbn13,
        'List Price': str(metadata.list_price_usd),
        'Page Count': str(metadata.page_count),
        'Binding Type': metadata.binding_type,
        'Interior Color': metadata.interior_color,
        'Paper Color': metadata.paper_color,
        'BISAC Category': metadata.bisac_category,
        'Short Description': metadata.short_description,
        'Language': metadata.language,
        'Invalid Field': 'This should trigger a warning'
    }
    
    # Validate fields
    validator = LSIFieldValidator()
    validation_result = validator.validate_all_fields(metadata_dict)
    
    logger.info(f"Validation result: Valid = {validation_result.is_valid}")
    logger.info(f"Errors: {validation_result.error_count}")
    logger.info(f"Warnings: {validation_result.warning_count}")
    
    # Log specific issues
    for issue in validation_result.get_all_issues():
        logger.info(f"  {issue.severity.value.upper()}: {issue.field_name} - {issue.message}")
    
    return validation_result

def test_error_recovery(logger):
    """Test error recovery mechanisms."""
    logger.info("Testing error recovery mechanisms...")
    
    from codexes.modules.distribution.error_recovery import recover_json_parsing, recover_field_value
    
    # Test JSON parsing recovery
    invalid_json = '{"title": "Test Book", "author": "Test Author"'  # Missing closing brace
    recovered_data = recover_json_parsing(invalid_json, default_value={'title': 'Unknown'})
    logger.info(f"JSON recovery result: {recovered_data}")
    
    # Test field value recovery
    recovered_value = recover_field_value('BISAC Category', 'LLM generation failed', 'test_book_123')
    logger.info(f"Field recovery result: {recovered_value}")
    
    return recovered_data, recovered_value

def run_full_lsi_generation(logger):
    """Run the full LSI generation pipeline."""
    logger.info("Running full LSI generation pipeline...")
    
    try:
        # Initialize the LSI generator
        template_path = "templates/lsi_full_template.csv"
        config_path = "configs/imprints/xynapse_traces.json"
        tranche_name = "xynapse_tranche_1"
        
        # Check if template exists, if not create a minimal one
        if not os.path.exists(template_path):
            logger.info("Creating minimal LSI template for testing...")
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, 'w') as f:
                f.write("Title,Author,ISBN,List Price,Page Count,Binding Type,Interior Color,Paper Color,Spine Width\\n")
        
        generator = LsiAcsGenerator(
            template_path=template_path,
            config_path=config_path,
            tranche_name=tranche_name,
            log_directory="logs/test_live_pipeline"
        )
        
        # Create test metadata
        metadata = create_test_metadata()
        
        # Test individual components
        logger.info("\\n" + "="*60)
        logger.info("TESTING INDIVIDUAL COMPONENTS")
        logger.info("="*60)
        
        # Test spine width calculation
        metadata = test_spine_width_calculation(generator, metadata, logger)
        
        # Test contributor role validation
        test_contributor_role_validation(metadata, logger)
        
        # Test file path generation
        test_file_path_generation(metadata, logger)
        
        # Test reserved fields management
        test_reserved_fields_management(logger)
        
        # Test field validation
        test_field_validation(metadata, logger)
        
        # Test error recovery
        test_error_recovery(logger)
        
        # Test full generation
        logger.info("\\n" + "="*60)
        logger.info("TESTING FULL LSI GENERATION")
        logger.info("="*60)
        
        output_path = "output/test_live_pipeline_lsi.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate LSI CSV with validation
        result = generator.generate_with_validation(metadata, output_path)
        
        logger.info(f"Generation completed: {result}")
        
        # Check if file was created
        if os.path.exists(output_path):
            logger.info(f"✅ LSI CSV file created successfully: {output_path}")
            
            # Read and display first few lines
            with open(output_path, 'r') as f:
                lines = f.readlines()
                logger.info(f"File contains {len(lines)} lines")
                if lines:
                    logger.info(f"Header: {lines[0].strip()}")
                    if len(lines) > 1:
                        logger.info(f"Data row: {lines[1].strip()}")
        else:
            logger.error(f"❌ LSI CSV file was not created")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in full LSI generation: {e}")
        logger.error(f"Stack trace:", exc_info=True)
        return False

def main():
    """Main test function."""
    print("Starting Live Pipeline Test with Xynapse Traces Data")
    print("="*60)
    
    # Set up logging
    logger = setup_test_logging()
    logger.info("Starting live pipeline test")
    
    try:
        # Run the full test
        success = run_full_lsi_generation(logger)
        
        if success:
            print("\\n✅ Live pipeline test completed successfully!")
            logger.info("Live pipeline test completed successfully")
        else:
            print("\\n❌ Live pipeline test failed!")
            logger.error("Live pipeline test failed")
            
    except Exception as e:
        print(f"\\n💥 Test crashed: {e}")
        logger.error(f"Test crashed: {e}", exc_info=True)
    
    print("\\nCheck logs/test_live_pipeline/ for detailed logs")

if __name__ == "__main__":
    main()