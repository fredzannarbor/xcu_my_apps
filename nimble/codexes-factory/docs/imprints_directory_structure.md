# Imprints Directory Structure

**Date:** October 1, 2025
**Status:** Active Standard

## Overview

This document defines the directory structure for managing imprint configurations at different stages of development and production readiness.

## Directory Structure

```
codexes-factory/
│
├── configs/
│   ├── imprints/                          # PRODUCTION
│   │   └── *.json                         # Live, tested, ready for deployment
│   │                                      # Read by system (dropdown_manager, imprint_config_loader)
│   │
│   ├── imprints_staging/                  # STAGING
│   │   └── *.json                         # Nearly production-ready, final polish
│   │                                      # Final QA and testing before moving to production
│   │
│   ├── imprints_draft/                    # DRAFTS
│   │   └── *.json                         # Working drafts, validate but need revision
│   │                                      # Active development and iteration
│   │
│   ├── imprints_archive/                  # ARCHIVE
│   │   └── *.json                         # Experimental, deprecated, or historical
│   │                                      # Moved from production when superseded
│   │
│   ├── expanded_imprints/                 # LEGACY (to be migrated)
│   │   └── *.json                         # Enhanced configs with additional metadata
│   │
│   └── expanded_imprints_complete/        # LEGACY (to be migrated)
│       └── *.json                         # Completed expanded configs
│
├── resources/
│   └── imprints_in_development/
│       ├── collections/                   # COLLECTIONS
│       │   ├── bigfive_replacement/       # Large related batches
│       │   └── [other_collections]/       # Organized by project/initiative
│       │
│       └── templates/                     # TEMPLATES
│           └── imprint_template.json      # Template sources
│
└── imprints/                              # ASSETS
    └── {imprint_name}/                    # Per-imprint assets
        ├── prompts.json                   # LLM prompts
        ├── template.tex                   # LaTeX templates
        ├── cover_template.tex             # Cover templates
        ├── prepress.py                    # Prepress scripts
        ├── schedule.csv                   # Publishing schedules
        └── [other assets]                 # Imprint-specific files
```

## Directory Purposes

### Production Tier

#### `configs/imprints/` - PRODUCTION
- **Purpose:** Live, production-ready imprint configurations
- **Criteria:**
  - Fully tested and validated
  - All required fields populated
  - Publisher persona defined
  - Ready for immediate deployment
  - Visible in Streamlit UI dropdowns
- **System Access:** Read by system components
  - `imprint_config_loader.py`
  - `dropdown_manager.py`
  - `configuration_service.py`
- **Example:** `xynapse_traces.json`

### Pre-Production Tiers

#### `configs/imprints_staging/` - STAGING
- **Purpose:** Nearly production-ready, in final polish
- **Criteria:**
  - Core configuration complete
  - Undergoing final QA/testing
  - Minor tweaks or polish needed
  - Awaiting final approval for production
- **Workflow:** Final review → `configs/imprints/`

#### `configs/imprints_draft/` - DRAFTS
- **Purpose:** Working drafts needing revision
- **Criteria:**
  - Validates against schema
  - Core structure in place
  - Needs content development
  - Requires significant revision
- **Workflow:** Development → Staging → Production

### Storage Tiers

#### `configs/imprints_archive/` - ARCHIVE
- **Purpose:** Historical, experimental, or deprecated configs
- **Criteria:**
  - Superseded by newer versions
  - Experimental concepts
  - Historical reference
  - Deprecated imprints
- **Workflow:** Production → Archive (when updated/replaced)

#### `resources/imprints_in_development/collections/` - COLLECTIONS
- **Purpose:** Large batches of related imprints
- **Criteria:**
  - Thematic or project-based groupings
  - Bulk-generated configurations
  - Require systematic revision
  - Not yet individually reviewed
- **Examples:**
  - `bigfive_replacement/` - BigFive template-based imprints
  - Future collections organized by initiative

#### `resources/imprints_in_development/templates/` - TEMPLATES
- **Purpose:** Template sources and generators
- **Criteria:**
  - Template files for imprint creation
  - Not actual imprint configs
  - Used by generation tools

### Asset Management

