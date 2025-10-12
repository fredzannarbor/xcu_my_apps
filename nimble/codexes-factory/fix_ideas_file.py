#!/usr/bin/env python3
"""
Fix the ideas file - remove null entries and ensure exactly 128 ideas
"""

import json
from pathlib import Path

def main():
    file_path = Path("data/ideation/not_a_miracle_readers/ideas/all_128_ideas.json")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Filter out null/empty ideas
    valid_ideas = [idea for idea in data['ideas'] if idea and idea.get('idea_number')]

    print(f"Original count: {len(data['ideas'])}")
    print(f"Valid ideas: {len(valid_ideas)}")

    # Sort by idea_number to ensure order
    valid_ideas.sort(key=lambda x: x['idea_number'])

    # Verify we have exactly 128
    if len(valid_ideas) != 128:
        print(f"ERROR: Expected 128 ideas, got {len(valid_ideas)}")

        # Check for duplicates or gaps
        idea_numbers = [idea['idea_number'] for idea in valid_ideas]
        print(f"Idea numbers: {min(idea_numbers)} to {max(idea_numbers)}")

        expected = set(range(1, 129))
        actual = set(idea_numbers)
        missing = expected - actual
        duplicates = [n for n in idea_numbers if idea_numbers.count(n) > 1]

        if missing:
            print(f"Missing: {sorted(missing)}")
        if duplicates:
            print(f"Duplicates: {sorted(set(duplicates))}")

        return

    # Update data
    data['ideas'] = valid_ideas
    data['total_ideas'] = 128

    # Save
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Successfully fixed file")
    print(f"✓ Exactly 128 valid ideas (1-128)")
    print(f"✓ File saved: {file_path}")

if __name__ == "__main__":
    main()
