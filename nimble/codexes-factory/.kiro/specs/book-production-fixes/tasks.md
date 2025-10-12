# Implementation Plan

- [x] 1. Fix bibliography formatting with memoir citation fields and hanging indent
  - Implement BibliographyFormatter class with memoir citation field integration
  - Add 0.15 hanging indent formatting for second and subsequent lines
  - Create LaTeX template modifications for proper bibliography display
  - Test bibliography formatting with multiple entries and long citations
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement ISBN lookup caching system to prevent duplicate API calls
  - Create ISBNLookupCache class with persistent JSON storage
  - Add document scanning tracking to avoid duplicate ISBN scans
  - Implement cache validation and expiration mechanisms
  - Add error handling for cache corruption and API failures
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Fix reporting accuracy for prompt success and quote retrieval statistics
  - Implement AccurateReportingSystem to track real-time statistics
  - Fix quote count reporting to show actual retrieved counts (not 0)
  - Add detailed prompt execution tracking with success/failure rates
  - Align reported statistics with actual pipeline execution results
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Enhance error handling for quote verification and field completion failures
  - Create EnhancedErrorHandler with detailed logging and context
  - Fix quote verification error handling for invalid verifier model responses
  - Add graceful fallbacks for field completion method errors
  - Implement comprehensive error logging with debugging context
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Implement Book Pipeline UI tranche configuration dropdown
  - Create TrancheConfigUIManager to load and display available tranche configurations
  - Update Book Pipeline UI to populate tranche dropdown with available options
  - Add tranche selection validation and configuration loading
  - Implement dropdown refresh functionality when configurations change
  - Test tranche selection and configuration passing to pipeline
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement typography enhancements for professional formatting
  - Create TypographyManager for consistent font and layout management
  - Format mnemonics pages with Adobe Caslon font matching quotations style
  - Add Apple Myungjo font support for Korean characters on title pages
  - Implement instruction placement on every 8th recto page bottom
  - Adjust chapter heading leading to approximately 36 points
  - Ensure LaTeX commands are properly escaped and not visible in final PDF
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 7. Implement 2-column glossary layout with Korean/English term stacking
  - Create GlossaryLayoutManager for proper column formatting
  - Ensure glossary fits within page text area constraints
  - Stack Korean and English terms vertically in left-hand cells
  - Distribute glossary entries evenly across both columns
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Enhance Publisher's Note generation with structured formatting
  - Create PublishersNoteGenerator with 3-paragraph structure requirement
  - Implement 600-character maximum limit per paragraph validation
  - Ensure pilsa book explanation is included exactly once
  - Add current events references without date-specific content
  - Focus content on motivating both publishers and readers
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Fix mnemonics JSON generation to include required keys
  - Create MnemonicsJSONProcessor with proper JSON structure validation
  - Update mnemonics prompt to require 'mnemonics_data' key in response
  - Implement validation for expected JSON keys before processing
  - Add error handling for missing keys with fallback behavior
  - Test mnemonics.tex creation with validated JSON data
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 10. Implement pilsa book identification in all content types
  - Create PilsaBookContentProcessor to add pilsa identification
  - Update back cover text generation to include pilsa book description
  - Ensure all descriptive content mentions 90 quotations and journaling pages
  - Add pilsa book designation to marketing copy and metadata
  - Validate pilsa description consistency across all content types
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11. Implement specific BISAC category generation
  - Create BISACCategoryAnalyzer to analyze book content for relevant categories
  - Replace generic categories like "Business>General" with specific technical categories
  - Implement content analysis to determine appropriate categories like "Science > Planetary Exploration"
  - Validate category relevance to actual book content
  - Test category generation with various book topics
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 12. Create hierarchical writing style configuration system
  - Implement WritingStyleManager with tranche/imprint/publisher hierarchy
  - Create writing_style.json file format and validation
  - Build prompt construction system for multiple text values
  - Add style configuration loading with proper precedence rules
  - Test style configuration application across different levels
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 13. Optimize quote assembly to prevent excessive author repetition
  - Create QuoteAssemblyOptimizer to limit consecutive author quotes
  - Implement quote reordering algorithm to improve author distribution
  - Ensure no author appears more than 3 times consecutively
  - Maintain thematic coherence while improving variety
  - Test quote assembly with various author distributions
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 14. Implement Notes heading for blank last verso pages
  - Create LastVersoPageManager to detect blank last verso pages
  - Add "Notes" chapter heading to blank last verso pages
  - Ensure Notes heading follows same formatting as other chapter headings
  - Validate Notes page positioning as final verso page
  - Test Notes page creation with various book structures
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 15. Implement ISBN barcode generation with UPC-A format
  - Create ISBNBarcodeGenerator for automatic barcode creation
  - Generate UPC-A barcodes with ISBN-13 and bar-code-reader numerals
  - Integrate barcode positioning into back cover design
  - Ensure barcode meets industry standards for retail scanning
  - Test barcode generation and integration with various ISBN formats
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 16. Fix storefront metadata to use accurate author information
  - Create StorefrontMetadataManager to extract author from tranche configuration
  - Ensure storefront_author_en and _ko fields use Contributor One name from tranche config
  - Prevent model interpolation of author names
  - Validate author consistency between LSI CSV and storefront data
  - Add error handling for missing author data in tranche configuration
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 17. Create comprehensive testing suite for all production fixes
  - Write unit tests for bibliography formatting, ISBN caching, and reporting accuracy
  - Create integration tests for typography enhancements and layout systems
  - Test error handling scenarios and recovery mechanisms
  - Test new UI components and configuration systems
  - Validate all fixes work together in complete pipeline execution
  - _Requirements: All requirements validation_

- [x] 18. Update documentation and user guides for new features
  - Document writing style configuration system usage
  - Create troubleshooting guide for enhanced error handling
  - Update typography and formatting guidelines
  - Document tranche configuration UI usage
  - Provide examples of proper bibliography and glossary formatting
  - _Requirements: All requirements documentation_