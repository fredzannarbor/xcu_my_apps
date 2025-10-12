# Implementation Plan

- [x] 1. Create tranche override management system
  - Implement TrancheOverrideManager class with replace/append logic
  - Add methods to determine override precedence and field types
  - Create unit tests for override behavior with various field types
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement JSON metadata extraction utilities
  - Create JSONMetadataExtractor class for thema and age data extraction
  - Add thema subject extraction with array handling and validation
  - Implement age range extraction with integer conversion and bounds checking
  - Write comprehensive unit tests for extraction edge cases
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Build series-aware description processor
  - Create SeriesDescriptionProcessor class for "This book" replacement logic
  - Implement series name validation and context checking
  - Add string replacement logic with series name interpolation
  - Write unit tests for various description and series combinations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 4. Create enhanced field mapping strategies
  - Implement ThemaSubjectStrategy for mapping extracted thema codes to LSI columns
  - Create AgeRangeStrategy for mapping min/max age values to integer columns
  - Build SeriesAwareDescriptionStrategy integrating description processor
  - Implement BlankIngramPricingStrategy to enforce blank values for specific pricing fields
  - Add TrancheFilePathStrategy for file path generation from tranche templates
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2_

- [x] 5. Integrate tranche override system with field mapping
  - Modify existing field mapping strategies to use TrancheOverrideManager
  - Update field mapping registry to apply overrides after LLM generation
  - Ensure append-type fields (like annotation_boilerplate) work correctly
  - Add integration tests for override precedence across different field types
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 6. Update tranche configuration schema and loading
  - Extend tranche configuration to support field_overrides and append_fields
  - Add file_path_templates and blank_fields configuration options
  - Update configuration validation to handle new schema elements
  - Modify tranche configuration loader to parse new fields
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 7. Implement comprehensive field validation
  - Add validation for thema subject codes against known formats
  - Implement age range bounds checking (0-150) with error logging
  - Create file path sanitization for LSI naming convention compliance
  - Add validation error collection and reporting mechanisms
  - _Requirements: 2.5, 3.3, 3.4, 6.4, 6.5_

- [x] 8. Wire new strategies into LSI generation pipeline
  - Register new field mapping strategies in the field mapping registry
  - Update LSI CSV generator to use enhanced strategies
  - Ensure proper order of operations (extraction → mapping → override → validation)
  - Add logging for each correction step for debugging purposes
  - _Requirements: All requirements integration_

- [x] 9. Create comprehensive test suite
  - Write integration tests for complete LSI generation with all corrections
  - Test with sample book metadata containing thema, age, and series data
  - Verify blank Ingram pricing fields in generated CSV output
  - Test tranche override precedence with real configuration files
  - Add performance tests to ensure no significant regression
  - _Requirements: All requirements validation_

- [x] 10. Update existing tranche configuration files
  - Add field_overrides for Series Name in xynapse_tranche_1.json
  - Configure blank_fields for Ingram pricing columns
  - Add file_path_templates for interior and cover file generation
  - Test updated configuration with live pipeline
  - _Requirements: 1.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2_