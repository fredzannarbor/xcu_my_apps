# Final Fixes API Reference

This document provides detailed API reference for all components in the final fixes implementation.

## ISBNFormatter

**Module**: `codexes.modules.metadata.isbn_formatter`

### Class: ISBNFormatter

Formats ISBN-13 with proper hyphenation and validation.

#### Constructor

```python
ISBNFormatter()
```

Initializes the formatter with hyphenation rules and validation system.

#### Methods

##### validate_isbn_format(isbn: str) -> bool

Validates ISBN format and check digit with comprehensive validation.

**Parameters**:
- `isbn` (str): ISBN to validate (with or without hyphens)

**Returns**:
- `bool`: True if valid, False otherwise

**Example**:
```python
formatter = ISBNFormatter()
is_valid = formatter.validate_isbn_format("9780134685991")
```

##### format_isbn_13_hyphenated(isbn13: str) -> str

Formats ISBN-13 with proper hyphenation rules.

**Parameters**:
- `isbn13` (str): ISBN-13 to format

**Returns**:
- `str`: Hyphenated ISBN or original if invalid

**Example**:
```python
formatted = formatter.format_isbn_13_hyphenated("9780134685991")
# Returns: "978-0-13-468599-1"
```

##### generate_copyright_page_isbn(isbn13: str) -> str

Generates properly formatted ISBN for copyright page display.

**Parameters**:
- `isbn13` (str): ISBN-13 to format

**Returns**:
- `str`: Copyright page formatted ISBN with "ISBN " prefix

**Example**:
```python
copyright_isbn = formatter.generate_copyright_page_isbn("9780134685991")
# Returns: "ISBN 978-0-13-468599-1"
```

##### extract_isbn_components(isbn13: str) -> Dict[str, str]

Extracts ISBN components for analysis.

**Parameters**:
- `isbn13` (str): ISBN-13 to analyze

**Returns**:
- `Dict[str, str]`: Dictionary with components (prefix, group, publisher_title, check_digit, full_isbn)

##### batch_format_isbns(isbn_list: list) -> Dict[str, str]

Formats multiple ISBNs in batch.

**Parameters**:
- `isbn_list` (list): List of ISBNs to format

**Returns**:
- `Dict[str, str]`: Mapping of original to formatted ISBNs

---

## ISBNBarcodeGenerator

**Module**: `codexes.modules.distribution.isbn_barcode_generator`

### Classes

#### Position

```python
@dataclass
class Position:
    x: float
    y: float
    unit: str = "inches"
```

#### Size

```python
@dataclass
class Size:
    width: float
    height: float
    unit: str = "inches"
```

#### SafetySpaces

```python
@dataclass
class SafetySpaces:
    top: float
    bottom: float
    left: float
    right: float
    unit: str = "inches"
```

#### BarcodeResult

```python
@dataclass
class BarcodeResult:
    barcode_data: bytes
    position: Position
    safety_spaces: SafetySpaces
    format_type: str = "UPC-A"
```

### Class: ISBNBarcodeGenerator

Generates UPC-A barcodes for ISBN-13 with proper formatting.

#### Constructor

```python
ISBNBarcodeGenerator(barcode_config: Dict[str, Any])
```

**Parameters**:
- `barcode_config` (Dict): Configuration dictionary for barcode settings

#### Methods

##### calculate_barcode_position(cover_dimensions: Tuple[float, float]) -> Position

Calculates barcode position maintaining current location with safety spaces.

**Parameters**:
- `cover_dimensions` (Tuple[float, float]): Cover width and height in inches

**Returns**:
- `Position`: Calculated position for barcode placement

##### validate_safety_spaces(position: Position, cover_dimensions: Tuple[float, float]) -> bool

Ensures adequate safety spaces around barcode with comprehensive validation.

**Parameters**:
- `position` (Position): Barcode position
- `cover_dimensions` (Tuple[float, float]): Cover dimensions

**Returns**:
- `bool`: True if safety spaces are adequate

##### generate_upc_barcode_with_positioning(isbn13: str, cover_specs: Dict) -> BarcodeResult

Generates UPC-A barcode with proper positioning and safety spaces.

