#!/usr/bin/env python3
"""
Associate generated imprints with BigFiveReplacement publisher
"""

import csv
import json
import os
from pathlib import Path

def associate_imprints_with_publisher(csv_file: str, publisher_name: str = "BigFiveReplacement LLC"):
    """Associate all imprints in CSV with the specified publisher"""

    # Read the CSV file
    imprints = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            imprints.append(row)

    print(f"📊 Found {len(imprints)} imprints to associate with {publisher_name}")

    # Create publisher association structure
    publisher_structure = {
        "publisher": publisher_name,
        "total_imprints": len(imprints),
        "establishment_date": "2025-09-22",
        "market_position": "Largest publisher by imprint count",
        "competitive_advantage": "Exceeds Big Five with 600+ specialized imprints",
        "estimated_annual_revenue": "$10B+",
        "market_coverage": {
            "revenue_gap_categories": 45,
            "big_five_equivalent_strength": 375,
            "emerging_innovation": 180
        },
        "imprints": {}
    }

    # Group imprints by category for organization
    category_counts = {}

    # Process each imprint
    for i, imprint in enumerate(imprints, 1):
        imprint_id = f"imprint_{i:03d}"

        # Add publisher association to imprint
        enhanced_imprint = {
            **imprint,
            "publisher": publisher_name,
            "imprint_id": imprint_id,
            "establishment_date": "2025-09-22",
            "status": "active",
            "annual_titles_target": "1000-5000",
            "distribution_channel": "Global POD + Traditional",
            "lsi_account": "LSI950000"
        }

        # Categorize by focus area for reporting
        focus = imprint.get('focus', '').lower()
        category = determine_category(focus)
        category_counts[category] = category_counts.get(category, 0) + 1

        publisher_structure["imprints"][imprint_id] = enhanced_imprint

    # Add category breakdown
    publisher_structure["category_breakdown"] = category_counts

    # Save enhanced structure
    output_file = f"bigfive_replacement_complete_structure.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(publisher_structure, f, indent=2, ensure_ascii=False)

    # Create individual imprint config files
    configs_dir = Path("configs/imprints")
    configs_dir.mkdir(parents=True, exist_ok=True)

    for imprint_id, imprint_data in publisher_structure["imprints"].items():
        # Create imprint config based on template
        imprint_config = create_imprint_config(imprint_data, publisher_name)

        config_file = configs_dir / f"{imprint_data['name'].lower().replace(' ', '_').replace('&', 'and')}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(imprint_config, f, indent=2, ensure_ascii=False)

    print(f"✅ Created complete publisher structure: {output_file}")
    print(f"✅ Created {len(imprints)} individual imprint configs in configs/imprints/")
    print(f"📈 Category breakdown: {category_counts}")

    return publisher_structure

def determine_category(focus_text: str) -> str:
    """Determine category based on focus text"""
    focus = focus_text.lower()

    if any(word in focus for word in ['puzzle', 'game', 'crossword', 'sudoku']):
        return 'puzzles_games'
    elif any(word in focus for word in ['farm', 'agriculture', 'homestead']):
        return 'agricultural'
    elif any(word in focus for word in ['manga', 'webtoon', 'comic']):
        return 'manga_comics'
    elif any(word in focus for word in ['spanish', 'bilingual', 'latino']):
        return 'bilingual_spanish'
    elif any(word in focus for word in ['christian', 'religious', 'faith']):
        return 'religious'
    elif any(word in focus for word in ['spiritual', 'meditation', 'new age']):
        return 'spirituality'
    elif any(word in focus for word in ['craft', 'knit', 'sewing', 'quilting']):
        return 'crafts'
    elif any(word in focus for word in ['military', 'war', 'veteran']):
        return 'military'
    elif any(word in focus for word in ['tarot', 'astrology', 'divination']):
        return 'divination'
    elif any(word in focus for word in ['fiction', 'novel', 'story']):
        return 'fiction'
    elif any(word in focus for word in ['business', 'economics', 'entrepreneur']):
        return 'business'
    elif any(word in focus for word in ['health', 'wellness', 'medical']):
        return 'health'
    elif any(word in focus for word in ['science', 'technology', 'research']):
        return 'science_tech'
    elif any(word in focus for word in ['history', 'historical']):
        return 'history'
    elif any(word in focus for word in ['cooking', 'food', 'recipe']):
        return 'cooking'
    else:
        return 'general'

def create_imprint_config(imprint_data: dict, publisher_name: str) -> dict:
    """Create standardized imprint configuration"""

    return {
        "imprint": imprint_data["name"],
        "publisher": publisher_name,
        "contact_email": f"contact@{imprint_data['name'].lower().replace(' ', '').replace('&', 'and')}.com",
        "branding": {
            "tagline": imprint_data.get("tagline", ""),
            "brand_colors": {"primary": "#1a237e", "secondary": "#303f9f"},
            "website": f"https://www.{imprint_data['name'].lower().replace(' ', '').replace('&', 'and')}.com"
        },
        "publishing_focus": {
            "primary_focus": imprint_data.get("focus", ""),
            "target_audience": imprint_data.get("target_audience", ""),
            "competitive_advantage": imprint_data.get("competitive_advantage", ""),
            "example_titles": imprint_data.get("examples", "")
        },
        "business_metrics": {
            "annual_titles_target": imprint_data.get("annual_titles_target", "1000-5000"),
            "establishment_date": imprint_data.get("establishment_date", "2025-09-22"),
            "status": imprint_data.get("status", "active")
        },
        "distribution_settings": {
            "lightning_source_account": imprint_data.get("lsi_account", "LSI950000"),
            "distribution_channel": imprint_data.get("distribution_channel", "Global POD + Traditional")
        }
    }

def main():
    csv_file = "bigfive_replacement_600_imprints.csv"

    if not os.path.exists(csv_file):
        print(f"❌ CSV file {csv_file} not found. Run the imprint generator first.")
        return False

    structure = associate_imprints_with_publisher(csv_file)

    print(f"\n🎉 BigFiveReplacement Publisher Structure Complete!")
    print(f"📊 Total imprints: {structure['total_imprints']}")
    print(f"💰 Estimated revenue: {structure['estimated_annual_revenue']}")
    print(f"🏆 Market position: {structure['market_position']}")

    return True

if __name__ == "__main__":
    main()