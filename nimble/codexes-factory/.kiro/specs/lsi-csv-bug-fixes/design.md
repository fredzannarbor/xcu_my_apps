# LSI CSV Bug Fixes Project - Design Document

## Overview

This project addresses critical bugs and issues in the existing LSI CSV generation system. The focus is on improving reliability, fixing prompt-related issues, enhancing validation, and ensuring robust error handling throughout the LSI generation pipeline.

## Architecture

### Current System Analysis

The existing LSI CSV generation system consists of:

```
Book Metadata (JSON) 
    ↓
Enhanced LLM Field Completer
    ↓
Field Mapping Registry
    ↓
LSI ACS Generator
    ↓
Validation & Output (CSV)
```

### Identified Problem Areas

1. **Prompt System Issues**
   - Old-style prompts causing JSON parsing failures
   - Inconsistent LLM response formats
   - Missing system messages for role definition

2. **Field Completion Problems**
   - Inaccurate BISAC code generation
   - Description length violations
   - Poor contributor information quality

3. **Validation Failures**
   - Incorrect field length checking
   - Missing required field detection issues
   - Format validation bugs

4. **Configuration Issues**
   - Multi-level config inheritance problems
   - Tranche configuration not applying correctly
   - Default value handling failures

5. **Error Handling Gaps**
   - Poor error recovery mechanisms
   - Insufficient logging and debugging info
   - Batch processing failure cascades

## Components and Interfaces

### 1. Enhanced Prompt System

#### Current Issues
- Bibliography prompt returning conversational text instead of JSON
- Inconsistent system message formatting
- Missing JSON enforcement in prompts

#### Proposed Fixes
```python
class ModernizedPromptManager:
    def ensure_json_response(self, prompt_config: Dict) -> Dict:
        """Ensure all prompts enforce JSON-only responses"""
        if 'messages' not in prompt_config:
            return self.convert_to_messages_format(prompt_config)
        
        # Add JSON enforcement to system message
        system_msg = prompt_config['messages'][0]['content']
        if 'JSON format' not in system_msg:
            system_msg += " You MUST respond ONLY in valid JSON format."
            prompt_config['messages'][0]['content'] = system_msg
        
        return prompt_config
```

#### Implementation Plan
- Convert all remaining old-style prompts to messages format
- Add explicit JSON enforcement to all system messages
- Implement response validation with fallback handling
- Add prompt testing framework

### 2. Improved Field Completion

#### Current Issues
- BISAC codes often invalid or outdated
- Descriptions exceeding character limits
- Generic contributor biographies

#### Proposed Fixes
```python
class EnhancedFieldValidator:
    def validate_bisac_code(self, code: str) -> ValidationResult:
        """Validate BISAC code against current standards"""
        # Check format: 3 letters + 6 digits
        if not re.match(r'^[A-Z]{3}\d{6}$', code):
            return ValidationResult(False, "Invalid BISAC format")
        
        # Check against current BISAC database
        if not self.bisac_db.is_valid(code):
            return ValidationResult(False, f"BISAC code {code} not found in current standards")
        
        return ValidationResult(True, "Valid BISAC code")
    
    def validate_description_length(self, description: str, max_length: int) -> ValidationResult:
        """Validate description length with proper truncation"""
        if len(description) <= max_length:
            return ValidationResult(True, "Description length valid")
        
        # Intelligent truncation at sentence boundary
        truncated = self.truncate_at_sentence(description, max_length)
        return ValidationResult(False, f"Description too long, suggested: {truncated}")
```

#### Implementation Plan
- Update BISAC validation with current standards
- Implement intelligent text truncation
- Enhance contributor bio generation with book context
- Add field-specific validation rules

### 3. Robust Validation Framework

#### Current Issues
- Validation rules not matching LSI requirements
- Poor error messages
- Validation bypassed in some code paths

#### Proposed Fixes
```python
class LSIComplianceValidator:
    def __init__(self):
        self.field_rules = self.load_lsi_field_rules()
        self.required_fields = self.load_required_fields()
    
    def validate_complete_record(self, metadata: CodexMetadata) -> ValidationReport:
        """Comprehensive validation of all LSI fields"""
        report = ValidationReport()
        
        # Check required fields
        for field in self.required_fields:
            if not getattr(metadata, field, None):
                report.add_error(f"Required field '{field}' is missing")
        
        # Validate field formats and lengths
        for field_name, value in metadata.to_dict().items():
            if field_name in self.field_rules:
                rule = self.field_rules[field_name]
                result = self.validate_field(field_name, value, rule)
                if not result.is_valid:
                    report.add_error(f"Field '{field_name}': {result.message}")
        
        return report
```

