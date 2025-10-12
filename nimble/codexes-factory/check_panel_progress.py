#!/usr/bin/env python3
"""Quick progress checker for Maya's Story Reel reader panels."""

import json
from pathlib import Path
from datetime import datetime

def check_progress():
    """Check current panel progress."""
    output_dir = Path('data/reader_panels/maya_story_reel')

    targets = {
        'children_9_10': 100,
        'parents': 80,
        'reading_experts': 50,
        'purchasing': 40
    }

    total_target = sum(targets.values())  # 270
    total_completed = 0

    print("="*80)
    print(f"MAYA'S STORY REEL - READER PANEL PROGRESS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    for panel_name, target in targets.items():
        # Find latest file for this panel
        panel_files = sorted(output_dir.glob(f"{panel_name}_feedback_*.json"))

        if panel_files:
            latest_file = panel_files[-1]
            with open(latest_file) as f:
                data = json.load(f)

            completed = data['total_reviews']
            total_completed += completed
            pct = (completed / target) * 100
            avg_rating = data['statistics']['avg_overall_rating']

            status = "✓" if completed >= target else "⋯"
            print(f"  {status} {panel_name:20s}: {completed:3d}/{target:3d} ({pct:5.1f}%) - Avg: {avg_rating:.1f}/10")
        else:
            print(f"  ⋯ {panel_name:20s}:   0/{target:3d} (  0.0%)")

    overall_pct = (total_completed / total_target) * 100
    print("="*80)
    print(f"Overall Progress: {total_completed}/{total_target} ({overall_pct:.1f}%)")
    print("="*80)

    return total_completed, total_target

if __name__ == "__main__":
    check_progress()
