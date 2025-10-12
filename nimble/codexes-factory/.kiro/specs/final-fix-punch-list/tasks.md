# Implementation Plan

- [ ] 1. Enhance UPC barcode generation and positioning system
  - [x] 1.1 Update ISBNBarcodeGenerator with positioning and safety space validation
    - Modify `src/codexes/modules/distribution/isbn_barcode_generator.py` to add positioning methods
    - Implement `calculate_barcode_position()` method to maintain current location with safety spaces
    - Add `validate_safety_spaces()` method to ensure adequate spacing around barcode
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Integrate enhanced barcode generator with cover generation pipeline
    - Update cover generation code to use new positioning methods
    - Ensure barcode placement maintains current location standards
    - Add validation to prevent barcode overlap with other cover elements
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Implement dotgrid positioning controller for interior layout
  - [x] 2.1 Create DotgridLayoutManager class
    - Create `src/codexes/modules/prepress/dotgrid_layout_manager.py`
    - Implement `calculate_dotgrid_position()` method with 0.5 inch minimum spacing
    - Add `validate_spacing_requirements()` method to ensure proper header/footer spacing
    - Write unit tests for positioning calculations
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Update LaTeX templates with improved dotgrid positioning
    - Modify dotgrid positioning in `imprints/xynapse_traces/template.tex`
    - Update `\dotgridtranscription` command to use new positioning logic
    - Ensure 0.5 inch minimum spacing between header bottom and dotgrid beginning
    - Test template compilation with new positioning
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 3. Create ISBN formatting system for copyright page
  - [x] 3.1 Implement ISBNFormatter class
    - Create `src/codexes/modules/metadata/isbn_formatter.py`
    - Implement `format_isbn_13_hyphenated()` method with proper hyphenation rules
    - Add `validate_isbn_format()` method with check digit validation
    - Create `generate_copyright_page_isbn()` method for display formatting
    - Write unit tests for ISBN formatting and validation
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.2 Integrate ISBN formatter with copyright page generation
    - Update copyright page generation code to use ISBNFormatter
    - Ensure properly hyphenated 13-digit ISBN with check digit display
    - Add validation to prevent malformed ISBN display
    - Test copyright page generation with various ISBN formats
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4. Build subtitle validation and LLM replacement system
  - [x] 4.1 Create SubtitleValidator class with nimble-llm-caller integration
    - Create `src/codexes/modules/metadata/subtitle_validator.py`
    - Implement `validate_subtitle_length()` method with 38 character limit for xynapse_traces
    - Add `generate_replacement_subtitle()` method using nimble-llm-caller
    - Implement `process_xynapse_subtitle()` method for complete validation and replacement flow
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Integrate subtitle validator with metadata processing pipeline
    - Update metadata processing to call subtitle validation for xynapse_traces titles
    - Ensure LLM-generated subtitles meet character limit requirements
    - Add error handling and fallback for LLM failures
    - Write integration tests for subtitle replacement workflow
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Enhance spine width calculation system
  - [x] 5.1 Update spine width calculator with SpineWidthLookup.xlsx integration
    - Enhance existing spine width calculation in `src/codexes/modules/covers/metadata2lsicoverspecs.py`
    - Ensure `calculate_spinewidth()` method uses "Standard perfect 70" page type
    - Add validation for calculated spine width values
    - Implement error handling with safe fallback values
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Implement spine width distribution to metadata and cover creator
    - Create `distribute_spine_width()` method to provide calculated width to both systems
    - Update metadata processing to receive and store spine width
    - Update cover generation to use distributed spine width values
    - Add logging for spine width calculation and distribution
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Create comprehensive error handling and logging system
  - [x] 6.1 Implement error handling for all fix components
    - Add try-catch blocks with specific error types for each component
    - Implement fallback strategies for LLM failures, lookup failures, and calculation errors
    - Add comprehensive logging to `logs/` directory with component context
    - Create error recovery mechanisms for template modifications
    - _Requirements: 1.3, 2.3, 3.3, 4.4, 5.5_

  - [x] 6.2 Add validation and safety checks across all components
    - Implement input validation for all public methods
    - Add safety checks to prevent invalid barcode positioning
    - Create validation for template modifications before application
    - Add checks to ensure generated content meets publishing standards
    - _Requirements: 1.3, 2.3, 3.3, 4.4, 5.5_

- [ ] 7. Write comprehensive test suite for all fixes
  - [x] 7.1 Create unit tests for individual components
    - Write tests for ISBNBarcodeGenerator positioning methods
    - Create tests for DotgridLayoutManager spacing calculations
    - Add tests for ISBNFormatter hyphenation and validation
    - Write tests for SubtitleValidator length checking and LLM integration
    - Create tests for enhanced spine width calculations
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 7.2 Create integration tests for end-to-end workflows
    - Write tests for complete book generation with all fixes applied
    - Create tests for xynapse_traces specific processing with subtitle replacement
    - Add tests for spine width propagation through metadata and cover generation
    - Write tests for template modification and LaTeX compilation
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Update configuration and documentation
  - [x] 8.1 Create configuration files for new components
    - Add LLM configuration for subtitle generation in `configs/llm_prompt_config.json`
    - Create imprint-specific configuration for xynapse_traces subtitle limits
    - Add spine width configuration with lookup file path and fallback values
    - Update existing configuration files to include new component settings
    - _Requirements: 4.3, 4.4, 5.1, 5.2_

  - [x] 8.2 Update documentation and usage guides
    - Document new components and their usage in appropriate docs files
    - Create troubleshooting guide for common issues with fixes
    - Update existing documentation to reflect changes in barcode and layout systems
    - Add examples of proper ISBN formatting and subtitle validation
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_