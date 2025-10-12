# Design Document

## Overview

LSI Field Enhancement Phase 4 is designed to significantly improve the field population rate in the LSI CSV output, addressing the current issue where 62.18% of fields are empty. This phase builds upon the previous enhancements and focuses on four key areas:

1. **Enhanced LLM Field Completion**: Improving the quality and success rate of LLM-based field completion for subjective fields.
2. **Expanded Computed Fields**: Adding more computed field strategies to derive values from existing metadata.
3. **Comprehensive Default Values**: Providing intelligent default values at multiple levels (global, publisher, imprint).
4. **Robust Field Mapping**: Enhancing field mapping strategies to handle all common field name variations.

The design aims to achieve 100% field population rate (up from current 37.82%) while ensuring high-quality data for all critical LSI fields, as required by publishers rushing books to market.

## Architecture

The existing architecture will be maintained, with enhancements to key components:

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

### Enhanced LLM Field Completion

The LLM Field Completer will be enhanced to improve the quality and success rate of field completion, addressing the issue where only 2/12 LLM completions are showing up in metadata:

```python
class EnhancedLLMFieldCompleter:
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash", 
                prompts_path: str = "prompts/enhanced_lsi_field_completion_prompts.json"):
        # Initialize with improved prompts
        
    def complete_missing_fields(self, metadata: CodexMetadata, book_content: Optional[str] = None, 
                           save_to_disk: bool = True, output_dir: Optional[str] = None) -> CodexMetadata:
        # Enhanced field completion with better error handling and fallbacks
        
    def _process_prompt(self, prompt_key: str, metadata: CodexMetadata, book_content: Optional[str] = None) -> Any:
        # Improved prompt processing with retry logic and better context handling
        
    def _save_llm_completions(self, metadata: CodexMetadata, field_name: str, value: str) -> None:
        # Save LLM completions to metadata BEFORE filtering via field mapping strategies
        # This addresses the requirement to save all LLM completions
        
    def _provide_fallback_value(self, field_name: str, metadata: CodexMetadata) -> str:
        # New method to provide intelligent fallback values when LLM completion fails
```

### Expanded Computed Fields

New computed field strategies will be added to derive values from existing metadata:

```python
def _compute_territorial_pricing(metadata: CodexMetadata, context: MappingContext) -> str:
    # Calculate territorial pricing based on US price and exchange rates
    
def _compute_physical_specs(metadata: CodexMetadata, context: MappingContext) -> str:
    # Calculate physical specifications based on page count and trim size
    
def _compute_dates(metadata: CodexMetadata, context: MappingContext) -> str:
    # Calculate dates based on available date information
    
def _compute_file_paths(metadata: CodexMetadata, context: MappingContext) -> str:
    # Calculate file paths based on ISBN and standard naming conventions
```

### Comprehensive Default Values

The configuration system will be enhanced to support multiple levels of default values:

```python
class EnhancedLSIConfiguration:
    def __init__(self, config_path: Optional[str] = None, 
                publisher_config_path: Optional[str] = None,
                imprint_config_path: Optional[str] = None):
        # Initialize with multiple configuration sources
        
    def get_default_value(self, field_name: str) -> str:
        # Get default value with priority: imprint > publisher > global
        
    def get_field_override(self, field_name: str) -> Optional[str]:
        # Get field override with priority: imprint > publisher > global
```

### Robust Field Mapping

The field mapping system will be enhanced to handle all common field name variations:

```python
class EnhancedFieldMappingRegistry:
    def __init__(self):
        # Initialize with enhanced field name normalization
        
    def register_strategy(self, field_name: str, strategy: MappingStrategy) -> None:
        # Register strategy with normalized field name
        
    def get_strategy(self, field_name: str) -> Optional[MappingStrategy]:
        # Get strategy with normalized field name lookup
        
    def _normalize_field_name(self, field_name: str) -> str:
        # Normalize field name for consistent lookup
```

## Components and Interfaces

### Enhanced LLM Field Completion Prompts

The LLM field completion prompts will be enhanced to improve the quality and success rate of field completion:

