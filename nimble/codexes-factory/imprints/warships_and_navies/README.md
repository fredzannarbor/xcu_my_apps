# Warships and Navies Imprint - Nimitz Project

**Project:** Fleet Admiral Chester W. Nimitz Reports
**Imprint:** Warships and Navies (Graybooks series)
**Status:** Active Development

## Project Overview

Multi-volume publication of Fleet Admiral Nimitz's comprehensive reports on naval operations, Pacific War strategy, and fleet command (1941-1945).

### Source Material
- **Primary Source:** MSC334_01_17_01.pdf (1 GB)
- **Location:** input_files_by_imprint/big_five_warships_and_navies/
- **Content:** Complete Nimitz reports with appendices

### Volume Structure
- **Total Volumes:** 8-9 planned
- **Volume Format:** 6x9 paperback, graybook style
- **OCR:** Gemini-enhanced OCR completed
- **Indices:** Comprehensive entities extraction

## Directory Structure

```
imprints/warships_and_navies/
├── README.md (this file)
├── scripts/ (processing tools)
│   ├── create_nimitz_volumes_final.py
│   ├── split_nimitz_into_volumes.py
│   ├── extract_nimitz_entities.py
│   └── [other processing scripts]
├── prompts/ (custom prompts for Nimitz)
├── volumes/ (organized by volume)
├── source/ (source PDFs)
├── nimitz_graybook_schedule.json
└── nimitz_volume_0_prompts.json

input_files_by_imprint/big_five_warships_and_navies/
├── MSC334_01_17_01.pdf (source)
├── by_volumes/ (split volumes)
├── nimitz_ocr_gemini/ (OCR processed, 116 items)
├── *.log (processing logs)
└── [processing scripts - see scripts/ above]
```

## Processing Scripts

### Volume Creation
- `create_nimitz_volumes_final.py` - Final volume creation
- `create_volumes_deterministic.py` - Deterministic splitting
- `split_nimitz_into_volumes.py` - Volume splitter

### OCR & Enhancement
- `ocr_nimitz_full.py` - Full OCR processing
- `ocr_nimitz_gemini.py` - Gemini OCR
- `retry_failed_nimitz_pages.py` - Retry failed pages
- `retry_failed_nimitz_pages_fixed.py` - Fixed retry script

### Analysis & Extraction
- `analyze_nimitz_pdf.py` - PDF analysis
- `extract_nimitz_bookmarks.py` - Extract bookmarks
- `extract_nimitz_entities.py` - Extract entities for indices
- `extract_nimitz_pages.py` - Page extraction

### Testing
- `compare_nimitz_ocr.py` - OCR comparison
- `test_ocr_comparison.py` - OCR quality testing

## Current Status

### Completed
✅ OCR processing of entire source document
✅ Volume splitting (8 volumes)
✅ Entity extraction for comprehensive indices
✅ Bookmark structure analysis

### In Progress
🚧 Index generation with cross-references
🚧 Volume formatting with Nimble Ultra pipeline
🚧 Comprehensive entity harmonization

### Planned
📋 Final volume production
📋 Cover generation for each volume
📋 LSI/distribution setup
📋 Marketing materials

## Key Files

**Schedule:** `nimitz_graybook_schedule.json`
- Volume definitions
- ISBN assignments (when ready)
- Publication timeline

**Prompts:** `nimitz_volume_0_prompts.json`
- Custom prompts for graybook format
- Entity extraction prompts
- Index generation prompts

## Volume Output

**OCR'd Volumes:** `input_files_by_imprint/big_five_warships_and_navies/nimitz_ocr_gemini/volumes_final/`
- nimitz_volume_1_final.pdf through nimitz_volume_8_final.pdf
- Clean, searchable PDFs ready for pipeline processing

## Next Steps

1. Finalize comprehensive indices
2. Process volumes through Nimble Ultra pipeline
3. Apply graybook formatting
4. Generate covers
5. Prepare for distribution

---

*Project Start: October 2025*
*Imprint: Warships and Navies*
*Branch: feature/nimitz*
