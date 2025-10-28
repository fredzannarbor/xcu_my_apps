# Nimble Ultra Pipeline Flow Documentation

## Overview
This document provides a detailed flow of content through the Nimble Ultra publishing pipeline, from initial configuration to final PDF generation.

---

## 1. Pipeline Entry Point: Book Schedule

**File Location:**
```
imprints/nimble_ultra/schedule.csv
```

**Key Fields:**
- `book_id`: Unique identifier (e.g., "BK001")
- `title`: Book title
- `author`: Author name
- `imprint`: "Nimble Ultra Global"
- `body_source`: Path to source PDF (e.g., "~/Downloads/DOC_0000258365.pdf")

**Command to Run:**
```bash
PYTHONPATH="$PWD/src:$PYTHONPATH" uv run python run_book_pipeline.py \
  --schedule-file imprints/nimble_ultra/schedule.csv \
  --imprint nimble_ultra \
  --model "gemini/gemini-2.5-pro" \
  --begin-with-book 1 \
  --end-with-book 1 \
  --overwrite
```

---

## 2. Imprint Configuration

### A. Content Pipeline Definition
**File Location:**
```
imprints/nimble_ultra/content_pipeline.json
```

**Structure:**
```json
{
  "imprint_name": "nimble_ultra",
  "codex_types": {
    "declassified_intelligence_report": {
      "front_matter": { "sections": [...] },
      "body": { "sections": [...] },
      "back_matter": { "sections": [...] }
    }
  },
  "default_codex_type": "declassified_intelligence_report",
  "prompt_defaults": {
    "model": "gemini/gemini-2.5-pro",
    "temperature": 0.7,
    "max_tokens": 65536
  }
}
```

**Defines:**
- Which codex type to use (declassified_intelligence_report)
- Which prompts to run for front matter
- Which prompts to run for back matter
- Body source handling (static PDF insertion)

### B. Persona Configuration
**File Location:**
```
configs/imprints/nimble_ultra.json
```

**Contains:**
- Publisher persona (Zero - "The Silence")
- Imprint metadata
- Branding information

---

## 3. Prompt System

### A. Prompt Definition File
**File Location:**
```
imprints/nimble_ultra/prompts.json
```

**View prompts:**
```bash
cat imprints/nimble_ultra/prompts.json | jq '.prompts | keys'
```

**Example prompt structure:**
```json
{
  "prompts": {
    "bibliographic_key_phrases": {
      "name": "bibliographic_key_phrases",
      "description": "Generate bibliographic keywords and subject headings",
      "prompt": "Based on the following document, generate comprehensive bibliographic keywords...",
      "model": "gemini/gemini-2.0-flash-exp",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    }
  }
}
```

### B. Front Matter Prompts (in execution order)
1. **bibliographic_key_phrases** - Keywords and subject headings
2. **gemini_get_basic_info_from_public_domain** - Extract metadata (title, author, date)
3. **motivation** - Publisher's Note explaining why this document matters
4. **place_in_historical_context** - Historical context and significance
5. **abstracts_x4** - Four different abstracts at varying lengths
6. **most_important_passages_with_reasoning** - Key passages with analysis

### C. Back Matter Prompts
1. **index_of_persons** - Index of people mentioned
2. **index_of_places** - Index of locations mentioned
3. **mnemonics_prompt** - Memory aids for key concepts

**View specific prompt:**
```bash
cat imprints/nimble_ultra/prompts.json | jq '.prompts.motivation'
```

---

## 4. LLM Response Generation & Storage

### A. Raw Response Storage
**Directory:**
```
output/nimble_ultra_build/raw_json_responses/
```

**File naming:**
```
{prompt_key}_{model_name}_{timestamp}.json
```

**Example:**
```
motivation_gemini-2.5-pro_20251024_004027.json
```

**Structure:**
```json
{
  "prompt_key": "motivation",
  "model": "gemini/gemini-2.5-pro",
  "timestamp": "2025-10-24T00:40:27",
  "raw_response": "...",
  "parsed_content": {
    "publishers_note": "This declassified document...",
    "motivation_analysis": "..."
  }
}
```

### B. Response Processing
**Code Location:**
```
run_book_pipeline.py:307-420 (process_single_book function)
src/codexes/modules/builders/llm_get_book_data.py
```

**Process Flow:**
1. Load prompts from `prompts.json`
2. Substitute variables (book_content, title, etc.)
3. Call LLM via `nimble-llm-caller` wrapper
4. Parse response (extract structured data)
5. Save raw response to `raw_json_responses/`
6. Add to `responses` array in metadata

