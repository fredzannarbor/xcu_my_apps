# LSI Field Enhancement Acceptance Test Guide

This guide provides step-by-step instructions for running an acceptance test with your real data through the Book Pipeline to verify that the LSI Field Enhancement system is working correctly.

## Prerequisites

1. Real book data in a schedule JSON file
2. Valid API keys for LLM services
3. All required Python packages installed

## Step 1: Prepare Your Test Environment

1. Make sure your schedule JSON file is properly formatted:

```json
{
  "publishing_schedule": [
    {
      "month": "July",
      "year": 2025,
      "books": [
        {
          "title": "Your Book Title",
          "author": "Your Author Name",
          "isbn13": "9781234567890",
          "publisher": "Nimble Books LLC",
          "imprint": "Xynapse Traces",
          "page_count": 250,
          "publication_date": "2025-07-20",
          "list_price_usd": 19.99,
          "summary_long": "Your book summary..."
          // Other metadata fields
        }
      ]
    }
  ]
}
```

2. Verify that your LSI configuration file exists:
   - Default location: `configs/default_lsi_config.json`
   - Contains default values, field overrides, and territorial configurations

3. Verify that your LSI template file exists:
   - Default location: `templates/LSI_ACS_header.csv`
   - Contains all required LSI field headers

4. Verify that your LLM field completion prompts file exists:
   - Default location: `prompts/lsi_field_completion_prompts.json`
   - Contains prompts for generating missing LSI fields

## Step 2: Run the Book Pipeline

Run the Book Pipeline with the following command, focusing only on Stage 4 (LSI CSV Generation):

```bash
python run_book_pipeline.py \
  --imprint "xynapse_traces" \
  --schedule-file "imprints/xynapse_traces/xynapse_trace_schedule.json" \
  --model "gemini/gemini-2.5-pro" \
  --lsi-config "configs/default_lsi_config.json" \
  --lsi-template "templates/LSI_ACS_header.csv" \
  --enable-llm-completion \
  --start-stage 4 \
  --end-stage 4 \
  --verbose
```

Key parameters:
- `--imprint`: Your imprint name
- `--schedule-file`: Path to your schedule JSON file
- `--model`: LLM model to use for field completion
- `--lsi-config`: Path to LSI configuration file
- `--lsi-template`: Path to LSI template CSV file
- `--enable-llm-completion`: Enable LLM-powered field completion
- `--start-stage 4 --end-stage 4`: Focus only on Stage 4 (LSI CSV Generation)
- `--verbose`: Enable verbose logging

## Step 3: Verify LLM Completions Storage

1. Check that LLM completions are saved in the expected location:
   ```
   output/{imprint}_build/{book_reference_id}/metadata/llm_completions_{isbn}_{timestamp}.json
   ```

2. Open the LLM completions file and verify that it contains:
   - Metadata information (title, author, ISBN)
   - LLM completions for each prompt

Example command to find LLM completion files:
```bash
find output/ -name "llm_completions_*.json"
```

## Step 4: Verify LSI CSV Output

1. Check that the LSI CSV file is generated:
   ```
   output/{imprint}_build/lsi_csv/{imprint}_batch_LSI.csv
   ```

2. Open the CSV file in a spreadsheet application and verify that:
   - All required fields are populated
   - LLM completions are included in the appropriate fields
   - Field values match the expected format

## Step 5: Review Field Completion Report

1. Open the field completion report in a web browser:
   ```
   output/{imprint}_build/lsi_csv/{imprint}_field_report.html
   ```

2. Review the field completion statistics:
   - Total fields
   - Populated fields
   - Empty fields
   - Completeness percentage

3. Review the strategy breakdown:
   - DirectMappingStrategy
   - ComputedMappingStrategy
   - DefaultMappingStrategy
   - ConditionalMappingStrategy
   - LLMCompletionStrategy

4. Review the field details:
   - Field name
   - Strategy
   - Value
   - Source
   - Empty status
   - LLM value

5. Identify fields that need additional effort:
   - Empty fields that should be populated
   - Fields with incorrect values
   - Fields that should use a different strategy

## Step 6: Generate Additional Reports (Optional)

If you want more detailed information about specific CSV files, you can use the field report generator directly:

```bash
python generate_lsi_field_report.py \
  --csv "output/{imprint}_build/lsi_csv/{imprint}_batch_LSI.csv" \
  --output "output/{imprint}_build/lsi_csv/detailed_field_report.html" \
  --format html \
  --config "configs/default_lsi_config.json"
```

## Troubleshooting

### LLM Completion Issues

If LLM completions are not being saved or used:

1. Check that the `--enable-llm-completion` flag is set
2. Verify that the LLM API keys are properly configured
3. Check the logs for API errors
4. Verify that the prompts file exists and is properly formatted

### Field Mapping Issues

If fields are not being properly mapped:

1. Check the field mapping registry for missing mappings
2. Verify that the LLM completions are properly mapped to LSI fields
3. Check for errors in the mapping strategies

### Storage Location Issues

If files are not being saved in the expected locations:

1. Check that the output directories exist
2. Verify that the code has write permissions
3. Check for path construction errors

## Field Completion Checklist

Use this checklist to verify that critical fields are properly populated:

- [ ] ISBN or SKU
- [ ] Title
- [ ] Publisher
- [ ] Imprint
- [ ] Contributor One (Author)
- [ ] Pages
- [ ] Pub Date
- [ ] US Suggested List Price
- [ ] US Wholesale Discount
- [ ] Annotation / Summary
- [ ] Short Description
- [ ] Keywords
- [ ] BISAC Category
- [ ] Language Code
- [ ] Rendition /Booktype
- [ ] Custom Trim Width (inches)
- [ ] Custom Trim Height (inches)
- [ ] Contributor One BIO
- [ ] Contributor One Affiliations
- [ ] Contributor One Professional Position
- [ ] Contributor One Location
- [ ] Contributor One Prior Work
- [ ] Territorial Rights
- [ ] Edition Number
- [ ] Edition Description

## Next Steps

After running the acceptance test:

1. Document any fields that need additional effort
2. Update the field mapping strategies as needed
3. Update the LLM field completion prompts as needed
4. Update the LSI configuration file as needed
5. Re-run the test to verify improvements