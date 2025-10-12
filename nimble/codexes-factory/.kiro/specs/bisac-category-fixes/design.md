# Design Document

## Overview

The BISAC category system needs to be redesigned to properly populate all three BISAC category fields with full category names using LLM assistance and validation. The current system has conflicting field mappings and doesn't properly generate multiple categories.

## Architecture

### Current Issues Analysis

1. **Conflicting Field Mappings**: Multiple strategies are registered for the same BISAC fields, causing overrides
2. **Code vs Name Confusion**: Some fields return codes (PSY031000) instead of full names
3. **Single Category Generation**: Only one category is being populated instead of three
4. **Incomplete LLM Integration**: LLM completion strategies exist but aren't working properly

### Proposed Solution

Create a unified BISAC category generation system that:
- Uses LLM to generate multiple relevant categories
- Validates all categories against current BISAC standards
- Properly formats categories as full names without codes
- Handles fallbacks gracefully

## Components and Interfaces

### 1. Enhanced BISAC Category Strategy

```python
class EnhancedBISACCategoryStrategy(MappingStrategy):
    """
    Unified strategy for generating and validating BISAC categories.
    Generates up to 3 relevant categories using LLM assistance with tranche overrides.
    """
    
    def __init__(self, category_number: int, llm_completer, bisac_validator):
        self.category_number = category_number  # 1, 2, or 3
        self.llm_completer = llm_completer
        self.bisac_validator = bisac_validator
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Check for tranche config override for primary category
        # Generate all categories at once with diversity requirements
        # Return the requested category number
        pass
```

### 2. BISAC Category Generator

```python
class BISACCategoryGenerator:
    """
    Generates multiple BISAC categories using LLM assistance and validation.
    Supports tranche overrides and ensures diversity across top-level categories.
    """
    
    def generate_categories(self, metadata: CodexMetadata, context: MappingContext, max_categories: int = 3) -> List[str]:
        # Check for tranche config override for primary category
        # Use LLM to generate categories based on book metadata
        # Ensure at least 2 categories from different top-level categories
        # Validate each category against BISAC standards
        # Return full category names (not codes)
        pass
    
    def apply_tranche_override(self, context: MappingContext) -> Optional[str]:
        # Check tranche config for BISAC category override
        # Validate override category
        # Return override category if valid
        pass
    
    def ensure_category_diversity(self, categories: List[str]) -> List[str]:
        # Analyze top-level categories (BUS, SEL, COM, etc.)
        # Reorder/replace to maximize diversity
        # Prefer categories from different top-levels
        pass
    
    def validate_and_format_category(self, category: str) -> Optional[str]:
        # Validate category against BISAC standards
        # Convert code to full name if needed
        # Return formatted category name
        pass
```

### 3. Updated BISAC Validator

Enhance the existing `BISACValidator` to:
- Support category name validation (not just codes)
- Provide category name lookup from codes
- Suggest similar category names

### 4. LLM Prompt Enhancement

Create specialized prompts for BISAC category generation:
- Analyze book title, subtitle, description, and keywords
- Generate 3 most relevant BISAC categories with diversity preference
- Prioritize categories from different top-level categories (BUS, SEL, COM, etc.)
- Return full category names in proper format
- Rank by relevance to book content while maintaining diversity
- Handle cases where tranche override is already specified

## Data Models

### BISAC Category Result

```python
@dataclass
class BISACCategoryResult:
    """Result of BISAC category generation."""
    categories: List[str]  # Full category names
    primary_category: str  # Most relevant category (may be tranche override)
    confidence_scores: List[float]  # Confidence for each category
    validation_results: List[BISACValidationResult]
    top_level_categories: List[str]  # Top-level prefixes (BUS, SEL, COM, etc.)
    diversity_score: float  # Measure of category diversity
    tranche_override_used: bool = False
    fallback_used: bool = False
```

### Enhanced Metadata Fields

Ensure metadata supports:
- `bisac_category_1`: Primary BISAC category (full name)
- `bisac_category_2`: Secondary BISAC category (full name)  
- `bisac_category_3`: Tertiary BISAC category (full name)
- `bisac_codes`: Original codes for reference

## Error Handling

### Validation Failures
- If generated category is invalid, use validator suggestions
- If no valid suggestions, use fallback categories
- Log all validation failures with details

### LLM Generation Failures
- Retry with simplified prompt
- Use existing metadata BISAC information as fallback
- Use safe default categories if all else fails

### Fallback Strategy
1. Apply tranche config override if specified
2. Use existing metadata BISAC information
3. Generate categories based on title/description keywords with diversity preference
4. Use safe default categories from different top-levels: "GENERAL", "BUSINESS & ECONOMICS", "REFERENCE"

## Testing Strategy

### Unit Tests
- Test BISAC category generation with various book types
- Test validation against current BISAC standards
- Test fallback strategies for edge cases
- Test category name formatting and code conversion

### Integration Tests
- Test full pipeline with BISAC category generation
- Verify all three category fields are populated
- Test with books that have existing BISAC information
- Test with books that need LLM generation

### Validation Tests
- Test against complete BISAC 2024 standards database
- Test category name to code conversion
- Test invalid category handling
- Test fallback category selection

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `EnhancedBISACCategoryStrategy` class
2. Create `BISACCategoryGenerator` class
3. Enhance `BISACValidator` with name validation
4. Create specialized LLM prompts

### Phase 2: Field Mapping Integration
1. Remove conflicting BISAC field registrations
2. Register new enhanced strategies for all three fields
3. Update field mapping configuration
4. Test field population

### Phase 3: Validation and Testing
1. Implement comprehensive test suite
2. Test with real book data
3. Validate against BISAC standards
4. Performance optimization

### Phase 4: Error Handling and Logging
1. Implement robust error handling
2. Add detailed logging for debugging
3. Create monitoring for category generation quality
4. Document troubleshooting procedures