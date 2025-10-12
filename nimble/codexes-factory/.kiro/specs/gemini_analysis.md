Here's a single, complete, accurate, lossless, and more concise set of Kiro specifications, followed by a document identifying issues, problems, potential conflicts, and regressions.

---

# Consolidated Codexes Factory Specifications

## Overview

This document consolidates the requirements, design, and tasks for various enhancements and bug fixes implemented across multiple phases of the Codexes Factory, particularly focusing on the LSI (Lightning Source Inc.) CSV generation, ISBN and Series management, Streamlit UI improvements, and core book production fixes. The overarching goal has been to automate, validate, and refine the book production pipeline to ensure high-quality, compliant outputs for distribution.

The system has evolved through several phases, progressively addressing field population rates, data accuracy, user interface usability, and critical production quality issues.

---

## 1. Requirements

### 1.1 LSI CSV Generation & Field Enhancements

**User Stories & Acceptance Criteria:**

*   **As a publisher using the Codexes system, I want the LSI ACS generator to support all available LSI fields, so that I can create complete submission files without manual editing.**
    *   WHEN the LSI ACS generator processes metadata THEN it SHALL map all 100+ LSI template fields to appropriate values. [lsi-field-enhancement/requirements.md:1.1]
    *   WHEN a field has no corresponding metadata value THEN the system SHALL use appropriate default values or leave empty based on LSI requirements. [lsi-field-enhancement/requirements.md:1.2]
    *   WHEN generating the CSV THEN the system SHALL maintain the exact field order and formatting required by LSI. [lsi-field-enhancement/requirements.md:1.3]
    *   WHEN processing contributor information THEN the system SHALL support multiple contributors with roles, bios, affiliations, and locations. [lsi-field-enhancement/requirements.md:1.4]
*   **As a publisher with different distribution strategies, I want configurable LSI field mappings, so that I can customize output for different imprints, territories, and pricing models.**
    *   WHEN configuring the generator THEN the system SHALL allow custom field mapping overrides. [lsi-field-enhancement/requirements.md:2.1]
    *   WHEN setting up different imprints THEN the system SHALL support imprint-specific default values. [lsi-field-enhancement/requirements.md:2.2]
    *   WHEN handling territorial rights THEN the system SHALL support region-specific pricing and discount configurations. [lsi-field-enhancement/requirements.md:2.3]
    *   WHEN processing series information THEN the system SHALL automatically populate series-related fields from metadata. [lsi-field-enhancement/requirements.md:2.4]
*   **As a publisher using the Codexes system, I want LLM-generated field completions to be properly stored in a consistent directory structure, so that I can easily access and review them alongside other book artifacts.**
    *   WHEN saving LLM completions THEN the system SHALL store them in a `metadata/` directory parallel to `covers/` and `interiors/` directories. [lsi-field-enhancement-phase2/requirements.md:1.1]
    *   WHEN determining the output directory THEN the system SHALL first look for existing book directories by `publisher_reference_id` or `ISBN`. [lsi-field-enhancement-phase2/requirements.md:1.2]
    *   WHEN saving completions THEN the system SHALL create the directory structure if it doesn't exist. [lsi-field-enhancement-phase2/requirements.md:1.3]
    *   WHEN saving completions THEN the system SHALL use consistent file naming with timestamps and ISBN. [lsi-field-enhancement-phase2/requirements.md:1.4]
*   **As a publisher using the Codexes system, I want LLM-generated field completions to be properly included in the final LSI CSV output, so that I don't need to manually add this information.**
    *   WHEN mapping fields to CSV THEN the system SHALL check for existing completions in the `metadata.llm_completions` dictionary. [lsi-field-enhancement-phase2/requirements.md:2.1]
    *   WHEN a field has a corresponding LLM completion THEN the system SHALL use that value in the CSV output. [lsi-field-enhancement-phase2/requirements.md:2.2]
    *   WHEN multiple LLM completions exist for a field THEN the system SHALL use a consistent priority order to select the appropriate value. [lsi-field-enhancement-phase2/requirements.md:2.3]
    *   WHEN using LLM completions THEN the system SHALL log the source of each field value for traceability. [lsi-field-enhancement-phase2/requirements.md:2.4]
*   **As a publisher, I need 100% field population with valid fields, including null valids.** [lsi-field-enhancement-phase4/requirements.md:1]
*   **As a publisher, I want improved field completion for LSI metadata, so that I can ensure accurate and consistent information across all required fields.**
    *   WHEN generating Annotation/Summary fields THEN the system SHALL:
        *   Format content in simple HTML (max 4000 characters, no outbound links). [lsi-field-enhancement-phase3/requirements.md:3.3]
        *   Include a dramatic hook in bold italic as the first paragraph. [lsi-field-enhancement-phase3/requirements.md:3.3]
        *   Include back_cover_text. [lsi-field-enhancement-phase3/requirements.md:3.3]
        *   Include paragraphed strings from the publisher's shared dictionary. [lsi-field-enhancement-phase3/requirements.md:3.3]
    *   WHEN generating Contributor info fields THEN the system SHALL assign based on results of `extract_lsi_contributor_info`. [lsi-field-enhancement-phase3/requirements.md:3.6]
    *   WHEN generating Illustrations and Illustration Note fields THEN the system SHALL assign based on results of `gemini_get_basic_info`. [lsi-field-enhancement-phase3/requirements.md:3.7]
    *   WHEN generating Table of Contents THEN the system SHALL assign based on results of `create_simple_toc`. [lsi-field-enhancement-phase3/requirements.md:3.8]
    *   WHEN generating LSI CSV THEN the system SHALL leave specified fields blank (Reserved\*, SIBI\*, Stamped\*, LSI Flexfield\*, Review Quotes). [lsi-field-enhancement-phase3/requirements.md:3.9]
*   **As a publisher, I want the book description to clearly identify this as a pilsa book, so that readers understand the unique nature and purpose of the publication.**
    *   WHEN descriptive content is generated THEN it SHALL clearly identify the book as a pilsa or transcriptive meditation handbook. [book-production-fixes/requirements.md:10.1]
    *   WHEN book descriptions are created THEN they SHALL mention the 90 quotations and 90 facing pages for journaling. [book-production-fixes/requirements.md:10.2]
    *   WHEN back cover text is generated THEN it SHALL include the pilsa book designation. [book-production-fixes/requirements.md:10.3]
    *   WHEN marketing copy is written THEN it SHALL emphasize the unique meditative and journaling aspects. [book-production-fixes/requirements.md:10.4]
    *   WHEN book metadata is created THEN it SHALL consistently reference the pilsa format. [book-production-fixes/requirements.md:10.5]

### 1.2 Validation & Error Handling

**User Stories & Acceptance Criteria:**

*   **As a system administrator, I want comprehensive validation of LSI field data, so that generated files meet LSI submission requirements and reduce rejection rates.**
    *   WHEN validating ISBN data THEN the system SHALL verify format and check-digit validity. [lsi-field-enhancement/requirements.md:3.1]
    *   WHEN processing pricing information THEN the system SHALL validate currency formats and discount percentages. [lsi-field-enhancement/requirements.md:3.2]
    *   WHEN handling dates THEN the system SHALL ensure proper date formatting for publication and street dates. [lsi-field-enhancement/requirements.md:3.3]
    *   WHEN validating BISAC codes THEN the system SHALL verify against current BISAC standards. [lsi-field-enhancement/requirements.md:3.4]
    *   WHEN checking physical specifications THEN the system SHALL validate trim sizes and page counts. [lsi-field-enhancement/requirements.md:3.5]
    *   WHEN validating digital files THEN interior and cover files SHALL be available in ftp2lsi staging area with names matching `ISBN_interior.pdf` and `ISBN_cover.pdf`. [lsi-field-enhancement/requirements.md:3.6]
    *   WHEN processing PDF files THEN interior and cover files SHALL pass verification as PDF X-1a format. [lsi-field-enhancement/requirements.md:3.7]
    *   WHEN validating interior specifications THEN interior PDF SHALL match page count and trim sizes provided in LSI spreadsheet. [lsi-field-enhancement/requirements.md:3.8]
*   **As a quality assurance user, I want detailed logging and error reporting, so that I can troubleshoot LSI submission issues and track field mapping accuracy.**
    *   WHEN generating LSI files THEN the system SHALL log all field mappings and transformations. [lsi-field-enhancement/requirements.md:5.1]
    *   WHEN encountering validation errors THEN the system SHALL provide specific field-level error messages. [lsi-field-enhancement/requirements.md:5.2]
    *   WHEN processing fails THEN the system SHALL generate detailed error reports with suggested corrections. [lsi-field-enhancement/requirements.md:5.3]
    *   WHEN successful generation occurs THEN the system SHALL provide summary reports of populated vs empty fields. [lsi-field-enhancement/requirements.md:5.4]
*   **As a developer, I want comprehensive error handling and logging, so that I can quickly diagnose and fix issues in the LSI generation process.**
    *   WHEN errors occur THEN the system SHALL log detailed context and stack traces. [lsi-csv-bug-fixes/requirements.md:6.1]
    *   WHEN processing books THEN the system SHALL provide progress indicators and status updates. [lsi-csv-bug-fixes/requirements.md:6.2]
    *   WHEN LLM calls fail THEN the system SHALL implement proper retry logic with backoff. [lsi-csv-bug-fixes/requirements.md:6.3]
    *   WHEN validation fails THEN the system SHALL log specific field issues and suggested fixes. [lsi-csv-bug-fixes/requirements.md:6.4]
    *   WHEN debugging is needed THEN the system SHALL provide verbose logging options. [lsi-csv-bug-fixes/requirements.md:6.5]
*   **As a quality assurance manager, I want comprehensive validation and error handling, so that the system maintains data integrity and provides clear feedback on issues.**
    *   WHEN invalid data is entered THEN the system SHALL reject it with specific error messages. [isbn-schedule-assignment/requirements.md:11.1]
    *   WHEN ISBN formatting is required THEN the system SHALL generate valid ISBN-13 numbers with correct check digits. [isbn-schedule-assignment/requirements.md:11.2]
    *   WHEN system errors occur THEN the system SHALL log detailed information for debugging. [isbn-schedule-assignment/requirements.md:11.3]
    *   WHEN data conflicts arise THEN the system SHALL prevent corruption and guide users to resolution. [isbn-schedule-assignment/requirements.md:11.4]
*   **As a content manager, I want accurate reporting of prompt success and quote retrieval statistics, so that I can monitor the effectiveness of the content generation process.**
    *   WHEN 90 quotes are successfully retrieved THEN the report SHALL accurately reflect this count, not show 0. [book-production-fixes/requirements.md:3.1]
    *   WHEN prompts execute successfully THEN the success rate SHALL be accurately calculated and reported. [book-production-fixes/requirements.md:3.2]
    *   WHEN quote retrieval completes THEN the system SHALL provide detailed statistics on success/failure rates. [book-production-fixes/requirements.md:3.3]
    *   WHEN reporting is generated THEN it SHALL align with actual test results and pipeline execution. [book-production-fixes/requirements.md:3.4]
    *   WHEN multiple prompts are processed THEN each prompt's individual success rate SHALL be tracked and reported. [book-production-fixes/requirements.md:3.5]
*   **As a developer, I want comprehensive error handling and logging for quote verification and field completion failures, so that I can diagnose and fix issues quickly.**
    *   WHEN quote verification fails THEN the system SHALL log detailed error information including the response received. [book-production-fixes/requirements.md:4.1]
    *   WHEN the verifier model returns invalid data THEN the system SHALL handle the error gracefully and continue processing. [book-production-fixes/requirements.md:4.2]
    *   WHEN field completion fails due to missing methods THEN the system SHALL provide clear error messages and fallback behavior. [book-production-fixes/requirements.md:4.3]
    *   WHEN validation reports 0 fields checked THEN the system SHALL investigate and report why no fields were processed. [book-production-fixes/requirements.md:4.4]
    *   WHEN runtime errors occur THEN they SHALL be logged with sufficient context for debugging and resolution. [book-production-fixes/requirements.md:4.5]

### 1.3 Pricing & Discount Management

**User Stories & Acceptance Criteria:**

*   **As a Lightning Source user, I want all prices to be decimal numbers without currency symbols, so that the CSV can be properly processed by LSI systems.**
    *   WHEN generating any price field THEN the system SHALL output decimal numbers with exactly 2 decimal places. [lsi-pricing-fixes/requirements.md:1.1]
    *   WHEN generating any price field THEN the system SHALL NOT include currency symbols ($, £, €, etc.). [lsi-pricing-fixes/requirements.md:1.2]
    *   WHEN generating US Suggested List Price THEN the output SHALL be format "19.95" not "$19.95". [lsi-pricing-fixes/requirements.md:1.3]
    *   WHEN generating UK Suggested List Price THEN the output SHALL be format "19.99" not "£19.99". [lsi-pricing-fixes/requirements.md:1.4]
    *   WHEN generating any territorial price THEN the output SHALL be numeric only. [lsi-pricing-fixes/requirements.md:1.5]
*   **As a publisher, I want EU, CA, and AU prices to be automatically calculated from the US base price, so that I have consistent multi-territorial pricing.**
    *   WHEN US Suggested List Price is provided THEN the system SHALL calculate EU Suggested List Price using current exchange rates. [lsi-pricing-fixes/requirements.md:2.1]
    *   WHEN US Suggested List Price is provided THEN the system SHALL calculate CA Suggested List Price using current exchange rates. [lsi-pricing-fixes/requirements.md:2.2]
    *   WHEN US Suggested List Price is provided THEN the system SHALL calculate AU Suggested List Price using current exchange rates. [lsi-pricing-fixes/requirements.md:2.3]
    *   WHEN calculating territorial prices THEN the system SHALL use cached exchange rates with fallback defaults. [lsi-pricing-fixes/requirements.md:2.4]
    *   WHEN territorial prices are calculated THEN they SHALL be formatted as decimal numbers without currency symbols. [lsi-pricing-fixes/requirements.md:2.5]
*   **As a Lightning Source user, I want GC and other specialty market prices to equal the US list price when not specifically set, so that pricing is consistent across all markets.**
    *   WHEN GC Suggested List Price is not specifically configured THEN it SHALL equal the US Suggested List Price. [lsi-pricing-fixes/requirements.md:3.1]
    *   WHEN USBR1 Suggested List Price is not configured THEN it SHALL equal the US Suggested List Price. [lsi-pricing-fixes/requirements.md:3.2]
    *   WHEN USDE1 Suggested List Price is not configured THEN it SHALL equal the US Suggested List Price. [lsi-pricing-fixes/requirements.md:3.3]
    *   WHEN any specialty market price is not configured THEN it SHALL default to the US Suggested List Price. [lsi-pricing-fixes/requirements.md:3.4]
    *   WHEN specialty market prices are set THEN they SHALL be formatted as decimal numbers without currency symbols. [lsi-pricing-fixes/requirements.md:3.5]
*   **As a publisher, I want wholesale discounts to be consistently applied across all markets, so that my distribution terms are uniform.**
    *   WHEN a wholesale discount is configured for US market THEN it SHALL be applied to all other markets unless specifically overridden. [lsi-pricing-fixes/requirements.md:4.1]
    *   WHEN no wholesale discount is specified for a market THEN it SHALL use the default wholesale discount percentage. [lsi-pricing-fixes/requirements.md:4.2]
    *   WHEN wholesale discounts are output THEN they SHALL be integer percentages without the % symbol. [lsi-pricing-fixes/requirements.md:4.3]
    *   WHEN wholesale discount is 40% THEN the output SHALL be "40" not "40%". [lsi-pricing-fixes/requirements.md:4.4]
    *   WHEN wholesale discounts are calculated THEN they SHALL be consistent across all territorial markets. [lsi-pricing-fixes/requirements.md:4.5]
*   **As an LSI administrator, I want specific Ingram pricing fields to remain blank, so that the CSV complies with current LSI requirements and avoids submission errors.**
    *   WHEN generating LSI CSV THEN the system SHALL ensure "US-Ingram-Only\* Suggested List Price (mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.1]
    *   WHEN generating LSI CSV THEN the system SHALL ensure "US-Ingram-Only\* Wholesale Discount % (Mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.2]
    *   WHEN generating LSI CSV THEN the system SHALL ensure "US - Ingram - GAP \* Suggested List Price (mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.3]
    *   WHEN generating LSI CSV THEN the system SHALL ensure "US - Ingram - GAP \* Wholesale Discount % (Mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.4]
    *   WHEN generating LSI CSV THEN the system SHALL ensure "SIBI - EDUC - US \* Suggested List Price (mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.5]
    *   WHEN generating LSI CSV THEN the system SHALL ensure "SIBI - EDUC - US \* Wholesale Discount % (Mode 2)" is blank. [lsi-field-mapping-corrections/requirements.md:5.6]
