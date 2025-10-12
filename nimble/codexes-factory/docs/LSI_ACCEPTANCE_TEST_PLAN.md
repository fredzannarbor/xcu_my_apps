# LSI Field Enhancement Acceptance Test Plan

## Objective

Verify that the LSI Field Enhancement system correctly completes LSI fields via the Book Pipeline with live API/real books, and that LLM completions are properly saved and included in the final LSI CSV output.

## Prerequisites

1. Access to real book data in a schedule JSON file
2. LSI template CSV file (`templates/LSI_ACS_header.csv`)
3. LSI configuration file (`configs/default_lsi_config.json`)
4. LLM field completion prompts (`prompts/lsi_field_completion_prompts.json`)
5. Valid API keys for LLM services

## Test Environment Setup

1. Ensure all required Python packages are installed
2. Verify that the LSI template CSV file exists
3. Verify that the LSI configuration file exists
4. Verify that the LLM field completion prompts file exists
5. Verify that API keys are properly configured

## Test Procedure

### Step 1: Run Book Pipeline with Focus on LSI Generation

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

### Step 2: Verify LLM Completions Storage

1. Check that LLM completions are saved in the expected location:
   ```
   output/{imprint}_build/{book_reference_id}/metadata/llm_completions_{isbn}_{timestamp}.json
   ```

2. Verify that the LLM completions file contains:
   - Metadata information (title, author, ISBN)
   - LLM completions for each prompt

### Step 3: Verify LSI CSV Output

1. Check that the LSI CSV file is generated:
   ```
   output/{imprint}_build/lsi_csv/{imprint}_batch_LSI.csv
   ```

2. Open the CSV file and verify that:
   - All required fields are populated
   - LLM completions are included in the appropriate fields
   - Field values match the expected format

### Step 4: Generate Field Completion Report

```bash
python generate_lsi_field_report.py \
  --csv "output/{imprint}_build/lsi_csv/{imprint}_batch_LSI.csv" \
  --output "output/{imprint}_build/lsi_csv/field_report.html" \
  --format html
```

### Step 5: Analyze Field Completion Report

1. Open the field completion report in a web browser
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

## Acceptance Criteria

1. **LLM Completion Storage**:
   - LLM completions are saved in the correct location
   - LLM completions file contains all expected data

2. **LSI CSV Output**:
   - LSI CSV file is generated successfully
   - All required fields are populated
   - LLM completions are included in the appropriate fields

3. **Field Completion Report**:
   - Report shows which fields are completed by which strategy
   - Report identifies fields that need additional effort
   - Report provides actual values for each field

4. **Overall Completeness**:
   - At least 80% of LSI fields are populated
   - All critical fields are populated (ISBN, title, author, publisher, etc.)
   - Fields that are intentionally left empty are documented

## Test Data

Use real book data from the production environment to ensure the test is representative of actual usage.

## Expected Results

1. The Book Pipeline successfully generates LSI CSV files
2. LLM completions are saved in the correct location
3. LLM completions are included in the final LSI CSV output
4. The field completion report shows which fields are completed by which strategy
5. The field completion report identifies fields that need additional effort

## Troubleshooting

If the test fails, check the following:

1. **LLM Completion Failures**:
   - Check the LLM caller logs for API errors
   - Verify that the prompts are properly configured
   - Check that the API keys are valid

2. **Field Mapping Issues**:
   - Check the field mapping registry for missing mappings
   - Verify that the LLM completions are properly mapped to LSI fields
   - Check for errors in the mapping strategies

3. **Storage Location Issues**:
   - Check that the output directories exist
   - Verify that the code has write permissions
   - Check for path construction errors

## Field Completion Checklist

| Field Category | Example Fields | Expected Strategy | Notes |
|----------------|----------------|-------------------|-------|
| Basic Information | ISBN, Title, Author | DirectMappingStrategy | Should be directly mapped from metadata |
| Content Description | Summary, Keywords | DirectMappingStrategy or LLMCompletionStrategy | May use LLM if not provided |
| Classification | BISAC Codes, Thema Subjects | DirectMappingStrategy or LLMCompletionStrategy | May use LLM if not provided |
| Contributor Information | Bio, Affiliations | DirectMappingStrategy or LLMCompletionStrategy | May use LLM if not provided |
| Physical Specifications | Weight, Trim Size | ComputedMappingStrategy | Should be computed from other fields |
| Pricing | List Price, Discounts | ComputedMappingStrategy | Should be computed from base price |
| Territorial Information | Rights, Pricing | ComputedMappingStrategy | Should be computed from configuration |
| Special Fields | LSI Special Category | DefaultMappingStrategy | Should use default values |
| Reserved Fields | Reserved 1-12 | DefaultMappingStrategy | Should be empty |

## Post-Test Actions

1. Document any fields that need additional effort
2. Update the field mapping strategies as needed
3. Update the LLM field completion prompts as needed
4. Update the LSI configuration file as needed
5. Re-run the test to verify improvements