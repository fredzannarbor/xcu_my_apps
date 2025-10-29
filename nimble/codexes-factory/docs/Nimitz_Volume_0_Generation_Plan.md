# Nimitz Graybook Volume 0: Complete Generation Plan

**Document Version:** 1.0
**Date:** October 26, 2025
**Project:** Command Summary of Fleet Admiral Chester W. Nimitz, USN - Volume 0
**Imprint:** Warships & Navies
**Publisher:** Nimble Books LLC

---

## Executive Summary

### Overview

Volume 0 is the master reference guide and analytical companion to the 8-volume Nimitz Graybook collection (4,023 pages of WWII Pacific Theater primary sources). This document provides a complete, step-by-step plan to produce a publication-ready 150-page volume combining essential reference materials (70-80 pages of indices) with experimental analytical sections (40-50 pages).

### Key Inputs

- **Enhanced OCR Results**: 2,842 pages processed via Gemini Flash 2.0 (`nimitz_ocr_gemini/ocr_results.jsonl`, 7.4 MB)
- **Original PDF**: 4,023 pages with 297 bookmarks (`MSC334_01_17_01.pdf`)
- **Volume 0 Outline**: Comprehensive content plan at `/Users/fred/xcu_my_apps/nimble/codexes-factory/docs/Nimitz_Volume_0_Outline.md`
- **Existing Infrastructure**: Codexes-factory pipeline, LaTeX templates, LLM integration via nimble-llm-caller

### Key Outputs

- **Publication-ready PDF**: PDF/X-1a compliant, 8.5×11", color hardcover, ~150 pages
- **LSI-ready files**: Cover PDF, interior PDF, metadata CSV
- **Source files**: LaTeX, JSON metadata, intermediate processing files

### Timeline: 10-12 Weeks

- **Weeks 1-2**: Foundation (OCR enhancement, data extraction)
- **Weeks 3-4**: Indices creation (intensive human verification)
- **Weeks 5-6**: Experimental sections (human curation + AI assistance)
- **Weeks 7-8**: Assembly and appendices
- **Weeks 9-10**: QA, proofreading, final production

### Budget Estimate: ~$49,250

- Labor: $49,000 (naval historian, data specialist, writer/editor, designer, consultants)
- Technology: $250 (AI/LLM costs)

### Success Criteria

Volume 0 is ready when it:
1. Contains complete, accurate indices covering all 4,023 pages
2. Provides genuine utility to naval history enthusiasts
3. Passes all quality checks (accuracy, LaTeX compilation, PDF/X-1a compliance)
4. Receives positive feedback from 3+ beta readers
5. Meets 150-page target (±10 pages acceptable)

---

## Phase 0: Preparation & Setup (Week 1, Days 1-2)

### Objective
Set up project infrastructure, validate existing resources, and prepare the working environment.

### Tasks

#### 0.1 Project Directory Setup
**Input**: None
**Process**: Manual setup
**Output**: Organized directory structure

```bash
mkdir -p /Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/warships_and_navies/nimitz_volume_0/{
    data,
    data/extracted_entities,
    data/indices,
    data/visualizations,
    scripts,
    build,
    output
}
```

**Estimated Time**: 30 minutes

#### 0.2 Validate OCR Results
**Input**: `nimitz_ocr_gemini/ocr_results.jsonl`
**Process**: Automated validation script
**Output**: Validation report

Create `scripts/validate_ocr_data.py`:
- Check JSONL integrity (all 2,842 entries valid JSON)
- Verify page numbering sequence (0-4022)
- Calculate coverage statistics (success rate, average text length)
- Sample 100 random pages and compare with original PDF
- Report any missing or corrupted entries

**Quality Check**: Success rate should be >95%

**Estimated Time**: 2 hours

#### 0.3 Extract PDF Bookmarks
**Input**: Original PDF with 297 bookmarks
**Process**: Python script using PyMuPDF
**Output**: `data/bookmarks.json`

Create `scripts/extract_bookmarks.py`:
```python
import fitz  # PyMuPDF
import json

def extract_bookmarks(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    bookmarks = []

    for level, title, page in toc:
        bookmarks.append({
            "level": level,
            "title": title,
            "page": page,
            "volume": determine_volume(page)  # Map page to volume 1-8
        })

    return bookmarks
```

**Estimated Time**: 3 hours

#### 0.4 Set Up LLM Configuration
**Input**: Existing nimble-llm-caller configuration
**Process**: Configure models for Volume 0 generation
**Output**: `config/volume_0_llm_config.json`

Configure model tiers:
- **Tier 1 (Ultra-low cost)**: `gemini/gemini-2.0-flash-exp` for bulk entity extraction
- **Tier 2 (Balanced)**: `anthropic/claude-3-5-sonnet-20241022` for analysis and context writing
- **Tier 3 (High quality)**: `anthropic/claude-3-7-sonnet-20250219` for final editorial passes (if needed)

**Estimated Time**: 1 hour

#### 0.5 Create Master Task Tracker
**Input**: This generation plan
**Process**: Manual spreadsheet/project management setup
**Output**: Task tracking system (CSV, Notion, or similar)

Columns:
- Phase
- Task ID
- Task Name
- Dependencies
- Assigned To
- Status (Not Started / In Progress / Completed / Blocked)
- Estimated Hours
- Actual Hours
- Notes

**Estimated Time**: 2 hours

**Phase 0 Total Time**: 8-10 hours
**Phase 0 Deliverables**:
- Organized directory structure
- OCR validation report
- Bookmarks JSON file
- LLM configuration
- Task tracking system

---

## Phase 1: Data Extraction & Processing (Week 1-2)

### Objective
Extract structured data from OCR results to support index creation and data visualizations.

### 1.1 Entity Extraction: Persons (Week 1, Days 3-5)

**Input**: `ocr_results.jsonl`
**Process**: AI-assisted extraction with structured output
**Output**: `data/extracted_entities/persons_raw.json`

#### Script: `scripts/extract_persons.py`

**Processing Logic**:
1. Load OCR results in batches (100 pages at a time)
2. For each batch, prompt Gemini Flash 2.0:
```
Extract all person names mentioned in these pages. For each person:
- Full name (as written)
- Rank/title (if mentioned)
- Affiliation (US Navy, Japanese Navy, etc.)
- Page number(s) where mentioned
- Context (brief: what role/action)

Return as JSON array.
```

3. Use structured output (JSON schema) for consistency
4. Aggregate results across all batches
5. Save raw extraction results

**Expected Output Format**:
```json
[
  {
    "name": "Nimitz, Chester W.",
    "rank": "Admiral",
    "affiliation": "US Navy",
    "pages": [1, 15, 23, 156, ...],
    "contexts": {
      "1": "Assumed command as CINCPAC",
      "15": "Issued orders for Wake Island",
      ...
    }
  },
  ...
]
```

**Quality Metrics**:
- Expected entities: 2,000-3,000 persons
- Confidence threshold: Include all extractions, flag low-confidence (<0.7) for human review

**Cost Estimate**: 2,842 pages × ~2,000 tokens/batch × $0.000001/token ≈ $5-10

**Estimated Time**: 8 hours (script development + processing + QA)

### 1.2 Entity Extraction: Places (Week 1, Days 3-5, Parallel)

**Input**: `ocr_results.jsonl`
**Process**: Same as persons, different prompt
**Output**: `data/extracted_entities/places_raw.json`

#### Script: `scripts/extract_places.py`

**Prompt**:
```
Extract all geographic locations (islands, atolls, bases, cities, seas, etc.) mentioned in these pages. For each location:
- Name (as written)
- Type (island, base, city, sea, etc.)
- Region (if determinable: Solomons, Marianas, etc.)
- Page number(s)
- Context (battle, operation, or activity)

Return as JSON array.
```

**Expected Output**: 1,500-2,000 place names

**Cost Estimate**: ~$5-10

**Estimated Time**: 8 hours

### 1.3 Entity Extraction: Ships (Week 2, Days 1-2)

**Input**: `ocr_results.jsonl`
**Process**: Same pattern, ship-specific prompt
**Output**: `data/extracted_entities/ships_raw.json`

#### Script: `scripts/extract_ships.py`

**Prompt**:
```
Extract all ship names mentioned in these pages. For each ship:
- Name (e.g., "USS Enterprise")
- Hull number (if mentioned, e.g., "CV-6")
- Navy (US, Japanese, British, etc.)
- Ship type (carrier, battleship, cruiser, destroyer, submarine, etc.)
- Page number(s)
- Activity (damage, battle, movement, etc.)

Return as JSON array.
```

**Expected Output**: 1,500-2,500 ships

**Cost Estimate**: ~$5-10

**Estimated Time**: 8 hours

### 1.4 Entity Extraction: Organizations (Week 2, Days 1-2, Parallel)

**Input**: `ocr_results.jsonl`
**Process**: Same pattern, organization-specific prompt
**Output**: `data/extracted_entities/organizations_raw.json`

#### Script: `scripts/extract_organizations.py`

**Prompt**:
```
Extract all military organizations, units, task forces, and commands mentioned in these pages. For each:
- Name (e.g., "Task Force 16", "CINCPAC", "Third Fleet")
- Type (task force, fleet, division, shore command, etc.)
- Commander (if mentioned)
- Page number(s)
- Context (formation, operations, composition)

Return as JSON array.
```

**Expected Output**: 800-1,200 organizations

**Cost Estimate**: ~$5-10

**Estimated Time**: 8 hours

### 1.5 Data Extraction for Visualizations (Week 2, Days 3-4)

**Input**: `ocr_results.jsonl`
**Process**: Targeted extraction for specific data series
**Output**: Multiple CSV files for charting

#### Script: `scripts/extract_viz_data.py`

Extract:

1. **Fleet Strength Over Time** → `data/visualizations/fleet_strength.csv`
   - Columns: date, ship_type, count, operational_count, damaged_count
   - Method: Search for fleet composition reports, strength summaries
   - AI prompt: "Extract ship counts by type and date from this page"

2. **Major Operations Timeline** → `data/visualizations/operations.csv`
   - Columns: operation_name, start_date, end_date, type, location, forces_committed
   - Method: Identify operation names and dates from bookmarks + text
   - Human-assisted: Supplement with known operation list

3. **Geographic Scope** → `data/visualizations/locations.csv`
   - Columns: location, lat, lon, operation_date, operation_name
   - Method: Link places to operations, geocode locations
   - Note: Geocoding requires external API or manual lookup table

**Expected Outputs**:
- Fleet strength: ~200 data points (quarterly snapshots 1941-1945)
- Operations: ~50 major operations
- Locations: ~100 key locations with coordinates

**Cost Estimate**: ~$10-15 (more complex extraction)

**Estimated Time**: 16 hours

**Phase 1 Total Time**: ~60 hours
**Phase 1 Cost**: ~$40-50 (LLM)
**Phase 1 Deliverables**:
- `persons_raw.json` (2,000-3,000 entities)
- `places_raw.json` (1,500-2,000 entities)
- `ships_raw.json` (1,500-2,500 entities)
- `organizations_raw.json` (800-1,200 entities)
- Visualization data CSVs

---

## Phase 2: Reference Materials Generation (Week 2-3)

### Objective
Create the foundational reference content for Part I of Volume 0.

### 2.1 Complete Table of Contents (Week 2, Day 5)

**Input**: `data/bookmarks.json`
**Process**: Manual formatting with LaTeX template
**Output**: `content/complete_toc.tex`

#### Script: `scripts/format_toc.py`

**Processing Logic**:
1. Load bookmarks JSON
2. Group by volume (1-8)
3. Organize hierarchically (preserve bookmark levels 1-4)
4. Format as two-column LaTeX longtable
5. Calculate page budget (aim for 10-12 pages)

**LaTeX Format**:
```latex
\section*{Volume 1: 7 December 1941 to 31 August 1942 (Pages 1-861)}

\begin{longtable}{p{0.12\textwidth} p{0.68\textwidth} p{0.15\textwidth}}
\toprule
Date & Section & Page \\
\midrule
7 Dec 1941 & Attack on Pearl Harbor & 1:15 \\
8 Dec 1941 & Initial Damage Assessment & 1:23 \\
...
\bottomrule
\end{longtable}
```

**Estimated Time**: 6 hours

### 2.2 Publisher's Note (Week 2, Day 5, Parallel)

**Input**: Imprint philosophy (Jellicoe persona), outline guidance
**Process**: Human writing in Jellicoe voice
**Output**: `content/publishers_note.tex`

**Content Requirements** (2-3 pages):
- Welcome and mission statement
- Why the Graybooks matter (primary sources sacred)
- What makes Volume 0 unique
- How to use this volume with Volumes 1-8
- Preservation and accessibility balance
- Tone: Authoritative, scholarly, passionate about naval history

**Author**: Lead editor/writer
**Estimated Time**: 4 hours

### 2.3 About This Edition (Week 3, Day 1)

**Input**: Publishing context, digitization history
**Process**: Human writing
**Output**: `content/about_edition.tex`

**Content Requirements** (1-2 pages):
- What is the Nimitz Graybook? (historical background)
- Original source and public domain status
- Why publish now? (preservation, accessibility)
- Physical characteristics of originals
- Scope of collection (4,023 pages, 1941-1945)

**Author**: Lead editor/writer
**Estimated Time**: 3 hours

