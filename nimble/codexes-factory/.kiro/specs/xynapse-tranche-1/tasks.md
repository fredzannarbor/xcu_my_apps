# Implementation Plan

- [x] 1. Set Lightning Source Account # to 6024045
  - Lightning Source Account is already set to "6024045" in configs/default_lsi_config.json
  - Account number appears correctly in generated CSV files
  - _Punch List Item: 1_

- [x] 2. Exclude Metadata Contact Dictionary from CSV output
  - Modify LSI CSV generator to skip "Metadata Contact Dictionary" field in output
  - Test that field does not appear in final CSV files
  - _Punch List Item: 2_

- [x] 3. Ensure Parent ISBN field is empty
  - Verify Parent ISBN field mapping returns empty string for this tranche
  - Test that Parent ISBN is empty in all generated CSV files
  - _Punch List Item: 3_

- [x] 4. Load ISBN database with real data
  - Imported authoritative ISBN data from /Users/fred/Downloads/prefix-978160888.csv using corrected logic
  - Database contains exactly 1,000 ISBNs: 680 available, 320 publicly assigned (with complete metadata)
  - Status correctly determined: ISBNs with Title, Format, and Status non-empty are publicly assigned
  - Ready to import additional Bowker files as they become available
  - _Punch List Item: 4_

- [x] 5. Assign unique ISBNs from database
  - Implement ISBN assignment functionality to assign unique ISBNs to each book
  - Test that each book gets a unique, valid ISBN from the database
  - _Punch List Item: 5_

- [x] 6. Create tranche configuration system
  - Create configs/tranches/ directory structure
  - Create configs/tranches/xynapse_tranche_1.json with batch-level settings
  - Modify pipeline to load and apply tranche config to all books in batch
  - Test that tranche settings are applied consistently to all 12 books
  - _Punch List Item: 6_

- [x] 7. Add rendition booktype validation
  - Implement validation check in field mapping using existing lsi_valid_rendition_booktypes.txt
  - Add validation to ensure booktype is in valid list before CSV generation
  - Test validation with both valid and invalid booktype values
  - _Punch List Item: 7_

- [x] 8. Add contributor role validation
  - Created contributor_role_validator.py with validation against LSI codes
  - Implemented ContributorRoleMappingStrategy for field mapping
  - Updated enhanced_field_mappings.py to use the new mapping strategy
  - Added comprehensive tests for validation and correction
  - _Punch List Item: 8_

- [x] 9. Implement Tuesday publication date distribution
  - Create date calculation utility to find all Tuesdays in target month
  - Read month/year from existing xynapse_traces_schedule.json
  - Implement date assignment logic to spread 12 books across available Tuesdays
  - Test that dates are assigned correctly and evenly distributed
  - _Punch List Item: 9_

- [x] 10. Combine LLM results with boilerplate for annotations
  - Created AnnotationProcessor class to handle boilerplate application
  - Modified LLM field completer to prepare annotations for boilerplate
  - Updated generate_lsi_csv.py to use AnnotationProcessor
  - Added comprehensive tests for annotation processing
  - _Punch List Item: 10_

- [x] 11. Strip codes from BISAC Subject fields
  - Created bisac_utils.py with strip_bisac_code and get_bisac_code functions
  - Created BisacCategoryMappingStrategy to handle BISAC field mapping
  - Updated enhanced_field_mappings.py to use the new mapping strategy
  - Added comprehensive tests for all components
  - _Punch List Item: 11_

- [x] 12. Add tranche BISAC Subject override
  - Added get_tranche_bisac_subject method to TrancheConfigLoader
  - Modified BisacCategoryMappingStrategy to check for tranche override
  - Updated FieldMappingRegistry to include context_config for overrides
  - Added comprehensive tests for tranche BISAC override functionality
  - _Punch List Item: 12_

- [x] 13. Add short description length validation
  - Created text_length_validator.py with validation and truncation functions
  - Implemented ShortDescriptionMappingStrategy for field mapping
  - Updated enhanced_field_mappings.py to use the new mapping strategy
  - Added comprehensive tests for validation and truncation
  - _Punch List Item: 13_

- [x] 14. Fix truncated Thema subjects
  - Created thema_subject_mapping.py with comprehensive Thema code mappings
  - Implemented ThemaSubjectMappingStrategy for field mapping
  - Updated enhanced_field_mappings.py to use the new mapping strategy
  - Added tests to verify proper expansion of Thema codes
  - _Punch List Item: 14_

- [x] 15. Set GC market prices equal to US price
  - Modified territorial_pricing.py to return base price for GC territory
  - Created test_territorial_pricing.py to verify the implementation
  - Confirmed that GC market prices are now equal to US price
  - _Punch List Item: 15_