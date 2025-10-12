# Design Document

## Overview

This design addresses six specific field mapping corrections in the LSI CSV generation system. The solution involves enhancing the existing field mapping strategies, adding new data extraction utilities, implementing tranche override logic, and ensuring proper field validation and formatting.

## Architecture

The corrections will be implemented through modifications to existing components in the LSI field mapping system:

- **Field Mapping Registry**: Enhanced to support tranche override precedence
- **Data Extraction Utilities**: New utilities for JSON metadata parsing
- **Field Mapping Strategies**: Updated strategies for specific field types
- **Validation Layer**: Enhanced validation for extracted data

## Components and Interfaces

### 1. Tranche Override Manager

**Location**: `src/codexes/modules/distribution/tranche_override_manager.py`

```python
class TrancheOverrideManager:
    def apply_overrides(self, field_name: str, llm_value: str, tranche_value: str, 
                       field_type: str = "replace") -> str:
        """Apply tranche overrides with support for append operations"""
        
    def is_append_field(self, field_name: str) -> bool:
        """Check if field should append rather than replace"""
        
    def should_override(self, tranche_value: Any) -> bool:
        """Determine if tranche value should override LLM value"""
```

### 2. JSON Metadata Extractor

**Location**: `src/codexes/modules/distribution/json_metadata_extractor.py`

```python
class JSONMetadataExtractor:
    def extract_thema_subjects(self, metadata: dict) -> List[str]:
        """Extract up to 3 thema subject codes from metadata"""
        
    def extract_age_range(self, metadata: dict) -> Tuple[Optional[int], Optional[int]]:
        """Extract and validate min/max age values"""
        
    def validate_age_value(self, age: Any) -> Optional[int]:
        """Validate and convert age value to integer"""
```

### 3. Series-Aware Description Processor

**Location**: `src/codexes/modules/distribution/series_description_processor.py`

```python
class SeriesDescriptionProcessor:
    def process_description(self, description: str, series_name: Optional[str]) -> str:
        """Process description to include series reference when applicable"""
        
    def has_series_context(self, series_name: Optional[str]) -> bool:
        """Check if series name is valid and should be included"""
```

### 4. Enhanced Field Mapping Strategies

**Modifications to**: `src/codexes/modules/distribution/enhanced_field_mappings.py`

New strategies will be added:
- `ThemaSubjectStrategy`: Extract and map thema subjects
- `AgeRangeStrategy`: Extract and validate age ranges  
- `SeriesAwareDescriptionStrategy`: Process series-aware descriptions
- `BlankIngramPricingStrategy`: Ensure specific pricing fields remain blank
- `TrancheFilePathStrategy`: Generate file paths from tranche configuration

## Data Models

### Tranche Override Configuration

```python
@dataclass
class TrancheOverrideConfig:
    field_overrides: Dict[str, Any]
    append_fields: List[str]  # Fields that append rather than replace
    file_path_templates: Dict[str, str]
    
@dataclass
class FieldOverrideResult:
    final_value: str
    override_applied: bool
    override_type: str  # "replace", "append", "none"
```

### Metadata Extraction Results

```python
@dataclass
class ThemaExtractionResult:
    subject_1: Optional[str]
    subject_2: Optional[str] 
    subject_3: Optional[str]
    warnings: List[str]

@dataclass
class AgeRangeResult:
    min_age: Optional[int]
    max_age: Optional[int]
    validation_errors: List[str]
```

## Error Handling

### Validation and Recovery

1. **Thema Subject Validation**:
   - Validate thema codes against known formats
   - Log warnings for invalid codes
   - Skip invalid entries, continue with valid ones

2. **Age Range Validation**:
   - Ensure values are numeric and within reasonable bounds (0-150)
   - Log validation errors for out-of-range values
   - Default to empty when validation fails

3. **Series Name Validation**:
   - Check for non-empty, non-null series names
   - Handle edge cases where series name contains special characters

4. **File Path Validation**:
   - Sanitize file paths according to LSI requirements
   - Remove or replace invalid characters
   - Ensure paths don't exceed length limits

### Error Recovery Strategies

- **Graceful Degradation**: When extraction fails, fall back to existing values
- **Partial Success**: Process valid data even when some fields fail validation
- **Comprehensive Logging**: Log all validation issues with context for debugging

## Testing Strategy

### Unit Tests

1. **Tranche Override Tests**:
   - Test replace vs append behavior
   - Test precedence rules
   - Test edge cases (null, empty values)

2. **JSON Extraction Tests**:
   - Test thema subject extraction with various array sizes
   - Test age range extraction with valid/invalid values
   - Test malformed JSON handling

3. **Series Description Tests**:
   - Test "This book" replacement logic
   - Test edge cases (no series, empty series)
   - Test descriptions without "This book"

4. **Field Mapping Tests**:
   - Test new strategies with sample data
   - Test integration with existing mapping system
   - Test blank field enforcement for Ingram pricing

### Integration Tests

1. **End-to-End Pipeline Tests**:
   - Test complete LSI generation with corrected mappings
   - Verify all six corrections work together
   - Test with real book metadata samples

2. **Configuration Tests**:
   - Test tranche configuration loading
   - Test override precedence in multi-level configs
   - Test file path template processing

### Performance Tests

1. **Extraction Performance**:
   - Benchmark JSON parsing and extraction
   - Test with large metadata objects
   - Ensure no significant performance regression

## Implementation Plan

### Phase 1: Core Infrastructure
- Implement TrancheOverrideManager
- Implement JSONMetadataExtractor
- Add unit tests for core utilities

### Phase 2: Field Strategies
- Implement new field mapping strategies
- Update existing strategies to use tranche overrides
- Add strategy-specific tests

### Phase 3: Integration
- Integrate new components with existing LSI generator
- Update field mapping registry
- Add integration tests

### Phase 4: Validation and Polish
- Implement comprehensive validation
- Add error recovery mechanisms
- Performance testing and optimization

## Configuration Changes

### Tranche Configuration Schema

```json
{
  "field_overrides": {
    "Series Name": "Transcriptive Meditation",
    "annotation_boilerplate": " This series explores..."
  },
  "append_fields": ["annotation_boilerplate"],
  "file_path_templates": {
    "interior": "interior/{title_slug}_interior.pdf",
    "cover": "covers/{title_slug}_cover.pdf"
  },
  "blank_fields": [
    "US-Ingram-Only* Suggested List Price (mode 2)",
    "US-Ingram-Only* Wholesale Discount % (Mode 2)",
    "US - Ingram - GAP * Suggested List Price (mode 2)",
    "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
    "SIBI - EDUC - US * Suggested List Price (mode 2)",
    "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
  ]
}
```

## Backward Compatibility

All changes will maintain backward compatibility:
- Existing field mappings continue to work unchanged
- New functionality is additive, not replacing existing logic
- Configuration changes are optional with sensible defaults
- Existing tranche configurations remain valid