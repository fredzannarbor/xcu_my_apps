# File Path Generation Strategies

This document provides an overview of the file path generation strategies implemented in the LSI Field Enhancement Phase 4 project.

## Overview

The file path generation strategies automatically generate file paths for various book assets (covers, interiors, jackets, etc.) based on ISBN, title, and other metadata. These strategies ensure that all file path fields are populated in the LSI CSV output with consistent, standardized naming conventions.

## Implementation

### Base FilePathStrategy

The `FilePathStrategy` class serves as the base class for all file path generation strategies:

```python
class FilePathStrategy(ComputedMappingStrategy):
    def __init__(self, file_type: str, base_path: str = "", 
                 naming_pattern: str = "{isbn}_{file_type}",
                 include_title: bool = False,
                 max_title_length: int = 50):
        # ...
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        # Generate file paths based on metadata and naming patterns
        # ...
```

The strategy performs the following steps:

1. **Extract ISBN**: Gets ISBN from various field names (isbn13, isbn10, sku)
2. **Apply Naming Pattern**: Uses configurable patterns to build filenames
3. **Clean Filename**: Removes invalid characters and formats appropriately
4. **Add Extension**: Applies appropriate file extensions based on file type
5. **Construct Path**: Combines base path with filename

### Specialized File Path Strategies

#### LSIFilePathStrategy

Specialized for LSI (Lightning Source Inc.) naming conventions:

```python
class LSIFilePathStrategy(FilePathStrategy):
    def __init__(self, file_type: str, base_path: str = ""):
        # Uses LSI-specific naming: {isbn}_{lsi_file_type}
        # Maps file types to LSI conventions (cover -> Cover, interior -> Text)
        # ...
```

**LSI Naming Conventions:**
- `cover` → `Cover`
- `interior` → `Text`
- `jacket` → `Jacket`
- `dust_jacket` → `DustJacket`
- `spine` → `Spine`
- `back_cover` → `BackCover`

**Example Output:**
- `9781234567890_Cover.pdf`
- `9781234567890_Text.pdf`
- `9781234567890_Jacket.pdf`

#### DetailedFilePathStrategy

Creates descriptive filenames including title and author information:

```python
class DetailedFilePathStrategy(FilePathStrategy):
    def __init__(self, file_type: str, base_path: str = "", include_author: bool = False):
        # Uses pattern: {isbn}_{title}_{file_type} or {isbn}_{title}_{author}_{file_type}
        # Includes title truncation and cleaning
        # ...
```

**Features:**
- Includes book title in filename
- Optional author inclusion
- Automatic title truncation (default: 30 characters)
- Special character cleaning

**Example Output:**
- `9781234567890_Python_Programming_cover.pdf`
- `9781234567890_Python_Programming_John_Smith_cover.pdf`

#### OrganizedFilePathStrategy

Creates organized directory structures for better file management:

```python
class OrganizedFilePathStrategy(FilePathStrategy):
    def __init__(self, file_type: str, organize_by_date: bool = True, 
                 organize_by_imprint: bool = False):
        # Creates dynamic directory structure
        # Organizes by publication date and/or imprint
        # ...
```

**Organization Options:**
- **By Date**: Groups files by publication year
- **By Imprint**: Groups files by publishing imprint
- **By File Type**: Groups files by type (covers, interiors, etc.)

**Example Output:**
- `covers/2024/9781234567890_cover.pdf`
- `covers/Tech_Books_Press/2024/9781234567890_cover.pdf`
- `epubs/AI_Publications/2024/9781234567890_epub.epub`

## Features

### Flexible ISBN Extraction

The system can extract ISBNs from various field names:

#### Primary ISBN Fields
- `isbn13` (preferred)
- `isbn_13`
- `isbn`
- `isbn10`
- `isbn_10`

#### Alternative Fields
- `sku`
- `product_id`

#### ISBN Cleaning
- Removes hyphens, spaces, and dots
- Validates ISBN length (10 or 13 digits)
- Handles formatted ISBNs (978-1-23-456789-0)

### Configurable Naming Patterns

The system supports flexible naming patterns using placeholders:

#### Available Placeholders
- `{isbn}` - Book ISBN
- `{file_type}` - File type (cover, interior, etc.)
- `{lsi_file_type}` - LSI-specific file type name
- `{title}` - Book title (cleaned)
- `{author}` - Author name (cleaned)

#### Pattern Examples
```python
# Basic pattern
"{isbn}_{file_type}"  # → 9781234567890_cover.pdf

# With title
"{isbn}_{title}_{file_type}"  # → 9781234567890_Python_Programming_cover.pdf

# LSI pattern
"{isbn}_{lsi_file_type}"  # → 9781234567890_Cover.pdf

# Custom order
"{title}_{isbn}"  # → Python_Programming_9781234567890.pdf
```

### File Type Support

The system supports various file types with appropriate extensions:

#### Print Files
- `cover` → `.pdf`
- `interior` → `.pdf`
- `jacket` → `.pdf`
- `dust_jacket` → `.pdf`
- `spine` → `.pdf`
- `back_cover` → `.pdf`

#### Digital Files
- `epub` → `.epub`
- `mobi` → `.mobi`
- `pdf` → `.pdf`
- `audiobook` → `.mp3`

