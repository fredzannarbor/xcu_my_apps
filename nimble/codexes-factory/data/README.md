# PT Boat Naval History Book

## Quick Start

### View the Book
```bash
open pt_boat_book.pdf
```

### Book Information

**Title:** Elco Naval Division of The Electric Boat Company
**Author:** Frank Andruss
**Format:** 7" × 10" photo book
**Pages:** 387
**Photos:** 347 high-resolution historical images
**Size:** 505 MB

## Contents

### Chapters
1. **Scott-Paine Design and the Elco 70 Foot Boat** (51 photos)
2. **Elco's Seventy-Seven-Foot Design** (51 photos)
3. **The Workers That Made It Happen** (67 photos)
4. **Elco 80 Foot** (69 photos)
5. **The Lighter Side of War** (67 photos)
7. **End of an Era** (42 photos)

*Note: Chapter 6 not included in source materials*

### Front & Back Matter
- Forward by Andrew J. Shanahan, Jr.
- Preface by Frank Andruss
- Table of Contents
- Acknowledgements

## Files in This Directory

| File | Description |
|------|-------------|
| `pt_boat_book.pdf` | **Final PDF book** (505 MB) |
| `pt_boat_book.tex` | LaTeX source document |
| `photo_manifest.json` | Complete photo-caption mapping |
| `build_log.txt` | LaTeX compilation log |
| `build_pt_book.py` | Main build script |
| `extract_odt.py` | ODT text extraction script |
| `BUILD_SUMMARY.md` | Detailed build summary |
| `COMPLETION_REPORT.md` | Project completion report |

## Rebuilding the Book

If you need to regenerate the PDF:

```bash
python3 build_pt_book.py
```

This will:
1. Re-extract text from ODT files
2. Re-match photos to captions
3. Regenerate LaTeX document
4. Compile new PDF

## Source Materials

Original files located in:
```
/Users/fred/Downloads/Files for New PT book/
```

## Photo Manifest

To view the complete photo-caption mapping:
```bash
cat photo_manifest.json | python3 -m json.tool | less
```

Or view specific chapter photos:
```bash
cat photo_manifest.json | python3 -c "import json,sys; m=json.load(sys.stdin); [print(f\"{p['photo_num']}: {p['caption'][:80]}...\") for p in m if p['chapter']==1]"
```

## Technical Details

### PDF Specifications
- **Page Size:** 7.0" × 10.0" (504 × 720 points)
- **Margins:** 0.75" all around (1" top/bottom)
- **Layout:** One photo per page with caption below
- **Photo Size:** Max 5.5" × 8" (maintains aspect ratio)
- **Font:** 11pt serif (book class)

### Build Process
- Text extraction from 16 ODT files
- 200+ TIF/TIFF to JPG conversions
- Caption parsing and photo matching
- LaTeX generation and compilation (2 passes)
- Total build time: ~5 minutes

## Historical Context

This book documents the **Elco Naval Division** in Bayonne, New Jersey, which was the largest American manufacturer of PT boats during World War II. The company built **399 PT boats** that served in both the Pacific and Mediterranean theaters.

### Key Figures
- **Henry R. Sutphen** - Executive Vice President
- **Irwin Chase** - Managing Constructor and design genius
- **Glenville S. Tremaine** - Chief Designer

### Historical Significance
- First American PT boats based on British Scott-Paine design
- Evolution from 70-foot through 77-foot to 80-foot designs
- State-of-the-art wooden boat manufacturing facility
- Critical contribution to Allied naval operations in WWII

## Support

For questions or modifications, see:
- `BUILD_SUMMARY.md` - Comprehensive build details
- `COMPLETION_REPORT.md` - Project completion report
- `build_log.txt` - LaTeX compilation details

---

**Status:** ✅ Complete and ready for review
**Quality:** Print-ready, high-resolution PDF
**Generated:** October 10, 2025

*"Although the PT Boat has long since gone, the bravery of the men who rode on her decks should never be forgotten."*
— Frank Andruss