---

## 5. Processed Metadata JSON

### A. File Location
**Directory:**
```
output/nimble_ultra_build/processed_json/
```

**Filename:**
```
{safe_title}.json
```

**Example:**
```
The_Strategic_Value_to_the_USSR_of_the_Conquest_of_Western_Europe.json
```

### B. Structure
```json
{
  "title": "The Strategic Value to the USSR...",
  "author": "CIA",
  "isbn13": "9781234567890",
  "body_source": "raw_json_responses/ocr_cache/DOC_0000258365_ocr.pdf",

  "responses": [
    {
      "prompt_key": "motivation",
      "model": "gemini/gemini-2.5-pro",
      "parsed_content": {...}
    }
  ],

  "_pipeline_content": {
    "front_matter": {
      "bibliographic_key_phrases": {...},
      "motivation": {...},
      "historical_context": {...},
      "abstracts_x4": {...},
      "important_passages": {...}
    },
    "back_matter": {
      "index_persons": {...},
      "index_places": {...},
      "mnemonics": {...}
    }
  }
}
```

**View processed JSON:**
```bash
cat output/nimble_ultra_build/processed_json/The_Strategic_Value_to_the_USSR_of_the_Conquest_of_Western_Europe.json | jq '._pipeline_content | keys'
```

---

## 6. LaTeX Template System

### A. Main Template
**File Location:**
```
imprints/nimble_ultra/template.tex
```

**View template:**
```bash
cat imprints/nimble_ultra/template.tex
```

### B. Section Templates (Jinja2)
**Directory:**
```
imprints/nimble_ultra/templates/
```

**Files:**
- `front_matter_section.tex.j2` - Front matter sections
- `section_markdown.tex.j2` - Markdown content sections
- `back_matter_section.tex.j2` - Back matter sections

**Example section template:**
```jinja2
\cleardoublepage
\chapter*{ {{ title }} }
\addcontentsline{toc}{chapter}{ {{ title }} }

{{ content }}
```

### C. Template Input Requirements

**Prepress script location:**
```
imprints/nimble_ultra/prepress.py
```

**Key function: `process_manuscript()`** (lines 102-145)

**Required Inputs:**
1. **Metadata JSON** - Complete book metadata with `_pipeline_content`
2. **Body PDF** - Source document (from `metadata['body_source']`)
3. **Template variables:**
   - `title` - Book title
   - `author` - Author name
   - `publisher` - Publisher name
   - `imprint` - Imprint name
   - `isbn13` - ISBN
   - `front_matter_sections` - List of front matter sections to render
   - `back_matter_sections` - List of back matter sections to render

**Template rendering code (lines 430-520):**
```python
# Load Jinja2 environment
template_env = Environment(loader=FileSystemLoader(template_dir))

# Prepare template variables
template_vars = {
    'title': metadata.get('title', 'Untitled'),
    'author': metadata.get('author', 'Unknown Author'),
    'isbn13': metadata.get('isbn13', '0000000000000'),
    'publisher': metadata.get('publisher', 'Nimble Books LLC'),
    'imprint': metadata.get('imprint', 'Nimble Ultra'),
    'front_matter_sections': front_matter_sections,
    'back_matter_sections': back_matter_sections,
    'body_pdf_path': 'pdf_body_source.pdf'
}

# Render main template
main_template = template_env.get_template('template.tex')
latex_content = main_template.render(**template_vars)
```

---

## 7. LaTeX to PDF Compilation

### A. Compilation Function
**File Location:**
```
src/codexes/modules/prepress/tex_utils.py
```

**Function signature:**
```python
def compile_tex_to_pdf(
    tex_file_path: Path,
    output_dir: Path,
    engine: str = "lualatex",
    passes: int = 2
) -> Optional[str]:
    """
    Compile LaTeX to PDF using specified engine.

    Args:
        tex_file_path: Path to .tex file
        output_dir: Directory for output files
        engine: LaTeX engine to use (default: lualatex)
        passes: Number of compilation passes (default: 2)

    Returns:
        Path to generated PDF or None if failed
    """
```

### B. Compilation Command
**Actual command executed:**
```bash
lualatex \
  -interaction=nonstopmode \
  -output-directory={output_dir} \
  -shell-escape \
  {tex_file_path}
```

**Two-pass compilation:**
1. **Pass 1** - Generate TOC and references
2. **Pass 2** - Resolve TOC page numbers

### C. Output Files
**LaTeX artifacts in output directory:**
- `{safe_title}.tex` - LaTeX source
- `{safe_title}.aux` - Auxiliary file
- `{safe_title}.log` - Compilation log
- `{safe_title}.toc` - Table of contents
- `{safe_title}.pdf` - **Final PDF output**