#### Implementation Plan
- Create comprehensive LSI field rules database
- Implement field-by-field validation
- Add validation report generation
- Ensure validation runs at all critical points

### 4. Configuration System Fixes

#### Current Issues
- Multi-level config inheritance not working
- Tranche configurations not applying
- Default values not loading properly

#### Proposed Fixes
```python
class FixedConfigLoader:
    def load_hierarchical_config(self, publisher: str, imprint: str, tranche: str = None) -> Dict:
        """Load and merge configurations in correct hierarchy"""
        config = {}
        
        # Load in order: default -> publisher -> imprint -> tranche
        config.update(self.load_default_config())
        config.update(self.load_publisher_config(publisher))
        config.update(self.load_imprint_config(imprint))
        
        if tranche:
            config.update(self.load_tranche_config(tranche))
        
        # Validate merged configuration
        self.validate_config(config)
        return config
```

#### Implementation Plan
- Fix configuration inheritance order
- Add configuration validation
- Implement proper default handling
- Add configuration debugging tools

### 5. Enhanced Error Handling

#### Current Issues
- Errors causing complete pipeline failures
- Poor error messages and logging
- No retry mechanisms for transient failures

#### Proposed Fixes
```python
class RobustErrorHandler:
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_exceptions': [ConnectionError, TimeoutError]
        }
    
    def with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        for attempt in range(self.retry_config['max_retries']):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.retry_config['max_retries'] - 1:
                    logger.error(f"Final attempt failed: {e}")
                    raise
                
                if type(e) in self.retry_config['retry_exceptions']:
                    wait_time = self.retry_config['backoff_factor'] ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
```

#### Implementation Plan
- Add retry logic for LLM calls
- Implement graceful error recovery
- Enhance logging with context
- Add error aggregation for batch processing

## Data Models

### Enhanced Validation Models

```python
@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    suggested_fix: Optional[str] = None
    severity: str = "error"  # error, warning, info

@dataclass
class ValidationReport:
    errors: List[ValidationResult]
    warnings: List[ValidationResult]
    field_completeness: Dict[str, bool]
    overall_score: float
    
    def is_lsi_compliant(self) -> bool:
        return len(self.errors) == 0 and self.overall_score >= 0.8
```

### Error Tracking Models

```python
@dataclass
class ProcessingError:
    timestamp: datetime
    component: str
    error_type: str
    message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    
@dataclass
class BatchProcessingResult:
    total_books: int
    successful: int
    failed: int
    errors: List[ProcessingError]
    processing_time: float
    
    def success_rate(self) -> float:
        return self.successful / self.total_books if self.total_books > 0 else 0.0
```

## Error Handling

### Error Categories and Responses

1. **Prompt/LLM Errors**
   - JSON parsing failures → Use fallback values
   - Rate limiting → Implement exponential backoff
   - Model unavailable → Switch to backup model

2. **Validation Errors**
   - Field format violations → Provide correction suggestions
   - Missing required fields → Attempt AI completion
   - Length violations → Intelligent truncation

3. **Configuration Errors**
   - Missing config files → Use defaults with warnings
   - Invalid config syntax → Detailed error reporting
   - Inheritance conflicts → Clear precedence rules

4. **System Errors**
   - Memory issues → Implement streaming processing
   - File I/O errors → Retry with different paths
   - Network failures → Offline mode with cached data

## Testing Strategy

### Bug Reproduction Tests
- Create test cases for each identified bug
- Implement regression tests to prevent reoccurrence
- Add edge case testing for boundary conditions

### Integration Testing
- Test complete LSI generation pipeline
- Validate configuration loading and inheritance
- Test batch processing with error scenarios

### Performance Testing
- Memory usage monitoring during batch processing
- LLM call performance and caching effectiveness
- Large dataset processing capabilities

### Validation Testing
- Test against real LSI submission requirements
- Validate generated CSV files with IngramSpark tools
- Cross-reference with successful submissions

## Implementation Phases

### Phase 1: Critical Bug Fixes (Week 1-2)
- Fix JSON parsing errors in prompts
- Resolve configuration loading issues
- Implement basic error recovery

### Phase 2: Validation Improvements (Week 3-4)
- Update field validation rules
- Implement comprehensive LSI compliance checking
- Add validation reporting

### Phase 3: Enhanced Error Handling (Week 5-6)
- Add retry logic and fallback mechanisms
- Implement batch processing error recovery
- Enhance logging and debugging

### Phase 4: Performance and Polish (Week 7-8)
- Optimize memory usage and performance
- Add comprehensive testing
- Documentation and deployment improvements