*   **As a pricing manager, I want consistent GC market pricing, so that country-specific markets have appropriate pricing.**
    *   WHEN setting GC market prices THEN the system SHALL use the same price as US List Price. [xynapse-tranche-1/requirements.md:10.1]
    *   WHEN processing multiple GC markets THEN the system SHALL apply consistent pricing across all. [xynapse-tranche-1/requirements.md:10.2]
    *   WHEN validating GC pricing THEN the system SHALL ensure all GC markets have identical pricing. [xynapse-tranche-1/requirements.md:10.3]
    *   WHEN pricing updates occur THEN the system SHALL maintain consistency across GC markets. [xynapse-tranche-1/requirements.md:10.4]

### 1.4 ISBN Management

**User Stories & Acceptance Criteria:**

*   **As a publisher, I want to manage my ISBN inventory efficiently, so that I can automatically assign ISBNs to new books and track their usage status.**
    *   WHEN a publisher uploads a Bowker spreadsheet THEN the system SHALL import all ISBNs owned by the publisher. [lsi-field-enhancement-phase3/requirements.md:1.1]
    *   WHEN the system imports ISBNs THEN it SHALL identify which ISBNs are available (never publicly assigned). [lsi-field-enhancement-phase3/requirements.md:1.2]
    *   WHEN a book requires an ISBN for LSI distribution THEN the system SHALL automatically pull the next available ISBN from the database. [lsi-field-enhancement-phase3/requirements.md:1.3]
    *   WHEN an ISBN is assigned to a book THEN the system SHALL mark it as "privately assigned" in the database. [lsi-field-enhancement-phase3/requirements.md:1.4]
    *   WHEN an ISBN is uploaded to LSI THEN the system SHALL mark it as "publicly assigned" in the database. [lsi-field-enhancement-phase3/requirements.md:1.5]
    *   WHEN an ISBN is marked as "publicly assigned" THEN the system SHALL prevent it from being used for any other purpose. [lsi-field-enhancement-phase3/requirements.md:1.6]
    *   WHEN a publisher requests to release a privately assigned ISBN THEN the system SHALL mark it as available again IF it has not yet been published. [lsi-field-enhancement-phase3/requirements.md:1.7]
*   **As a production manager, I want proper ISBN assignment from a validated database, so that each book has a unique, valid ISBN.**
    *   WHEN initializing the system THEN the system SHALL load ISBN database with real data. [xynapse-tranche-1/requirements.md:2.1]
    *   WHEN processing each book THEN the system SHALL assign a unique ISBN from the valid database. [xynapse-tranche-1/requirements.md:2.2]
    *   WHEN assigning ISBNs THEN the system SHALL mark assigned ISBNs as unavailable. [xynapse-tranche-1/requirements.md:2.3]
    *   WHEN ISBN assignment fails THEN the system SHALL provide clear error messages. [xynapse-tranche-1/requirements.md:2.4]
*   **As a publisher, I want to manage ISBN blocks and ranges, so that I can efficiently allocate ISBNs from my registered blocks to upcoming book publications.**
    *   WHEN I add a new ISBN block THEN the system SHALL store the prefix, publisher code, imprint code, start number, end number, and total count. [isbn-schedule-assignment/requirements.md:1.1]
    *   WHEN I view ISBN blocks THEN the system SHALL display utilization statistics including used, reserved, and available ISBNs. [isbn-schedule-assignment/requirements.md:1.2]
    *   WHEN I add an ISBN block with invalid parameters THEN the system SHALL reject the block and provide clear error messages. [isbn-schedule-assignment/requirements.md:1.3]
    *   IF an ISBN block overlaps with existing blocks THEN the system SHALL warn about potential conflicts. [isbn-schedule-assignment/requirements.md:1.4]
*   **As a production manager, I want to schedule ISBN assignments for upcoming books, so that I can plan publication schedules and ensure ISBNs are available when needed.**
    *   WHEN I schedule an ISBN assignment THEN the system SHALL automatically assign the next available ISBN from appropriate blocks. [isbn-schedule-assignment/requirements.md:2.1]
    *   WHEN I schedule an assignment THEN the system SHALL store book title, book ID, scheduled date, imprint, publisher, format, priority, and notes. [isbn-schedule-assignment/requirements.md:2.2]
    *   WHEN no ISBNs are available THEN the system SHALL reject the assignment and notify me of the shortage. [isbn-schedule-assignment/requirements.md:2.3]
    *   WHEN I schedule an assignment THEN the system SHALL update block utilization counts automatically. [isbn-schedule-assignment/requirements.md:2.4]
    *   IF I specify an imprint or publisher THEN the system SHALL prioritize matching ISBN blocks. [isbn-schedule-assignment/requirements.md:2.5]
*   **As a production coordinator, I want to view and manage scheduled ISBN assignments, so that I can track upcoming publications and make adjustments as needed.**
    *   WHEN I view assignments THEN the system SHALL display ISBN, title, book ID, scheduled date, status, and other metadata. [isbn-schedule-assignment/requirements.md:3.1]
    *   WHEN I filter assignments by status THEN the system SHALL show only assignments matching the selected status. [isbn-schedule-assignment/requirements.md:3.2]
    *   WHEN I filter assignments by date range THEN the system SHALL show only assignments within the specified dates. [isbn-schedule-assignment/requirements.md:3.3]
    *   WHEN I search assignments THEN the system SHALL find matches in title, ISBN, or book ID fields. [isbn-schedule-assignment/requirements.md:3.4]
    *   WHEN I select an assignment THEN the system SHALL allow me to assign, reserve, edit, or view details. [isbn-schedule-assignment/requirements.md:3.5]
*   **As a production manager, I want to assign ISBNs immediately when books are ready for publication, so that I can move books from scheduled to active status.**
    *   WHEN I assign an ISBN THEN the system SHALL change status from scheduled to assigned. [isbn-schedule-assignment/requirements.md:4.1]
    *   WHEN I assign an ISBN THEN the system SHALL record the assignment date and time. [isbn-schedule-assignment/requirements.md:4.2]
    *   WHEN I try to assign a non-existent ISBN THEN the system SHALL reject the operation with an error message. [isbn-schedule-assignment/requirements.md:4.3]
    *   WHEN I assign an ISBN THEN the system SHALL update all related reports and statistics. [isbn-schedule-assignment/requirements.md:4.4]
*   **As a publisher, I want to reserve ISBNs for special projects, so that I can prevent them from being automatically assigned to regular publications.**
    *   WHEN I reserve an ISBN THEN the system SHALL change its status to reserved. [isbn-schedule-assignment/requirements.md:5.1]
    *   WHEN I reserve an ISBN THEN the system SHALL require and store a reservation reason. [isbn-schedule-assignment/requirements.md:5.2]
    *   WHEN I reserve an ISBN THEN the system SHALL exclude it from automatic assignment pools. [isbn-schedule-assignment/requirements.md:5.3]
    *   WHEN I view reserved ISBNs THEN the system SHALL display the reservation reason and date. [isbn-schedule-assignment/requirements.md:5.4]
*   **As a production manager, I want to update existing ISBN assignments, so that I can correct information or adjust schedules as publication plans change.**
    *   WHEN I update an assignment THEN the system SHALL allow changes to title, book ID, scheduled date, priority, and notes. [isbn-schedule-assignment/requirements.md:6.1]
    *   WHEN I update an assignment THEN the system SHALL validate all changes before saving. [isbn-schedule-assignment/requirements.md:6.2]
    *   WHEN I try to update a non-existent assignment THEN the system SHALL reject the operation with an error message. [isbn-schedule-assignment/requirements.md:6.3]
    *   WHEN I update an assignment THEN the system SHALL maintain an audit trail of changes. [isbn-schedule-assignment/requirements.md:6.4]
*   **As a publisher, I want to generate comprehensive reports on ISBN usage and availability, so that I can make informed decisions about ordering new ISBN blocks.**
    *   WHEN I generate an availability report THEN the system SHALL show total, used, reserved, and available ISBNs. [isbn-schedule-assignment/requirements.md:7.1]
    *   WHEN I generate a report THEN the system SHALL display assignments grouped by status. [isbn-schedule-assignment/requirements.md:7.2]
    *   WHEN I generate a report THEN the system SHALL show block utilization percentages. [isbn-schedule-assignment/requirements.md:7.3]
    *   WHEN I generate a report THEN the system SHALL provide export options in JSON and CSV formats. [isbn-schedule-assignment/requirements.md:7.4]
    *   WHEN I view upcoming assignments THEN the system SHALL show books scheduled within a specified timeframe. [isbn-schedule-assignment/requirements.md:7.5]
*   **As a production coordinator, I want to perform bulk operations on ISBN assignments, so that I can efficiently manage large publication schedules.**
    *   WHEN I upload a CSV file THEN the system SHALL validate the format and required columns. [isbn-schedule-assignment/requirements.md:8.1]
    *   WHEN I process bulk assignments THEN the system SHALL schedule ISBNs for all valid entries. [isbn-schedule-assignment/requirements.md:8.2]
    *   WHEN bulk processing encounters errors THEN the system SHALL report which entries failed and why. [isbn-schedule-assignment/requirements.md:8.3]
    *   WHEN I perform bulk status updates THEN the system SHALL allow assigning all ISBNs scheduled for a specific date. [isbn-schedule-assignment/requirements.md:8.4]
    *   WHEN I perform bulk operations THEN the system SHALL provide progress feedback and final summary. [isbn-schedule-assignment/requirements.md:8.5]
*   **As a system administrator, I want the ISBN schedule to persist across sessions, so that all assignment data is safely stored and recoverable.**
    *   WHEN I make changes to assignments or blocks THEN the system SHALL automatically save to persistent storage. [isbn-schedule-assignment/requirements.md:9.1]
    *   WHEN the system restarts THEN the system SHALL load all existing assignments and blocks. [isbn-schedule-assignment/requirements.md:9.2]
    *   WHEN save operations fail THEN the system SHALL notify users and attempt recovery. [isbn-schedule-assignment/requirements.md:9.3]
    *   WHEN loading data THEN the system SHALL validate file integrity and handle corruption gracefully. [isbn-schedule-assignment/requirements.md:9.4]
*   **As a developer, I want a command-line interface for ISBN management, so that I can integrate ISBN operations with automated publishing workflows.**
    *   WHEN I use the CLI THEN the system SHALL support all major operations including add-block, schedule, assign, and report. [isbn-schedule-assignment/requirements.md:10.1]
    *   WHEN I use CLI commands THEN the system SHALL provide clear help documentation and examples. [isbn-schedule-assignment/requirements.md:10.2]
    *   WHEN CLI operations fail THEN the system SHALL return appropriate exit codes and error messages. [isbn-schedule-assignment/requirements.md:10.3]
    *   WHEN I use the CLI THEN the system SHALL support different output formats including table, JSON, and CSV. [isbn-schedule-assignment/requirements.md:10.4]
*   **As a publisher, I want automatic UPC-A barcode generation with ISBN-13 when ISBNs are assigned, so that books are ready for retail distribution.**
    *   WHEN an ISBN-13 is assigned to a book THEN a UPC-A barcode SHALL be automatically generated. [book-production-fixes/requirements.md:15.1]
    *   WHEN the barcode is created THEN it SHALL include bar-code-reader numerals for retail scanning. [book-production-fixes/requirements.md:15.2]
    *   WHEN the barcode is integrated THEN it SHALL be properly positioned on the back cover. [book-production-fixes/requirements.md:15.3]
    *   WHEN barcode generation occurs THEN it SHALL meet industry standards for retail distribution. [book-production-fixes/requirements.md:15.4]
    *   WHEN ISBN assignment is complete THEN the book SHALL be ready for retail with proper barcode integration. [book-production-fixes/requirements.md:15.5]
*   **As a system administrator, I want ISBN lookups to be cached in processed JSON files and avoid duplicate scans, so that the system is efficient and doesn't repeat expensive API calls.**
    *   WHEN an ISBN is encountered in a document THEN the system SHALL check if it has already been processed in the cached JSON. [book-production-fixes/requirements.md:2.1]
    *   WHEN an ISBN lookup is performed THEN the results SHALL be stored in the processed JSON file for future reference. [book-production-fixes/requirements.md:2.2]
    *   WHEN a document is scanned for ISBNs THEN the system SHALL not repeat the scan if it has already been completed. [book-production-fixes/requirements.md:2.3]
    *   WHEN cached ISBN data exists THEN it SHALL be used instead of making new API calls. [book-production-fixes/requirements.md:2.4]
    *   WHEN ISBN lookup fails THEN the system SHALL log the failure and continue processing without blocking the pipeline. [book-production-fixes/requirements.md:2.5]
*   **As a scheduling coordinator, I want intelligent publication date assignment, so that books are distributed evenly across available publication dates.**
    *   WHEN processing publication dates THEN the system SHALL extract month/year from `schedule.json`. [xynapse-tranche-1/requirements.md:5.1]
    *   WHEN assigning dates THEN the system SHALL spread all titles across Tuesdays in the target month. [xynapse-tranche-1/requirements.md:5.2]
    *   WHEN multiple books exist THEN the system SHALL distribute them evenly across available Tuesdays. [xynapse-tranche-1/requirements.md:5.3]
    *   WHEN date assignment completes THEN the system SHALL ensure no date conflicts exist. [xynapse-tranche-1/requirements.md:5.4]

### 1.5 Series Metadata Management

**User Stories & Acceptance Criteria:**

*   **As a publisher, I want to manage book series metadata for LSI distribution, so that I can maintain consistent series information and automatically assign series numbers.**
    *   WHEN a publisher creates a series THEN the system SHALL store the series name and generate a unique series ID. [lsi-field-enhancement-phase3/requirements.md:2.1]
    *   WHEN a book is added to a series THEN the system SHALL assign it a sequence number within that series. [lsi-field-enhancement-phase3/requirements.md:2.2]
    *   WHEN a user starts the Book Pipeline with a series name THEN the system SHALL automatically assign the appropriate series number. [lsi-field-enhancement-phase3/requirements.md:2.3]
    *   WHEN a publisher has multiple series THEN the system SHALL maintain separate tracking for each series. [lsi-field-enhancement-phase3/requirements.md:2.4]
    *   WHEN different publishers have series with the same name THEN the system SHALL treat them as separate series with different IDs. [lsi-field-enhancement-phase3/requirements.md:2.5]
    *   WHEN a series is designated as multi-publisher THEN the system SHALL allow multiple publishers to contribute to it. [lsi-field-enhancement-phase3/requirements.md:2.6]
    *   WHEN a series is not explicitly designated as multi-publisher THEN the system SHALL default it to single-publisher. [lsi-field-enhancement-phase3/requirements.md:2.7]
    *   WHEN a user performs CRUD operations on series titles THEN the system SHALL maintain the integrity of the series without renumbering. [lsi-field-enhancement-phase3/requirements.md:2.8]
*   **As a user, I select a series in the UI THEN the system SHALL allow selection from registered series or creation of a new one.** [lsi-field-enhancement-phase3/requirements.md:3.1]
*   **As a user, when a title is assigned to a series THEN the system SHALL assign it a series ID number.** [lsi-field-enhancement-phase3/requirements.md:3.2]
*   **As a series publisher, I want short descriptions to reference the series name when applicable, so that readers understand the book's context within the series.**
    *   WHEN a book has a series name AND short description contains "This book" THEN the system SHALL replace it with "This book in the {series_name} series". [lsi-field-mapping-corrections/requirements.md:4.1]
    *   WHEN a book has no series name THEN the system SHALL leave "This book" unchanged. [lsi-field-mapping-corrections/requirements.md:4.2]
    *   WHEN short description doesn't contain "This book" THEN the system SHALL leave the description unchanged. [lsi-field-mapping-corrections/requirements.md:4.3]
    *   WHEN series name is empty or null THEN the system SHALL treat it as no series. [lsi-field-mapping-corrections/requirements.md:4.4]

### 1.6 UI & Configuration Management

**User Stories & Acceptance Criteria:**

*   **As a user, I want the configuration to load automatically when I select publisher/imprint/tranche options, so that I don't need to manually click a load button.**
    *   WHEN I select a publisher, imprint, or tranche THEN the system SHALL automatically load and merge the configurations. [streamlit-form-button-fix/requirements.md:1.1]
    *   WHEN configurations are loaded automatically THEN the system SHALL update the session state with the merged configuration. [streamlit-form-button-fix/requirements.md:1.2]
    *   WHEN configuration loading fails THEN the system SHALL display an error message to the user. [streamlit-form-button-fix/requirements.md:1.3]
    *   WHEN no configurations are selected THEN the system SHALL use default values. [streamlit-form-button-fix/requirements.md:1.4]