**Parameters**:
- `isbn13` (str): ISBN-13 for barcode generation
- `cover_specs` (Dict): Cover specifications with width and height

**Returns**:
- `BarcodeResult`: Complete barcode result with data and positioning

**Example**:
```python
generator = ISBNBarcodeGenerator({})
cover_specs = {"width": 6.0, "height": 9.0}
result = generator.generate_upc_barcode_with_positioning("9780134685991", cover_specs)
```

##### generate_upc_barcode(isbn13: str) -> bytes

Generates UPC-A barcode from ISBN-13.

**Parameters**:
- `isbn13` (str): ISBN-13 to convert

**Returns**:
- `bytes`: Barcode image data

##### format_barcode_numerals(isbn13: str) -> str

Formats bar-code-reader numerals for display.

**Parameters**:
- `isbn13` (str): ISBN-13 to format

**Returns**:
- `str`: Formatted numerals for barcode display

##### validate_barcode_standards(barcode_data: bytes) -> bool

Validates barcode meets industry standards for retail scanning.

**Parameters**:
- `barcode_data` (bytes): Generated barcode data

**Returns**:
- `bool`: True if meets standards

---

## DotgridLayoutManager

**Module**: `codexes.modules.prepress.dotgrid_layout_manager`

### Classes

#### PageSpecs

```python
@dataclass
class PageSpecs:
    width: float
    height: float
    header_height: float
    footer_height: float
    margin_top: float
    margin_bottom: float
    unit: str = "inches"
```

### Class: DotgridLayoutManager

Manages dotgrid positioning for interior pages with proper spacing.

#### Constructor

```python
DotgridLayoutManager(layout_config: Optional[Dict[str, Any]] = None)
```

**Parameters**:
- `layout_config` (Optional[Dict]): Layout configuration dictionary

#### Methods

##### calculate_dotgrid_position(page_specs: PageSpecs) -> Position

Calculates dotgrid position with 0.5in minimum spacing from header.

**Parameters**:
- `page_specs` (PageSpecs): Page specifications

**Returns**:
- `Position`: Calculated dotgrid position

**Example**:
```python
manager = DotgridLayoutManager()
page_specs = PageSpecs(
    width=5.5, height=8.5,
    header_height=0.75, footer_height=0.5,
    margin_top=1.0, margin_bottom=1.0
)
position = manager.calculate_dotgrid_position(page_specs)
```

##### validate_spacing_requirements(position: Position, page_specs: PageSpecs) -> bool

Validates spacing meets minimum requirements with comprehensive validation.

**Parameters**:
- `position` (Position): Dotgrid position
- `page_specs` (PageSpecs): Page specifications

**Returns**:
- `bool`: True if spacing requirements are met

##### update_template_positioning(template_path: str, position: Position) -> None

Updates LaTeX template with new dotgrid positioning.

**Parameters**:
- `template_path` (str): Path to LaTeX template file
- `position` (Position): New position for dotgrid

##### get_standard_page_specs(imprint: str = "xynapse_traces") -> PageSpecs

Gets standard page specifications for different imprints.

**Parameters**:
- `imprint` (str): Imprint name

**Returns**:
- `PageSpecs`: Standard page specifications for the imprint

##### apply_dotgrid_fixes(imprint_path: str) -> bool

Applies dotgrid positioning fixes to imprint templates.

**Parameters**:
- `imprint_path` (str): Path to imprint directory

**Returns**:
- `bool`: True if fixes applied successfully

---

## SubtitleValidator

**Module**: `codexes.modules.metadata.subtitle_validator`

### Classes

#### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool
    current_length: int
    max_length: int
    needs_replacement: bool
    error_message: Optional[str] = None