### 2.4 Note on Methods (Week 3, Days 1-2)

**Input**: OCR methodology, AI usage, index creation process
**Process**: Human writing with technical accuracy
**Output**: `content/methods_note.tex`

**Content Requirements** (3-4 pages):

**Subsection A: OCR Enhancement** (2 pages)
- Original PDF quality issues
- Decision to use Gemini Flash 2.0
- Process description (page-by-page analysis)
- Cost transparency (~$50 for 4,023 pages)
- Accuracy improvements vs. standard OCR
- Limitations and known errors
- Where enhanced OCR is used (indices) vs. original images (preserved pages)

**Subsection B: AI-Generated Content** (1 page)
- Which sections use AI (experimental only, not indices)
- Human oversight process
- Quality assurance steps
- Transparency commitment
- Why AI: scalability, pattern recognition

**Subsection C: Index Creation** (0.5 pages)
- Automated extraction + human verification
- Subject matter expert review
- Cross-referencing methodology
- Format standards

**Subsection D: Editorial Standards** (0.5 pages)
- Preservation priority (original pages as-is)
- No modernization of language
- Distinction between original and editorial content

**Author**: Lead editor/writer with technical input
**Estimated Time**: 6 hours

**Phase 2 Total Time**: 19 hours
**Phase 2 Deliverables**:
- Complete TOC (10-12 pages, LaTeX)
- Publisher's Note (2-3 pages, LaTeX)
- About This Edition (1-2 pages, LaTeX)
- Note on Methods (3-4 pages, LaTeX)

---

## Phase 3: Indices Generation (Week 3-4) — INTENSIVE PHASE

### Objective
Transform raw entity extractions into publication-ready indices through rigorous human verification and cross-referencing.

**Critical Success Factor**: Index quality is the primary value proposition of Volume 0. This phase requires expert attention and cannot be rushed.

### 3.1 Index of Persons: Verification & Enhancement (Week 3, Days 3-5)

**Input**: `data/extracted_entities/persons_raw.json`
**Process**: Human verification with AI assistance
**Output**: `data/indices/persons_verified.json` → `content/index_persons.tex`

#### Script: `scripts/build_person_index.py`

**Human Verification Tasks**:
1. **Deduplication**: Merge variant spellings and name forms
   - "Nimitz, Chester W." = "Nimitz, C.W." = "Admiral Nimitz"
   - "Halsey, William F." = "Halsey, Bull" = "Admiral Halsey"
   - AI assistance: Suggest potential duplicates based on name similarity

2. **Disambiguation**: Separate people with same names
   - Multiple "Lieutenant Smith" entries → identify by context
   - Japanese names (romanization variants)

3. **Rank/Title Verification**:
   - Confirm ranks at time of reference
   - Note promotions where significant
   - Cross-reference with naval registers (Navy.mil, Wikipedia)

4. **Cross-References**: Add "See also" entries
   - Command positions → see organization entries
   - "Fletcher, Frank Jack" → see also "Task Force 17"

5. **Page Reference Consolidation**:
   - Collapse dense page ranges (e.g., "throughout Volumes 2-3")
   - Highlight key passages vs. passing mentions

**Two-Column LaTeX Format**:
```latex
\begin{multicols}{2}
\small
\noindent
\textbf{Nimitz, Chester W., ADM}\\
\hspace*{1em}Appointment as CINCPAC: 1:1\\
\hspace*{1em}Pearl Harbor aftermath: 1:15-45\\
\hspace*{1em}Midway decision: 1:445-478\\
\hspace*{1em}\textit{See also:} CINCPAC, Commander in Chief Pacific\\

\noindent
\textbf{Spruance, Raymond A., RADM (later ADM)}\\
\hspace*{1em}Midway command: 1:456-478\\
\hspace*{1em}Central Pacific operations: 4:125-230\\
...
\end{multicols}
```

**Quality Metrics**:
- Target: 2,000-2,500 verified persons (after deduplication)
- Page count: 20-24 pages
- Spot check: 100 random entries verified against source pages

**Personnel**: Naval historian (primary), data specialist (AI tools support)
**Estimated Time**: 40 hours (intensive)

### 3.2 Index of Places: Verification & Enhancement (Week 3-4)

**Input**: `data/extracted_entities/places_raw.json`
**Process**: Same verification pattern as persons
**Output**: `data/indices/places_verified.json` → `content/index_places.tex`

#### Script: `scripts/build_place_index.py`

**Additional Tasks Beyond Persons**:
- **Geographic Hierarchy**: Organize by region
  - Main entry: "Guadalcanal (Solomon Islands)"
  - Sub-entries: Henderson Field, specific beach codes
- **Code Name Cross-References**:
  - "Cactus" → see "Guadalcanal"
  - "King II" → see "Tarawa operation"
- **Coordinates**: Optional (if time permits, add lat/lon for major locations)

**Expected Output**: 1,500-1,800 verified places, 14-18 pages

**Personnel**: Naval historian + geographic specialist (or atlas reference)
**Estimated Time**: 30 hours

### 3.3 Index of Ships: Verification & Enhancement (Week 4, Days 1-2)

**Input**: `data/extracted_entities/ships_raw.json`
**Process**: Ship-specific verification
**Output**: `data/indices/ships_verified.json` → `content/index_ships.tex`

#### Script: `scripts/build_ship_index.py`

**Ship-Specific Tasks**:
- **Hull Number Verification**: Confirm accuracy (CV-6, BB-64, etc.)
- **Ship Type Standardization**: Use consistent abbreviations
- **Fate Tracking**: Note sinkings, major damage, decommissioning
- **Task Force Cross-References**: Link ships to task forces
- **Sister Ships**: Group ship classes (Essex-class carriers, etc.)

**Appendix to Ship Index** (2 pages):
- Ship type abbreviations glossary
- Hull number system explanation
- Japanese ship naming conventions

**Expected Output**: 1,500-2,000 verified ships, 20-24 pages (including appendix)

**Personnel**: Naval historian with ship expertise
**Estimated Time**: 35 hours

### 3.4 Index of Organizations: Verification (Week 4, Days 3-4)

**Input**: `data/extracted_entities/organizations_raw.json`
**Process**: Organization hierarchy verification
**Output**: `data/indices/organizations_verified.json` → `content/index_organizations.tex`

**Organization-Specific Tasks**:
- **Hierarchy Mapping**: Show parent-child relationships
  - "Third Fleet" → contains "Task Force 38" → contains "TG 38.2"
- **Command Relationships**: Link to commanders
- **Evolution Over Time**: Note reorganizations (3rd/5th Fleet alternation)
- **Abbreviation Expansion**: Full names for all acronyms

**Expected Output**: 800-1,000 verified organizations, 10-12 pages

**Personnel**: Naval historian
**Estimated Time**: 25 hours

### 3.5 Glossary of Naval Terminology (Week 4, Days 4-5)

**Input**: Combined entity extractions + naval terminology resources
**Process**: Curated glossary building
**Output**: `content/glossary.tex`

#### Script: `scripts/build_glossary.py`

**Sources**:
1. **Extracted Terms**: AI scan of OCR text for abbreviations and technical terms
2. **Standard References**:
   - Navy.mil glossaries
   - Jane's Fighting Ships terminology
   - WWII-era naval manuals
3. **Expert Knowledge**: Naval historian fills gaps

**Term Categories**:
- Abbreviations (AA, CINCPAC, TBS, etc.)
- Technical terms (knots, fathoms, turret, etc.)
- Operational terms (amphibious, CAP, etc.)
- Japanese terms (when used in documents)
- Period slang ("Tin Can Navy", etc.)

**Format** (two-column):
```latex
\noindent
\textbf{AA (Anti-Aircraft)}\\
Defensive fire against enemy aircraft. Also ``ack-ack.''\\
\textit{See also:} CAP, VT fuse\\
```

**Appendix to Glossary** (1 page):
- Rank abbreviations (RADM, VADM, etc.)
- Phonetic alphabet (1940s version)
- Time zone conventions

**Expected Output**: 500-600 terms, 10-14 pages

**Personnel**: Naval historian + writer
**Estimated Time**: 20 hours

### 3.6 How to Use These Indices (Week 4, Day 5)

**Input**: Completed indices structure
**Process**: Human writing (instructional)
**Output**: `content/index_intro.tex`

**Content** (2 pages):
- Citation format explanation (Volume:Page)
- Cross-reference system
- Abbreviations used
- Coverage and limitations
- Tips for effective use
- Known issues (illegible pages, ambiguous references)

**Personnel**: Lead writer
**Estimated Time**: 3 hours

**Phase 3 Total Time**: ~153 hours (intensive human effort)
**Phase 3 Deliverables**:
- Index of Persons (20-24 pages)
- Index of Places (14-18 pages)
- Index of Ships (20-24 pages)
- Index of Organizations (10-12 pages)
- Glossary (10-14 pages)
- How to Use Indices (2 pages)
- **Total: 76-94 pages of indices**

---

## Phase 4: Experimental Sections Generation (Week 5-6)

### Objective
Create the analytical companion sections that demonstrate "possibility space" thinking.

### 4.1 Introduction to Possibility Space (Week 5, Day 1)

**Input**: Outline philosophy, xtuff.ai concepts
**Process**: Human writing
**Output**: `content/intro_possibility_space.tex`

**Content** (2 pages):
- What are these experiments?
- Why include them? (intellectual diversity)
- How to use (invitations, not requirements)
- Ground rules (never distort history)
- Transparency about AI-generated content

**Personnel**: Lead writer/editor
**Estimated Time**: 4 hours

### 4.2 Data Visualizations (Week 5, Days 1-2)

**Input**: `data/visualizations/*.csv` from Phase 1.5
**Process**: Python data visualization + LaTeX integration
**Output**: `content/data_visualizations.tex` + image files

#### Script: `scripts/generate_visualizations.py`

**Visualizations to Create**:

1. **Fleet Strength Over Time** (line chart)
   - Tool: matplotlib/seaborn
   - X-axis: Quarterly dates (Dec 1941 - Aug 1945)
   - Y-axis: Ship count by type (stacked or multi-line)
   - Annotations: Pearl Harbor, Midway, major losses

2. **Geographic Scope of Operations** (map)
   - Tool: matplotlib + basemap OR static design in Adobe Illustrator
   - Pacific Theater outline
   - Color-coded by year (1942, 1943, 1944, 1945)
   - Major battles/operations marked

3. **Operational Tempo** (bar chart)
   - Operations by quarter, scaled by forces committed
   - Shows ramp-up from 1942 to peak in 1944

4. **Ship Type Distribution** (pie charts)
   - 5 snapshots: Pre-Pearl, Post-Pearl, Mid-1942, End-1944, V-J Day
   - Shows shift from battleships to carriers

5. **Command Structure Evolution** (org charts)
   - 1942 structure vs. 1944 structure
   - Hierarchical boxes

**LaTeX Integration**:
```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{visualizations/fleet_strength.pdf}
\caption{US Pacific Fleet Strength by Ship Type, 1941-1945}
\label{fig:fleet_strength}
\end{figure}
```

**Appendix**: Data sources and methodology (1 page)

**Expected Output**: 8-10 pages (5 visualizations + intro + appendix)

**Personnel**: Data analyst/designer + naval historian (verification)
**Estimated Time**: 16 hours

### 4.3 Most Important Passages (Week 5, Days 3-5) — HIGH-VALUE CURATION

**Input**: Enhanced OCR, bookmarks, indices
**Process**: Human expert curation + AI context generation
**Output**: `content/important_passages.tex`

#### Script: `scripts/curate_important_passages.py` (AI-assisted context only)

**Human Curation Process**:
1. **Selection Criteria**:
   - Historical significance (turning points)
   - Insight into decision-making
   - Literary quality (well-written dispatches)
   - Representative of volume's content
   - Teachable moments

2. **Expert Reading**: Naval historian reads/skims all 8 volumes with indices
   - Flag ~100 candidate passages
   - Narrow to 40 (5 per volume)
   - Ensure thematic diversity

3. **AI Context Generation**: For each selected passage:
   - Prompt: "Write 2-3 sentence context for this passage: [quote passage]. Explain historical situation, why significant, what came next."
   - Human edits for accuracy

**Organization**: 7 thematic clusters (not chronological)
- Strategic Turning Points (5-6 passages)
- Operational Innovation (5-6 passages)
- Crisis Management (5-6 passages)
- Intelligence & Code-Breaking (5-6 passages)
- Leadership & Decision-Making (5-6 passages)
- Human Element (5-6 passages)
- Technical & Logistical Mastery (5-6 passages)

**Format** (per passage):
- Theme heading
- Passage title
- Volume and page reference
- Context (2-3 sentences)
- Brief excerpt (3-4 sentences) OR page range for extended discussion

**Expected Output**: 12-15 pages (40 passages × ~0.3 pages each)

**Personnel**: Naval historian (primary, 30 hours) + writer (AI context editing, 8 hours)
**Estimated Time**: 38 hours

### 4.4 Reading Guides: Thematic Paths (Week 5-6)

**Input**: Indices, bookmarks, important passages
**Process**: Human path design + AI page compilation
**Output**: `content/reading_guides.tex`

#### Script: `scripts/compile_reading_paths.py` (AI-assisted page finding)

