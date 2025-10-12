# LSI Best Practices Guide

This guide provides best practices for using the LSI Field Enhancement features to ensure high-quality metadata for your LSI submissions.

## Table of Contents

1. [Field Completion Best Practices](#field-completion-best-practices)
2. [ISBN Management Best Practices](#isbn-management-best-practices)
3. [Series Management Best Practices](#series-management-best-practices)
4. [Validation and Error Recovery Best Practices](#validation-and-error-recovery-best-practices)
5. [Reporting Best Practices](#reporting-best-practices)
6. [Integration Best Practices](#integration-best-practices)

## Field Completion Best Practices

### Complete Subjective Fields Early

Use the LLM Field Completer during stage 1 of the book creation process to generate high-quality content for subjective fields like contributor bios, descriptions, and classifications.

```python
# Complete fields early in the process
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

### Use Book Content for Context

Always provide the full book content to the LLM Field Completer for more accurate and relevant field completion.

```python
# Load book content
with open("path/to/book.txt", "r") as f:
    book_content = f.read()

# Complete fields with book content
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

### Use Deterministic Calculations for Objective Fields

For fields that can be calculated deterministically (like weight, pricing, file paths), use direct calculations rather than LLM generation.

```python
# Calculate weight based on page count
page_count = metadata.page_count or 0
weight = page_count * 0.0025  # Approximate weight in lbs
metadata.weight_lbs = f"{weight:.2f}"
```

### Review Generated Fields

Always review LLM-generated fields for accuracy and relevance before submission.

```python
# Generate field completion report
reporter = LSIFieldCompletionReporter(field_registry)
report_path = reporter.generate_markdown_report(metadata, lsi_headers, "output/report.md")

# Open the report for review
print(f"Please review the field completion report at {report_path}")
```

### Customize Prompts for Your Content

Customize the LLM field completion prompts to better match your content and style.

```python
# Create a custom prompts file
custom_prompts = {
    "generate_contributor_bio": {
        "messages": [
            {"role": "system", "content": "You are an expert biographer."},
            {"role": "user", "content": "Write a professional bio for {author}, the author of {title}."}
        ],
        "params": {"temperature": 0.7, "max_tokens": 300}
    }
}

# Save custom prompts
with open("prompts/custom_prompts.json", "w") as f:
    json.dump(custom_prompts, f, indent=2)

# Use custom prompts
field_completer = LLMFieldCompleter(prompts_path="prompts/custom_prompts.json")
```

## ISBN Management Best Practices

### Import ISBNs in Bulk

Import ISBNs from Bowker spreadsheets in bulk to ensure a consistent pool of available ISBNs.

```python
# Import ISBNs from Bowker spreadsheet
isbn_db = ISBNDatabase()
stats = isbn_db.import_from_bowker("path/to/bowker_spreadsheet.csv", "publisher-id")
print(f"Imported {stats['imported']} ISBNs, {stats['available']} available")
```

### Assign ISBNs Early

Assign ISBNs to books early in the process to ensure they are properly tracked.

```python
# Assign ISBN during initial metadata creation
isbn = isbn_db.get_next_available_isbn(publisher_id)
if isbn:
    isbn_db.assign_isbn(isbn, metadata.uuid)
    metadata.isbn13 = isbn
```

### Mark ISBNs as Published

Mark ISBNs as published when the book is actually published to maintain accurate records.

```python
# Mark ISBN as published when the book is published
isbn_db.mark_as_published(metadata.isbn13)
```

### Release Unused ISBNs

Release ISBNs that are no longer needed to keep the pool of available ISBNs accurate.

```python
# Release ISBN if the book is cancelled
isbn_db.release_isbn(metadata.isbn13)
```

### Regularly Audit ISBN Usage

Regularly audit ISBN usage to ensure that all ISBNs are properly tracked.

```python
# Get ISBN statistics
stats = isbn_db.get_statistics()
print(f"Total ISBNs: {stats['total']}")
print(f"Available ISBNs: {stats['available']}")
print(f"Privately assigned ISBNs: {stats['privately_assigned']}")
print(f"Publicly assigned ISBNs: {stats['publicly_assigned']}")
```

## Series Management Best Practices

### Create Series with Clear Names

Create series with clear, descriptive names to make them easy to identify.

```python
# Create a series with a clear name
series_id = registry.create_series("The AI Revolution Series", publisher_id)
```

### Use Multi-Publisher Series for Collaborations

Use multi-publisher series for collaborative projects that involve multiple publishers.

```python
# Create a multi-publisher series
series_id = registry.create_series("Collaborative AI Series", publisher_id, multi_publisher=True)
```

### Assign Sequence Numbers Consistently

Assign sequence numbers consistently to ensure that books appear in the correct order.

```python
# Assign book to series with a specific sequence number
series_id, sequence_number = assigner.assign_book_to_series(
    metadata, "The AI Revolution Series", sequence_number=3
)
```

### Add Series Information to Book Metadata

Always add series information to book metadata to ensure it appears in the LSI CSV.

```python
# Update metadata with series information
metadata.series_name = "The AI Revolution Series"
metadata.series_number = "3"
```

### Organize Series by Publisher

Organize series by publisher to make them easier to manage.

```python
# Get series for a specific publisher
publisher_series = registry.get_series_for_publisher(publisher_id)
```

## Validation and Error Recovery Best Practices

### Validate Before Generation

Always validate metadata before generating LSI CSV files to catch errors early.

```python
# Validate metadata before generation
validation_result = generator.validate_metadata(metadata)
if not validation_result.is_valid:
    print("Validation failed:")
    for error in validation_result.errors:
        print(f"- {error}")
```

### Use Error Recovery for Common Issues

Use the Error Recovery Manager to automatically fix common issues like invalid ISBNs.

```python
# Recover from validation errors
recovery_manager = ErrorRecoveryManager()
fixed_metadata = recovery_manager.recover_from_validation_errors(metadata, validation_result)
```

### Get Recovery Suggestions

Get recovery suggestions for issues that cannot be automatically fixed.

```python
# Get recovery suggestions
suggestions = recovery_manager.get_recovery_suggestions(validation_result)
print("Recovery suggestions:")
for suggestion in suggestions:
    print(f"- {suggestion}")
```

### Correct ISBNs Automatically

Use the ISBN correction functionality to automatically fix invalid ISBNs.

```python
# Correct an invalid ISBN
corrected_isbn = recovery_manager.attempt_isbn_correction(metadata.isbn13)
if corrected_isbn != metadata.isbn13:
    print(f"Corrected ISBN: {corrected_isbn}")
    metadata.isbn13 = corrected_isbn
```

### Calculate Missing Pricing

Calculate missing territorial pricing based on the US price.

```python
# Calculate missing UK price
if not metadata.uk_suggested_list_price and metadata.list_price_usd:
    uk_price = recovery_manager.calculate_missing_pricing(metadata.list_price_usd, 'UK')
    metadata.uk_suggested_list_price = uk_price
```

## Reporting Best Practices

### Generate Comprehensive Reports

Generate comprehensive reports on field completion status to identify issues.

```python
# Generate reports in multiple formats
reporter = LSIFieldCompletionReporter(field_registry)
output_files = reporter.generate_field_strategy_report(
    metadata, lsi_headers, output_dir="output/reports",
    formats=["csv", "html", "json", "md"]
)
```

### Review Reports Regularly

Regularly review field completion reports to identify fields that need attention.

```python
# Generate and open a report
report_path = reporter.generate_markdown_report(metadata, lsi_headers, "output/report.md")
print(f"Please review the field completion report at {report_path}")
```

### Track Field Completion Sources

Track the sources of field values to understand how fields are being completed.

```python
# Generate a report with field sources
report_path = reporter.generate_field_strategy_report(
    metadata, lsi_headers, output_dir="output/reports",
    formats=["html"]
)["html"]
print(f"Field sources report: {report_path}")
```

### Monitor Completion Rates

Monitor field completion rates to ensure that metadata is complete.

```python
# Generate a report and check completion rate
report_data = reporter._generate_report_data(metadata, lsi_headers)
stats = reporter._calculate_statistics(report_data)
print(f"Field completion rate: {stats.completion_percentage:.1f}%")
```

### Identify Empty Fields

Identify empty fields that need attention.

```python
# Generate a report and identify empty fields
report_data = reporter._generate_report_data(metadata, lsi_headers)
empty_fields = [data.field_name for data in report_data if data.is_empty]
print(f"Empty fields: {empty_fields}")
```

## Integration Best Practices

### Integrate Field Completion with LSI Generator

Integrate field completion with the LSI ACS Generator to ensure that all fields are properly completed.

```python
# Integrate field completion with LSI generator
integrate_field_completion_with_lsi_generator(generator)
```

### Integrate Series Management with LSI Generator

Integrate series management with the LSI ACS Generator to ensure that series information is properly included.

```python
# Integrate series management with LSI generator
integrate_series_with_lsi_generator(generator)
```

### Use a Consistent Workflow

Use a consistent workflow for book creation and distribution to ensure that all steps are properly followed.

```python
# Example workflow
def process_book(metadata, book_content):
    # Step 1: Complete missing fields
    field_completer = LLMFieldCompleter()
    metadata = field_completer.complete_missing_fields(metadata, book_content)
    
    # Step 2: Assign ISBN
    isbn_db = ISBNDatabase()
    isbn = isbn_db.get_next_available_isbn(metadata.publisher)
    if isbn:
        isbn_db.assign_isbn(isbn, metadata.uuid)
        metadata.isbn13 = isbn
    
    # Step 3: Assign to series (if applicable)
    if metadata.series_name:
        registry = SeriesRegistry()
        assigner = SeriesAssigner(registry)
        assigner.assign_book_to_series(metadata, metadata.series_name)
    
    # Step 4: Generate LSI CSV
    generator = LsiAcsGenerator()
    integrate_field_completion_with_lsi_generator(generator)
    integrate_series_with_lsi_generator(generator)
    result = generator.generate_with_validation(metadata, f"output/{metadata.isbn13}.csv", book_content)
    
    return result
```

### Use Configuration Files

Use configuration files to customize the behavior of the LSI Field Enhancement features.

```python
# Load configuration from file
with open("configs/default_lsi_config.json", "r") as f:
    config = json.load(f)

# Initialize LSI ACS generator with configuration
generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/default_lsi_config.json"
)
```

### Monitor Logs

Monitor logs to identify issues and track the progress of field completion and LSI generation.

```python
# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/lsi_generation.log"),
        logging.StreamHandler()
    ]
)
```