#### `imprints/{imprint_name}/` - ASSETS
- **Purpose:** Per-imprint operational assets
- **Criteria:**
  - Imprint-specific files
  - Not configuration metadata
  - Used during production/prepress
- **Contents:**
  - `prompts.json` - LLM prompt configurations
  - `template.tex` - LaTeX interior templates
  - `cover_template.tex` - LaTeX cover templates
  - `prepress.py` - Prepress processing scripts
  - `schedule.csv` - Publishing schedules
  - `writing_style.json` - Style guidelines
  - Other operational files

## Promotion Workflow

### Standard Path
```
Draft → Staging → Production
  ↓        ↓          ↓
configs/ configs/   configs/
imprints_draft/ → imprints_staging/ → imprints/
```

### Collection Path
```
Collection → Individual Review → Draft → Staging → Production
     ↓              ↓              ↓        ↓          ↓
resources/    [manual review]  configs/  configs/  configs/
imprints_in_  [extraction]    imprints_ imprints_ imprints/
development/                   draft/    staging/
collections/
```

### Archive Path
```
Production → Archive (when superseded)
    ↓            ↓
configs/    configs/
imprints/   imprints_archive/
```

## File Naming Conventions

- **Format:** `{imprint_name}.json`
- **Normalization:** Lowercase, underscores for spaces
- **Examples:**
  - `xynapse_traces.json`
  - `nimble_ultra.json`
  - `text_hip_global.json`

## Migration Plan

### Legacy Directories to Migrate

**`configs/expanded_imprints/`** and **`configs/expanded_imprints_complete/`**
- Review each config
- Determine readiness level
- Move to appropriate tier:
  - Production-ready → `configs/imprints/`
  - Nearly ready → `configs/imprints_staging/`
  - Needs work → `configs/imprints_draft/`

### Steps:
1. Audit existing configs in legacy directories
2. Assess production readiness
3. Move to appropriate new location
4. Update documentation
5. Remove legacy directories when empty

## Validation Requirements

### Production Tier (`configs/imprints/`)
- ✅ Valid JSON schema
- ✅ All required fields present
- ✅ Publisher persona defined
- ✅ Email validation passes
- ✅ Pricing/discount percentages valid
- ✅ No validation errors
- ✅ Tested with system components

### Staging Tier (`configs/imprints_staging/`)
- ✅ Valid JSON schema
- ✅ All required fields present
- ✅ Publisher persona defined
- ⚠️ May have minor warnings
- ⚠️ Awaiting final testing

### Draft Tier (`configs/imprints_draft/`)
- ✅ Valid JSON schema
- ⚠️ May be missing optional fields
- ⚠️ May have validation warnings
- ℹ️ Work in progress

## System Integration

### Read Locations (Priority Order)
1. `configs/imprints/` - Primary production location
2. `imprints/` - Legacy fallback (for backwards compatibility)
3. Other locations - Not read by system

### Write Locations
- New configs created in: `configs/imprints_draft/`
- Promoted to staging: `configs/imprints_staging/`
- Promoted to production: `configs/imprints/`

## Maintenance

### Regular Tasks
- **Weekly:** Review staging tier for promotion candidates
- **Monthly:** Audit draft tier for stale configs
- **Quarterly:** Archive superseded production configs

### Quality Gates
- Draft → Staging: Complete all required fields, validate
- Staging → Production: Full testing, final approval
- Production → Archive: Superseded by new version

## Examples

### Xynapse Traces Timeline
1. **Collection:** `resources/imprints_in_development/bigfive_replacement/xynapse_traces.json`
2. **Expanded:** `configs/expanded_imprints/xynapse_traces.json`
3. **Production:** `configs/imprints/xynapse_traces.json` ← Current
4. **Assets:** `imprints/xynapse_traces/` (prompts, templates, etc.)

### Future Imprint Path
1. Generate from template → `configs/imprints_draft/new_imprint.json`
2. Review and polish → `configs/imprints_staging/new_imprint.json`
3. Final approval → `configs/imprints/new_imprint.json`
4. Create assets → `imprints/new_imprint/` (if needed)

---

*Document Version: 1.0*
*Last Updated: October 1, 2025*
*Maintained by: Publishing Operations*
