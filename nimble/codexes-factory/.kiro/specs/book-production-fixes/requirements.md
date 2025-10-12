# Book Production Fixes and Enhancements Requirements

## Introduction

This specification addresses critical production issues and enhancements needed for the book generation pipeline, covering typography, formatting, error handling, reporting accuracy, and new features for professional book production. The system currently has several issues affecting the quality and reliability of generated books, including bibliography formatting problems, inefficient ISBN lookups, inaccurate reporting, and inconsistent typography that fails to meet professional publishing standards.

## Requirements

### Requirement 1: Bibliography Formatting Enhancement

**User Story:** As a publisher and editor, I want bibliographies to use proper hanging indent formatting with memoir citation fields, so that the bibliography appears professionally formatted according to publishing standards.

#### Acceptance Criteria

1. WHEN a bibliography is generated THEN it SHALL use memoir citation field formatting
2. WHEN bibliography entries span multiple lines THEN the second and subsequent lines SHALL have a 0.15 hanging indent
3. WHEN bibliography entries are processed THEN they SHALL maintain consistent formatting across all entries
4. WHEN the LaTeX template is applied THEN bibliography formatting SHALL be automatically applied without manual intervention
5. WHEN multiple bibliography entries exist THEN each SHALL be properly separated and formatted independently

### Requirement 2: ISBN Lookup and Caching System

**User Story:** As a system administrator, I want ISBN lookups to be cached in processed JSON files and avoid duplicate scans, so that the system is efficient and doesn't repeat expensive API calls.

#### Acceptance Criteria

1. WHEN an ISBN is encountered in a document THEN the system SHALL check if it has already been processed in the cached JSON
2. WHEN an ISBN lookup is performed THEN the results SHALL be stored in the processed JSON file for future reference
3. WHEN a document is scanned for ISBNs THEN the system SHALL not repeat the scan if it has already been completed
4. WHEN cached ISBN data exists THEN it SHALL be used instead of making new API calls
5. WHEN ISBN lookup fails THEN the system SHALL log the failure and continue processing without blocking the pipeline

### Requirement 3: Accurate Prompt and Quote Reporting

**User Story:** As a content manager, I want accurate reporting of prompt success and quote retrieval statistics, so that I can monitor the effectiveness of the content generation process.

#### Acceptance Criteria

1. WHEN 90 quotes are successfully retrieved THEN the report SHALL accurately reflect this count, not show 0
2. WHEN prompts execute successfully THEN the success rate SHALL be accurately calculated and reported
3. WHEN quote retrieval completes THEN the system SHALL provide detailed statistics on success/failure rates
4. WHEN reporting is generated THEN it SHALL align with actual test results and pipeline execution
5. WHEN multiple prompts are processed THEN each prompt's individual success rate SHALL be tracked and reported

### Requirement 4: Error Handling and Logging Improvements

**User Story:** As a developer, I want comprehensive error handling and logging for quote verification and field completion failures, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. WHEN quote verification fails THEN the system SHALL log detailed error information including the response received
2. WHEN the verifier model returns invalid data THEN the system SHALL handle the error gracefully and continue processing
3. WHEN field completion fails due to missing methods THEN the system SHALL provide clear error messages and fallback behavior
4. WHEN validation reports 0 fields checked THEN the system SHALL investigate and report why no fields were processed
5. WHEN runtime errors occur THEN they SHALL be logged with sufficient context for debugging and resolution

### Requirement 5: Book Pipeline UI Must Display and Honor Available Tranche Configs

**User Story:** As a web admin and system operator, I need the tranche config to be available on the dropdowns in the Book Pipeline, so that users can select appropriate tranche configurations for book processing.

#### Acceptance Criteria

1. WHEN the Book Pipeline UI loads THEN the tranche dropdown SHALL display all available tranche configurations
2. WHEN tranche configurations are updated THEN the dropdown SHALL refresh to show current options
3. WHEN a user selects a tranche THEN the system SHALL load the corresponding configuration
4. WHEN no tranche configurations exist THEN the system SHALL display an appropriate message
5. WHEN tranche selection is made THEN it SHALL be properly passed to the book processing pipeline

### Requirement 6: Typography and Formatting Enhancements

**User Story:** As a book designer, I want consistent typography and formatting across all book elements, so that the final product meets professional publishing standards.

#### Acceptance Criteria