*   **As a user, I want to be able to change my configuration selections if I realize I picked the wrong ones, so that I can correct my choices without errors.**
    *   WHEN I change any configuration selection THEN the system SHALL immediately reload the configuration. [streamlit-form-button-fix/requirements.md:2.1]
    *   WHEN I change from a valid configuration to an invalid one THEN the system SHALL show validation warnings. [streamlit-form-button-fix/requirements.md:2.2]
    *   WHEN I change configurations THEN the system SHALL preserve any manual parameter overrides where possible. [streamlit-form-button-fix/requirements.md:2.3]
    *   WHEN configuration changes occur THEN the system SHALL provide visual feedback about the loading process. [streamlit-form-button-fix/requirements.md:2.4]
*   **As a developer, I want the form to comply with Streamlit's constraints, so that the application runs without errors.**
    *   WHEN the form is rendered THEN it SHALL NOT contain any `st.button()` calls. [streamlit-form-button-fix/requirements.md:3.1]
    *   WHEN the form is rendered THEN it SHALL only use `st.form_submit_button()` for form submission. [streamlit-form-button-fix/requirements.md:3.2]
    *   WHEN the configuration selector is used THEN it SHALL work both inside and outside of forms. [streamlit-form-button-fix/requirements.md:3.3]
    *   WHEN the UI components are loaded THEN they SHALL not cause Streamlit API exceptions. [streamlit-form-button-fix/requirements.md:3.4]
*   **As a user, I want clear visual feedback about configuration loading status, so that I understand what's happening when I make selections.**
    *   WHEN configurations are being loaded THEN the system SHALL show a loading indicator. [streamlit-form-button-fix/requirements.md:4.1]
    *   WHEN configuration loading completes successfully THEN the system SHALL show a success message. [streamlit-form-button-fix/requirements.md:4.2]
    *   WHEN configuration inheritance is active THEN the system SHALL display the inheritance chain. [streamlit-form-button-fix/requirements.md:4.3]
    *   WHEN validation occurs THEN the system SHALL show validation status in real-time. [streamlit-form-button-fix/requirements.md:4.4]
*   **As a user, I want the imprint dropdown to automatically refresh and show available imprints when I select a publisher, so that I can properly configure the pipeline without manual page refreshes.**
    *   WHEN a user selects "nimble_books" as publisher THEN the imprint dropdown SHALL immediately show "xynapse_traces" as an option. [streamlit-ui-runaway-fixes/requirements.md:1.1]
    *   WHEN a user changes from one publisher to another THEN the imprint dropdown SHALL clear and repopulate with the new publisher's imprints. [streamlit-ui-runaway-fixes/requirements.md:1.2]
    *   WHEN the publisher selection changes THEN the system SHALL NOT trigger infinite rerun loops. [streamlit-ui-runaway-fixes/requirements.md:1.3]
    *   WHEN the imprint dropdown refreshes THEN the tranche dropdown SHALL also refresh to show relevant tranches. [streamlit-ui-runaway-fixes/requirements.md:1.4]
    *   WHEN no publisher is selected THEN the imprint dropdown SHALL show only an empty option. [streamlit-ui-runaway-fixes/requirements.md:1.5]
*   **As a user, I want to click the "Validate Only" button to check my configuration without causing the application to enter an infinite refresh loop, so that I can validate my settings safely.**
    *   WHEN a user clicks the "Validate Only" button THEN the system SHALL validate the configuration exactly once. [streamlit-ui-runaway-fixes/requirements.md:2.1]
    *   WHEN validation completes THEN the system SHALL display validation results without triggering additional reruns. [streamlit-ui-runaway-fixes/requirements.md:2.2]
    *   WHEN validation results are shown THEN the page SHALL remain stable and responsive. [streamlit-ui-runaway-fixes/requirements.md:2.3]
    *   WHEN validation finds errors THEN the system SHALL display them clearly without causing UI instability. [streamlit-ui-runaway-fixes/requirements.md:2.4]
    *   WHEN validation is successful THEN the system SHALL show success status without page refresh loops. [streamlit-ui-runaway-fixes/requirements.md:2.5]
*   **As a user, I want the UI to respond to my interactions smoothly without causing cascading page refreshes that make the application unusable, so that I can work efficiently with the configuration interface.**
    *   WHEN any form element changes THEN the system SHALL update only the necessary dependent elements. [streamlit-ui-runaway-fixes/requirements.md:3.1]
    *   WHEN session state is updated THEN the system SHALL NOT trigger unnecessary reruns. [streamlit-ui-runaway-fixes/requirements.md:3.2]
    *   WHEN dropdown dependencies change THEN the system SHALL use controlled refresh mechanisms. [streamlit-ui-runaway-fixes/requirements.md:3.3]
    *   WHEN validation is triggered THEN the system SHALL prevent rerun loops during the validation process. [streamlit-ui-runaway-fixes/requirements.md:3.4]
    *   WHEN configuration loading occurs THEN the system SHALL debounce rapid successive changes. [streamlit-ui-runaway-fixes/requirements.md:3.5]
*   **As a user, I want the application to maintain consistent state across interactions without losing my selections or causing unexpected behavior, so that my workflow is predictable and reliable.**
    *   WHEN dropdown selections change THEN the system SHALL update session state atomically. [streamlit-ui-runaway-fixes/requirements.md:4.1]
    *   WHEN publisher changes THEN the system SHALL preserve valid dependent selections where possible. [streamlit-ui-runaway-fixes/requirements.md:4.2]
    *   WHEN configuration loads THEN the system SHALL maintain UI state consistency. [streamlit-ui-runaway-fixes/requirements.md:4.3]
    *   WHEN validation occurs THEN the system SHALL preserve form data and user selections. [streamlit-ui-runaway-fixes/requirements.md:4.4]
    *   WHEN errors occur THEN the system SHALL maintain stable session state without corruption. [streamlit-ui-runaway-fixes/requirements.md:4.5]
*   **As a user, I want the publisher and imprint I select in the Configuration Selection to automatically populate the corresponding fields in Core Settings, so that I don't get validation errors for fields that should be pre-filled.**
    *   WHEN a user selects a publisher in the Configuration Selection THEN the publisher field in Core Settings SHALL be automatically populated with the same value. [config-sync-fix/requirements.md:1.1]
    *   WHEN a user selects an imprint in the Configuration Selection THEN the imprint field in Core Settings SHALL be automatically populated with the same value. [config-sync-fix/requirements.md:1.2]
    *   WHEN a user clicks the refresh button in Configuration Selection THEN any updated publisher/imprint values SHALL be synchronized to Core Settings. [config-sync-fix/requirements.md:1.3]
    *   WHEN the Configuration Selection values are synchronized to Core Settings THEN the validation SHALL pass for these required fields. [config-sync-fix/requirements.md:1.4]
    *   WHEN a user manually changes the publisher or imprint in Core Settings THEN it SHALL override the Configuration Selection values for that session. [config-sync-fix/requirements.md:1.5]
*   **As a user, I want the Core Settings to show meaningful default values based on my configuration selection, so that I can see what values will be used without having to guess.**
    *   WHEN the page loads with no configuration selected THEN the Core Settings publisher and imprint fields SHALL show placeholder text indicating they will be populated from configuration. [config-sync-fix/requirements.md:2.1]
    *   WHEN a valid publisher and imprint are selected in Configuration Selection THEN the Core Settings SHALL immediately reflect these values. [config-sync-fix/requirements.md:2.2]
    *   WHEN the configuration selection is cleared or reset THEN the Core Settings SHALL revert to empty/placeholder state. [config-sync-fix/requirements.md:2.3]
    *   WHEN configuration values are populated THEN they SHALL be visually distinct from user-entered values (e.g., with helper text indicating "from configuration"). [config-sync-fix/requirements.md:2.4]
*   **As a user, I want the validation to recognize when required fields are populated from configuration selection, so that I don't see false validation errors.**
    *   WHEN publisher and imprint are populated from Configuration Selection THEN validation SHALL treat these as valid required field values. [config-sync-fix/requirements.md:3.1]
    *   WHEN validation runs THEN it SHALL check both the Core Settings form values AND the Configuration Selection values for required fields. [config-sync-fix/requirements.md:3.2]
    *   WHEN a required field is empty in Core Settings but populated in Configuration Selection THEN validation SHALL pass for that field. [config-sync-fix/requirements.md:3.3]
    *   WHEN validation displays results THEN it SHALL clearly indicate which values came from configuration vs. user input. [config-sync-fix/requirements.md:3.4]
    *   WHEN validation fails THEN error messages SHALL provide clear guidance on whether to fix the issue in Configuration Selection or Core Settings. [config-sync-fix/requirements.md:3.5]
*   **As a user, I want a clear understanding of how Configuration Selection and Core Settings work together, so that I can efficiently configure the pipeline without confusion.**
    *   WHEN I view the interface THEN there SHALL be clear visual indicators showing which Core Settings values are populated from Configuration Selection. [config-sync-fix/requirements.md:4.1]
    *   WHEN I change a value in Configuration Selection THEN any affected Core Settings SHALL update immediately with visual feedback. [config-sync-fix/requirements.md:4.2]
    *   WHEN I manually override a Core Settings value THEN there SHALL be a clear indication that this value is now independent of Configuration Selection. [config-sync-fix/requirements.md:4.3]
    *   WHEN I hover over auto-populated fields THEN tooltips SHALL explain that these values come from Configuration Selection. [config-sync-fix/requirements.md:4.4]
    *   WHEN validation runs THEN the results SHALL clearly distinguish between configuration-derived and user-entered values. [config-sync-fix/requirements.md:4.5]
*   **As a developer, I want proper state synchronization between Configuration Selection and Core Settings, so that the interface behaves predictably and maintains data consistency.**
    *   WHEN Configuration Selection values change THEN the session state SHALL be updated to reflect the new values. [config-sync-fix/requirements.md:5.1]
    *   WHEN Core Settings form is rendered THEN it SHALL pull default values from the current Configuration Selection state. [config-sync-fix/requirements.md:5.2]
    *   WHEN a user manually overrides a Core Settings value THEN the override state SHALL be tracked separately from configuration defaults. [config-sync-fix/requirements.md:5.3]
    *   WHEN the page refreshes or reloads THEN the synchronization between Configuration Selection and Core Settings SHALL be restored. [config-sync-fix/requirements.md:5.4]
    *   WHEN multiple users access the system THEN each user's configuration state SHALL be maintained independently. [config-sync-fix/requirements.md:5.5]
*   **As a publisher, I want required fields to have sensible defaults, so that I don't have to manually enter common values every time.**
    *   WHEN using simple or advanced display modes THEN `lightning_source_account` SHALL default to "6024045". [pipeline-configuration-fixes/requirements.md:1.1]
    *   WHEN configuring language settings THEN `language_code` SHALL default to "eng". [pipeline-configuration-fixes/requirements.md:1.2]
    *   WHEN setting up field reports THEN `field_reports` SHALL default to "HTML". [pipeline-configuration-fixes/requirements.md:1.3]
    *   WHEN these defaults are set THEN they SHALL be visible in the UI and used in processing. [pipeline-configuration-fixes/requirements.md:1.4]
*   **As a web admin and system operator, I need the tranche config to be available on the dropdowns in the Book Pipeline, so that users can select appropriate tranche configurations for book processing.**
    *   WHEN the Book Pipeline UI loads THEN the tranche dropdown SHALL display all available tranche configurations. [book-production-fixes/requirements.md:5.1]
    *   WHEN tranche configurations are updated THEN the dropdown SHALL refresh to show current options. [book-production-fixes/requirements.md:5.2]
    *   WHEN a user selects a tranche THEN the system SHALL load the corresponding configuration. [book-production-fixes/requirements.md:5.3]
    *   WHEN no tranche configurations exist THEN the system SHALL display an appropriate message. [book-production-fixes/requirements.md:5.4]
    *   WHEN tranche selection is made THEN it SHALL be properly passed to the book processing pipeline. [book-production-fixes/requirements.md:5.5]

### 1.7 Content Generation & Formatting (General)

**User Stories & Acceptance Criteria:**

*   **As a publisher, I want the back cover text to properly substitute template variables like `{stream}`, `{title}`, `{description}`, and `{quotes_per_book}` with actual book data, so that the back cover displays meaningful content instead of placeholder text.**
    *   WHEN the cover generation system processes `back_cover_text` THEN it SHALL substitute `{stream}` with the book's subject/topic. [cover-fixes/requirements.md:1.1]
    *   WHEN the cover generation system processes `back_cover_text` THEN it SHALL substitute `{title}` with the actual book title. [cover-fixes/requirements.md:1.2]
    *   WHEN the cover generation system processes `back_cover_text` THEN it SHALL substitute `{description}` with the book description. [cover-fixes/requirements.md:1.3]
    *   WHEN the cover generation system processes `back_cover_text` THEN it SHALL substitute `{quotes_per_book}` with the actual number of quotes. [cover-fixes/requirements.md:1.4]
    *   WHEN all variables are substituted THEN the back cover SHALL display complete, meaningful text without any remaining placeholder variables. [cover-fixes/requirements.md:1.5]
*   **As a publisher, I want the Korean characters (필사) on the front cover to display properly without visible LaTeX commands, so that the cover looks professional and the Korean text renders correctly.**
    *   WHEN the cover generation system processes Korean text THEN it SHALL NOT display visible `\korean{}` LaTeX commands on the rendered cover. [cover-fixes/requirements.md:2.1]
    *   WHEN Korean text is processed THEN it SHALL use the proper Korean font (AppleMyungjo) for rendering. [cover-fixes/requirements.md:2.2]
    *   WHEN the cover is generated THEN the Korean characters SHALL appear as clean, properly formatted text. [cover-fixes/requirements.md:2.3]
    *   WHEN the LaTeX is compiled THEN the `\korean{}` command SHALL be processed internally without appearing in the final output. [cover-fixes/requirements.md:2.4]
    *   WHEN the cover template is populated THEN Korean text variables SHALL be properly escaped for LaTeX processing. [cover-fixes/requirements.md:2.5]
*   **As a book publisher, I want the back cover text to be processed through an LLM so that all variable substitutions are resolved intelligently and the final text flows naturally.**
    *   WHEN the cover generation process encounters back cover text with variables THEN the system SHALL send the template text to an LLM for processing. [llm-back-cover-text-processing/requirements.md:1.1]
    *   WHEN the LLM processes the back cover text THEN it SHALL resolve all variable substitutions using the book metadata. [llm-back-cover-text-processing/requirements.md:1.2]
    *   WHEN the LLM returns the processed text THEN it SHALL be clean, final text with no remaining variables or placeholders. [llm-back-cover-text-processing/requirements.md:1.3]
    *   WHEN the processed text is returned THEN it SHALL be properly formatted for LaTeX placement on the cover. [llm-back-cover-text-processing/requirements.md:1.4]
*   **As a book designer, I want the back cover narrative to be less than 100 words. All back text must fit in a safe area in top part of page.** [llm-back-cover-text-processing/requirements.md:5]
*   **As a book processing system, I want to accurately count mnemonic entries that start with bold text, so that I can generate the correct number of practice pages.**
    *   WHEN processing mnemonics LaTeX content THEN the system SHALL count only `\textbf` commands that appear at the beginning of a line. [textbf-line-detection-fix/requirements.md:1.1]
    *   WHEN a `\textbf` command is preceded by whitespace or other characters on the same line THEN the system SHALL NOT count it as a line-beginning bold command. [textbf-line-detection-fix/requirements.md:1.2]
    *   WHEN a `\textbf` command appears immediately after a newline character with no intervening characters THEN the system SHALL count it as a line-beginning bold command. [textbf-line-detection-fix/requirements.md:1.3]
    *   WHEN the mnemonics count is determined THEN the system SHALL use this count to generate the appropriate number of practice pages. [textbf-line-detection-fix/requirements.md:1.4]
*   **As a book publisher, I want to generate books with alternating mnemonic and practice pages, so that readers can study mnemonics and then practice them on dedicated dot grid pages.**
    *   WHEN a book contains mnemonic content THEN the system SHALL place each mnemonic on a verso (left-hand) page. [mnemonic-practice-layout/requirements.md:1.1]
    *   WHEN a mnemonic is placed on a verso page THEN the system SHALL generate a corresponding recto (right-hand) dot grid page immediately following it. [mnemonic-practice-layout/requirements.md:1.2]
    *   WHEN generating dot grid practice pages THEN the system SHALL include "Mnemonic Practice {i}" text at the bottom of each page where {i} is the sequential practice number. [mnemonic-practice-layout/requirements.md:1.3]
*   **As a content manager, I want enhanced annotation/summary generation, so that book descriptions are comprehensive and consistent.**
    *   WHEN generating annotations THEN the system SHALL combine LLM completion results with boilerplate strings. [xynapse-tranche-1/requirements.md:6.1]
    *   WHEN using boilerplate THEN the system SHALL source strings from configuration dictionary. [xynapse-tranche-1/requirements.md:6.2]
    *   WHEN joining content THEN the system SHALL ensure proper formatting and flow. [xynapse-tranche-1/requirements.md:6.3]
    *   WHEN content exceeds limits THEN the system SHALL truncate appropriately while maintaining readability. [xynapse-tranche-1/requirements.md:6.4]
