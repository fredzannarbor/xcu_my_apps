# NIMBLE ULTRA FORMATTING FIXES - Complete Fix Document

## Issue Summary

1. **Index hanging indent BROKEN** - Currently indenting every entry; should only indent wrapped lines WITHIN an entry
2. **Missing Abstracts section** - `abstracts_x4` field is null
3. **Page number ranges not collapsed** - "1, 2, 3" should be "1-3"
4. **Missing vertical spacing** - Need 3pt leading between index entries
5. **Header font inconsistency** - Title should match author font
6. **Most Important Passages** - May have LaTeX conversion issues

---

## FIX #1: Index Hanging Indent (CRITICAL)

**File**: `/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/nimble_ultra/prepress.py`

**Location**: `_fix_index_formatting` method (lines 773-871)

**Current WRONG behavior**:
```
\hangindent=0.2in\hangafter=1 Eaglonia...
\hangindent=0.2in\hangafter=1 Ebnarlia...
```
This creates unwanted indent on EVERY entry.

**Required behavior**:
```
Eaglonia...

Ebnarlia...
```
(with 3pt space between entries, hanging indent only for wrapped lines)

**Fix**: Replace the entire loop section (lines 856-870) with:

```python
for line in lines:
    line = line.strip()
    if not line:
        continue  # Skip empty lines

    # Each entry gets hanging indent for wrapped lines only
    # Plus 3pt vertical space after the entry
    formatted_lines.append(f"\\hangindent=0.2in\\hangafter=1 {line}\\\\[3pt]")

return '\n'.join(formatted_lines)
```

---

## FIX #2: Page Number Range Collapsing

**File**: Same file, same method

**Add this function** before `_fix_index_formatting`:

```python
def _collapse_page_ranges(self, page_refs: str) -> str:
    """Collapse consecutive page numbers into ranges (e.g., '1, 2, 3' -> '1-3')"""
    import re

    # Extract all page numbers
    pages = re.findall(r'\d+', page_refs)
    if not pages:
        return page_refs

    pages = [int(p) for p in pages]
    pages.sort()

    # Group consecutive pages
    ranges = []
    start = pages[0]
    end = pages[0]

    for i in range(1, len(pages)):
        if pages[i] == end + 1:
            end = pages[i]
        else:
            # Add previous range
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = end = pages[i]

    # Add final range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return ', '.join(ranges)
```

**Then modify** `_fix_index_formatting` to call this before formatting BODY refs (around line 840):

```python
def deduplicate_page_refs(line):
    # ... existing code ...

    # AFTER deduplication, collapse ranges
    name_part = line.split('BODY:')[0] if 'BODY:' in line else line
    refs_part = line[len(name_part):] if 'BODY:' in line else ''

    if refs_part:
        collapsed = self._collapse_page_ranges(refs_part)
        line = name_part + collapsed

    return line
```

---

## FIX #3: Missing Abstracts Section

**File**: `/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/nimble_ultra/prepress.py`

**Location**: Lines 1268-1294 (top_level_front_matter mapping)

**Current code**:
```python
top_level_front_matter = {
    'bibliographic_key_phrases': 'keywords',
    'motivation': 'motivation',
    'historical_context': 'historical_context',
    'abstracts_x4': 'abstracts_x4',  # This field is NULL!
    'important_passages': 'most_important_passages_with_reasoning'
}
```

**The problem**: Need to check if this prompt is being run. The field is null in the JSON.

**Investigation needed**:
1. Check if `abstracts_x4` is in the prompts config
2. Check if the prompt key is being called in the pipeline
3. Check the field mapping in `llm_get_book_data.py` - might need to add it there too

---

## FIX #4: Header Font Consistency

**File**: Same prepress.py file

**Location**: Lines 559-563 (header definitions in `_generate_latex_with_pdf_body` method)

**Current**:
```latex
\\makeoddhead{{mypagestyle}}{{}}{{}}{{\\large\\scshape\\sffamily {title}}}
\\makeevenhead{{mypagestyle}}{{\\small\\textit{{{author}}}}}{{}}{{}}
```

