#!/usr/bin/env python3
"""
Analyze the Snark evaluations and generate a summary report.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

INPUT_PATH = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark/children_feedback.jsonl"
OUTPUT_PATH = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark/children_evaluation_summary.md"


def load_evaluations() -> List[Dict[str, Any]]:
    """Load all evaluations from JSONL file."""
    evaluations = []
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                evaluations.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
    return evaluations


def generate_report(evaluations: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive markdown report."""

    report = []
    report.append("# The Hunting of the Snark: 100 Child Reader Evaluation Report\n")
    report.append(f"**Lewis Carroll (1876) - Evaluated by Modern 9-12 Year Olds in 2025**\n\n")
    report.append(f"**Total Evaluations:** {len(evaluations)} children\n\n")

    # Group by archetype
    by_archetype = defaultdict(list)
    for eval in evaluations:
        persona = eval.get('persona', {})
        archetype = persona.get('archetype', 'Unknown')
        by_archetype[archetype].append(eval)

    # Overall Statistics
    report.append("## Executive Summary\n\n")

    all_market = [e.get('market_appeal', 0) for e in evaluations if 'market_appeal' in e]
    all_genre = [e.get('genre_fit', 0) for e in evaluations if 'genre_fit' in e]
    all_audience = [e.get('audience_alignment', 0) for e in evaluations if 'audience_alignment' in e]
    all_overall = [e.get('overall_rating', 0) for e in evaluations if 'overall_rating' in e]

    if all_overall:
        avg_market = sum(all_market) / len(all_market)
        avg_genre = sum(all_genre) / len(all_genre)
        avg_audience = sum(all_audience) / len(all_audience)
        avg_overall = sum(all_overall) / len(all_overall)

        report.append(f"**Overall Average Scores (out of 10):**\n\n")
        report.append(f"- **Market Appeal:** {avg_market:.1f}/10\n")
        report.append(f"- **Genre Fit:** {avg_genre:.1f}/10\n")
        report.append(f"- **Audience Alignment:** {avg_audience:.1f}/10\n")
        report.append(f"- **OVERALL RATING:** {avg_overall:.1f}/10\n\n")

    # Key Findings
    report.append("### Key Findings\n\n")

    # Verdict based on rating
    if avg_overall < 4:
        verdict = "NOT RECOMMENDED for modern children"
        explanation = "Struggles significantly across all reader types"
    elif avg_overall < 6:
        verdict = "MARGINAL appeal for modern children"
        explanation = "Works for niche audiences but faces significant challenges"
    elif avg_overall < 8:
        verdict = "GOOD fit for specific reader types"
        explanation = "Appeals to certain children but not broadly"
    else:
        verdict = "EXCELLENT for modern children"
        explanation = "Successfully engages contemporary young readers"

    report.append(f"**VERDICT:** {verdict}\n")
    report.append(f"_{explanation}_\n\n")

    # Common themes
    favorite_themes = defaultdict(int)
    confusing_themes = defaultdict(int)

    for eval in evaluations:
        for fav in eval.get('favorite_parts', []):
            if 'name' in str(fav).lower():
                favorite_themes['Character names'] += 1
            if 'rhyme' in str(fav).lower():
                favorite_themes['Rhymes/poetry'] += 1
            if 'snark' in str(fav).lower() or 'creature' in str(fav).lower():
                favorite_themes['The Snark concept'] += 1

        for conf in eval.get('confusing_parts', []):
            if 'language' in str(conf).lower() or 'word' in str(conf).lower():
                confusing_themes['Old-fashioned language'] += 1
            if 'plot' in str(conf).lower() or 'story' in str(conf).lower():
                confusing_themes['Unclear plot'] += 1
            if 'boring' in str(conf).lower() or 'slow' in str(conf).lower():
                confusing_themes['Slow pacing'] += 1

    if favorite_themes:
        report.append("**What Kids LIKED:**\n")
        for theme, count in sorted(favorite_themes.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {theme}: {count} mentions\n")
        report.append("\n")

    if confusing_themes:
        report.append("**What Kids STRUGGLED With:**\n")
        for theme, count in sorted(confusing_themes.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {theme}: {count} mentions\n")
        report.append("\n")

    # Breakdown by Reader Archetype
    report.append("## Breakdown by Reader Archetype\n\n")

    for archetype in sorted(by_archetype.keys()):
        evals = by_archetype[archetype]
        if not evals:
            continue

        report.append(f"### {archetype} ({len(evals)} children)\n\n")

        arch_market = [e.get('market_appeal', 0) for e in evals if 'market_appeal' in e]
        arch_genre = [e.get('genre_fit', 0) for e in evals if 'genre_fit' in e]
        arch_audience = [e.get('audience_alignment', 0) for e in evals if 'audience_alignment' in e]
        arch_overall = [e.get('overall_rating', 0) for e in evals if 'overall_rating' in e]

        if arch_overall:
            report.append(f"**Average Scores:**\n")
            report.append(f"- Market Appeal: {sum(arch_market)/len(arch_market):.1f}/10\n")
            report.append(f"- Genre Fit: {sum(arch_genre)/len(arch_genre):.1f}/10\n")
            report.append(f"- Audience Alignment: {sum(arch_audience)/len(arch_audience):.1f}/10\n")
            report.append(f"- **Overall Rating: {sum(arch_overall)/len(arch_overall):.1f}/10**\n\n")

        # Sample feedback
        report.append("**Sample Feedback:**\n\n")
        for i, eval in enumerate(evals[:2], 1):
            persona = eval.get('persona', {})
            name = persona.get('name', 'Unknown')
            age = persona.get('age', '?')
            feedback = eval.get('detailed_feedback', 'No feedback')[:300]
            report.append(f"{i}. {name}, age {age}: \"{feedback}...\"\n\n")

    return ''.join(report)


def main():
    """Generate the evaluation report."""
    print("Loading evaluations...")
    evaluations = load_evaluations()
    print(f"Loaded {len(evaluations)} evaluations")

    print("Generating report...")
    report = generate_report(evaluations)

    print(f"Saving report to {OUTPUT_PATH}")
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    print("Report generated successfully!")
    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
