# Overwrite Flag Implementation Summary

## Overview
Added the `--overwrite` flag to the Book Pipeline UI with default value set to `True` as requested.

## Changes Made

### 1. Parameter Definition (`src/codexes/modules/ui/parameter_groups.py`)
- Added `overwrite` parameter to the parameter definitions
- Set default value to `True` (enabled by default)
- Placed in `pipeline_control` group alongside other pipeline control parameters
- Parameter type: `CHECKBOX`
- Help text: "Force re-running stages even if output files already exist"

### 2. Command Builder (`src/codexes/modules/ui/command_builder.py`)
- Added `('overwrite', '--overwrite')` to the `boolean_flags` list
- This ensures the `--overwrite` flag is included in the command when the parameter is `True`

### 3. UI Default Values (`src/codexes/pages/10_Book_Pipeline.py`)
- Added `'overwrite': True` to the `default_values` dictionary
- This ensures backward compatibility and sets the default to enabled

## Behavior

### When Overwrite is Enabled (Default)
- The UI will include `--overwrite` in the generated command
- The pipeline will re-run stages even if output files already exist
- This matches the requested "default on" behavior

### When Overwrite is Disabled
- The UI will not include the `--overwrite` flag in the command
- The pipeline will skip stages if output files already exist (original behavior)

## Testing
- Verified parameter definition loads correctly
- Verified command builder includes/excludes flag appropriately
- Verified UI parameter groups load without errors
- Confirmed default value is `True` as requested

## UI Location
The overwrite checkbox will appear in the "Pipeline Control" section of the Book Pipeline UI, alongside other pipeline control parameters like:
- Start Stage
- End Stage
- Max Books
- Begin with Book #
- End with Book #
- Quotes Per Book
- Only Run Specific Prompts

## Command Line Equivalent
When enabled, this generates the equivalent of:
```bash
python run_book_pipeline.py --overwrite [other parameters...]
```

The `--overwrite` flag was already implemented in the CLI (`run_book_pipeline.py`), so this change just exposes it through the UI with the requested default behavior.