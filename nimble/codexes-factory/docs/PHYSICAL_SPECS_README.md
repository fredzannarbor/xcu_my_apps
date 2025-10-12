# Physical Specifications Calculation

This document provides an overview of the physical specifications calculation feature implemented in the LSI Field Enhancement Phase 4 project.

## Overview

The physical specifications calculation feature automatically calculates physical properties of books such as weight, spine width, and thickness based on page count, trim size, and paper type. This ensures that all physical specification fields are populated in the LSI CSV output, improving the field population rate.

## Implementation

### PhysicalSpecsStrategy

The `PhysicalSpecsStrategy` class in `computed_field_strategies.py` implements the physical specifications calculation:

```python
class PhysicalSpecsStrategy(ComputedMappingStrategy):
    def __init__(self, spec_type: str, paper_type: str = "standard"):
        # spec_type: "weight", "spine_width", "thickness"
        # paper_type: "standard", "premium", "lightweight"
        # ...
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate physical specifications based on page count and trim size
        # ...
```

The strategy performs the following steps:

1. **Extract Page Count**: Gets the page count from metadata, handling different field names and formats
2. **Extract Trim Size**: Parses trim size information from various formats (e.g., "6 x 9", "6\" x 9\"")
3. **Determine Binding Type**: Identifies whether the book is paperback or hardcover
4. **Calculate Specification**: Computes the requested specification using paper properties
5. **Format Result**: Returns the result in the appropriate format and units

### Supported Specifications

#### Weight Calculation

Calculates the total weight of the book including:
- Text block weight based on page count and paper weight
- Cover weight based on binding type
- Results formatted in grams (g) or ounces (oz)

#### Spine Width Calculation

Calculates the spine width based on:
- Page count and paper thickness
- Cover thickness adjustment
- Results formatted in inches with appropriate precision

#### Thickness Calculation

Calculates the overall book thickness:
- Based on page count and paper thickness
- Results formatted in inches with appropriate precision

### Paper Types

The system supports different paper types with specific properties:

#### Standard Paper
- Weight per page: 0.8 grams
- Thickness per page: 0.002 inches
- Density: 0.4 g/cm³

#### Premium Paper
- Weight per page: 1.2 grams
- Thickness per page: 0.003 inches
- Density: 0.5 g/cm³

#### Lightweight Paper
- Weight per page: 0.6 grams
- Thickness per page: 0.0015 inches
- Density: 0.35 g/cm³

### Binding Types

The system recognizes different binding types:

#### Paperback
- Cover weight: 15 grams
- Cover thickness: 0.01-0.02 inches

#### Hardcover
- Cover weight: 150 grams
- Cover thickness: 0.02+ inches

## Configuration

Physical specifications can be configured through the enhanced field mappings:

```python
# Physical specifications strategies
registry.register_strategy("Weight", 
                         PhysicalSpecsStrategy("weight", paper_type="standard"))

registry.register_strategy("Spine Width", 
                         PhysicalSpecsStrategy("spine_width", paper_type="standard"))

registry.register_strategy("Thickness", 
                         PhysicalSpecsStrategy("thickness", paper_type="standard"))
```

## Features

### Flexible Page Count Extraction

The system can extract page count from various field names:
- `page_count`
- `pages`
- `total_pages`
- `number_of_pages`
- `page_extent`
- `extent`

It also handles different formats:
- Numeric values: `250`
- String values: `"250 pages"`
- Mixed formats: `"Total: 250"`

### Trim Size Parsing

The system can parse trim size from various formats:
- Standard format: `"6 x 9"`
- With units: `"6\" x 9\""`
- Unicode multiplication: `"6 × 9"`
- Decimal values: `"6.0 x 9.0"`

### Binding Type Detection

The system automatically detects binding type from various field names:
- `binding`
- `binding_type`
- `format`
- `book_format`

It recognizes keywords:
- Hardcover: "hard", "cloth"
- Paperback: "paper", "soft"

### Intelligent Formatting

Results are formatted appropriately:
- **Weight**: Grams for light books, ounces for heavier books
- **Spine Width**: High precision for thin books, standard precision for thick books
- **Thickness**: Consistent with spine width formatting

## Usage

### Basic Usage

```python
# Calculate weight with standard paper
strategy = PhysicalSpecsStrategy("weight", "standard")
weight = strategy.map_field(metadata, context)

# Calculate spine width with premium paper
strategy = PhysicalSpecsStrategy("spine_width", "premium")
spine_width = strategy.map_field(metadata, context)
```

### Advanced Usage

```python
# Calculate thickness with lightweight paper
strategy = PhysicalSpecsStrategy("thickness", "lightweight")
thickness = strategy.map_field(metadata, context)
```

## Examples

### Example Calculations

For a 250-page, 6" x 9" paperback book with standard paper:

- **Weight**: 215g (0.48 oz)
- **Spine Width**: 0.52"
- **Thickness**: 0.50"

For a 400-page, 7" x 10" hardcover book with premium paper:

- **Weight**: 630g (1.4 oz)
- **Spine Width**: 1.22"
- **Thickness**: 1.20"

### Edge Cases

The system handles various edge cases:

- **Missing page count**: Returns empty string
- **Invalid trim size**: Uses default 6" x 9"
- **Unknown binding**: Defaults to paperback
- **Very thin books**: Uses high precision formatting
- **Very thick books**: Adjusts cover thickness accordingly

## Testing

The physical specifications calculation can be tested using the test scripts:

```bash
# Test physical specifications only
python test_physical_specs.py

# Test all computed strategies including physical specs
python test_computed_strategies.py
```

These scripts test various scenarios including:
- Different book sizes and page counts
- Various paper types
- Different binding types
- Edge cases and error handling
- Format parsing capabilities

## Integration

The physical specifications strategies are integrated into the LSI field mapping system and will automatically calculate values for the following LSI fields:

- Weight (lbs)
- Spine Width
- Thickness
- Book dimensions

This integration ensures that physical specification fields are populated even when not provided in the original metadata, significantly improving the field population rate in LSI CSV outputs.