# Batch Imprint Operations - Implementation Plan

## Overview
Add batch processing capabilities to Enhanced Imprint Creator and Ideation Dashboard for performing operations on collections of imprints from multiple directories.

## 1. Directory Structure & Data Sources

### Config Directories (JSON Files - High-Level Specs)
- `configs/imprints/` - Production imprint configurations
- `configs/imprints_draft/` - Draft imprint configurations
- `configs/imprints_staging/` - Staging/testing imprint configurations
- `configs/imprints_archive/` - Archived imprint configurations

### Imprint Directories (Directories with Pipeline Tools)
- `imprints/` - Production imprint directories with full pipeline setup
- `imprints_in_development/` - Development imprint directories

## 2. Feature Requirements

### 2.1 Path Selection UI Component
**Location**: Shared utility module for reuse across pages

**Inputs**:
- Dropdown selector with predefined paths
- Optional manual path entry field
- Multi-select capability for batch operations

**Functionality**:
```python
def render_path_selector(
    allow_multi_select: bool = True,
    allow_custom_path: bool = True,
    filter_type: str = "all"  # "configs", "directories", "all"
) -> List[Path]:
    """
    Renders path selection UI and returns selected paths.

    Returns:
        List of Path objects to process
    """
```

**Output**:
- List of selected Path objects
- Validation status
- File/directory count per path

---

## 3. Operation 1: Complete and Validate Imprint Configs

### 3.1 Inputs
- **Source Paths**: One or more config directories (configs/imprints*, etc.)
- **Selection Criteria**:
  - All configs in path
  - Specific configs by name/pattern
  - Incomplete configs only (missing required fields)
- **Validation Rules**: Schema from `imprint_template.json`
- **LLM Model**: User-selectable (default: claude-sonnet-4-5-20250929)

### 3.2 Processing Logic
```python
def complete_and_validate_configs(
    source_paths: List[Path],
    selected_configs: List[str],
    validation_schema: Dict,
    llm_model: str,
    auto_fix: bool = True
) -> BatchOperationResult:
    """
    Complete missing fields and validate imprint configs.

    Process:
    1. Load all configs from selected paths
    2. Identify missing/placeholder fields ([PLACEHOLDER])
    3. Use LLM to generate missing content based on:
       - Existing imprint information
       - Template structure
       - Context from related fields
    4. Validate against schema
    5. Report issues/fixes

    Returns:
        BatchOperationResult with:
        - configs_processed: int
        - configs_fixed: int
        - validation_errors: List[ValidationError]
        - updated_configs: Dict[str, ImprintConfig]
    """
```

### 3.3 Operations Per Config
1. **Load & Parse** JSON config file
2. **Detect Placeholders**: Find fields with `[PLACEHOLDER]` or empty required fields
3. **Generate Missing Content**:
   - Use LLM with prompt: "Complete this imprint configuration..."
   - Context: existing fields + template + imprint focus
4. **Validate Schema**: Check all required fields present
5. **Save Updated**: Write to same path or staging directory

### 3.4 Outputs
- **Updated Config Files**: Written to selected destination
- **Validation Report** (Streamlit display):
  - Configs processed: N
  - Fields completed: N
  - Validation errors: List with details
  - Download button for report JSON
- **Backup**: Original files backed up to `configs/imprints_archive/backups/`

---

## 4. Operation 2: Revise Imprint Configs Per User Prompt

### 4.1 Inputs
- **Source Paths**: Config directories to process
- **Selected Configs**: Specific files or all in path
- **Revision Prompt**: Natural language instruction (e.g., "make all publishers one-name AIs")
- **LLM Model**: User-selectable
- **Preview Mode**: Show changes before applying (checkbox)

### 4.2 Processing Logic
```python
def revise_configs_batch(
    source_paths: List[Path],
    selected_configs: List[str],
    revision_prompt: str,
    llm_model: str,
    preview_only: bool = True,
    fields_to_modify: List[str] = None  # Optional: limit scope
) -> BatchRevisionResult:
    """
    Revise imprint configs based on natural language prompt.

    Process:
    1. Load all selected configs
    2. For each config:
       a. Create revision prompt with context
       b. LLM generates revised JSON
       c. Validate changes
       d. Show diff if preview_only
    3. Apply changes if approved

    Returns:
        BatchRevisionResult with:
        - configs_modified: int
        - changes_preview: Dict[str, ConfigDiff]
        - validation_status: Dict[str, bool]
    """
```

### 4.3 Example Use Cases
| Prompt | Action |
|--------|--------|
| "make all publishers one-name AIs" | Modify `publisher_persona.persona_name` to single names |
| "update all trim sizes to 6x9" | Change `default_book_settings.trim_size` |
| "add sustainability focus to all charters" | Append text to `wizard_configuration.charter` |
| "increase all default prices by 15%" | Modify `wizard_configuration.price_point` |