*   **As a format compliance manager, I want proper content length validation, so that all text fields meet LSI requirements.**
    *   WHEN validating short description THEN the system SHALL ensure it is no more than 350 bytes. [xynapse-tranche-1/requirements.md:8.1]
    *   WHEN content exceeds limits THEN the system SHALL truncate while preserving meaning. [xynapse-tranche-1/requirements.md:8.2]
    *   WHEN truncation occurs THEN the system SHALL log the original and truncated content. [xynapse-tranche-1/requirements.md:8.3]
    *   WHEN validation completes THEN the system SHALL report any length violations. [xynapse-tranche-1/requirements.md:8.4]
*   **As a subject classification specialist, I want proper Thema subject handling, so that subject codes are complete and accurate.**
    *   WHEN processing Thema subjects THEN the system SHALL use full multi-letter strings instead of single letters. [xynapse-tranche-1/requirements.md:9.1]
    *   WHEN validating Thema codes THEN the system SHALL ensure codes are complete and valid. [xynapse-tranche-1/requirements.md:9.2]
    *   WHEN Thema subjects are truncated THEN the system SHALL restore full codes. [xynapse-tranche-1/requirements.md:9.3]
    *   WHEN multiple Thema subjects exist THEN the system SHALL handle all with consistent formatting. [xynapse-tranche-1/requirements.md:9.4]
*   **As a metadata manager, I want Thema subject codes extracted from JSON metadata and properly mapped to LSI columns, so that subject classification is accurate and complete.**
    *   WHEN JSON metadata contains "thema" field with array values THEN the system SHALL extract the first three values. [lsi-field-mapping-corrections/requirements.md:2.1]
    *   WHEN thema values are extracted THEN the system SHALL map them to "Thema Subject 1", "Thema Subject 2", and "Thema Subject 3" columns respectively. [lsi-field-mapping-corrections/requirements.md:2.2]
    *   WHEN fewer than 3 thema values exist THEN the system SHALL leave remaining Thema Subject columns empty. [lsi-field-mapping-corrections/requirements.md:2.3]
    *   WHEN no thema values exist in JSON THEN the system SHALL leave all Thema Subject columns empty. [lsi-field-mapping-corrections/requirements.md:2.4]
    *   WHEN thema values are malformed or invalid THEN the system SHALL log warnings and skip invalid entries. [lsi-field-mapping-corrections/requirements.md:2.5]
*   **As a content categorizer, I want minimum and maximum age values extracted from JSON metadata and formatted as integers, so that age targeting is properly specified in the LSI submission.**
    *   WHEN JSON metadata contains "min_age" field THEN the system SHALL extract and convert it to integer format for "Min Age" column. [lsi-field-mapping-corrections/requirements.md:3.1]
    *   WHEN JSON metadata contains "max_age" field THEN the system SHALL extract and convert it to integer format for "Max Age" column. [lsi-field-mapping-corrections/requirements.md:3.2]
    *   WHEN age values are non-numeric THEN the system SHALL log warnings and leave age columns empty. [lsi-field-mapping-corrections/requirements.md:3.3]
    *   WHEN age values are negative or unrealistic (>150) THEN the system SHALL validate and reject invalid values. [lsi-field-mapping-corrections/requirements.md:3.4]
    *   WHEN no age values exist in JSON THEN the system SHALL leave age columns empty. [lsi-field-mapping-corrections/requirements.md:3.5]
*   **As a publisher, I want a properly created Mnemonics appendix for each book, so that the mnemonics.tex file is generated successfully without JSON parsing errors.**
    *   WHEN mnemonics are generated THEN the LLM response SHALL include the expected 'mnemonics_data' key. [book-production-fixes/requirements.md:9.1]
    *   WHEN the mnemonics prompt is executed THEN it SHALL be reformulated to require the expected JSON structure. [book-production-fixes/requirements.md:9.2]
    *   WHEN JSON parsing fails THEN the system SHALL provide clear error messages and fallback behavior. [book-production-fixes/requirements.md:9.3]
    *   WHEN mnemonics content is missing THEN the system SHALL log the issue and continue processing. [book-production-fixes/requirements.md:9.4]
    *   WHEN mnemonics.tex is created THEN it SHALL contain properly formatted mnemonic content. [book-production-fixes/requirements.md:9.5]
*   **As a publisher and bookseller, I want BISAC categories to accurately reflect the specific technical content of each book, so that readers can find books through appropriate subject classifications.**
    *   WHEN BISAC categories are generated THEN they SHALL reflect the specific technical content discussed in the book. [book-production-fixes/requirements.md:11.1]
    *   WHEN generic categories like "Business>General" are detected THEN they SHALL be replaced with more specific classifications. [book-production-fixes/requirements.md:11.2]
    *   WHEN technical content is analyzed THEN appropriate categories like "Science > Planetary Exploration" SHALL be selected. [book-production-fixes/requirements.md:11.3]
    *   WHEN multiple BISAC categories are assigned THEN each SHALL be relevant to the book's actual content. [book-production-fixes/requirements.md:11.4]
    *   WHEN category validation occurs THEN it SHALL ensure categories match the book's subject matter. [book-production-fixes/requirements.md:11.5]
*   **As a content curator, I want quote assembly to avoid repetitive author citations, so that the quotations section has better variety and readability.**
    *   WHEN quotations are assembled THEN no single author SHALL be quoted more than three times in a row. [book-production-fixes/requirements.md:13.1]
    *   WHEN author repetition is detected THEN the system SHALL reorder quotes to improve distribution. [book-production-fixes/requirements.md:13.2]
    *   WHEN quote ordering is applied THEN it SHALL maintain thematic coherence while improving author variety. [book-production-fixes/requirements.md:13.3]
    *   WHEN insufficient quotes exist from different authors THEN the system SHALL work with available content while minimizing repetition. [book-production-fixes/requirements.md:13.4]
    *   WHEN quote assembly is complete THEN the final arrangement SHALL be reviewed for author distribution balance. [book-production-fixes/requirements.md:13.5]
*   **As an editor, I want the Publisher's Note to be concise, engaging, and properly formatted, so that it effectively motivates both publishers and readers.**
    *   WHEN the Publisher's Note is generated THEN it SHALL consist of exactly 3 medium-length paragraphs. [book-production-fixes/requirements.md:8.1]
    *   WHEN each paragraph is created THEN it SHALL have a maximum of 600 characters. [book-production-fixes/requirements.md:8.2]
    *   WHEN the content is written THEN it SHALL explain once that this is a pilsa book. [book-production-fixes/requirements.md:8.3]
    *   WHEN current events are referenced THEN they SHALL be included without being date-specific. [book-production-fixes/requirements.md:8.4]
    *   WHEN the note is finalized THEN it SHALL focus on motivating both publisher and reader engagement. [book-production-fixes/requirements.md:8.5]
*   **As a publisher, I want publisher's note to be 100% LLM generated, so that no boilerplate text is attached.**
    *   WHEN publisher's note is generated THEN it SHALL be 100% LLM generated content. [frontmatter-backmatter-fixes/requirements.md:3.1]
    *   WHEN publisher's note is created THEN no boilerplate paragraphs SHALL be attached. [frontmatter-backmatter-fixes/requirements.md:3.2]
    *   WHEN publisher's note uses reprompting THEN it SHALL use `storefront_get_en_motivation` prompt. [frontmatter-backmatter-fixes/requirements.md:3.3]
*   **As a publisher, I want foreword generation to produce clean text, so that Korean characters and markdown are properly formatted.**
    *   WHEN foreword is generated THEN Korean characters SHALL be properly formatted (no visible markdown). [frontmatter-backmatter-fixes/requirements.md:4.1]
    *   WHEN foreword contains Korean terms THEN they SHALL use proper LaTeX commands. [frontmatter-backmatter-fixes/requirements.md:4.2]
    *   WHEN foreword is generated THEN no visible markdown syntax SHALL appear (no `*pilsa*`). [frontmatter-backmatter-fixes/requirements.md:4.3]
    *   WHEN foreword uses reprompting THEN it SHALL follow same sequence as main model calls. [frontmatter-backmatter-fixes/requirements.md:4.4]
*   **As a publisher, I want glossary to display correctly, so that it has proper formatting and no numbering issues.**
    *   WHEN glossary is generated THEN it SHALL NOT have numeral "2" at the beginning. [frontmatter-backmatter-fixes/requirements.md:5.1]
    *   WHEN glossary text is displayed THEN it SHALL NOT be overprinted on itself. [frontmatter-backmatter-fixes/requirements.md:5.2]
    *   WHEN glossary is formatted THEN it SHALL have proper leading for typographic best practices. [frontmatter-backmatter-fixes/requirements.md:5.3]
    *   WHEN glossary uses chapter heading THEN it SHALL use `\chapter*{Glossary}` (unnumbered). [frontmatter-backmatter-fixes/requirements.md:5.4]
*   **As a publisher, I want mnemonics section to appear in the final document, so that all backmatter is complete.**
    *   WHEN book is processed THEN mnemonics section SHALL appear in final document. [frontmatter-backmatter-fixes/requirements.md:6.1]
    *   WHEN mnemonics processing fails THEN fallback methods SHALL be used. [frontmatter-backmatter-fixes/requirements.md:6.2]
    *   WHEN mnemonics are generated THEN they SHALL use proper LLM configuration. [frontmatter-backmatter-fixes/requirements.md:6.3]
    *   WHEN mnemonics file is created THEN it SHALL be `mnemonics.tex` in build directory. [frontmatter-backmatter-fixes/requirements.md:6.4]
*   **As a publisher, I want all three BISAC category fields to be populated with appropriate categories, so that my books are properly classified for distribution.**
    *   WHEN the LSI CSV is generated THEN all three BISAC Category fields (BISAC Category, BISAC Category 2, BISAC Category 3) SHALL be populated. [bisac-category-fixes/requirements.md:1.1]
    *   WHEN a BISAC category is assigned THEN it SHALL contain the full category name without the code (e.g., "BUSINESS & ECONOMICS / General" not "BUS000000"). [bisac-category-fixes/requirements.md:1.2]
    *   WHEN multiple BISAC categories are needed THEN they SHALL be distinct and relevant to the book content. [bisac-category-fixes/requirements.md:1.3]
    *   IF fewer than three relevant categories exist THEN only the relevant categories SHALL be populated, leaving others empty. [bisac-category-fixes/requirements.md:1.4]
*   **As a publisher, I want BISAC categories to be validated against current standards, so that my books meet distribution requirements.**
    *   WHEN BISAC categories are generated THEN they SHALL be validated against the current BISAC standards database. [bisac-category-fixes/requirements.md:2.1]
    *   WHEN an invalid BISAC category is detected THEN the system SHALL use a fallback strategy with valid alternatives. [bisac-category-fixes/requirements.md:2.2]
    *   WHEN BISAC categories are assigned THEN they SHALL use the most recent BISAC standards (2024). [bisac-category-fixes/requirements.md:2.3]
    *   IF a generated category is not found in the standards THEN the system SHALL log a warning and use the closest valid match. [bisac-category-fixes/requirements.md:2.4]
*   **As a publisher, I want BISAC categories to be intelligently generated based on book content, so that categorization is accurate and relevant.**
    *   WHEN generating BISAC categories THEN the system SHALL use LLM assistance to analyze book metadata. [bisac-category-fixes/requirements.md:3.1]
    *   WHEN the LLM generates categories THEN they SHALL be ranked by relevance to the book content. [bisac-category-fixes/requirements.md:3.2]
    *   WHEN book metadata contains existing BISAC information THEN it SHALL be used as the primary category. [bisac-category-fixes/requirements.md:3.3]
    *   IF the primary category is invalid THEN the system SHALL generate alternatives using LLM assistance. [bisac-category-fixes/requirements.md:3.4]
*   **As a publisher, I want tranche configuration to override BISAC categories for specific book series, so that all books in a series (like PILSA) can be consistently categorized.**
    *   WHEN a tranche config specifies a BISAC category override THEN it SHALL be used as the primary category. [bisac-category-fixes/requirements.md:4.1]
    *   WHEN tranche override is applied THEN the remaining categories SHALL be generated to complement the override. [bisac-category-fixes/requirements.md:4.2]
    *   WHEN tranche override is "Self-Help / Journaling" THEN all PILSA books SHALL use this as their primary category. [bisac-category-fixes/requirements.md:4.3]
    *   IF tranche override is invalid THEN the system SHALL log a warning and use the override anyway if it's a valid category name. [bisac-category-fixes/requirements.md:4.4]
*   **As a publisher, I want BISAC categories to come from different top-level categories when possible, so that books have broader discoverability.**
    *   WHEN generating multiple BISAC categories THEN at least 2 categories SHOULD come from different top-level categories (e.g., BUS vs SEL vs COM). [bisac-category-fixes/requirements.md:5.1]
    *   WHEN selecting categories THEN the system SHALL prioritize diversity across top-level categories. [bisac-category-fixes/requirements.md:5.2]
    *   WHEN only one top-level category is relevant THEN the system SHALL use the most specific subcategories within that top-level. [bisac-category-fixes/requirements.md:5.3]
    *   IF diverse top-level categories cannot be found THEN the system SHALL log this and use the most relevant categories available. [bisac-category-fixes/requirements.md:5.4]
*   **As a publisher and editor, I want bibliographies to use proper hanging indent formatting with memoir citation fields, so that the bibliography appears professionally formatted according to publishing standards.**
    *   WHEN a bibliography is generated THEN it SHALL use memoir citation field formatting. [book-production-fixes/requirements.md:1.1]
    *   WHEN bibliography entries span multiple lines THEN the second and subsequent lines SHALL have a 0.15 hanging indent. [book-production-fixes/requirements.md:1.2]
    *   WHEN bibliography entries are processed THEN they SHALL maintain consistent formatting across all entries. [book-production-fixes/requirements.md:1.3]
    *   WHEN the LaTeX template is applied THEN bibliography formatting SHALL be automatically applied without manual intervention. [book-production-fixes/requirements.md:1.4]
    *   WHEN multiple bibliography entries exist THEN each SHALL be properly separated and formatted independently. [book-production-fixes/requirements.md:1.5]
*   **As a book designer, I want consistent typography and formatting across all book elements, so that the final product meets professional publishing standards.**
    *   WHEN mnemonics pages are generated THEN they SHALL use the same format as quotations with Adobe Caslon font. [book-production-fixes/requirements.md:6.1]
    *   WHEN acronym mnemonics are displayed THEN each letter of the expanded acronym SHALL have its own bullet point. [book-production-fixes/requirements.md:6.2]
    *   WHEN Korean characters appear on title pages THEN they SHALL use Apple Myungjo font. [book-production-fixes/requirements.md:6.3]
    *   WHEN instructions are placed THEN they SHALL appear on every 8th recto page at the bottom. [book-production-fixes/requirements.md:6.4]
    *   WHEN chapter headings are formatted THEN the leading underneath SHALL be reduced to approximately 36 points. [book-production-fixes/requirements.md:6.5]
    *   WHEN LaTeX commands are used THEN they SHALL be properly escaped so that they are not visible. For example, the string "\textit" should never be visible in the compiled PDF. [book-production-fixes/requirements.md:6.6]
*   **As a content formatter, I want glossaries to be properly formatted in 2 columns within the page text area, so that Korean and English terms are clearly presented.**
    *   WHEN a glossary is generated THEN it SHALL be formatted in exactly 2 columns. [book-production-fixes/requirements.md:7.1]
    *   WHEN glossary content is laid out THEN it SHALL fit within the defined page text area. [book-production-fixes/requirements.md:7.2]
    *   WHEN Korean and English terms are displayed THEN they SHALL be stacked on top of each other in the left-hand cells. [book-production-fixes/requirements.md:7.3]
    *   WHEN glossary formatting is applied THEN it SHALL maintain consistent spacing and alignment. [book-production-fixes/requirements.md:7.4]
    *   WHEN multiple glossary entries exist THEN they SHALL be distributed evenly across both columns. [book-production-fixes/requirements.md:7.5]
*   **As a publisher, I want configurable writing styles at tranche, imprint, and publisher levels, so that I can maintain consistent voice and tone across publications.**
    *   WHEN writing style configuration is needed THEN it SHALL be available at tranche, imprint, and publisher levels. [book-production-fixes/requirements.md:12.1]
    *   WHEN style configuration is defined THEN it SHALL be stored in a `writing_style.json` file in the appropriate directory. [book-production-fixes/requirements.md:12.2]
    *   WHEN multiple text values exist in the JSON THEN they SHALL be constructed into a single prompt to append to the original prompt. [book-production-fixes/requirements.md:12.3]
    *   WHEN style configuration is applied THEN it SHALL override lower-level configurations (tranche > imprint > publisher). [book-production-fixes/requirements.md:12.4]
    *   WHEN no style configuration exists THEN the system SHALL use default styling without errors. [book-production-fixes/requirements.md:12.5]
