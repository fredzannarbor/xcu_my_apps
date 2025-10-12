# LSI Field Enhancement Guide

## Overview

The LSI Field Enhancement feature provides comprehensive support for generating and mapping all 100+ LSI (Lightning Source Inc.) template fields from CodexMetadata objects. This guide explains how to use the feature, configure field mappings, and integrate it with your book creation workflow.

## Key Components

### 1. LLM Field Completer

The LLM Field Completer uses the LLM caller module to generate high-quality content for creative and subjective LSI fields during stage 1 of the book creation process. It leverages the entire book content to create accurate and relevant metadata.

**Key Features:**
- Generates contributor biographies, BISAC codes, keywords, and more
- Uses the full book content for context-aware field completion
- Supports contributor information extraction with detailed information
- Stores results in the metadata object for later use
- Focuses only on subjective fields that benefit from LLM generation

### 2. Enhanced Field Mappings

The Enhanced Field Mappings system provides comprehensive mapping strategies for all LSI template fields, ensuring that every field in the LSI template is properly populated.

**Key Features:**
- Supports all 100+ LSI template fields with multiple field name variations
- Uses different mapping strategies based on field requirements
- Handles territorial pricing with currency conversion
- Supports special fields like LSI Flex Fields and Reserved fields
- Provides robust fallback mechanisms for field mapping

### 3. LSI ACS Generator

The LSI ACS Generator creates LSI-compatible CSV files from CodexMetadata objects, using the enhanced field mappings to ensure complete and accurate data.

**Key Features:**
- Validates metadata before generation
- Provides detailed logging and error reporting
- Supports batch generation for multiple books
- Handles special cases like blank mode 2 fields

### 4. ISBN Database Management

The ISBN Database Management system provides functionality for managing ISBNs, including importing from Bowker spreadsheets, tracking ISBN status, and assigning ISBNs to books.

**Key Features:**
- Import ISBNs from Bowker spreadsheets
- Track ISBN status (available, privately assigned, publicly assigned)
- Assign ISBNs to books and update status automatically
- Release ISBNs back to the available pool if needed

### 5. Series Management

The Series Management system provides functionality for managing book series metadata, including creating series, tracking series membership, and assigning sequence numbers to books within series.

**Key Features:**
- Create and manage series with publisher isolation
- Support multi-publisher series for collaborative projects
- Automatically assign sequence numbers to books in series
- Integrate series information with LSI CSV generation

### 6. Field Completion Reporting

The Field Completion Reporting system provides detailed reports on field completion status, including which fields were completed, how they were completed, and statistics on field completion quality.

**Key Features:**
- Generate reports in multiple formats (CSV, HTML, JSON, Markdown)
- Track field completion sources (direct, computed, LLM)
- Provide statistics on field completion quality
- Identify empty fields that need attention

### 7. Error Recovery Manager

The Error Recovery Manager provides functionality for handling and recovering from field completion errors, implementing fallback strategies for failed completions, and providing error logging and reporting.

**Key Features:**
- Automatically correct common errors like invalid ISBNs
- Suggest BISAC codes based on title, keywords, and description
- Calculate missing territorial pricing based on US price
- Generate default contributor information when missing

## Integration with Book Creation Workflow

### Stage 1: LLM Field Completion

During the initial book creation stage, use the LLM Field Completer to generate high-quality content for LSI fields:

```python
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter

# Initialize LLM field completer with a specific model
field_completer = LLMFieldCompleter(model_name="gemini/gemini-2.5-flash")

# Complete missing fields
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

The completed fields are stored in the `llm_completions` attribute of the metadata object and also directly mapped to the corresponding metadata fields.

### Stage 2: ISBN Assignment

During the book creation process, assign an ISBN to the book:

```python
from src.codexes.modules.distribution.isbn_database import ISBNDatabase

# Initialize ISBN database
isbn_db = ISBNDatabase()

# Get next available ISBN
isbn = isbn_db.get_next_available_isbn(publisher_id)

# Assign ISBN to book
isbn_db.assign_isbn(isbn, book_id)

# Update metadata with ISBN
metadata.isbn13 = isbn
```

### Stage 3: Series Assignment

If the book is part of a series, assign it to the series:

```python
from src.codexes.modules.distribution.series_registry import SeriesRegistry
from src.codexes.modules.distribution.series_assigner import SeriesAssigner

# Initialize series registry and assigner
registry = SeriesRegistry()
assigner = SeriesAssigner(registry)

