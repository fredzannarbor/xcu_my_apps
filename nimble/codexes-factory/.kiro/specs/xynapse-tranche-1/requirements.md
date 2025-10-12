# Requirements Document

## Introduction

The Xynapse Tranche 1 project addresses 15 specific field completion and validation issues to ship a complete batch of 12 xynapse traces books with fully optimized LSI metadata. Each requirement corresponds to a specific item in the punch list that must be resolved for successful LSI distribution.

## Requirements

### Requirement 1: Account and Configuration Fields

**User Story:** As a publisher, I want correct Lightning Source account information and proper field exclusions, so that LSI files are properly configured for our account.

#### Acceptance Criteria

1. WHEN generating LSI files THEN the system SHALL set Lightning Source Account # to "6024045"
2. WHEN creating CSV output THEN the system SHALL exclude "Metadata Contact Dictionary" field from CSV output
3. WHEN processing Parent ISBN field THEN the system SHALL leave it empty for this tranche
4. WHEN validating account fields THEN the system SHALL ensure Lightning Source Account # is always populated

### Requirement 2: ISBN Management and Database

**User Story:** As a production manager, I want proper ISBN assignment from a validated database, so that each book has a unique, valid ISBN.

#### Acceptance Criteria

1. WHEN initializing the system THEN the system SHALL load ISBN database with real data
2. WHEN processing each book THEN the system SHALL assign a unique ISBN from the valid database
3. WHEN assigning ISBNs THEN the system SHALL mark assigned ISBNs as unavailable
4. WHEN ISBN assignment fails THEN the system SHALL provide clear error messages

### Requirement 3: Tranche Configuration Management

**User Story:** As a configuration manager, I want tranche-level configuration options, so that consistent settings can be applied to all books in a batch.

#### Acceptance Criteria

1. WHEN processing a tranche THEN the system SHALL apply tranche-level configuration to all books
2. WHEN tranche config is set THEN the system SHALL override individual book settings with tranche settings
3. WHEN validating configuration THEN the system SHALL ensure tranche settings are consistent across all books
4. WHEN configuration conflicts occur THEN the system SHALL prioritize tranche-level settings

### Requirement 4: Field Validation Against Valid Lists

**User Story:** As a quality assurance specialist, I want validation against LSI valid value lists, so that all field values are accepted by LSI systems.

#### Acceptance Criteria

1. WHEN validating rendition booktype THEN the system SHALL check against lsi_valid_rendition_booktypes.txt
2. WHEN validating Contributor Role One THEN the system SHALL check against lsi_valid_contributor_codes.csv
3. WHEN validation fails THEN the system SHALL provide specific error messages with valid options
4. WHEN valid values are updated THEN the system SHALL use the most current validation lists

### Requirement 5: Smart Publication Date Assignment

**User Story:** As a scheduling coordinator, I want intelligent publication date assignment, so that books are distributed evenly across available publication dates.

#### Acceptance Criteria

1. WHEN processing publication dates THEN the system SHALL extract month/year from schedule.json
2. WHEN assigning dates THEN the system SHALL spread all titles across Tuesdays in the target month
3. WHEN multiple books exist THEN the system SHALL distribute them evenly across available Tuesdays
4. WHEN date assignment completes THEN the system SHALL ensure no date conflicts exist

### Requirement 6: Enhanced Content Generation

**User Story:** As a content manager, I want enhanced annotation/summary generation, so that book descriptions are comprehensive and consistent.

#### Acceptance Criteria

1. WHEN generating annotations THEN the system SHALL combine LLM completion results with boilerplate strings
2. WHEN using boilerplate THEN the system SHALL source strings from configuration dictionary
3. WHEN joining content THEN the system SHALL ensure proper formatting and flow
4. WHEN content exceeds limits THEN the system SHALL truncate appropriately while maintaining readability

### Requirement 7: BISAC Subject Handling

**User Story:** As a metadata specialist, I want proper BISAC subject formatting and override capability, so that categorization is accurate and consistent.

#### Acceptance Criteria

1. WHEN setting BISAC Subject THEN the system SHALL use category name only (no code)
2. WHEN setting BISAC Subject 2 and 3 THEN the system SHALL follow the same format as BISAC Subject
3. WHEN tranche config specifies required BISAC Subject THEN the system SHALL override LLM completion
4. WHEN BISAC validation occurs THEN the system SHALL ensure all subjects are valid category names

### Requirement 8: Content Length Validation

**User Story:** As a format compliance manager, I want proper content length validation, so that all text fields meet LSI requirements.

#### Acceptance Criteria

1. WHEN validating short description THEN the system SHALL ensure it is no more than 350 bytes
2. WHEN content exceeds limits THEN the system SHALL truncate while preserving meaning
3. WHEN truncation occurs THEN the system SHALL log the original and truncated content
4. WHEN validation completes THEN the system SHALL report any length violations

### Requirement 9: Thema Subject Correction

**User Story:** As a subject classification specialist, I want proper Thema subject handling, so that subject codes are complete and accurate.

#### Acceptance Criteria

1. WHEN processing Thema subjects THEN the system SHALL use full multi-letter strings instead of single letters
2. WHEN validating Thema codes THEN the system SHALL ensure codes are complete and valid
3. WHEN Thema subjects are truncated THEN the system SHALL restore full codes
4. WHEN multiple Thema subjects exist THEN the system SHALL handle all with consistent formatting

### Requirement 10: GC Market Pricing

**User Story:** As a pricing manager, I want consistent GC market pricing, so that country-specific markets have appropriate pricing.

#### Acceptance Criteria

1. WHEN setting GC market prices THEN the system SHALL use the same price as US List Price
2. WHEN processing multiple GC markets THEN the system SHALL apply consistent pricing across all
3. WHEN validating GC pricing THEN the system SHALL ensure all GC markets have identical pricing
4. WHEN pricing updates occur THEN the system SHALL maintain consistency across GC markets