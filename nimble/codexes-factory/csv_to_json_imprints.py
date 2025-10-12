#!/usr/bin/env python3
"""
Convert CSV imprint data to JSON format for batch processing.
"""

import csv
import json
import sys
from pathlib import Path

def csv_to_json_imprints(csv_file: str, output_dir: str = "imprint_objects"):
    """Convert CSV imprint data to individual JSON files."""

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Read CSV and convert to JSON objects
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, 1):
            # Skip empty rows
            if not row.get('name'):
                continue

            # Create CodexObject-compatible structure
            imprint_obj = {
                "title": row.get('name', f'Imprint {i}'),
                "content": f"""Imprint Charter: {row.get('charter', '')}

Focus Areas: {row.get('focus', '')}

Tagline: {row.get('tagline', '')}

Target Audience: {row.get('target_audience', '')}

Competitive Advantage: {row.get('competitive_advantage', '')}

Examples: {row.get('examples', '')}""",
                "genre": "Publishing",
                "target_audience": row.get('target_audience', 'General'),
                "object_type": "idea",
                "metadata": {
                    "imprint_name": row.get('name', ''),
                    "charter": row.get('charter', ''),
                    "focus": row.get('focus', ''),
                    "tagline": row.get('tagline', ''),
                    "competitive_advantage": row.get('competitive_advantage', ''),
                    "examples": row.get('examples', '')
                }
            }

            # Generate filename from imprint name
            safe_name = row.get('name', f'imprint_{i}').replace(' ', '_').replace('/', '_')
            output_file = output_path / f"{safe_name}.json"

            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as json_f:
                json.dump(imprint_obj, json_f, indent=2, ensure_ascii=False)

            print(f"✅ Created: {output_file}")

    print(f"\n📦 Created {len(list(output_path.glob('*.json')))} JSON files in {output_dir}/")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json_imprints.py <csv_file> [output_dir]")
        sys.exit(1)

    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "imprint_objects"

    csv_to_json_imprints(csv_file, output_dir)