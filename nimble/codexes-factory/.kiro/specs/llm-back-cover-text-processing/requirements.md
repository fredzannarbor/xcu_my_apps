# Requirements Document

## Introduction

The current back cover text processing system uses basic string substitution to replace variables like `{stream}`, `{title}`, `{author}`, etc. in the back cover text template. This approach is fragile and doesn't handle complex variable resolution or produce natural, flowing text. The system needs to be enhanced to use LLM-based processing that takes the template text with variables and returns clean, final text ready for placement on the book cover.

## Requirements

### Requirement 1

**User Story:** As a book publisher, I want the back cover text to be processed through an LLM so that all variable substitutions are resolved intelligently and the final text flows naturally.

#### Acceptance Criteria

1. WHEN the cover generation process encounters back cover text with variables THEN the system SHALL send the template text to an LLM for processing
2. WHEN the LLM processes the back cover text THEN it SHALL resolve all variable substitutions using the book metadata
3. WHEN the LLM returns the processed text THEN it SHALL be clean, final text with no remaining variables or placeholders
4. WHEN the processed text is returned THEN it SHALL be properly formatted for LaTeX placement on the cover

### Requirement 2

**User Story:** As a developer, I want the LLM back cover text processing to be integrated seamlessly into the existing cover generation pipeline without breaking current functionality.

#### Acceptance Criteria

1. WHEN the cover generator processes back cover text THEN it SHALL use the new LLM-based processor instead of basic string substitution
2. WHEN the LLM processing fails THEN the system SHALL fall back to the current string substitution method
3. WHEN the cover generation completes THEN all existing cover generation features SHALL continue to work as before
4. WHEN the system processes back cover text THEN it SHALL log the LLM processing steps for debugging

### Requirement 3

**User Story:** As a content creator, I want the LLM to have access to all relevant book metadata so that it can create contextually appropriate back cover text.

#### Acceptance Criteria

1. WHEN the LLM processes back cover text THEN it SHALL have access to title, author, imprint, subject/stream, description, quotes_per_book, and other relevant metadata
2. WHEN the LLM encounters a variable reference THEN it SHALL substitute it with the appropriate metadata value
3. WHEN metadata is missing for a variable THEN the LLM SHALL use intelligent fallbacks or omit the reference gracefully
4. WHEN the LLM generates text THEN it SHALL maintain the intended tone and style appropriate for the book's subject matter

### Requirement 4

**User Story:** As a system administrator, I want the LLM back cover text processing to be configurable and monitorable for cost and performance management.

#### Acceptance Criteria

1. WHEN the system processes back cover text THEN it SHALL use the configured LLM model and settings
2. WHEN LLM processing occurs THEN it SHALL be logged with request/response details for monitoring
3. WHEN the system encounters LLM errors THEN it SHALL retry with exponential backoff according to configuration
4. WHEN processing completes THEN it SHALL track token usage and costs for the back cover text generation

### Requirement 5

**User Story:** As a book designer, I want the back cover narrative to be less than 100 words. All back text must fit in a safe area in top part of page.
