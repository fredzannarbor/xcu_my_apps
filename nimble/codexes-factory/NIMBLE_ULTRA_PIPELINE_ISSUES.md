# Nimble Ultra Pipeline Issues - Resume Point

**Date:** 2025-10-29 23:40
**Branch:** feature/nimble-ultra-prod-test

## What Works

✅ **OCR Detection & Processing**
- Detects PDFs with no embedded text
- Uses gemini-2.5-pro vision for OCR
- Saves OCR text to `output/nimble_ultra_ocr/`

✅ **Text Extraction**
- Correctly reads OCR or embedded PDF text
- Passes to LLM prompts via `{book_content}` placeholder

✅ **LLM Content Generation**
- 12 LLM calls per document with gemini-2.5-pro
- Generates bibliographic keywords, metadata, publisher note, historical context, abstracts, passages, mnemonics
- Content saved to JSON in `_pipeline_content`

✅ **Data Structure**
- Properly organized as `{"front_matter": {...}, "back_matter": {...}}`
- Prepress recognizes and attempts to render sections

## The Problem

❌ **Inconsistent Response Formats** causing garbled LaTeX rendering:

**Prompt requests:** "markdown" | "JSON" | "structured JSON with specific schema"

**LLM returns:** Mix of:
- Pure markdown (sometimes with broken newlines)
- JSON strings containing markdown
- Nested JSON with content keys
- Escaped characters (\n not rendered as newlines)

**Parsing issues:**
```json
// Example broken historical_context:
"### Time Period\n\nText here" // Markdown with \n as literal strings
vs
"### Time Period

Actual newlines" // Proper markdown

// Example broken publishers_note:
{"publishers_note": {"content": "..."}} // Nested dict
vs
"Publisher note text..." // Direct string
```

**Result:** Content exists but renders as garbled text in PDF

## Files Affected

**Scripts:**
- `run_full_nimble_ultra_pipeline.py` - Pipeline orchestration
- `check_pdf_text_and_ocr.py` - OCR detection
- `resize_nimble_ultra_pdfs.py` - PDF formatting

**Prepress:**
- `imprints/nimble_ultra/prepress.py` - Template rendering (lines 400-500)
- `imprints/nimble_ultra/prompts.json` - Prompt definitions

**Output:**
- `output/nimble_ultra_full_pipeline/*/` - Final PDFs (have content but garbled)
- `output/nimble_ultra_ocr/CIA-RDP83-00423R002300010005-0_ocr.txt` - OCR text

## Root Cause Analysis

**Prompt Format Confusion:**
1. Some prompts request "ONLY valid JSON"
2. Others request "markdown with proper formatting"
3. Parser tries to handle both but gets confused

**Parsing Chain:**
1. LLM returns response
2. `_extract_content()` tries to parse (JSON? markdown? nested?)
3. Content passed to LaTeX renderer
4. Markdown→LaTeX conversion fails on escaped chars

## Fix Required

**Need consistent format strategy:**

**Option A:** All prompts request structured JSON, parse reliably, extract content
**Option B:** All prompts request clean markdown, no JSON wrapping
**Option C:** Separate prompts by type (metadata=JSON, narrative=markdown)

**Recommend Option C:**
- Bibliographic/metadata prompts → JSON schema with strict parsing
- Narrative prompts (context, passages, notes) → Pure markdown with format rules
- Update `_extract_content()` to handle both consistently

## To Resume

1. **Review prompts.json** - Categorize by response type needed
2. **Update prompts** - Make format requests consistent per category
3. **Fix _extract_content()** - Handle JSON vs markdown deterministically
4. **Test** - Run on one document, verify LaTeX rendering
5. **Rerun full pipeline** on both documents

## Files Ready for Review

**Working:**
- 2 resized PDFs (8.5x11, LSI-ready)
- OCR text for CIA document
- Full pipeline script (generates content, just rendering broken)

**Needs Fix:**
- Prompt format consistency
- Content extraction/parsing
- LaTeX rendering of extracted content

---

**Current working directory:** `/Users/fred/xcu_my_apps/nimble/codexes-factory`
**Branch:** `feature/nimble-ultra-prod-test`
**Worktrees available:**
- `worktrees/nimitz` → feature/nimitz (Nimitz harmonization)
- Main checkout → feature/nimble-ultra-prod-test (current work)
