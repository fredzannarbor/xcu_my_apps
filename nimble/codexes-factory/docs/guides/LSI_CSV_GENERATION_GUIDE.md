# LSI CSV Generation Guide

This guide explains how to use the LSI Field Enhancement system to create complete LSI format CSVs with all fields properly filled in, both via command line and the Streamlit interface.

## Overview

The LSI Field Enhancement system provides comprehensive support for generating and mapping all 100+ LSI (Lightning Source Inc.) template fields from CodexMetadata objects. The system consists of two main components:

1. **LLM Field Completer**: Uses AI to intelligently populate missing LSI fields during stage 1 of the book creation process.
2. **LSI ACS Generator**: Creates LSI-compatible CSV files from CodexMetadata objects during stage 4 of the book creation process.

## Command Line Usage

### Option 1: Using the Book Pipeline

The most comprehensive way to generate LSI CSVs is through the book pipeline, which handles the entire process from content generation to LSI CSV creation.

```bash
python run_book_pipeline.py \
  --imprint "xynapse_traces" \
  --schedule-file "imprints/xynapse_traces/xynapse_trace_schedule.json" \
  --model "gemini/gemini-2.5-pro" \
  --lsi-config "configs/default_lsi_config.json" \
  --lsi-template "templates/LSI_ACS_header.csv" \
  --enable-llm-completion \
  --start-stage 1 \
  --end-stage 4
```

Key parameters:
- `--imprint`: The imprint to use for the pipeline
- `--schedule-file`: Path to the schedule JSON file containing book metadata
- `--model`: Primary LLM model for content generation
- `--lsi-config`: Path to LSI configuration file for enhanced field mapping
- `--lsi-template`: Path to LSI template CSV file
- `--enable-llm-completion`: Enable LLM-powered field completion for missing LSI metadata
- `--start-stage`: The stage to start from (1:LLM, 2:Verify, 3:Prepress, 4:LSI)
- `--end-stage`: The stage to end at (1:LLM, 2:Verify, 3:Prepress, 4:LSI)

If you only want to generate LSI CSVs from existing metadata without running the full pipeline, you can use:

```bash
python run_book_pipeline.py \
  --imprint "xynapse_traces" \
  --schedule-file "imprints/xynapse_traces/xynapse_trace_schedule.json" \
  --model "gemini/gemini-2.5-pro" \
  --lsi-config "configs/default_lsi_config.json" \
  --lsi-template "templates/LSI_ACS_header.csv" \
  --enable-llm-completion \
  --start-stage 4 \
  --end-stage 4
```

### Option 2: Using the Test Integration Script

For testing purposes, you can use the `test_book_pipeline_integration.py` script to generate a sample LSI CSV:

```bash
python test_book_pipeline_integration.py
```

This script creates a sample metadata object, completes missing fields using a mock LLM field completer, and generates an LSI CSV file in the `output/pipeline_test` directory.

### Option 3: Direct API Usage

You can also use the LSI ACS Generator directly in your own Python scripts:

```python
from src.codexes.modules.metadata.metadata_models import CodexMetadata
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from src.codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator

# Create or load metadata
metadata = CodexMetadata(
    title="The Future of AI: Balancing Innovation and Ethics",
    author="Dr. Alex Johnson",
    isbn13="9781234567890",
    publisher="Nimble Books LLC",
    imprint="Xynapse Traces",
    page_count=250,
    publication_date="2025-07-20",
    list_price_usd=19.99,
    summary_long="This book explores the future of artificial intelligence..."
)

# Complete missing fields with LLM
field_completer = LLMFieldCompleter(model_name="gemini/gemini-2.5-flash")
metadata = field_completer.complete_missing_fields(metadata, book_content)

# Generate LSI CSV
lsi_generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/default_lsi_config.json",
    log_directory="logs/lsi_generation"
)
result = lsi_generator.generate_with_validation(metadata, "output/lsi_output.csv")

print(f"LSI CSV generation successful: {result.success}")
print(f"Populated fields: {result.populated_fields_count}")
print(f"Empty fields: {result.empty_fields_count}")
```

## Streamlit Interface

The Streamlit interface provides a user-friendly way to generate LSI CSVs. To use it:

1. Navigate to the "Metadata and Distribution" page in the Codexes Factory UI
2. Find the "LSI ACS Generator" section
3. Upload or select a book metadata file
4. Configure the LSI generation options:
   - Select the LSI template file
   - Select the LSI configuration file
   - Enable LLM field completion if needed
5. Click "Generate LSI CSV" to create the CSV file

