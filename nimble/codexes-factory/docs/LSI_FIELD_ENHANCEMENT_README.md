# LSI Field Enhancement System

## Overview

The LSI Field Enhancement system provides comprehensive support for generating and mapping all 100+ LSI (Lightning Source Inc.) template fields from CodexMetadata objects. This system ensures that all LSI fields are properly filled in, either via command line or via the Streamlit interface.

## Key Components

1. **Enhanced Field Mappings**: A comprehensive mapping system that supports all 100+ LSI template fields using various mapping strategies.
2. **LLM Field Completer**: Uses AI to intelligently populate missing LSI fields during the book creation process.
3. **LSI ACS Generator**: Creates LSI-compatible CSV files from CodexMetadata objects with validation and detailed logging.
4. **Configuration System**: Supports multiple publishers, imprints, and territorial configurations.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required Python packages (install with `pip install -r requirements.txt`)
- LSI template CSV file (provided in `templates/LSI_ACS_header.csv`)
- LSI configuration file (provided in `configs/default_lsi_config.json`)

### Command Line Usage

#### Generate LSI CSV for a Single Book

```bash
python generate_lsi_csv.py \
  --input path/to/metadata.json \
  --output path/to/output.csv \
  --config configs/default_lsi_config.json \
  --template templates/LSI_ACS_header.csv \
  --enable-llm
```

#### Generate LSI CSVs for Multiple Books (Batch Processing)

```bash
python generate_lsi_csv.py \
  --batch path/to/metadata/directory \
  --output path/to/output/directory \
  --config configs/default_lsi_config.json \
  --template templates/LSI_ACS_header.csv \
  --enable-llm
```

#### Using the Book Pipeline

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

### Streamlit Interface

The Streamlit interface provides a user-friendly way to generate LSI CSVs:

1. Navigate to the "Metadata and Distribution" page in the Codexes Factory UI
2. Find the "LSI ACS Generator" section
3. Upload or select a book metadata file
4. Configure the LSI generation options
5. Click "Generate LSI CSV" to create the CSV file

## Configuration

### LSI Configuration File

The LSI configuration file (`configs/default_lsi_config.json`) contains default values, field overrides, and territorial configurations:

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

### LLM Field Completion Prompts

The LLM field completion prompts are stored in `prompts/lsi_field_completion_prompts.json`. You can customize these prompts to generate different types of content for LSI fields.

## Testing

### Running Tests

```bash
# Test LSI CSV generation
python test_lsi_csv_generation.py

# Test LLM field completion
python test_llm_field_completer.py

# Test book pipeline integration
python test_book_pipeline_integration.py
```

## Troubleshooting

### Common Issues

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

### Logging

The LSI ACS Generator provides detailed logging for troubleshooting:

- Field mapping logs: Show how each field was mapped
- Validation logs: Show validation results for each field
- Error logs: Show detailed error messages for failed operations

Logs are stored in the `logs/lsi_generation` directory.

## Additional Resources

- [LSI Field Enhancement Guide](docs/LSI_FIELD_ENHANCEMENT_GUIDE.md): Comprehensive guide to using the LSI Field Enhancement system
- [LSI CSV Generation Guide](LSI_CSV_GENERATION_GUIDE.md): Guide to generating LSI CSVs with all fields properly filled in

## Conclusion

The LSI Field Enhancement system provides a comprehensive solution for generating complete LSI format CSVs with all fields properly filled in. By using the LLM Field Completer and the LSI ACS Generator together, you can ensure that your LSI submissions are complete and accurate.