```json
{
  "generate_contributor_bio": {
    "messages": [
      {
        "role": "system",
        "content": "You are a professional book metadata specialist with expertise in creating contributor biographies for LSI submissions."
      },
      {
        "role": "user",
        "content": "Generate a professional biography (100-150 words) for the author of this book:\n\nTitle: {title}\nAuthor: {author}\nPublisher: {publisher}\nSummary: {summary_short}\nBook Content: {book_content}\n\nThe biography should highlight the author's expertise, credentials, and background relevant to the book topic. Include academic affiliations, professional positions, and notable achievements if available in the content. Format the biography in third person and maintain a professional tone suitable for book metadata."
      }
    ],
    "params": {
      "temperature": 0.7,
      "max_tokens": 300
    },
    "fallback": "A respected expert in the field with extensive knowledge and experience related to {title}."
  }
}
```

### Expanded Computed Field Strategies

New computed field strategies will be implemented to derive values from existing metadata:

```python
class TerritorialPricingStrategy(ComputedMappingStrategy):
    def __init__(self, territory_code: str, exchange_rate: float, 
                 base_price_field: str = "list_price_usd"):
        self.territory_code = territory_code
        self.exchange_rate = exchange_rate
        self.base_price_field = base_price_field
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate territorial pricing based on US price and exchange rate
        
class PhysicalSpecsStrategy(ComputedMappingStrategy):
    def __init__(self, spec_type: str):
        self.spec_type = spec_type  # "weight", "spine_width", etc.
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate physical specifications based on page count and trim size
        
class DateComputationStrategy(ComputedMappingStrategy):
    def __init__(self, date_type: str, offset_days: int = 0):
        self.date_type = date_type  # "pub_date", "street_date", etc.
        self.offset_days = offset_days
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate dates based on available date information
        
class FilePathStrategy(ComputedMappingStrategy):
    def __init__(self, file_type: str):
        self.file_type = file_type  # "cover", "interior", "jacket", etc.
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate file paths based on ISBN and standard naming conventions
```

### Enhanced Configuration System

The configuration system will be enhanced to support multiple levels of default values:

```python
class ConfigurationLevel:
    def __init__(self, config_data: Dict[str, Any]):
        self.defaults = config_data.get("defaults", {})
        self.field_overrides = config_data.get("field_overrides", {})
        self.territorial_configs = config_data.get("territorial_configs", {})
        
class MultiLevelConfiguration:
    def __init__(self):
        self.levels = []
        
    def add_level(self, level: ConfigurationLevel, priority: int):
        # Add configuration level with priority
        
    def get_value(self, section: str, key: str) -> Optional[str]:
        # Get value with priority from highest to lowest
```

### Field Name Normalization

A field name normalization system will be implemented to handle all common field name variations:

```python
class FieldNameNormalizer:
    def __init__(self):
        self.normalization_rules = [
            # Remove special characters
            (r'[^\w\s]', ' '),
            # Convert to lowercase
            (lambda s: s.lower()),
            # Remove extra whitespace
            (r'\s+', ' '),
            # Remove common words
            (r'\b(the|a|an|of|in|for|to|with|by|at|from|on)\b', ''),
            # Trim whitespace
            (lambda s: s.strip())
        ]
        
    def normalize(self, field_name: str) -> str:
        # Apply normalization rules
        
    def get_variations(self, field_name: str) -> List[str]:
        # Generate common variations of field name
```

## Data Models

### Enhanced CodexMetadata

The CodexMetadata class will be enhanced with additional fields and methods:

```python
@dataclass
class EnhancedCodexMetadata(CodexMetadata):
    # Additional fields for LSI submission
    
    # Enhanced contributor information
    contributor_one_bio: str = ""
    contributor_one_affiliations: str = ""
    contributor_one_professional_position: str = ""
    contributor_one_location: str = ""
    contributor_one_location_type_code: str = ""
    contributor_one_prior_work: str = ""
    
    # Enhanced physical specifications
    spine_width_in: float = 0.0
    weight_lbs: str = ""
    
    # Enhanced pricing information
    territorial_pricing: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Enhanced file paths
    jacket_path_filename: str = ""
    interior_path_filename: str = ""
    cover_path_filename: str = ""
    
    # LLM completion tracking - addressing the requirement to save all LLM completions
    llm_completions: Dict[str, Any] = field(default_factory=dict)
    llm_completion_attempts: Dict[str, int] = field(default_factory=dict)
    llm_completion_failures: Dict[str, List[str]] = field(default_factory=dict)
    
    def compute_derived_fields(self):
        # Compute derived fields based on existing metadata
        
    def get_field_population_stats(self) -> Dict[str, Any]:
        # Get statistics on field population
```

