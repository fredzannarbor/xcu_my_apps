# Batch Transformation CLI Guide

## Overview

The Batch Transformation CLI (`batch_transform_cli.py`) provides a powerful command-line interface for transforming CodexObjects with batch processing, quality assessment, history tracking, and rollback capabilities.

## Installation & Setup

```bash
# Ensure you're in the project root directory
cd codexes-factory

# The CLI tool is ready to use with uv
uv run python batch_transform_cli.py --help
```

## Commands Overview

The CLI provides four main commands:

1. **`single`** - Transform a single file
2. **`batch`** - Transform multiple files
3. **`history`** - View transformation history
4. **`rollback`** - Manage snapshots and rollback operations

## Single File Transformation

### Basic Usage

```bash
# Transform an idea to a synopsis
uv run python batch_transform_cli.py single idea.json --target synopsis

# Transform with custom output file
uv run python batch_transform_cli.py single story.json --target outline --output story_outline.json

# Transform with quality assessment
uv run python batch_transform_cli.py single draft.json --target manuscript --quality --verbose
```

### Advanced Options

```bash
# Create a rollback snapshot before transformation
uv run python batch_transform_cli.py single important.json --target synopsis --snapshot

# Use different transformation approach and parameter
uv run python batch_transform_cli.py single content.json --target outline --approach gardening --parameter restructure
```

### Single Command Options

- `--target, -t` (required): Target content type
- `--output, -o`: Output file path (default: `input_transformed.json`)
- `--approach`: Transformation approach (`planning` or `gardening`)
- `--parameter`: Transformation parameter (`expand`, `condense`, `restructure`, `enhance`)
- `--quality`: Enable quality assessment
- `--snapshot`: Create rollback snapshot before transformation
- `--verbose, -v`: Verbose output with detailed information

## Batch Transformation

### Basic Usage

```bash
# Transform all JSON files in a directory
uv run python batch_transform_cli.py batch data/ --target synopsis

# Transform files matching a pattern
uv run python batch_transform_cli.py batch "stories/*.json" --target outline

# Batch transform with custom output directory
uv run python batch_transform_cli.py batch input/ --target manuscript --output-dir results/
```

### Advanced Batch Processing

```bash
# Parallel processing with quality assessment
uv run python batch_transform_cli.py batch "*.json" --target synopsis --parallel --quality

# Create snapshot before batch transformation
uv run python batch_transform_cli.py batch data/ --target outline --snapshot --verbose

# Custom transformation parameters for batch
uv run python batch_transform_cli.py batch stories/ --target treatment --approach gardening --parameter enhance
```

### Batch Command Options

- `input_pattern` (required): Directory path or glob pattern for input files
- `--target, -t` (required): Target content type for all files
- `--output-dir, -o`: Output directory (default: `batch_output`)
- `--approach`: Transformation approach for all files
- `--parameter`: Transformation parameter for all files
- `--quality`: Enable quality assessment for all transformations
- `--parallel`: Use parallel processing (faster for large batches)
- `--snapshot`: Create rollback snapshot before batch processing
- `--verbose, -v`: Verbose output with progress details

## History Management

### View History

```bash
# List recent transformations
uv run python batch_transform_cli.py history --list

# Export complete history to file
uv run python batch_transform_cli.py history --export transformation_history_backup.json
```

### History Information

The history command shows:
- **Single transformations**: File paths, content types, quality scores
- **Batch transformations**: Number of files, success rates, average quality
- **Timestamps**: When each transformation was performed
- **Parameters**: Approaches and parameters used

## Rollback & Snapshots

### Snapshot Management

```bash
# List all available snapshots
uv run python batch_transform_cli.py rollback --list-snapshots

# Restore objects from a specific snapshot
uv run python batch_transform_cli.py rollback --snapshot snapshot_20250822_143015_a1b2c3d4

# Restore to custom directory
uv run python batch_transform_cli.py rollback --snapshot snapshot_id --output-dir restored_content/
```

### Snapshot Features

- **Automatic Creation**: Snapshots created before batch operations (when `--snapshot` flag used)
- **Complete State**: Full object data including content, metadata, and relationships
- **Easy Restoration**: One-command restoration of any snapshot
- **Organized Storage**: Snapshots stored in `transformation_snapshots/` directory

## Content Types

Available content types for transformation:

- `idea` - Brief concepts or premises
- `logline` - One-sentence story summaries  
- `summary` - Brief story overviews
- `synopsis` - Detailed story summaries
- `treatment` - Narrative treatments
- `outline` - Structured story breakdowns
- `detailed_outline` - Comprehensive outlines
- `draft` - Partial manuscript text
- `manuscript` - Complete story text
- `series` - Series-level content

## Transformation Parameters

### Approaches

- **`planning`** (default) - Top-down structured approach
- **`gardening`** - Bottom-up organic approach

### Parameters

- **`expand`** (default) - Add detail and depth to content
- **`condense`** - Summarize and focus content
- **`restructure`** - Change format or structure
- **`enhance`** - Improve existing content quality

## Quality Assessment

When `--quality` flag is used, the CLI provides:

