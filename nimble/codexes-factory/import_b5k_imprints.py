#!/usr/bin/env python3
"""
Import 600 B5K imprints from bigfive_replacement_complete_structure.json
and create individual imprint configs under configs/imprints/b5k/

This script:
1. Reads the B5K structure file
2. Creates individual imprint configs based on imprint_template.json
3. Maps charter, focus, tagline, competitive_advantage from source
4. Updates BigFiveKiller.json with all imprint_ids
5. Generates a comprehensive import report
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2):
    """Save JSON file with pretty formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def create_imprint_slug(imprint_name: str) -> str:
    """Create URL-friendly slug from imprint name."""
    return imprint_name.lower().replace(' ', '_').replace('&', 'and').replace("'", "")


def create_imprint_config(imprint_data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """Create imprint config from template and source data."""
    config = template.copy()

    imprint_name = imprint_data['name']
    imprint_slug = create_imprint_slug(imprint_name)

    # Update metadata
    config['_config_info']['description'] = imprint_data.get('charter', '')
    config['_config_info']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    config['_config_info']['parent_publisher'] = "Big Five Killer LLC"

    # Core identity
    config['imprint'] = imprint_name
    config['publisher'] = "Big Five Killer LLC"
    config['contact_email'] = "editorial@bigfivekiller.com"

    # Branding
    config['branding']['logo_path'] = f"logos/b5k/{imprint_slug}_logo.png"
    config['branding']['tagline'] = imprint_data.get('tagline', '')
    config['branding']['website'] = f"https://www.codexes.xtuff.ai/b5k/{imprint_slug}"

    # Publishing focus
    config['publishing_focus']['specialization'] = imprint_data.get('focus', '')
    config['publishing_focus']['target_audience'] = imprint_data.get('target_audience', '')

    # Distribution settings
    config['distribution_settings']['lightning_source_account'] = imprint_data.get('lsi_account', 'LSI950000')

    # Publisher persona - will be enhanced later with specific AI personas
    config['publisher_persona'] = {
        "persona_name": "Thaumette",
        "parent_persona": "Thaumette (Big Five Killer LLC)",
        "imprint_charter": imprint_data.get('charter', ''),
        "competitive_advantage": imprint_data.get('competitive_advantage', ''),
        "risk_tolerance": "moderate",
        "decision_style": "data-driven with literary quality focus",
        "preferred_topics": imprint_data.get('focus', ''),
        "target_demographics": imprint_data.get('target_audience', ''),
        "editorial_philosophy": "Fill profitable gaps ignored by Big Five while maintaining high literary standards"
    }

    # Wizard configuration
    config['wizard_configuration']['name'] = imprint_name
    config['wizard_configuration']['charter'] = imprint_data.get('charter', '')
    config['wizard_configuration']['imprint_type'] = "specialized_niche"

    # B5K specific metadata
    config['b5k_metadata'] = {
        "imprint_id": imprint_data.get('imprint_id', ''),
        "establishment_date": imprint_data.get('establishment_date', '2025-09-22'),
        "status": imprint_data.get('status', 'active'),
        "annual_titles_target": imprint_data.get('annual_titles_target', '200-1000'),
        "distribution_channel": imprint_data.get('distribution_channel', 'Global POD + Traditional'),
        "examples": imprint_data.get('examples', ''),
        "source_system": "bigfive_replacement_import",
        "import_date": datetime.now().isoformat()
    }

    return config


def main():
    """Main import process."""
    print("=" * 80)
    print("B5K IMPRINT IMPORT - Big Five Killer LLC")
    print("=" * 80)
    print()

    # Paths
    base_path = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory")
    source_file = base_path / "publishers/bigfive_replacement/bigfive_replacement_complete_structure.json"
    template_file = base_path / "configs/imprints/imprint_template.json"
    publisher_config_file = base_path / "configs/publishers/BigFiveKiller.json"
    output_dir = base_path / "configs/imprints/b5k"
    report_file = base_path / "B5K_IMPORT_REPORT.md"

    # Load source data
    print(f"Loading source data from: {source_file}")
    source_data = load_json(source_file)
    print(f"✓ Loaded publisher: {source_data['publisher']}")
    print(f"✓ Total imprints in source: {source_data['total_imprints']}")
    print()

    # Load template
    print(f"Loading template from: {template_file}")
    template = load_json(template_file)
    print(f"✓ Template loaded successfully")
    print()

    # Load publisher config
    print(f"Loading publisher config from: {publisher_config_file}")
    publisher_config = load_json(publisher_config_file)
    print(f"✓ Publisher config loaded: {publisher_config['publisher']}")
    print()

    # Process each imprint
    print("Processing imprints...")
    print("-" * 80)

    imprints = source_data.get('imprints', {})
    imprint_ids = []
    created_files = []
    errors = []

    for imprint_key, imprint_data in imprints.items():
        try:
            imprint_name = imprint_data['name']
            imprint_id = imprint_data.get('imprint_id', imprint_key)
            imprint_slug = create_imprint_slug(imprint_name)

            # Create config
            config = create_imprint_config(imprint_data, template)

            # Save to file
            output_file = output_dir / f"{imprint_slug}.json"
            save_json(config, output_file)

            # Track
            imprint_ids.append(imprint_id)
            created_files.append(str(output_file))

            print(f"✓ {imprint_id}: {imprint_name}")

        except Exception as e:
            error_msg = f"✗ {imprint_key}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)

    print("-" * 80)
    print(f"Created {len(created_files)} imprint configs")
    print()

    # Update publisher config with imprint IDs
    print("Updating publisher config with imprint IDs...")
    publisher_config['imprint_ids'] = sorted(imprint_ids)
    publisher_config['scale_metrics']['current_imprints'] = str(len(imprint_ids))
    publisher_config['_template_info']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    save_json(publisher_config, publisher_config_file)
    print(f"✓ Updated {publisher_config_file}")
    print(f"✓ Added {len(imprint_ids)} imprint IDs")
    print()

    # Generate report
    print("Generating import report...")
    report = generate_report(source_data, imprint_ids, created_files, errors)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved to: {report_file}")
    print()

    # Summary
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Total imprints imported: {len(created_files)}")
    print(f"Total errors: {len(errors)}")
    print(f"Output directory: {output_dir}")
    print(f"Report: {report_file}")
    print()

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  {error}")


def generate_report(source_data: Dict, imprint_ids: List[str],
                   created_files: List[str], errors: List[str]) -> str:
    """Generate comprehensive import report."""
    report = f"""# B5K Imprint Import Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Publisher**: Big Five Killer LLC
**Source**: bigfive_replacement_complete_structure.json

## Summary Statistics

- **Total Imprints in Source**: {source_data.get('total_imprints', 0)}
- **Imprints Successfully Imported**: {len(created_files)}
- **Errors Encountered**: {len(errors)}
- **Success Rate**: {len(created_files) / max(source_data.get('total_imprints', 1), 1) * 100:.1f}%

## Source Data Overview

- **Publisher**: {source_data.get('publisher', 'N/A')}
- **Establishment Date**: {source_data.get('establishment_date', 'N/A')}
- **Market Position**: {source_data.get('market_position', 'N/A')}
- **Competitive Advantage**: {source_data.get('competitive_advantage', 'N/A')}
- **Estimated Annual Revenue**: {source_data.get('estimated_annual_revenue', 'N/A')}

### Market Coverage
"""

    if 'market_coverage' in source_data:
        coverage = source_data['market_coverage']
        report += f"""
- **Revenue Gap Categories**: {coverage.get('revenue_gap_categories', 0)}
- **Big Five Equivalent Strength**: {coverage.get('big_five_equivalent_strength', 0)}
- **Emerging Innovation**: {coverage.get('emerging_innovation', 0)}
"""

    report += f"""

## Import Process

### Configuration
- **Template Source**: configs/imprints/imprint_template.json
- **Output Directory**: configs/imprints/b5k/
- **Publisher Config**: configs/publishers/BigFiveKiller.json

### Field Mapping
The following fields were mapped from source to imprint configs:
- `name` → `imprint`
- `charter` → `publisher_persona.imprint_charter`
- `focus` → `publishing_focus.specialization`
- `tagline` → `branding.tagline`
- `target_audience` → `publishing_focus.target_audience` and `publisher_persona.target_demographics`
- `competitive_advantage` → `publisher_persona.competitive_advantage`
- `imprint_id` → `b5k_metadata.imprint_id`
- `examples` → `b5k_metadata.examples`

### Imprint List

Total: {len(created_files)} imprints

"""

    # Add sample imprints (first 10)
    sample_count = min(10, len(created_files))
    report += f"#### Sample Imprints (First {sample_count}):\n\n"

    imprints = source_data.get('imprints', {})
    for i, (key, data) in enumerate(list(imprints.items())[:sample_count]):
        report += f"{i+1}. **{data['name']}** (`{data.get('imprint_id', key)}`)\n"
        report += f"   - Charter: {data.get('charter', 'N/A')[:100]}...\n"
        report += f"   - Focus: {data.get('focus', 'N/A')}\n"
        report += f"   - Target: {data.get('annual_titles_target', 'N/A')} titles/year\n\n"

    if len(created_files) > sample_count:
        report += f"\n...and {len(created_files) - sample_count} more imprints.\n"

    if errors:
        report += f"\n### Errors\n\n"
        for error in errors:
            report += f"- {error}\n"

    report += f"""

## Next Steps

1. **Review Generated Configs**: Spot-check configs in `configs/imprints/b5k/`
2. **Create AI Personas**: Develop unique AI personas for each imprint (see B5K_Imprint_Personas.md)
3. **Configure LLM Preferences**: Add model preferences and prompt customizations per imprint
4. **Test Pipeline**: Run test book generation through sample imprints
5. **Update Documentation**: Document any custom workflows for B5K imprints

## Files Created

- **Imprint Configs**: {len(created_files)} files in `configs/imprints/b5k/`
- **Publisher Config**: Updated `configs/publishers/BigFiveKiller.json`
- **This Report**: `B5K_IMPORT_REPORT.md`

---

*Generated by import_b5k_imprints.py*
*Big Five Killer LLC - Books are not content. Readers are not users.*
"""

    return report


if __name__ == "__main__":
    main()
