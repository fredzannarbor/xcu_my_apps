#!/usr/bin/env python3
"""
Create tournament to evaluate Volume 9 middle reader adaptation approaches.
Uses codexes-factory Tournament class.
"""

import json
from pathlib import Path
from datetime import datetime

try:
    from codexes.tournaments.tournament import Tournament, TournamentConfig
except ModuleNotFoundError:
    from src.codexes.tournaments.tournament import Tournament, TournamentConfig


def create_volume_9_tournament():
    """Create tournament for middle reader adaptation ideas"""

    # Load the Volume 0 prompts to get the Volume 9 prompt
    prompts_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/warships_and_navies/prompts/nimitz_volume_0_experimental.json")

    with open(prompts_file, 'r') as f:
        prompts_data = json.load(f)

    volume_9_prompt = prompts_data["volume_0_experimental_sections"]["volume_9_middle_reader_adaptation"]["prompt"]

    # Tournament configuration
    config = TournamentConfig(
        tournament_name="Nimitz Graybook Volume 9: Middle Reader Adaptation",
        description="Evaluate different approaches for adapting the Nimitz Graybooks for middle readers (ages 9-12)",

        # Idea generation
        num_ideas=10,
        idea_generation_prompt=volume_9_prompt,
        idea_model="gemini/gemini-2.5-pro",

        # Evaluation criteria (from the prompt)
        evaluation_criteria=[
            {
                "name": "Authenticity",
                "description": "Uses real Graybook content, not fictional additions",
                "weight": 20,
                "scoring_guide": "20=Perfect fidelity to sources, 15=Mostly authentic, 10=Some fictional elements, 5=Mostly made up"
            },
            {
                "name": "Age-Appropriateness",
                "description": "Truly works for 9-12 year olds",
                "weight": 20,
                "scoring_guide": "20=Perfect for middle readers, 15=Good but some issues, 10=Too advanced or too simple, 5=Wrong age level"
            },
            {
                "name": "Educational Value",
                "description": "Teaches history, critical thinking, primary source analysis",
                "weight": 20,
                "scoring_guide": "20=Excellent learning outcomes, 15=Good educational content, 10=Some learning, 5=Minimal educational value"
            },
            {
                "name": "Engagement",
                "description": "Kids would actually read this",
                "weight": 20,
                "scoring_guide": "20=Page-turner for kids, 15=Interesting, 10=Okay, 5=Boring"
            },
            {
                "name": "Inspiration",
                "description": "Encourages dreams of service, leadership, or history careers",
                "weight": 10,
                "scoring_guide": "10=Highly inspiring, 7=Somewhat inspiring, 4=Neutral, 1=Not inspiring"
            },
            {
                "name": "Practicality",
                "description": "Can be produced at reasonable cost",
                "weight": 10,
                "scoring_guide": "10=Easy to produce, 7=Moderate complexity, 4=Difficult, 1=Too expensive/complex"
            }
        ],

        # Tournament structure
        tournament_format="round_robin",  # All ideas compete against each other
        judge_model="gemini/gemini-2.5-pro",
        rounds=3,  # Multiple rounds for consistency

        # Output
        output_dir=Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/warships_and_navies/volume_9_tournament"),
        save_intermediate_results=True
    )

    # Create tournament
    tournament = Tournament(config)

    print("=" * 80)
    print("Nimitz Graybook Volume 9 Tournament")
    print("=" * 80)
    print(f"Tournament: {config.tournament_name}")
    print(f"Evaluating: {config.num_ideas} middle reader adaptation approaches")
    print(f"Criteria: {len(config.evaluation_criteria)} dimensions, 100 points total")
    print(f"Model: {config.idea_model} (with grounding)")
    print()

    # Run tournament
    print("Phase 1: Generating 10 candidate ideas...")
    ideas = tournament.generate_ideas()
    print(f"✓ Generated {len(ideas)} ideas")
    print()

    print("Phase 2: Round-robin evaluation...")
    results = tournament.run()
    print(f"✓ Tournament complete")
    print()

    # Display results
    print("=" * 80)
    print("TOURNAMENT RESULTS")
    print("=" * 80)
    print()

    print("Final Rankings:")
    for i, result in enumerate(results["rankings"], 1):
        print(f"{i}. {result['idea_name']}")
        print(f"   Score: {result['total_score']:.1f}/100")
        print(f"   Concept: {result['concept'][:100]}...")
        print()

    print("=" * 80)
    print("TOP 3 FINALISTS")
    print("=" * 80)

    for i, finalist in enumerate(results["finalists"][:3], 1):
        print(f"\n{i}. {finalist['idea_name']} - {finalist['total_score']:.1f}/100")
        print(f"   {finalist['concept']}")
        print()

    print("=" * 80)
    print("WINNER")
    print("=" * 80)
    print(f"\n🏆 {results['winner']['approach']}")
    print(f"\nScore: {results['winner']['total_score']:.1f}/100")
    print(f"\n{results['reasoning']}")
    print()

    # Save comprehensive results
    results_file = config.output_dir / "tournament_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Full results saved: {results_file}")
    print()

    # Create markdown summary
    summary_file = config.output_dir / "VOLUME_9_RECOMMENDATION.md"
    with open(summary_file, 'w') as f:
        f.write(f"# Nimitz Graybook Volume 9: Middle Reader Adaptation\n\n")
        f.write(f"**Tournament Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"## Winning Approach: {results['winner']['approach']}\n\n")
        f.write(f"**Score:** {results['winner']['total_score']:.1f}/100\n\n")
        f.write(f"### Concept\n\n{results['winner']['full_concept']}\n\n")
        f.write(f"### Why This Won\n\n{results['reasoning']}\n\n")
        f.write(f"### Implementation Plan\n\n{results['winner']['implementation_plan']}\n\n")
        f.write(f"### Market Potential\n\n{results['winner']['market_potential']}\n\n")
        f.write(f"### Estimated Cost\n\n{results['winner']['estimated_cost']}\n\n")

        f.write(f"## Finalists\n\n")
        for i, finalist in enumerate(results["finalists"][:3], 1):
            f.write(f"### {i}. {finalist['idea_name']} ({finalist['total_score']:.1f}/100)\n\n")
            f.write(f"{finalist['concept']}\n\n")

        f.write(f"## All Candidates (Ranked)\n\n")
        for i, result in enumerate(results["rankings"], 1):
            f.write(f"{i}. **{result['idea_name']}** - {result['total_score']:.1f}/100\n")

    print(f"✓ Summary saved: {summary_file}")
    print()

    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Review tournament results and winning approach")
    print("2. Develop sample chapter using winning format")
    print("3. Test with actual middle readers (Navy families, schools)")
    print("4. Refine based on feedback")
    print("5. Produce Volume 9 as educational companion to main series")
    print()
    print("=" * 80)

    return results


if __name__ == "__main__":
    create_volume_9_tournament()