## Ensuring Complete LSI CSVs

To ensure that all fields are properly filled in:

1. **Use LLM Field Completion**: Enable the `--enable-llm-completion` flag or use the LLMFieldCompleter directly to intelligently populate missing fields.

2. **Configure Default Values**: Create a comprehensive LSI configuration file with default values for common fields:

```json
{
  "defaults": {
    "publisher": "Nimble Books LLC",
    "imprint": "Xynapse Traces",
    "lightning_source_account": "6024045",
    "cover_submission_method": "FTP",
    "text_block_submission_method": "FTP",
    "rendition_booktype": "Perfect Bound",
    "carton_pack_quantity": "1",
    "territorial_rights": "World",
    "returnability": "Yes-Destroy",
    "us_wholesale_discount": "40",
    "uk_wholesale_discount": "40",
    "eu_wholesale_discount": "40"
  },
  "field_overrides": {
    "metadata_contact_dictionary": "Editorial Department"
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
    }
  }
}
```

3. **Verify Field Mappings**: Check that all LSI template fields have corresponding mapping strategies in the `enhanced_field_mappings.py` file.

4. **Review Generation Results**: After generating the CSV, check the generation result for:
   - Number of populated fields
   - Number of empty fields
   - Validation warnings or errors

5. **Examine the Log Files**: Check the detailed logs in the `logs/lsi_generation` directory for:
   - Field mapping details
   - Validation results
   - Error messages

## Troubleshooting

If you encounter issues with LSI CSV generation:

1. **Missing Fields**: If fields are missing in the generated CSV:
   - Check if they are properly mapped in the enhanced field mappings
   - Ensure the metadata object has the required fields
   - Configure default values in the LSI configuration file

2. **Validation Errors**: If validation fails:
   - Check the error messages for specific issues with the metadata
   - Fix the metadata fields that are causing validation errors
   - Update the validation rules if necessary

3. **LLM Completion Failures**: If LLM completion fails:
   - Check the LLM caller configuration and API keys
   - Verify that the prompts are properly configured
   - Try using a different LLM model

4. **Territorial Pricing Issues**: If territorial pricing is incorrect:
   - Check the territorial configurations in the LSI configuration files
   - Verify that the exchange rates are up to date
   - Adjust the pricing multipliers if needed

## Example: Complete LSI CSV Generation

Here's a complete example of generating an LSI CSV with all fields properly filled in:

```python
import os
import json
from src.codexes.modules.metadata.metadata_models import CodexMetadata
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from src.codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator

# Create output directory
output_dir = "output/lsi_test"
os.makedirs(output_dir, exist_ok=True)

# Create or load metadata
metadata = CodexMetadata(
    title="The Future of AI: Balancing Innovation and Ethics",
    author="Dr. Alex Johnson",
    isbn13="9781234567890",
    publisher="Nimble Books LLC",
    imprint="Xynapse Traces",
    page_count=250,
    publication_date="2025-07-20",
    list_price_usd=19.99,
    summary_long="This book explores the future of artificial intelligence..."
)

# Load book content (if available)
book_content = ""
with open("path/to/book_content.txt", "r", encoding="utf-8") as f:
    book_content = f.read()

# Complete missing fields with LLM
field_completer = LLMFieldCompleter(model_name="gemini/gemini-2.5-flash")
metadata = field_completer.complete_missing_fields(metadata, book_content)

# Initialize LSI ACS Generator
lsi_generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/default_lsi_config.json",
    log_directory=f"{output_dir}/logs"
)

# Generate LSI CSV
output_path = f"{output_dir}/lsi_output.csv"
result = lsi_generator.generate_with_validation(metadata, output_path)

# Print generation result
print(f"LSI CSV Generation Result:")
print(f"Success: {result.success}")
print(f"Output Path: {result.output_path}")
print(f"Populated Fields: {result.populated_fields_count}")
print(f"Empty Fields: {result.empty_fields_count}")

# Save metadata to file for reference
metadata_path = f"{output_dir}/metadata.json"
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump({
        "metadata": {
            "title": metadata.title,
            "author": metadata.author,
            "isbn13": metadata.isbn13,
            "publisher": metadata.publisher,
            "imprint": metadata.imprint,
            "page_count": metadata.page_count,
            "publication_date": metadata.publication_date,
            "summary_long": metadata.summary_long,
            # Add other fields as needed
        },
        "llm_completions": getattr(metadata, 'llm_completions', {})
    }, f, indent=2)
```

By following these guidelines, you can ensure that your LSI CSVs are complete and properly formatted for submission to Lightning Source.