# Assign book to series
series_id, sequence_number = assigner.assign_book_to_series(
    metadata, series_name, sequence_number, publisher_id
)
```

### Stage 4: LSI ACS Generation

During the distribution stage, use the LSI ACS Generator to create LSI-compatible CSV files:

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

The generator will use the enhanced field mappings to populate all LSI fields, including those generated during stage 1, and will automatically include series information if the book is part of a series.

## Configuration

### LSI Configuration

The LSI configuration system supports multiple publishers, imprints, and territorial configurations. The configuration is stored in JSON files:

- `configs/default_lsi_config.json`: Default configuration
- `configs/publishers/*.json`: Publisher-specific configurations
- `configs/imprints/*.json`: Imprint-specific configurations

Example configuration with enhanced default values:

```json
{
  "defaults": {
    "publisher": "Nimble Books LLC",
    "imprint": "xynapse traces",
    "lightning_source_account": "6024045",
    "cover_submission_method": "FTP",
    "text_block_submission_method": "FTP",
    "rendition_booktype": "Perfect Bound",
    "carton_pack_quantity": "1",
    "territorial_rights": "World",
    "returnability": "Yes-Destroy",
    "us_wholesale_discount": "40",
    "uk_wholesale_discount": "40",
    "eu_wholesale_discount": "40",
    "edition_number": "1",
    "edition_description": "First Edition",
    "order_type_eligibility": "POD",
    "language_code": "ENG",
    "bisac_category": "TEC000000",
    "metadata_contact": "Editorial Department",
    "weight_lbs": "0.75",
    "trim_width_inches": "6",
    "trim_height_inches": "9",
    "pages": "200",
    "pub_date": "2025-07-18",
    "street_date": "2025-07-25",
    "interior_color": "Black and White",
    "interior_paper": "Cream",
    "binding": "Perfect Bound",
    "cover_type": "Paperback"
  },
  "field_overrides": {
    "metadata_contact_dictionary": "Editorial Department",
    "stamped_text_left": "",
    "stamped_text_center": "",
    "stamped_text_right": ""
  },
  "territorial_configs": {
    "US": {
      "wholesale_discount_percent": "40",
      "returnability": "Yes - Destroy",
      "currency": "USD",
      "pricing_multiplier": 1.0
    },
    "UK": {
      "wholesale_discount_percent": "40",
      "returnability": "No",
      "currency": "GBP",
      "pricing_multiplier": 0.79
    },
    "EU": {
      "wholesale_discount_percent": "40",
      "returnability": "No",
      "currency": "EUR",
      "pricing_multiplier": 0.92
    },
    "AU": {
      "wholesale_discount_percent": "40",
      "returnability": "No",
      "currency": "AUD",
      "pricing_multiplier": 1.45
    },
    "CA": {
      "wholesale_discount_percent": "40",
      "returnability": "No",
      "currency": "CAD",
      "pricing_multiplier": 1.35
    }
  }
}
```

### LLM Field Completion Prompts

The LLM field completion prompts are stored in `prompts/lsi_field_completion_prompts.json`. You can customize these prompts to generate different types of content for LSI fields.

### ISBN Database Configuration

The ISBN database is stored in `data/isbn_database.json`. You can import ISBNs from Bowker spreadsheets using the `import_from_bowker` method:

```python
from src.codexes.modules.distribution.isbn_database import ISBNDatabase

# Initialize ISBN database
isbn_db = ISBNDatabase()

# Import ISBNs from Bowker spreadsheet
stats = isbn_db.import_from_bowker("path/to/bowker_spreadsheet.csv", "publisher-id")
```

### Series Registry Configuration

The series registry is stored in `data/series_registry.json`. You can create series and add books to them using the `SeriesRegistry` and `SeriesAssigner` classes.

## Best Practices

1. **Configure Comprehensive Default Values**: Set up comprehensive default values in your LSI configuration files to minimize the need for LLM completion. The more default values you provide, the more reliable and consistent your field mapping will be.

2. **Use Field Name Variations**: Take advantage of the field name variations system to ensure compatibility with different LSI template formats. Register multiple field names for each strategy to improve mapping robustness.

3. **Complete Subjective Fields Early**: Use the LLM Field Completer during stage 1 of the book creation process to generate high-quality content for subjective fields like contributor bios, descriptions, and classifications.

4. **Use Deterministic Calculations for Objective Fields**: For fields that can be calculated deterministically (like weight, pricing, file paths), use direct calculations rather than LLM generation.

5. **Use Book Content**: Provide the full book content to the LLM Field Completer for more accurate and relevant field completion.

6. **Configure Territorial Pricing**: Set up territorial configurations for accurate pricing in different regions using the configuration system rather than LLM generation.

7. **Validate Before Generation**: Always validate metadata before generating LSI CSV files to catch errors early.

8. **Review Generated Fields**: Review LLM-generated fields for accuracy and relevance before submission.

9. **Manage ISBNs Properly**: Use the ISBN Database Management system to track ISBN status and ensure proper assignment.

10. **Organize Books in Series**: Use the Series Management system to organize books in series and ensure consistent sequence numbering.

11. **Monitor Field Completion Reports**: Regularly review field completion reports to identify fields that need attention.

12. **Handle Errors Gracefully**: Use the Error Recovery Manager to handle and recover from field completion errors.

13. **Customize Default Values by Imprint**: Create imprint-specific configuration files to customize default values for different imprints, ensuring consistent branding and formatting.

## Troubleshooting

### Common Issues

1. **Missing Fields**: If fields are missing in the generated CSV, check if they are properly mapped in the enhanced field mappings.

2. **Validation Errors**: If validation fails, check the error messages for specific issues with the metadata.

3. **LLM Completion Failures**: If LLM completion fails, check the LLM caller configuration and API keys.

4. **Territorial Pricing Issues**: If territorial pricing is incorrect, check the territorial configurations in the LSI configuration files.

5. **ISBN Assignment Failures**: If ISBN assignment fails, check that the ISBN is available and not already assigned.

6. **Series Assignment Issues**: If series assignment fails, check that the series exists and the sequence number is not already taken.

### Logging

The LSI ACS Generator provides detailed logging for troubleshooting:

- Field mapping logs: Show how each field was mapped
- Validation logs: Show validation results for each field
- Error logs: Show detailed error messages for failed operations
- Field completion reports: Show which fields were completed and how

Logs are stored in the `logs/lsi_generation` directory.

### How to Fix Individual Field Issues

If you need to work through field issues one at a time, follow these steps:

#### Step 1: Identify Empty or Problematic Fields

1. Generate a field completion report to identify which fields are empty or have issues:

```python
from src.codexes.modules.distribution.lsi_field_completion_reporter import LSIFieldCompletionReporter

# Initialize reporter
reporter = LSIFieldCompletionReporter(field_registry)

# Generate reports
output_files = reporter.generate_field_strategy_report(
    metadata, lsi_headers, output_dir="output/reports",
    formats=["csv", "html", "md"]
)
```

2. Review the generated report (especially the HTML or Markdown version) to identify fields that are empty or have issues.

#### Step 2: Determine the Best Fix Strategy

For each problematic field, determine the best strategy to fix it:

1. **Add Default Value in Configuration**: For fields that should have consistent default values across all books.
   - Edit `configs/default_lsi_config.json` to add the default value.
   - Example: Adding a default language code:
   ```json
   "defaults": {
     "language_code": "ENG"
   }
   ```

2. **Add Field Name Variation**: If the field is not being recognized due to name mismatch.
   - Edit `src/codexes/modules/distribution/enhanced_field_mappings.py` to add more field name variations.
   - Example: Adding variations for a field:
   ```python
   registry.register_strategy("Language Code", DefaultMappingStrategy(lang_code))
   registry.register_strategy("Language", DefaultMappingStrategy(lang_code))
   registry.register_strategy("Book Language", DefaultMappingStrategy(lang_code))
   ```

3. **Create Custom Mapping Strategy**: For fields that require special calculation or transformation.
   - Create a custom mapping strategy in `src/codexes/modules/distribution/enhanced_field_mappings.py`.
   - Example: Creating a computed strategy for weight based on page count:
   ```python
   def _calculate_weight(metadata: CodexMetadata, context: MappingContext) -> str:
       page_count = int(getattr(metadata, "page_count", 200))
       return f"{0.5 + (page_count * 0.002):.2f}"
   
   registry.register_strategy("Weight(Lbs)", ComputedMappingStrategy(_calculate_weight))
   ```

4. **Improve LLM Completion**: For subjective fields that require LLM generation.
   - Edit the prompts in `prompts/lsi_field_completion_prompts.json` to improve the quality of generated content.
   - Example: Improving a contributor bio prompt:
   ```json
   "generate_contributor_bio": {
     "messages": [
       {
         "role": "system",
         "content": "You are an expert in creating professional author biographies for book metadata."
       },
       {
         "role": "user",
         "content": "Create a professional biography for author {author} who wrote the book '{title}'. The biography should be concise (100-150 words) and highlight their expertise and background relevant to the book topic."
       }
     ],
     "params": {
       "temperature": 0.7,
       "max_tokens": 200
     }
   }
   ```

5. **Direct Metadata Update**: For fields that need specific values for individual books.
   - Update the metadata object directly in your code before generating the CSV.
   - Example: Setting a specific field value:
   ```python
   metadata.contributor_one_bio = "Author is an expert in the field with over 10 years of experience."
   ```

#### Step 3: Test and Verify the Fix

1. After implementing the fix, run the LSI ACS Generator again:

```python
# Generate CSV file with validation and field completion
result = generator.generate_with_validation(metadata, output_path, book_content)
```

2. Generate a new field completion report to verify that the field is now properly populated:

```python
# Generate new report
output_files = reporter.generate_field_strategy_report(
    metadata, lsi_headers, output_dir="output/reports",
    formats=["html"]
)
```

3. Check the generated CSV file to ensure the field has the correct value.

#### Step 4: Repeat for Each Problematic Field

Repeat steps 1-3 for each problematic field until all fields are properly populated.

#### Example: Fixing a Missing Contributor Bio

1. **Identify the issue**: The field completion report shows that "Contributor One BIO" is empty.

2. **Choose a fix strategy**: Since contributor bios are subjective and unique to each author, improve the LLM completion.

3. **Implement the fix**: Update the LLM prompt for contributor bios in `prompts/lsi_field_completion_prompts.json`.

4. **Test the fix**: Run the LSI ACS Generator again and check if the contributor bio is now populated.

5. **Verify**: Generate a new field completion report and check the CSV file to ensure the bio is properly populated.

## Advanced Features

### Field Name Variations

The system supports multiple field name variations for each LSI field, ensuring compatibility with different LSI template formats. When registering field mapping strategies, you can specify multiple field names that should map to the same strategy:

```python
# Register a strategy with multiple field name variations
registry.register_strategy("Lightning Source Account", DefaultMappingStrategy(account_value))
registry.register_strategy("Lightning Source Account #", DefaultMappingStrategy(account_value))
registry.register_strategy("LSI Account", DefaultMappingStrategy(account_value))
registry.register_strategy("LSI Account Number", DefaultMappingStrategy(account_value))
registry.register_strategy("Account Number", DefaultMappingStrategy(account_value))
registry.register_strategy("Account ID", DefaultMappingStrategy(account_value))
```

This ensures that regardless of the exact field name used in the LSI template, the system will correctly map the appropriate value. The enhanced field mappings system includes variations for all common LSI fields, including:

- Account information fields (Lightning Source Account, etc.)
- Submission method fields (Cover Submission Method, etc.)
- Book format fields (Rendition/Booktype, etc.)
- Physical specification fields (Carton Pack Quantity, etc.)
- Territorial rights fields (Territorial Rights, etc.)
- Returnability fields (Returnable, etc.)
- Wholesale discount fields (US Wholesale Discount, etc.)
- Edition information fields (Edition Number, etc.)
- Order type fields (Order Type Eligibility, etc.)
- Language code fields (Language Code, etc.)
- BISAC category fields (BISAC Category, etc.)
- Trim size fields (Custom Trim Width, etc.)
- Weight fields (Weight(Lbs), etc.)
- Page count fields (Pages, etc.)
- Date fields (Pub Date, etc.)
- Metadata contact fields (Metadata Contact, etc.)

### Custom Mapping Strategies

You can create custom mapping strategies for specific fields:

```python
from src.codexes.modules.distribution.field_mapping import MappingStrategy

class CustomMappingStrategy(MappingStrategy):
    def map_field(self, metadata, context):
        # Custom mapping logic
        return custom_value

# Register the custom strategy
registry.register_strategy("Custom Field", CustomMappingStrategy())
```

### Territorial Pricing Strategies

The system supports advanced territorial pricing strategies with exchange rate conversion, wiggle room, and market access fees:

```python
from src.codexes.modules.distribution.territorial_pricing import TerritorialPricingConfig

pricing_config = TerritorialPricingConfig(
    base_currency="USD",
    wiggle_room_percent=5.0,  # 5% wiggle room
    market_access_fee_usd=1.0,  # $1 market access fee
    cache_duration_hours=24
)
```

### Batch Generation

For processing multiple books at once, use the batch generation feature:

```python
result = generator.generate_batch_csv(metadata_list, output_path)
```

### Field Completion Reporting

Generate detailed reports on field completion status:

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

### Error Recovery

Use the Error Recovery Manager to handle and recover from field completion errors:

```python
from src.codexes.modules.distribution.error_recovery_manager import ErrorRecoveryManager

# Initialize error recovery manager
recovery_manager = ErrorRecoveryManager()

# Recover from validation errors
fixed_metadata = recovery_manager.recover_from_validation_errors(metadata, validation_result)

# Get recovery suggestions
suggestions = recovery_manager.get_recovery_suggestions(validation_result)
```

## Conclusion

The LSI Field Enhancement feature provides comprehensive support for generating and mapping all LSI template fields, ensuring accurate and complete metadata for LSI submissions. By integrating LLM field completion, ISBN management, series management, field completion reporting, and error recovery, you can streamline the book creation and distribution process and ensure high-quality metadata for your books.