**Final output location:**
```
output/nimble_ultra_build/{safe_title}.pdf
```

---

## 8. Complete Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SCHEDULE FILE (schedule.csv)                            │
│    - book_id, title, author, body_source                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. IMPRINT CONFIGURATION                                    │
│    ┌────────────────────────────────────────────────────┐   │
│    │ content_pipeline.json                              │   │
│    │  → Defines codex_type: declassified_intel_report   │   │
│    │  → Lists front_matter prompts                      │   │
│    │  → Lists back_matter prompts                       │   │
│    └────────────────────────────────────────────────────┘   │
│    ┌────────────────────────────────────────────────────┐   │
│    │ configs/imprints/nimble_ultra.json                 │   │
│    │  → Persona: Zero ("The Silence")                   │   │
│    └────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PROMPT LOADING (prompts.json)                            │
│    ┌────────────────────────────────────────────────────┐   │
│    │ Front Matter Prompts:                              │   │
│    │  1. bibliographic_key_phrases                      │   │
│    │  2. gemini_get_basic_info_from_public_domain       │   │
│    │  3. motivation (Publisher's Note)                  │   │
│    │  4. place_in_historical_context                    │   │
│    │  5. abstracts_x4                                   │   │
│    │  6. most_important_passages_with_reasoning         │   │
│    │                                                     │   │
│    │ Back Matter Prompts:                               │   │
│    │  1. index_of_persons                               │   │
│    │  2. index_of_places                                │   │
│    │  3. mnemonics_prompt                               │   │
│    └────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM CONTENT GENERATION                                   │
│    For each prompt:                                         │
│    ┌────────────────────────────────────────────────────┐   │
│    │ a) Load prompt text                                │   │
│    │ b) Substitute variables (book_content, title, etc) │   │
│    │ c) Call LLM (gemini/gemini-2.5-pro)               │   │
│    │ d) Parse response → extract structured data        │   │
│    │ e) Save to raw_json_responses/{prompt_key}.json    │   │
│    │ f) Add to responses[] array                        │   │
│    └────────────────────────────────────────────────────┘   │
│                                                             │
│    Output: raw_json_responses/                              │
│    ├── motivation_gemini-2.5-pro_timestamp.json             │
│    ├── historical_context_gemini-2.5-pro_timestamp.json     │
│    └── ... (one file per prompt)                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. RESPONSE PROCESSING & JSON BUILDING                      │
│    ┌────────────────────────────────────────────────────┐   │
│    │ Transform responses → _pipeline_content            │   │
│    │                                                     │   │
│    │ _pipeline_content: {                               │   │
│    │   front_matter: {                                  │   │
│    │     bibliographic_key_phrases: {...},              │   │
│    │     motivation: {...},                             │   │
│    │     historical_context: {...},                     │   │
│    │     abstracts_x4: {...},                           │   │
│    │     important_passages: {...}                      │   │
│    │   },                                               │   │
│    │   back_matter: {                                   │   │
│    │     index_persons: {...},                          │   │
│    │     index_places: {...},                           │   │
│    │     mnemonics: {...}                               │   │
│    │   }                                                │   │
│    │ }                                                  │   │
│    └────────────────────────────────────────────────────┘   │
│                                                             │
│    Output: processed_json/{safe_title}.json                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. PREPRESS: LaTeX GENERATION                               │
│    File: imprints/nimble_ultra/prepress.py                  │
│    ┌────────────────────────────────────────────────────┐   │
│    │ process_manuscript() function:                     │   │
│    │                                                     │   │
│    │ Inputs:                                            │   │
│    │  - metadata JSON (with _pipeline_content)          │   │
│    │  - body_source PDF                                 │   │
│    │                                                     │   │
│    │ Process:                                           │   │
│    │  1. Load Jinja2 templates from templates/          │   │
│    │  2. Prepare template variables                     │   │
│    │  3. Render front matter sections                   │   │
│    │  4. Copy body PDF to output directory              │   │
│    │  5. Render back matter sections                    │   │
│    │  6. Generate complete .tex file                    │   │
│    │                                                     │   │
│    │ Template files:                                    │   │
│    │  - template.tex (main document structure)          │   │
│    │  - templates/front_matter_section.tex.j2           │   │
│    │  - templates/section_markdown.tex.j2               │   │
│    │  - templates/back_matter_section.tex.j2            │   │
│    └────────────────────────────────────────────────────┘   │
│                                                             │
│    Output: {safe_title}.tex                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. PDF COMPILATION                                          │
│    File: src/codexes/modules/prepress/tex_utils.py          │
│    ┌────────────────────────────────────────────────────┐   │
│    │ compile_tex_to_pdf(tex_file, output_dir)           │   │
│    │                                                     │   │
│    │ Command (Pass 1):                                  │   │
│    │   lualatex -interaction=nonstopmode \              │   │
│    │            -output-directory={output_dir} \         │   │
│    │            -shell-escape \                         │   │
│    │            {tex_file}                              │   │
│    │                                                     │   │
│    │ Command (Pass 2):                                  │   │
│    │   (same - to resolve TOC page numbers)             │   │
│    └────────────────────────────────────────────────────┘   │
│                                                             │
│    Output: {safe_title}.pdf                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. FINAL OUTPUT                                             │
│    ┌────────────────────────────────────────────────────┐   │
│    │ output/nimble_ultra_build/                         │   │
│    │ ├── {safe_title}.json (411 KB metadata)            │   │
│    │ ├── {safe_title}.pdf (2.7 MB final book)           │   │
│    │ ├── {safe_title}.tex (LaTeX source)                │   │
│    │ ├── pdf_body_source.pdf (original document)        │   │
│    │ ├── processed_json/                                │   │
│    │ │   └── {safe_title}.json (processed metadata)     │   │
│    │ └── raw_json_responses/                            │   │
│    │     ├── motivation_*.json                          │   │
│    │     ├── historical_context_*.json                  │   │
│    │     └── ... (all LLM responses)                    │   │
│    └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Key File Paths Reference