### Enhanced Validation Result

The validation system will be enhanced to provide more detailed information:

```python
@dataclass
class EnhancedFieldValidationResult:
    field_name: str
    is_valid: bool
    error_message: str = ""
    warning_message: str = ""
    suggested_value: str = ""
    severity: str = "info"  # "info", "warning", "error", "critical"
    
@dataclass
class EnhancedValidationResult:
    is_valid: bool
    field_results: List[EnhancedFieldValidationResult]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def get_errors_by_severity(self, severity: str) -> List[str]:
        # Get errors filtered by severity
        
    def has_critical_errors(self) -> bool:
        # Check if there are any critical errors
```

## Error Handling

### Enhanced Error Recovery

The error recovery system will be enhanced to provide better fallback values and recovery strategies:

```python
class EnhancedErrorRecoveryManager:
    def __init__(self, config: EnhancedLSIConfiguration):
        self.config = config
        self.recovery_strategies = {
            "contributor_bio": self._recover_contributor_bio,
            "bisac_codes": self._recover_bisac_codes,
            "territorial_pricing": self._recover_territorial_pricing,
            "physical_specs": self._recover_physical_specs,
            "dates": self._recover_dates,
            "file_paths": self._recover_file_paths
        }
        
    def recover_field(self, field_name: str, metadata: CodexMetadata) -> str:
        # Recover field value using appropriate strategy
        
    def _recover_contributor_bio(self, metadata: CodexMetadata) -> str:
        # Generate a generic contributor bio based on available metadata
        
    def _recover_bisac_codes(self, metadata: CodexMetadata) -> str:
        # Generate BISAC codes based on title and keywords
        
    def _recover_territorial_pricing(self, metadata: CodexMetadata) -> Dict[str, str]:
        # Calculate territorial pricing based on US price
        
    def _recover_physical_specs(self, metadata: CodexMetadata) -> Dict[str, str]:
        # Calculate physical specifications based on page count
        
    def _recover_dates(self, metadata: CodexMetadata) -> Dict[str, str]:
        # Calculate dates based on available date information
        
    def _recover_file_paths(self, metadata: CodexMetadata) -> Dict[str, str]:
        # Calculate file paths based on ISBN
```

### Enhanced Logging System

The logging system will be enhanced to provide high transparency and filterability, addressing Requirements 2 and 3:

