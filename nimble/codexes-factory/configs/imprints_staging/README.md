# Imprints Staging Directory

**Purpose:** Nearly production-ready imprint configurations in final polish phase

## Status: STAGING

This directory contains imprint configurations that are nearly production-ready and undergoing final quality assurance and testing before promotion to `configs/imprints/`.

## Criteria for Entry

- ✅ Valid JSON schema
- ✅ All required fields present
- ✅ Publisher persona defined
- ✅ Core configuration complete
- ⚠️ May have minor warnings
- ⚠️ Awaiting final testing

## Current Imprints

Review each configuration file in this directory for promotion readiness.

## Promotion Process

### To Production (`configs/imprints/`)

1. **Final Review:**
   - Verify all fields are accurate
   - Test with system components
   - Confirm publisher persona is complete
   - Run validation checks

2. **Quality Gates:**
   - No validation errors
   - All pricing/discount percentages valid
   - Email validation passes
   - Tested with dropdown_manager
   - Confirmed working in Streamlit UI

3. **Promotion:**
   ```bash
   # After review and testing
   cp configs/imprints_staging/{imprint}.json configs/imprints/{imprint}.json
   git add configs/imprints/{imprint}.json
   git commit -m "feat: Promote {imprint} to production"
   ```

4. **Archive Staging:**
   ```bash
   # Optional: remove from staging after successful promotion
   git rm configs/imprints_staging/{imprint}.json
   ```

## Demotion Process

### To Draft (`configs/imprints_draft/`)

If significant issues are found:

```bash
mv configs/imprints_staging/{imprint}.json configs/imprints_draft/{imprint}.json
git add -A
git commit -m "refactor: Move {imprint} back to draft for revision"
```

## Testing Checklist

Before promoting to production, verify:

- [ ] Loads successfully in system
- [ ] Appears in imprint dropdown
- [ ] All fields populate correctly
- [ ] No validation errors
- [ ] Publisher persona displays properly
- [ ] Pricing calculations work
- [ ] LSI field mappings correct

## See Also

- [Imprints Directory Structure](../../docs/imprints_directory_structure.md)
- [Production Imprints](../imprints/README.md)
- [Draft Imprints](../imprints_draft/README.md)
