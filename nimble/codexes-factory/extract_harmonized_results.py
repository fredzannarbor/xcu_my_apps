#!/usr/bin/env python3
"""
Extract successful harmonization results from checkpoint files.
Combine with page references to create final indices.
"""

import json
from pathlib import Path


def load_checkpoint_data():
    """Load all Pass 1 checkpoint files"""

    checkpoints_dir = Path("input_files_by_imprint/big_five_warships_and_navies/nimitz_ocr_gemini")

    harmonized = {
        "persons": {},
        "places": {},
        "ships": {},
        "organizations": {}
    }

    for entity_type in harmonized.keys():
        # Find all checkpoints for this entity type
        checkpoint_pattern = f"pass1_checkpoint_{entity_type}_*.json"
        checkpoint_files = sorted(checkpoints_dir.glob(checkpoint_pattern))

        if checkpoint_files:
            # Load the last (most complete) checkpoint
            latest = checkpoint_files[-1]
            print(f"Loading {entity_type}: {latest.name}")

            with open(latest, 'r') as f:
                data = json.load(f)
                harmonized[entity_type] = data

    return harmonized


def main():
    print("=" * 80)
    print("Extracting Harmonized Indices from Checkpoints")
    print("=" * 80)
    print()

    # Load harmonized data
    harmonized = load_checkpoint_data()

    # Load page mappings
    page_index_file = Path("input_files_by_imprint/big_five_warships_and_navies/nimitz_ocr_gemini/entity_page_index.json")

    with open(page_index_file, 'r') as f:
        entity_page_data = json.load(f)

    entity_page_mappings = entity_page_data["entity_page_mappings"]

    print()
    print("Merging harmonization with page references...")
    print()

    final_indices = {}

    for entity_type in harmonized:
        final_indices[entity_type] = {}

        for authoritative, data in harmonized[entity_type].items():
            # Collect page references from all variants
            all_pages = set()

            # Handle dict, string, or list values
            if isinstance(data, str):
                data = {"variants": [data], "subentries": []}
            elif isinstance(data, list):
                data = {"variants": data, "subentries": []}
            elif not isinstance(data, dict):
                data = {"variants": [str(data)], "subentries": []}

            variants = data.get("variants", [authoritative])
            if isinstance(variants, str):
                variants = [variants]

            for variant in variants:
                if variant in entity_page_mappings[entity_type]:
                    all_pages.update(entity_page_mappings[entity_type][variant])

            # Sort pages
            sorted_pages = sorted(list(all_pages), key=lambda x: (
                int(x.split('-')[0]),
                int(x.split(':')[1])
            ))

            final_indices[entity_type][authoritative] = {
                "pages": sorted_pages,
                "page_count": len(sorted_pages),
                "subentries": data.get("subentries", []),
                "variants_merged": variants
            }

        print(f"{entity_type.capitalize()}: {len(final_indices[entity_type]):,} entries")

    # Save final indices
    output_file = Path("output/indices_harmonized_final.json")

    with open(output_file, 'w') as f:
        json.dump({
            "created": "2025-10-29",
            "model": "gemini/gemini-2.5-flash",
            "harmonization": "Two-pass (within-batch + cross-batch)",
            "total_entries": sum(len(v) for v in final_indices.values()),
            "indices": final_indices,
            "stats": {
                entity_type: {
                    "entries": len(final_indices[entity_type]),
                    "page_refs": sum(len(v["pages"]) for v in final_indices[entity_type].values())
                }
                for entity_type in final_indices
            }
        }, f, indent=2)

    print()
    print("=" * 80)
    print("FINAL HARMONIZED INDICES")
    print("=" * 80)
    print(f"\nTotal entries: {sum(len(v) for v in final_indices.values()):,}")
    print(f"\nBy type:")
    for et in final_indices:
        print(f"  {et.capitalize()}: {len(final_indices[et]):,}")

    print(f"\nSaved: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