*   **As a book designer, I want blank last verso pages to have a "Notes" heading, so that the page serves a functional purpose for readers.**
    *   WHEN the last verso page is blank THEN it SHALL have a chapter heading reading "Notes" at the top of the page. [book-production-fixes/requirements.md:14.1]
    *   WHEN the Notes heading is added THEN it SHALL follow the same formatting as other chapter headings. [book-production-fixes/requirements.md:14.2]
    *   WHEN the last verso page has content THEN no Notes heading SHALL be added. [book-production-fixes/requirements.md:14.3]
    *   WHEN the Notes page is created THEN it SHALL provide space for reader annotations. [book-production-fixes/requirements.md:14.4]
    *   WHEN the book is compiled THEN the Notes page SHALL be properly positioned as the final verso page. [book-production-fixes/requirements.md:14.5]
*   **As the operator of a online book storefront, I want all metadata for each title to be complete and accurate.**
    *   WHEN storefront metadata is generated THEN the author name SHALL match the Contributor One name from the Tranche config. [book-production-fixes/requirements.md:16.1]
    *   WHEN author fields are populated THEN they SHALL not be interpolated or generated by the model. [book-production-fixes/requirements.md:16.2]
    *   WHEN storefront_author_en and _ko fields are created THEN they SHALL use the exact name from the configuration. [book-production-fixes/requirements.md:16.3]
    *   WHEN metadata is validated THEN it SHALL ensure consistency between LSI CSV and storefront data. [book-production-fixes/requirements.md:16.4]
    *   WHEN tranche configuration is missing author data THEN the system SHALL provide clear error messages. [book-production-fixes/requirements.md:16.5]
*   **As a publisher, I want all LLM calls to respect the pipeline configuration, so that I have consistent model usage and cost control.**
    *   WHEN I configure LLM settings in the pipeline THEN all stage 3 processing SHALL use those settings. [pipeline-configuration-fixes/requirements.md:2.1]
    *   WHEN BackmatterProcessor is instantiated THEN it SHALL receive the pipeline LLM configuration. [pipeline-configuration-fixes/requirements.md:2.2]
    *   WHEN foreword generation occurs THEN it SHALL use the pipeline LLM configuration (not hardcoded gemini-2.5-pro). [pipeline-configuration-fixes/requirements.md:2.3]
    *   WHEN publisher's note generation occurs THEN it SHALL use the pipeline LLM configuration. [pipeline-configuration-fixes/requirements.md:2.4]
    *   WHEN no LLM configuration is provided THEN it SHALL use sensible defaults (not hardcoded gemini models). [pipeline-configuration-fixes/requirements.md:2.5]
    *   WHEN LLM calls are made THEN they SHALL log the model being used for transparency. [pipeline-configuration-fixes/requirements.md:2.6]
*   **As a publisher, I want font configurations to be consistently applied, so that the compiled PDF matches my configuration settings.**
    *   WHEN Korean font is configured in tranche settings THEN the LaTeX template SHALL use that font. [pipeline-configuration-fixes/requirements.md:3.1]
    *   WHEN template processing occurs THEN font variables SHALL be substituted from configuration. [pipeline-configuration-fixes/requirements.md:3.2]
    *   WHEN fonts are not specified THEN sensible defaults SHALL be used. [pipeline-configuration-fixes/requirements.md:3.3]
    *   WHEN font substitution fails THEN clear error messages SHALL be provided. [pipeline-configuration-fixes/requirements.md:3.4]
*   **As a publisher, I want all backmatter components to be generated properly, so that the final interior contains complete foreword, publisher's note, and glossary sections.**
    *   WHEN book processing occurs THEN a foreword SHALL be generated using LLM about pilsa tradition. [pipeline-configuration-fixes/requirements.md:4.1]
    *   WHEN book processing occurs THEN a publisher's note SHALL be generated with 3 structured paragraphs. [pipeline-configuration-fixes/requirements.md:4.2]
    *   WHEN book processing occurs THEN a glossary SHALL be generated in 2-column format. [pipeline-configuration-fixes/requirements.md:4.3]
    *   WHEN glossary is generated THEN Korean terms SHALL appear at top of left-hand cells with English equivalents below. [pipeline-configuration-fixes/requirements.md:4.4]
    *   WHEN glossary is generated THEN it SHALL fit within page margins using proper column layout. [pipeline-configuration-fixes/requirements.md:4.5]
    *   WHEN any backmatter generation fails THEN clear error messages SHALL be provided. [pipeline-configuration-fixes/requirements.md:4.6]
*   **As a publisher, I want clean LaTeX output without broken commands, so that the compiled PDF displays properly formatted text.**
    *   WHEN LaTeX content is generated THEN broken LaTeX commands like "extit{" SHALL be properly escaped or removed. [pipeline-configuration-fixes/requirements.md:5.1]
    *   WHEN foreword is generated THEN it SHALL contain no stray LaTeX commands in the final output. [pipeline-configuration-fixes/requirements.md:5.2]
    *   WHEN any text processing occurs THEN LaTeX special characters SHALL be properly escaped. [pipeline-configuration-fixes/requirements.md:5.3]
    *   WHEN LaTeX compilation occurs THEN no LaTeX syntax errors SHALL be present. [pipeline-configuration-fixes/requirements.md:5.4]
*   **As a publisher, I want properly formatted bibliography citations, so that the compiled PDF displays professional hanging indents.**
    *   WHEN bibliography is generated THEN citations SHALL have first line flush left. [pipeline-configuration-fixes/requirements.md:6.1]
    *   WHEN bibliography is generated THEN second and following lines SHALL be indented 0.15 inches. [pipeline-configuration-fixes/requirements.md:6.2]
    *   WHEN bibliography appears in compiled PDF THEN hanging indent formatting SHALL be visible. [pipeline-configuration-fixes/requirements.md:6.3]
    *   WHEN bibliography formatting fails THEN clear error messages SHALL be provided. [pipeline-configuration-fixes/requirements.md:6.4]
*   **As a publisher, I want configuration values to follow a strict hierarchy, so that tranche settings always override other configurations.**
    *   WHEN configuration values conflict THEN hierarchy SHALL be: default < publisher < imprint < tranche (tranche wins). [frontmatter-backmatter-fixes/requirements.md:1.1]
    *   WHEN `schedule.json` contains subtitle THEN it SHALL always trump machine-generated alternatives. [frontmatter-backmatter-fixes/requirements.md:1.2]
    *   WHEN `tranche.json` contains author and imprint THEN they SHALL always trump LLM generated values. [frontmatter-backmatter-fixes/requirements.md:1.3]
    *   WHEN ISBN is assigned THEN it SHALL appear on the copyright page. [frontmatter-backmatter-fixes/requirements.md:1.4]
    *   WHEN logo font is specified in imprint config THEN it SHALL be used (Zapfino for xynapse_traces). [frontmatter-backmatter-fixes/requirements.md:1.5]
*   **As a publisher, I want bibliography formatting to remain stable, so that hanging indents work correctly.** (DO NOT CHANGE)
    *   WHEN bibliography is generated THEN it SHALL use memoir class `\begin{hangparas}{0.15in}{1}` format. [frontmatter-backmatter-fixes/requirements.md:2.1]
    *   WHEN bibliography formatting works correctly THEN it SHALL be marked as "do not change". [frontmatter-backmatter-fixes/requirements.md:2.2]
    *   WHEN bibliography is compiled THEN first line SHALL be flush left, subsequent lines indented 0.15in. [frontmatter-backmatter-fixes/requirements.md:2.3]
*   **As a publisher, I want proper classification of document sections, so that frontmatter and backmatter are correctly organized.**
    *   WHEN sections are classified THEN foreword SHALL be frontmatter. [frontmatter-backmatter-fixes/requirements.md:7.1]
    *   WHEN sections are classified THEN publisher's note SHALL be frontmatter. [frontmatter-backmatter-fixes/requirements.md:7.2]
    *   WHEN sections are classified THEN glossary SHALL be frontmatter. [frontmatter-backmatter-fixes/requirements.md:7.3]
    *   WHEN sections are classified THEN mnemonics SHALL be backmatter. [frontmatter-backmatter-fixes/requirements.md:7.4]
    *   WHEN sections are classified THEN bibliography SHALL be backmatter. [frontmatter-backmatter-fixes/requirements.md:7.5]
    *   WHEN frontmatter sections use reprompting THEN they SHALL follow reprompt sequence. [frontmatter-backmatter-fixes/requirements.md:7.6]

### 1.8 General System Features

**User Stories & Acceptance Criteria:**

*   **As a publisher, I want the system to automatically fill missing metadata fields using AI, so that I can generate complete LSI submissions with minimal manual input.**
    *   WHEN metadata has missing fields THEN the system SHALL use LLM to generate appropriate content. [lsi-csv-generator-project/requirements.md:2.1]
    *   WHEN using AI completion THEN the system SHALL provide fallback values if AI generation fails. [lsi-csv-generator-project/requirements.md:2.2]
    *   WHEN generating AI content THEN the system SHALL ensure all generated text meets LSI field requirements. [lsi-csv-generator-project/requirements.md:2.3]
    *   WHEN completing fields THEN the system SHALL log all AI-generated content for review. [lsi-csv-generator-project/requirements.md:2.4]
    *   WHEN AI completion is disabled THEN the system SHALL still generate valid CSV files with available data. [lsi-csv-generator-project/requirements.md:2.5]
*   **As a publisher, I want to process multiple books simultaneously, so that I can efficiently generate LSI files for entire catalogs.**
    *   WHEN provided with multiple metadata files THEN the system SHALL process them in batch. [lsi-csv-generator-project/requirements.md:4.1]
    *   WHEN batch processing THEN the system SHALL generate individual CSV files for each book. [lsi-csv-generator-project/requirements.md:4.2]
    *   WHEN batch processing THEN the system SHALL create a combined catalog CSV file. [lsi-csv-generator-project/requirements.md:4.3]
    *   WHEN processing batches THEN the system SHALL provide progress reporting and error handling. [lsi-csv-generator-project/requirements.md:4.4]
    *   WHEN batch processing fails THEN the system SHALL continue with remaining files and report failures. [lsi-csv-generator-project/requirements.md:4.5]
*   **As a publisher, I want flexible configuration options, so that I can customize the LSI generation for different imprints and publishing workflows.**
    *   WHEN configuring the system THEN the system SHALL support publisher-specific settings. [lsi-csv-generator-project/requirements.md:5.1]
    *   WHEN using configurations THEN the system SHALL support imprint-specific customizations. [lsi-csv-generator-project/requirements.md:5.2]
    *   WHEN processing books THEN the system SHALL apply tranche-specific configurations. [lsi-csv-generator-project/requirements.md:5.3]
    *   WHEN configuring fields THEN the system SHALL allow field mapping and transformation rules. [lsi-csv-generator-project/requirements.md:5.4]
    *   WHEN updating configurations THEN the system SHALL validate configuration files before use. [lsi-csv-generator-project/requirements.md:5.5]
*   **As a publisher, I want detailed reports on LSI generation results, so that I can monitor quality and identify areas for improvement.**
    *   WHEN generating CSV files THEN the system SHALL create completion reports showing field population rates. [lsi-csv-generator-project/requirements.md:6.1]
    *   WHEN processing multiple books THEN the system SHALL generate summary analytics. [lsi-csv-generator-project/requirements.md:6.2]
    *   WHEN AI completion is used THEN the system SHALL report on AI-generated content quality. [lsi-csv-generator-project/requirements.md:6.3]
    *   WHEN validation occurs THEN the system SHALL provide detailed validation reports. [lsi-csv-generator-project/requirements.md:6.4]
    *   WHEN generating reports THEN the system SHALL support multiple output formats (HTML, CSV, JSON). [lsi-csv-generator-project/requirements.md:6.5]
*   **As a developer, I want a modular system architecture, so that I can easily extend and integrate the LSI generator with other publishing tools.**
    *   WHEN designing the system THEN the system SHALL use modular, pluggable architecture. [lsi-csv-generator-project/requirements.md:7.1]
    *   WHEN extending functionality THEN the system SHALL support custom field processors. [lsi-csv-generator-project/requirements.md:7.2]
    *   WHEN integrating THEN the system SHALL provide clear API interfaces. [lsi-csv-generator-project/requirements.md:7.3]
    *   WHEN adding features THEN the system SHALL maintain backward compatibility. [lsi-csv-generator-project/requirements.md:7.4]
    *   WHEN deploying THEN the system SHALL support both standalone and integrated usage. [lsi-csv-generator-project/requirements.md:7.5]
*   **As a publisher, I want fast and reliable LSI generation, so that I can process large catalogs efficiently.**
    *   WHEN processing single books THEN the system SHALL complete generation within 30 seconds. [lsi-csv-generator-project/requirements.md:8.1]
    *   WHEN batch processing THEN the system SHALL handle 100+ books without memory issues. [lsi-csv-generator-project/requirements.md:8.2]
    *   WHEN using AI completion THEN the system SHALL implement efficient caching and rate limiting. [lsi-csv-generator-project/requirements.md:8.3]
    *   WHEN processing large datasets THEN the system SHALL provide progress indicators. [lsi-csv-generator-project/requirements.md:8.4]
    *   WHEN system resources are limited THEN the system SHALL gracefully handle resource constraints. [lsi-csv-generator-project/requirements.md:8.5]
*   **As a quality assurance user, I want detailed field completion reports, so that I can understand which fields are being completed by which strategy and identify any issues.**
    *   WHEN generating LSI CSV files THEN the system SHALL generate detailed field completion reports. [lsi-field-enhancement-phase2/requirements.md:3.1]
    *   WHEN creating field completion reports THEN the system SHALL include field name, strategy type, actual value, and source. [lsi-field-enhancement-phase2/requirements.md:3.2]
    *   WHEN creating field completion reports THEN the system SHALL support multiple output formats (CSV, HTML, JSON). [lsi-field-enhancement-phase2/requirements.md:3.3]
    *   WHEN creating HTML reports THEN the system SHALL include statistics on field population rates and strategy usage. [lsi-field-enhancement-phase2/requirements.md:3.4]
    *   WHEN creating reports THEN the system SHALL highlight empty fields and potential issues. [lsi-field-enhancement-phase2/requirements.md:3.5]
*   **As a system administrator, I want the field completion reporting to be integrated with the book pipeline, so that reports are automatically generated during batch processing.**
    *   WHEN running the book pipeline THEN the system SHALL generate field completion reports for each book. [lsi-field-enhancement-phase2/requirements.md:4.1]
    *   WHEN generating reports THEN the system SHALL save them alongside the LSI CSV files. [lsi-field-enhancement-phase2/requirements.md:4.2]
    *   WHEN generating reports THEN the system SHALL maintain backward compatibility with existing reporting. [lsi-field-enhancement-phase2/requirements.md:4.3]
    *   WHEN generating reports THEN the system SHALL handle errors gracefully and continue processing. [lsi-field-enhancement-phase2/requirements.md:4.4]
*   **As a publisher rushing books to market, I need the top IMMEDIATE priority is that running the pipeline against rows 1-12 of xynapse_traces_schedule.json must create valid fully populated complete LSI csv for those titles.** [lsi-field-enhancement-phase4/requirements.md:5]
*   **As a publisher rushing books to market, I need 100% field population with valid fields, including null valids.** [lsi-field-enhancement-phase4/requirements.md:1]
*   **As a publisher rushing books to market, I need high transparency: what is happening at each step.** [lsi-field-enhancement-phase4/requirements.md:2]
*   **As a publisher rushing books to market, I need high filterability: show me only warnings, errors, and major decisions.** [lsi-field-enhancement-phase4/requirements.md:3]
*   **As a book designer, I want clearly numbered practice pages, so that I can easily track my progress through the mnemonic exercises.**
    *   WHEN dot grid practice pages are generated THEN each page SHALL display "Mnemonic Practice {i}" at the bottom. [mnemonic-practice-layout/requirements.md:2.1]
    *   WHEN numbering practice pages THEN the system SHALL increment {i} sequentially starting from 1. [mnemonic-practice-layout/requirements.md:2.2]
    *   WHEN placing the practice label THEN the system SHALL position it in the instruction location at the bottom of the page. [mnemonic-practice-layout/requirements.md:2.3]
*   **As a book designer, I want the mnemonic practice layout to integrate with existing LaTeX templates, so that the feature works seamlessly with current book generation workflows.**
    *   WHEN generating mnemonic practice layouts THEN the system SHALL use existing dot grid generation capabilities. [mnemonic-practice-layout/requirements.md:3.1]
    *   WHEN applying the layout THEN the system SHALL maintain compatibility with current LaTeX template structure. [mnemonic-practice-layout/requirements.md:3.2]
    *   WHEN processing book content THEN the system SHALL detect mnemonic content and automatically apply the alternating layout. [mnemonic-practice-layout/requirements.md:3.3]
    *   WHEN generating the final layout THEN the system SHALL place the Mnemonics section in the back matter after the Bibliography and before any other appendixes. [mnemonic-practice-layout/requirements.md:3.4]
