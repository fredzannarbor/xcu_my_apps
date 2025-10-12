# Supplementary Materials Module

This module provides support for loading and processing supplementary materials (documents, PDFs, etc.) to enhance LLM-based operations on imprint configurations.

## Overview

Supplementary materials allow you to provide additional context to LLM models when generating content for imprints. This could include:

- Reference documents about the imprint's domain
- Market research reports
- Editorial guidelines
- Sample content or style guides
- Domain-specific knowledge bases

## Configuration

### Imprint Config Structure

Add a `supplementary_materials` section to your imprint JSON configuration:

```json
{
  "imprint": "Your Imprint Name",
  "supplementary_materials": {
    "enabled": true,
    "description": "Optional description of what these materials provide",
    "materials": {
      "Title of Document 1": "path/to/document.txt",
      "Title of Document 2": "path/to/report.pdf",
      "Title of Document 3": "path/to/guide.md"
    },
    "usage_notes": "Optional notes about usage"
  }
}
```

### Supported File Formats

- `.txt` - Plain text files
- `.md`, `.markdown` - Markdown files
- `.docx` - Microsoft Word documents (requires python-docx)
- `.pdf` - PDF files (requires PyMuPDF/fitz)

### File Paths

Paths can be:
- **Absolute paths**: `/Users/fred/documents/guide.pdf`
- **Relative paths**: `resources/domain_info.txt` (relative to imprint config directory)

## Usage

### In Batch Operations

When creating ideation tournaments or performing batch operations, enable supplementary materials:

```python
from codexes.modules.batch_operations import create_ideation_tournaments

result = create_ideation_tournaments(
    source_paths=[Path("configs/imprints")],
    tournament_config=config,
    use_supplementary=True  # Enable supplementary materials
)
```

### In Command-Line Scripts

```python
from codexes.modules.supplementary import load_imprint_supplementary_materials

# Load materials from config
supplementary_content = load_imprint_supplementary_materials(
    config=imprint_config,
    use_supplementary=True,
    max_tokens=50000  # Optional: limit token count
)

# Use in your prompt
prompt = f"{supplementary_content}\n\nYour main prompt here..."
```

### In Streamlit UI

The Enhanced Imprint Creator page includes a checkbox for "Include supplementary materials" in the batch operations section.

## How It Works

### 1. Loading

The `SupplementaryMaterialsLoader` class:
- Reads files from configured paths
- Extracts text content based on file type
- Handles errors gracefully (logs warnings for missing/unreadable files)

### 2. Compacting

Content is intelligently compacted to fit within token limits:

- **Smart compression**: Allocates space proportionally to each document
- **Truncation**: Removes excess content with clear markers
- **Token estimation**: Uses ~4 chars per token heuristic

### 3. Context Window Selection

When `use_supplementary=True`:
- Automatically selects the **largest available context window** for the chosen model
- Allocates ~30% of context to supplementary materials
- Reserves remaining space for prompt and response

### Supported Models and Context Sizes

| Model | Context Window |
|-------|----------------|
| `gemini/gemini-2.5-pro` | 2,000,000 tokens |
| `gemini/gemini-2.5-flash` | 1,000,000 tokens |
| `anthropic/claude-sonnet-4-5-20250929` | 200,000 tokens |
| `anthropic/claude-opus-4` | 200,000 tokens |
| `openai/gpt-4-turbo` | 128,000 tokens |
| `xai/grok-3-latest` | 131,072 tokens |

## API Reference

### `load_imprint_supplementary_materials(config, use_supplementary, max_tokens)`

Load supplementary materials from an imprint configuration.

**Parameters:**
- `config` (dict): Imprint configuration dictionary
- `use_supplementary` (bool): Whether to load materials
- `max_tokens` (int, optional): Maximum tokens for content

**Returns:**
- `str | None`: Formatted supplementary content or None

### `get_largest_context_model(model_name)`

Get the maximum context window size for a model.

**Parameters:**
- `model_name` (str): Model identifier (e.g., "gemini/gemini-2.5-flash")

**Returns:**
- `int`: Maximum context window in tokens

### `SupplementaryMaterialsLoader`

Main class for loading and processing materials.

**Methods:**
- `load_materials(materials_dict)`: Load all materials from dict of title -> path
- `compact_materials(materials, max_chars, strategy)`: Compact content to fit limits
- `format_for_model_context(materials, target_tokens)`: Format for LLM inclusion

## Examples

### Example 1: Children's Book Imprint

For Mississippi Miracle Books (children's picture books):

```json
{
  "imprint": "Mississippi Miracle Books",
  "supplementary_materials": {
    "enabled": true,
    "materials": {
      "K-4 Literacy Standards": "resources/k4_literacy_standards.pdf",
      "Inclusive Children's Literature Guide": "resources/inclusive_childrens_lit.md",
      "Southern Cultural Context": "resources/southern_culture_notes.txt"
    }
  }
}
```

### Example 2: Technical Publishing Imprint

For a technical/programming imprint:

```json
{
  "imprint": "TechPress",
  "supplementary_materials": {
    "enabled": true,
    "materials": {
      "Current Tech Trends Report": "market_research/tech_trends_2025.pdf",
      "Target Audience Analysis": "market_research/developer_survey.docx",
      "Competitive Analysis": "analysis/competitor_titles.md"
    }
  }
}
```

## Best Practices

1. **Keep materials focused**: Include only documents directly relevant to the imprint's domain
2. **Update regularly**: Ensure supplementary materials reflect current information
3. **Use descriptive titles**: Make it clear what each document provides
4. **Monitor token usage**: Large documents may be truncated; consider summarizing first
5. **Test with and without**: Compare idea generation with/without supplementary materials

## Troubleshooting

### Materials not loading

- Check file paths are correct (absolute or relative to config directory)
- Verify file formats are supported (.txt, .md, .docx, .pdf)
- Check logs for specific error messages

### Content truncated

- Increase `max_tokens` parameter if possible
- Use models with larger context windows (Gemini 2.5 Pro has 2M tokens)
- Pre-summarize long documents before including

### Dependencies missing

If you see import errors:

```bash
# For DOCX support
uv add python-docx

# For PDF support (usually already installed)
uv add pymupdf
```

## Implementation Details

### File Loading Pipeline

1. **Path resolution**: Resolve relative paths against config directory
2. **Format detection**: Determine file type from extension
3. **Content extraction**:
   - Text/Markdown: Direct read with UTF-8 encoding
   - DOCX: Extract paragraphs and tables using python-docx
   - PDF: Extract text from all pages using PyMuPDF
4. **Error handling**: Log warnings for failures, continue with other files

### Prompt Integration

Supplementary content is prepended to the main prompt:

```
SUPPLEMENTARY MATERIALS
================================================================================

## Document Title 1
--------------------------------------------------------------------------------
[Document content...]

## Document Title 2
--------------------------------------------------------------------------------
[Document content...]

================================================================================
The above materials provide context about the domain and mission of this imprint.
Use these materials to inform your book concept generation, ensuring ideas align
with the themes, values, and focus areas described.

[Main prompt continues...]
```

## Future Enhancements

Potential improvements:

- [ ] Automatic summarization of large documents
- [ ] Semantic chunking for better context utilization
- [ ] Support for additional formats (HTML, EPUB, etc.)
- [ ] Material version tracking and change detection
- [ ] Per-material token allocation control
- [ ] Material relevance scoring and selective inclusion
