# Implementation Plan

- [x] 1. Extend CodexMetadata model with missing LSI-specific fields
  - Add Lightning Source account information fields (lightning_source_account, metadata_contact_dictionary)
  - Add submission method fields (cover_submission_method, text_block_submission_method)
  - Add enhanced contributor fields (contributor_one_bio, affiliations, professional_position, location, etc.)
  - Add physical specification fields (weight_lbs, carton_pack_quantity)
  - Add publication timing fields (street_date separate from pub_date)
  - Add territorial rights and edition fields
  - Add file path fields for submission (jacket_path_filename, interior_path_filename, cover_path_filename)
  - Add LSI special fields (lsi_special_category, stamped_text fields, order_type_eligibility)
  - Add LSI flex fields (lsi_flexfield1-5) and publisher_reference_id
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 2. Create field mapping strategy system
- [x] 2.1 Implement base mapping strategy interface
  - Create abstract MappingStrategy class with map_field method
  - Define MappingContext dataclass for field mapping context
  - Write unit tests for strategy interface
  - _Requirements: 2.1, 2.2_

- [x] 2.2 Implement concrete mapping strategies
  - Create DirectMappingStrategy for simple field mappings
  - Implement ComputedMappingStrategy for calculated fields (weight, pricing)
  - Build DefaultMappingStrategy for fallback values
  - Develop ConditionalMappingStrategy for dependent fields
  - Create LLMCompletionStrategy using existing llm_caller and prompt_manager
  - _Requirements: 2.1, 2.3_

- [x] 2.3 Build field mapping registry
  - Create FieldMappingRegistry class to manage strategies
  - Implement strategy registration and retrieval methods
  - Add method to apply all mappings to metadata
  - Write comprehensive unit tests for registry
  - _Requirements: 1.1, 2.1_

- [x] 2.4 Implement LLM-based field completion system
  - Create LLMFieldCompleter class using existing llm_caller and prompt_manager
  - Design prompts for contributor bio generation, BISAC suggestions, and marketing copy
  - Integrate with existing litellm infrastructure for API calls
  - Add intelligent field completion for missing LSI metadata
  - Write unit tests with mocked LLM responses
  - _Requirements: 1.1, 2.1, 4.1_

- [x] 3. Develop validation system
- [x] 3.1 Create validation framework
  - Implement abstract FieldValidator base class
  - Create ValidationResult and FieldValidationResult dataclasses
  - Build LSIValidationPipeline to orchestrate validators
  - Write unit tests for validation framework
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.2 Implement specific field validators
  - Create ISBNValidator with format and check-digit validation
  - Build PricingValidator for currency and discount validation
  - Implement DateValidator for publication and street dates
  - Create BISACValidator for BISAC code verification
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3.3 Add PDF and file validation
  - Implement PDFValidator for PDF X-1a format checking
  - Create file existence validator for FTP staging area
  - Add file naming convention validator (ISBN_interior.pdf format)
  - Validate page count and trim size consistency
  - _Requirements: 3.6, 3.7, 3.8_

- [x] 4. Build configuration management system
- [x] 4.1 Create LSI configuration class
  - Implement LSIConfiguration class with JSON config loading
  - Add methods for default values, overrides, and imprint configs
  - Support territorial configuration management
  - Create publishers/ and imprints/ directory structure for multiple configurations
  - Write unit tests for configuration loading
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 4.2 Design configuration file structure
  - Create default LSI configuration JSON templates
  - Define imprint-specific configuration sections
  - Add territorial pricing and discount configurations
  - Document configuration options and examples
  - _Requirements: 2.2, 2.3_

- [x] 5. Enhance existing LSI ACS Generator
- [x] 5.1 Refactor existing LsiAcsGenerator class to use new mapping system
  - Update existing _map_metadata_to_lsi_template method to use FieldMappingRegistry
  - Replace hardcoded field mapping with strategy-based approach
  - Integrate validation pipeline into generation process
  - Add configuration support to generator initialization
  - Maintain backward compatibility with existing interface
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 5.2 Complete comprehensive field mapping for all 100+ LSI fields
  - Analyze LSI template to identify all unmapped fields
  - Create mapping strategies for remaining fields using strategy system
  - Handle special cases for reserved fields (Reserved 1-12) and flex fields
  - Implement proper field ordering and CSV formatting
  - Add support for multiple BISAC categories and contributors
  - Map all territorial pricing fields (USBR1, USDE1, USRU1, etc.)
  - _Requirements: 1.1, 1.4_