*   **As a content creator, I want the system to handle variable numbers of mnemonics, so that books with different amounts of mnemonic content are properly formatted.**
    *   WHEN a book contains multiple mnemonics THEN the system SHALL create the appropriate number of verso/recto page pairs. [mnemonic-practice-layout/requirements.md:4.1]
    *   WHEN processing mnemonic content THEN the system SHALL maintain proper page sequencing regardless of the total number of mnemonics. [mnemonic-practice-layout/requirements.md:4.2]
    *   WHEN generating the final layout THEN the system SHALL ensure proper page alignment for printing requirements. [mnemonic-practice-layout/requirements.md:4.3]

---

## 2. Design

### 2.1 Core System Architecture

The Codexes Factory system leverages a modular architecture, including a **LSI ACS Generator** as the central transformation engine. This generator interacts with several key components:

*   **Field Mapper**: Applies mapping strategies (Direct, Computed, Default, Conditional, LLMCompletion) to transform metadata.
*   **Validator**: Enforces rules for data formats, lengths, and LSI compliance.
*   **Config Manager**: Handles multi-level configuration (default, publisher, imprint, tranche) with inheritance and overrides.
*   **Enhanced Metadata Model**: Extends `CodexMetadata` to support all LSI-specific fields.
*   **File Manager**: Manages PDF checks and FTP staging.
*   **Reporter**: Generates detailed logs, error reports, and field completion statistics.
*   **Error Recovery Manager**: Implements strategies for correction and graceful degradation.

This architecture supports extensibility, configurability, robust validation, and comprehensive logging. [lsi-field-enhancement/design.md:Architecture]

### 2.2 LSI Field Mapping & Completion Design

*   **Field Mapping Strategy Pattern**:
    *   `DirectMappingStrategy`: 1:1 field mappings.
    *   `ComputedMappingStrategy`: Fields requiring calculation (weight, pricing, dates, file paths, physical specs).
    *   `DefaultMappingStrategy`: Fields with fallback values.
    *   `ConditionalMappingStrategy`: Fields dependent on other field values.
    *   `LLMCompletionStrategy`: Fields requiring LLM inference. [lsi-field-enhancement/design.md:Field Mapping Strategy Pattern]
*   **LLM-Based Field Completion**: Leverages `llm_caller.py` and `prompt_manager.py` for intelligent field population, including contributor bios, BISAC suggestions, and marketing copy. [lsi-field-enhancement/design.md:LLM-Based Field Completion]
    *   `LLMFieldCompleter`: Enhanced to save completions to `metadata/llm_completions` BEFORE filtering by strategies, with robust directory discovery and consistent file naming (timestamps, ISBN). [lsi-field-enhancement-phase2/design.md:Enhanced LLM Field Completer], [lsi-field-enhancement-phase4/design.md:Enhanced LLM Field Completion]
    *   `LLMCompletionStrategy`: Checks for existing completions in `metadata.llm_completions` first, then direct field value, then uses LLM if needed. Logs source of value. [lsi-field-enhancement-phase2/design.md:Enhanced LLM Completion Strategy]
    *   Enhanced LLM Prompts for fields like `generate_contributor_bio` with detailed instructions and fallback values. [lsi-field-enhancement-phase4/design.md:Enhanced LLM Field Completion Prompts]
*   **Comprehensive Default Values**: Configuration supports multi-level defaults (imprint > publisher > global). [lsi-field-enhancement-phase4/design.md:Comprehensive Default Values]
*   **Robust Field Mapping**: Enhanced `FieldMappingRegistry` with field name normalization for consistent lookup and handling of variations. [lsi-field-enhancement-phase4/design.md:Robust Field Mapping]
*   **Tranche Override Management**: `TrancheOverrideManager` applies overrides with `replace`/`append` logic, checking precedence and field types. [lsi-field-mapping-corrections/design.md:1. Tranche Override Manager]
*   **JSON Metadata Extraction**: `JSONMetadataExtractor` for Thema subjects (array handling) and age range (integer conversion, bounds checking). [lsi-field-mapping-corrections/design.md:2. JSON Metadata Extractor]
*   **Series-Aware Description Processor**: `SeriesDescriptionProcessor` for "This book" replacement with series name. [lsi-field-mapping-corrections/design.md:3. Series-Aware Description Processor]

### 2.3 Pricing System Design

*   **Unified Pricing Strategy**: `EnhancedPricingStrategy` handles all price fields, ensures decimal format without symbols, and calculates territorial prices. [lsi-pricing-fixes/design.md:1. Enhanced Pricing Strategy]
*   **Currency Formatter**: `CurrencyFormatter` utility for decimal price formatting and numeric value extraction. [lsi-pricing-fixes/design.md:2. Currency Formatter]
*   **Territorial Price Calculator**: `TerritorialPriceCalculator` for automatic EU, CA, AU price calculation from US base price, with exchange rate caching. [lsi-pricing-fixes/design.md:3. Territorial Price Calculator]
*   **Specialty Market Pricing**: Standardizes GC and other specialty market prices to equal US List Price if not configured. [lsi-pricing-fixes/design.md:4. Fix Specialty Market Pricing]
*   **Wholesale Discount Standardization**: Removes percentage symbols, ensures consistency, and defaults to 40% for all markets. [lsi-pricing-fixes/design.md:5. Standardize Wholesale Discount Formatting]
*   **Field Mapping Optimization**: Audits and eliminates duplicate pricing strategy registrations, consolidating to approximately 119 strategies. [lsi-pricing-fixes/design.md:6. Optimize Field Mapping Strategy Registration]

### 2.4 ISBN & Series Management Design

*   **ISBN Database Manager**:
    *   `ISBNDatabase`: Core class for managing database, import from Bowker spreadsheets, status tracking (available, privately assigned, publicly assigned), and CRUD operations.
    *   `ISBNAssigner`: Assigns next available ISBN.
    *   `ISBNStatusTracker`: Manages ISBN lifecycle. [lsi-field-enhancement-phase3/design.md:1. ISBN Database Manager]
*   **Series Metadata Manager**:
    *   `SeriesRegistry`: Core class for series creation, CRUD operations, and publisher isolation.
    *   `SeriesAssigner`: Assigns books to series, manages sequence numbers.
    *   `SeriesValidator`: Validates series metadata. [lsi-field-enhancement-phase3/design.md:2. Series Metadata Manager]
*   **ISBN Scheduler (`isbn_scheduler.py`)**:
    *   `ISBNScheduler`: Manages ISBN blocks, assignment scheduling, immediate assignment, reservation, updates, and reports.
    *   Data Models: `ISBNAssignment`, `ISBNBlock`, `ISBNStatus` (Enum).
    *   Persistent storage in `configs/isbn_schedule.json` with atomic writes and backups. [isbn-schedule-assignment/design.md:Core ISBN Scheduler]

### 2.5 UI & Configuration Design (Streamlit)

*   **Enhanced Configuration Manager**: Central component (`EnhancedConfigurationManager`) for multi-level config loading (default → publisher → imprint → tranche), merging, validation, and UI state management. [streamlit-ui-config-enhancement/design.md:1. Enhanced Configuration Manager]
*   **Dynamic Configuration Discovery**: `DynamicConfigurationLoader` scans directories, loads JSON, and handles validation for publisher/imprint/tranche. [streamlit-ui-config-enhancement/design.md:2. Dynamic Configuration Loader]
*   **Parameter Organization System**: `ParameterGroupManager` organizes parameters into logical, expandable groups (Core Settings, LSI, Territorial Pricing, LLM/AI, Debug/Monitoring, etc.) with help text and dependencies. [streamlit-ui-config-enhancement/design.md:3. Parameter Group Manager]
*   **Configuration Validation Framework**: `ConfigurationValidator` for real-time, cross-parameter, and LSI-specific validation. [streamlit-ui-config-enhancement/design.md:4. Build Configuration Validation Framework]
*   **Enhanced UI Components**: `ConfigurationUI` for dynamic dropdowns, input widgets with validation, expandable groups, and mandatory complete config preview. [streamlit-ui-config-enhancement/design.md:5. Create Enhanced UI Components]
*   **Command Builder and Serialization**: `CommandBuilder` converts UI config to CLI arguments, handles complex serialization, and manages temporary files. [streamlit-ui-config-enhancement/design.md:7. Build Command Builder and Serialization]
*   **Form Button Fix**: `st.button()` removed from forms, replaced with automatic configuration loading triggered by selection changes. Uses `_has_selection_changed()` and `_show_loading_feedback()`. [streamlit-form-button-fix/design.md:Overview], [streamlit-form-button-fix/design.md:Modified ConfigurationUI Methods]
*   **Runaway Fixes**: Implements `DropdownManager`, `ValidationManager`, and `StateManager` for controlled state updates, event debouncing, and atomic session state changes to prevent rerun loops. [streamlit-ui-runaway-fixes/design.md:Overview], [streamlit-ui-runaway-fixes/design.md:Components and Interfaces]
*   **Configuration Synchronization Fix**: `ConfigurationSynchronizer` automatically populates core settings fields from configuration selection, tracks user overrides, and provides visual indicators (`SynchronizedFormRenderer`). `ConfigurationAwareValidator` considers both form and config values. [config-sync-fix/design.md:Overview], [config-sync-fix/design.md:Components and Interfaces]
*   **ISBN Schedule Manager UI**: Streamlit page for ISBN scheduling, assignment management, block management, and reporting. [isbn-schedule-assignment/design.md:Streamlit User Interface]
*   **ISBN Schedule CLI**: Command-line tool for `add-block`, `schedule`, `assign`, `reserve`, `list`, `report`, and `bulk` operations. [isbn-schedule-assignment/design.md:Command Line Interface]

### 2.6 Book Production & Formatting Design

*   **Bibliography Formatting**: `BibliographyFormatter` uses memoir citation fields and applies 0.15 hanging indent. [book-production-fixes/design.md:1. Bibliography Formatting System]
*   **Typography & Layout Manager**: `TypographyManager` for consistent font (Adobe Caslon for mnemonics, Apple Myungjo for Korean on title pages), layout (instructions on every 8th recto page bottom, chapter heading leading to 36 points), and LaTeX escaping. [book-production-fixes/design.md:5. Typography and Layout Manager]
*   **Glossary Layout System**: `GlossaryLayoutManager` formats glossaries in 2 columns with Korean/English term stacking and even distribution. [book-production-fixes/design.md:6. Glossary Layout System]
*   **Publisher's Note Generator**: `PublishersNoteGenerator` creates 3-paragraph notes (max 600 chars/para) including pilsa explanation and current events references. [book-production-fixes/design.md:10. Publisher's Note Generator]
*   **Mnemonics JSON Processor**: `MnemonicsJSONProcessor` validates LLM responses for `mnemonics_data` key and creates `mnemonics.tex`. [book-production-fixes/design.md:11. Mnemonics JSON Processor]
*   **BISAC Category Analyzer**: `BISACCategoryAnalyzer` uses LLM to generate specific, relevant BISAC categories, replacing generics, and ensuring relevance. [book-production-fixes/design.md:12. BISAC Category Analyzer]
*   **Pilsa Book Content Processor**: `PilsaBookContentProcessor` ensures all descriptive content identifies the book as "pilsa" and mentions 90 quotes/journaling pages. [book-production-fixes/design.md:13. Pilsa Book Content Processor]
*   **Last Verso Page Manager**: `LastVersoPageManager` adds "Notes" chapter heading to blank last verso pages. [book-production-fixes/design.md:14. Last Verso Page Manager]
*   **Storefront Metadata Manager**: `StorefrontMetadataManager` extracts author from tranche config for `storefront_author_en/_ko` fields, preventing model interpolation and validating consistency. [book-production-fixes/design.md:16. Storefront Metadata Manager]
*   **Configuration Hierarchy Enforcement**: `ConfigurationHierarchyEnforcer` applies strict hierarchy (`default < publisher < imprint < tranche`), with `schedule.json` subtitle, tranche author/imprint always winning. [frontmatter-backmatter-fixes/design.md:1. Configuration Hierarchy Enforcer]
*   **Frontmatter Generator (Reprompting)**: `FrontmatterGenerator` for 100% LLM-generated Publisher's Note (no boilerplate), Foreword (clean Korean, no markdown), and Glossary. [frontmatter-backmatter-fixes/design.md:2. Frontmatter Generator (Reprompting System)]

### 2.7 Data Models

*   **CodexMetadata Extensions**: Adds LSI-specific fields (account info, submission methods, contributors, physical specs, publication timing, territorial rights, file paths, special fields, flex fields, publisher reference ID, marketing image). [lsi-field-enhancement/design.md:Enhanced CodexMetadata Extensions]
    *   Includes `llm_completions` to store all LLM results before filtering. [lsi-field-enhancement-phase4/design.md:Enhanced CodexMetadata]
*   **Validation Result Models**: `FieldValidationResult` (field name, valid, error/warning msg, suggested value, severity) and `ValidationResult` (overall valid, list of field results, errors, warnings). [lsi-field-enhancement/design.md:Validation Result Models]
    *   Enhanced with severity (`info`, `warning`, `error`, `critical`) and methods to filter/check critical errors. [lsi-field-enhancement-phase4/design.md:Enhanced Validation Result]
    *   `ValidationResult` (is_valid, errors, warnings, field_completeness, get_summary) and `CompletionResult` (completed_fields, confidence, fallback_used, processing_time). [lsi-csv-generator-project/design.md:Data Models]
*   **Report Data Models**: `FieldCompletionData` (field name, strategy type, value, source, is_empty, llm_value) and `ReportStatistics` (total, populated, empty fields, completion percentage, strategy/source counts). [lsi-field-enhancement-phase2/design.md:Data Models]
*   **ISBN Models**: `ISBN` (isbn, publisher_id, status, assigned_to, dates, notes) for DB management. [lsi-field-enhancement-phase3/design.md:1. ISBN Database Model]
    *   `ISBNAssignment` and `ISBNBlock` for ISBN scheduling, with `ISBNStatus` enum. [isbn-schedule-assignment/design.md:Data Models]
*   **Series Models**: `Series` (id, name, publisher_id, multi_publisher, dates) and `SeriesBook` (series_id, book_id, sequence_number). [lsi-field-enhancement-phase3/design.md:2. Series Metadata Model]
*   **Pricing Models**: `PriceConfiguration` (us_list_price, discount, territorial_rates, specialty_markets) and `PricingResult` (formatted prices). [lsi-pricing-fixes/design.md:Data Models]
*   **Tranche Configuration**: `TrancheConfig` (id, LSI account, exclude fields, BISAC override, boilerplate, pub month/year). [xynapse-tranche-1/design.md:Tranche Configuration]
    *   Extended with `field_overrides`, `append_fields`, `file_path_templates`, `blank_fields`. [lsi-field-mapping-corrections/design.md:Tranche Override Configuration]
*   **UI Configuration Models**: `ConfigurationParameter`, `ParameterGroup`, `ConfigurationState` (publisher, imprint, tranche, parameters, validation results), `ValidationResult` (is_valid, errors, warnings, param_status). [streamlit-ui-config-enhancement/design.md:Data Models]
*   **Session State for UI**: Tracks selected configs, current config, validation results, expanded groups, loading state, last load time, auto-load enabled, caches (publisher-imprints, imprint-tranches), timestamps. [streamlit-form-button-fix/design.md:Session State Structure], [streamlit-ui-runaway-fixes/design.md:Session State Structure]
*   **Config Sync State**: `ConfigSyncState` (publisher, imprint, tranche, user overrides, timestamp, sync_status for each field). [config-sync-fix/design.md:Data Models]
*   **Book Production Specific Models**:
    *   `BibliographyEntry` (author, title, publisher, year, isbn, style, indent).
    *   `ISBNCacheEntry` (isbn, title, author, pub date, lookup_timestamp, source).
    *   `ProcessingStatistics` (prompt counts, quotes, time, error details).
    *   `PublishersNote` (paragraphs, lengths, pilsa explanation).
    *   `MnemonicsData` (mnemonics_data key, acronym, expansion, explanation).
    *   `BISACCategory` (code, name, specificity, relevance, source).
    *   `StorefrontMetadata` (title, authors, source, consistency). [book-production-fixes/design.md:Data Models]
