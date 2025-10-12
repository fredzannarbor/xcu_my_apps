#!/usr/bin/env python3
"""
Analyze the children's feedback for Maya's Story Reel.
"""

import json
from collections import defaultdict
from pathlib import Path

def load_evaluations(file_path: str) -> list:
    """Load all evaluations from JSONL file."""
    evaluations = []
    with open(file_path, 'r') as f:
        for line in f:
            evaluations.append(json.loads(line))
    return evaluations

def analyze_evaluations(evaluations: list):
    """Generate comprehensive analysis of evaluations."""

    print("="*80)
    print("MAYA'S STORY REEL - CHILDREN'S 9-10 READER PANEL EVALUATION RESULTS")
    print("="*80)
    print(f"\nTotal Evaluations: {len(evaluations)}")
    print()

    # Calculate overall statistics
    market_appeal_scores = [e['market_appeal_score'] for e in evaluations]
    genre_fit_scores = [e['genre_fit_score'] for e in evaluations]
    audience_alignment_scores = [e['audience_alignment_score'] for e in evaluations]
    overall_ratings = [e['overall_rating'] for e in evaluations]

    avg_market = sum(market_appeal_scores) / len(market_appeal_scores)
    avg_genre = sum(genre_fit_scores) / len(genre_fit_scores)
    avg_audience = sum(audience_alignment_scores) / len(audience_alignment_scores)
    avg_overall = sum(overall_ratings) / len(overall_ratings)

    print("OVERALL AVERAGE SCORES:")
    print(f"  Market Appeal:       {avg_market:.2f}/10")
    print(f"  Genre Fit:           {avg_genre:.2f}/10")
    print(f"  Audience Alignment:  {avg_audience:.2f}/10")
    print(f"  Overall Rating:      {avg_overall:.2f}/10")
    print()

    # Rating distribution
    high_ratings = sum(1 for e in evaluations if e['overall_rating'] >= 7)
    medium_ratings = sum(1 for e in evaluations if 4 <= e['overall_rating'] < 7)
    low_ratings = sum(1 for e in evaluations if e['overall_rating'] < 4)

    print("RATING DISTRIBUTION:")
    print(f"  High (7-10):   {high_ratings:3d} ({high_ratings/len(evaluations)*100:.1f}%)")
    print(f"  Medium (4-6):  {medium_ratings:3d} ({medium_ratings/len(evaluations)*100:.1f}%)")
    print(f"  Low (0-3):     {low_ratings:3d} ({low_ratings/len(evaluations)*100:.1f}%)")
    print()

    # Group by persona type
    persona_groups = defaultdict(list)
    for e in evaluations:
        persona_type = e['persona_name'].rsplit('#', 1)[0].strip()
        persona_groups[persona_type].append(e)

    print("BREAKDOWN BY READER TYPE:")
    print()
    for persona_type in sorted(persona_groups.keys()):
        group = persona_groups[persona_type]
        avg_rating = sum(e['overall_rating'] for e in group) / len(group)
        avg_market = sum(e['market_appeal_score'] for e in group) / len(group)
        avg_genre = sum(e['genre_fit_score'] for e in group) / len(group)
        avg_audience = sum(e['audience_alignment_score'] for e in group) / len(group)

        print(f"{persona_type} (n={len(group)}):")
        print(f"  Overall: {avg_rating:.2f}/10  |  Market: {avg_market:.2f}  |  Genre: {avg_genre:.2f}  |  Audience: {avg_audience:.2f}")
        print()

    # Common themes in feedback
    print("="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print()

    # Count mentions of key themes in detailed feedback
    themes = {
        'AI/technology': 0,
        'phonics concerns': 0,
        'dolphin/animals': 0,
        'reading struggles': 0,
        'adventure': 0,
        'humor': 0,
        'video making': 0,
        'relatable': 0
    }

    for e in evaluations:
        feedback = e['detailed_feedback'].lower()
        if 'ai' in feedback or 'technology' in feedback or 'tech' in feedback:
            themes['AI/technology'] += 1
        if 'phonics' in feedback and ('boring' in feedback or 'concern' in feedback or 'worried' in feedback):
            themes['phonics concerns'] += 1
        if 'dolphin' in feedback or 'animal' in feedback:
            themes['dolphin/animals'] += 1
        if 'reading struggle' in feedback or 'struggle with reading' in feedback:
            themes['reading struggles'] += 1
        if 'adventure' in feedback:
            themes['adventure'] += 1
        if 'humor' in feedback or 'funny' in feedback:
            themes['humor'] += 1
        if 'video' in feedback:
            themes['video making'] += 1
        if 'relat' in feedback:  # catches "relatable", "relate", etc.
            themes['relatable'] += 1

    print("THEME MENTIONS IN FEEDBACK:")
    for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme:20s}: {count:3d} ({count/len(evaluations)*100:.1f}%)")
    print()

    # Common recommendations
    print("MOST COMMON RECOMMENDATIONS:")
    rec_themes = {
        'more adventure': 0,
        'more humor': 0,
        'more animals': 0,
        'more action': 0,
        'less phonics focus': 0,
        'more visuals/pictures': 0
    }

    for e in evaluations:
        recs = e['recommendations'].lower()
        if 'adventure' in recs:
            rec_themes['more adventure'] += 1
        if 'humor' in recs or 'funny' in recs:
            rec_themes['more humor'] += 1
        if 'animal' in recs:
            rec_themes['more animals'] += 1
        if 'action' in recs:
            rec_themes['more action'] += 1
        if 'less' in recs and 'phonics' in recs:
            rec_themes['less phonics focus'] += 1
        if 'picture' in recs or 'visual' in recs or 'comic' in recs:
            rec_themes['more visuals/pictures'] += 1

    for rec, count in sorted(rec_themes.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {rec:25s}: {count:3d} ({count/len(evaluations)*100:.1f}%)")
    print()

    # Common concerns
    print("MOST COMMON CONCERNS:")
    concern_themes = {
        'too much phonics': 0,
        'not enough action': 0,
        'too educational': 0,
        'not relatable': 0,
        'too serious/sad': 0
    }

    for e in evaluations:
        concerns = e['concerns'].lower()
        if 'phonics' in concerns and ('much' in concerns or 'focus' in concerns):
            concern_themes['too much phonics'] += 1
        if 'action' in concerns or 'adventure' in concerns:
            concern_themes['not enough action'] += 1
        if 'educational' in concerns or 'school' in concerns or 'homework' in concerns or 'lesson' in concerns:
            concern_themes['too educational'] += 1
        if 'relat' in concerns and 'not' in concerns:
            concern_themes['not relatable'] += 1
        if 'serious' in concerns or 'sad' in concerns:
            concern_themes['too serious/sad'] += 1

    for concern, count in sorted(concern_themes.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {concern:25s}: {count:3d} ({count/len(evaluations)*100:.1f}%)")
    print()

    # Top and bottom rated evaluations
    sorted_evals = sorted(evaluations, key=lambda x: x['overall_rating'], reverse=True)

    print("="*80)
    print("TOP 3 MOST ENTHUSIASTIC EVALUATIONS:")
    print("="*80)
    for i, e in enumerate(sorted_evals[:3], 1):
        print(f"\n{i}. {e['persona_name']} - Rating: {e['overall_rating']}/10")
        print(f"   {e['detailed_feedback'][:200]}...")

    print()
    print("="*80)
    print("BOTTOM 3 MOST SKEPTICAL EVALUATIONS:")
    print("="*80)
    for i, e in enumerate(sorted_evals[-3:], 1):
        print(f"\n{i}. {e['persona_name']} - Rating: {e['overall_rating']}/10")
        print(f"   {e['detailed_feedback'][:200]}...")

    print()
    print("="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

def main():
    file_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/children_9_10_claude_max_feedback.jsonl"

    evaluations = load_evaluations(file_path)
    analyze_evaluations(evaluations)

if __name__ == "__main__":
    main()