**Path Creation Process**:
1. **Path Design** (human expert):
   - Select 6 themes (Guadalcanal, Amphibious Warfare, Intelligence, Submarines, Logistics, Air-Naval Coordination)
   - Define scope and learning objectives for each
   - Identify key topics within each path

2. **Page Reference Compilation** (AI-assisted):
   - Prompt: "Find all page references in indices related to [topic]"
   - AI aggregates page numbers from indices
   - Human curates and sequences (chronological or logical order)

3. **Path Formatting**:
   - Introduction to path (learning objectives)
   - Chronological/thematic section breakdown
   - Page references by volume
   - Estimated reading time
   - Key highlights

**Example Path Structure**:
```
Path 1: The Guadalcanal Campaign (1.5 pages)

Introduction: First major offensive, critical turning point...

Section 1: Planning (Jul-Aug 1942)
- Initial planning: 1:756-789
- Intelligence assessments: 1:790-810
- Force composition: 1:811-825

Section 2: Landings and Naval Battles (Aug-Nov 1942)
- D-Day landings: 2:1-23
- Battle of Savo Island: 2:24-56
...

Estimated reading: 300-400 pages across Volumes 1-3
Key highlights: Henderson Field operations, night surface battles
```

**Expected Output**: 6-8 pages (6 paths × ~1 page each)

**Personnel**: Naval historian
**Estimated Time**: 16 hours

### 4.5 Communication Styles Analysis (Week 6, Day 1)

**Input**: Selected Nimitz dispatches, modern format knowledge
**Process**: AI-generated analysis + human editing
**Output**: `content/communication_analysis.tex`

#### Script: `scripts/analyze_communication_styles.py`

**Process**:
1. **Select Examples**: Choose 3-4 representative Nimitz dispatches
2. **AI Analysis**: Prompt Claude Sonnet:
```
Analyze these WWII naval dispatches by Admiral Nimitz. Compare his communication style to:
1. Amazon 6-pager format (narrative decision memos)
2. Modern military decision brief format
3. Corporate memo standards

For each format, discuss:
- Structure differences
- Information density
- Clarity mechanisms
- Trade-offs (brevity vs. completeness)

What universal principles of effective communication emerge?
```

3. **Human Editing**:
   - Verify historical accuracy
   - Ensure respectful tone (not claiming modern methods are "better")
   - Add specific examples

**Content Structure**:
- Introduction (1 page)
- Nimitz's style characteristics (1.5 pages)
- Modern formats overview (1 page)
- Comparative analysis table (0.5 pages)
- Universal principles (1 page)

**Expected Output**: 4-6 pages

**Personnel**: Writer + naval historian (fact-checking)
**Estimated Time**: 10 hours

### 4.6 Battle of Midway as Amazon 6-Pager (Week 6, Days 1-2)

**Input**: Midway dispatches and decisions from Volume 1
**Process**: AI generation + historical fact-checking
**Output**: `content/midway_6pager.tex`

#### Script: `scripts/generate_midway_memo.py`

**Process**:
1. **Extract Midway Content**: Pull relevant pages (1:445-523)
2. **AI Memo Generation**: Prompt Claude Sonnet:
```
Based on these Midway dispatches, write a decision memo in Amazon 6-pager format:
- Introduction: Context and decision
- Goals: 3-4 bullet points
- Tenets: Strategic principles
- State of the Situation: Intelligence, forces, risks
- Execution Plan: Positioning, trigger, attack priorities
- Questions Anticipated: What-ifs and contingencies

Use ONLY factual information from these documents. No speculation.
```

3. **Human Fact-Checking**: Naval historian verifies every claim
4. **Add Side-by-Side Comparison**: Original dispatches vs. 6-pager sections

**Content Structure**:
- Introduction (1 page)
- Actual Midway dispatches (excerpts, 0.5 pages)
- Midway as 6-pager (2.5 pages)
- Side-by-side comparison table (0.5 pages)
- Analysis: What changed? (1 page)

**Expected Output**: 3-5 pages

**Personnel**: Writer + naval historian
**Estimated Time**: 12 hours

### 4.7 For Wargamers: Scenario Conversion Notes (Week 6, Days 3-4)

**Input**: OCR text, indices, operational data
**Process**: Wargaming expert curation + AI data extraction
**Output**: `content/wargaming_scenarios.tex`

#### Script: `scripts/extract_scenario_data.py` (AI assists with OOB extraction)

**Process**:
1. **Scenario Selection** (human expert):
   - Choose 4-5 operations suitable for wargaming:
     * Midway (Jun 1942)
     * Guadalcanal Naval Battles (Aug-Nov 1942)
     * Philippine Sea (Jun 1944)
     * Leyte Gulf (Oct 1944)
     * Okinawa Kamikaze Defense (Apr-Jun 1945)

2. **Data Extraction** (AI-assisted):
   - Order of Battle: Ships by name and type
   - Timeline: Key events by hour/day
   - Forces: Exact compositions
   - AI prompt: "Extract complete order of battle for [battle] from pages [X-Y]"

3. **Scenario Design** (human expert):
   - Victory conditions
   - Special rules (intelligence asymmetry, pilot quality, etc.)
   - Map data requirements
   - Recommended game systems
   - Design notes (balancing history vs. playability)

**Format** (per scenario, 2 pages):
- Historical summary (0.25 pages)
- Order of Battle (0.75 pages, detailed lists)
- Timeline (0.5 pages)
- Victory conditions & special rules (0.5 pages)

**Plus**:
- Introduction (1 page)
- General design notes (0.5 pages)
- Data sources guide (0.5 pages)

**Expected Output**: 8-10 pages (5 scenarios + supplementary)

**Personnel**: Wargaming consultant (specialist) + AI data extraction
**Estimated Time**: 25 hours (consultant time)

### 4.8 Metadata of War: Pink vs. Green Paper (Week 6, Day 5)

**Input**: Original PDF analysis, archival research
**Process**: Archival researcher investigation + writing
**Output**: `content/metadata_war.tex`

**Research Tasks**:
1. **Examine Original PDF**: Sample 100 pages, categorize by color (pink, green, white)
2. **Archival Research**: Consult NHHC documentation, archival guides
3. **Hypothesis Formation**: What do colors signify?
   - Draft vs. final?
   - Classification levels?
   - Different sources (CINCPAC vs. subordinate commands)?
4. **Write Analysis**: Document findings, acknowledge uncertainties

**Content Structure**:
- Introduction (1 page)
- Color-coding system analysis (1 page)
- Classification markings (1 page)
- Document characteristics (typewritten, carbon copies, annotations) (0.5 pages)
- Reading documents as artifacts (0.5 pages)

**Expected Output**: 3-4 pages

**Personnel**: Archival researcher + writer
**Estimated Time**: 15 hours

**Phase 4 Total Time**: ~136 hours
**Phase 4 Cost**: ~$50-100 (LLM for context generation, analysis)
**Phase 4 Deliverables**:
- Introduction (2 pages)
- Data Visualizations (8-10 pages)
- Most Important Passages (12-15 pages)
- Reading Guides (6-8 pages)
- Communication Styles (4-6 pages)
- Midway 6-Pager (3-5 pages)
- Wargaming Scenarios (8-10 pages)
- Metadata of War (3-4 pages)
- **Total: 46-60 pages of experimental sections**

---

## Phase 5: Assembly & Finalization (Week 7-8)

### Objective
Combine all components into a cohesive LaTeX document and compile to PDF.

### 5.1 Appendices Creation (Week 7, Days 1-2)

**Input**: Project records, sources used
**Process**: Human writing
**Output**: `content/appendices.tex`

#### Appendix A: Sources and References (2-3 pages)
- Primary sources (NHHC collection info)
- Secondary sources (select bibliography, 10-15 key works)
- Archival sources
- Online resources
- Acknowledgment of gaps

#### Appendix B: About Warships & Navies (1 page)
- Imprint mission
- Jellicoe persona statement
- Other titles in catalog
- Contact information

#### Appendix C: About Nimble Books LLC (1 page)
- Company background
- Publishing philosophy (AI-assisted, human-curated)
- Technology and innovation
- Other imprints

#### Appendix D: Acknowledgments (1 page, optional)
- Contributors
- Institutional support
- Technology partners
- Community thanks

**Personnel**: Lead writer/editor
**Estimated Time**: 8 hours

### 5.2 LaTeX Template Creation (Week 7, Days 2-3)

**Input**: Nimitz Graybook template (existing), outline structure
**Process**: Adapt template for Volume 0 (text-heavy, not page scans)
**Output**: `templates/nimitz_volume_0_template.tex`

#### Script: `scripts/create_volume_0_template.py`

**Template Requirements**:
- **Front Matter**: Title page, copyright, TOC for Volume 0
- **Part I**: Reference materials (standard text formatting)
- **Part II**: Indices (two-column, dense, sans-serif for readability)
- **Part III**: Experimental sections (standard text + figures)
- **Appendices**: Standard formatting
- **Page Numbers**: Roman numerals (front matter), Arabic (main content)
- **Headers/Footers**: Volume 0 branding

