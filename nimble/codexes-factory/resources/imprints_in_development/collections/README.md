# Imprint Collections Directory

**Purpose:** Large batches of related imprint configurations requiring systematic review

## Status: BULK DEVELOPMENT

This directory contains collections of imprint configurations that were generated in batches or organized by project/initiative. These require systematic review and individual assessment before promotion.

## Contents

### Current Collections

#### `bigfive_replacement/`
- **Purpose:** Template-based imprints from BigFive replacement initiative
- **Count:** Multiple imprint configurations
- **Status:** Requires individual review
- **Next Steps:** Extract, review, refine individual imprints

## When to Use Collections

Collections are appropriate for:

- **Bulk Generation:** AI-generated or template-based batch creation
- **Project Initiatives:** Related imprints from specific projects
- **Thematic Groups:** Sets of imprints sharing common characteristics
- **Systematic Development:** Large-scale content that needs organized review

## Collection Structure

Each collection should be in its own subdirectory:

```
collections/
├── {collection_name}/
│   ├── README.md              # Collection documentation
│   ├── {imprint1}.json
│   ├── {imprint2}.json
│   └── ...
```

## Processing Collections

### Individual Extraction

1. **Review Collection:**
   ```bash
   ls resources/imprints_in_development/collections/{collection}/
   ```

2. **Select Imprint:**
   - Review individual config
   - Assess quality and completeness
   - Determine appropriate tier

3. **Extract to Appropriate Tier:**

   **To Draft** (needs significant work):
   ```bash
   cp resources/imprints_in_development/collections/{collection}/{imprint}.json \
      configs/imprints_draft/{imprint}.json
   ```

   **To Staging** (nearly ready):
   ```bash
   cp resources/imprints_in_development/collections/{collection}/{imprint}.json \
      configs/imprints_staging/{imprint}.json
   ```

   **To Production** (ready now):
   ```bash
   cp resources/imprints_in_development/collections/{collection}/{imprint}.json \
      configs/imprints/{imprint}.json
   ```

4. **Refine as Needed:**
   - Update publisher persona
   - Adjust metadata
   - Validate configuration
   - Test with system

### Batch Processing

For systematic processing of entire collections:

```bash
# Create processing script
./scripts/process_collection.sh {collection_name}
```

Example script workflow:
1. Iterate through collection configs
2. Validate each config
3. Categorize by readiness
4. Move to appropriate tiers
5. Generate review report

## Collection Lifecycle

```
1. Generate/Create Collection
   ↓
2. Store in collections/{name}/
   ↓
3. Review & Assess Quality
   ↓
4. Extract Individual Imprints
   ├── → configs/imprints_draft/ (needs work)
   ├── → configs/imprints_staging/ (nearly ready)
   └── → configs/imprints/ (ready now)
   ↓
5. Archive Empty Collection (optional)
```

## Creating New Collections

### From Bulk Generation

When generating multiple related imprints:

```bash
# Create collection directory
mkdir -p resources/imprints_in_development/collections/my_collection

# Run generator targeting collection
python scripts/generate_imprints.py \
  --output resources/imprints_in_development/collections/my_collection \
  --template template_name
```

### From Project Initiative

For project-based imprint sets:

```bash
# Create collection
mkdir -p resources/imprints_in_development/collections/project_initiative

# Document collection
cat > resources/imprints_in_development/collections/project_initiative/README.md << 'EOF'
# Project Initiative Collection

## Purpose
[Describe the project and imprint goals]

## Imprints
[List and describe each imprint]

## Status
[Current status and next steps]
EOF
```

## Archive Collections

When a collection has been fully processed:

```bash
# Archive the collection
tar -czf resources/imprints_in_development/collections/archive/{collection}_$(date +%Y%m%d).tar.gz \
  resources/imprints_in_development/collections/{collection}/

# Remove original (after verification)
rm -rf resources/imprints_in_development/collections/{collection}/
```

## Review Checklist

For each imprint in a collection:

- [ ] JSON validates
- [ ] Required fields present
- [ ] Publisher persona defined (or needs one)
- [ ] Pricing/discount values reasonable
- [ ] Contact email valid
- [ ] Metadata appropriate for genre/focus
- [ ] Uniqueness - no duplicate of existing imprint
- [ ] Quality - meets minimum standards

## See Also

- [Imprints Directory Structure](../../../docs/imprints_directory_structure.md)
- [BigFive Collection Documentation](./bigfive_replacement/README.md)
- [Batch Processing Scripts](../../../scripts/README.md)