```

### Class: SubtitleValidator

Validates subtitle length and generates replacements using LLM.

#### Constructor

```python
SubtitleValidator(llm_caller: Optional[LLMCaller] = None)
```

**Parameters**:
- `llm_caller` (Optional[LLMCaller]): LLM caller instance for subtitle generation

#### Methods

##### validate_subtitle_length(subtitle: str, imprint: str) -> ValidationResult

Validates subtitle length against imprint-specific limits with comprehensive validation.

**Parameters**:
- `subtitle` (str): Subtitle to validate
- `imprint` (str): Imprint name for limit lookup

**Returns**:
- `ValidationResult`: Validation result with details

**Example**:
```python
validator = SubtitleValidator()
result = validator.validate_subtitle_length("Long subtitle", "xynapse_traces")
```

##### generate_replacement_subtitle(original_subtitle: str, book_metadata: Dict[str, Any]) -> str

Generates replacement subtitle using nimble-llm-caller.

**Parameters**:
- `original_subtitle` (str): Original subtitle to replace
- `book_metadata` (Dict): Book metadata for context

**Returns**:
- `str`: Generated replacement subtitle

##### process_xynapse_subtitle(subtitle: str, book_metadata: Dict[str, Any]) -> str

Processes xynapse_traces subtitle with length validation and replacement.

**Parameters**:
- `subtitle` (str): Subtitle to process
- `book_metadata` (Dict): Book metadata

**Returns**:
- `str`: Processed subtitle (original or replacement)

**Example**:
```python
book_metadata = {
    "title": "Test Book",
    "subject": "Computer Science",
    "imprint": "xynapse_traces"
}
result = validator.process_xynapse_subtitle("Long subtitle", book_metadata)
```

##### batch_validate_subtitles(subtitle_data: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationResult]

Validates multiple subtitles in batch.

**Parameters**:
- `subtitle_data` (Dict): Dictionary mapping book IDs to subtitle data

**Returns**:
- `Dict[str, ValidationResult]`: Validation results for each book

##### get_character_limit(imprint: str) -> int

Gets character limit for specific imprint.

**Parameters**:
- `imprint` (str): Imprint name

**Returns**:
- `int`: Character limit for the imprint

##### update_character_limits(limits: Dict[str, int]) -> None

Updates character limits for imprints.

**Parameters**:
- `limits` (Dict[str, int]): New character limits mapping

---

## SpineWidthCalculator

**Module**: `codexes.modules.covers.spine_width_calculator`

### Class: SpineWidthCalculator

Enhanced spine width calculator with validation and error handling.

#### Constructor

```python
SpineWidthCalculator(lookup_file_path: str = "resources/SpineWidthLookup.xlsx")
```

**Parameters**:
- `lookup_file_path` (str): Path to Excel lookup file

#### Methods

##### calculate_spine_width_from_lookup(page_count: int, paper_type: str = None) -> float

Calculates spine width using SpineWidthLookup.xlsx logic.

**Parameters**:
- `page_count` (int): Number of pages in book
- `paper_type` (str, optional): Paper type (defaults to "Standard perfect 70")

**Returns**:
- `float`: Calculated spine width in inches

**Example**:
```python
calculator = SpineWidthCalculator()
spine_width = calculator.calculate_spine_width_from_lookup(200, "Standard perfect 70")
```

##### validate_calculation(spine_width: float, page_count: int) -> bool

Validates calculated spine width against expected ranges with comprehensive validation.

**Parameters**:
- `spine_width` (float): Calculated spine width
- `page_count` (int): Page count used for calculation

**Returns**:
- `bool`: True if validation passes

##### distribute_spine_width(spine_width: float, metadata: Dict[str, Any], cover_generator: Any = None) -> None

Distributes spine width to metadata and cover creator components.

**Parameters**:
- `spine_width` (float): Calculated spine width
- `metadata` (Dict or object): Metadata to update
- `cover_generator` (Any, optional): Cover generator to update

##### get_available_paper_types() -> list

Gets list of available paper types from lookup file.

**Returns**:
- `list`: Available paper type names

##### calculate_spine_width_with_validation(page_count: int, paper_type: str = None) -> Tuple[float, bool]

Calculates spine width with validation, returns (spine_width, is_valid).

**Parameters**:
- `page_count` (int): Number of pages
- `paper_type` (str, optional): Paper type

**Returns**:
- `Tuple[float, bool]`: Spine width and validation result

##### get_spine_width_range(paper_type: str = None) -> Tuple[float, float]

Gets the range of spine widths for a given paper type.

**Parameters**:
- `paper_type` (str, optional): Paper type

**Returns**:
- `Tuple[float, float]`: Minimum and maximum spine widths

##### clear_cache() -> None

Clears the sheets cache to force reload.

---

## ValidationSystem

**Module**: `codexes.modules.fixes.validation_system`

### Classes

#### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool
    component: str
    check_name: str
    error_message: Optional[str] = None
    warnings: List[str] = None
```