1. WHEN mnemonics pages are generated THEN they SHALL use the same format as quotations with Adobe Caslon font
2. WHEN acronym mnemonics are displayed THEN each letter of the expanded acronym SHALL have its own bullet point
3. WHEN Korean characters appear on title pages THEN they SHALL use Apple Myungjo font
4. WHEN instructions are placed THEN they SHALL appear on every 8th recto page at the bottom
5. WHEN chapter headings are formatted THEN the leading underneath SHALL be reduced to approximately 36 points
6. WHEN LaTeX commands are used THEN they SHALL be properly escaped so that they are not visible. For example, the string "\textit" should never be visible in the compiled PDF.

### Requirement 7: Glossary Layout and Formatting

**User Story:** As a content formatter, I want glossaries to be properly formatted in 2 columns within the page text area, so that Korean and English terms are clearly presented.

#### Acceptance Criteria

1. WHEN a glossary is generated THEN it SHALL be formatted in exactly 2 columns
2. WHEN glossary content is laid out THEN it SHALL fit within the defined page text area
3. WHEN Korean and English terms are displayed THEN they SHALL be stacked on top of each other in the left-hand cells
4. WHEN glossary formatting is applied THEN it SHALL maintain consistent spacing and alignment
5. WHEN multiple glossary entries exist THEN they SHALL be distributed evenly across both columns

### Requirement 8: Publisher's Note Enhancement

**User Story:** As an editor, I want the Publisher's Note to be concise, engaging, and properly formatted, so that it effectively motivates both publishers and readers.

#### Acceptance Criteria

1. WHEN the Publisher's Note is generated THEN it SHALL consist of exactly 3 medium-length paragraphs
2. WHEN each paragraph is created THEN it SHALL have a maximum of 600 characters
3. WHEN the content is written THEN it SHALL explain once that this is a pilsa book
4. WHEN current events are referenced THEN they SHALL be included without being date-specific
5. WHEN the note is finalized THEN it SHALL focus on motivating both publisher and reader engagement

### Requirement 9: Mnemonics JSON properly created

**User Story:** As an editor, I want a properly created Mnemonics appendix for each book, so that the mnemonics.tex file is generated successfully without JSON parsing errors.

#### Acceptance Criteria

1. WHEN mnemonics are generated THEN the LLM response SHALL include the expected 'mnemonics_data' key
2. WHEN the mnemonics prompt is executed THEN it SHALL be reformulated to require the expected JSON structure
3. WHEN JSON parsing fails THEN the system SHALL provide clear error messages and fallback behavior
4. WHEN mnemonics content is missing THEN the system SHALL log the issue and continue processing
5. WHEN mnemonics.tex is created THEN it SHALL contain properly formatted mnemonic content

### Requirement 10: Back Text should include mention that book is pilsa book

**User Story:** As a reader and publisher, I want the book description to clearly identify this as a pilsa book, so that readers understand the unique nature and purpose of the publication.

#### Acceptance Criteria

1. WHEN descriptive content is generated THEN it SHALL clearly identify the book as a pilsa or transcriptive meditation handbook
2. WHEN book descriptions are created THEN they SHALL mention the 90 quotations and 90 facing pages for journaling
3. WHEN back cover text is generated THEN it SHALL include the pilsa book designation
4. WHEN marketing copy is written THEN it SHALL emphasize the unique meditative and journaling aspects
5. WHEN book metadata is created THEN it SHALL consistently reference the pilsa format

### Requirement 11: BISAC Categories 2 and 3 are too vague

**User Story:** As a publisher and bookseller, I want BISAC categories to accurately reflect the specific technical content of each book, so that readers can find books through appropriate subject classifications.

#### Acceptance Criteria

1. WHEN BISAC categories are generated THEN they SHALL reflect the specific technical content discussed in the book
2. WHEN generic categories like "Business>General" are detected THEN they SHALL be replaced with more specific classifications
3. WHEN technical content is analyzed THEN appropriate categories like "Science > Planetary Exploration" SHALL be selected
4. WHEN multiple BISAC categories are assigned THEN each SHALL be relevant to the book's actual content
5. WHEN category validation occurs THEN it SHALL ensure categories match the book's subject matter

### Requirement 12: Writing Style Configuration System

**User Story:** As a publisher, I want configurable writing styles at tranche, imprint, and publisher levels, so that I can maintain consistent voice and tone across publications.

