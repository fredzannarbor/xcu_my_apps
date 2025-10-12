#!/usr/bin/env python3
"""
Maya's Story Reel Reader Panels - Agent-Based Evaluation
Uses Claude Code's Task tool to run evaluations with Claude Max (no API calls)
"""

import json
from pathlib import Path
from datetime import datetime

def load_personas_and_book():
    """Load all personas and book data."""
    from run_maya_reader_panels import (
        create_children_personas,
        create_parent_personas,
        create_expert_personas,
        create_purchasing_personas,
        load_maya_story
    )

    return {
        'book_idea': load_maya_story(),
        'panels': {
            'children_9_10': create_children_personas(),
            'parents': create_parent_personas(),
            'reading_experts': create_expert_personas(),
            'purchasing': create_purchasing_personas()
        }
    }

def save_evaluation(panel_name: str, persona_name: str, evaluation: dict, output_dir: Path):
    """Save individual evaluation result."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Append to panel file
    panel_file = output_dir / f"{panel_name}_agent_evaluations.jsonl"
    with open(panel_file, 'a') as f:
        result = {
            'timestamp': datetime.now().isoformat(),
            'persona_name': persona_name,
            'evaluation': evaluation
        }
        f.write(json.dumps(result) + '\n')

    print(f"✓ {panel_name}: {persona_name} - Rating: {evaluation.get('overall_rating', 'N/A')}/10")

if __name__ == "__main__":
    print("="*80)
    print("MAYA'S STORY REEL - AGENT-BASED READER PANELS")
    print("Using Claude Code Task tool for evaluations")
    print("="*80)

    data = load_personas_and_book()
    book = data['book_idea']

    print(f"\nBook: {book.title}")
    print(f"Total personas: {sum(len(p) for p in data['panels'].values())}")
    print("\nThis script prepares data for agent-based evaluation.")
    print("The actual evaluations should be run through Claude Code's Task tool.\n")

    # Export data for agent consumption
    export_file = Path('data/reader_panels/maya_story_reel/agent_evaluation_data.json')
    export_file.parent.mkdir(parents=True, exist_ok=True)

    export_data = {
        'book_title': book.title,
        'book_description': book.description,
        'book_logline': book.logline,
        'panels': {}
    }

    for panel_name, personas in data['panels'].items():
        export_data['panels'][panel_name] = [
            {
                'name': p.name,
                'characteristics': p.characteristics
            }
            for p in personas
        ]

    with open(export_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✓ Exported evaluation data to: {export_file}")
    print(f"\nTo run evaluations with Claude Code agents, use the Task tool to:")
    print("1. Read the exported data")
    print("2. For each persona, evaluate the book idea")
    print("3. Save results back to data/reader_panels/maya_story_reel/")