- **Overall Quality Score**: Percentage score (0-100%)
- **Length Appropriateness**: How well the length fits the content type
- **Content Preservation**: How much original content is retained
- **Type Appropriateness**: How well content fits the target type

### Quality Metrics Example

```
📊 Quality Score: 85.2%
📈 Quality Details:
  • Length Score: 0.90
  • Content Preservation: 0.83
  • Type Appropriateness: 0.85
```

## File Formats

### Input File Format

CodexObjects should be saved as JSON files:

```json
{
  "uuid": "unique-identifier",
  "title": "Story Title",
  "content": "The actual story content...",
  "object_type": "idea",
  "word_count": 150,
  "genre": "Fantasy",
  "target_audience": "Young Adult",
  "created_timestamp": "2025-01-15T10:30:00",
  "modified_timestamp": "2025-01-15T10:30:00"
}
```

### Output Files

Transformed objects maintain the same JSON structure with updated:
- `object_type` - Changed to target type
- `modified_timestamp` - Updated to transformation time
- `content` - Potentially modified content (depending on transformation engine)

## Examples & Workflows

### Workflow 1: Single File Development

```bash
# Start with an idea
uv run python batch_transform_cli.py single idea.json --target logline --quality --snapshot

# Develop to synopsis
uv run python batch_transform_cli.py single idea_transformed.json --target synopsis --quality

# Create detailed outline
uv run python batch_transform_cli.py single idea_transformed.json --target outline --approach planning --parameter expand
```

### Workflow 2: Batch Processing Pipeline

```bash
# Create snapshot of all source files
uv run python batch_transform_cli.py batch raw_ideas/ --target synopsis --snapshot --quality --parallel

# Review results and transform best ones to outlines
uv run python batch_transform_cli.py batch batch_output/ --target outline --quality --verbose

# Check history to see progress
uv run python batch_transform_cli.py history --list
```

### Workflow 3: Experimental Transformations

```bash
# Create snapshot before experimenting
uv run python batch_transform_cli.py batch experimental/ --target treatment --snapshot --approach gardening

# If results aren't good, rollback
uv run python batch_transform_cli.py rollback --list-snapshots
uv run python batch_transform_cli.py rollback --snapshot snapshot_id --output-dir original_restored/
```

## Performance Considerations

### Parallel Processing

- **When to Use**: Batches of 3+ files benefit from `--parallel`
- **Worker Threads**: Automatically limited to 4 concurrent workers
- **Memory Usage**: Each worker processes one file at a time
- **Progress Tracking**: Real-time updates show completion status

### Large Batches

For processing 50+ files:

```bash
# Use parallel processing with quality assessment
uv run python batch_transform_cli.py batch large_dataset/ --target synopsis --parallel --quality --verbose

# Monitor progress and create snapshots for safety
uv run python batch_transform_cli.py batch large_dataset/ --target outline --parallel --snapshot
```

## Error Handling

The CLI provides comprehensive error handling:

- **File Errors**: Clear messages for missing or corrupted files
- **Transformation Errors**: Graceful handling of failed transformations
- **Batch Resilience**: Failed files don't stop batch processing
- **Recovery Options**: Snapshots allow recovery from any issues

### Common Error Scenarios

```bash
# File not found
❌ Error loading input.json: [Errno 2] No such file or directory

# Invalid JSON format
❌ Error loading data.json: Expecting ',' delimiter: line 5 column 10

# Transformation failure
⚠️ Advanced transformation failed: Content too short for target type
🔄 Falling back to basic transformation...
```

## Integration with Streamlit UI

The CLI tool complements the Streamlit UI:

- **Same Transformation Engine**: Uses identical transformation logic
- **Compatible Formats**: Files work seamlessly between CLI and UI
- **History Sharing**: Transformation history accessible from both interfaces
- **Snapshot Compatibility**: Snapshots created in CLI can be viewed in UI

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from project root with `uv run`
2. **File Permissions**: Check read/write permissions for input/output directories
3. **Memory Issues**: Use smaller batches or disable parallel processing
4. **Quality Assessment Slow**: Disable `--quality` for faster processing

### Debug Mode

```bash
# Enable verbose output for debugging
uv run python batch_transform_cli.py single input.json --target synopsis --verbose

# Check transformation history for patterns
uv run python batch_transform_cli.py history --list
```

## Advanced Usage

### Scripting and Automation

The CLI is designed for scripting:

```bash
#!/bin/bash
# Automated content development pipeline

# Stage 1: Ideas to loglines
uv run python batch_transform_cli.py batch ideas/ --target logline --snapshot --quality

# Stage 2: Best loglines to synopses (quality > 80%)
# (Custom script to filter by quality scores)

# Stage 3: Synopses to outlines
uv run python batch_transform_cli.py batch high_quality_synopses/ --target outline --parallel
```

### Custom Output Processing

```bash
# Export history for analysis
uv run python batch_transform_cli.py history --export analysis_data.json

# Process with external tools
python analyze_transformation_patterns.py analysis_data.json
```

## Conclusion

The Batch Transformation CLI provides a powerful, flexible interface for content transformation with enterprise-grade features like quality assessment, history tracking, and rollback capabilities. It's designed to handle everything from single-file transformations to large-scale batch processing with robust error handling and performance optimization.