*   **PipelineConfig**: Data class for `lightning_source_account`, `language_code`, `field_reports`, `llm_config`, `fonts`. [pipeline-configuration-fixes/design.md:Configuration Schema]
*   **BookConfiguration**: Data class for hierarchy levels and final resolved values, validation status. [frontmatter-backmatter-fixes/design.md:Configuration Schema]
*   **DocumentSection**: Data class for name, section type (`frontmatter`/`backmatter`), generation method, prompt key, required, locked status. [frontmatter-backmatter-fixes/design.md:Section Classification]

---

## 3. Tasks

This section consolidates all tasks from the provided specifications, categorized by their current status. Tasks are grouped by their original directory/feature for clarity.

### 3.1 Completed Tasks

*   **LSI Field Enhancement (Initial Phase & Acceptance Test Fixes)**
    *   Extend CodexMetadata model with missing LSI-specific fields.
    *   Create field mapping strategy system (base interface, concrete strategies).
    *   Build field mapping registry.
    *   Implement LLM-based field completion system.
    *   Develop validation system (framework, specific validators, PDF/file validation).
    *   Build configuration management system (LSI config class, file structure).
    *   Enhance existing LSI ACS Generator (refactor to use new mapping, comprehensive field mapping, generation result reporting).
    *   Implement error handling and recovery (error recovery manager, comprehensive logging).
    *   Create comprehensive test suite (unit tests for components, integration tests, file system integration tests).
    *   Update existing codebase integration (metadata generation workflows, migration utilities).
    *   Documentation and examples (comprehensive documentation, sample configs/test data).
    *   Fix CSV output to include all pipeline job rows.
    *   Remove specific discount mode cell values from output.
    *   Add advanced territorial pricing strategies.
    *   Optimize field completion prompts (use full content, extract up to 3 contributors).
    *   Enhance validation with LSI-specific business rules.
*   **LSI Field Enhancement - Phase 2**
    *   Enhance LLM Field Completer for proper storage (improve directory discovery logic, enhance file naming and metadata storage).
    *   Enhance LLM Completion Strategy for CSV integration (update `map_field` to check existing completions, improve field value extraction logic).
    *   Implement Field Completion Reporter (create LSIFieldCompletionReporter class, add multiple output format support, add statistics and visualization).
    *   Integrate with Book Pipeline (update `run_book_pipeline.py` to use new reporter, add backward compatibility and error handling).
*   **LSI Field Enhancement - Phase 3**
    *   Set up ISBN Database Management System (implement core classes, develop Bowker Spreadsheet Importer, implement ISBN Assignment System, add ISBN Publication Tracking, create ISBN Database Storage Layer).
    *   Implement Series Metadata Management (create data models/storage, create Series Registry Core Classes, develop Series Assignment System, implement Multi-Publisher Series Support, create Series UI Integration, implement Series CRUD Operations).
    *   Implement Enhanced Annotation/Summary Generation.
    *   Enhance BISAC Category Field Generation.
    *   Implement Thema Subject Field Generation.
    *   Enhance Contributor Information Extraction.
    *   Implement Illustrations Field Generation.
    *   Enhance Table of Contents Generation.
    *   Update Field Mapping for Reserved Fields.
    *   Integrate ISBN Database with LSI Generator.
    *   Integrate Series Management with LSI Generator.
    *   Integrate Enhanced Field Completion with LSI Generator.
    *   Create ISBN Database Tests.
    *   Create Series Management Tests.
    *   Create Enhanced Field Completion Tests.
    *   Update LSI Field Enhancement Guide.
    *   Create API Reference Documentation.
    *   Update User Guides.
    *   Create Field Completion Reporting System (implement Field Completion Reporter, create Field Validation Framework, integrate Reporting with LSI Generator).
    *   Implement Error Recovery Manager (create Error Recovery Strategies, implement Error Logging System).
*   **LSI Field Enhancement - Phase 4**
    *   Fix LLM completion storage issue.
    *   Improve LLM field completion prompts.
    *   Implement retry logic and error handling.
    *   Implement physical specifications calculation.
    *   Implement date calculation.
    *   Implement file path generation.
    *   Implement multi-level configuration.
    *   Add imprint-specific default values.
    *   Add publisher-specific default values.
    *   Enhance global default values.
    *   Test with `xynapse_traces_schedule.json` rows 1-12.
*   **Xynapse Tranche 1**
    *   Set Lightning Source Account # to 6024045.
    *   Exclude Metadata Contact Dictionary from CSV output.
    *   Ensure Parent ISBN field is empty.
    *   Load ISBN database with real data.
    *   Assign unique ISBNs from database.
    *   Create tranche configuration system.
    *   Add rendition booktype validation.
    *   Add contributor role validation.
    *   Implement Tuesday publication date distribution.
    *   Combine LLM results with boilerplate for annotations.
    *   Strip codes from BISAC Subject fields.
    *   Add tranche BISAC Subject override.
    *   Add short description length validation.
    *   Fix truncated Thema subjects.
    *   Set GC market prices equal to US price.
*   **textbf-line-detection-fix**
    *   Create unit tests for the regex pattern.
*   **mnemonic-practice-layout**
    *   Create LaTeX template commands for mnemonic practice layout.
    *   Implement mnemonic extraction logic in prepress system.
    *   Modify prepress processing to generate alternating layout.
    *   Enhance dot grid system for instruction placement.
    *   Add comprehensive error handling and logging.
    *   Create integration tests for end-to-end processing.
    *   Evaluate and potentially refine mnemonic formatting.
    *   Update documentation and add configuration options.
*   **LLM Back Cover Text Processing**
    *   Enhance Stage 1 content generation to include back cover text generation.
*   **LSI CSV Bug Fixes**
    *   Fix remaining old-style prompts causing JSON parsing errors.
    *   Implement robust JSON response validation.
    *   Fix bibliography prompt and similar field completion issues.
    *   Improve BISAC code generation and validation.
    *   Fix description length and formatting issues.
    *   Enhance contributor information generation.
    *   Fix age range and audience determination.
    *   Fix multi-level configuration inheritance.
    *   Fix batch processing failure cascades.
    *   Implement comprehensive LSI field validation.
    *   Fix field mapping and transformation issues.
    *   Add comprehensive validation reporting.
    *   Implement retry logic for LLM failures.
    *   Enhance logging and debugging capabilities.
    *   Add comprehensive error recovery mechanisms.
    *   Fix BISAC field validation (ISSUE-015).
    *   Implement price calculations (ISSUE-016, ISSUE-017, ISSUE-018, ISSUE-019).
    *   Fix calculated spine width override (ISSUE-012).
    *   Fix contributor role validation (ISSUE-013).
    *   Implement file path generation (ISSUE-014).
    *   Set reserved fields to blank (ISSUE-020).
*   **LSI Pricing Fixes**
    *   Create Currency Formatter Utility.
    *   Create Enhanced Pricing Strategy.
*   **BISAC Category Fixes**
    *   Create enhanced BISAC category generator.
    *   Enhance BISAC validator for category names.
    *   Create specialized LLM prompts for BISAC generation.
    *   Implement unified BISAC category mapping strategy.
    *   Fix field mapping registrations.
*   **LSI Field Mapping Corrections**
    *   Create tranche override management system.
    *   Implement JSON metadata extraction utilities.
    *   Build series-aware description processor.
    *   Create enhanced field mapping strategies.
    *   Integrate tranche override system with field mapping.
    *   Update tranche configuration schema and loading.
    *   Implement comprehensive field validation.
    *   Wire new strategies into LSI generation pipeline.
    *   Create comprehensive test suite.
*   **Streamlit UI Config Enhancement**
    *   Create Enhanced Configuration Management Infrastructure.
    *   Implement Dynamic Configuration Discovery.
    *   Create Parameter Organization System.
    *   Build Configuration Validation Framework.
    *   Create Enhanced UI Components.
    *   Implement Complete Configuration Preview System.
    *   Build Command Builder and Serialization.
    *   Enhance Book Pipeline Page with Multi-Level Configuration.
    *   Implement LSI Configuration UI Components.
    *   Add LLM and AI Configuration Interface.
    *   Build Debug and Monitoring Dashboard.
    *   Implement Configuration File Management.
    *   Add Pre-Submission Validation and Inspection.
    *   Implement Configuration History and Audit Trail.
    *   Add Advanced User Experience Features.
    *   Create Configuration Management Page.
    *   Integrate Enhanced UI with Pipeline Execution.
    *   Add Comprehensive Testing and Validation.
    *   Create Documentation and Help System.
    *   Final Integration and Polish.
*   **Streamlit Form Button Fix**
    *   Remove problematic button from ConfigurationUI.
    *   Implement automatic configuration loading detection.
    *   Add automatic configuration loading logic.
    *   Enhance loading feedback and error handling.
    *   Implement configuration change preservation.
    *   Add real-time validation feedback.
    *   Test form compliance and functionality.
    *   Add performance optimizations.
*   **Streamlit UI Runaway Fixes**
    *   Create core infrastructure classes for controlled state management.
    *   Implement session state structure updates.
    *   Fix imprint dropdown refresh without rerun loops.
    *   Fix validation button runaway loop.
    *   Update ConfigurationUI to use new managers.
*   **Config Sync Fix**
    *   Implement core configuration synchronization mechanism.
    *   Enhance Book Pipeline page with configuration synchronization.
    *   Create configuration-aware validation system.
    *   Add visual indicators for synchronized fields.
    *   Implement user override functionality.
    *   Add comprehensive error handling and fallbacks.
    *   Create integration tests for configuration synchronization.
    *   Polish user experience and add real-time feedback.
*   **Book Production Fixes**
    *   Fix bibliography formatting with memoir citation fields and hanging indent.
    *   Implement ISBN lookup caching system to prevent duplicate API calls.
    *   Fix reporting accuracy for prompt success and quote retrieval statistics.
    *   Enhance error handling for quote verification and field completion failures.
    *   Implement Book Pipeline UI tranche configuration dropdown.
    *   Implement typography enhancements for professional formatting.
    *   Implement 2-column glossary layout with Korean/English term stacking.
    *   Enhance Publisher's Note generation with structured formatting.
    *   Fix mnemonics JSON generation to include required keys.
    *   Implement pilsa book identification in all content types.
    *   Implement specific BISAC category generation.
    *   Create hierarchical writing style configuration system.
    *   Optimize quote assembly to prevent excessive author repetition.
    *   Implement Notes heading for blank last verso pages.
    *   Implement ISBN barcode generation with UPC-A format.
    *   Fix storefront metadata to use accurate author information.
    *   Create comprehensive testing suite for all production fixes.
    *   Update documentation and user guides for new features.
*   **ISBN Schedule Assignment**
    *   Create core ISBN scheduler module with data models.
    *   Implement ISBN block management functionality.
    *   Develop ISBN assignment scheduling system.
    *   Create assignment management and status operations.
    *   Build assignment querying and filtering system.
    *   Develop comprehensive reporting engine.
    *   Create bulk operations and CSV processing.
    *   Develop Streamlit user interface components.
    *   Develop command-line interface tool.
    *   Write comprehensive unit tests for core scheduler.
*   **Pipeline Configuration Fixes**
    *   Fix default configuration values in Book Pipeline UI.
    *   Fix LLM configuration propagation in BackmatterProcessor.
    *   Update XynapseTracesPrepress to pass LLM configuration.
    *   Fix foreword generation LLM configuration.
    *   Fix publisher's note generation LLM configuration.
    *   Implement font configuration system in template processing.
    *   Update LaTeX template to use font variables.
    *   Validate glossary generation and formatting.
    *   Fix LaTeX escaping and command formatting issues.
    *   Implement proper bibliography formatting with hanging indents.

### 3.2 In Progress / To Do Tasks

*   **textbf-line-detection-fix**
    *   Implement the regex-based fix in prepress.py.
    *   Test the implementation with actual mnemonics content.
*   **LLM Back Cover Text Processing**
    *   Update back cover text prompt configuration.
    *   Implement back cover text generation in Stage 1 pipeline.
    *   Add validation and fallback mechanisms.
    *   Simplify cover generator to use pre-generated text.
    *   Update cover generation to handle pre-processed text.
    *   Create comprehensive tests for back cover text generation.
    *   Test full pipeline integration.
    *   Add monitoring and configuration options.
    *   Validate and optimize text quality.
*   **Cover Fixes**
    *   Implement Template Variable Substitution System (`substitute_template_variables` function, integrate into cover pipeline).
    *   Enhance Korean Text Processing (Korean-aware LaTeX escaping, update cover template).
    *   Create Comprehensive Test Suite (unit tests for substitution, Korean text; integration test for cover generation).
    *   Validate and Deploy Fixes (test with real book data, update documentation).
*   **LSI CSV Bug Fixes**
    *   Resolve tranche configuration application issues.
    *   Implement robust error handling for configuration.
    *   Improve batch processing error reporting.
    *   Optimize memory usage and performance.
    *   Create comprehensive test suite for bug fixes.
    *   Validate fixes against real LSI submissions.
    *   Performance testing and optimization.
    *   Update documentation for fixed components.
    *   Create deployment and monitoring tools.
    *   Final integration testing and validation.
*   **LSI Pricing Fixes**
    *   Implement Territorial Price Calculator.
    *   Fix Specialty Market Pricing.
    *   Standardize Wholesale Discount Formatting.
    *   Optimize Field Mapping Strategy Registration.
    *   Update Price Field Mappings.
    *   Create Comprehensive Pricing Tests.
    *   Update Configuration System.
    *   Integration and Testing.
*   **BISAC Category Fixes**
    *   Test BISAC category generation with live pipeline.
    *   Add comprehensive error handling and logging.
    *   Create unit tests for BISAC category system.
*   **LSI Field Mapping Corrections**
    *   Update existing tranche configuration files.
*   **Streamlit UI Runaway Fixes**
    *   Implement debouncing mechanisms for state updates.
    *   Create atomic session state management.
    *   Update Book Pipeline page to prevent validation loops.
    *   Add comprehensive error handling and recovery.
    *   Create unit tests for all new manager classes.
    *   Create integration tests for UI interaction flows.
    *   Implement performance optimizations and monitoring.
*   **ISBN Schedule Assignment**
    *   Build comprehensive error handling and validation.
    *   Implement data persistence and session management.
    *   Build Streamlit reporting and analytics interface.
    *   Create Streamlit bulk operations interface.
    *   Implement CLI assignment management commands.
    *   Create CLI bulk operations and advanced features.
    *   Develop integration tests for user interfaces.
    *   Create comprehensive test data and validation scenarios.
    *   Implement system integration and configuration.
    *   Finalize documentation and deployment preparation.
*   **Pipeline Configuration Fixes**
    *   Add configuration validation and error handling.
    *   Add comprehensive logging and transparency.
    *   Create integration tests for configuration fixes.
    *   Update documentation and create migration guide.
*   **Frontmatter and Backmatter Fixes**
    *   Mark bibliography formatting as LOCKED (DO NOT CHANGE).
    *   Implement configuration hierarchy enforcement.
    *   Fix ISBN display on copyright page.
    *   Fix logo font configuration.
    *   Fix glossary formatting issues.
    *   Clean up publisher's note generation.
    *   Fix foreword generation Korean formatting.
    *   Ensure mnemonics section appears.
    *   Classify sections as frontmatter vs backmatter.
    *   Implement foreword reprompting.
    *   Integrate publisher's note with reprompting.
    *   Create regression prevention system.
    *   Add comprehensive logging and monitoring.
    *   Create integration tests.
    *   Document locked components and anti-regression measures.

---

## 4. Issues, Problems, Potential Conflicts, and Regressions

This section identifies known and inferred issues, conflicts, and regressions across the development history.

### 4.1 Critical / High Priority Open Issues (from `known-issues.md` and analysis)

*   **ISSUE-003: BISAC Code Validation Failures (High Priority)**
    *   **Description**: Generated BISAC codes often invalid or outdated, causing LSI submission rejections. Examples include `BUS999999`, `ABC123456`, outdated codes.
    *   **Status**: 🟡 Open.
    *   **Context**: Despite `bisac-category-fixes` efforts (creating enhanced generator, validator, prompts, unified mapping), this fundamental issue persists from previous `lsi-csv-bug-fixes` tracking. The `bisac-category-fixes/tasks.md` has "Test BISAC category generation with live pipeline" and "Create unit tests for BISAC category system" as incomplete, suggesting the fixes are not fully validated or integrated.
*   **ISSUE-004: Description Length Violations (High Priority)**
    *   **Description**: Generated descriptions exceed LSI character limits (`short_description`: 350, `long_description`/`annotation`: 4000), leading to truncation or rejection. AI generates text without constraints.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-csv-bug-fixes` aimed to "Implement intelligent text truncation at sentence boundaries" and "Add character limit validation for all description fields", and `xynapse-tranche-1` included "Add short description length validation". The persistence as an open issue implies these fixes were either incomplete or insufficient.
*   **ISSUE-005: Configuration Inheritance Not Working (High Priority)**
    *   **Description**: Multi-level configuration (default → publisher → imprint → tranche) not applying correctly. Tranche-specific settings ignored, default values not loading, publisher overrides not applying.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-csv-bug-fixes` claimed this was "✅ Resolved" (ISSUE-R004), stating they "Fixed configuration loading order and context tracking", "Implemented proper inheritance hierarchy". However, `streamlit-ui-config-enhancement`, `streamlit-form-button-fix`, `streamlit-ui-runaway-fixes`, and `config-sync-fix` all continue to heavily address configuration loading, inheritance, and synchronization issues, implying the fix was not truly comprehensive or new issues arose. This is a significant regression/lingering problem.
