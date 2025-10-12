# Content Transformation CLI Tool

A command-line tool for transforming CodexObject files from one content type to another.

## Quick Start

```bash
# Transform an idea to a synopsis
uv run python transform_content.py example_idea.json --target synopsis

# Transform with verbose output
uv run python transform_content.py example_idea.json --target synopsis --verbose

# Transform with custom output file
uv run python transform_content.py idea.json --target outline --output my_outline.json
```

## Usage

```
python transform_content.py INPUT_FILE --target TARGET_TYPE [OPTIONS]
```

### Required Arguments

- `INPUT_FILE`: Path to JSON file containing a CodexObject
- `--target` / `-t`: Target content type to transform to

### Optional Arguments

- `--output` / `-o`: Output JSON file (default: `input_transformed.json`)
- `--approach`: Transformation approach (`planning` or `gardening`, default: `planning`)
- `--parameter`: Transformation parameter (`expand`, `condense`, `restructure`, `enhance`, default: `expand`)
- `--verbose` / `-v`: Show detailed output
- `--help` / `-h`: Show help message

## Content Types

Available content types for transformation:

- `idea` - Brief concepts or premises
- `logline` - One-sentence story summaries  
- `summary` - Brief story overviews
- `synopsis` - Detailed story summaries
- `treatment` - Narrative treatments
- `outline` - Structured story breakdowns
- `draft` - Partial manuscript text
- `manuscript` - Complete story text
- `book_idea` - Book-specific ideas
- `idea_with_fields` - Ideas with additional metadata

## Transformation Options

### Approaches
- `planning` - Top-down structured approach (default)
- `gardening` - Bottom-up organic approach

### Parameters
- `expand` - Add detail and depth (default)
- `condense` - Summarize and focus
- `restructure` - Change format/structure
- `enhance` - Improve existing content

## Input File Format

The input JSON file should contain a CodexObject with the following structure:

```json
{
  "uuid": "unique-id",
  "title": "Your Content Title",
  "content": "The actual content text...",
  "object_type": "idea",
  "word_count": 25,
  "genre": "Science Fiction",
  "target_audience": "Adult",
  "created_timestamp": "2025-08-21T18:00:00Z"
}
```

### Required Fields
- `title` - Title of the content
- `content` - The actual text content
- `object_type` - Current content type

### Optional Fields
- `uuid` - Unique identifier (generated if missing)
- `word_count` - Number of words (calculated if missing)
- `genre` - Content genre
- `target_audience` - Intended audience
- `created_timestamp` - Creation timestamp (generated if missing)

## Examples

### Basic Transformation

```bash
# Transform idea to synopsis
uv run python transform_content.py my_idea.json --target synopsis
```

### Advanced Transformation

```bash
# Transform synopsis to outline with planning approach and expand parameter
uv run python transform_content.py synopsis.json \
  --target outline \
  --approach planning \
  --parameter expand \
  --output detailed_outline.json \
  --verbose
```

### Batch Processing

```bash
# Transform multiple files (using shell loop)
for file in ideas/*.json; do
  uv run python transform_content.py "$file" --target synopsis --output "synopses/$(basename "$file")"
done
```

## Output

The tool creates a new JSON file with the transformed CodexObject:

```json
{
  "uuid": "new-unique-id",
  "title": "Your Content Title",
  "content": "Transformed content...",
  "object_type": "synopsis",
  "word_count": 150,
  "genre": "Science Fiction",
  "target_audience": "Adult",
  "created_timestamp": "2025-08-21T18:00:00Z",
  "modified_timestamp": "2025-08-21T19:30:00Z"
}
```

## Transformation Engine

The tool uses two transformation methods:

1. **Advanced Engine** (when available): Uses the full ideation transformation engine with AI-powered content generation
2. **Basic Transformation** (fallback): Simple type conversion that preserves content but changes the object type

The tool automatically falls back to basic transformation if the advanced engine encounters issues.

## Error Handling

The tool provides clear error messages for common issues:

- File not found
- Invalid JSON format
- Unsupported content types
- Transformation failures

Use `--verbose` flag for detailed error information and troubleshooting.

## Integration

This CLI tool can be integrated into:

- Build scripts and automation workflows
- Content management pipelines
- Batch processing systems
- CI/CD processes for content validation

## Example Workflow

1. **Create initial idea**:
   ```json
   {
     "title": "Space Colony Story",
     "content": "Humans establish the first permanent colony on Mars but discover they're not alone.",
     "object_type": "idea",
     "genre": "Science Fiction"
   }
   ```

2. **Transform to synopsis**:
   ```bash
   uv run python transform_content.py idea.json --target synopsis --verbose
   ```

3. **Transform to outline**:
   ```bash
   uv run python transform_content.py idea_transformed.json --target outline
   ```

4. **Transform to draft**:
   ```bash
   uv run python transform_content.py idea_transformed_transformed.json --target draft
   ```

This provides a complete command-line workflow for content transformation that bypasses the UI issues and gives you direct access to the transformation functionality.