#### Acceptance Criteria

1. WHEN writing style configuration is needed THEN it SHALL be available at tranche, imprint, and publisher levels
2. WHEN style configuration is defined THEN it SHALL be stored in a writing_style.json file in the appropriate directory
3. WHEN multiple text values exist in the JSON THEN they SHALL be constructed into a single prompt to append to the original prompt
4. WHEN style configuration is applied THEN it SHALL override lower-level configurations (tranche > imprint > publisher)
5. WHEN no style configuration exists THEN the system SHALL use default styling without errors

### Requirement 13: Quote Assembly and Author Distribution

**User Story:** As a content curator, I want quote assembly to avoid repetitive author citations, so that the quotations section has better variety and readability.

#### Acceptance Criteria

1. WHEN quotations are assembled THEN no single author SHALL be quoted more than three times in a row
2. WHEN author repetition is detected THEN the system SHALL reorder quotes to improve distribution
3. WHEN quote ordering is applied THEN it SHALL maintain thematic coherence while improving author variety
4. WHEN insufficient quotes exist from different authors THEN the system SHALL work with available content while minimizing repetition
5. WHEN quote assembly is complete THEN the final arrangement SHALL be reviewed for author distribution balance

### Requirement 14: Last Verso Page

**User Story:** As a book designer, I want blank last verso pages to have a "Notes" heading, so that the page serves a functional purpose for readers.

#### Acceptance Criteria

1. WHEN the last verso page is blank THEN it SHALL have a chapter heading reading "Notes" at the top of the page
2. WHEN the Notes heading is added THEN it SHALL follow the same formatting as other chapter headings
3. WHEN the last verso page has content THEN no Notes heading SHALL be added
4. WHEN the Notes page is created THEN it SHALL provide space for reader annotations
5. WHEN the book is compiled THEN the Notes page SHALL be properly positioned as the final verso page

### Requirement 15: ISBN and Barcode Integration

**User Story:** As a publisher, I want automatic UPC-A barcode generation with ISBN-13 when ISBNs are assigned, so that books are ready for retail distribution.

#### Acceptance Criteria

1. WHEN an ISBN-13 is assigned to a book THEN a UPC-A barcode SHALL be automatically generated
2. WHEN the barcode is created THEN it SHALL include bar-code-reader numerals for retail scanning
3. WHEN the barcode is integrated THEN it SHALL be properly positioned on the back cover
4. WHEN barcode generation occurs THEN it SHALL meet industry standards for retail distribution
5. WHEN ISBN assignment is complete THEN the book SHALL be ready for retail with proper barcode integration

### Requirement 16: Storefront Catalog metadata

**User Story:** As the operator of a online book storefront, I want all metadata for each title to be complete and accurate.

#### Acceptance Criteria

1. WHEN storefront metadata is generated THEN the author name SHALL match the Contributor One name from the Tranche config
2. WHEN author fields are populated THEN they SHALL not be interpolated or generated by the model
3. WHEN storefront_author_en and _ko fields are created THEN they SHALL use the exact name from the configuration
4. WHEN metadata is validated THEN it SHALL ensure consistency between LSI CSV and storefront data
5. WHEN tranche configuration is missing author data THEN the system SHALL provide clear error messages



## Success Criteria

- Bibliography entries display with proper hanging indents using memoir citation fields
- ISBN lookups are cached and not repeated, improving system efficiency
- Reporting accurately reflects actual prompt success and quote retrieval statistics
- Error handling provides clear, actionable information for debugging
- Typography and formatting meet professional publishing standards
- Glossaries are properly formatted in 2 columns with correct term stacking
- Publisher's Notes are concise, engaging, and properly structured
- Writing style configuration works across all organizational levels
- Quote assembly avoids excessive author repetition
- ISBN assignment automatically generates proper UPC-A barcodes
- Storefront metadata uses accurate author names from tranche configuration

## Technical Considerations

- LaTeX memoir class integration for bibliography formatting
- JSON caching system for ISBN lookup results
- Enhanced logging and error reporting mechanisms
- Font management for Korean characters (Apple Myungjo)
- Column layout algorithms for glossary formatting
- Hierarchical configuration loading system
- Quote reordering algorithms for author distribution
- Barcode generation libraries and positioning systems
- Tranche configuration integration for accurate metadata sourcing
