# Design Document

## Overview

The LSI Field Enhancement Phase 2 addresses specific issues identified during acceptance testing of the initial implementation. This phase focuses on three key areas:

1. **LLM Completion Storage**: Ensuring LLM-generated field completions are properly stored in a consistent directory structure.
2. **LSI CSV Output Integration**: Ensuring LLM-generated field completions are properly included in the final LSI CSV output.
3. **Field Completion Visibility**: Providing detailed reports on field completion strategies and values.

The design builds upon the existing architecture while adding new components and enhancing existing ones to address these specific issues.

## Architecture

### Enhanced Components

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
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Phase 2 Enhancements                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Enhanced LLM    │  │ Enhanced LLM    │  │ Field       │ │
│  │ Field Completer │  │ Completion      │  │ Completion  │ │
│  │ - Storage       │  │ Strategy        │  │ Reporter    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced LLM Field Completer

The existing `LLMFieldCompleter` class will be enhanced to improve storage of LLM completions:

```python
class LLMFieldCompleter:
    # ... existing methods ...
    
    def _save_completions_to_disk(self, metadata: CodexMetadata, output_dir: Optional[str] = None) -> None:
        """
        Save LLM completions to disk.
        
        Args:
            metadata: CodexMetadata object with completions
            output_dir: Directory to save completions (defaults to metadata/ parallel to covers/ and interiors/)
            
        Returns:
            Path to the saved file or None if saving failed
        """
        # Enhanced directory discovery logic
        # Look for existing book directories by publisher_reference_id or ISBN
        # Create directory structure if it doesn't exist
        # Save completions with consistent file naming
```

### Enhanced LLM Completion Strategy

The `LLMCompletionStrategy` class will be enhanced to properly include LLM completions in the CSV output:

```python
class LLMCompletionStrategy(MappingStrategy):
    """
    Strategy for LLM-based field completion.
    Uses the LLMFieldCompleter to generate field values intelligently.
    
    This strategy first checks if the field has already been completed in the
    metadata.llm_completions dictionary, then checks if the field has a direct value,
    and finally attempts to complete the field using the LLMFieldCompleter.
    """
    
    def __init__(self, field_completer, metadata_field: str, prompt_key: str = None, fallback_value: str = ""):
        # ... initialization ...
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate field value using LLM field completer with fallback."""
        # Check for existing completions in metadata.llm_completions
        # Check for direct field value
        # Use LLM to complete the field if needed
        # Log the source of the field value
```

### Field Completion Reporter

A new `LSIFieldCompletionReporter` class will be implemented to provide detailed reports on field completion strategies and values:

```python
class LSIFieldCompletionReporter:
    """
    Generates reports on LSI field completion strategies and values.
    
    This class provides visibility into which fields are being completed by which
    strategies and their actual values. It can generate reports in CSV and HTML formats.
    """
    
    def __init__(self, registry: FieldMappingRegistry):
        """Initialize with field mapping registry."""
        
    def generate_field_strategy_report(self, metadata: CodexMetadata, 
                                      lsi_headers: List[str], 
                                      output_dir: Optional[str] = None,
                                      formats: List[str] = ["csv", "html"]) -> Dict[str, str]:
        """Generate report on field completion strategies and values."""
        
    def _generate_report_data(self, metadata: CodexMetadata, lsi_headers: List[str]) -> List[Dict[str, Any]]:
        """Generate report data for field completion strategies and values."""
        
    def _determine_field_source(self, metadata: CodexMetadata, field_name: str, 
                              strategy: MappingStrategy, value: str) -> str:
        """Determine the source of a field value."""
        
    def _generate_csv_report(self, report_data: List[Dict[str, Any]], output_path: str) -> None:
        """Generate a CSV report."""
        
    def _generate_html_report(self, report_data: List[Dict[str, Any]], 
                            metadata: CodexMetadata, output_path: str) -> None:
        """Generate an HTML report with statistics and formatting."""
```

