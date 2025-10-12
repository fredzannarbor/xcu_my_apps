# LSI CSV Generation - Known Issues

## Overview

This document tracks specific, reproducible issues in the LSI CSV generation system. Each issue includes reproduction steps, error details, and current status.

## Critical Issues (Blocking Production)

### ISSUE-001: Bibliography Prompt JSON Parsing Error
**Status**: ✅ Resolved  
**Priority**: Critical  
**Component**: LLM Field Completion  
**Discovered**: 2025-07-28  
**Resolved**: 2025-07-28  

**Description**: Bibliography prompt returns conversational text instead of JSON, causing parsing failures.

**Error Message**:
```
2025-07-28 07:00:53,785 - ERROR - codexes.core.llm_caller._parse_llm_response:31 - Failed to decode JSON from response: Expecting value: line 1 column 1 (char 0). Raw content: I apologize, but the quotes containing the source citations were not provided. To create the bibliography, I need the text of the quotes so I can identify and extract the cited sources. Please provide...
```

**Root Cause**: Old-style prompt format without proper JSON enforcement

**Solution**: 
- Converted bibliography_prompt to modern messages format
- Added explicit JSON enforcement in system message
- Implemented robust JSON parsing with multiple fallback strategies

**Fix Status**: ✅ Resolved - Prompt modernized and JSON parsing enhanced

---

### ISSUE-002: Old-Style Prompts Causing JSON Failures
**Status**: ✅ Resolved  
**Priority**: Critical  
**Component**: Prompt System  
**Discovered**: 2025-07-28  
**Resolved**: 2025-07-28  

**Description**: Multiple prompts using old "prompt" format instead of "messages" format, causing inconsistent JSON responses.

**Affected Prompts**:
- `bibliography_prompt`
- `gemini_get_basic_info`
- `bibliographic_key_phrases`
- `custom_transcription_note_prompt`
- `storefront_get_*` prompts

**Solution**:
- Created prompt modernization utility
- Converted all old-style prompts to messages format
- Added JSON enforcement to all system messages
- Implemented comprehensive testing framework

**Fix Status**: ✅ Resolved - All prompts converted to modern format

---

## High Priority Issues

### ISSUE-003: BISAC Code Validation Failures
**Status**: 🟡 Open  
**Priority**: High  
**Component**: Field Validation  

**Description**: Generated BISAC codes often invalid or outdated, causing LSI submission rejections.

**Examples of Invalid Codes**:
- `BUS999999` (non-existent category)
- `ABC123456` (invalid format)
- Outdated codes from previous BISAC versions

**Impact**: LSI submissions rejected due to invalid subject classification

**Reproduction Steps**:
1. Generate LSI CSV with AI field completion
2. Check BISAC codes against current BISAC database
3. Many codes fail validation

---
### ISSUE-015: One BISAC Category Per BISAC Column
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Validation

**Description**: Each of the three BISAC fields -- BISAC Category, BISAC Category 2, and BISAC Category 3 -- shall have exactly one BISAC category name.

### ISSUE-004: Description Length Violations
**Status**: 🟡 Open  
**Priority**: High  
**Component**: Field Completion  

**Description**: Generated descriptions exceed LSI character limits, causing truncation or rejection.

**Field Limits**:
- `short_description`: 350 characters
- `long_description`: 4000 characters
- `annotation`: 4000 characters

**Current Behavior**: AI generates text without length constraints, leading to truncated submissions

---
### ISSUE-016: Price Calculations Missing
**Status**: 🟡 Open  
**Priority**: High  
**Component**: Field Completion  

---
### ISSUE-017: Prices Are Two-Decimal Floats
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Completion  

**Description**: all prices, including USD and non-USD prices, should be two-decimal floats with no currency sign, just the numeral.
---
### ISSUE-018: Some Calculated Prices Are Missing
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Completion  

**Description**: EU, CA, and AU prices are missing and should be calculated based on method that includes exchange rate, wiggle room, and optional special fees.

### ISSUE-019: Some Replicated Prices Are Missing
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Completion  

**Description**: Prices for the following fields are missing and should be the same as the US List Price.
UAEUSD Suggested List Price (mode 2)
USBR1 Suggested List Price (mode 2)
USCN1 Suggested List Price (mode 2)
USDE1 Suggested List Price (mode 2)
USIN1 Suggested List Price (mode 2)
USJP2 Suggested List Price(mode 2)
USKR1 Suggested List Price (mode 2)
USPL1 Suggested List Price (mode 2)
USRU1 Suggested List Price (mode 2)