**Key LaTeX Packages**:
- `geometry` (8.5×11", appropriate margins)
- `multicol` (two-column indices)
- `longtable` (multi-page tables for TOC, indices)
- `hyperref` (bookmarks, internal links)
- `graphicx` (data visualization figures)
- `fontspec` (font selection: Adobe Caslon Pro for body, Helvetica for headers)

**Jinja2 Variables**:
- `{{ TITLE }}`, `{{ VOLUME_NUMBER }}`, `{{ ISBN }}`
- `{{ PART_I_CONTENT }}`, `{{ PART_II_CONTENT }}`, `{{ PART_III_CONTENT }}`

**Personnel**: Book designer (LaTeX expert)
**Estimated Time**: 12 hours

### 5.3 Content Assembly (Week 7, Days 4-5)

**Input**: All `.tex` content files from Phases 2-4
**Process**: Integrate into master LaTeX document
**Output**: `build/nimitz_volume_0_master.tex`

#### Script: `scripts/assemble_volume_0.py`

**Assembly Process**:
1. Load template
2. Insert front matter (publishers note, about edition, methods)
3. Insert Part I (complete TOC)
4. Insert Part II (all indices in order)
5. Insert Part III (all experimental sections in order)
6. Insert appendices
7. Verify all cross-references resolve
8. Check page count estimate (should be ~150 pages)

**Quality Checks**:
- All `\label{}` and `\ref{}` pairs valid
- All figures exist and compile
- No missing citations
- LaTeX syntax valid (test compile)

**Personnel**: Book designer + developer
**Estimated Time**: 8 hours

### 5.4 Initial Compilation & Debugging (Week 7, Day 5)

**Input**: `nimitz_volume_0_master.tex`
**Process**: LuaLaTeX compilation
**Output**: `build/nimitz_volume_0_draft.pdf`

#### Compilation Command:
```bash
cd build
lualatex nimitz_volume_0_master.tex
bibtex nimitz_volume_0_master  # if using bibliography
lualatex nimitz_volume_0_master.tex
lualatex nimitz_volume_0_master.tex
```

**Expected Issues**:
- Overfull/underfull hboxes (formatting adjustments)
- Missing figures (path issues)
- Font errors (ensure fonts installed)
- Long tables breaking across pages (adjust longtable settings)

**Iterative Debugging**: Fix errors, recompile, repeat until clean

**Personnel**: Book designer
**Estimated Time**: 8 hours (expect multiple iterations)

### 5.5 Page Count Adjustment (Week 8, Day 1)

**Input**: Draft PDF with actual page count
**Process**: Adjust content to hit 150-page target
**Output**: Revised LaTeX files

**If Over 150 Pages** (reduce):
- Tighten TOC formatting (-2 to -3 pages)
- Reduce Organizations index (-2 to -3 pages)
- Trim wargaming scenarios from 5 to 3 (-2 to -3 pages)
- Adjust margins/spacing slightly

**If Under 150 Pages** (expand):
- Expand Most Important Passages (+3 to +5 pages)
- Expand Glossary (+2 to +4 pages)
- Add more data visualizations (+2 to +3 pages)

**Target Range**: 145-155 pages acceptable

**Personnel**: Book designer + lead editor (content decisions)
**Estimated Time**: 4 hours

### 5.6 Cover Generation (Week 8, Days 1-2)

**Input**: Metadata, existing Nimitz cover template
**Process**: Design cover for Volume 0
**Output**: `covers/nimitz_volume_0_cover.pdf`

#### Cover Design Requirements (per LSI specs):
- **Trim Size**: 8.5×11" hardcover
- **Spine Width**: Calculate based on final page count (150 pages ≈ 0.3-0.4" spine)
- **Bleed**: 0.125" all sides
- **Total Size**: Width = (8.5 × 2) + spine + (0.125 × 2), Height = 11 + (0.125 × 2)

**Design Elements**:
- **Front Cover**:
  - Title: "Command Summary of Fleet Admiral Chester W. Nimitz, USN"
  - Volume number: "Volume 0"
  - Subtitle: "Master Guide and Analytical Companion"
  - Imagery: Naval/archival theme (compass rose, vintage map, or abstract)
  - Warships & Navies logo
- **Spine**: Title, Volume 0, Publisher
- **Back Cover**:
  - Description (150-200 words)
  - Barcode (ISBN-13)
  - Price ($34.99)
  - Publisher info

**Tools**: Adobe InDesign or LaTeX (using existing template adapted)

**Personnel**: Book designer / cover designer
**Estimated Time**: 8 hours

**Phase 5 Total Time**: 48 hours
**Phase 5 Deliverables**:
- Complete appendices (5-7 pages)
- Volume 0 LaTeX template
- Assembled master LaTeX file
- Draft PDF (~150 pages)
- Final cover PDF

---

## Phase 6: Quality Assurance (Week 9-10)

### Objective
Ensure accuracy, completeness, and publication readiness through rigorous testing.

### 6.1 Automated Validation (Week 9, Day 1)

**Input**: Draft PDF, LaTeX source, index JSON files
**Process**: Automated test suite
**Output**: Validation report with pass/fail status

#### Script: `scripts/validate_volume_0.py`

**Automated Tests**:

1. **Index Entry Validation**:
   - Parse all index entries
   - Extract page references (e.g., "1:456", "3:23-45")
   - Verify all page numbers are within valid ranges:
     * Volume 1: 1-861
     * Volume 2: 862-1262
     * Volume 3: 1263-1612
     * Volume 4: 1613-1830
     * Volume 5: 1831-2485
     * Volume 6: 2486-3249
     * Volume 7: 3250-3548
     * Volume 8: Non-sequential (skip validation)
   - Report any out-of-range references

2. **Cross-Reference Verification**:
   - Find all "See also" entries in indices
   - Verify referenced entries exist
   - Report dangling cross-references

3. **LaTeX Compilation Test**:
   - Clean build from scratch
   - Check for errors/warnings
   - Verify PDF generates without crashes

4. **PDF/X-1a Compliance Pre-Check**:
   - Check color space (CMYK only for print)
   - Verify fonts embedded
   - Check image resolution (300+ DPI for print)
   - Validate page size consistency

5. **Hyperlink Validation**:
   - Test internal hyperlinks (TOC → sections)
   - Verify external URLs (if any)

**Pass Criteria**: All tests pass OR only minor warnings (no errors)

**Personnel**: Developer/QA specialist
**Estimated Time**: 6 hours

### 6.2 Content Accuracy Spot Check (Week 9, Days 2-3)

**Input**: Draft PDF, original Graybook PDFs
**Process**: Manual verification sampling
**Output**: Spot check report

**Sampling Strategy**:
1. **Index Accuracy**: Random sample 100 index entries (25 each from persons, places, ships, organizations)
   - Verify person/place/ship actually appears on cited page
   - Check context accuracy
   - Record error rate (target: <5% errors)

2. **Historical Facts**: Review all factual claims in experimental sections
   - Battle dates correct?
   - Ship names and types correct?
   - Command relationships accurate?
   - Cross-reference with standard sources (Morison, Potter)

3. **Most Important Passages**: Verify all 40 passages
   - Correct volume and page references
   - Context summaries accurate
   - Quotes verbatim (if excerpts included)

**Personnel**: Naval historian + fact-checker
**Estimated Time**: 16 hours

### 6.3 Proofreading Pass 1: Structural (Week 9, Days 4-5)

**Input**: Draft PDF
**Process**: Structural proofreading
**Output**: Corrections list

**Focus Areas**:
- **Consistency**: Formatting uniform across sections?
- **Completeness**: All planned sections present?
- **Navigation**: TOC accurate? Hyperlinks work?
- **Headers/Footers**: Correct on all pages?
- **Page Numbers**: Sequential and correct?
- **Figures**: All referenced figures appear? Captions correct?
- **Cross-References**: "See Section X" references resolve?

**Personnel**: Proofreader (structural focus)
**Estimated Time**: 12 hours

### 6.4 Proofreading Pass 2: Copy Editing (Week 10, Days 1-2)

**Input**: Draft PDF (post-structural corrections)
**Process**: Detailed copy editing
**Output**: Copy edits list

**Focus Areas**:
- **Grammar & Syntax**: Sentence structure correct?
- **Spelling**: Consistent spelling (including naval terms)?
- **Punctuation**: Proper use throughout?
- **Typos**: Catch all typographical errors
- **Style Consistency**: Voice and tone consistent?
- **Readability**: Awkward phrasings flagged

**Personnel**: Copy editor
**Estimated Time**: 16 hours

### 6.5 Beta Reader Feedback (Week 9-10, Parallel)

**Input**: Draft PDF
**Process**: External beta reader review
**Output**: Beta reader feedback reports

**Beta Reader Recruitment** (5-7 readers):
- 2× Naval historians (credibility check)
- 2× Serious naval history enthusiasts (target audience)
- 1× Wargamer (wargaming section utility)
- 1× Librarian/archivist (index usability)
- 1× General reader (accessibility)

**Feedback Questions**:
1. **Overall**: Does Volume 0 fulfill its promise as master guide?
2. **Indices**: Are they comprehensive and useful? What's missing?
3. **Experimental Sections**: Which are most valuable? Least valuable?
4. **Errors**: Spot any factual errors or typos?
5. **Accessibility**: Is it approachable for target audience?
6. **Improvements**: What would make it better?

**Timeline**: Allow 1 week for beta reading, 3 days for feedback compilation

**Personnel**: Project manager (coordinate) + lead editor (synthesize feedback)
**Estimated Time**: 8 hours (coordination + synthesis)

### 6.6 Final Corrections & Revisions (Week 10, Days 3-4)

**Input**: All QA reports (validation, spot check, proofreading, beta feedback)
**Process**: Implement corrections
**Output**: Revised LaTeX files and PDF

**Correction Priority**:
1. **Critical Errors** (must fix): Factual errors, broken links, invalid page references
2. **High Priority** (should fix): Typos, formatting issues, missing cross-references
3. **Medium Priority** (nice to fix): Style inconsistencies, minor awkward phrasings
4. **Low Priority** (consider): Suggestions for future editions

**Recompile After Corrections**: Generate final candidate PDF

**Personnel**: Book designer + lead editor
**Estimated Time**: 12 hours

### 6.7 Final PDF/X-1a Compliance Check (Week 10, Day 5)

**Input**: Final candidate PDF
**Process**: Professional PDF/X-1a validation
**Output**: Compliant PDF ready for LSI upload

**Validation Tools**:
- Adobe Acrobat Pro (Preflight: PDF/X-1a profile)
- LSI's own validation tool (if available online)

**PDF/X-1a Requirements**:
- All colors CMYK (no RGB)
- All fonts embedded
- No transparency (flatten if present)
- Images 300+ DPI
- Trim box defined (8.5×11")
- No layers
- Compliant ICC color profile

**Fixes If Non-Compliant**:
- Convert RGB images to CMYK
- Re-embed fonts
- Flatten transparency layers
- Resample low-resolution images

**Final Output**: `nimitz_volume_0_FINAL_INTERIOR.pdf`

**Personnel**: Book designer (PDF expert)
**Estimated Time**: 4 hours

**Phase 6 Total Time**: 74 hours
**Phase 6 Deliverables**:
- Validation report (all tests passed)
- Spot check report (error rate <5%)
- Proofread and corrected PDF
- Beta reader feedback synthesis
- PDF/X-1a compliant interior PDF

---

## Phase 7: Production & Publication (Week 10+)

### Objective
Prepare all final files for Lightning Source International (LSI) upload and publication.

### 7.1 LSI Metadata Preparation (Week 10, Day 5)

**Input**: Book metadata, finalized ISBN
**Process**: Generate LSI CSV and title setup
**Output**: LSI metadata submission

**LSI Title Setup Requirements**:
- **ISBN-13**: Obtain from ISBN block (Nimble Books LLC)
- **Title & Subtitle**: Exact as on cover
- **Trim Size**: 8.5×11" (Hardcover Casebound)
- **Binding**: Hardcover (color interior)
- **Page Count**: Final count from PDF (e.g., 152 pages)
- **Interior Color**: Color
- **Paper Type**: 50# White
- **Lamination**: Matte
- **Spine Width**: Auto-calculated by LSI based on page count
- **Price**: $34.99 (as planned)
- **BISAC Codes**:
  - HIS027150 (History / Military / Naval)
  - HIS027000 (History / Military / World War II)
  - HIS036060 (History / United States / 20th Century)
- **Keywords**: Admiral Nimitz, Pacific War, WWII, Naval History, Command Summary, CINCPAC, Reference Guide

**Process**: Use LSI web interface or generate CSV via `generate_lsi_csv.py` (existing tool)

**Personnel**: Publisher/production manager
**Estimated Time**: 2 hours

### 7.2 Cover File Finalization (Week 10, Day 5)

**Input**: Cover PDF from Phase 5.6
**Process**: Adjust for exact spine width, validate specs
**Output**: `nimitz_volume_0_FINAL_COVER.pdf`

**LSI Cover Specs** (Hardcover 8.5×11"):
- **Spine Width**: Calculate using LSI calculator (e.g., 152 pages × 0.002252" = 0.342")
- **Total Width**: (8.5 × 2) + 0.342 + (0.125 × 2) = 17.592"
- **Height**: 11 + (0.125 × 2) = 11.25"
- **Bleed**: 0.125" all sides (extends beyond trim)
- **Safe Area**: 0.25" inside trim (keep text/logos within)
- **Barcode Placement**: Lower right back cover, in safe area

**Validation**: Use LSI's cover template (download for exact specs)

**Personnel**: Book designer
**Estimated Time**: 2 hours

### 7.3 Final File Upload to LSI (Week 11, Day 1)

**Input**: Final interior PDF, final cover PDF, metadata
**Process**: LSI web portal upload
**Output**: Title submitted for review

**Upload Process**:
1. Log in to LSI Publisher Portal
2. Create new title (use ISBN)
3. Enter all metadata
4. Upload interior PDF
5. Upload cover PDF
6. Submit for automated review
7. Wait for approval (typically 1-2 business days)

**Automated Review Checks**:
- File integrity (PDFs not corrupted)
- Page count matches metadata
- Cover dimensions correct
- Spine width matches page count
- PDF/X-1a compliance

**If Review Fails**: Fix issues and re-upload

**Personnel**: Publisher/production manager
**Estimated Time**: 2 hours (upload) + 1-2 days (wait for review)

### 7.4 Order Proof Copies (Week 11, Day 2+)

**Input**: LSI-approved title
**Process**: Order physical proof copies
**Output**: 2-3 printed proofs for final inspection

**Proof Order**:
- Order 2-3 copies via LSI
- Turnaround: 7-10 business days (shipping to US)
- Cost: ~$20-30 per proof copy

**Proof Inspection** (upon receipt):
- **Cover**: Colors accurate? No printing defects? Spine aligned?
- **Binding**: Solid? Pages secure?
- **Interior**: Print quality good? No smudging, missing pages?
- **Overall**: Does it meet quality standards?

**If Issues Found**:
- Minor (acceptable): Approve for distribution
- Major (unacceptable): Fix files and re-upload (restart from 7.3)

**Personnel**: Publisher + lead editor
**Estimated Time**: 1 hour (order) + 30 min (inspection per copy)

### 7.5 Approve for Distribution (Week 11-12)

**Input**: Approved proof copies
**Process**: Activate title for distribution in LSI portal
**Output**: Volume 0 live and available for order

**Distribution Channels**:
- **Lightning Source**: Direct orders (libraries, bookstores)
- **Ingram**: Distribution to wholesale and retail
- **Amazon**: Listed automatically via Ingram
- **Nimble Books Direct**: Website sales

**Metadata Propagation**: Allow 2-4 weeks for full propagation to all channels (Amazon, libraries, etc.)

**Personnel**: Publisher/production manager
**Estimated Time**: 1 hour

### 7.6 Create Digital Assets (Week 11-12, Parallel)

**Input**: Final PDF, cover images
**Process**: Generate marketing assets
**Output**: Website listings, social media graphics, email announcements

**Assets to Create**:
- **Website Listing**: Product page on nimblebooks.com
  - Cover image (high-res)
  - Description (from back cover + expanded)
  - Sample pages (TOC, index sample)
  - "Buy Now" links (Amazon, direct)
- **Social Media Graphics**:
  - Announcement graphics (1080×1080 for Instagram)
  - Cover reveal posts
  - Sample index page images
- **Email Announcement**: Newsletter to mailing list
  - Launch announcement
  - "Master guide to 4,023 pages" pitch
  - Bundle offer (Volume 0 + Volumes 1-8 set)

**Personnel**: Marketing/web designer
**Estimated Time**: 8 hours

**Phase 7 Total Time**: ~15 hours (plus waiting time for LSI review and proof shipping)
**Phase 7 Deliverables**:
- LSI title setup (metadata live)
- Final interior PDF uploaded
- Final cover PDF uploaded
- Proof copies approved
- Title activated for distribution
- Marketing assets published

---

## AI Generation Playbook

### Overview

Volume 0 uses AI strategically for tasks that benefit from scale, pattern recognition, and structured data extraction. Human expertise remains central for curation, verification, and historical accuracy.

### AI Usage Matrix

| Task | Model | Why This Model | Cost per Task | Human Oversight |
|------|-------|----------------|---------------|-----------------|
| **Entity Extraction** (persons, places, ships, orgs) | Gemini Flash 2.0 | Ultra-low cost, good accuracy for structured extraction, 1M token context | $5-10 total | Heavy (verification) |
| **Data Extraction** (fleet strength, operations) | Gemini Flash 2.0 | Same as above | $10-15 | Heavy (validation) |
| **Context Writing** (passage contexts) | Claude 3.5 Sonnet | Superior writing quality, historical nuance | $15-25 | Medium (editing) |
| **Comparative Analysis** (communication styles, Midway memo) | Claude 3.5 Sonnet | Analytical depth, respectful tone | $20-30 | Medium (fact-checking) |
| **Glossary Terms** | Gemini Flash 2.0 | Bulk term extraction | $5 | Heavy (curation) |
| **Page Reference Compilation** (reading guides) | Gemini Flash 2.0 | Aggregate index references | $5 | Medium (sequencing) |

**Total Estimated AI Cost**: $60-100 (negligible compared to labor)

### Key Principles

1. **AI Assists, Humans Decide**: AI generates raw material, humans curate and verify
2. **Transparency**: Label AI-generated content clearly in published work
3. **Historical Accuracy First**: Any AI output that contradicts historical record is rejected
4. **Structured Outputs**: Use JSON schemas for entity extraction to ensure consistency
5. **Batch Processing**: Process OCR results in batches (100 pages) to stay within token limits
6. **Quality Thresholds**: Set confidence thresholds (>0.7) for AI extractions; flag low-confidence for review

### Prompt Templates

#### Template 1: Entity Extraction (Persons)

```
You are analyzing historical naval documents from WWII. Extract all person names mentioned in the following pages.

INSTRUCTIONS:
- Extract every person mentioned (military personnel, civilians, officials)
- Capture exact name as written (including rank/title if present)
- Determine affiliation (US Navy, Japanese Navy, civilian, etc.)
- Note page number
- Provide brief context (1 sentence: what they did or why mentioned)

OUTPUT FORMAT: JSON array with this structure:
[
  {
    "name": "Full name as written",
    "rank": "Rank or title if mentioned",
    "affiliation": "US Navy | Japanese Navy | US Army | Civilian | etc",
    "page": 123,
    "context": "Brief 1-sentence context"
  },
  ...
]

PAGES TO ANALYZE:
[Insert batch of OCR text]

IMPORTANT: Only extract names actually mentioned in the text. Do not infer or add information not present.
```

**Variations**: Adapt for places, ships, organizations by changing entity type and schema fields.

#### Template 2: Context Writing (Important Passages)

```
You are writing brief historical context for a selected passage from Admiral Nimitz's WWII command summaries.

PASSAGE:
[Quote the selected passage]

VOLUME & PAGE: [e.g., Volume 1, pages 456-478]

TASK: Write 2-3 sentences providing context for this passage. Include:
1. What was happening at this point in the war? (situation)
2. Why is this passage historically significant? (significance)
3. What happened next? (outcome, if known)

TONE: Scholarly but accessible. Write for serious naval history enthusiasts.

CONSTRAINTS:
- 2-3 sentences maximum
- Factually accurate (no speculation)
- Focused on providing context readers need to understand significance

OUTPUT:
[Your context here]
```

#### Template 3: Comparative Analysis (Communication Styles)

```
You are analyzing Admiral Nimitz's WWII naval dispatch communication style compared to modern decision-making formats.

NIMITZ DISPATCHES:
[Provide 2-3 example dispatches]

MODERN FORMATS TO COMPARE:
1. Amazon 6-pager (narrative decision memos)
2. Modern military decision brief (OPORD format)
3. Corporate memo standards

TASK: Write a 4-6 page comparative analysis covering:
1. Nimitz's Communication Style (1.5 pages)
   - Key characteristics (brevity, clarity, hierarchy of information, etc.)
   - Examples from provided dispatches
   - Why this style worked in his context (radio costs, time pressure, trust)

2. Modern Formats Overview (1 page)
   - Brief description of each format
   - Key characteristics of each

3. Comparative Analysis (1.5 pages)
   - What's similar across all formats? (universal principles)
   - What's different? (adaptations to medium and context)
   - Trade-offs (brevity vs completeness, speed vs shared understanding)

4. Universal Principles (1 page)
   - What can we learn about effective communication under uncertainty?
   - Principles that transcend era and medium

TONE: Intellectually engaging, respectful of historical practice. Do NOT claim modern methods are "better" — they serve different contexts.

CONSTRAINTS:
- Grounded in actual examples
- Historically accurate
- Analytical but accessible
- Respectful of Nimitz's proven effectiveness

OUTPUT: Markdown text, well-structured with headings
```

### Quality Control for AI Outputs

**For Entity Extraction**:
1. **Automated Validation**: Check for JSON validity, required fields present
2. **Sampling Verification**: Human checks 100 random extractions against source pages
3. **Deduplication**: AI-assisted (suggest potential duplicates) + human decision
4. **Error Rate Target**: <10% for raw extraction, <2% after human verification

**For Analytical Content**:
1. **Fact-Checking**: Naval historian verifies every factual claim
2. **Tone Review**: Editor ensures respectful, appropriate tone
3. **Completeness**: Check that analysis addresses all required points
4. **Revision Cycles**: Expect 1-2 revision rounds per AI-generated section

**For Context Writing**:
1. **Accuracy Check**: Verify dates, names, events against standard sources
2. **Clarity Test**: Does context genuinely help readers understand significance?
3. **Length Check**: Stay within 2-3 sentence limit
4. **Batch Processing**: Generate contexts for all 40 passages, then batch-review

---

## Scripts Specification

### Overview

Python scripts automate data extraction, processing, and assembly. All scripts follow consistent patterns and use the codexes-factory infrastructure.

### Script Development Standards

**Common Imports**:
```python
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from nimble_llm_caller import LLMContentGenerator
import fitz  # PyMuPDF for PDF operations
```

**Logging Setup**:
```python
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
```

**Error Handling**:
- Use try/except blocks for file I/O and API calls
- Log errors with context
- Fail gracefully with informative messages

**Configuration**:
- Use JSON config files for model selection, paths, parameters
- Command-line arguments for input/output paths
- Environment variables for API keys (via .env)

### Script Inventory

#### 1. `scripts/validate_ocr_data.py`

**Purpose**: Validate OCR results integrity and coverage

**Inputs**:
- `nimitz_ocr_gemini/ocr_results.jsonl`

**Processing**:
```python
def validate_ocr_data(jsonl_path: Path) -> Dict[str, Any]:
    """
    Validate OCR results for completeness and integrity.

    Returns validation report with:
    - Total entries
    - Success rate
    - Average text length
    - Missing pages
    - Corrupted entries
    """
    entries = []
    errors = []

    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                entry = json.loads(line)
                entries.append(entry)
                # Validate required fields
                assert 'page_number' in entry
                assert 'success' in entry
                assert 'new_ocr_text' in entry
            except Exception as e:
                errors.append({'line': line_num, 'error': str(e)})

    report = {
        'total_entries': len(entries),
        'success_count': sum(1 for e in entries if e['success']),
        'success_rate': sum(1 for e in entries if e['success']) / len(entries),
        'errors': errors,
        'avg_text_length': sum(len(e['new_ocr_text']) for e in entries) / len(entries)
    }

    return report
```

**Outputs**:
- `data/ocr_validation_report.json`
- Console summary

**Estimated Development Time**: 3 hours

#### 2. `scripts/extract_bookmarks.py`

**Purpose**: Extract PDF bookmarks to structured JSON

**Inputs**:
- Original PDF path

**Processing**:
```python
import fitz

def extract_bookmarks(pdf_path: Path) -> List[Dict]:
    """Extract bookmarks from PDF with volume mapping."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()  # Returns [(level, title, page), ...]

    bookmarks = []
    for level, title, page in toc:
        volume = determine_volume_from_page(page)
        bookmarks.append({
            'level': level,
            'title': title,
            'page_pdf': page,  # PDF page number (1-indexed)
            'page_graybook': page,  # Graybook page number
            'volume': volume
        })

    return bookmarks

def determine_volume_from_page(page: int) -> int:
    """Map PDF page to volume number."""
    # Volume 1: pages 1-861
    if page <= 861:
        return 1
    # Volume 2: pages 862-1262
    elif page <= 1262:
        return 2
    # ... etc for all 8 volumes
```

**Outputs**:
- `data/bookmarks.json`

**Estimated Development Time**: 2 hours

#### 3. `scripts/extract_persons.py`

**Purpose**: Extract person entities from OCR text using AI

**Inputs**:
- `ocr_results.jsonl`
- Config: model, batch size, output path

**Processing**:
```python
from nimble_llm_caller import LLMContentGenerator

def extract_persons(jsonl_path: Path, batch_size: int = 100) -> List[Dict]:
    """Extract person entities using AI in batches."""

    generator = LLMContentGenerator(
        default_model="gemini/gemini-2.0-flash-exp"
    )

    # Load OCR results
    ocr_entries = load_jsonl(jsonl_path)

    all_persons = []

    for i in range(0, len(ocr_entries), batch_size):
        batch = ocr_entries[i:i+batch_size]
        batch_text = "\n\n---PAGE BREAK---\n\n".join(
            f"Page {e['page_number']}: {e['new_ocr_text']}"
            for e in batch
        )

        # Build prompt (use template from playbook)
        prompt = build_person_extraction_prompt(batch_text)

        # Call AI with structured output
        response = generator.generate(
            prompt=prompt,
            response_format=ResponseFormat.JSON,
            json_schema=PERSON_SCHEMA  # Define JSON schema
        )

        # Parse response
        persons = json.loads(response.content)
        all_persons.extend(persons)

        logger.info(f"Extracted {len(persons)} persons from batch {i//batch_size + 1}")

    return all_persons
```

**Outputs**:
- `data/extracted_entities/persons_raw.json`
- Progress log

**Estimated Development Time**: 6 hours

#### 4-6. `scripts/extract_places.py`, `extract_ships.py`, `extract_organizations.py`

**Purpose**: Extract other entity types (same pattern as persons)

**Processing**: Similar to `extract_persons.py`, with entity-specific prompts and schemas

**Outputs**:
- `data/extracted_entities/places_raw.json`
- `data/extracted_entities/ships_raw.json`
- `data/extracted_entities/organizations_raw.json`

**Estimated Development Time**: 5 hours each (15 hours total)

#### 7. `scripts/extract_viz_data.py`

**Purpose**: Extract data for visualizations (fleet strength, operations, etc.)

**Inputs**:
- `ocr_results.jsonl`
- Known operation list (manual curated)

**Processing**:
```python
def extract_fleet_strength(ocr_entries: List[Dict]) -> pd.DataFrame:
    """Extract fleet strength data points."""

    # Prompt AI to find fleet composition reports
    prompt = """
    Search these pages for mentions of fleet strength, ship counts, or
    operational status reports. Extract:
    - Date
    - Ship type (carrier, battleship, cruiser, destroyer, submarine)
    - Count (operational)
    - Count (damaged/repairing if mentioned)

    Return as JSON array.
    """

    # Process in batches, extract, aggregate
    # Return as pandas DataFrame for easy CSV export
```

**Outputs**:
- `data/visualizations/fleet_strength.csv`
- `data/visualizations/operations.csv`
- `data/visualizations/locations.csv`

**Estimated Development Time**: 12 hours

#### 8. `scripts/build_person_index.py`

**Purpose**: Transform raw person extractions into verified index

**Inputs**:
- `data/extracted_entities/persons_raw.json`

**Processing**:
```python
def build_person_index(raw_persons: List[Dict]) -> Dict[str, Dict]:
    """
    Build verified person index with deduplication and enhancement.

    Steps:
    1. Load raw extractions
    2. Deduplicate (AI-assisted suggestions + human review)
    3. Merge page references
    4. Add cross-references
    5. Format for LaTeX output
    """

    # Deduplication
    deduplicated = deduplicate_persons(raw_persons)

    # Enhance with cross-references
    enhanced = add_cross_references(deduplicated)

    # Format page references
    formatted = format_page_references(enhanced)

    return formatted

def deduplicate_persons(persons: List[Dict]) -> List[Dict]:
    """
    Deduplicate person entries.

    Strategy:
    - AI suggests potential duplicates based on name similarity
    - Human reviews and merges
    - Interactive process with confirmation
    """
    # AI-powered similarity detection
    duplicates = find_potential_duplicates_ai(persons)

    # Interactive review
    for dup_group in duplicates:
        print(f"Potential duplicates:")
        for p in dup_group:
            print(f"  - {p['name']} ({p['rank']}) on pages {p['pages']}")

        decision = input("Merge? (y/n/skip): ")
        if decision == 'y':
            merged = merge_persons(dup_group)
            # Update persons list

    return persons
```

**Outputs**:
- `data/indices/persons_verified.json`
- `content/index_persons.tex`

**Estimated Development Time**: 10 hours (including interactive process)

#### 9-11. `scripts/build_place_index.py`, `build_ship_index.py`, `build_organization_index.py`

**Purpose**: Build other indices (same pattern)

**Processing**: Similar to `build_person_index.py` with entity-specific logic

**Outputs**:
- Verified JSON files
- LaTeX index files

**Estimated Development Time**: 8 hours each (24 hours total)

#### 12. `scripts/build_glossary.py`

**Purpose**: Generate glossary from extracted terms + manual additions

**Inputs**:
- OCR text (for term extraction)
- Manual glossary entries (curated)

**Processing**:
```python
def build_glossary() -> List[Dict]:
    """Build glossary combining AI extraction and manual curation."""

    # AI extracts abbreviations and technical terms
    extracted_terms = extract_terms_ai(ocr_text)

    # Load manual additions (from naval glossaries)
    manual_terms = load_manual_glossary()

    # Merge and deduplicate
    all_terms = merge_terms(extracted_terms, manual_terms)

    # Human reviews and edits definitions
    reviewed_terms = interactive_review(all_terms)

    return reviewed_terms
```

**Outputs**:
- `content/glossary.tex`

**Estimated Development Time**: 8 hours

#### 13. `scripts/generate_visualizations.py`

**Purpose**: Create data visualization charts from extracted data

**Inputs**:
- `data/visualizations/*.csv`

**Processing**:
```python
import matplotlib.pyplot as plt
import seaborn as sns

def generate_fleet_strength_chart(df: pd.DataFrame, output_path: Path):
    """Generate fleet strength over time line chart."""

    plt.figure(figsize=(12, 6))

    for ship_type in df['ship_type'].unique():
        data = df[df['ship_type'] == ship_type]
        plt.plot(data['date'], data['count'], label=ship_type, marker='o')

    plt.xlabel('Date')
    plt.ylabel('Number of Ships (Operational)')
    plt.title('US Pacific Fleet Strength by Ship Type, 1941-1945')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Annotate major events
    plt.axvline(x='1941-12-07', color='red', linestyle='--', alpha=0.5)
    plt.text('1941-12-07', max_y, 'Pearl Harbor', rotation=90)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
```

**Outputs**:
- `content/visualizations/*.pdf` (for LaTeX inclusion)

**Estimated Development Time**: 12 hours

#### 14. `scripts/format_toc.py`

**Purpose**: Format bookmarks into LaTeX table of contents

**Inputs**:
- `data/bookmarks.json`

**Processing**:
```python
def format_toc(bookmarks: List[Dict]) -> str:
    """Format bookmarks as LaTeX longtable."""

    latex = []
    latex.append(r"\section*{Complete Table of Contents: Volumes 1-8}")
    latex.append(r"\begin{longtable}{p{0.12\textwidth} p{0.68\textwidth} p{0.15\textwidth}}")
    latex.append(r"\toprule")
    latex.append(r"Date & Section & Page \\")
    latex.append(r"\midrule")

    current_volume = None
    for bm in bookmarks:
        if bm['volume'] != current_volume:
            # New volume header
            latex.append(format_volume_header(bm['volume']))
            current_volume = bm['volume']

        # Format entry based on level (indent sub-entries)
        entry = format_bookmark_entry(bm)
        latex.append(entry)

    latex.append(r"\bottomrule")
    latex.append(r"\end{longtable}")

    return "\n".join(latex)
```

**Outputs**:
- `content/complete_toc.tex`

**Estimated Development Time**: 4 hours

#### 15. `scripts/assemble_volume_0.py`

**Purpose**: Assemble all content into master LaTeX document

**Inputs**:
- `templates/nimitz_volume_0_template.tex`
- All `content/*.tex` files

**Processing**:
```python
from jinja2 import Environment, FileSystemLoader

def assemble_volume_0(template_path: Path, content_dir: Path, output_path: Path):
    """Assemble all content into master LaTeX document."""

    # Load Jinja2 template
    env = Environment(loader=FileSystemLoader(template_path.parent))
    template = env.get_template(template_path.name)

    # Load all content sections
    content = {
        'publishers_note': load_tex(content_dir / 'publishers_note.tex'),
        'about_edition': load_tex(content_dir / 'about_edition.tex'),
        'methods_note': load_tex(content_dir / 'methods_note.tex'),
        'complete_toc': load_tex(content_dir / 'complete_toc.tex'),
        'index_intro': load_tex(content_dir / 'index_intro.tex'),
        'index_persons': load_tex(content_dir / 'index_persons.tex'),
        # ... all other sections
    }

    # Metadata
    metadata = {
        'title': 'Command Summary of Fleet Admiral Chester W. Nimitz, USN',
        'volume_number': 0,
        'subtitle': 'Master Guide and Analytical Companion',
        'isbn': 'TBD',  # From LSI assignment
        # ... other metadata
    }

    # Render template
    rendered = template.render(**content, **metadata)

    # Write to output
    output_path.write_text(rendered, encoding='utf-8')
    logger.info(f"Assembled master LaTeX to {output_path}")
```

**Outputs**:
- `build/nimitz_volume_0_master.tex`

**Estimated Development Time**: 6 hours

#### 16. `scripts/validate_volume_0.py`

**Purpose**: Automated validation suite (as described in Phase 6.1)

**Processing**: Implement all automated tests (index validation, cross-references, PDF checks)

**Outputs**:
- `validation_report.json`
- Console output with pass/fail status

**Estimated Development Time**: 8 hours

### Scripts Summary

**Total Scripts**: 16 major scripts
**Total Development Time**: ~125 hours
**Primary Developer**: Data specialist / Python developer
**Support**: Naval historian (for interactive curation scripts)

---

## Template Requirements

### LaTeX Template Structure

**File**: `templates/nimitz_volume_0_template.tex`

### Design Specifications

**Page Geometry**:
- Trim size: 8.5×11"
- Margins: 1" top/bottom, 0.75" inside/outside
- Header: 0.5" from top edge
- Footer: 0.5" from bottom edge

**Typography**:
- Body text: Adobe Caslon Pro, 11pt, 13pt leading
- Headers: Helvetica Neue Bold, 14-18pt
- Index text: Helvetica Neue, 9pt (for density)
- Captions: Italics, 10pt

**Front Matter**:
- Title page: Centered, hierarchical typography
- Copyright page: Small type, flush left
- Table of Contents (Volume 0): Standard TOC with dots

**Part I: Reference Materials**:
- Standard body text formatting
- Section headings: Chapter-level styling
- Subsection headings: Section-level styling

**Part II: Indices**:
- **Critical**: Two-column layout (`multicol` package)
- Sans-serif font for readability (Helvetica Neue 9pt)
- Hanging indent for multi-line entries
- Bold for main entry, roman for sub-entries
- Page references: Light weight, possibly small caps

**Index Entry Format Example**:
```latex
\noindent
\textbf{Nimitz, Chester W., ADM}\\
\hspace*{1em}Appointment as CINCPAC: 1:1\\
\hspace*{1em}Pearl Harbor aftermath: 1:15-45\\
\hspace*{1em}Midway decision: 1:445-478\\
\hspace*{1em}\textit{See also:} CINCPAC\\
```

**Part III: Experimental Sections**:
- Standard body text
- Figure placement: `[h]` (here) or `[t]` (top)
- Figure captions: Below figures, 10pt italics
- Data visualization figures: Full width or 0.9\textwidth

**Appendices**:
- Standard formatting
- Smaller section headings

**Headers/Footers**:
- Even pages (left): Page number (outer), "Volume 0: Master Guide" (inner)
- Odd pages (right): Section name (inner), Page number (outer)
- Footer: Small centered text "Warships & Navies"

### Jinja2 Variables

Template uses Jinja2 for dynamic content insertion:

```latex
% Title page
{\Huge\headingfont {{ TITLE }}}
{\LARGE\headingfont Volume {{ VOLUME_NUMBER }}}
{\large {{ SUBTITLE }}}

% Copyright page
ISBN: {{ ISBN }}

% Main content insertion
{{ PART_I_CONTENT }}
{{ PART_II_CONTENT }}
{{ PART_III_CONTENT }}
{{ APPENDICES }}
```

### LaTeX Packages Required

```latex
\usepackage[paperwidth=8.5in, paperheight=11in, margin=1in]{geometry}
\usepackage{fontspec}  % XeLaTeX/LuaLaTeX fonts
\usepackage{multicol}  % Two-column indices
\usepackage{longtable}  % Multi-page tables (for TOC)
\usepackage{graphicx}  % Figures
\usepackage{hyperref}  % Hyperlinks and bookmarks
\usepackage{fancyhdr}  % Custom headers/footers
\usepackage{titlesec}  % Section formatting
\usepackage{tocloft}  % TOC formatting
\usepackage{xcolor}  % Color (for subtle highlights)
```

### Compilation Requirements

**Compiler**: LuaLaTeX (for fontspec and better Unicode support)

**Compilation Sequence**:
```bash
lualatex nimitz_volume_0_master.tex
lualatex nimitz_volume_0_master.tex  # Second pass for cross-refs
```

**Font Installation**: Ensure Adobe Caslon Pro and Helvetica Neue installed on system

---

## Quality Assurance Plan

### Automated Checks

**Tool**: `scripts/validate_volume_0.py` (Phase 6.1)

**Checks Performed**:
1. **Index Validation**: All page references within valid ranges
2. **Cross-Reference Validation**: All "See also" entries exist
3. **LaTeX Compilation**: Clean build with no errors
4. **PDF/X-1a Pre-Check**: Color space, fonts, images
5. **Hyperlink Validation**: Internal links resolve

**Pass Criteria**: Zero errors, minor warnings acceptable

**Frequency**: Run after every major content change

### Human Review Checklists

#### Checklist 1: Index Quality (Phase 6.2)

**Sampling**: 100 random entries (25 per index type)

- [ ] Person/place/ship appears on cited page
- [ ] Context accurate (correct battle, operation, etc.)
- [ ] Rank/hull number correct (for persons/ships)
- [ ] No obvious omissions (major figures/ships present)
- [ ] Cross-references helpful and accurate
- [ ] Page ranges appropriate (not too broad)

**Error Rate Threshold**: <5% errors

**If Failed**: Revise index creation process, increase human verification

#### Checklist 2: Historical Accuracy (Phase 6.2)

**Scope**: All experimental sections + Most Important Passages

- [ ] Dates correct (cross-reference with Morison, Potter)
- [ ] Ship names and types correct
- [ ] Command relationships accurate
- [ ] Battle outcomes accurate
- [ ] No anachronistic language or concepts
- [ ] Quotations verbatim (if included)
- [ ] Context summaries accurate

**Sources for Verification**:
- Morison, *History of United States Naval Operations in World War II*
- Potter, *Nimitz*
- Naval History and Heritage Command online resources

**If Failed**: Revise content, add additional fact-checking pass

#### Checklist 3: Tone and Style (Phase 6.4)

**Scope**: All written content

- [ ] Consistent voice (scholarly but accessible)
- [ ] Respectful of historical figures and events
- [ ] No sensationalism or hyperbole
- [ ] Clear and concise prose
- [ ] Appropriate vocabulary for target audience (serious enthusiasts)
- [ ] AI-generated content edited for natural flow
- [ ] No jarring transitions between sections

**Reviewer**: Copy editor + lead editor

**If Failed**: Revise for consistency, re-edit AI content

#### Checklist 4: Completeness (Phase 6.3)

**Scope**: Entire volume

- [ ] All planned sections present (cross-check with outline)
- [ ] Table of Contents complete (all 297 bookmarks)
- [ ] All indices complete (persons, places, ships, orgs, glossary)
- [ ] All experimental sections complete (7 sections)
- [ ] All appendices present
- [ ] All figures present and referenced
- [ ] Page count within target range (145-155 pages)

**If Failed**: Add missing content, re-assemble

#### Checklist 5: Production Readiness (Phase 6.7)

**Scope**: Final PDF

- [ ] PDF/X-1a compliant (Adobe Preflight passes)
- [ ] All fonts embedded
- [ ] All colors CMYK (no RGB)
- [ ] Images 300+ DPI
- [ ] No transparency layers
- [ ] Trim box defined correctly (8.5×11")
- [ ] Page count matches metadata
- [ ] Hyperlinks work (internal TOC links)
- [ ] Bookmarks present (PDF navigation panel)

**Tool**: Adobe Acrobat Pro (Preflight)

**If Failed**: Fix issues and recompile

### Beta Reader Feedback Process

**Recruitment** (Week 9):
- Post on naval history forums (Warships1, Naval History & Heritage Command)
- Reach out to naval history societies
- Contact wargaming communities (for wargaming section feedback)
- Invite librarians/archivists (for index usability)

**Beta Reader Packet**:
- Draft PDF of Volume 0
- Feedback form (Google Form or similar)
- Timeline: 1 week for reading + feedback

**Feedback Questions**:
1. Overall impression (1-5 stars + comments)
2. Index usability: Could you find what you were looking for?
3. Most valuable section: Which part did you find most useful?
4. Least valuable section: What could be cut or improved?
5. Errors spotted: Any factual errors, typos, or issues?
6. Missing content: What would make this better?
7. Target audience fit: Does this serve serious enthusiasts well?

**Synthesis** (Week 10):
- Aggregate feedback
- Identify common themes
- Prioritize actionable improvements
- Implement critical fixes
- Note suggestions for future editions

---

## Production Timeline (Gantt-Style)

### Week 1: Foundation

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 0 | Project setup, directory structure | 4 | None |
| Tue | 0 | Validate OCR, extract bookmarks | 5 | OCR results exist |
| Wed | 1 | Entity extraction: Persons (start) | 8 | OCR validated |
| Thu | 1 | Entity extraction: Persons (finish) | 8 | Wed |
| Fri | 1 | Entity extraction: Places | 8 | OCR validated |

**Deliverables**: Validated OCR, bookmarks JSON, persons and places raw JSON

### Week 2: Data Extraction + Reference Materials

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 1 | Entity extraction: Ships | 8 | OCR validated |
| Tue | 1 | Entity extraction: Organizations | 8 | OCR validated |
| Wed | 1 | Visualization data extraction (start) | 8 | OCR validated |
| Thu | 1 | Visualization data extraction (finish) | 8 | Wed |
| Fri | 2 | Complete TOC, Publisher's Note | 10 | Bookmarks JSON |

**Deliverables**: All entity JSONs, viz data CSVs, TOC and Publisher's Note drafted

### Week 3: Reference Materials + Indices Start

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 2 | About Edition, Note on Methods (start) | 8 | None |
| Tue | 2 | Note on Methods (finish) | 4 | Mon |
| Wed | 3 | Index: Persons verification (start) | 8 | Persons raw JSON |
| Thu | 3 | Index: Persons verification (continue) | 8 | Wed |
| Fri | 3 | Index: Persons verification (finish) | 8 | Thu |

**Deliverables**: All reference materials drafted, Persons index 50% complete

### Week 4: Indices (Intensive Week)

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 3 | Index: Persons finalization | 8 | Week 3 |
| Tue | 3 | Index: Places verification | 8 | Places raw JSON |
| Wed | 3 | Index: Ships verification (start) | 8 | Ships raw JSON |
| Thu | 3 | Index: Ships verification (finish) | 8 | Wed |
| Fri | 3 | Index: Organizations, Glossary (start) | 8 | Orgs raw JSON |

**Deliverables**: Persons, Places, Ships indices complete; Organizations 50% complete

### Week 5: Indices Finish + Experimental Sections Start

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 3 | Glossary, Organizations finish | 8 | Week 4 |
| Tue | 4 | Data visualizations generation | 8 | Viz data CSVs |
| Wed | 4 | Most Important Passages curation (start) | 8 | Indices complete |
| Thu | 4 | Most Important Passages curation (continue) | 8 | Wed |
| Fri | 4 | Most Important Passages curation (finish) | 8 | Thu |

**Deliverables**: All indices complete (76-94 pages), visualizations done, passages selected

### Week 6: Experimental Sections Finish

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 4 | Reading Guides, Communication Styles | 12 | Indices |
| Tue | 4 | Midway 6-Pager | 8 | None |
| Wed | 4 | Wargaming scenarios (start) | 8 | OCR, indices |
| Thu | 4 | Wargaming scenarios (finish) | 8 | Wed |
| Fri | 4 | Metadata of War | 8 | Archival research |

**Deliverables**: All experimental sections complete (46-60 pages)

### Week 7: Assembly

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 5 | Appendices creation | 8 | None |
| Tue | 5 | LaTeX template creation | 8 | Design specs |
| Wed | 5 | LaTeX template refinement | 4 | Tue |
| Thu | 5 | Content assembly | 8 | All content files |
| Fri | 5 | Initial compilation, debugging | 8 | Thu |

**Deliverables**: Assembled master LaTeX, draft PDF (first compile)

### Week 8: Assembly + Cover

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 5 | Page count adjustment | 4 | Draft PDF |
| Tue | 5 | Cover generation (start) | 4 | Metadata |
| Wed | 5 | Cover generation (finish) | 4 | Tue |
| Thu | 5 | Final clean compilation | 4 | Adjusted content |
| Fri | 5 | — | — | — |

**Deliverables**: Final draft PDF (~150 pages), cover PDF

### Week 9: QA (Intensive)

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 6 | Automated validation | 6 | Draft PDF |
| Tue | 6 | Content accuracy spot check (start) | 8 | Draft PDF |
| Wed | 6 | Content accuracy spot check (finish) | 8 | Tue |
| Thu | 6 | Proofreading: Structural (start) | 6 | Draft PDF |
| Fri | 6 | Proofreading: Structural (finish) | 6 | Thu |

**Deliverables**: Validation report, spot check report, structural proofread complete

**Beta Readers**: Start reading (1-week turnaround)

### Week 10: QA Finish + Final Production

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 6 | Proofreading: Copy editing (start) | 8 | Week 9 |
| Tue | 6 | Proofreading: Copy editing (finish) | 8 | Mon |
| Wed | 6 | Final corrections & revisions | 8 | All QA reports |
| Thu | 6 | Final revisions continue | 4 | Wed |
| Fri | 6/7 | PDF/X-1a compliance check, LSI prep | 6 | Final PDF |

**Deliverables**: Final interior PDF (PDF/X-1a compliant), final cover PDF, LSI metadata

**Beta Reader Feedback**: Due end of week

### Week 11+: Publication

| Day | Phase | Tasks | Hours | Dependencies |
|-----|-------|-------|-------|--------------|
| Mon | 7 | Upload to LSI, wait for review | 2 | Final files |
| Tue-Fri | 7 | (Wait for LSI approval) | — | — |
| +7-10 days | 7 | Receive and inspect proofs | 1 | LSI approval |
| +1-2 days | 7 | Approve for distribution | 1 | Proofs OK |
| +2-4 weeks | — | Volume 0 live on Amazon, Ingram | — | Distribution activation |

**Deliverables**: Volume 0 published and available for order

---

## Resource Requirements

### Personnel

#### 1. Naval Historian / Subject Matter Expert

**Role**: Primary curator, historical verification, index validation

**Qualifications**:
- PhD or equivalent experience in WWII Pacific naval history
- Familiarity with Nimitz, CINCPAC operations
- Comfortable with primary source documents
- Detail-oriented

**Time Commitment**:
- Weeks 3-4: 40 hours/week (index verification)
- Week 5: 30 hours (passage curation)
- Week 6: 16 hours (reading guides, fact-checking)
- Week 9-10: 20 hours (accuracy checks, proofreading support)
- **Total: ~145 hours over 8 weeks**

**Suggested Rate**: $75/hour (academic rate)

**Total Cost**: ~$10,875

**Potential Candidates**:
- Retired naval officers with historical expertise
- Academic historians (adjunct, emeritus)
- Naval museum curators
- Naval War College faculty (part-time consulting)

#### 2. Data Specialist / Python Developer

**Role**: Script development, AI integration, data extraction

**Qualifications**:
- Strong Python programming (pandas, LLM APIs)
- Experience with nimble-llm-caller or similar LLM frameworks
- Data processing and automation
- LaTeX familiarity (bonus)

**Time Commitment**:
- Week 1: 20 hours (setup, validation scripts)
- Week 2: 20 hours (entity extraction scripts)
- Week 3: 16 hours (index building scripts, support)
- Week 5: 16 hours (visualization generation)
- Week 7: 12 hours (assembly scripts)
- Week 9: 6 hours (validation scripts)
- **Total: ~90 hours over 10 weeks**

**Suggested Rate**: $100/hour (developer rate)

**Total Cost**: ~$9,000

#### 3. Writer / Editor

**Role**: Original writing (front matter, appendices), AI content editing, proofreading

**Qualifications**:
- Strong writing skills (scholarly but accessible)
- Experience with historical or technical writing
- Editing AI-generated content
- Understanding of naval history (or ability to learn quickly)

**Time Commitment**:
- Week 2-3: 20 hours (front matter writing)
- Week 5-6: 20 hours (experimental section writing/editing)
- Week 7: 8 hours (appendices)
- Week 10: 16 hours (copy editing)
- **Total: ~64 hours over 6 weeks**

**Suggested Rate**: $65/hour (editor rate)

**Total Cost**: ~$4,160

#### 4. Book Designer / LaTeX Expert

**Role**: Template creation, layout, compilation, cover design

**Qualifications**:
- Expert in LaTeX (especially LuaLaTeX)
- Book design experience (academic or trade)
- Cover design skills (InDesign or LaTeX-based)
- PDF/X-1a compliance expertise

**Time Commitment**:
- Week 7: 24 hours (template creation, initial assembly)
- Week 8: 12 hours (cover design, adjustments)
- Week 9-10: 16 hours (QA support, corrections)
- **Total: ~52 hours over 4 weeks**

**Suggested Rate**: $75/hour (designer rate)

**Total Cost**: ~$3,900

#### 5. Wargaming Consultant (Optional but Recommended)

**Role**: Wargaming scenarios section (Phase 4.7)

**Qualifications**:
- Experienced wargamer (board or miniatures)
- Naval wargaming expertise (WWII Pacific)
- Historical knowledge (understands sources)
- Scenario design experience

**Time Commitment**:
- Week 6: 25 hours (scenario design, OOB compilation)
- **Total: ~25 hours in 1 week**

**Suggested Rate**: $75/hour (consultant rate)

**Total Cost**: ~$1,875

#### 6. Archival Researcher (Optional but Recommended)

**Role**: Metadata of War section (Phase 4.8)

**Qualifications**:
- Archival research experience
- Familiarity with NHHC or similar collections
- Document analysis skills

**Time Commitment**:
- Week 6: 15 hours (research and writing)
- **Total: ~15 hours in 1 week**

**Suggested Rate**: $65/hour (researcher rate)

**Total Cost**: ~$975

#### 7. Proofreader / Fact-Checker

**Role**: Dedicated proofreading and fact verification (Phase 6)

**Qualifications**:
- Professional proofreading experience
- Attention to detail
- Familiarity with academic/historical publishing

**Time Commitment**:
- Week 9-10: 28 hours (structural + copy editing)
- **Total: ~28 hours over 2 weeks**

**Suggested Rate**: $50/hour (proofreader rate)

**Total Cost**: ~$1,400

### Personnel Summary

| Role | Hours | Rate | Cost |
|------|-------|------|------|
| Naval Historian | 145 | $75 | $10,875 |
| Data Specialist | 90 | $100 | $9,000 |
| Writer/Editor | 64 | $65 | $4,160 |
| Book Designer | 52 | $75 | $3,900 |
| Wargaming Consultant | 25 | $75 | $1,875 |
| Archival Researcher | 15 | $65 | $975 |
| Proofreader | 28 | $50 | $1,400 |
| **TOTAL LABOR** | **419** | — | **$32,185** |

**Note**: Rates are market estimates for contractors. Adjust for in-house staff or geographic location.

### Compute Resources

**AI/LLM Costs**:
- Gemini Flash 2.0 (entity extraction, data extraction): ~$40
- Claude 3.5 Sonnet (context writing, analysis): ~$40
- Miscellaneous (testing, revisions): ~$20
- **Total AI Cost**: ~$100

**Hardware Requirements**:
- MacBook Pro or Linux workstation (LaTeX compilation)
- 16 GB RAM minimum (for large LaTeX compilations)
- 500 GB storage (intermediate files, PDFs)

**Software**:
- LuaLaTeX (free, part of TeX Live distribution)
- Python 3.12+ (free)
- Adobe Acrobat Pro (for PDF/X-1a validation, ~$20/month)
- Adobe InDesign (for cover design, ~$50/month or use LaTeX)

**Total Software Cost**: ~$70 (2 months)

### Data Storage & Version Control

**Git Repository**:
- GitHub private repo (free for Nimble Books account)
- Version control for all scripts, LaTeX, content files

**Cloud Storage**:
- Google Drive or Dropbox (for beta reader distribution)
- ~100 GB (multiple PDF drafts, proofs)

**Backup Strategy**:
- Daily backups to external drive
- Weekly cloud backups

**Total Storage Cost**: ~$10/month × 3 months = $30

### Total Budget

| Category | Cost |
|----------|------|
| **Labor** | $32,185 |
| **AI/LLM** | $100 |
| **Software** | $70 |
| **Storage** | $30 |
| **LSI Proof Copies** | $75 |
| **Contingency (10%)** | $3,246 |
| **TOTAL BUDGET** | **$35,706** |

**Reduced Budget Option** (if necessary):
- Skip wargaming consultant (scripted scenarios instead): -$1,875
- Skip archival researcher (general research only): -$975
- Reduce naval historian hours (spot checks only): -$3,000
- Reduced budget: **~$29,800**

---

## Risk Mitigation

### Risk Register

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| **OCR Quality Issues** | Medium | High | Validate OCR early (Week 1). If poor quality, budget for re-OCR or manual transcription of critical sections. |
| **Entity Extraction Accuracy** | Medium | Medium | Human verification required (built into plan). Spot checks catch errors before indices finalized. |
| **Timeline Slippage** | Medium | Medium | Buffer time in Weeks 9-10. Prioritize critical paths (indices must complete before experimental sections). |
| **Personnel Availability** | Low | High | Recruit personnel early (by Week 0). Have backup contacts for critical roles (historian, designer). |
| **Scope Creep** | Medium | Low | Stick to outline. Defer non-essential experiments to future editions. Use page count limits as hard constraint. |
| **Budget Overruns** | Low | Medium | Track hours weekly. Halt work if approaching budget limit. Use AI strategically to reduce manual labor. |
| **Beta Reader Feedback Negative** | Low | Medium | Recruit diverse beta readers early. Address critical feedback in revisions, note others for future editions. |
| **LSI Rejection (Technical)** | Low | High | Validate PDF/X-1a compliance before submission (Week 10). Use LSI's cover templates exactly. |
| **LaTeX Compilation Errors** | Medium | Low | Test template early (Week 7). Incremental compilation with frequent testing. Use stable LaTeX distribution (TeX Live 2024). |
| **Historical Inaccuracies** | Low | High | Naval historian reviews all factual content. Cross-reference with standard sources (Morison, Potter). Corrections welcome post-publication. |

### Critical Path Analysis

**Critical Path**: OCR Validation → Entity Extraction → Index Verification → Assembly → QA → Publication

**Dependencies**:
- **Indices depend on**: Entity extraction (Week 1-2)
- **Experimental sections depend on**: Indices complete (needed for passage curation, reading guides)
- **Assembly depends on**: All content complete (Week 7)
- **QA depends on**: Draft PDF (Week 8)
- **Publication depends on**: Final PDF (Week 10)

**Non-Critical Paths** (can run in parallel):
- Data visualizations (parallel to indices)
- Cover design (parallel to QA)
- Beta reader recruitment (Week 9, parallel to QA)

**Buffer Time**:
- Week 10 has flexibility (4-5 days for revisions)
- Week 11+ is waiting time (LSI review, proof shipping)

**If Timeline Slips**:
- Reduce experimental sections (cut 1-2 sections)
- Reduce index page count (tighten formatting)
- Extend timeline by 1-2 weeks (still feasible for November 2025 publication)

### Contingency Plans

#### If OCR Quality Is Poor (<90% Success Rate)

**Option A**: Re-OCR with Different Model
- Use Claude Opus (more expensive but higher accuracy)
- Cost: +$200-300
- Timeline: +1 week

**Option B**: Hybrid Approach
- Use existing OCR for indices (acceptable accuracy)
- Manually transcribe critical sections (Most Important Passages)
- Cost: +20 hours writer time (~$1,300)
- Timeline: No change

**Recommended**: Option B (more cost-effective)

#### If Naval Historian Unavailable

**Option A**: Recruit Alternative Expert
- Contact Naval War College, Naval Museum, or retired officers
- Budget extra time for onboarding (+1 week)

**Option B**: Outsource to Naval History Society
- Some organizations offer consulting/verification services
- May be slower but ensures quality

**Recommended**: Recruit backup historian in Week 0

#### If Budget Exceeded by 20%+

**Priority Cuts** (in order):
1. Skip wargaming consultant (DIY scenarios): -$1,875
2. Skip archival researcher (general metadata section): -$975
3. Reduce experimental sections from 7 to 5: -10 hours writer time (~$650)
4. Reduce Most Important Passages from 40 to 32: -8 hours historian time (~$600)

**Total Savings**: ~$4,100

**Last Resort**: Delay publication by 1-2 months, spread work over longer timeline to reduce weekly costs

#### If LSI Rejects Submission

**Common Rejection Reasons**:
- Cover dimensions wrong → Fix and resubmit (1 day)
- PDF not PDF/X-1a compliant → Convert and resubmit (1 day)
- Page count mismatch → Correct metadata (1 hour)

**Prevention**: Follow LSI specs exactly, validate with Preflight before submission

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Page Count** | 145-155 pages | Final PDF page count |
| **Index Completeness** | 6,000-9,000 entries | Count of index entries |
| **Index Accuracy** | >95% | Spot check validation (100 samples) |
| **Historical Accuracy** | 100% factual claims verified | Fact-checking against standard sources |
| **OCR Success Rate** | >95% | OCR validation report |
| **Beta Reader Rating** | >4.0/5.0 average | Beta reader feedback forms |
| **LaTeX Compilation** | 0 errors, <10 warnings | Compilation log |
| **PDF/X-1a Compliance** | Pass | Adobe Preflight report |
| **Timeline Adherence** | ±2 weeks of plan | Project tracking |
| **Budget Adherence** | ±10% of budget | Expense tracking |

### Qualitative Metrics

| Aspect | Success Criteria | Evaluation Method |
|--------|------------------|-------------------|
| **Utility** | Readers find indices genuinely useful for navigating 4,023 pages | Beta reader feedback, post-launch reviews |
| **Intellectual Value** | Experimental sections provide fresh insights, not just gimmicks | Beta reader feedback, peer reviews |
| **Historical Respect** | Tone is respectful, no sensationalism, accurately represents history | Naval historian approval, beta reader feedback |
| **Accessibility** | Target audience (serious enthusiasts) finds it approachable | Beta reader feedback (enthusiasm level) |
| **Production Quality** | Professional-grade book (typography, binding, printing) | Proof copy inspection, initial customer feedback |
| **Brand Alignment** | Embodies Warships & Navies / Jellicoe philosophy ("every document worth saving") | Editorial review, publisher approval |

### Definition of Done

**Volume 0 is ready for publication when**:

1. **Content Complete**:
   - All sections from outline present
   - All indices contain entries within target ranges
   - All experimental sections complete
   - All appendices present

2. **Quality Verified**:
   - Automated validation passes (0 errors)
   - Spot check accuracy >95%
   - Fact-checking complete (all claims verified)
   - Proofread twice (structural + copy editing)
   - Beta reader feedback addressed (critical issues fixed)

3. **Production Ready**:
   - Final PDF compiles cleanly (0 LaTeX errors)
   - PDF/X-1a compliant (Preflight passes)
   - Cover designed and validated (LSI specs)
   - Page count 145-155 pages
   - ISBNs assigned

4. **LSI Approved**:
   - Interior PDF uploaded and approved
   - Cover PDF uploaded and approved
   - Metadata complete and correct
   - Proof copies ordered and inspected

5. **Stakeholder Approval**:
   - Publisher (Nimble Books LLC) approves
   - Lead editor approves
   - Naval historian approves (historical accuracy)
   - Book designer approves (production quality)

**Final Gate**: Physical proof copy in hand, inspected, and approved. Activate for distribution.

---

## Appendix A: Entity Extraction JSON Schemas

### Person Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "page"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Full name as written in text"
    },
    "rank": {
      "type": "string",
      "description": "Military rank or civilian title"
    },
    "affiliation": {
      "type": "string",
      "enum": ["US Navy", "US Marine Corps", "US Army", "US Air Force",
               "Japanese Navy", "Japanese Army", "British Navy", "Australian Navy",
               "Civilian", "Other"]
    },
    "page": {
      "type": "integer",
      "description": "Page number where mentioned (0-4022)"
    },
    "context": {
      "type": "string",
      "description": "Brief context (1 sentence)"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Extraction confidence (0-1)"
    }
  }
}
```

### Place Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "page"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Location name as written"
    },
    "type": {
      "type": "string",
      "enum": ["island", "atoll", "base", "city", "port", "sea", "strait", "reef", "other"]
    },
    "region": {
      "type": "string",
      "description": "Geographic region (Solomons, Marianas, etc.)"
    },
    "page": {
      "type": "integer"
    },
    "context": {
      "type": "string",
      "description": "Battle, operation, or activity"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  }
}
```

### Ship Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "page"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Ship name (e.g., 'USS Enterprise')"
    },
    "hull_number": {
      "type": "string",
      "description": "Hull number if mentioned (e.g., 'CV-6')"
    },
    "navy": {
      "type": "string",
      "enum": ["US Navy", "Japanese Navy", "British Navy", "Australian Navy", "Other"]
    },
    "type": {
      "type": "string",
      "enum": ["carrier", "battleship", "cruiser", "destroyer", "submarine",
               "transport", "auxiliary", "other"]
    },
    "page": {
      "type": "integer"
    },
    "activity": {
      "type": "string",
      "description": "What ship was doing (battle, damage, etc.)"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  }
}
```

### Organization Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "page"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Organization name (e.g., 'Task Force 16')"
    },
    "type": {
      "type": "string",
      "enum": ["task_force", "fleet", "division", "squadron", "shore_command",
               "staff_section", "other"]
    },
    "commander": {
      "type": "string",
      "description": "Commanding officer if mentioned"
    },
    "page": {
      "type": "integer"
    },
    "context": {
      "type": "string",
      "description": "Formation, operation, or action"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  }
}
```