### Configuration Files
- Schedule: `imprints/nimble_ultra/schedule.csv`
- Content pipeline: `imprints/nimble_ultra/content_pipeline.json`
- Persona config: `configs/imprints/nimble_ultra.json`
- Prompts: `imprints/nimble_ultra/prompts.json`

### Templates
- Main template: `imprints/nimble_ultra/template.tex`
- Cover template: `imprints/nimble_ultra/cover_template.tex`
- Jinja2 templates: `imprints/nimble_ultra/templates/*.tex.j2`

### Code Files
- Pipeline orchestrator: `run_book_pipeline.py`
- LLM content generation: `src/codexes/modules/builders/llm_get_book_data.py`
- Prepress processing: `imprints/nimble_ultra/prepress.py`
- LaTeX compilation: `src/codexes/modules/prepress/tex_utils.py`

### Output Directories
- Main output: `output/nimble_ultra_build/`
- Processed JSON: `output/nimble_ultra_build/processed_json/`
- Raw responses: `output/nimble_ultra_build/raw_json_responses/`
- LSI CSV: `output/nimble_ultra_build/lsi_csv/`

---

## 10. Useful Commands

### View all prompts
```bash
cat imprints/nimble_ultra/prompts.json | jq '.prompts | keys'
```

### View specific prompt
```bash
cat imprints/nimble_ultra/prompts.json | jq '.prompts.motivation'
```

### View pipeline content structure
```bash
cat output/nimble_ultra_build/processed_json/{title}.json | jq '._pipeline_content'
```

### View raw LLM response
```bash
cat output/nimble_ultra_build/raw_json_responses/motivation_*.json | jq .
```

### Check PDF page count
```bash
PYTHONPATH="$PWD/src:$PYTHONPATH" uv run python -c "
import fitz
pdf = fitz.open('output/nimble_ultra_build/{title}.pdf')
print(f'Pages: {len(pdf)}')
"
```

### Rebuild book
```bash
PYTHONPATH="$PWD/src:$PYTHONPATH" uv run python run_book_pipeline.py \
  --schedule-file imprints/nimble_ultra/schedule.csv \
  --imprint nimble_ultra \
  --model "gemini/gemini-2.5-pro" \
  --begin-with-book 1 \
  --end-with-book 1 \
  --overwrite
```

---

## 11. Data Flow Summary

1. **Input** → Schedule CSV defines book + body source
2. **Config** → content_pipeline.json defines which prompts to run
3. **Prompts** → prompts.json contains LLM prompt text
4. **Generation** → LLM generates content for each prompt
5. **Storage** → Responses saved to raw_json_responses/
6. **Processing** → Responses transformed into _pipeline_content structure
7. **Metadata** → Complete JSON saved to processed_json/
8. **Templating** → Jinja2 templates render LaTeX sections
9. **Compilation** → LuaLaTeX compiles .tex → .pdf
10. **Output** → Final PDF + metadata JSON + LaTeX source