```python
class EnhancedLSILoggingManager:
    def __init__(self, log_dir: str = "logs/lsi_generation", 
                 verbosity: str = "normal"):
        self.log_dir = log_dir
        self.verbosity = verbosity  # "minimal", "normal", "detailed"
        self.session_id = f"lsi_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.field_mapping_log = []
        self.validation_log = []
        self.error_log = []
        self.performance_log = []
        
    def set_verbosity(self, verbosity: str):
        # Set logging verbosity level
        # "minimal" - only warnings, errors, and major decisions (for systems operators)
        # "normal" - errors, warnings, and important info
        # "detailed" - all events including debug information (for programmers)
        self.verbosity = verbosity
        
    def log_field_mapping(self, field_name: str, strategy_name: str, value: str, source: str, severity: str = "info"):
        # Log field mapping details if verbosity level allows
        if self._should_log(severity):
            self.field_mapping_log.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": "field_mapping",
                "field_name": field_name,
                "strategy_name": strategy_name,
                "value": value,
                "source": source,
                "severity": severity
            })
        
    def log_validation(self, field_name: str, is_valid: bool, message: str, severity: str):
        # Log validation details if verbosity level allows
        if self._should_log(severity):
            self.validation_log.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": "validation",
                "field_name": field_name,
                "is_valid": is_valid,
                "message": message,
                "severity": severity
            })
        
    def log_error(self, error_type: str, message: str, field_name: str = None, severity: str = "error"):
        # Log error details if verbosity level allows
        if self._should_log(severity):
            self.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": "error",
                "error_type": error_type,
                "message": message,
                "field_name": field_name,
                "severity": severity
            })
        
    def log_performance(self, operation: str, duration_ms: float, severity: str = "info"):
        # Log performance details if verbosity level allows
        if self._should_log(severity):
            self.performance_log.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": "performance",
                "operation": operation,
                "duration_ms": duration_ms,
                "severity": severity
            })
        
    def _should_log(self, severity: str) -> bool:
        # Determine if event should be logged based on verbosity level
        if self.verbosity == "detailed":
            return True
        elif self.verbosity == "normal":
            return severity in ["info", "warning", "error", "critical"]
        else:  # minimal - for systems operators
            return severity in ["warning", "error", "critical", "major_decision"]
        
    def get_filtered_log(self, severity_filter: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        # Get filtered log based on severity
        severity_filter = severity_filter or ["info", "warning", "error", "critical"]
        
        return {
            "field_mapping": [entry for entry in self.field_mapping_log if entry["severity"] in severity_filter],
            "validation": [entry for entry in self.validation_log if entry["severity"] in severity_filter],
            "error": [entry for entry in self.error_log if entry["severity"] in severity_filter],
            "performance": [entry for entry in self.performance_log if entry["severity"] in severity_filter]
        }
        
    def save_session_log(self):
        # Save session log to file
        os.makedirs(os.path.join(self.log_dir, "logs"), exist_ok=True)
        log_path = os.path.join(self.log_dir, "logs", f"{self.session_id}.json")
        
        with open(log_path, "w") as f:
            json.dump({
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "verbosity": self.verbosity,
                "field_mapping_log": self.field_mapping_log,
                "validation_log": self.validation_log,
                "error_log": self.error_log,
                "performance_log": self.performance_log
            }, f, indent=2)
            
        return log_path
```

## Comprehensive Reporting System

A comprehensive reporting system will be implemented, with a focus on HTML reports as specified in Requirement 4:

```python
class EnhancedLSIFieldReportGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        
    def generate_report(self, metadata: CodexMetadata, csv_path: str, log_path: str) -> Dict[str, Any]:
        # Generate comprehensive field population report
        field_stats = metadata.get_field_population_stats()
        
        # Load log data
        with open(log_path, "r") as f:
            log_data = json.load(f)
            
        # Generate report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "csv_path": csv_path,
            "field_population_rate": field_stats["population_rate"],
            "total_fields": field_stats["total_fields"],
            "populated_fields": field_stats["populated_fields"],
            "empty_fields": field_stats["empty_fields"],
            "field_details": field_stats["field_details"],
            "low_population_fields": [
                field for field, details in field_stats["field_details"].items()
                if not details["is_populated"]
            ],
            "validation_errors": [
                entry for entry in log_data["validation_log"]
                if not entry["is_valid"] and entry["severity"] in ["error", "critical"]
            ],
            "llm_completion_failures": metadata.llm_completion_failures
        }
        
        # Generate recommendations
        report_data["recommendations"] = self._generate_recommendations(report_data)
        
        # Save report - only HTML by default, as specified in Requirement 4
        self._save_report(report_data, formats=["html"])
        
        return report_data
        
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        # Generate recommendations for improving field population rates
        recommendations = []
        
        # Check for low population fields
        if len(report_data["low_population_fields"]) > 0:
            recommendations.append(
                f"Consider adding default values for {len(report_data['low_population_fields'])} empty fields."
            )
            
        # Check for LLM completion failures
        if len(report_data["llm_completion_failures"]) > 0:
            recommendations.append(
                f"Review LLM prompts for {len(report_data['llm_completion_failures'])} fields with completion failures."
            )
            
        # Check for validation errors
        if len(report_data["validation_errors"]) > 0:
            recommendations.append(
                f"Fix {len(report_data['validation_errors'])} validation errors to improve field quality."
            )
            
        # General recommendations
        if report_data["field_population_rate"] < 100:
            recommendations.append(
                "Consider adding more computed field strategies to derive values from existing metadata."
            )
            
        return recommendations
        
    def _save_report(self, report_data: Dict[str, Any], formats=["html"]):
        # Save report in specified formats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML report (default)
        if "html" in formats:
            html_report_path = os.path.join(self.output_dir, f"field_report__{timestamp}.html")
            self._save_html_report(report_data, html_report_path)
            
        # Save CSV report (optional)
        if "csv" in formats:
            csv_report_path = os.path.join(self.output_dir, f"field_report__{timestamp}.csv")
            self._save_csv_report(report_data, csv_report_path)
            
        # Save JSON report (optional)
        if "json" in formats:
            json_report_path = os.path.join(self.output_dir, f"field_report__{timestamp}.json")
            self._save_json_report(report_data, json_report_path)
        
        return {
            "html_report_path": html_report_path if "html" in formats else None,
            "csv_report_path": csv_report_path if "csv" in formats else None,
            "json_report_path": json_report_path if "json" in formats else None
        }
        
    def _save_csv_report(self, report_data: Dict[str, Any], path: str):
        # Save report as CSV
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Field Name", "Populated", "Value", "Source", "Validation"])
            
            for field, details in report_data["field_details"].items():
                writer.writerow([
                    field,
                    "Yes" if details["is_populated"] else "No",
                    details.get("value", ""),
                    details.get("source", ""),
                    details.get("validation_status", "")
                ])
                
    def _save_html_report(self, report_data: Dict[str, Any], path: str):
        # Save report as HTML with visualizations
        # Implementation details omitted for brevity
        pass
        
    def _save_json_report(self, report_data: Dict[str, Any], path: str):
        # Save report as JSON
        with open(path, "w") as f:
            json.dump(report_data, f, indent=2)
```

