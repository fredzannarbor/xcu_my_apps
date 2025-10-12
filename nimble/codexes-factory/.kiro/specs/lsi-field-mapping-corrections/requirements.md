# Requirements Document

## Introduction

This specification addresses six specific field mapping corrections needed in the LSI CSV generation system. These corrections focus on proper tranche value precedence, data extraction from JSON metadata, series-aware descriptions, pricing field management, and file path handling to ensure accurate and compliant LSI CSV output.

## Requirements

### Requirement 1: Tranche Value Override Priority

**User Story:** As a publisher, I want tranche configuration values to override LLM-generated values (except for specific append cases), so that my publishing-specific settings take precedence over AI-generated content.

#### Acceptance Criteria

1. WHEN a field has both tranche configuration and LLM-generated values THEN the system SHALL use the tranche value as the final output
2. WHEN the field is "annotation_boilerplate" or similar append-type fields THEN the system SHALL append tranche values to LLM-generated content
3. WHEN a tranche value is explicitly set to empty/null THEN the system SHALL respect that override and not fall back to LLM values
4. WHEN no tranche value exists THEN the system SHALL use LLM-generated values as fallback

### Requirement 2: Thema Subject Extraction and Mapping

**User Story:** As a metadata manager, I want Thema subject codes extracted from JSON metadata and properly mapped to LSI columns, so that subject classification is accurate and complete.

#### Acceptance Criteria

1. WHEN JSON metadata contains "thema" field with array values THEN the system SHALL extract the first three values
2. WHEN thema values are extracted THEN the system SHALL map them to "Thema Subject 1", "Thema Subject 2", and "Thema Subject 3" columns respectively
3. WHEN fewer than 3 thema values exist THEN the system SHALL leave remaining Thema Subject columns empty
4. WHEN no thema values exist in JSON THEN the system SHALL leave all Thema Subject columns empty
5. WHEN thema values are malformed or invalid THEN the system SHALL log warnings and skip invalid entries

### Requirement 3: Age Range Extraction and Formatting

**User Story:** As a content categorizer, I want minimum and maximum age values extracted from JSON metadata and formatted as integers, so that age targeting is properly specified in the LSI submission.

#### Acceptance Criteria

1. WHEN JSON metadata contains "min_age" field THEN the system SHALL extract and convert it to integer format for "Min Age" column
2. WHEN JSON metadata contains "max_age" field THEN the system SHALL extract and convert it to integer format for "Max Age" column
3. WHEN age values are non-numeric THEN the system SHALL log warnings and leave age columns empty
4. WHEN age values are negative or unrealistic (>150) THEN the system SHALL validate and reject invalid values
5. WHEN no age values exist in JSON THEN the system SHALL leave age columns empty

### Requirement 4: Series-Aware Short Description

**User Story:** As a series publisher, I want short descriptions to reference the series name when applicable, so that readers understand the book's context within the series.

#### Acceptance Criteria

1. WHEN a book has a series name AND short description contains "This book" THEN the system SHALL replace it with "This book in the {series_name} series"
2. WHEN a book has no series name THEN the system SHALL leave "This book" unchanged
3. WHEN short description doesn't contain "This book" THEN the system SHALL leave the description unchanged
4. WHEN series name is empty or null THEN the system SHALL treat it as no series

### Requirement 5: Ingram Pricing Field Management

**User Story:** As an LSI administrator, I want specific Ingram pricing fields to remain blank, so that the CSV complies with current LSI requirements and avoids submission errors.

#### Acceptance Criteria

1. WHEN generating LSI CSV THEN the system SHALL ensure "US-Ingram-Only* Suggested List Price (mode 2)" is blank
2. WHEN generating LSI CSV THEN the system SHALL ensure "US-Ingram-Only* Wholesale Discount % (Mode 2)" is blank
3. WHEN generating LSI CSV THEN the system SHALL ensure "US - Ingram - GAP * Suggested List Price (mode 2)" is blank
4. WHEN generating LSI CSV THEN the system SHALL ensure "US - Ingram - GAP * Wholesale Discount % (Mode 2)" is blank
5. WHEN generating LSI CSV THEN the system SHALL ensure "SIBI - EDUC - US * Suggested List Price (mode 2)" is blank
6. WHEN generating LSI CSV THEN the system SHALL ensure "SIBI - EDUC - US * Wholesale Discount % (Mode 2)" is blank

### Requirement 6: File Path Tranche Compliance

**User Story:** As a file manager, I want LSI CSV file paths to honor tranche definitions, so that the correct file locations are specified for each publishing configuration.

#### Acceptance Criteria

1. WHEN tranche configuration specifies file path patterns THEN the system SHALL use those patterns for "Interior Path / Filename" and "Cover Path / Filename" columns
2. WHEN tranche defines custom path templates THEN the system SHALL apply book-specific variables (title, ISBN, etc.) to generate actual paths
3. WHEN no tranche file path is defined THEN the system SHALL use default path generation logic
4. WHEN file paths are generated THEN the system SHALL validate they follow LSI naming conventions
5. WHEN file paths contain invalid characters THEN the system SHALL sanitize them according to LSI requirements