*   **ISSUE-018: Some Calculated Prices Are Missing (Medium Priority)**
    *   **Description**: EU, CA, and AU prices are missing and should be calculated based on exchange rate, wiggle room, and optional special fees.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-pricing-fixes` has "Implement Territorial Price Calculator" as an incomplete task (`[ ]`), directly confirming this issue is still open.
*   **ISSUE-019: Some Replicated Prices Are Missing (Medium Priority)**
    *   **Description**: Prices for various specialty fields (e.g., UAEUSD, USBR1) are missing and should be the same as the US List Price.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-pricing-fixes` has "Fix Specialty Market Pricing" as an incomplete task (`[ ]`), directly confirming this issue is still open.
*   **ISSUE-006: Batch Processing Memory Leaks (Medium Priority)**
    *   **Description**: Memory usage increases during large batch processing, eventually causing system slowdown or crashes.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-csv-bug-fixes` claimed "Batch Processing Error Isolation" was "✅ Resolved" (ISSUE-R005), stating "Implemented error isolation" and "Enhanced error reporting". However, the task "Optimize memory usage and performance" for `lsi-csv-bug-fixes` is still `[ ]`. This indicates a potential partial fix or new regression.

### 4.2 Medium / Low Priority Open Issues

*   **ISSUE-015: One BISAC Category Per BISAC Column (Medium Priority)**
    *   **Description**: Each of the three BISAC fields must have exactly one BISAC category name.
    *   **Status**: 🟡 Open.
    *   **Context**: The `bisac-category-fixes` requirements (1.1, 1.2) aim for this, but the task to "Test BISAC category generation with live pipeline" is incomplete, indicating this is still an issue.
*   **ISSUE-007: Contributor Bio Generation Quality (Medium Priority)**
    *   **Description**: Generated contributor biographies are generic and don't reflect book content or author expertise.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-csv-bug-fixes` aimed to "Enhance contributor information generation", but this issue remains open.
*   **ISSUE-008: Age Range Validation Inconsistencies (Medium Priority)**
    *   **Description**: Age range fields sometimes contain invalid values or inconsistent ranges (`min_age: "Adult"` or `max_age: "5"` with `min_age: "18"`).
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-field-mapping-corrections` has acceptance criteria for "Age Range Extraction and Formatting" (2.1-2.5) including validation against unrealistic values, but `lsi-csv-bug-fixes` still lists this as open. This suggests that the fix in `lsi-field-mapping-corrections` might not be fully integrated or sufficient.
*   **ISSUE-013: Blank Contributor Roles Should Match Blank Contributor Names (Medium Priority)**
    *   **Description**: Sometimes, with blank Contributor Two or Three names, the codes for Contributor Role Two and Contributor Role Three are populated.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-csv-bug-fixes` claimed this was "✅ Resolved", but it also appears as a separate `ISSUE-013` with slightly different phrasing. The task "Fix contributor role validation" in `lsi-csv-bug-fixes` was marked as complete, but its continued listing implies the fix may be fragile or incomplete.
*   **ISSUE-009: Verbose Logging Performance Impact (Low Priority)**
    *   **Description**: Verbose logging mode significantly slows down processing due to excessive I/O.
    *   **Status**: 🟢 Open.
    *   **Context**: `lsi-field-enhancement-phase4` and `lsi-csv-generator-project` both address logging, with `lsi-field-enhancement-phase4` explicitly aiming for "high filterability" for system operators, but the performance impact remains.
*   **ISSUE-010: Error Messages Not User-Friendly (Medium Priority)**
    *   **Description**: Technical error messages shown to users without context or suggested fixes.
    *   **Status**: 🟢 Open.
    *   **Context**: `lsi-csv-bug-fixes` has tasks like "Implement robust error handling for configuration" and "Improve batch processing error reporting" that should improve this, but the overall issue is still listed.
*   **ISSUE-020: Fields Always Blank (Low Priority)**
    *   **Description**: Specific fields (Reserved 1-4, Custom Trim, Weight, LSI FlexFields, etc.) should always be blank.
    *   **Status**: 🟡 Open.
    *   **Context**: `lsi-field-mapping-corrections` includes a `BlankIngramPricingStrategy` and `blank_fields` configuration, which *should* address this for Ingram pricing, but the general issue for other "reserved" fields (as per ISSUE-020 description) implies it's either not fully implemented or tested across all such fields.

### 4.3 Unaddressed / Lingering Tasks (from `tasks.md` not explicitly resolved by subsequent specs)

These are tasks that were part of a plan and appear as `[ ]` (incomplete) or `[-]` (on hold/removed) in the latest relevant `tasks.md` file, and were not explicitly marked as resolved by a subsequent spec.

*   **LSI Pricing System Fixes (from `lsi-pricing-fixes/tasks.md`)**
    *   Implement Territorial Price Calculator.
    *   Fix Specialty Market Pricing.
    *   Standardize Wholesale Discount Formatting.
    *   Optimize Field Mapping Strategy Registration.
    *   Update Price Field Mappings.
    *   Create Comprehensive Pricing Tests.
    *   Update Configuration System.
    *   Integration and Testing.
*   **Streamlit UI Runaway Fixes (from `streamlit-ui-runaway-fixes/tasks.md`)**
    *   Implement debouncing mechanisms for state updates.
    *   Create atomic session state management.
    *   Update Book Pipeline page to prevent validation loops.
    *   Add comprehensive error handling and recovery.
    *   Create unit tests for all new manager classes.
    *   Create integration tests for UI interaction flows.
    *   Implement performance optimizations and monitoring.
*   **ISBN Schedule Assignment (from `isbn-schedule-assignment/tasks.md`)**
    *   Build comprehensive error handling and validation.
    *   Implement data persistence and session management.
    *   Build Streamlit reporting and analytics interface.
    *   Create Streamlit bulk operations interface.
    *   Implement CLI assignment management commands.
    *   Create CLI bulk operations and advanced features.
    *   Develop integration tests for user interfaces.
    *   Create comprehensive test data and validation scenarios.
    *   Implement system integration and configuration.
    *   Finalize documentation and deployment preparation.
*   **Pipeline Configuration Fixes (from `pipeline-configuration-fixes/tasks.md`)**
    *   Add configuration validation and error handling.
    *   Add comprehensive logging and transparency.
    *   Create integration tests for configuration fixes.
    *   Update documentation and create migration guide.
*   **Frontmatter and Backmatter Fixes (from `frontmatter-backmatter-fixes/tasks.md`)**
    *   Mark bibliography formatting as LOCKED (DO NOT CHANGE).
    *   Implement configuration hierarchy enforcement.
    *   Fix ISBN display on copyright page.
    *   Fix logo font configuration.
    *   Fix glossary formatting issues.
    *   Clean up publisher's note generation.
    *   Fix foreword generation Korean formatting.
    *   Ensure mnemonics section appears.
    *   Classify sections as frontmatter vs backmatter.
    *   Implement foreword reprompting.
    *   Integrate publisher's note with reprompting.
    *   Create regression prevention system.
    *   Add comprehensive logging and monitoring.
    *   Create integration tests.
    *   Document locked components and anti-regression measures.
*   **Cover Fixes (from `cover-fixes/tasks.md`)**
    *   All tasks related to `Template Variable Substitution System`, `Korean Text Processing`, and `Comprehensive Test Suite` are `[ ]`. This indicates the entire cover fixes initiative is incomplete.
*   **LLM Back Cover Text Processing (from `llm-back-cover-text-processing/tasks.md`)**
    *   All tasks except "Enhance Stage 1 content generation to include back cover text generation" are `[ ]`. This means LLM generation for back cover text, prompt updates, validation, fallback, cover generator simplification, testing, monitoring, and quality optimization are largely incomplete.
*   **LSI CSV Bug Fixes (from `lsi-csv-bug-fixes/tasks.md`)**
    *   Resolve tranche configuration application issues.
    *   Implement robust error handling for configuration.
    *   Improve batch processing error reporting.
    *   Optimize memory usage and performance.
    *   Create comprehensive test suite for bug fixes.
    *   Validate fixes against real LSI submissions.
    *   Performance testing and optimization.
    *   Update documentation for fixed components.
    *   Create deployment and monitoring tools.
    *   Final integration testing and validation.
*   **BISAC Category Fixes (from `bisac-category-fixes/tasks.md`)**
    *   Test BISAC category generation with live pipeline.
    *   Add comprehensive error handling and logging.
    *   Create unit tests for BISAC category system.
*   **textbf-line-detection-fix (from `textbf-line-detection-fix/tasks.md`)**
    *   Implement the regex-based fix in prepress.py.
    *   Test the implementation with actual mnemonics content.

### 4.4 Potential Conflicts & Regressions

*   **Configuration System Redundancy/Conflict**:
    *   Multiple specs (LSI Field Enhancement, LSI CSV Bug Fixes, Streamlit UI Config Enhancement, Config Sync Fix, Pipeline Config Fixes, Frontmatter/Backmatter Fixes) all deal with "configuration management," "inheritance," "overrides," and "validation." While this represents iterative improvement, it also points to a high degree of churn and potential for conflicting implementations or incomplete integration. The `ISSUE-005: Configuration Inheritance Not Working` being "resolved" then reappearing is a prime example.
    *   Specifically, `streamlit-ui-runaway-fixes` and `config-sync-fix` address core UI state management and configuration synchronization, indicating earlier "fixes" in `lsi-csv-bug-fixes` related to configuration inheritance might have been partial or caused new UI problems.
*   **BISAC Fixes Inconsistency**:
    *   `xynapse-tranche-1` implements "Strip codes from BISAC Subject fields" and "Add tranche BISAC Subject override".
    *   `bisac-category-fixes` redesigns the entire BISAC system with LLM generation, validation for full names, and diversity.
    *   `book-production-fixes` has "Implement specific BISAC category generation" to replace generic categories.
    *   The `ISSUE-003` and `ISSUE-015` in `lsi-csv-bug-fixes/known-issues.md` remain open, indicating the successive fixes might not have fully resolved the core problem or introduced new issues. There's a clear regression/incomplete fix in BISAC handling.
*   **Spine Width Calculation**:
    *   `lsi-field-enhancement` lists "physical specification fields (weight_lbs, carton_pack_quantity)" for `CodexMetadata` and `ComputedMappingStrategy` for "calculated fields (weight, pricing)".
    *   `lsi-field-enhancement-phase4` explicitly has a task "Implement physical specifications calculation".
    *   `lsi-csv-bug-fixes` has `ISSUE-012: [Calculated Spine Should Trump Configs]` as open, meaning the calculation isn't consistently overriding or is failing. This is a clear regression or unaddressed requirement.
*   **Bibliography Formatting**:
    *   `book-production-fixes` lists `Fix bibliography formatting with memoir citation fields and hanging indent` as `[x]`.
    *   `pipeline-configuration-fixes` also lists `Implement proper bibliography formatting with hanging indents` as `[x]`.
    *   However, `frontmatter-backmatter-fixes` explicitly marks `Mark bibliography formatting as LOCKED (DO NOT CHANGE)` and states "WHEN bibliography formatting works correctly THEN it SHALL be marked as "do not change"" and "Ensure memoir class hangparas format is preserved". This suggests that previous "fixes" might have been fragile or prone to regression, necessitating a "lockdown". This is a good anti-regression measure, but highlights past instability.
*   **Publisher's Note Generation**:
    *   `book-production-fixes` tasks `Enhance Publisher's Note generation with structured formatting` (`[x]`) aiming for 3 paragraphs, 600 chars max, pilsa explanation, etc.
    *   `pipeline-configuration-fixes` has `Fix publisher's note generation LLM configuration` (`[x]`).
    *   `frontmatter-backmatter-fixes` has `Clean up publisher's note generation` (`[ ]`) with acceptance criteria "Remove boilerplate paragraph attachment" and "Ensure 100% LLM generated content". This indicates that the earlier "enhancement" (adding boilerplate) might have been reversed or caused issues, leading to new tasks to remove it and ensure pure LLM generation. This is a functional reversal or regression.
*   **Foreword Generation**:
    *   `pipeline-configuration-fixes` has `Fix foreword generation LLM configuration` (`[x]`).
    *   `frontmatter-backmatter-fixes` has `Fix foreword generation Korean formatting` (`[ ]`) and `Implement foreword reprompting` (`[ ]`) with requirements to eliminate visible markdown and use proper LaTeX commands, implying previous generation was messy. This is a functional regression/incomplete fix.
*   **Mnemonics Section Generation**:
    *   `mnemonic-practice-layout` completely redesigns mnemonic layout and generation (`[x]` for all tasks).
    *   `book-production-fixes` lists `Fix mnemonics JSON generation to include required keys` (`[x]`).
    *   However, `frontmatter-backmatter-fixes` lists `Ensure mnemonics section appears` (`[ ]`) as an open task, debugging "why mnemonics section is not being created". This points to a significant regression or an intermittent failure in the mnemonic generation pipeline that wasn't fully resolved by previous efforts.
*   **Back Cover Text Processing**:
    *   `cover-fixes` attempts to fix "Back Cover Text Variable Substitution" using a substitution system (all tasks `[ ]`).
    *   `llm-back-cover-text-processing` then *replaces* this approach with LLM-based processing for back cover text, aiming to generate "clean, final text with no remaining variables" in Stage 1. However, most tasks in this spec are also `[ ]`. This indicates a significant architectural shift that is *incomplete*, and the prior fixes are likely moot or superseded but not fully implemented by the new approach.
*   **Contributor Roles**: `ISSUE-013` is listed twice in `known-issues.md` with slightly different descriptions but related to blank names and populated roles. This indicates a persistent and potentially nuanced bug that hasn't been fully resolved.
*   **File Paths**: `ISSUE-014` in `known-issues.md` states "Values for interior, cover and file paths should be filenames exactly matching the file names of the final deliverable artifacts for each." `lsi-field-mapping-corrections` has `TrancheFilePathStrategy` and "Implement comprehensive field validation" (`[x]`) which should generate and validate file paths from tranche config. This suggests the issue might be one of integration, or that the implementation isn't perfectly matching the *exact* filenames of artifacts.

### 4.5 General Observations & Recommendations

*   **High Churn in UI and Configuration**: The frequent and overlapping fixes/enhancements for Streamlit UI, configuration loading, and state management across `streamlit-ui-config-enhancement`, `streamlit-form-button-fix`, `streamlit-ui-runaway-fixes`, and `config-sync-fix` suggest a highly volatile and complex area of the codebase. A more holistic UI/State management framework from the outset might have reduced this churn.
*   **Persistent "Known Issues"**: Several critical and high-priority issues from `lsi-csv-bug-fixes/known-issues.md` (BISAC, Description Length, Pricing, Memory Leaks, Contributor Bio, Age Range) are still marked "Open" despite being addressed in subsequent "fix" specs. This indicates that the fixes were either incomplete, introduced new regressions, or the testing/validation wasn't sufficient to close them out. A rigorous regression test suite and consistent issue tracking across phases is crucial.
*   **Lack of Closure**: Many tasks across various `tasks.md` files remain `[ ]` or `[-]` without clear resolution in later documents, suggesting uncompleted work or abandoned features. This points to a need for better project management and task lifecycle tracking.
*   **Documentation Lag**: With so many changes, ensuring that documentation (user guides, API references) is up-to-date will be a significant challenge, as evidenced by `Update documentation` tasks often being at the end or left incomplete.
*   **"Top IMMEDIATE priority" vs. Reality**: `lsi-field-enhancement-phase4` states "The top IMMEDIATE priority is that running the pipeline against rows 1-12 of xynapse_traces_schedule.json must create valid fully populated complete LSI csv for those titles." However, numerous critical issues remain open (e.g., BISAC validation, pricing) that would likely prevent a "valid fully populated complete LSI csv" for *any* title, let alone the tranche. This indicates a disconnect between stated priorities and actual progress on critical path items.
*   **Testing Gaps**: While unit and integration tests are mentioned repeatedly, the persistence of bugs (and explicit incomplete test tasks) indicates testing may not be comprehensive enough or not consistently run/validated. The "Regression Prevention System" and "Anti-Regression Checklist" tasks in `frontmatter-backmatter-fixes` highlight a recognition of this problem, but they are themselves `[ ]`.

The overall impression is of an ambitious project with continuous development, but also with significant technical debt accumulation and a need for more robust integration, validation, and project closure processes.