### Book Pipeline Integration

The existing `run_book_pipeline.py` script will be enhanced to integrate the field completion reporter:

```python
# In run_book_pipeline.py

# After generating batch LSI CSV
if result.success:
    # ... existing code ...
    
    # Generate field completion reports
    try:
        # Initialize LSIFieldCompletionReporter
        reporter = LSIFieldCompletionReporter(registry)
        
        # Generate reports for each metadata object
        for metadata in lsi_metadata_list:
            # Generate report
            report_files = reporter.generate_field_strategy_report(
                metadata=metadata,
                lsi_headers=headers,
                output_dir=config['lsi_output_dir'],
                formats=["html", "csv"]
            )
            
        # Also generate combined report for backward compatibility
        generate_field_report(
            csv_path=str(batch_lsi_csv_path),
            output_path=str(report_path),
            config_path=config['lsi_config_path'],
            format="markdown"
        )
    except Exception as e:
        logger.warning(f"Failed to generate field completion report: {e}")
```

## Data Models

### Field Completion Report Data

```python
@dataclass
class FieldCompletionData:
    field_name: str
    strategy_type: str
    value: str
    source: str
    is_empty: bool
    llm_value: Optional[str] = None
```

### Report Statistics

```python
@dataclass
class ReportStatistics:
    total_fields: int
    populated_fields: int
    empty_fields: int
    completion_percentage: float
    strategy_counts: Dict[str, int]
    source_counts: Dict[str, int]
```

## Implementation Approach

### Phase 2.1: Enhanced LLM Field Completer

1. Enhance the `_save_completions_to_disk` method to improve directory discovery
2. Add robust error handling and logging
3. Ensure consistent file naming with timestamps and ISBN

### Phase 2.2: Enhanced LLM Completion Strategy

1. Update the `LLMCompletionStrategy` class to check for existing completions
2. Add support for prompt_key parameter to help locate the right completion
3. Improve field value extraction logic to handle different result formats
4. Add logging for field completion source

### Phase 2.3: Field Completion Reporter

1. Implement the `LSIFieldCompletionReporter` class
2. Add support for multiple output formats (CSV, HTML, JSON)
3. Include statistics on field population rates and strategy usage
4. Create visually appealing HTML reports with progress bars and color coding

### Phase 2.4: Book Pipeline Integration

1. Update `run_book_pipeline.py` to use the new reporter
2. Add fallback to existing report generator for backward compatibility
3. Ensure reports are generated for each book in the batch
4. Add error handling to continue processing even if reporting fails

## Testing Strategy

### Unit Testing

1. **LLM Field Completer Tests**
   - Test directory discovery logic with various scenarios
   - Test file naming and path construction
   - Test error handling and recovery

2. **LLM Completion Strategy Tests**
   - Test completion source priority (direct field, llm_completions, new completion)
   - Test field value extraction from different result formats
   - Test fallback behavior

3. **Field Completion Reporter Tests**
   - Test report data generation
   - Test field source determination
   - Test CSV and HTML report generation
   - Test statistics calculation

### Integration Testing

1. **End-to-End Tests**
   - Test complete flow from LLM completion to CSV generation to reporting
   - Test with various metadata completeness levels
   - Test with different output formats and configurations

2. **Book Pipeline Integration Tests**
   - Test report generation during batch processing
   - Test error handling and recovery
   - Test backward compatibility with existing reporting

### Validation Testing

1. **Real-world Data Tests**
   - Test with existing book metadata
   - Test with edge cases and unusual data
   - Verify report accuracy and completeness

## Implementation Phases

### Phase 2.1: Core Enhancements
- Enhanced LLM Field Completer with improved storage
- Enhanced LLM Completion Strategy with better integration

### Phase 2.2: Reporting System
- Field Completion Reporter implementation
- Multiple output format support
- Statistics and visualization

### Phase 2.3: Pipeline Integration
- Book Pipeline integration
- Backward compatibility
- Error handling and recovery