- [x] 5.3 Add generation result reporting
  - Create GenerationResult dataclass for detailed reporting
  - Implement field population statistics and validation summaries
  - Add timestamp and metadata tracking to results
  - Write unit tests for result generation
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Implement error handling and recovery
- [x] 6.1 Create error recovery manager
  - Implement ErrorRecoveryManager class with correction methods
  - Add ISBN format correction and validation
  - Create BISAC code suggestion based on title and keywords
  - Implement missing pricing calculation for territories
  - _Requirements: 5.3, 5.4_

- [x] 6.2 Add comprehensive logging system
  - Integrate detailed logging throughout generation process
  - Log all field mappings, transformations, and validations
  - Create structured error and warning message formats
  - Add performance metrics and timing information
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 7. Create comprehensive test suite
- [x] 7.1 Write unit tests for all components
  - Test field mapping strategies independently
  - Test validation system with valid and invalid inputs
  - Test LLM field completion system with mocked responses
  - Achieve comprehensive coverage for new components
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 7.2 Implement integration tests
  - Test end-to-end metadata to CSV generation
  - Test with various metadata completeness levels
  - Test imprint and territorial configuration scenarios
  - Validate generated CSV against LSI template requirements
  - _Requirements: 1.2, 1.3, 2.2, 2.3_

- [x] 7.3 Add file system integration tests
  - Test PDF validation with sample files
  - Test FTP staging area file checks
  - Test file naming convention validation
  - Mock file system operations for reliable testing
  - _Requirements: 3.6, 3.7, 3.8_

- [x] 8. Update existing codebase integration
- [x] 8.1 Update metadata generation workflows
  - Modify existing metadata processing to populate new LSI fields
  - Update LLM prompts to extract LSI-specific information
  - Ensure backward compatibility with existing metadata objects
  - Test integration with existing book processing pipeline
  - _Requirements: 4.1, 4.4_

- [x] 8.2 Create migration utilities
  - Build utility to migrate existing metadata to new format
  - Add validation for migrated metadata completeness
  - Create scripts to populate missing LSI fields from existing data
  - Document migration process and requirements
  - _Requirements: 4.1, 4.4_

- [x] 9. Documentation and examples
- [x] 9.1 Create comprehensive documentation
  - Document all new classes, methods, and configuration options
  - Create usage examples for different publishing scenarios
  - Document LSI field mappings and validation rules
  - Add troubleshooting guide for common issues
  - _Requirements: 2.1, 3.1, 5.4_

- [x] 9.2 Create sample configurations and test data
  - Provide sample configuration files for different imprints
  - Create test metadata objects with various completeness levels
  - Add example CSV outputs for validation
  - Document best practices for LSI submission preparation
  - _Requirements: 2.2, 2.3, 5.4_

## Punch List Fixes

- [x] 10. Fix CSV output to include all pipeline job rows
  - Ensure CSV generation includes complete row data from current pipeline
  - Verify all existing metadata fields are properly mapped to CSV output
  - Test CSV generation with multiple book records from pipeline
  - _Requirements: 1.3, 6.2_

- [x] 11. Remove specific discount mode cell values from output
  - Ensure these columns are blank in CSV output: "US-Ingram-Only* Suggested List Price (mode 2)", "US-Ingram-Only* Wholesale Discount % (Mode 2)", "US - Ingram - GAP * Suggested List Price (mode 2)", "US - Ingram - GAP * Wholesale Discount % (Mode 2)", "SIBI - EDUC - US * Suggested List Price (mode 2)", "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
  - Update field mapping strategies to leave these specific mode 2 fields empty
  - Verify CSV template excludes these columns or maps them to empty values
  - _Requirements: 1.2, 1.3_

## Additional Enhancement Tasks


- [x] 15. Add advanced territorial pricing strategies
  - add a method that dynamically calculates pricing multiplier for each territory based on today's exchange rates
    - include "wiggle room" parameter that allows an extra x% increase to allow for possible unexpected variations
    - include "market access fee" that allows an extra y USD surcharge.
  - Allow market-specific pricing strategies for different territories
  - Create pricing validation against LSI territory requirements
  - Add support for promotional pricing and special discounts
  - _Requirements: 2.3, 2.4_


- [x] 18. Optimize field completion prompts
  - Review and refine LLM prompts for LSI-specific field completion
  - Use the entire main content (body) of the book when creating information about the book as a whole, e.g. description, BISAC codes, etc.
  - Enhance contributor information extraction prompts to extract information about up to 3 contributors total (but no more) if the body of the document contains it.
  - Test prompt effectiveness with real-world metadata
  - _Requirements: 1.1, 2.1, 4.1_

- [x] 17. Enhance validation with LSI-specific business rules
  - Add validation for LSI account-specific requirements
  - Implement validation for territorial distribution restrictions
  - Add checks for LSI special category eligibility
  - Validate file naming conventions against LSI standards
  - _Requirements: 3.1, 3.2, 3.5_