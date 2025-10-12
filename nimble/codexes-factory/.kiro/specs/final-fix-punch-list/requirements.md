# Requirements Document

## Introduction

This specification addresses critical fixes needed for the final book production pipeline to ensure proper cover generation, interior layout, and metadata accuracy. The fixes target UPC barcode placement, dotgrid positioning, ISBN formatting, subtitle length validation, and spine width calculations to meet publishing standards and distribution requirements.

## Requirements

### Requirement 1: UPC Barcode Generation and Placement

**User Story:** As a book publisher, I want UPC-A US style barcodes automatically generated and properly positioned on book covers, so that my books meet retail distribution standards and can be scanned at point of sale.

#### Acceptance Criteria

1. WHEN a book cover is generated THEN the system SHALL create a UPC-A US style barcode
2. WHEN placing the barcode THEN the system SHALL position it in the same location as currently implemented
3. WHEN positioning the barcode THEN the system SHALL maintain adequate safety spaces around the barcode to prevent printing issues

### Requirement 2: Interior Layout Dotgrid Positioning

**User Story:** As a book designer, I want the dotgrid image positioned with proper spacing from headers and footers, so that the interior layout maintains professional typography standards and readability.

#### Acceptance Criteria

1. WHEN generating interior pages THEN the system SHALL position the dotgrid image lower on the page
2. WHEN positioning the dotgrid THEN the system SHALL leave at least 0.5 inches between the bottom of the header and the beginning of the dotgrid
3. WHEN positioning the dotgrid THEN the system SHALL ensure adequate space between the dotgrid and footer elements

### Requirement 3: ISBN Formatting on Copyright Page

**User Story:** As a publisher, I want the ISBN displayed in proper hyphenated 13-digit format on the copyright page, so that the book meets industry standards and is easily identifiable by retailers and libraries.

#### Acceptance Criteria

1. WHEN generating the copyright page THEN the system SHALL display the ISBN in properly hyphenated full 13-digit format
2. WHEN formatting the ISBN THEN the system SHALL include the check digit
3. WHEN displaying the ISBN THEN the system SHALL follow standard ISBN hyphenation rules

### Requirement 4: Subtitle Length Validation and LLM Replacement

**User Story:** As a publisher of xynapse_traces titles, I want subtitles automatically validated and regenerated when too long, so that my books meet distribution platform character limits and maintain consistent branding.

#### Acceptance Criteria

1. WHEN processing xynapse_traces titles THEN the system SHALL validate subtitle length against a 38 character hard limit
2. IF the subtitle exceeds 38 characters THEN the system SHALL replace it with a new subtitle
3. WHEN generating a replacement subtitle THEN the system SHALL use nimble-llm-caller to create the new subtitle
4. WHEN creating the replacement subtitle THEN the system SHALL ensure it does not exceed the 38 character limit

### Requirement 5: Spine Width Calculation and Validation

**User Story:** As a book production manager, I want accurate spine width calculations based on page specifications, so that covers are properly sized and books can be printed without binding issues.

#### Acceptance Criteria

1. WHEN calculating spine width THEN the system SHALL use the logic from metadata2lsicoverspecs.py
2. WHEN looking up spine width THEN the system SHALL reference resources/SpineWidthLookup.xlsx
3. WHEN determining page specifications THEN the system SHALL use "Standard perfect 70" as the page type for these books
4. WHEN spine width is calculated THEN the system SHALL provide this value to both metadata and cover creator components
5. WHEN spine width calculation fails THEN the system SHALL log an error and skip producing the cover.