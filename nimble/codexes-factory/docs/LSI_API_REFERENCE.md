# LSI API Reference

This document provides a comprehensive reference for the LSI Field Enhancement API, including classes, methods, and usage examples.

## Table of Contents

1. [LLM Field Completer](#llm-field-completer)
2. [Enhanced Field Mappings](#enhanced-field-mappings)
3. [ISBN Database Management](#isbn-database-management)
4. [Series Management](#series-management)
5. [Field Completion Reporting](#field-completion-reporting)
6. [Error Recovery Manager](#error-recovery-manager)
7. [LSI ACS Generator Integration](#lsi-acs-generator-integration)

## LLM Field Completer

The `LLMFieldCompleter` class provides functionality to complete LSI fields using LLM calls.

### Class: `LLMFieldCompleter`

```python
class LLMFieldCompleter:
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash", 
                prompts_path: str = "prompts/lsi_field_completion_prompts.json"):
        """
        Initialize the LLM field completer.
        
        Args:
            model_name: Name of the LLM model to use
            prompts_path: Path to the LSI field completion prompts file
        """
        
    def complete_missing_fields(self, metadata: CodexMetadata, book_content: Optional[str] = None, 
                           save_to_disk: bool = True, output_dir: Optional[str] = None) -> CodexMetadata:
        """
        Complete missing LSI fields in the metadata object.
        
        Args:
            metadata: CodexMetadata object to complete
            book_content: Optional book content to use for field completion
            save_to_disk: Whether to save completions to disk
            output_dir: Directory to save completions
            
        Returns:
            Updated CodexMetadata object with completed fields
        """
```

### Usage Example

```python
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter

# Initialize LLM field completer
field_completer = LLMFieldCompleter(model_name="gemini/gemini-2.5-flash")

# Complete missing fields
metadata = field_completer.complete_missing_fields(
    metadata, 
    book_content="Full text of the book...",
    save_to_disk=True,
    output_dir="output/metadata"
)
```

## Enhanced Field Mappings

The Enhanced Field Mappings system provides comprehensive mapping strategies for all LSI template fields.

### Class: `FieldMappingRegistry`

```python
class FieldMappingRegistry:
    def __init__(self):
        """Initialize empty registry."""
        
    def register_strategy(self, field_name: str, strategy: MappingStrategy) -> None:
        """
        Register a mapping strategy for a specific field.
        
        Args:
            field_name: Name of the LSI field this strategy handles
            strategy: MappingStrategy instance to use for this field
        """
        
    def get_strategy(self, field_name: str) -> Optional[MappingStrategy]:
        """
        Get the mapping strategy for a specific field.
        
        Args:
            field_name: Name of the LSI field
            
        Returns:
            MappingStrategy instance or None if not found
        """
        
    def apply_mappings(self, metadata: CodexMetadata, lsi_headers: List[str]) -> Dict[str, str]:
        """
        Apply all registered mapping strategies to generate LSI field values.
        
        Args:
            metadata: Source CodexMetadata object
            lsi_headers: List of LSI header names in order
            
        Returns:
            Dictionary mapping LSI field names to their values
        """
```

### Function: `create_enhanced_field_mapping_registry`

```python
def create_enhanced_field_mapping_registry() -> FieldMappingRegistry:
    """
    Create an enhanced field mapping registry with specialized strategies.
    
    Returns:
        FieldMappingRegistry with enhanced mapping strategies
    """
```

### Usage Example

```python
from src.codexes.modules.distribution.enhanced_field_mappings import create_enhanced_field_mapping_registry

# Create enhanced field mapping registry
registry = create_enhanced_field_mapping_registry()

# Apply mappings to generate LSI field values
field_values = registry.apply_mappings(metadata, lsi_headers)
```

## ISBN Database Management

The ISBN Database Management system provides functionality for managing ISBNs.

### Class: `ISBNDatabase`

```python
class ISBNDatabase:
    def __init__(self, storage_path: str = "data/isbn_database.json"):
        """
        Initialize the ISBN database.
        
        Args:
            storage_path: Path to the JSON file for persistent storage
        """
        
    def import_from_bowker(self, file_path: str, publisher_id: str) -> Dict[str, Any]:
        """
        Import ISBNs from a Bowker spreadsheet.
        
        Args:
            file_path: Path to the Bowker spreadsheet
            publisher_id: ID of the publisher
            
        Returns:
            Dictionary with import statistics
        """
        
    def get_next_available_isbn(self, publisher_id: str = None) -> Optional[str]:
        """
        Get the next available ISBN for a publisher.
        
        Args:
            publisher_id: ID of the publisher (optional)
            
        Returns:
            ISBN string or None if no ISBNs are available
        """
        
    def assign_isbn(self, isbn: str, book_id: str) -> bool:
        """
        Assign an ISBN to a book (private assignment).
        
        Args:
            isbn: ISBN to assign
            book_id: ID of the book
            
        Returns:
            True if successful, False otherwise
        """
        
    def mark_as_published(self, isbn: str) -> bool:
        """
        Mark an ISBN as publicly assigned (published).
        
        Args:
            isbn: ISBN to mark as published
            
        Returns:
            True if successful, False otherwise
        """
        
    def release_isbn(self, isbn: str) -> bool:
        """
        Release a privately assigned ISBN back to the available pool.
        
        Args:
            isbn: ISBN to release
            
        Returns:
            True if successful, False otherwise
        """
```

### Usage Example

```python
from src.codexes.modules.distribution.isbn_database import ISBNDatabase

# Initialize ISBN database
isbn_db = ISBNDatabase()

# Import ISBNs from Bowker spreadsheet
stats = isbn_db.import_from_bowker("path/to/bowker_spreadsheet.csv", "publisher-id")

# Get next available ISBN
isbn = isbn_db.get_next_available_isbn("publisher-id")

# Assign ISBN to book
isbn_db.assign_isbn(isbn, "book-123")

# Mark ISBN as published
isbn_db.mark_as_published(isbn)
```

## Series Management

The Series Management system provides functionality for managing book series metadata.

### Class: `SeriesRegistry`

```python
class SeriesRegistry:
    def __init__(self, storage_path: str = "data/series_registry.json"):
        """
        Initialize the series registry.
        
        Args:
            storage_path: Path to the JSON file for persistent storage
        """
        
    def create_series(self, name: str, publisher_id: str, multi_publisher: bool = False, description: Optional[str] = None) -> str:
        """
        Create a new series and return its ID.
        
        Args:
            name: Name of the series
            publisher_id: ID of the publisher creating the series
            multi_publisher: Whether the series allows multiple publishers
            description: Optional description of the series
            
        Returns:
            ID of the created series
        """
        
    def add_book_to_series(self, series_id: str, book_id: str, sequence_number: Optional[int] = None, publisher_id: Optional[str] = None) -> int:
        """
        Add a book to a series with an optional sequence number.
        
        Args:
            series_id: ID of the series
            book_id: ID of the book
            sequence_number: Optional sequence number (auto-assigned if None)
            publisher_id: Optional ID of the publisher adding the book
            
        Returns:
            Assigned sequence number
        """
        
    def get_books_in_series(self, series_id: str, publisher_id: Optional[str] = None) -> List[SeriesBook]:
        """
        Get all books in a series.
        
        Args:
            series_id: ID of the series
            publisher_id: Optional ID of the publisher
            
        Returns:
            List of SeriesBook objects
        """
```

### Class: `SeriesAssigner`

```python
class SeriesAssigner:
    def __init__(self, series_registry: SeriesRegistry):
        """
        Initialize the series assigner.
        
        Args:
            series_registry: SeriesRegistry instance to use for series management
        """
        
    def assign_book_to_series(self, metadata: CodexMetadata, series_name: str, 
                             sequence_number: Optional[int] = None,
                             publisher_id: Optional[str] = None) -> Tuple[str, int]:
        """
        Assign a book to a series.
        
        Args:
            metadata: CodexMetadata object for the book
            series_name: Name of the series
            sequence_number: Optional sequence number (auto-assigned if None)
            publisher_id: Optional ID of the publisher (defaults to metadata.publisher)
            
        Returns:
            Tuple of (series_id, sequence_number)
        """
```

### Usage Example

```python
from src.codexes.modules.distribution.series_registry import SeriesRegistry
from src.codexes.modules.distribution.series_assigner import SeriesAssigner

# Initialize series registry and assigner
registry = SeriesRegistry()
assigner = SeriesAssigner(registry)

# Create a series
series_id = registry.create_series("Test Series", "publisher-id")

# Assign book to series
series_id, sequence_number = assigner.assign_book_to_series(
    metadata, "Test Series", sequence_number=1, publisher_id="publisher-id"
)
```

## Field Completion Reporting

The Field Completion Reporting system provides detailed reports on field completion status.

### Class: `LSIFieldCompletionReporter`

```python
class LSIFieldCompletionReporter:
    def __init__(self, registry: FieldMappingRegistry):
        """
        Initialize the LSI field completion reporter.
        
        Args:
            registry: FieldMappingRegistry instance to use for field mapping
        """
        
    def generate_field_strategy_report(self, metadata: CodexMetadata, lsi_headers: List[str],
                                     output_dir: str = "output/reports",
                                     formats: List[str] = ["csv", "html", "json"]) -> Dict[str, str]:
        """
        Generate a report on field completion strategies and results.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            output_dir: Directory to save reports
            formats: List of report formats to generate (csv, html, json)
            
        Returns:
            Dictionary mapping format to output file path
        """
        
    def generate_markdown_report(self, metadata: CodexMetadata, lsi_headers: List[str], 
                               output_path: str) -> str:
        """
        Generate a Markdown report.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            output_path: Path to save the Markdown file
            
        Returns:
            Path to the generated report
        """
```

### Usage Example

```python
from src.codexes.modules.distribution.lsi_field_completion_reporter import LSIFieldCompletionReporter

# Initialize reporter
reporter = LSIFieldCompletionReporter(field_registry)

# Generate reports
output_files = reporter.generate_field_strategy_report(
    metadata, lsi_headers, output_dir="output/reports",
    formats=["csv", "html", "json", "md"]
)
```

## Error Recovery Manager

The Error Recovery Manager provides functionality for handling and recovering from field completion errors.

### Class: `ErrorRecoveryManager`

```python
class ErrorRecoveryManager:
    def __init__(self):
        """Initialize the error recovery manager."""
        
    def attempt_isbn_correction(self, isbn: str) -> str:
        """
        Attempt to correct an invalid ISBN.
        
        Args:
            isbn: ISBN string to correct
            
        Returns:
            Corrected ISBN string or original if correction fails
        """
        
    def suggest_bisac_codes(self, title: str, keywords: str = "", description: str = "") -> List[str]:
        """
        Suggest BISAC codes based on title, keywords, and description.
        
        Args:
            title: Book title
            keywords: Book keywords
            description: Book description
            
        Returns:
            List of suggested BISAC codes
        """
        
    def calculate_missing_pricing(self, base_price_usd: float, territory: str) -> str:
        """
        Calculate missing territorial pricing based on US price.
        
        Args:
            base_price_usd: Base price in USD
            territory: Territory code (UK, EU, CA, AU, etc.)
            
        Returns:
            Formatted price string with currency symbol
        """
        
    def recover_from_validation_errors(self, metadata: CodexMetadata, validation_result: ValidationResult) -> CodexMetadata:
        """
        Attempt to recover from validation errors.
        
        Args:
            metadata: CodexMetadata object to fix
            validation_result: ValidationResult with errors
            
        Returns:
            Updated CodexMetadata object with fixes applied
        """
        
    def get_recovery_suggestions(self, validation_result: ValidationResult) -> List[str]:
        """
        Get suggestions for recovering from validation errors.
        
        Args:
            validation_result: ValidationResult with errors
            
        Returns:
            List of suggestion strings
        """
```

### Usage Example

```python
from src.codexes.modules.distribution.error_recovery_manager import ErrorRecoveryManager

# Initialize error recovery manager
recovery_manager = ErrorRecoveryManager()

# Correct an invalid ISBN
corrected_isbn = recovery_manager.attempt_isbn_correction("978-1-234-56789-0")

# Suggest BISAC codes
bisac_codes = recovery_manager.suggest_bisac_codes(
    "Artificial Intelligence Guide",
    "AI, machine learning",
    "A comprehensive guide to artificial intelligence"
)

# Recover from validation errors
fixed_metadata = recovery_manager.recover_from_validation_errors(metadata, validation_result)
```

## LSI ACS Generator Integration

The LSI ACS Generator Integration provides functionality to integrate field completion and series management with the LSI ACS Generator.

### Function: `integrate_field_completion_with_lsi_generator`

```python
def integrate_field_completion_with_lsi_generator(generator, model_name: str = "gemini/gemini-2.5-flash",
                                               prompts_path: str = "prompts/lsi_field_completion_prompts.json") -> None:
    """
    Integrate field completion with an LSI ACS Generator instance.
    
    Args:
        generator: LsiAcsGenerator instance
        model_name: Name of the LLM model to use
        prompts_path: Path to the LSI field completion prompts file
    """
```

### Function: `integrate_series_with_lsi_generator`

```python
def integrate_series_with_lsi_generator(generator, series_registry_path: Optional[str] = None) -> None:
    """
    Integrate series management with an LSI ACS Generator instance.
    
    Args:
        generator: LsiAcsGenerator instance
        series_registry_path: Optional path to the series registry file
    """
```

### Usage Example

```python
from src.codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
from src.codexes.modules.distribution.lsi_field_completion_integration import integrate_field_completion_with_lsi_generator
from src.codexes.modules.distribution.series_lsi_integration import integrate_series_with_lsi_generator

# Initialize LSI ACS generator
generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/default_lsi_config.json"
)

# Integrate field completion and series management
integrate_field_completion_with_lsi_generator(generator)
integrate_series_with_lsi_generator(generator)

# Generate CSV file with validation and field completion
result = generator.generate_with_validation(metadata, output_path, book_content)
```