---

## Appendix B: LaTeX Template Snippets

### Index Entry Formatting Macro

```latex
% Custom command for index entries with hanging indent
\newcommand{\indexentry}[3]{%
  % #1: Main entry (person/place/ship name)
  % #2: Sub-entries (array of lines)
  % #3: Cross-references (optional)
  \noindent
  \textbf{#1}\\
  #2
  \ifthenelse{\equal{#3}{}}{}{%
    \hspace*{1em}\textit{See also:} #3\\
  }
  \vspace{0.5em}
}

% Usage example:
\indexentry{Nimitz, Chester W., ADM}{
  \hspace*{1em}Appointment as CINCPAC: 1:1\\
  \hspace*{1em}Pearl Harbor aftermath: 1:15-45\\
  \hspace*{1em}Midway decision: 1:445-478
}{CINCPAC, Commander in Chief Pacific}
```

### Two-Column Index Layout

```latex
% Index section with two-column layout
\section*{Index of Persons}
\begin{multicols}{2}
\small
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}

% Index entries here
\indexentry{Nimitz, Chester W., ADM}{...}{...}
\indexentry{Spruance, Raymond A., RADM}{...}{...}
% ... more entries

\end{multicols}
```

### Figure Inclusion for Data Visualizations

```latex
% Data visualization figure with caption
\begin{figure}[ht]
  \centering
  \includegraphics[width=0.9\textwidth]{visualizations/fleet_strength.pdf}
  \caption{US Pacific Fleet Strength by Ship Type, December 1941 to August 1945.
           Data extracted from CINCPAC command summaries. Notable events marked:
           Pearl Harbor (Dec 1941), Battle of Midway (Jun 1942), and peak strength (Dec 1944).}
  \label{fig:fleet_strength}
\end{figure}
```