### Class: ValidationSystem

Comprehensive validation system for all fix components.

#### Constructor

```python
ValidationSystem()
```

#### Methods

##### validate_isbn_input(isbn: str) -> ValidationResult

Validates ISBN input format and structure.

**Parameters**:
- `isbn` (str): ISBN to validate

**Returns**:
- `ValidationResult`: Validation result

##### validate_barcode_positioning(position: Dict[str, float], cover_dimensions: Dict[str, float]) -> ValidationResult

Validates barcode positioning and safety spaces.

**Parameters**:
- `position` (Dict): Position with x, y coordinates
- `cover_dimensions` (Dict): Cover dimensions with width, height

**Returns**:
- `ValidationResult`: Validation result

##### validate_dotgrid_spacing(dotgrid_position: Dict[str, float], page_specs: Dict[str, float]) -> ValidationResult

Validates dotgrid positioning meets spacing requirements.

**Parameters**:
- `dotgrid_position` (Dict): Dotgrid position
- `page_specs` (Dict): Page specifications

**Returns**:
- `ValidationResult`: Validation result

##### validate_subtitle_length(subtitle: str, imprint: str, max_length: int = 38) -> ValidationResult

Validates subtitle length against imprint requirements.

**Parameters**:
- `subtitle` (str): Subtitle to validate
- `imprint` (str): Imprint name
- `max_length` (int): Maximum allowed length

**Returns**:
- `ValidationResult`: Validation result

##### validate_spine_width_calculation(page_count: int, calculated_width: float) -> ValidationResult

Validates spine width calculation results.

**Parameters**:
- `page_count` (int): Number of pages
- `calculated_width` (float): Calculated spine width

**Returns**:
- `ValidationResult`: Validation result

##### validate_template_modification_safety(template_path: str, backup_exists: bool = False) -> ValidationResult

Validates safety of template modifications.

**Parameters**:
- `template_path` (str): Path to template file
- `backup_exists` (bool): Whether backup exists

**Returns**:
- `ValidationResult`: Validation result

##### validate_llm_response(response: str, expected_max_length: int = 38) -> ValidationResult

Validates LLM-generated subtitle response.

**Parameters**:
- `response` (str): LLM response to validate
- `expected_max_length` (int): Expected maximum length

**Returns**:
- `ValidationResult`: Validation result

##### validate_configuration_values(config: Dict[str, Any]) -> ValidationResult

Validates configuration values for all components.

**Parameters**:
- `config` (Dict): Configuration dictionary

**Returns**:
- `ValidationResult`: Validation result

##### run_comprehensive_validation(validation_data: Dict[str, Any]) -> List[ValidationResult]

Runs all validation checks and returns comprehensive results.

**Parameters**:
- `validation_data` (Dict): Data for validation containing various component inputs

**Returns**:
- `List[ValidationResult]`: List of all validation results

**Example**:
```python
validator = ValidationSystem()
validation_data = {
    "isbn": "9780134685991",
    "barcode_position": {"x": 10.0, "y": 0.5},
    "cover_dimensions": {"width": 6.0, "height": 9.0},
    "subtitle": "Test Subtitle",
    "imprint": "xynapse_traces"
}
results = validator.run_comprehensive_validation(validation_data)
```

---

## Error Handling

**Module**: `codexes.modules.fixes.error_handler`

### Enums

#### FixComponentType

```python
class FixComponentType(Enum):
    ISBN_FORMATTER = "isbn_formatter"
    BARCODE_GENERATOR = "barcode_generator"
    DOTGRID_LAYOUT = "dotgrid_layout"
    SUBTITLE_VALIDATOR = "subtitle_validator"
    SPINE_WIDTH_CALCULATOR = "spine_width_calculator"
```

#### ErrorSeverity

