#!/usr/bin/env python3
"""
Create indices with page references by linking entities to the pages where they appear.
Uses the new page numbering format: {volume}-BODY:{page}
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set


def load_page_mapping():
    """Load page mapping to convert original page numbers to new format"""
    mapping_file = Path("nimitz_ocr_gemini/page_mapping.json")

    with open(mapping_file, 'r') as f:
        data = json.load(f)

    # Convert to simple dict: original_page -> new_page_id
    mapping = {}
    for page_str, page_data in data["mapping"].items():
        if not page_data.get("excluded"):
            mapping[int(page_str)] = page_data["new_page_id"]

    return mapping


def build_entity_page_index():
    """Build reverse index: entity -> list of pages where it appears"""

    print("Building entity-to-page mappings...")
    print()

    # Load page mapping
    page_mapping = load_page_mapping()

    # Initialize entity indices
    entity_pages = {
        "persons": defaultdict(set),
        "places": defaultdict(set),
        "ships": defaultdict(set),
        "organizations": defaultdict(set)
    }

    # Load all page-level entity extractions
    entities_dir = Path("nimitz_ocr_gemini/entities_per_page")

    total_pages = 4023

    for page_num in range(total_pages):
        entity_file = entities_dir / f"entities_page_{page_num}.json"

        if entity_file.exists():
            with open(entity_file, 'r') as f:
                page_data = json.load(f)

            # Get new page ID
            new_page_id = page_mapping.get(page_num)

            if not new_page_id:
                continue  # Skip excluded pages

            # Add page reference for each entity found on this page
            if page_data.get("success") and not page_data.get("skipped"):
                entities = page_data.get("entities", {})

                for entity_type in entity_pages.keys():
                    for entity in entities.get(entity_type, []):
                        entity_pages[entity_type][entity].add(new_page_id)

    # Convert sets to sorted lists
    for entity_type in entity_pages:
        entity_pages[entity_type] = {
            entity: sorted(list(pages), key=lambda x: (int(x.split('-')[0]), int(x.split(':')[1])))
            for entity, pages in entity_pages[entity_type].items()
        }

    return entity_pages


def format_page_list(pages: List[str], max_display: int = 10) -> str:
    """Format page list for display, with continuation for long lists"""

    if len(pages) <= max_display:
        return ", ".join(pages)
    else:
        displayed = ", ".join(pages[:max_display])
        return f"{displayed}, ... ({len(pages)} total)"


def create_sample_index_with_pages(entity_type: str, entity_pages: Dict, max_entities: int = 50):
    """Create a sample index showing page references"""

    print(f"\n{'=' * 80}")
    print(f"SAMPLE: INDEX OF {entity_type.upper()} (showing first {max_entities})")
    print('=' * 80)
    print()

    sorted_entities = sorted(entity_pages.keys())

    for entity in sorted_entities[:max_entities]:
        pages = entity_pages[entity]
        page_ref = format_page_list(pages)

        # Format for display
        print(f"{entity:<60} {page_ref}")

    if len(sorted_entities) > max_entities:
        print()
        print(f"... and {len(sorted_entities) - max_entities:,} more entries")

    print()
    print(f"Total {entity_type}: {len(sorted_entities):,}")

    # Statistics
    page_counts = [len(pages) for pages in entity_pages.values()]
    avg_pages = sum(page_counts) / len(page_counts) if page_counts else 0
    max_pages = max(page_counts) if page_counts else 0

    print(f"Avg pages per entry: {avg_pages:.1f}")
    print(f"Max pages for single entry: {max_pages}")

    # Find most-referenced entities
    top_entities = sorted(entity_pages.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print(f"\nMost frequently appearing {entity_type}:")
    for entity, pages in top_entities:
        print(f"  {entity}: {len(pages)} pages")


def main():
    print("=" * 80)
    print("Creating Nimitz Indices with Page References")
    print("=" * 80)
    print()

    # Build entity-page mappings
    entity_pages = build_entity_page_index()

    # Show samples of each index
    for entity_type in ["persons", "places", "ships", "organizations"]:
        create_sample_index_with_pages(entity_type, entity_pages[entity_type], max_entities=50)

    # Save complete entity-page index
    output_file = Path("nimitz_ocr_gemini/entity_page_index.json")

    # Convert sets to lists for JSON serialization
    serializable = {}
    for entity_type, entities in entity_pages.items():
        serializable[entity_type] = {
            entity: pages for entity, pages in entities.items()
        }

    with open(output_file, 'w') as f:
        json.dump({
            "created_date": "2025-10-27",
            "total_entities": sum(len(v) for v in entity_pages.values()),
            "page_format": "{volume}-BODY:{page}",
            "entity_page_mappings": serializable,
            "stats": {
                entity_type: {
                    "total_entities": len(entity_pages[entity_type]),
                    "total_page_references": sum(len(pages) for pages in entity_pages[entity_type].values())
                }
                for entity_type in entity_pages
            }
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("COMPLETE INDEX SAVED")
    print("=" * 80)
    print(f"\nFile: {output_file}")
    print(f"Total entities: {sum(len(v) for v in entity_pages.values()):,}")
    print(f"Total page references: {sum(sum(len(pages) for pages in entity_pages[et].values()) for et in entity_pages):,}")
    print()
    print("Next step: Review samples above, then harmonize if needed")
    print("=" * 80)


if __name__ == "__main__":
    main()
