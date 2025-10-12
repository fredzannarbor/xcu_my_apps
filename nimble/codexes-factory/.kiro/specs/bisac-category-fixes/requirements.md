# Requirements Document

## Introduction

The BISAC category fields in the LSI CSV generation system are not working correctly. Currently, only one BISAC category field is being populated, and it contains a code instead of the full category name. The system needs to be fixed to properly populate all three BISAC category fields with full category names (not codes) using LLM assistance and validation against the current BISAC standards.

## Requirements

### Requirement 1

**User Story:** As a publisher, I want all three BISAC category fields to be populated with appropriate categories, so that my books are properly classified for distribution.

#### Acceptance Criteria

1. WHEN the LSI CSV is generated THEN all three BISAC Category fields (BISAC Category, BISAC Category 2, BISAC Category 3) SHALL be populated
2. WHEN a BISAC category is assigned THEN it SHALL contain the full category name without the code (e.g., "BUSINESS & ECONOMICS / General" not "BUS000000")
3. WHEN multiple BISAC categories are needed THEN they SHALL be distinct and relevant to the book content
4. IF fewer than three relevant categories exist THEN only the relevant categories SHALL be populated, leaving others empty

### Requirement 2

**User Story:** As a publisher, I want BISAC categories to be validated against current standards, so that my books meet distribution requirements.

#### Acceptance Criteria

1. WHEN BISAC categories are generated THEN they SHALL be validated against the current BISAC standards database
2. WHEN an invalid BISAC category is detected THEN the system SHALL use a fallback strategy with valid alternatives
3. WHEN BISAC categories are assigned THEN they SHALL use the most recent BISAC standards (2024)
4. IF a generated category is not found in the standards THEN the system SHALL log a warning and use the closest valid match

### Requirement 3

**User Story:** As a publisher, I want BISAC categories to be intelligently generated based on book content, so that categorization is accurate and relevant.

#### Acceptance Criteria

1. WHEN generating BISAC categories THEN the system SHALL use LLM assistance to analyze book metadata
2. WHEN the LLM generates categories THEN they SHALL be ranked by relevance to the book content
3. WHEN book metadata contains existing BISAC information THEN it SHALL be used as the primary category
4. IF the primary category is invalid THEN the system SHALL generate alternatives using LLM assistance

### Requirement 4

**User Story:** As a publisher, I want tranche configuration to override BISAC categories for specific book series, so that all books in a series (like PILSA) can be consistently categorized.

#### Acceptance Criteria

1. WHEN a tranche config specifies a BISAC category override THEN it SHALL be used as the primary category
2. WHEN tranche override is applied THEN the remaining categories SHALL be generated to complement the override
3. WHEN tranche override is "Self-Help / Journaling" THEN all PILSA books SHALL use this as their primary category
4. IF tranche override is invalid THEN the system SHALL log a warning and use the override anyway if it's a valid category name

### Requirement 5

**User Story:** As a publisher, I want BISAC categories to come from different top-level categories when possible, so that books have broader discoverability.

#### Acceptance Criteria

1. WHEN generating multiple BISAC categories THEN at least 2 categories SHOULD come from different top-level categories (e.g., BUS vs SEL vs COM)
2. WHEN selecting categories THEN the system SHALL prioritize diversity across top-level categories
3. WHEN only one top-level category is relevant THEN the system SHALL use the most specific subcategories within that top-level
4. IF diverse top-level categories cannot be found THEN the system SHALL log this and use the most relevant categories available

### Requirement 6

**User Story:** As a developer, I want the BISAC category system to have proper error handling and logging, so that issues can be diagnosed and resolved.

#### Acceptance Criteria

1. WHEN BISAC category generation fails THEN the system SHALL log detailed error information
2. WHEN fallback strategies are used THEN the system SHALL log the reason and chosen alternatives
3. WHEN validation fails THEN the system SHALL provide specific error messages with suggested corrections
4. IF all generation attempts fail THEN the system SHALL use safe fallback categories and log the failure