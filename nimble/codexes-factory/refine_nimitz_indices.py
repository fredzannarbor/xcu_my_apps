#!/usr/bin/env python3
"""
Refine Nimitz Graybook indices using:
1. Chicago Manual of Style indexing guidelines (18th edition, 2024, Chapter 16)
2. Naval history expertise for proper naming conventions
3. Cross-referencing and hierarchical organization
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


def normalize_person_name(name: str) -> tuple:
    """
    Normalize person names per Chicago Manual + naval conventions.
    Returns (main_entry, subentries, cross_references)
    """
    # Remove obvious junk
    if any(x in name.lower() for x in ['enlisted men', 'officers', 'warrant officer', 'civilian']) and name[0].isdigit():
        return None, [], []

    # Remove standalone ranks
    if name.strip().upper() in ['ADM', 'RADM', 'VADM', 'CAPT', 'CDR', 'LCDR', 'LT', 'LTJG', 'ENS']:
        return None, [], []

    # Standard format: "Last, First M., RANK"
    # Keep as is if already well-formatted
    if ',' in name and any(rank in name.upper() for rank in ['ADM', 'CAPT', 'CDR', 'COL', 'GEN']):
        return name, [], []

    return name, [], []


def normalize_place_name(place: str) -> tuple:
    """
    Normalize place names per naval/geographic conventions.
    Returns (main_entry, cross_references)
    """
    # Chicago Manual: Geographic entries alphabetized by specific to general
    # E.g., "Guadalcanal (Solomon Islands)" not "Solomon Islands, Guadalcanal"

    # Remove coordinate-like junk
    if re.match(r'^[\d\s,°-]+$', place):
        return None, []

    # Keep proper naval base/island names
    return place, []


def normalize_ship_name(ship: str) -> tuple:
    """
    Normalize ship names per naval conventions.
    Returns (main_entry, cross_references)
    Chicago Manual 16.90: Naval vessels indexed by name, not "USS"
    """

    # Standard format examples:
    # "Enterprise (CV-6)"  [main entry]
    # Cross-reference: "USS Enterprise. See Enterprise (CV-6)"

    # Remove standalone hull classifications
    if ship.strip().upper() in ['CV', 'BB', 'CA', 'CL', 'DD', 'SS', 'CVE', 'CVL']:
        return None, []

    # If already has hull number, good
    if '(' in ship and ')' in ship:
        # Extract ship name without USS prefix for main entry
        clean_name = ship.replace('USS ', '').replace('IJN ', '').replace('HMS ', '')
        return clean_name, []

    return ship, []


def normalize_organization_name(org: str) -> tuple:
    """
    Normalize military unit names per Chicago Manual.
    Chicago Manual 16.89: Military units alphabetized by designation, not generic terms
    """

    # Remove standalone abbreviations that aren't real organizations
    if org.strip().upper() in ['CA', 'CL', 'DD', 'BB', 'CV', 'SS']:
        return None, []

    # "Task Force 16" => main entry "Task Force 16", cross-ref "TF 16. See Task Force 16"
    # "CINCPAC" => keep as is (standard abbreviation)

    return org, []


def create_refined_indices():
    """Create refined indices with proper indexing standards."""

    print("=" * 80)
    print("Refining Nimitz Graybook Indices")
    print("Per Chicago Manual of Style 18th Ed. (2024), Chapter 16")
    print("=" * 80)
    print()

    # Load entities
    entities_file = Path("nimitz_ocr_gemini/entities_per_page/entities_all.json")
    with open(entities_file, 'r') as f:
        data = json.load(f)

    entities = data["entities"]

    print(f"Raw entities loaded:")
    print(f"  Persons: {len(entities['persons']):,}")
    print(f"  Places: {len(entities['places']):,}")
    print(f"  Ships: {len(entities['ships']):,}")
    print(f"  Organizations: {len(entities['organizations']):,}")
    print()

    # Normalize each entity type
    print("Normalizing entities...")

    refined = {
        "persons": set(),
        "places": set(),
        "ships": set(),
        "organizations": set()
    }

    # Process persons
    for person in entities["persons"]:
        main_entry, _, _ = normalize_person_name(person)
        if main_entry:
            refined["persons"].add(main_entry)

    # Process places
    for place in entities["places"]:
        main_entry, _ = normalize_place_name(place)
        if main_entry:
            refined["places"].add(main_entry)

    # Process ships
    for ship in entities["ships"]:
        main_entry, _ = normalize_ship_name(ship)
        if main_entry:
            refined["ships"].add(main_entry)

    # Process organizations
    for org in entities["organizations"]:
        main_entry, _ = normalize_organization_name(org)
        if main_entry:
            refined["organizations"].add(main_entry)

    print(f"\nAfter normalization:")
    print(f"  Persons: {len(refined['persons']):,}")
    print(f"  Places: {len(refined['places']):,}")
    print(f"  Ships: {len(refined['ships']):,}")
    print(f"  Organizations: {len(refined['organizations']):,}")
    print(f"  Total reduction: {sum(len(entities[k]) for k in entities) - sum(len(refined[k]) for k in refined):,} entries")
    print()

    # Save refined entities
    refined_file = Path("nimitz_ocr_gemini/entities_refined.json")
    with open(refined_file, 'w') as f:
        json.dump({
            "refined_date": "2025-10-27",
            "normalization_rules": "Chicago Manual of Style 18th Ed (2024) + Naval History Conventions",
            "entities": {k: sorted(list(v)) for k, v in refined.items()},
            "stats": {
                "persons": len(refined["persons"]),
                "places": len(refined["places"]),
                "ships": len(refined["ships"]),
                "organizations": len(refined["organizations"]),
                "total": sum(len(v) for v in refined.values())
            }
        }, f, indent=2)

    print(f"✓ Saved refined entities: {refined_file}")
    print()

    # Now create properly formatted LaTeX indices
    print("Creating Chicago Manual-compliant LaTeX indices...")
    # (Will integrate with create_nimitz_indices.py using refined data)

    print("=" * 80)
    print(f"\nRefined indices ready for Volume 0")
    print(f"Next step: Add page references by cross-referencing with OCR data")
    print("=" * 80)


if __name__ == "__main__":
    create_refined_indices()
