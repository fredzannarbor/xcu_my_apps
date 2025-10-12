# Date Computation Strategies

This document provides an overview of the date computation strategies implemented in the LSI Field Enhancement Phase 4 project.

## Overview

The date computation strategies automatically calculate various dates based on available date information in the metadata. These strategies ensure that all date-related fields are populated in the LSI CSV output, improving the field population rate and providing consistent date formatting.

## Implementation

### Base DateComputationStrategy

The `DateComputationStrategy` class serves as the base class for all date computation strategies:

```python
class DateComputationStrategy(ComputedMappingStrategy):
    def __init__(self, date_type: str, offset_days: int = 0, 
                 preferred_base_field: str = None,
                 fallback_to_current: bool = False):
        # ...
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Calculate dates based on available date information
        # ...
```

The strategy performs the following steps:

1. **Extract Base Date**: Gets a base date from metadata using various field names
2. **Apply Offset**: Adds or subtracts days from the base date if specified
3. **Format Date**: Returns the date in YYYY-MM-DD format
4. **Handle Errors**: Gracefully handles parsing errors and missing dates

### Specialized Date Strategies

#### PublicationDateStrategy

Specialized for computing publication dates with priority given to publication-related fields:

```python
class PublicationDateStrategy(DateComputationStrategy):
    def __init__(self, offset_days: int = 0, fallback_to_current: bool = False):
        # Prioritizes: publication_date, pub_date, publish_date, copyright_date
        # ...
```

**Priority Order:**
1. `publication_date`
2. `pub_date`
3. `publish_date`
4. `copyright_date`
5. `release_date`
6. `street_date`
7. `on_sale_date`
8. `available_date`

#### StreetDateStrategy

Specialized for computing street dates (on-sale dates) with intelligent offset handling:

```python
class StreetDateStrategy(DateComputationStrategy):
    def __init__(self, offset_days: int = 7, fallback_to_current: bool = False):
        # Prioritizes: street_date, on_sale_date, release_date
        # Automatically adds offset when using publication_date as base
        # ...
```

**Priority Order:**
1. `street_date`
2. `on_sale_date`
3. `release_date`
4. `available_date`
5. `publication_date` (with offset applied)
6. `pub_date` (with offset applied)

**Smart Offset Logic:**
- If a direct street date field is found, uses it as-is
- If only publication date is available, automatically adds the specified offset
- Default offset is 7 days (typical industry standard)

#### CopyrightDateStrategy

Specialized for computing copyright dates with support for year-only formats:

```python
class CopyrightDateStrategy(DateComputationStrategy):
    def __init__(self, fallback_to_current: bool = False):
        # Handles both full dates and year-only formats
        # ...
```

**Priority Order:**
1. `copyright_date`
2. `copyright_year` (converted to January 1st of that year)
3. `copyright` (if numeric year)
4. `publication_date`
5. `pub_date`
6. `created_date`

**Year Handling:**
- Accepts numeric years (e.g., "2024")
- Validates year range (1900 to current year + 10)
- Converts year to January 1st of that year

## Features

### Flexible Date Parsing

The system can parse dates from various formats:

#### Standard Formats
- `YYYY-MM-DD` (ISO format)
- `YYYY/MM/DD`
- `MM/DD/YYYY` (US format)
- `DD/MM/YYYY` (European format)

#### DateTime Formats
- `YYYY-MM-DD HH:MM:SS`
- `YYYY-MM-DDTHH:MM:SS` (ISO datetime)
- `YYYY-MM-DDTHH:MM:SSZ` (ISO datetime with timezone)

#### Natural Language Formats
- `March 15, 2024`
- `Mar 15, 2024`
- `15 March 2024`
- `15 Mar 2024`

### Configurable Offsets

All strategies support configurable day offsets:

```python
# Street date 7 days after publication
street_strategy = StreetDateStrategy(offset_days=7)

# Street date 14 days after publication
street_strategy = StreetDateStrategy(offset_days=14)

# Past date (30 days before base date)
past_strategy = DateComputationStrategy("past_date", offset_days=-30)
```