### ISSUE-005: Configuration Inheritance Not Working
**Status**: 🟡 Open  
**Priority**: High  
**Component**: Configuration System  

**Description**: Multi-level configuration (default → publisher → imprint → tranche) not applying correctly.

**Symptoms**:
- Tranche-specific settings ignored
- Default values not loading
- Publisher overrides not applying

**Impact**: Books processed with incorrect settings, affecting metadata quality

---

### ISSUE-012: [Calculated Spine Should Trump Configs]
**Status**: 🔴 Open / 🟡 In Progress / ✅ Resolved  
**Priority**: Critical / High / Medium / Low  
**Component**: [System Component]  
**Discovered**: [Date]  
**Assigned**: [Developer]  

**Description**: Calculated spine width should always override configured. There is no value to setting configured spine width since there must always be a calculation using actual rendition type and page count.

### ISSUE-014: File paths
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Batch Processing  

**Description**: Values for interior, cover and file paths should be filenames exactly matching the file names of the final deliverable artifacts for each.

### ISSUE-006: Batch Processing Memory Leaks
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Batch Processing  

**Description**: Memory usage increases during large batch processing, eventually causing system slowdown or crashes.

**Reproduction**:
1. Process 50+ books in batch mode
2. Monitor memory usage over time
3. Memory usage grows without being released

**Impact**: Cannot process large catalogs reliably

---

### ISSUE-007: Contributor Bio Generation Quality
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Completion  

**Description**: Generated contributor biographies are generic and don't reflect book content or author expertise.

**Current Output Example**:
```
"A respected expert in the field with extensive knowledge and experience."
```

**Desired Output**: Contextual bio based on book content and subject matter for newly encountered authors for this imprint, OR defined standard bio for repeated authors, such as AI Lab For Book-Lovers

---

### ISSUE-008: Age Range Validation Inconsistencies
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Validation  

**Description**: Age range fields sometimes contain invalid values or inconsistent ranges.

**Invalid Examples**:
- `min_age: "Adult"` (should be numeric)
- `max_age: "5"` with `min_age: "18"` (inverted range)
- Non-standard age values

---

### ISSUE-013: Blank Contributor Roles ShouldMatch Blank Contributor names
**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Validation  

**Description**: 1) Sometimes with blank Contributor Two or Three, the codes for Contributor Role Two and Contributor Role Three are populated.

**Desired Output**: if Contributor Two or Three are blank, the corresponding Contributor Two and Three Roles should also be blank.

---
---

### ISSUE-013: Contributor Roles Should Match Interior of Book, Be Accurate, and Be Valid

**Status**: 🟡 Open  
**Priority**: Medium  
**Component**: Field Validation  

**Description**: 1) Sometimes with blank Contributor Two or Three, the codes for Contributor Role Two and Contributor Role Three are populated.

**Desired Output**: if Contributor Two or Three are blank, the corresponding Contributor Two and Three Roles should also be blank.


## Low Priority Issues

### ISSUE-009: Verbose Logging Performance Impact
**Status**: 🟢 Open  
**Priority**: Low  
**Component**: Logging System  

**Description**: Verbose logging mode significantly slows down processing due to excessive I/O.

**Impact**: Development and debugging workflows are slower than necessary

---

### ISSUE-010: Error Messages Not User-Friendly
**Status**: 🟢 Open  
**Priority**: Medium
**Component**: Error Handling  

**Description**: Technical error messages shown to users without context or suggested fixes.

**Example**:
```
AttributeError: 'NoneType' object has no attribute 'get'
```

**Desired**: "Missing required field 'title' in book metadata. Please check your input file."

---

### ISSUE-020: Fields Always Blank
**Status**: 🟡 Open  
**Priority**: Low  
**Component**: Field Completion  

**Description**: The following fields should always be blank in current xynapse_traces workflow:

