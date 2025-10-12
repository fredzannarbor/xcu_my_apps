# Implementation Plan

- [x] 1. Fix default configuration values in Book Pipeline UI
  - Update default values for lightning_source_account, language_code, and field_reports
  - Ensure defaults are visible in the UI form fields
  - Add validation for required fields
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Fix LLM configuration propagation in BackmatterProcessor
  - Update BackmatterProcessor to use provided LLM configuration instead of hardcoded values
  - Change default model from gemini-2.5-flash to gpt-4o-mini
  - Add logging to show which LLM model is being used
  - _Requirements: 2.1, 2.2, 2.5, 2.6_

- [x] 3. Update XynapseTracesPrepress to pass LLM configuration
  - Modify XynapseTracesPrepress to extract LLM config from pipeline configuration
  - Pass LLM configuration to BackmatterProcessor during initialization
  - Ensure configuration flows properly from pipeline to processors
  - _Requirements: 2.1, 2.2_

- [x] 4. Fix foreword generation LLM configuration
  - Update foreword generation to use pipeline LLM configuration instead of hardcoded gemini-2.5-pro
  - Ensure foreword generation receives LLM config from prepress workflow
  - Add logging for foreword generation model usage
  - _Requirements: 2.3, 2.6, 4.1_

- [x] 5. Fix publisher's note generation LLM configuration
  - Update PublishersNoteGenerator to accept and use pipeline LLM configuration
  - Ensure publisher's note generation uses configured model instead of hardcoded values
  - Add logging for publisher's note generation model usage
  - _Requirements: 2.4, 2.6, 4.2_

- [x] 6. Implement font configuration system in template processing
  - Update _process_template method to inject font variables from configuration
  - Add font configuration extraction from tranche/imprint settings
  - Ensure Korean font and other fonts are properly substituted in templates
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 7. Update LaTeX template to use font variables
  - Replace hardcoded "Apple Myungjo" with {korean_font} template variable
  - Ensure template can handle font substitution gracefully
  - Add fallback handling for missing font configurations
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 8. Validate glossary generation and formatting
  - Ensure glossary is generated in proper 2-column layout within page margins
  - Verify Korean terms appear at top of left-hand cells with English equivalents below
  - Test glossary layout with various term counts and lengths
  - Add validation for glossary formatting requirements
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 9. Fix LaTeX escaping and command formatting issues
  - Fix broken LaTeX commands like "extit{" in foreword and other generated content
  - Implement robust LaTeX escaping for all text processing
  - Ensure no stray LaTeX commands appear in final output
  - Add validation to detect and fix malformed LaTeX commands
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10. Implement proper bibliography formatting with hanging indents
  - Ensure bibliography citations have first line flush left
  - Implement 0.15 inch indentation for second and following lines
  - Verify hanging indent formatting appears correctly in compiled PDF
  - Add validation for bibliography formatting requirements
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 11. Add configuration validation and error handling
  - Implement validation for required fields (lightning_source_account, language_code)
  - Add validation for LLM configuration parameters
  - Add validation for font configuration and provide helpful error messages
  - Create clear error messages for configuration issues
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 12. Add comprehensive logging and transparency
  - Log LLM model usage in BackmatterProcessor, foreword, and publisher's note generation
  - Log configuration values at pipeline startup
  - Log template substitution details for debugging
  - Log backmatter generation success/failure for all components
  - Add monitoring for configuration validation success/failure
  - Add logging for LaTeX processing errors with context
  - _Requirements: TR6_

- [ ] 13. Create integration tests for configuration fixes
  - Test that default values are properly applied in pipeline
  - Test that LLM configuration flows correctly to BackmatterProcessor, foreword, and publisher's note generation
  - Test that font configuration is properly substituted in templates
  - Test that glossary is generated with proper 2-column Korean/English layout
  - Test that LaTeX escaping prevents broken commands in output
  - Test that bibliography formatting includes proper hanging indents
  - Test error handling for invalid configurations
  - _Requirements: All requirements validation_

- [ ] 14. Update documentation and create migration guide
  - Document the new default values and their rationale
  - Create guide for users to update existing configurations
  - Document the font configuration system
  - Document LLM configuration propagation to all backmatter components
  - Document glossary generation requirements and formatting
  - Document LaTeX escaping improvements and bibliography formatting
  - _Requirements: User guidance and transparency_