## Testing Strategy

### Unit Testing

1. **Enhanced LLM Field Completion Tests**
   - Test improved prompts with sample book content
   - Test fallback value generation
   - Test retry logic and error handling
   - Test saving of all LLM completions to metadata

2. **Expanded Computed Fields Tests**
   - Test territorial pricing calculation
   - Test physical specifications calculation
   - Test date calculation
   - Test file path generation

3. **Comprehensive Default Values Tests**
   - Test multi-level configuration
   - Test default value resolution with different priorities
   - Test field override resolution

4. **Robust Field Mapping Tests**
   - Test field name normalization
   - Test field name variation handling
   - Test field mapping with different CSV templates

5. **Enhanced Logging Tests**
   - Test different verbosity levels
   - Test severity filtering
   - Test structured log format

6. **Comprehensive Reporting Tests**
   - Test report generation with different field population rates
   - Test recommendation generation
   - Test HTML report format

### Integration Testing

1. **End-to-End Generation Tests**
   - Test complete metadata → CSV generation
   - Test with various metadata completeness levels
   - Test with different imprint configurations
   - **Test with rows 1-12 of xynapse_traces_schedule.json** (Requirement 5)

2. **Performance Testing**
   - Test field completion performance
   - Test CSV generation performance
   - Test with large datasets

3. **Logging and Reporting Integration Tests**
   - Test logging during CSV generation
   - Test report generation after CSV generation
   - Test log filtering and analysis

### Validation Testing

1. **LSI Compliance Tests**
   - Test generated CSV against LSI template
   - Test field formatting and validation
   - Test with LSI sample data

2. **Error Recovery Tests**
   - Test recovery from LLM completion failures
   - Test recovery from validation failures
   - Test recovery from configuration issues

## Implementation Phases

### Phase 1: Enhanced LLM Field Completion
- Improve LLM field completion prompts
- Add retry logic and better error handling
- Implement intelligent fallback values
- **Ensure all LLM completions are saved to metadata** (Requirement 4)

### Phase 2: Expanded Computed Fields
- Implement territorial pricing calculation
- Implement physical specifications calculation
- Implement date calculation
- Implement file path generation

### Phase 3: Comprehensive Default Values
- Implement multi-level configuration
- Add imprint-specific default values
- Add publisher-specific default values
- Enhance global default values

### Phase 4: Robust Field Mapping
- Implement field name normalization
- Add support for field name variations
- Enhance field mapping registry

### Phase 5: Enhanced Logging and Reporting
- Implement configurable logging system
- Add severity-based filtering
- Create comprehensive HTML reporting system

### Phase 6: Integration and Testing
- Integrate all components
- Comprehensive testing
- Performance optimization
- **Test with rows 1-12 of xynapse_traces_schedule.json** (Requirement 5)