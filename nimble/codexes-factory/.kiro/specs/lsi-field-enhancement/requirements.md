# Requirements Document

## Introduction

The LSI ACS Generator currently maps a subset of available LSI (Lightning Source Inc.) fields from CodexMetadata objects to CSV format. The LSI template contains over 100 fields including account information, submission methods, territorial rights, multiple pricing tiers, contributor details, and specialized distribution options. This enhancement will expand the generator to support comprehensive field mapping, provide configuration options for different publishing scenarios, and ensure data validation for LSI submission requirements.

## Requirements

### Requirement 1

**User Story:** As a publisher using the codexes system, I want the LSI ACS generator to support all available LSI fields, so that I can create complete submission files without manual editing.

#### Acceptance Criteria

1. WHEN the LSI ACS generator processes metadata THEN it SHALL map all 100+ LSI template fields to appropriate values
2. WHEN a field has no corresponding metadata value THEN the system SHALL use appropriate default values or leave empty based on LSI requirements
3. WHEN generating the CSV THEN the system SHALL maintain the exact field order and formatting required by LSI
4. WHEN processing contributor information THEN the system SHALL support multiple contributors with roles, bios, affiliations, and locations

### Requirement 2

**User Story:** As a publisher with different distribution strategies, I want configurable LSI field mappings, so that I can customize output for different imprints, territories, and pricing models.

#### Acceptance Criteria

1. WHEN configuring the generator THEN the system SHALL allow custom field mapping overrides
2. WHEN setting up different imprints THEN the system SHALL support imprint-specific default values
3. WHEN handling territorial rights THEN the system SHALL support region-specific pricing and discount configurations
4. WHEN processing series information THEN the system SHALL automatically populate series-related fields from metadata

### Requirement 3

**User Story:** As a system administrator, I want comprehensive validation of LSI field data, so that generated files meet LSI submission requirements and reduce rejection rates.

#### Acceptance Criteria

1. WHEN validating ISBN data THEN the system SHALL verify format and check-digit validity
2. WHEN processing pricing information THEN the system SHALL validate currency formats and discount percentages
3. WHEN handling dates THEN the system SHALL ensure proper date formatting for publication and street dates
4. WHEN validating BISAC codes THEN the system SHALL verify against current BISAC standards
5. WHEN checking physical specifications THEN the system SHALL validate trim sizes and page counts
6. WHEN validating digital files THEN interior and cover files SHALL be available in ftp2lsi staging area with names matching ISBN_interior.pdf and ISBN_cover.pdf
7. WHEN processing PDF files THEN interior and cover files SHALL pass verification as PDF X-1a format
8. WHEN validating interior specifications THEN interior PDF SHALL match page count and trim sizes provided in LSI spreadsheet

### Requirement 4

**User Story:** As a content manager, I want enhanced metadata model support, so that all LSI-specific information can be stored and retrieved from the system.

#### Acceptance Criteria

1. WHEN extending the metadata model THEN the system SHALL add fields for all unmapped LSI requirements
2. WHEN storing contributor information THEN the system SHALL support detailed contributor profiles with bios and affiliations
3. WHEN handling territorial data THEN the system SHALL store region-specific pricing and availability information
4. WHEN managing submission preferences THEN the system SHALL store cover and text submission method preferences

### Requirement 5

**User Story:** As a quality assurance user, I want detailed logging and error reporting, so that I can troubleshoot LSI submission issues and track field mapping accuracy.

#### Acceptance Criteria

1. WHEN generating LSI files THEN the system SHALL log all field mappings and transformations
2. WHEN encountering validation errors THEN the system SHALL provide specific field-level error messages
3. WHEN processing fails THEN the system SHALL generate detailed error reports with suggested corrections
4. WHEN successful generation occurs THEN the system SHALL provide summary reports of populated vs empty fields

### Requirement 6

**User Story:** As the Nimble Books (host) website manager, I want to add this new functionality to the existing UI, codexes-factory-home-ui, as an optional checkbox or section under 10. Book Pipeline.

#### Acceptance Criteria

1. WHEN viewing the Book Pipeline page THEN LSI enhanced metadata SHALL be available as an option on the main form
2. WHEN the LSI enhanced metadata option is selected THEN a valid, complete LSI ACS spreadsheet row SHALL be delivered for each book built