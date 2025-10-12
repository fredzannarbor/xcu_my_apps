# Design Document

## Overview

The LSI ACS Implementation will transform the current LSI ACS Generator from a basic field mapper to a comprehensive, configurable system that handles all 100+ LSI template fields. The design focuses on extensibility, validation, and maintainability while ensuring LSI submission compliance.

The enhancement will introduce a layered architecture with field mapping strategies, validation pipelines, and configuration management to support diverse publishing scenarios and territorial requirements.

The classes share some information with other existing classes and objects such as CodexesMetadata and the values should be consistent unless explicitly allowed.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    LSI ACS Generator                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Field Mapper  │  │   Validator     │  │  Config     │ │
│  │   - Strategy    │  │   - Rules       │  │  - Defaults │ │
│  │   - Transform   │  │   - Formats     │  │  - Overrides│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Enhanced        │  │  File Manager   │  │  Reporter   │ │
│  │ Metadata Model  │  │  - PDF Check    │  │  - Logging  │ │
│  │ - LSI Fields    │  │  - FTP Stage    │  │  - Errors   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Field Mapping Strategy Pattern

The system will use a strategy pattern to handle different field mapping approaches:

- **DirectMappingStrategy**: Simple 1:1 field mappings
- **ComputedMappingStrategy**: Fields requiring calculation or transformation
- **DefaultMappingStrategy**: Fields with fallback values
- **ConditionalMappingStrategy**: Fields dependent on other field values
- **LLMCompletionStrategy**: Fields requiring LLM inference using existing litellm infrastructure

### LLM-Based Field Completion

The system will leverage the existing `llm_caller.py` and `prompt_manager.py` infrastructure to intelligently populate missing LSI fields:

```python
class LLMFieldCompleter:
    def __init__(self, llm_caller: LLMCaller, prompt_manager: PromptManager)
    def complete_missing_fields(self, metadata: CodexMetadata) -> CodexMetadata
    def generate_contributor_bio(self, author: str, title: str) -> str
    def suggest_bisac_codes(self, title: str, summary: str) -> List[str]
    def generate_marketing_copy(self, metadata: CodexMetadata) -> Dict[str, str]
```

This approach will use targeted prompts to fill gaps in metadata, particularly for:
- Contributor biographies and affiliations
- Enhanced descriptions and marketing copy
- BISAC code suggestions
- Territorial market analysis

## Components and Interfaces

### Enhanced LSI ACS Generator

```python
class EnhancedLsiAcsGenerator(BaseGenerator):
    def __init__(self, template_path: str, config_path: Optional[str] = None)
    def generate(self, metadata: CodexMetadata, output_path: str, **kwargs)
    def validate_submission(self, metadata: CodexMetadata) -> ValidationResult
    def generate_with_validation(self, metadata: CodexMetadata, output_path: str) -> GenerationResult
```

### Field Mapping System

```python
class FieldMappingRegistry:
    def register_strategy(self, field_name: str, strategy: MappingStrategy)
    def get_mapping_for_field(self, field_name: str) -> MappingStrategy
    def apply_all_mappings(self, metadata: CodexMetadata, headers: List[str]) -> List[str]

class MappingStrategy(ABC):
    @abstractmethod
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str

class DirectMappingStrategy(MappingStrategy):
    def __init__(self, metadata_field: str, default_value: str = "")

class ComputedMappingStrategy(MappingStrategy):
    def __init__(self, computation_func: Callable[[CodexMetadata], str])
```

### Validation System

```python
class LSIValidationPipeline:
    def __init__(self, validators: List[FieldValidator])
    def validate(self, metadata: CodexMetadata) -> ValidationResult
    def validate_field(self, field_name: str, value: str) -> FieldValidationResult

class FieldValidator(ABC):
    @abstractmethod
    def validate(self, field_name: str, value: str, metadata: CodexMetadata) -> FieldValidationResult

class ISBNValidator(FieldValidator):
class PricingValidator(FieldValidator):
class DateValidator(FieldValidator):
class BISACValidator(FieldValidator):
class PDFValidator(FieldValidator):
```

### Configuration Management

```python
class LSIConfiguration:
    def __init__(self, config_path: Optional[str] = None)
    def get_default_value(self, field_name: str) -> str
    def get_field_override(self, field_name: str) -> Optional[str]
    def get_imprint_config(self, imprint: str) -> Dict[str, str]
    def get_territorial_config(self, territory: str) -> Dict[str, str]

# Configuration file structure (YAML)
defaults:
  publisher: "Nimble Books LLC"
  imprint: "Xynapse Traces"
  rendition_booktype: "Perfect Bound"
  
field_overrides:
  lightning_source_account: "6024045"
  cover_submission_method: "FTP"
  
imprint_configs:
  "Xynapse Traces":
    publisher: "Nimble Books LLC"
    us_wholesale_discount: "40"
    returnability: "Yes-Destroy"
    
territorial_configs:
  UK:
    wholesale_discount_percent: "40"
  EU:
    wholesale_discount_percent: "40"
    returnability: "Yes-Destroy"

and so on for all other territories

Note: the system must support multiple configurable publishers and imprints. Store as json files in publishers/ and imprints/ directories.

```

## Data Models

### Enhanced CodexMetadata Extensions