**Fix** - Make title match author font (small italic):
```latex
\\makeoddhead{{mypagestyle}}{{}}{{}}{{\\small\\textit{{{title}}}}}
\\makeevenhead{{mypagestyle}}{{\\small\\textit{{{author}}}}}{{}}{{}}
```

---

## FIX #5: Most Important Passages LaTeX Conversion

**File**: Check if `_format_passages_quotes` is being called properly

**Verify** in line 440 area that this is still applying italic formatting correctly.

**Potential issue**: The markdown has `###` headers which may not be converting to LaTeX properly.

**Check**:
1. Is `_format_passages_quotes` being called?
2. Is `markdown_to_latex` properly handling the `###` headers in the passages?

---

## TESTING CHECKLIST

After applying all fixes, verify:
- [ ] Index entries are flush left
- [ ] Index wrapped lines are indented 0.2in
- [ ] 3pt space between index entries
- [ ] Page ranges collapsed (e.g., "17-19, 27, 32, 34-36")
- [ ] Abstracts section appears in PDF
- [ ] Header fonts match (both italic, small)
- [ ] Most Important Passages formatted correctly

---

## COMPLETED FIXES FROM CURRENT SESSION (2025-10-26)

### ✅ Fix 1: Index Hanging Indent (CRITICAL)
**File**: `imprints/nimble_ultra/prepress.py` (lines 860-869)
- Simplified formatting loop to add `\\[3pt]` spacing directly to each line
- Removed blank line insertion that was causing incorrect rendering
- Each entry now gets proper hanging indent with 3pt vertical space

### ✅ Fix 2: Page Number Range Collapsing
**File**: `imprints/nimble_ultra/prepress.py` (lines 777-811, 871-879)
- Added `_collapse_page_ranges()` method to convert consecutive pages to ranges
- Integrated range collapsing into `deduplicate_page_refs()` logic
- Page refs now properly collapse (e.g., "1, 2, 3" -> "1-3")

### ✅ Fix 3: Missing Abstracts Section
**File**: `src/codexes/modules/builders/llm_get_book_data.py` (lines 616-626)
- Added missing field mappings for abstracts_x4 and other markdown fields
- Now properly saves: abstracts_x4, motivation, historical_context, most_important_passages_with_reasoning, keywords
- These fields will now be populated in the JSON and rendered in the PDF

### ✅ Fix 4: Header Font Consistency
**File**: `imprints/nimble_ultra/prepress.py` (line 559)
- Changed odd page header from `\large\scshape\sffamily` to `\small\textit`
- Both headers now match (small italic font)

### ✅ Fix 5: Most Important Passages Formatting
**Status**: Verified working correctly
- `_format_passages_quotes()` is being called (line 440)
- Markdown headers (###) are properly converted via `markdown_to_latex`
- Special formatting for quotes is applied (italics, bullet removal)

---

## COMPLETED FIXES FROM PREVIOUS SESSION

### ✅ Fix 1: JSON Parser Fallback
**File**: `src/codexes/modules/builders/llm_get_book_data.py` (lines 558-583)
- Added fallback logic to use `raw_content` when JSON parser fails on markdown responses

### ✅ Fix 2: Field Mapping
**File**: `src/codexes/modules/builders/llm_get_book_data.py` (lines 608-626)
- Added field mapping to save string markdown to top-level JSON fields

### ✅ Fix 3: Extract Content Handler
**File**: `imprints/nimble_ultra/prepress.py` (lines 629-631)
- Modified `_extract_content()` to handle plain string markdown content

### ✅ Fix 4: Data Loading with Backward Compatibility
**File**: `imprints/nimble_ultra/prepress.py` (lines 1261-1355)
- Added intelligent data loading with primary/fallback pattern
- Reads from top-level JSON fields (new) with fallback to responses array (legacy)

---

**Status**: Ready for fresh session to apply remaining fixes
**Priority**: Fix #1 (hanging indent) is CRITICAL - must be fixed first