### Header/Footer Configuration

```latex
% Custom headers and footers
\usepackage{fancyhdr}
\pagestyle{fancy}

% Clear default headers/footers
\fancyhf{}

% Even pages (left)
\fancyhead[LE]{\thepage}
\fancyhead[RE]{\small\textit{Volume 0: Master Guide}}

% Odd pages (right)
\fancyhead[LO]{\small\textit{\nouppercase{\leftmark}}}
\fancyhead[RO]{\thepage}

% Footer (both)
\fancyfoot[C]{\tiny Warships \& Navies}

% Header/footer rules
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
```

---

## Appendix C: Beta Reader Feedback Form Template

**Nimitz Graybook Volume 0 - Beta Reader Feedback**

Thank you for reviewing Volume 0! Your feedback is invaluable. Please complete this form after reading.

### About You
- Name (optional): _____________
- Background: [ ] Naval historian [ ] Enthusiast [ ] Wargamer [ ] Librarian [ ] General reader [ ] Other: _____
- Familiarity with WWII Pacific naval history: [ ] Expert [ ] Advanced [ ] Intermediate [ ] Beginner

### Overall Impression
1. Overall rating (1-5 stars): ☆☆☆☆☆
2. In one sentence, what is your impression of Volume 0?

### Usefulness & Utility
3. Did the indices help you find information? [ ] Yes, very helpful [ ] Somewhat helpful [ ] Not helpful
4. Which index did you use most? [ ] Persons [ ] Places [ ] Ships [ ] Organizations [ ] Glossary
5. What's missing from the indices?

