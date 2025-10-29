# Big Five Killer Publisher System Implementation

## Status: Phase 1.1 Started

**Branch:** `b5k-config`
**Started:** 2025-10-29
**Estimated Total:** 6-9 days

## Completed

### Phase 1.1: Publisher Base Class ✅
- Created `src/codexes/domain/models/publisher.py`
- Publisher class with full domain model
- Supports child imprint management
- Persona integration (Thaumette)
- Branding cascade to imprints
- LSI/distribution configuration

## Next Steps (In Order)

### Phase 1.2: Finalize B5K Publisher Config
**File:** `configs/publishers/BigFiveKiller.json` (exists, needs enhancement)

**TODO:**
1. Add complete Thaumette persona from `docs/Thaumette_Publisher_Persona.md`
2. Initialize empty `imprint_ids` array (will populate during import)
3. Add all territorial configs (US, UK, EU, CA, AU)
4. Configure LSI account settings
5. Add AI capabilities section

### Phase 1.3: Import 575 Imprints
**Create:** `scripts/import_575_imprints.py`

**TODO:**
1. Locate your 575 imprints list (CSV/JSON/database?)
2. Map to imprint config template structure
3. Assign personas from `docs/B5K_Imprint_Personas.md`
4. Create stub configs in `configs/imprints/b5k/`
5. Register each imprint ID in B5K publisher config
6. Generate imprint persona glyphs

**User Input Needed:** Location of 575 imprints list

### Phase 2: Imprint Templates & UI (2-3 days)

**Key files to update:**
- `configs/imprints/imprint_template.json` - Add publisher persona, tournaments, LLM settings
- `src/codexes/pages/20_Enhanced_Imprint_Creator.py` - Add publisher selection, persona wizard
- Update all 7 existing imprint configs to new format

### Phase 3: Tournament Integration (1 day)

**Create:**
- `templates/tournament_configs/` directory
- Tournament templates for different use cases
- Integration with imprint creation

### Phase 4: Warships & Navies Migration (1 day)

**Update:**
- Change publisher from "Nimble Books LLC" to "Big Five Killer LLC"
- Add Jellicoe persona details
- Maintain editorial independence

### Phase 5: Publisher Management UI (1-2 days)

**Create:**
- `src/codexes/pages/30_Publisher_Management.py`
- Dashboard for B5K with 575 imprints
- Thaumette persona editor

### Phase 6: LLM Standardization (1 day)

**Create:**
- `configs/llm_preferences.json`
- `src/codexes/modules/prompts/prompt_registry.py`

## Open Questions

1. **575 Imprints Source**: Where is the list? Format?
2. **Warships & Navies**: Immediate migration to B5K or gradual?
3. **Priority**: Start with B5K infrastructure or template updates?

## Technical Debt to Address

- Update existing 7 imprint configs to new template
- Backward compatibility for old workflows
- Testing strategy for bulk imprint import
- Publisher-imprint relationship validation

---

**To resume work:** Review next steps in Phase 1.2, locate 575 imprints list, then continue implementation sequentially through phases.
