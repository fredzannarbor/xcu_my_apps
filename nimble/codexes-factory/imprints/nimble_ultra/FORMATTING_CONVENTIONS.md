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
- Plain text entries
- **Double newlines between each entry** (blank line separates entries)
- Format: `Name (description), page references`

### Page Number References
- **Format:** `BODY:N` (matches body pagination)
- **Ranges:** Use Chicago Manual of Style conventions
  - Consecutive pages: `BODY:1-3` (NOT `BODY:1, BODY:2, BODY:3`)
  - Non-consecutive: `BODY:1, BODY:5, BODY:12`
  - Mixed: `BODY:1-3, BODY:12, BODY:15-17`

### Entry Spacing
- Each entry MUST be on its own line
- Each entry MUST be preceded and followed by a blank line (double newlines)

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

## Footer Layout

### Body Section Footer
- **Odd pages (recto):** Page number in outside (right) slot as `BODY:{n}`
- **Even pages (verso):** Page number in outside (left) slot as `BODY:{n}`
- **Format:** Combined format `BODY:{n}` in single slot, not split across center and outside
- **Example:** Footer displays as `BODY:1`, `BODY:2`, `BODY:3`, etc.

## Historical Context Formatting

### Section Structure
- All subsections use level 3 headings (`###`)
- Required sections:
  - Time Period and Geopolitical Situation
  - Intelligence Context
  - Strategic Significance
  - Long-term Impact

### Critical Spacing Rules
- **Strategic Significance section MUST always be followed by a blank line**
- Each `###` heading must be on its own line
- Blank line (double newline) after EVERY heading before body text
- Paragraphs separated by blank lines

## Most Important Passages Formatting

### Structure
- Each passage numbered: `### Passage 1`, `### Passage 2`, etc. (no title on heading line)
- Five passages total

### Elements (each on own line with blank line spacing)
1. **Passage Name:** Title on separate line after blank line
2. **Location:** On own line, followed by `Page BODY:N` on next line after blank line
3. **Quoted text:** Label on own line, quote on next line after blank line
4. **Significance:** Label on own line (preceded by blank line), explanation on next line after blank line

### Critical Rules
- **NO bullet points** in quoted text
- Quoted text rendered in italics (automatic)
- Each element MUST be separated by blank lines
- Location uses `BODY:N` format

### Example Format
```
### Passage 1

Passage Name:
Projected Soviet Economic Dominance

Location:
Page BODY:6

Quoted text:
It is not impossible that within a period of about ten years the joint economic power...

Significance:
This passage reveals the core long-term fear driving US Cold War strategy...
```

## Historical Notes

- **2025-10-24:** Changed from `BODY-N` to `BODY:N` format (colon instead of dash)
- **2025-10-24:** Implemented Chicago Manual of Style page ranges for indices
- **2025-10-24:** Added Information section to Back Matter explaining index pagination conventions
- **2025-10-24:** Fixed footer format to display `BODY:{n}` as combined unit in outside slot only
- **2025-10-24:** Updated index prompts to require double newlines between entries
- **2025-10-24:** Added JSON structure example to mnemonics prompt for clarity
- **2025-10-24:** Restructured Most Important Passages format: separate Passage Name, Location, Quoted text, and Significance labels on own lines
- **2025-10-24:** Removed bullet points from quoted text, ensured automatic italicization
- **2025-10-24:** Added explicit spacing requirement for Strategic Significance section
- **2025-10-24:** Changed passage headings to `### Passage N` format (number only, title on separate Passage Name line)
