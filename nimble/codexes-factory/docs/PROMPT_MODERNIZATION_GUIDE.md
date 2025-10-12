# Prompt Modernization Guide

This guide explains the prompt modernization process and tools for converting old-style prompts to the modern messages format.

## Background

The Codexes Factory project originally used a simple prompt format:

```json
{
  "my_prompt": {
    "prompt": "Generate something based on {variable}",
    "tags": ["tag1", "tag2"]
  }
}
```

This has been modernized to use the messages format that works better with current LLM infrastructure:

```json
{
  "my_prompt": {
    "params": {
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "messages": [
      {
        "role": "system",
        "content": "You are a professional specialist. You MUST respond ONLY in valid JSON format."
      },
      {
        "role": "user",
        "content": "Generate something based on {variable}"
      }
    ],
    "tags": ["tag1", "tag2"]
  }
}
```

## Benefits of Modern Format

1. **Better LLM Integration**: Works seamlessly with the current LLM caller infrastructure
2. **Consistent JSON Responses**: System messages enforce JSON-only responses
3. **Proper Role Definition**: Clear system messages establish the AI's role and expertise
4. **Optimized Parameters**: Temperature and max_tokens are set appropriately for each task type
5. **Error Reduction**: Eliminates the JSON parsing errors that occurred with conversational responses

## Tools

### 1. Prompt Modernizer Utility

**Location**: `src/codexes/utilities/prompt_modernizer.py`

**Usage**:
```bash
# Convert a single file
python src/codexes/utilities/prompt_modernizer.py prompts/my_prompts.json

# Convert with output to different file
python src/codexes/utilities/prompt_modernizer.py input.json output.json

# Verbose mode
python src/codexes/utilities/prompt_modernizer.py --verbose prompts/my_prompts.json
```

**Features**:
- Automatically detects old-style prompts
- Generates appropriate system messages based on prompt content and tags
- Sets optimal parameters (temperature, max_tokens) based on task type
- Preserves all existing metadata and tags
- Validates JSON output

### 2. Batch Modernization Script

**Location**: `modernize_prompts.py` (project root)

**Usage**:
```bash
# Modernize all prompt files in the project
python modernize_prompts.py

# Dry run to see what would be changed
python modernize_prompts.py --dry-run

# Verbose output
python modernize_prompts.py --verbose
```

**Features**:
- Automatically finds all prompt files in the project
- Processes prompts in `prompts/` directory
- Processes imprint-specific prompts in `imprints/*/prompts.json`
- Supports dry-run mode for safe testing

## Conversion Logic

### System Message Generation

The modernizer automatically generates appropriate system messages based on:

1. **Tags**: Determines the AI's role (e.g., "metadata" → "book metadata specialist")
2. **Prompt Content**: Detects JSON requirements and task complexity
3. **Prompt Key**: Uses naming patterns to infer specialization

### Parameter Optimization

**Temperature Settings**:
- `0.3`: Technical, metadata, classification tasks
- `0.4`: Abstracts, summaries
- `0.5`: General tasks (default)
- `0.7`: Creative writing, marketing content

**Max Tokens Settings**:
- `300`: Short responses, brief descriptions
- `500`: Standard responses
- `800`: Biographies, glossaries, indexes
- `1000`: Default
- `1500`: Long content, detailed annotations

### JSON Enforcement

All prompts that require JSON responses get explicit system instructions:
```
"You MUST respond ONLY in valid JSON format. Do not include any text outside the JSON structure."
```

## File Locations

The modernizer processes prompt files in these locations:

- `prompts/*.json` - Main prompt files
- `imprints/*/prompts.json` - Imprint-specific prompts
- `imprints/*/prompts/*.json` - Additional imprint prompt directories

## Validation

After modernization, the tools validate:

1. **JSON Syntax**: Ensures all files remain valid JSON
2. **Required Fields**: Verifies messages format is properly structured
3. **Parameter Values**: Checks that temperature and max_tokens are reasonable

## Troubleshooting

### Common Issues

1. **JSON Parsing Errors**: Usually caused by old-style prompts returning conversational text instead of JSON
   - **Solution**: Run the modernizer to convert to messages format

2. **Missing System Messages**: Old prompts lack role definition
   - **Solution**: Modernizer automatically generates appropriate system messages

3. **Inconsistent Parameters**: Old prompts used default parameters for all tasks
   - **Solution**: Modernizer sets task-appropriate temperature and max_tokens

### Verification

After running the modernizer, verify the conversion:

```bash
# Check JSON syntax
python -c "import json; json.load(open('prompts/prompts.json'))"

# Test a specific prompt (if you have test infrastructure)
python test_prompt.py my_prompt_key
```

## Best Practices

### For New Prompts

Always create new prompts in the modern format:

```json
{
  "my_new_prompt": {
    "params": {
      "temperature": 0.5,
      "max_tokens": 800
    },
    "messages": [
      {
        "role": "system",
        "content": "You are a [specific role]. [JSON requirement if needed]."
      },
      {
        "role": "user",
        "content": "Your task description with {variables}"
      }
    ],
    "tags": ["relevant", "tags"]
  }
}
```

### For JSON Responses

Always include JSON enforcement in the system message:
```
"You MUST respond ONLY in valid JSON format. Do not include any text outside the JSON structure."
```

### Parameter Guidelines

- Use lower temperature (0.2-0.4) for factual, technical tasks
- Use higher temperature (0.6-0.8) for creative tasks
- Set max_tokens based on expected response length
- Consider the task complexity when setting parameters

## Migration Status

As of the latest update, all prompt files have been modernized:

- ✅ `prompts/prompts.json` - Main prompts
- ✅ `prompts/enhanced_lsi_field_completion_prompts.json` - Already modern
- ✅ `prompts/lsi_field_completion_prompts.json` - Already modern  
- ✅ `prompts/codexes_user_prompts.json` - Converted 48 prompts
- ✅ `prompts/nimble_proprietary_prompts.json` - Converted 2 prompts
- ✅ `imprints/xynapse_traces/prompts.json` - Converted 13 prompts
- ✅ `imprints/admin/prompts.json` - Converted 9 prompts
- ✅ All other imprint-specific prompt files

## Future Maintenance

1. **New Prompts**: Always use the modern format for new prompts
2. **Regular Validation**: Run `python modernize_prompts.py --dry-run` periodically to check for any old-style prompts
3. **Testing**: Test prompts after modernization to ensure they work as expected
4. **Documentation**: Update this guide when adding new prompt types or conversion logic