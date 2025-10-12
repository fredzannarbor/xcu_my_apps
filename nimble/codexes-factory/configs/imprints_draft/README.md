# Imprints Draft Directory

**Purpose:** Working drafts of imprint configurations needing revision

## Status: DRAFT

This directory contains imprint configurations that are actively under development. These configs validate against the schema but require significant content development and revision before moving to staging.

## Criteria for Entry

- ✅ Valid JSON schema
- ⚠️ May be missing optional fields
- ⚠️ May have validation warnings
- ℹ️ Work in progress

## When to Use This Directory

- New imprint concepts being developed
- Configs requiring significant revision
- Experimental or exploratory configurations
- Generated configs awaiting manual review

## Promotion Process

### To Staging (`configs/imprints_staging/`)

1. **Complete Development:**
   - Fill in all required fields
   - Add publisher persona
   - Complete metadata defaults
   - Add distribution settings
   - Configure pricing

2. **Quality Check:**
   - JSON validates
   - No critical errors
   - Core configuration complete
   - Ready for final polish

3. **Promote:**
   ```bash
   cp configs/imprints_draft/{imprint}.json configs/imprints_staging/{imprint}.json
   git add configs/imprints_staging/{imprint}.json
   git commit -m "feat: Promote {imprint} to staging"
   ```

## Creating New Drafts

### From Template

```python
from src.codexes.modules.distribution.imprint_config_loader import ImprintConfigurationManager

manager = ImprintConfigurationManager("configs")
manager.create_imprint_from_template(
    imprint_name="New Imprint",
    publisher_name="Publisher Name",
    contact_email="contact@example.com"
)
```

The new config will be created in `configs/imprints/` by the legacy system, then move it here for development:

```bash
mv configs/imprints/new_imprint.json configs/imprints_draft/new_imprint.json
```

### Manual Creation

1. Copy template:
   ```bash
   cp resources/imprints_in_development/templates/imprint_template.json configs/imprints_draft/my_imprint.json
   ```

2. Edit configuration
3. Validate
4. Iterate until ready for staging

## Development Workflow

1. **Create** draft config in this directory
2. **Develop** content and configuration
3. **Validate** regularly
4. **Review** when substantially complete
5. **Promote** to staging when ready for final QA

## Archive Process

For abandoned or deprecated drafts:

```bash
mv configs/imprints_draft/{imprint}.json configs/imprints_archive/{imprint}_draft_$(date +%Y%m%d).json
git add -A
git commit -m "chore: Archive abandoned draft {imprint}"
```

## See Also

- [Imprints Directory Structure](../../docs/imprints_directory_structure.md)
- [Staging Imprints](../imprints_staging/README.md)
- [Template Documentation](../../resources/imprints_in_development/templates/README.md)