### 4.4 Outputs
- **Preview Table** (if preview mode):
  - Config name
  - Fields changed
  - Old value → New value
  - Approve/Reject checkboxes
- **Applied Changes**:
  - Updated config files
  - Change log JSON
  - Backup of originals
- **Validation Report**

---

## 5. Operation 3: Connect to Ideation Dashboard & Create Tournaments

### 5.1 Inputs
- **Source Type**: Config directories OR imprint directories
- **Sour Paths**: Selected paths
- **Selected Imprints**: Specific imprints or all
- **Tournament Configuration**:
  - Number of ideas to generate per imprint
  - Tournament type (single, multi-round, continuous)
  - Evaluation criteria
  - LLM model for generation/evaluation
- **Integration Mode**:
  - Generate ideas only
  - Generate + run tournament
  - Generate + tournament + export results

### 5.2 Processing Logic
```python
def create_ideation_tournaments(
    source_paths: List[Path],
    selected_imprints: List[str],
    tournament_config: TournamentConfig,
    integration_mode: str = "full"
) -> IdeationBatchResult:
    """
    Create ideation tournaments for multiple imprints.

    Process:
    1. Load imprint configs/directories
    2. For each imprint:
       a. Extract publisher persona
       b. Initialize ContinuousIdeaGenerator
       c. Generate N ideas aligned with imprint focus
       d. Create Tournament instance
       e. Run evaluation if mode == "full"
    3. Aggregate results
    4. Export to Ideation Dashboard

    Returns:
        IdeationBatchResult with:
        - tournaments_created: List[Tournament]
        - ideas_generated: Dict[str, List[BookIdea]]
        - evaluation_results: Dict[str, TournamentResults]
        - dashboard_export_path: Path
    """
```

### 5.3 Imprint → Ideation Mapping
**From Config Files** (`configs/imprints/*.json`):
```python
{
    "imprint": "Mississippi Miracle Books",
    "publisher_persona": {
        "persona_name": "Magnolia",  # Publisher AI name
        "persona_bio": "...",
        "editorial_philosophy": "...",
        "preferred_topics": "...",
        "target_demographics": "..."
    },
    "publishing_focus": {
        "primary_genres": [...],
        "specialization": "..."
    }
}
```

**To Tournament Setup**:
```python
# Generate ideas aligned with imprint
generator = ContinuousIdeaGenerator(
    imprint_name="Mississippi Miracle Books",
    publisher_persona=PublisherPersona.from_config(config),
    focus_areas=config["publishing_focus"]["primary_genres"],
    target_audience=config["publishing_focus"]["target_audience"]
)

# Create tournament
tournament = Tournament(
    imprint_id=imprint_name,
    ideas=generated_ideas,
    evaluation_criteria=[
        "alignment_with_imprint",
        "market_viability",
        "originality",
        "execution_feasibility"
    ]
)
```

**From Imprint Directories** (`imprints/*/`):
- Load `imprint_config.json` from directory
- Access existing ideation setups if present
- Link to production pipelines

### 5.4 Outputs
- **Tournament Dashboard Integration**:
  - New tournaments visible in Ideation Dashboard
  - Linked to originating imprint
  - Ready for manual curation/evolution

- **Export Files** (per imprint):
  - `{imprint_name}_ideas_{timestamp}.json` - Generated ideas
  - `{imprint_name}_tournament_{timestamp}.json` - Tournament config/results
  - `{imprint_name}_evaluation_{timestamp}.json` - Evaluation scores

- **Summary Report** (Streamlit):
  - Imprints processed: N
  - Total ideas generated: N
  - Tournaments created: N
  - Top-rated ideas preview table
  - Link to Ideation Dashboard

---

## 6. UI Implementation Plan

### 6.1 Enhanced Imprint Creator Page Updates
**New Section**: "Batch Operations"

```
┌─────────────────────────────────────────────────────┐
│ 🔧 Batch Operations                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Select Operation Type:                              │
│ ○ Complete & Validate Configs                       │
│ ○ Revise Configs (Bulk Edit)                       │
│ ○ Generate Ideation Tournaments                     │
│                                                     │
│ ─────────────────────────────────────────────────── │
│                                                     │
│ Select Source Path(s):                              │
│ ☑ configs/imprints/                                 │
│ ☐ configs/imprints_draft/                           │
│ ☐ configs/imprints_staging/                         │
│ ☐ imprints/                                         │
│ ☐ imprints_in_development/                          │
│                                                     │
│ Custom Path: [________________] [Add]               │
│                                                     │
│ ─────────────────────────────────────────────────── │
│                                                     │
│ Selected Configs: 3 files                           │
│ ☑ mississippi_miracle_books.json                    │
│ ☑ xynapse_traces.json                               │
│ ☐ imprint_template.json                             │
│                                                     │
│ [▶ Run Operation]  [💾 Export Report]              │
└─────────────────────────────────────────────────────┘
```

