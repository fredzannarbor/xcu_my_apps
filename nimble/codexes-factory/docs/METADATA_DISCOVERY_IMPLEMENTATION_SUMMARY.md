# Metadata Discovery Implementation Summary

## Overview
Implemented a metadata discovery toggle to prevent LLM from hallucinating publisher, imprint, and author names when they should come from configuration. The system now has two modes:

1. **Standard Mode (Default)**: Uses configured publisher/imprint/author values, prevents LLM override
2. **Discovery Mode**: Allows LLM to discover metadata from content (for public domain works)

## Changes Made

### 1. Prompt Structure (`prompts/prompts.json`)
- **`gemini_get_basic_info`**: Now only asks for `summary` (no publisher/imprint/author)
- **`gemini_get_basic_info_from_public_domain`**: Asks for full metadata including publisher/imprint/author for discovery

### 2. Parameter Definition (`src/codexes/modules/ui/parameter_groups.py`)
- Added `enable_metadata_discovery` parameter
- Type: `CHECKBOX`
- Default: `False` (disabled by default)
- Group: `llm_configuration`
- Help text: "Allow LLM to discover publisher, imprint, and author from content (for public domain works)"

### 3. Command Builder (`src/codexes/modules/ui/command_builder.py`)
- Added `('enable_metadata_discovery', '--enable-metadata-discovery')` to boolean flags
- Generates `--enable-metadata-discovery` flag when enabled

### 4. CLI Arguments (`run_book_pipeline.py`)
- Added `--enable-metadata-discovery` argument
- Action: `store_true`
- Help text explains purpose for public domain works

### 5. UI Default Values (`src/codexes/pages/10_Book_Pipeline.py`)
- Added `'enable_metadata_discovery': False` to default values
- Ensures backward compatibility with discovery disabled by default

### 6. Book Processing Logic (`src/codexes/modules/builders/llm_get_book_data.py`)

#### Function Signature Update
- Added `enable_metadata_discovery: bool = False` parameter to `process_book()`

#### Prompt Selection Logic
- **Discovery Enabled**: Replaces `gemini_get_basic_info` with `gemini_get_basic_info_from_public_domain`
- **Discovery Disabled**: Ensures `gemini_get_basic_info` is used (no metadata discovery)

#### Default Values Logic
- **Discovery Enabled**: Uses minimal defaults (`author=""`, `publisher=""`, `imprint=""`) that can be overridden
- **Discovery Disabled**: Uses configured values (`author="AI Lab for Book-Lovers"`, `publisher="Nimble Books LLC"`, `imprint="xynapse traces"`)

#### Response Processing Protection
- When discovery is disabled, ignores LLM-provided `author`, `publisher`, and `imprint` values
- Logs when protected values are ignored for debugging

### 7. Pipeline Integration (`run_book_pipeline.py`)
- Passes `enable_metadata_discovery=args.enable_metadata_discovery` to `process_book()`

## Behavior

### Standard Mode (Default: Discovery Disabled)
- Uses `gemini_get_basic_info` prompt (only asks for summary)
- Sets configured publisher/imprint/author values
- Ignores any LLM attempts to override these values
- Prevents hallucination of metadata
- Suitable for current xynapse traces use case

### Discovery Mode (Discovery Enabled)
- Uses `gemini_get_basic_info_from_public_domain` prompt (asks for full metadata)
- Starts with empty publisher/imprint/author values
- Allows LLM to populate these from content analysis
- Suitable for public domain works where metadata needs to be discovered

## Use Cases

### Current Imprint (xynapse traces)
- Keep discovery **disabled** (default)
- Publisher and imprint are always known and configured
- Prevents LLM from hallucinating incorrect metadata

### Public Domain Imprints
- Enable discovery when needed
- LLM can analyze content to determine appropriate publisher/imprint
- Useful for historical works or content where metadata isn't predetermined

## UI Location
The metadata discovery checkbox appears in the "LLM Configuration" section of the Book Pipeline UI, alongside other LLM-related settings like:
- Max Retries
- Base Delay
- Enable LLM Field Completion
- Enable ISBN Assignment

## Command Line Usage
```bash
# Standard mode (default)
python run_book_pipeline.py --model gpt-4o --imprint xynapse_traces [other args...]

# Discovery mode
python run_book_pipeline.py --model gpt-4o --imprint xynapse_traces --enable-metadata-discovery [other args...]
```

## Testing
- Verified parameter definition and defaults
- Verified command builder includes/excludes flag appropriately
- Verified prompt selection logic works correctly
- Confirmed UI parameter groups load without errors