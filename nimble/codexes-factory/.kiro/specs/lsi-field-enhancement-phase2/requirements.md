# Requirements Document

## Introduction

The LSI Field Enhancement Phase 2 builds upon the existing LSI ACS Generator implementation to address specific issues identified during acceptance testing. While Phase 1 successfully implemented the core field mapping system, validation framework, and configuration management, Phase 2 focuses on improving the integration of LLM-generated content, enhancing field completion visibility, and ensuring proper storage of completion data.

## Requirements

### Requirement 1

**User Story:** As a publisher using the codexes system, I want LLM-generated field completions to be properly stored in a consistent directory structure, so that I can easily access and review them alongside other book artifacts.

#### Acceptance Criteria

1. WHEN saving LLM completions THEN the system SHALL store them in a metadata/ directory parallel to covers/ and interiors/ directories
2. WHEN determining the output directory THEN the system SHALL first look for existing book directories by publisher_reference_id or ISBN
3. WHEN saving completions THEN the system SHALL create the directory structure if it doesn't exist
4. WHEN saving completions THEN the system SHALL use consistent file naming with timestamps and ISBN

### Requirement 2

**User Story:** As a publisher using the codexes system, I want LLM-generated field completions to be properly included in the final LSI CSV output, so that I don't need to manually add this information.

#### Acceptance Criteria

1. WHEN mapping fields to CSV THEN the system SHALL check for existing completions in the metadata.llm_completions dictionary
2. WHEN a field has a corresponding LLM completion THEN the system SHALL use that value in the CSV output
3. WHEN multiple LLM completions exist for a field THEN the system SHALL use a consistent priority order to select the appropriate value
4. WHEN using LLM completions THEN the system SHALL log the source of each field value for traceability

### Requirement 3

**User Story:** As a quality assurance user, I want detailed field completion reports, so that I can understand which fields are being completed by which strategy and identify any issues.

#### Acceptance Criteria

1. WHEN generating LSI CSV files THEN the system SHALL generate detailed field completion reports
2. WHEN creating field completion reports THEN the system SHALL include field name, strategy type, actual value, and source
3. WHEN creating field completion reports THEN the system SHALL support multiple output formats (CSV, HTML, JSON)
4. WHEN creating HTML reports THEN the system SHALL include statistics on field population rates and strategy usage
5. WHEN creating reports THEN the system SHALL highlight empty fields and potential issues

### Requirement 4

**User Story:** As a system administrator, I want the field completion reporting to be integrated with the book pipeline, so that reports are automatically generated during batch processing.

#### Acceptance Criteria

1. WHEN running the book pipeline THEN the system SHALL generate field completion reports for each book
2. WHEN generating reports THEN the system SHALL save them alongside the LSI CSV files
3. WHEN generating reports THEN the system SHALL maintain backward compatibility with existing reporting
4. WHEN generating reports THEN the system SHALL handle errors gracefully and continue processing