The existing CodexMetadata class will be extended with additional fields to support all LSI requirements:

```python
@dataclass
class CodexMetadata:
    # ... existing fields ...
    
    # LSI Account and Submission Information
    lightning_source_account: str = "" 
    metadata_contact_dictionary: dict = {} to come
    parent_isbn: str = ""
    cover_submission_method: str = "FTP"  # FTP, Email, Portal
    text_block_submission_method: str = "FTP"
    
    # Enhanced Contributor Information
    contributor_one_bio: str = ""
    contributor_one_affiliations: str = ""
    contributor_one_professional_position: str = ""
    contributor_one_location: str = ""
    contributor_one_location_type_code: str = "" # lookup table
    contributor_one_prior_work: str = ""
    
    # Physical Specifications
    weight_lbs: str = "" # calculate
    carton_pack_quantity: str = "1"
    
    # Publication Timing
    street_date: str = ""  # Different from pub_date
    
    # Territorial Rights
    territorial_rights: str = "World" # default.  Alternatives should be validated against lookup table.
    
    # Edition Information
    edition_number: str = ""
    edition_description: str = "" 
    
    # File Paths for Submission
    jacket_path_filename: str = ""
    interior_path_filename: str = ""
    cover_path_filename: str = ""
    
    # Special LSI Fields

    lsi_special_category: str = ""
    stamped_text_left: str = ""
    stamped_text_center: str = ""
    stamped_text_right: str = ""
    order_type_eligibility: str = ""
    
    # LSI Flex Fields (5 configurable fields)
    lsi_flexfield1: str = ""
    lsi_flexfield2: str = ""
    lsi_flexfield3: str = ""
    lsi_flexfield4: str = ""
    lsi_flexfield5: str = ""
    
    # Publisher Reference
    publisher_reference_id: str = "" # safe folder name for digital artifacts
    
    # Marketing
    marketing_image: str = "" # path to artifact created during production
```

### Validation Result Models

```python
@dataclass
class FieldValidationResult:
    field_name: str
    is_valid: bool
    error_message: str = ""
    warning_message: str = ""
    suggested_value: str = ""

@dataclass
class ValidationResult:
    is_valid: bool
    field_results: List[FieldValidationResult]
    errors: List[str]
    warnings: List[str]
    
    def get_errors_by_field(self, field_name: str) -> List[str]
    def has_blocking_errors(self) -> bool

@dataclass
class GenerationResult:
    success: bool
    output_path: str
    validation_result: ValidationResult
    populated_fields_count: int
    empty_fields_count: int
    generation_timestamp: str
```

## Error Handling

### Validation Error Categories

1. **Blocking Errors**: Prevent LSI submission
   - Invalid ISBN format
   - Missing required fields (Title, ISBN, Publisher)
   - Invalid date formats
   - PDF validation failures
   - Invalid trim sizes or paper weights
   - Empty pricing fields for territories

2. **Information Notices**: Optimization suggestions
   - Default values used
   - Fields auto-calculated
   - Recommended field population

### Error Recovery Strategies

```python
class ErrorRecoveryManager:
    def attempt_isbn_correction(self, isbn: str) -> str
    def suggest_bisac_codes(self, title: str, keywords: str) -> List[str]
    def calculate_missing_pricing(self, base_price: float, territory: str) -> str
    def generate_default_contributor_info(self, author: str) -> Dict[str, str]
```

## Testing Strategy

### Unit Testing

1. **Field Mapping Tests**
   - Test each mapping strategy independently
   - Verify field transformations and calculations
   - Test default value application

2. **Validation Tests**
   - Test each validator with valid/invalid inputs
   - Test validation pipeline integration
   - Test error message generation

3. **Configuration Tests**
   - Test configuration loading and parsing
   - Test imprint and territorial overrides
   - Test default value resolution

### Integration Testing

1. **End-to-End Generation Tests**
   - Test complete metadata → CSV generation
   - Test with various metadata completeness levels
   - Test with different imprint configurations

2. **File System Integration Tests**
   - Test PDF validation with actual files
   - Test FTP staging area checks
   - Test file naming conventions

### Validation Testing

1. **LSI Compliance Tests**
   - Test generated CSV against LSI template
   - Test field ordering and formatting
   - Test with LSI sample data

2. **Real-world Data Tests**
   - Test with existing book metadata
   - Test with edge cases and unusual data
   - Performance testing with large datasets

### Test Data Management

```python
# Test fixtures for different scenarios
@pytest.fixture
def minimal_metadata():
    """Metadata with only required fields"""

@pytest.fixture  
def complete_metadata():
    """Metadata with all fields populated"""

@pytest.fixture
def multi_contributor_metadata():
    """Metadata with multiple contributors"""

@pytest.fixture
def international_metadata():
    """Metadata with international pricing"""
```

## Implementation Phases

### Phase 1: Core Infrastructure
- Enhanced metadata model with LSI fields
- Field mapping registry and strategy pattern
- Basic validation framework

### Phase 2: Comprehensive Field Support
- All 100+ LSI field mappings
- Configuration system implementation
- Advanced validation rules

### Phase 3: File Integration
- PDF validation system
- FTP staging area integration
- File naming and path management

### Phase 4: Reporting and Monitoring
- Detailed logging system
- Error reporting and recovery
- Generation analytics and metrics