#### Marketing Files
- `thumbnail` → `.jpg`
- `preview` → `.pdf`

### Filename Cleaning

The system automatically cleans filenames for cross-platform compatibility:

#### Invalid Character Handling
- Replaces `<>:"/\|?*` with underscores
- Consolidates multiple spaces/underscores
- Removes leading/trailing spaces and underscores

#### Length Management
- Truncates long titles (configurable limit)
- Ensures filenames are not empty
- Provides fallback names for missing data

### Directory Organization

The organized file path strategy creates logical directory structures:

#### By File Type
```
covers/
interiors/
jackets/
epubs/
```

#### By Publication Date
```
covers/2024/
covers/2023/
covers/2022/
```

#### By Imprint
```
covers/Tech_Books_Press/
covers/AI_Publications/
covers/Code_Masters/
```

#### Combined Organization
```
covers/Tech_Books_Press/2024/
interiors/AI_Publications/2024/
epubs/Code_Masters/2023/
```

## Configuration

File path strategies are configured in the enhanced field mappings:

```python
# LSI-specific file paths (no base path for direct submission)
registry.register_strategy("Cover Path / Filename", 
                         LSIFilePathStrategy("cover", base_path=""))

registry.register_strategy("Interior Path / Filename", 
                         LSIFilePathStrategy("interior", base_path=""))

# Organized file paths for internal management
registry.register_strategy("Cover File Path", 
                         FilePathStrategy("cover", base_path="covers"))

registry.register_strategy("EPUB File Path", 
                         OrganizedFilePathStrategy("epub", organize_by_date=True))

# Detailed file paths with metadata
registry.register_strategy("PDF File Path", 
                         DetailedFilePathStrategy("pdf", base_path="pdfs", include_author=True))
```

## Usage

### Basic Usage

```python
# Generate basic cover file path
cover_strategy = FilePathStrategy("cover", base_path="covers")
cover_path = cover_strategy.map_field(metadata, context)

# Generate LSI-compliant interior path
interior_strategy = LSIFilePathStrategy("interior")
interior_path = interior_strategy.map_field(metadata, context)
```

### Advanced Usage

```python
# Generate detailed file path with author
detailed_strategy = DetailedFilePathStrategy(
    "cover", 
    base_path="detailed_covers",
    include_author=True
)
detailed_path = detailed_strategy.map_field(metadata, context)

# Generate organized file path by date and imprint
organized_strategy = OrganizedFilePathStrategy(
    "epub",
    organize_by_date=True,
    organize_by_imprint=True
)
organized_path = organized_strategy.map_field(metadata, context)
```

### Custom Naming Patterns

```python
# Custom naming pattern
custom_strategy = FilePathStrategy(
    "cover",
    base_path="custom",
    naming_pattern="{title}_{author}_{isbn}",
    include_title=True
)
custom_path = custom_strategy.map_field(metadata, context)
```

## Examples

### Example File Paths

For a book with:
- ISBN: `9781234567890`
- Title: `"Python Programming Guide"`
- Author: `"John Smith"`
- Imprint: `"Tech Books"`
- Publication Date: `"2024-03-15"`

**Basic Strategy:**
- Cover: `covers/9781234567890_cover.pdf`
- Interior: `interiors/9781234567890_interior.pdf`

**LSI Strategy:**
- Cover: `9781234567890_Cover.pdf`
- Interior: `9781234567890_Text.pdf`

**Detailed Strategy:**
- Cover: `9781234567890_Python_Programming_cover.pdf`
- With Author: `9781234567890_Python_Programming_John_Smith_cover.pdf`

**Organized Strategy:**
- By Date: `covers/2024/9781234567890_cover.pdf`
- By Imprint: `covers/Tech_Books/9781234567890_cover.pdf`
- Combined: `covers/Tech_Books/2024/9781234567890_cover.pdf`

### Edge Cases

The system handles various edge cases:

- **Missing ISBN**: Returns empty string with warning
- **Invalid characters**: Replaces with underscores
- **Long titles**: Truncates to specified length
- **Missing metadata**: Uses fallback values
- **Special characters**: Properly escaped for filenames

## Error Handling

The file path generation strategies include comprehensive error handling:

### Missing Data
- Searches multiple field names for ISBN
- Provides fallback values for missing metadata
- Logs warnings for missing required data

### Invalid Characters
- Automatically cleans filenames
- Replaces problematic characters
- Ensures cross-platform compatibility

### Length Limits
- Truncates long titles and author names
- Prevents filesystem path length issues
- Maintains readability while staying within limits

## Testing

The file path generation strategies can be tested using the test script:

```bash
python test_file_path_generation.py
```

This script tests:
- Various ISBN formats and extraction
- Different naming patterns and strategies
- Special character handling
- Edge cases and error conditions
- Directory organization features

## Integration

The file path generation strategies are integrated into the LSI field mapping system and will automatically generate values for file path fields:

- Cover Path / Filename
- Interior Path / Filename
- Jacket Path / Filename
- EPUB File Path
- PDF File Path

This integration ensures that file path fields are populated with consistent, standardized paths that follow LSI naming conventions and best practices for file organization.