### 6.2 Ideation Dashboard Updates
**New Tab**: "Batch Tournament Creation"

```
┌─────────────────────────────────────────────────────┐
│ 🎯 Batch Tournament Creation                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Source Imprints:                                    │
│ [Select from configs ▼] or [Select from dirs ▼]    │
│                                                     │
│ Tournament Configuration:                            │
│ • Ideas per imprint: [10]                           │
│ • Tournament type: [Multi-round ▼]                  │
│ • Model: [claude-sonnet-4-5-20250929 ▼]            │
│                                                     │
│ Evaluation Criteria:                                │
│ ☑ Imprint Alignment                                 │
│ ☑ Market Viability                                  │
│ ☑ Originality                                       │
│ ☐ Cross-imprint Synergy                             │
│                                                     │
│ Integration Mode:                                   │
│ ○ Generate ideas only                               │
│ ● Generate + Run tournament                         │
│ ○ Full automation (generate + evaluate + export)    │
│                                                     │
│ [🚀 Create Tournaments]                             │
└─────────────────────────────────────────────────────┘
```

---

## 7. Implementation Steps

### Phase 1: Foundation (Days 1-2)
1. Create shared utility module: `src/codexes/modules/batch_operations/`
   - `path_selector.py` - UI component for path selection
   - `config_loader.py` - Batch config loading utilities
   - `validation.py` - Schema validation engine
   - `backup.py` - Backup/restore utilities

2. Create data models:
   - `BatchOperationResult`
   - `ConfigDiff`
   - `ValidationError`
   - `IdeationBatchResult`

### Phase 2: Config Operations (Days 3-4)
3. Implement config completion:
   - `complete_and_validate_configs()` function
   - LLM prompt engineering for field completion
   - Validation against template schema
   - Backup mechanism

4. Implement config revision:
   - `revise_configs_batch()` function
   - Natural language → JSON transformation
   - Preview/diff display
   - Approval workflow

### Phase 3: Ideation Integration (Days 5-6)
5. Implement ideation pipeline:
   - `create_ideation_tournaments()` function
   - Config → PersonaPublisher mapping
   - Batch idea generation
   - Tournament creation & linking

6. Dashboard integration:
   - Export format for tournaments
   - Dashboard import functionality
   - Cross-linking between imprints and tournaments

### Phase 4: UI Implementation (Days 7-8)
7. Enhanced Imprint Creator updates:
   - Add "Batch Operations" tab
   - Integrate path selector
   - Operation-specific forms
   - Results display

8. Ideation Dashboard updates:
   - Add "Batch Tournament Creation" tab
   - Imprint source selector
   - Tournament configuration UI
   - Results summary

### Phase 5: Testing & Documentation (Days 9-10)
9. Testing:
   - Unit tests for batch operations
   - Integration tests with real configs
   - UI/UX testing

10. Documentation:
    - User guide for batch operations
    - API documentation
    - Example workflows

---

## 8. Expected Outputs Summary

### Operation 1: Complete & Validate
**Input**: Incomplete config files from multiple directories
**Output**:
- ✅ Completed config files with all placeholders filled
- 📊 Validation report (JSON + Streamlit display)
- 💾 Backups in `configs/imprints_archive/backups/`

### Operation 2: Bulk Revision
**Input**: Configs + natural language revision prompt
**Output**:
- ✏️ Revised config files
- 📋 Change log with diffs
- 👀 Preview mode for approval workflow
- 💾 Backups of originals

### Operation 3: Ideation Tournaments
**Input**: Imprint configs/directories
**Output**:
- 💡 Generated book ideas (JSON files)
- 🎯 Tournament instances (linked to Dashboard)
- 📈 Evaluation results (if run)
- 🔗 Dashboard integration exports

---

## 9. Dependencies

### New Modules Needed
- `src/codexes/modules/batch_operations/` - New directory
- Updates to `20_Enhanced_Imprint_Creator.py`
- Updates to `15_Ideation_and_Development.py`

### Existing Modules to Leverage
- `ImprintManager` - Existing imprint management
- `ContinuousIdeaGenerator` - Existing ideation system
- `Tournament` / `TournamentManager` - Existing tournament system
- `LLMCaller` - Existing LLM integration

### External Dependencies
- No new packages required
- Uses existing: `streamlit`, `pandas`, `json`, `pathlib`

---

## 10. Success Criteria

✅ User can select multiple config directories via dropdown + custom path
✅ Batch validation identifies and completes missing fields in 10+ configs
✅ Bulk revision applies user prompt changes to multiple configs with preview
✅ Ideation tournaments can be created for 5+ imprints simultaneously
✅ All operations create proper backups before modifying files
✅ Results are exportable as JSON and displayed clearly in UI
✅ Integration with existing Ideation Dashboard is seamless