### Fallback Options

Strategies can be configured to use the current date as a fallback:

```python
# Use current date if no publication date found
pub_strategy = PublicationDateStrategy(fallback_to_current=True)

# Use current date if no street date found
street_strategy = StreetDateStrategy(fallback_to_current=True)
```

### Field Name Flexibility

The system recognizes various field names for dates:

#### Publication Date Fields
- `publication_date`
- `pub_date`
- `publish_date`

#### Street Date Fields
- `street_date`
- `on_sale_date`
- `release_date`
- `available_date`

#### Copyright Date Fields
- `copyright_date`
- `copyright_year`
- `copyright`

#### Generic Date Fields
- `created_date`
- `date`
- `embargo_date`

## Configuration

Date computation strategies are configured in the enhanced field mappings:

```python
# Date computation strategies
registry.register_strategy("Publication Date", 
                         PublicationDateStrategy(offset_days=0, fallback_to_current=False))

registry.register_strategy("Street Date", 
                         StreetDateStrategy(offset_days=7, fallback_to_current=False))

registry.register_strategy("Copyright Date", 
                         CopyrightDateStrategy(fallback_to_current=False))

registry.register_strategy("On Sale Date", 
                         StreetDateStrategy(offset_days=0, fallback_to_current=False))

registry.register_strategy("Release Date", 
                         DateComputationStrategy("release_date", offset_days=0))
```

## Usage

### Basic Usage

```python
# Calculate publication date
pub_strategy = PublicationDateStrategy()
pub_date = pub_strategy.map_field(metadata, context)

# Calculate street date (7 days after publication)
street_strategy = StreetDateStrategy(offset_days=7)
street_date = street_strategy.map_field(metadata, context)
```

### Advanced Usage

```python
# Calculate street date with fallback to current date
street_strategy = StreetDateStrategy(
    offset_days=14, 
    fallback_to_current=True
)
street_date = street_strategy.map_field(metadata, context)

# Calculate copyright date from year-only field
copyright_strategy = CopyrightDateStrategy()
copyright_date = copyright_strategy.map_field(metadata, context)
```

## Examples

### Example Calculations

For a book with `publication_date = "2024-03-15"`:

- **Publication Date**: `2024-03-15`
- **Street Date (7 days)**: `2024-03-22`
- **Street Date (14 days)**: `2024-03-29`
- **Past Date (-30 days)**: `2024-02-14`

For a book with `copyright_year = "2024"`:

- **Copyright Date**: `2024-01-01`

For a book with `street_date = "March 22, 2024"`:

- **Street Date**: `2024-03-22` (parsed and formatted)

### Edge Cases

The system handles various edge cases:

- **Missing dates**: Returns empty string or uses fallback
- **Invalid formats**: Tries multiple parsing formats
- **Year-only copyright**: Converts to January 1st
- **Future dates**: Validates reasonable year ranges
- **Multiple date fields**: Uses priority order to select best field

## Error Handling

The date computation strategies include comprehensive error handling:

### Parsing Errors
- Tries multiple date formats before giving up
- Logs warnings for unparseable dates
- Returns empty string for invalid dates

### Missing Data
- Searches multiple field names
- Uses fallback dates if configured
- Logs information about missing dates

### Invalid Years
- Validates year ranges (1900 to current + 10)
- Rejects obviously invalid years
- Logs warnings for out-of-range years

## Testing

The date computation strategies can be tested using the test script:

```bash
python test_date_computation.py
```

This script tests:
- Various date formats and parsing
- Different offset calculations
- Specialized strategy behaviors
- Edge cases and error handling
- Fallback mechanisms

## Integration

The date computation strategies are integrated into the LSI field mapping system and will automatically calculate values for date-related LSI fields:

- Publication Date
- Street Date / On Sale Date
- Copyright Date
- Release Date
- Available Date

This integration ensures that date fields are populated even when not provided in the original metadata, and that all dates are consistently formatted according to LSI requirements (YYYY-MM-DD format).