Reserved 1
Reserved 2
Reserved 3
Reserved 4
Custom Trim Width (inches)
Custom Trim Height (inches)
Weight(Lbs)
Reserved5
Reserved6
Reserved7
Reserved8
Interior Path / Filename
Cover Path / Filename
Annotation / Summary
Reserved (Special Instructions)
LSI Special Category  (please consult LSI before using
Stamped Text LEFT
Stamped Text CENTER
Stamped Text RIGHT
LSI FlexField1 (please consult LSI before using)
LSI FlexField2 (please consult LSI before using)
LSI FlexField3 (please consult LSI before using)
LSI FlexField4 (please consult LSI before using)
LSI FlexField5 (please consult LSI before using)
Reserved11
Reserved12
Reserved9
Reserved10

## Resolved Issues

### ISSUE-R001: JSON Response Validation Enhanced
**Status**: ✅ Resolved  
**Priority**: Critical  
**Component**: LLM Response Processing  
**Resolved**: 2025-07-28  

**Description**: Enhanced JSON parsing with multiple fallback strategies to handle malformed LLM responses.

**Solution**: 
- Implemented 4-tier JSON parsing strategy
- Added conversational response parsing
- Enhanced error logging with fallback indicators
- Added JSON extraction from markdown/mixed content

### ISSUE-R002: BISAC Code Validation System
**Status**: ✅ Resolved  
**Priority**: High  
**Component**: Field Validation  
**Resolved**: 2025-07-28  

**Description**: Created comprehensive BISAC code validation and suggestion system.

**Solution**:
- Built current BISAC codes database (2024 standards)
- Implemented format validation and correction suggestions
- Added keyword-based BISAC code suggestions
- Created fallback codes for failed generation

### ISSUE-R003: Text Formatting and Length Validation
**Status**: ✅ Resolved  
**Priority**: High  
**Component**: Field Completion  
**Resolved**: 2025-07-28  

**Description**: Enhanced text formatting with intelligent truncation and validation.

**Solution**:
- Created LSI text formatter with field-specific limits
- Implemented intelligent truncation at sentence boundaries
- Added HTML annotation formatting
- Enhanced keyword formatting and deduplication

### ISSUE-R004: Multi-Level Configuration System
**Status**: ✅ Resolved  
**Priority**: High  
**Component**: Configuration System  
**Resolved**: 2025-07-28  

**Description**: Fixed configuration inheritance and loading issues.

**Solution**:
- Fixed configuration loading order and context tracking
- Implemented proper inheritance hierarchy
- Added configuration debugging utilities
- Enhanced error handling for missing config files

### ISSUE-R005: Batch Processing Error Isolation
**Status**: ✅ Resolved  
**Priority**: High  
**Component**: Batch Processing  
**Resolved**: 2025-07-28  

**Description**: Enhanced batch processing with error isolation and recovery.

**Solution**:
- Implemented error isolation for individual book processing
- Added comprehensive batch processing statistics
- Enhanced error reporting and logging
- Maintained CSV structure even with failed books

### ISSUE-R006: Enhanced LLM Retry Logic
**Status**: ✅ Resolved  
**Priority**: Medium  
**Component**: LLM Integration  
**Resolved**: 2025-07-28  

**Description**: Improved LLM call reliability with enhanced retry mechanisms.

**Solution**:
- Added intelligent retry logic for different error types
- Implemented exponential backoff with maximum delay limits
- Enhanced error classification for retryable vs non-retryable errors
- Added network and timeout error handling

---

## Issue Tracking Template

### ISSUE-XXX: [Issue Title]
**Status**: 🔴 Open / 🟡 In Progress / ✅ Resolved  
**Priority**: Critical / High / Medium / Low  
**Component**: [System Component]  
**Discovered**: [Date]  
**Assigned**: [Developer]  

**Description**: [Detailed description of the issue]

**Error Message** (if applicable):
```
[Exact error message or log output]
```

**Reproduction Steps**:
1. [Step 1]
2. [Step 2]
3. [Expected vs Actual behavior]

**Root Cause**: [Analysis of why this happens]

**Impact**: [Business/technical impact]

**Fix Status**: [Current status and any attempted solutions]

**Related Issues**: [Links to related issues]

---

## Status Legend

- 🔴 **Open**: Issue identified, not yet started
- 🟡 **In Progress**: Actively being worked on
- ✅ **Resolved**: Issue fixed and verified
- ⏸️ **Blocked**: Cannot proceed due to dependencies
- 🔄 **Testing**: Fix implemented, undergoing testing

## Priority Definitions

- **Critical**: Blocks production use, causes system failures
- **High**: Significantly impacts functionality or data quality
- **Medium**: Affects user experience or system efficiency
- **Low**: Minor issues, cosmetic problems, or nice-to-have improvements