```python
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### Functions

#### handle_fix_error(component_type: FixComponentType, error: Exception, context: Dict[str, Any], severity: ErrorSeverity) -> Any

Handles errors with component-specific fallback strategies.

**Parameters**:
- `component_type` (FixComponentType): Type of component that errored
- `error` (Exception): The exception that occurred
- `context` (Dict): Context information for error handling
- `severity` (ErrorSeverity): Severity level of the error

**Returns**:
- `Any`: Fallback result appropriate for the component

**Example**:
```python
try:
    result = some_isbn_operation()
except Exception as e:
    context = {"isbn": "9780134685991", "operation": "format"}
    fallback = handle_fix_error(
        FixComponentType.ISBN_FORMATTER,
        e,
        context,
        ErrorSeverity.MEDIUM
    )
```

---

## Configuration Loading

### Functions

#### load_config(config_path: str) -> Dict[str, Any]

Loads configuration from JSON file.

**Parameters**:
- `config_path` (str): Path to configuration file

**Returns**:
- `Dict[str, Any]`: Loaded configuration

**Example**:
```python
import json

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

# Usage
llm_config = load_config("configs/llm_prompt_config.json")
```

---

## Backward Compatibility

### Functions

#### calculate_spinewidth(sheetname: str, finalpagecount: int) -> float

Backward compatible function for existing code.

**Parameters**:
- `sheetname` (str): Paper type sheet name
- `finalpagecount` (int): Final page count

**Returns**:
- `float`: Calculated spine width

**Example**:
```python
from codexes.modules.covers.spine_width_calculator import calculate_spinewidth

spine_width = calculate_spinewidth("Standard perfect 70", 200)
```

---

## Usage Examples

### Complete Workflow Example

```python
from codexes.modules.metadata.isbn_formatter import ISBNFormatter
from codexes.modules.distribution.isbn_barcode_generator import ISBNBarcodeGenerator
from codexes.modules.prepress.dotgrid_layout_manager import DotgridLayoutManager, PageSpecs
from codexes.modules.metadata.subtitle_validator import SubtitleValidator
from codexes.modules.covers.spine_width_calculator import SpineWidthCalculator
from codexes.modules.fixes.validation_system import ValidationSystem

# Initialize components
isbn_formatter = ISBNFormatter()
barcode_generator = ISBNBarcodeGenerator({})
layout_manager = DotgridLayoutManager()
subtitle_validator = SubtitleValidator()
spine_calculator = SpineWidthCalculator()
validator = ValidationSystem()

# Book data
book_data = {
    "isbn13": "9780134685991",
    "title": "Test Book",
    "subtitle": "A Very Long Subtitle That Needs Processing",
    "page_count": 200,
    "imprint": "xynapse_traces"
}

# Process ISBN
formatted_isbn = isbn_formatter.generate_copyright_page_isbn(book_data["isbn13"])

# Generate barcode
cover_specs = {"width": 6.0, "height": 9.0}
barcode_result = barcode_generator.generate_upc_barcode_with_positioning(
    book_data["isbn13"], 
    cover_specs
)

# Calculate dotgrid position
page_specs = PageSpecs(width=5.5, height=8.5, header_height=0.75, 
                      footer_height=0.5, margin_top=1.0, margin_bottom=1.0)
dotgrid_position = layout_manager.calculate_dotgrid_position(page_specs)

# Process subtitle
processed_subtitle = subtitle_validator.process_xynapse_subtitle(
    book_data["subtitle"], 
    book_data
)

# Calculate spine width
spine_width = spine_calculator.calculate_spine_width_from_lookup(
    book_data["page_count"]
)

# Validate everything
validation_data = {
    "isbn": book_data["isbn13"],
    "barcode_position": {"x": barcode_result.position.x, "y": barcode_result.position.y},
    "cover_dimensions": cover_specs,
    "subtitle": processed_subtitle,
    "imprint": book_data["imprint"],
    "page_count": book_data["page_count"],
    "spine_width": spine_width
}

validation_results = validator.run_comprehensive_validation(validation_data)

# Check results
all_valid = all(result.is_valid for result in validation_results)
print(f"All validations passed: {all_valid}")
```

This API reference provides complete documentation for all public methods and classes in the final fixes implementation.