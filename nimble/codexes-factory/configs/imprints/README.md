# Production Imprints Directory

**Purpose:** Live, production-ready imprint configurations

## Status: PRODUCTION ⭐

This directory contains imprint configurations that are fully tested, validated, and ready for immediate use in the Codexes Factory publishing platform.

## System Integration

This directory is the **primary source** for imprint configurations. System components read from here:

- `imprint_config_loader.py` - Loads imprint configurations
- `dropdown_manager.py` - Populates UI dropdowns
- `configuration_service.py` - Provides configuration services
- Streamlit UI pages - Display imprint options

## Criteria for Production

Configurations in this directory must meet all of these requirements:

- ✅ Valid JSON schema
- ✅ All required fields present and populated
- ✅ Publisher persona defined
- ✅ Email validation passes
- ✅ Pricing/discount percentages valid (0-100)
- ✅ No validation errors
- ✅ Tested with system components
- ✅ Confirmed working in UI

## Current Production Imprints

### Xynapse Traces
**File:** `xynapse_traces.json`
**Publisher:** Nimble Books LLC
**Focus:** Transcriptive meditation (pilsa) and knowledge dichotomies
**Status:** Active, 476-book catalog
**Publisher Persona:** Seon (선/禪)

*Additional imprints will be listed here as they are promoted to production.*

## Adding New Production Imprints

### Promotion from Staging

When an imprint in `configs/imprints_staging/` is ready:

1. **Final Validation:**
   ```python
   from src.codexes.modules.distribution.imprint_config_loader import ImprintConfigurationManager

   manager = ImprintConfigurationManager("configs")
   result = manager.validate_imprint_config("imprint_name")

   if result['valid']:
       print("✅ Ready for production")
   else:
       print("❌ Validation errors:", result['errors'])
   ```

2. **Copy to Production:**
   ```bash
   cp configs/imprints_staging/{imprint}.json configs/imprints/{imprint}.json
   ```

3. **Test in System:**
   - Launch Streamlit UI
   - Verify imprint appears in dropdown
   - Test configuration loading
   - Confirm all fields populate correctly

4. **Commit:**
   ```bash
   git add configs/imprints/{imprint}.json
   git commit -m "feat: Add {imprint} to production

   - Promoted from staging
   - Validated and tested
   - Ready for live use"
   ```

### Direct Creation (Not Recommended)

Only for urgent situations:

```bash
# Copy from template
cp resources/imprints_in_development/templates/imprint_template.json \
   configs/imprints/{imprint}.json

# Edit thoroughly
# Validate extensively
# Test comprehensively
```

**Note:** Standard workflow (draft → staging → production) is preferred for quality assurance.

## Updating Production Imprints

When updating an existing production config:

1. **Archive Current Version:**
   ```bash
   # Create backup
   cp configs/imprints/{imprint}.json \
      configs/imprints_archive/{imprint}_v1_$(date +%Y%m%d).json
   ```

2. **Make Updates:**
   - Edit configuration file
   - Update version/date in `_config_info`
   - Validate changes

3. **Test:**
   - Reload in system
   - Verify no breaking changes
   - Confirm backward compatibility

4. **Commit with Archive:**
   ```bash
   git add configs/imprints/{imprint}.json \
           configs/imprints_archive/{imprint}_v1_*.json
   git commit -m "feat: Update {imprint} config

   - [Describe changes]
   - Archived previous version
   - Tested and validated"
   ```

## Removing Production Imprints

When decommissioning an imprint:

1. **Archive:**
   ```bash
   mv configs/imprints/{imprint}.json \
      configs/imprints_archive/{imprint}_deprecated_$(date +%Y%m%d).json
   ```

2. **Document:**
   - Add note to archive README
   - Update this README
   - Notify stakeholders

3. **Commit:**
   ```bash
   git add -A
   git commit -m "chore: Deprecate {imprint}

   - Moved to archive
   - [Reason for deprecation]
   - Effective date: $(date +%Y-%m-%d)"
   ```

## Quality Assurance

### Pre-Production Checklist

Before promoting any imprint to production:

- [ ] JSON validates without errors
- [ ] All required fields present
- [ ] Publisher persona complete and appropriate
- [ ] Contact email valid format
- [ ] Pricing defaults reasonable
- [ ] Distribution settings correct
- [ ] Metadata defaults appropriate
- [ ] LSI-specific settings configured
- [ ] Tested in development environment
- [ ] Appears in UI dropdown
- [ ] Loads without errors
- [ ] All fields populate correctly
- [ ] Documentation updated

### Regular Audits

- **Monthly:** Review all production configs for updates needed
- **Quarterly:** Validate all configs still meet current standards
- **Annually:** Comprehensive audit and refresh

## File Structure

Each production config should follow this structure:

```json
{
  "_config_info": {
    "description": "Brief description",
    "version": "1.0",
    "last_updated": "2025-10-01",
    "parent_publisher": "Publisher Name"
  },
  "imprint": "Imprint Name",
  "publisher": "Publisher Name",
  "contact_email": "email@example.com",
  "branding": { ... },
  "publishing_focus": { ... },
  "default_book_settings": { ... },
  "pricing_defaults": { ... },
  "distribution_settings": { ... },
  "metadata_defaults": { ... },
  "publisher_persona": {
    "persona_name": "Name",
    "persona_bio": "Description",
    "risk_tolerance": "High|Moderate|Low",
    "decision_style": "Style",
    "preferred_topics": "Topics",
    "target_demographics": "Demographics",
    "editorial_philosophy": "Philosophy",
    "vulnerabilities": "Vulnerabilities"
  },
  ...
}
```

## See Also

- [Imprints Directory Structure](../../docs/imprints_directory_structure.md)
- [Staging Imprints](../imprints_staging/README.md)
- [Configuration Reference](../../docs/xynapse_traces_imprint_configuration.md)
- [Validation Guide](../../docs/)

---

*Last Updated: October 1, 2025*
*Production Imprints: 1 active*
