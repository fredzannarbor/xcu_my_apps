# LSI Troubleshooting Guide

This guide provides solutions for common issues encountered when using the LSI Field Enhancement features.

## Table of Contents

1. [Field Completion Issues](#field-completion-issues)
2. [ISBN Management Issues](#isbn-management-issues)
3. [Series Management Issues](#series-management-issues)
4. [Validation Issues](#validation-issues)
5. [LSI CSV Generation Issues](#lsi-csv-generation-issues)
6. [Integration Issues](#integration-issues)

## Field Completion Issues

### LLM Completion Fails

**Symptoms:**
- Fields remain empty after running field completion
- Error messages in logs about LLM completion failures

**Possible Causes:**
- API key issues
- Network connectivity problems
- Invalid prompt configuration

**Solutions:**
1. Check that your LLM API key is valid and properly configured
2. Verify network connectivity to the LLM API
3. Check the prompt configuration in `prompts/lsi_field_completion_prompts.json`
4. Try a different LLM model

```python
# Try a different model
field_completer = LLMFieldCompleter(model_name="gpt-4")
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

### Poor Quality Field Completions

**Symptoms:**
- Generated fields contain irrelevant or low-quality content
- Fields don't match the book content

**Possible Causes:**
- Insufficient book content provided
- Poorly configured prompts
- Using a less capable LLM model

**Solutions:**
1. Provide more comprehensive book content
2. Customize prompts for your specific needs
3. Use a more capable LLM model
4. Manually review and edit generated fields

```python
# Provide more comprehensive book content
with open("path/to/full_book.txt", "r") as f:
    book_content = f.read()

# Use a more capable model
field_completer = LLMFieldCompleter(model_name="gemini/gemini-2.5-pro")
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

### Missing Field Mappings

**Symptoms:**
- Some fields are empty in the generated CSV
- Error messages about missing mapping strategies

**Possible Causes:**
- Missing field mapping strategies
- Incorrect field names

**Solutions:**
1. Check that all required fields have mapping strategies
2. Verify field names match the LSI template
3. Add missing mapping strategies

```python
# Check if a field has a mapping strategy
if not field_registry.has_strategy("Field Name"):
    # Add a mapping strategy
    field_registry.register_strategy("Field Name", DirectMappingStrategy("metadata_field"))
```

## ISBN Management Issues

### No Available ISBNs

**Symptoms:**
- `get_next_available_isbn` returns None
- Error messages about no available ISBNs

**Possible Causes:**
- No ISBNs imported
- All ISBNs already assigned
- Incorrect publisher ID

**Solutions:**
1. Import ISBNs from a Bowker spreadsheet
2. Release unused ISBNs
3. Check the publisher ID

```python
# Import ISBNs
isbn_db = ISBNDatabase()
stats = isbn_db.import_from_bowker("path/to/bowker_spreadsheet.csv", "publisher-id")

# Check available ISBNs
stats = isbn_db.get_statistics()
print(f"Available ISBNs: {stats['available']}")
```

### ISBN Assignment Fails

**Symptoms:**
- `assign_isbn` returns False
- Error messages about ISBN assignment failures

**Possible Causes:**
- ISBN already assigned
- Invalid ISBN
- ISBN not in database

**Solutions:**
1. Check if the ISBN is already assigned
2. Verify the ISBN is valid
3. Check if the ISBN is in the database

```python
# Check ISBN status
status = isbn_db.get_isbn_status(isbn)
if status == "privately_assigned" or status == "publicly_assigned":
    print(f"ISBN {isbn} is already assigned")
elif status is None:
    print(f"ISBN {isbn} not found in database")
```

### Invalid ISBNs

**Symptoms:**
- Validation errors about invalid ISBNs
- LSI rejects submissions due to ISBN issues

**Possible Causes:**
- Incorrect check digit
- Wrong ISBN format
- Typos in ISBN

**Solutions:**
1. Use the ISBN correction functionality
2. Verify ISBNs against Bowker records
3. Ensure ISBNs are properly formatted

```python
# Correct an invalid ISBN
recovery_manager = ErrorRecoveryManager()
corrected_isbn = recovery_manager.attempt_isbn_correction(metadata.isbn13)
if corrected_isbn != metadata.isbn13:
    print(f"Corrected ISBN: {corrected_isbn}")
    metadata.isbn13 = corrected_isbn
```

## Series Management Issues

### Series Creation Fails

**Symptoms:**
- `create_series` raises an exception
- Error messages about series creation failures

**Possible Causes:**
- Empty series name
- Series already exists
- Permission issues with storage file

**Solutions:**
1. Ensure the series name is not empty
2. Check if the series already exists
3. Verify permissions on the storage file

```python
# Check if series exists
existing_series = registry.get_series_by_name(series_name, publisher_id)
if existing_series:
    print(f"Series '{series_name}' already exists")
else:
    # Create series
    series_id = registry.create_series(series_name, publisher_id)
```

### Book Assignment to Series Fails

**Symptoms:**
- `add_book_to_series` raises an exception
- Error messages about sequence number conflicts

**Possible Causes:**
- Series doesn't exist
- Sequence number already taken
- Permission issues

**Solutions:**
1. Verify the series exists
2. Check if the sequence number is already taken
3. Use auto-assignment for sequence numbers

```python
# Check if sequence number is available
if not assigner.validate_sequence_number(series_id, sequence_number):
    # Get next available sequence number
    sequence_number = registry.get_next_sequence_number(series_id)
    print(f"Using next available sequence number: {sequence_number}")

# Assign book to series
series_id, assigned_sequence = assigner.assign_book_to_series(
    metadata, series_name, sequence_number
)
```

### Series Information Missing in LSI CSV

**Symptoms:**
- Series fields are empty in the generated CSV
- Series information not appearing in LSI submissions

**Possible Causes:**
- Series integration not enabled
- Series information not in metadata
- Incorrect field mappings

**Solutions:**
1. Integrate series management with the LSI generator
2. Ensure series information is in the metadata
3. Check field mappings for series fields

```python
# Integrate series management with LSI generator
integrate_series_with_lsi_generator(generator)

# Ensure series information is in metadata
if metadata.series_name and not metadata.series_number:
    # Get series information
    series_info = assigner.get_book_series_info(metadata.uuid)
    if series_info:
        metadata.series_number = str(series_info[0]['sequence_number'])
```

## Validation Issues

### Validation Failures

**Symptoms:**
- `validate_metadata` returns a failed validation result
- Error messages about validation failures

**Possible Causes:**
- Missing required fields
- Invalid field values
- Format issues

**Solutions:**
1. Check validation error messages for specific issues
2. Use the Error Recovery Manager to fix common issues
3. Manually fix issues that cannot be automatically fixed

```python
# Validate metadata
validation_result = generator.validate_metadata(metadata)
if not validation_result.is_valid:
    # Try automatic recovery
    recovery_manager = ErrorRecoveryManager()
    fixed_metadata = recovery_manager.recover_from_validation_errors(metadata, validation_result)
    
    # Check if recovery was successful
    validation_result = generator.validate_metadata(fixed_metadata)
    if not validation_result.is_valid:
        # Get recovery suggestions
        suggestions = recovery_manager.get_recovery_suggestions(validation_result)
        print("Recovery suggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")
```

### Missing Required Fields

**Symptoms:**
- Validation errors about missing required fields
- LSI rejects submissions due to missing fields

**Possible Causes:**
- Fields not completed
- Field mapping issues
- Configuration issues

**Solutions:**
1. Complete missing fields
2. Check field mappings
3. Verify configuration

```python
# Check for missing required fields
report_data = reporter._generate_report_data(metadata, lsi_headers)
empty_fields = [data.field_name for data in report_data if data.is_empty]
print(f"Empty fields: {empty_fields}")

# Complete missing fields
field_completer = LLMFieldCompleter()
metadata = field_completer.complete_missing_fields(metadata, book_content)
```

### Format Issues

**Symptoms:**
- Validation errors about field format issues
- LSI rejects submissions due to format issues

**Possible Causes:**
- Incorrect date formats
- Incorrect price formats
- Incorrect ISBN formats

**Solutions:**
1. Use the Error Recovery Manager to fix format issues
2. Manually fix format issues
3. Update field mapping strategies to ensure correct formats

```python
# Fix date format issues
if hasattr(metadata, 'publication_date') and metadata.publication_date:
    # Ensure date is in YYYY-MM-DD format
    try:
        date_obj = datetime.strptime(metadata.publication_date, "%m/%d/%Y")
        metadata.publication_date = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass

# Fix price format issues
if hasattr(metadata, 'list_price_usd') and metadata.list_price_usd:
    # Ensure price has $ symbol and 2 decimal places
    if isinstance(metadata.list_price_usd, (int, float)):
        metadata.list_price_usd = f"${metadata.list_price_usd:.2f}"
    elif isinstance(metadata.list_price_usd, str) and not metadata.list_price_usd.startswith('$'):
        try:
            price = float(metadata.list_price_usd)
            metadata.list_price_usd = f"${price:.2f}"
        except ValueError:
            pass
```

## LSI CSV Generation Issues

### CSV Generation Fails

**Symptoms:**
- `generate_with_validation` raises an exception
- Error messages about CSV generation failures

**Possible Causes:**
- Validation failures
- File permission issues
- Template issues

**Solutions:**
1. Fix validation issues
2. Check file permissions
3. Verify the template file

```python
# Check if output directory exists
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Generate CSV with validation
try:
    result = generator.generate_with_validation(metadata, output_path)
    if result.success:
        print(f"CSV generated successfully: {output_path}")
    else:
        print(f"CSV generation failed: {result.error}")
except Exception as e:
    print(f"Error generating CSV: {e}")
```

### Missing Fields in CSV

**Symptoms:**
- Some fields are empty in the generated CSV
- LSI rejects submissions due to missing fields

**Possible Causes:**
- Missing field mapping strategies
- Field completion failures
- Configuration issues

**Solutions:**
1. Check field mapping strategies
2. Complete missing fields
3. Verify configuration

```python
# Generate field completion report
reporter = LSIFieldCompletionReporter(field_registry)
report_path = reporter.generate_markdown_report(metadata, lsi_headers, "output/report.md")
print(f"Please review the field completion report at {report_path}")

# Check for missing required fields
report_data = reporter._generate_report_data(metadata, lsi_headers)
empty_fields = [data.field_name for data in report_data if data.is_empty]
print(f"Empty fields: {empty_fields}")
```

### Incorrect Field Values

**Symptoms:**
- Fields have incorrect values in the generated CSV
- LSI rejects submissions due to incorrect field values

**Possible Causes:**
- Incorrect field mapping strategies
- Field completion issues
- Configuration issues

**Solutions:**
1. Check field mapping strategies
2. Review field completion results
3. Verify configuration

```python
# Generate field completion report
reporter = LSIFieldCompletionReporter(field_registry)
report_path = reporter.generate_html_report(metadata, lsi_headers, "output/report.html")
print(f"Please review the field completion report at {report_path}")

# Check field values
field_values = field_registry.apply_mappings(metadata, lsi_headers)
for field, value in field_values.items():
    print(f"{field}: {value}")
```

## Integration Issues

### Field Completion Integration Issues

**Symptoms:**
- Field completion not happening during CSV generation
- Error messages about field completion integration

**Possible Causes:**
- Integration not enabled
- Configuration issues
- LLM API issues

**Solutions:**
1. Ensure field completion integration is enabled
2. Check configuration
3. Verify LLM API access

```python
# Check if field completion integration is enabled
if not hasattr(generator, 'field_completion_integrator'):
    # Enable field completion integration
    integrate_field_completion_with_lsi_generator(generator)

# Test field completion
test_metadata = CodexMetadata(title="Test Book")
result = generator.field_completion_integrator.complete_and_validate_metadata(
    test_metadata, "Test book content", generator.validate_metadata
)
if not result["success"]:
    print(f"Field completion test failed: {result.get('error', 'Unknown error')}")
```

### Series Integration Issues

**Symptoms:**
- Series information not included in CSV
- Error messages about series integration

**Possible Causes:**
- Integration not enabled
- Series registry issues
- Configuration issues

**Solutions:**
1. Ensure series integration is enabled
2. Check series registry
3. Verify configuration

```python
# Check if series integration is enabled
if not hasattr(generator, 'series_integrator'):
    # Enable series integration
    integrate_series_with_lsi_generator(generator)

# Test series integration
test_metadata = CodexMetadata(
    title="Test Book",
    uuid="test-uuid",
    series_name="Test Series",
    series_number="1"
)
# Ensure series data is properly set
generator.series_integrator.ensure_series_data(test_metadata)
```

### Reporting Integration Issues

**Symptoms:**
- Field completion reports not generated
- Error messages about reporting integration

**Possible Causes:**
- Integration not enabled
- Configuration issues
- File permission issues

**Solutions:**
1. Ensure reporting integration is enabled
2. Check configuration
3. Verify file permissions

```python
# Generate field completion report manually
reporter = LSIFieldCompletionReporter(field_registry)
try:
    report_path = reporter.generate_markdown_report(metadata, lsi_headers, "output/report.md")
    print(f"Report generated successfully: {report_path}")
except Exception as e:
    print(f"Error generating report: {e}")
```