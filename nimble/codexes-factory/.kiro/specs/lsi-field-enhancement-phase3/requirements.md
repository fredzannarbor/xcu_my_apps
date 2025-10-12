# Requirements Document

## Introduction

Phase 3 of the LSI Field Enhancement project builds upon previous phases to improve the management of ISBNs, series metadata, and field completion for Lightning Source Inc. (LSI) distribution. This phase focuses on creating a database for ISBN management, implementing series metadata functionality, and enhancing field completion for various LSI metadata fields.

## Requirements

### Requirement 1: ISBN Database Management

**User Story:** As a publisher, I want to manage my ISBN inventory efficiently, so that I can automatically assign ISBNs to new books and track their usage status.

#### Acceptance Criteria

1. WHEN a publisher uploads a Bowker spreadsheet THEN the system SHALL import all ISBNs owned by the publisher.
2. WHEN the system imports ISBNs THEN it SHALL identify which ISBNs are available (never publicly assigned).
3. WHEN a book requires an ISBN for LSI distribution THEN the system SHALL automatically pull the next available ISBN from the database.
4. WHEN an ISBN is assigned to a book THEN the system SHALL mark it as "privately assigned" in the database.
5. WHEN an ISBN is uploaded to LSI THEN the system SHALL mark it as "publicly assigned" in the database.
6. WHEN an ISBN is marked as "publicly assigned" THEN the system SHALL prevent it from being used for any other purpose.
7. WHEN a publisher requests to release a privately assigned ISBN THEN the system SHALL mark it as available again IF it has not yet been published.

### Requirement 2: LSI Series Metadata Management

**User Story:** As a publisher, I want to manage book series metadata for LSI distribution, so that I can maintain consistent series information and automatically assign series numbers.

#### Acceptance Criteria

1. WHEN a publisher creates a series THEN the system SHALL store the series name and generate a unique series ID.
2. WHEN a book is added to a series THEN the system SHALL assign it a sequence number within that series.
3. WHEN a user starts the Book Pipeline with a series name THEN the system SHALL automatically assign the appropriate series number.
4. WHEN a publisher has multiple series THEN the system SHALL maintain separate tracking for each series.
5. WHEN different publishers have series with the same name THEN the system SHALL treat them as separate series with different IDs.
6. WHEN a series is designated as multi-publisher THEN the system SHALL allow multiple publishers to contribute to it.
7. WHEN a series is not explicitly designated as multi-publisher THEN the system SHALL default it to single-publisher.
8. WHEN a user performs CRUD operations on series titles THEN the system SHALL maintain the integrity of the series without renumbering.

### Requirement 3: Enhanced Field Completion

**User Story:** As a publisher, I want improved field completion for LSI metadata, so that I can ensure accurate and consistent information across all required fields.

#### Acceptance Criteria

1. WHEN a user selects a series in the UI THEN the system SHALL allow selection from registered series or creation of a new one.
2. WHEN a title is assigned to a series THEN the system SHALL assign it a series ID number.
3. WHEN generating Annotation/Summary fields THEN the system SHALL:
   - Format content in simple HTML (max 4000 characters, no outbound links)
   - Include a dramatic hook in bold italic as the first paragraph
   - Include back_cover_text
   - Include paragraphed strings from the publisher's shared dictionary
4. WHEN generating BISAC Category fields THEN the system SHALL:
   - Use llm_completion to suggest_bisac_codes
   - Apply any user-specified BISAC category overrides for specific job types
5. WHEN generating Thema Subject fields THEN the system SHALL assign based on results of suggest_thema_codes.
6. WHEN generating Contributor info fields THEN the system SHALL assign based on results of extract_lsi_contributor_info.
7. WHEN generating Illustrations and Illustration Note fields THEN the system SHALL assign based on results of gemini_get_basic_info.
8. WHEN generating Table of Contents THEN the system SHALL assign based on results of create_simple_toc.
9. WHEN generating LSI CSV THEN the system SHALL leave specified fields blank (Reserved*, SIBI*, Stamped*, LSI Flexfield*, Review Quotes).