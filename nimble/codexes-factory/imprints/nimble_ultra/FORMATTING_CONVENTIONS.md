# Nimble Ultra Imprint - Formatting Conventions

This document captures the specific formatting conventions and rules for the Nimble Ultra imprint.

## Pagination Format

### Body Section
- **Format:** `BODY:N` (with colon, no spaces)
- **Examples:** BODY:1, BODY:2, BODY:3, etc.
- **Implementation:** Footer displays as `BODY:N` throughout the body section
- **Previous format:** `BODY-N` (changed to use colon per user preference)

### Front Matter
- Uses lowercase Roman numerals (i, ii, iii, iv, v, etc.)
- Page i: Title page (unnumbered)
- Page ii: Copyright page (unnumbered, verso)
- Page iii: Table of Contents (unnumbered, recto)
- Page v and following: Front matter with printed page numbers

### Back Matter
- Uses format: `Back Matter - N`
- Continuous numbering from where body section ended

## Index Formatting

### General Rules
- **NO bullet points** or markdown formatting
- Plain text entries, one per line
- Format: `Name (description), page references`

### Page Number References
- **Format:** `BODY:N` (matches body pagination)
- **Ranges:** Use Chicago Manual of Style conventions
  - Consecutive pages: `BODY:1-3` (NOT `BODY:1, BODY:2, BODY:3`)
  - Non-consecutive: `BODY:1, BODY:5, BODY:12`
  - Mixed: `BODY:1-3, BODY:12, BODY:15-17`

### Index of Persons
```
Forrestal, James (US Secretary of Defense), BODY:1-3, BODY:12, BODY:34
Marshall, George (US Secretary of State), BODY:2, BODY:15-16
Truman, Harry S. (US President), BODY:1, BODY:6-8, BODY:22, BODY:38
```

### Index of Places
```
Berlin (Germany, divided city), BODY:1, BODY:5-7, BODY:12, BODY:28
Moscow (Soviet Union, capital), BODY:2-4, BODY:15, BODY:34, BODY:41
Washington D.C. (United States, capital), BODY:3, BODY:14-16, BODY:22
```

## Back Matter Structure

### Required Sections

1. **Back Matter** (chapter heading)
2. **Information** (section heading)
   - Standard text for declassified documents: "Indexes are generated with reference to the current document's pagination, not the original."
   - This explains that page references use BODY:N format of the current edition, not original document page numbers

3. **Index of Persons** (if applicable)
4. **Index of Places** (if applicable)
5. **Mnemonics** (if applicable)

## Document Type: Declassified Intelligence Documents

For this document type:
- Indexes reference current pagination (BODY:N), not original document page numbers
- Information section explicitly states this for reader clarity
- Page ranges formatted per Chicago Manual of Style

## Historical Notes

- **2025-10-24:** Changed from `BODY-N` to `BODY:N` format (colon instead of dash)
- **2025-10-24:** Implemented Chicago Manual of Style page ranges for indices
- **2025-10-24:** Added Information section to Back Matter explaining index pagination conventions
