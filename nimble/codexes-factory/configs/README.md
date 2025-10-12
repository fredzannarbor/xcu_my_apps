# Configs Directory

**Purpose:** Configuration files for the Codexes Factory publishing platform

## Directory Structure

```
configs/
├── imprints/                   # PRODUCTION: Live, production-ready imprints
├── imprints_staging/           # STAGING: Nearly ready, in final polish
├── imprints_draft/             # DRAFTS: Working drafts needing revision
├── imprints_archive/           # ARCHIVE: Historical and deprecated configs
├── publishers/                 # Publisher configurations
├── tranches/                   # Batch/tranche configurations
├── templates/                  # Configuration templates
├── test_imprints/              # Test imprints for development
├── expanded_imprints/          # LEGACY: To be migrated
└── expanded_imprints_complete/ # LEGACY: To be migrated
```

## Imprint Configuration Tiers

### Production Tier

#### `imprints/` - PRODUCTION ⭐
**Purpose:** Live, production-ready imprint configurations

- Read by system components (UI dropdowns, config loaders)
- Fully tested and validated
- All required fields complete
- Ready for immediate use

See: [imprints/README.md](./imprints/README.md)

### Pre-Production Tiers

#### `imprints_staging/` - STAGING 🔄
**Purpose:** Nearly production-ready, in final QA

- Undergoing final review and testing
- Core configuration complete
- Minor polish needed
- Awaiting promotion to production

See: [imprints_staging/README.md](./imprints_staging/README.md)

#### `imprints_draft/` - DRAFTS ✏️
**Purpose:** Working drafts under active development

- Validates against schema
- Requires significant content work
- Active iteration and refinement
- Not yet ready for staging

See: [imprints_draft/README.md](./imprints_draft/README.md)

### Storage Tier

#### `imprints_archive/` - ARCHIVE 📦
**Purpose:** Historical, experimental, and deprecated configs

- Superseded production versions
- Discontinued imprints
- Experimental concepts
- Historical reference

See: [imprints_archive/README.md](./imprints_archive/README.md)

## Other Configuration Directories

### `publishers/`
Publisher-level configurations defining publishing houses and their settings.

### `tranches/`
Batch/tranche configurations for processing multiple books together.

### `templates/`
Template files for creating new configurations.

### `test_imprints/`
Test imprint configurations for development and testing purposes.

## Configuration Files

### Top-Level Configs

- `default_lsi_config.json` - Default LSI/Lightning Source configuration
- `isbn_schedule.json` - ISBN assignment schedules
- `llm_monitoring_config.json` - LLM usage monitoring settings
- `llm_prompt_config.json` - LLM prompt configurations
- `logging_config.json` - Logging settings
- `spine_width_config.json` - Spine width calculation config
- `validation_config.json` - Validation rules

## Workflow: Imprint Promotion

Standard path for new imprints:

```
1. Create Draft
   └─> configs/imprints_draft/{imprint}.json

2. Develop & Refine
   └─> Iterate on draft configuration

3. Promote to Staging
   └─> configs/imprints_staging/{imprint}.json

4. Final QA & Testing
   └─> Test with system, validate

5. Promote to Production
   └─> configs/imprints/{imprint}.json

6. Archive on Update
   └─> configs/imprints_archive/{imprint}_v1_{date}.json
```

See: [Full Workflow Documentation](../docs/imprints_directory_structure.md)

## Quick Reference

### Find an Imprint Config

```bash
# Production imprints
ls configs/imprints/

# All configs across tiers
find configs -name "*.json" -path "*/imprints*" | grep -v archive
```

### Validate an Imprint

```python
from src.codexes.modules.distribution.imprint_config_loader import ImprintConfigurationManager

manager = ImprintConfigurationManager("configs")
validation = manager.validate_imprint_config("imprint_name")
print(validation)
```

### Promote to Production

```bash
# After testing and validation
cp configs/imprints_staging/my_imprint.json configs/imprints/my_imprint.json
git add configs/imprints/my_imprint.json
git commit -m "feat: Promote my_imprint to production"
```

## Legacy Directories (To Be Migrated)

### `expanded_imprints/` and `expanded_imprints_complete/`

These directories contain legacy expanded configurations that are being migrated to the new tier system:

- **Production-ready** configs → Move to `imprints/`
- **Nearly ready** configs → Move to `imprints_staging/`
- **Needs work** configs → Move to `imprints_draft/`

Once migration is complete, these directories will be removed.

## See Also

- [Imprints Directory Structure Documentation](../docs/imprints_directory_structure.md)
- [Imprint Configuration Reference](../docs/xynapse_traces_imprint_configuration.md)
- [System Integration Guide](../docs/)
- [Rights Management Usage Guide](../src/codexes/modules/rights_management/USAGE_GUIDE.md)

---

*Last Updated: October 1, 2025*
*Maintained by: Publishing Operations*