### Experimental Sections
6. Which experimental section did you find MOST valuable?
   [ ] Data Visualizations
   [ ] Most Important Passages
   [ ] Reading Guides
   [ ] Communication Styles Analysis
   [ ] Midway as Amazon 6-Pager
   [ ] Wargaming Scenarios
   [ ] Metadata of War

7. Which section did you find LEAST valuable?

8. Should any sections be cut or expanded?

### Accuracy & Errors
9. Did you spot any factual errors? (Please list with page numbers)

10. Did you spot any typos or formatting issues? (Please list with page numbers)

### Accessibility & Tone
11. Is Volume 0 approachable for its target audience (serious enthusiasts)? [ ] Yes [ ] No
12. Is the tone appropriate (scholarly but accessible)? [ ] Yes [ ] Too academic [ ] Too casual

### Improvements
13. What would make Volume 0 better?

14. Would you recommend Volume 0 to other naval history enthusiasts? [ ] Yes [ ] No [ ] Maybe

15. Any other comments or suggestions?

**Submit to**: [beta-feedback@nimblebooks.com] by [DATE]

---

## Conclusion

This generation plan provides a complete, actionable roadmap to produce Nimitz Graybook Volume 0 from enhanced OCR data to publication-ready PDF in 10-12 weeks.

**Key Success Factors**:
1. **Quality Over Speed**: Indices are the core value proposition—do not rush human verification
2. **AI as Assistant, Not Replacement**: Use AI strategically for scale, but human expertise is essential
3. **Transparency**: Label AI-generated content, document methodology clearly
4. **Iterative Testing**: Compile frequently, catch issues early
5. **Beta Reader Feedback**: Incorporate real user perspectives before finalizing

**Next Steps**:
1. **Week 0**: Recruit personnel (naval historian, data specialist, designer)
2. **Week 0**: Set up project infrastructure (directories, Git repo, LLM config)
3. **Week 1**: Begin Phase 0 and 1 (foundation and data extraction)

Volume 0 represents a unique publishing experiment: combining essential reference utility (comprehensive indices) with intellectual exploration (analytical experiments). When executed with care, it will serve serious naval history enthusiasts for decades as the master guide to one of WWII's most important primary source collections.

**Production Ready**: November 2025

---

**Document prepared by**: Claude Code (Anthropic AI)
**For**: Nimble Books LLC, Warships & Navies Imprint
**Date**: October 26, 2025
**Status**: Complete generation plan ready for implementation
