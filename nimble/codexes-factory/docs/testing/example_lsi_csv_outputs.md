# Example LSI CSV Outputs

This directory contains example LSI ACS CSV files generated from different types of metadata to demonstrate the system's capabilities and provide validation references.

## Files

### complete_book_example.csv
Generated from complete metadata with all major fields populated. Demonstrates comprehensive field mapping and territorial pricing.

**Source Metadata**: Technical book with full metadata
- Title: "Artificial Intelligence: A Comprehensive Guide"
- Author: Dr. Sarah Johnson
- ISBN: 9781234567890
- Publisher: Tech Publications
- 350 pages, $29.99

### fiction_book_example.csv
Generated from fiction book metadata showing genre-specific field handling.

**Source Metadata**: Cyberpunk thriller
- Title: "The Last Algorithm"
- Author: Alex Chen
- ISBN: 9789876543210
- Publisher: Nimble Books LLC
- Imprint: Xynapse Traces

### academic_book_example.csv
Generated from academic book metadata with scholarly publishing settings.

**Source Metadata**: Academic textbook
- Title: "Quantum Computing: Theory and Applications"
- Author: Prof. Maria Rodriguez
- ISBN: 9781111222333
- Publisher: Academic Press International
- Higher pricing, academic discount structure

### children_book_example.csv
Generated from children's book metadata with age-appropriate settings.

**Source Metadata**: Children's picture book
- Title: "The Robot Who Loved to Read"
- Author: Emma Thompson
- ISBN: 9785555666777
- Target age: 4-8 years
- Full-color illustrations

### minimal_metadata_example.csv
Generated from minimal metadata to show default value application and field completion.

**Source Metadata**: Basic required fields only
- Title: "The Future of Technology"
- Author: Dr. Sarah Johnson
- ISBN: 9781234567890
- Publisher: Tech Publications

## Field Mapping Examples

### Direct Mappings
- Title → "Title" field
- Author → "Contributor One" field
- ISBN13 → "ISBN or SKU" field
- Publisher → "Publisher" field

### Computed Mappings
- Page count × 0.0025 → "Weight(Lbs)" field
- Price formatting → "US Suggested List Price" field
- Keywords formatting → "Keywords" field

### Default Mappings
- "Perfect Bound" → "Rendition /Booktype" field
- "Author" → "Contributor One Role" field
- "1" → "Carton Pack Quantity" field

### Territorial Mappings
- US pricing and discounts
- UK pricing with GBP conversion
- EU pricing with EUR conversion
- Specialized territories (Brazil, Germany, etc.)

## Validation Points

### Required Fields
All examples include required LSI fields:
- ISBN or SKU
- Title
- Publisher
- Contributor One
- Pages
- US Suggested List Price

### Format Compliance
- Proper CSV formatting with UTF-8 BOM
- Correct field ordering matching LSI template
- Proper date formats (YYYY-MM-DD)
- Currency formatting ($XX.XX)

### Business Rules
- Wholesale discounts within acceptable ranges
- Returnability settings appropriate for book type
- Territorial rights properly configured
- File submission methods specified

## Usage

These examples can be used for:

1. **Validation Testing**: Compare generated output against known good examples
2. **Field Mapping Verification**: Ensure all fields are properly mapped
3. **Configuration Testing**: Validate different publisher/imprint configurations
4. **Integration Testing**: Test with LSI submission systems
5. **Documentation**: Show expected output format to users

## Generating New Examples

To generate new example files:

```python
from src.codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from tests.test_data.sample_metadata import create_complete_metadata

# Create generator
generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")

# Generate example
metadata = create_complete_metadata()
result = generator.generate_with_validation(
    metadata, 
    "tests/test_data/example_outputs/new_example.csv"
)

print(f"Generated: {result.success}")
print(f"Populated fields: {result.populated_fields_count}")
```