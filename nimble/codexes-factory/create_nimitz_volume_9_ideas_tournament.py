"""
Create Ideation Tournament for Nimitz Graybook Volume 9 - Middle Reader Adaptation
Generates and evaluates 10 different approaches for making the Graybooks accessible to ages 9-12.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from codexes.modules.batch_operations.ideation_integration import (
        generate_imprint_ideas,
        create_ideation_tournaments
    )
    from codexes.modules.batch_operations.models import TournamentConfig
except ImportError:
    from src.codexes.modules.batch_operations.ideation_integration import (
        generate_imprint_ideas,
        create_ideation_tournaments
    )
    from src.codexes.modules.batch_operations.models import TournamentConfig


def create_volume_9_tournament():
    """Create tournament for Volume 9 middle reader adaptation approaches."""

    print("=" * 80)
    print("NIMITZ GRAYBOOK VOLUME 9 - MIDDLE READER ADAPTATION TOURNAMENT")
    print("=" * 80)
    print()

    # Load the Volume 9 prompt from our prompts file
    prompts_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/warships_and_navies/prompts/nimitz_volume_0_experimental.json")

    with open(prompts_file, 'r') as f:
        prompts_data = json.load(f)

    volume_9_data = prompts_data["volume_0_experimental_sections"]["volume_9_middle_reader_adaptation"]

    print("✓ Loaded Volume 9 adaptation prompt")
    print(f"  Description: {volume_9_data['description']}")
    print()

    # Create a minimal "imprint config" for the ideation system
    # This adapts Warships & Navies for the Volume 9 educational mission
    imprint_config = {
        "imprint": "Warships & Navies - Volume 9 Educational",
        "wizard_configuration": {
            "charter": volume_9_data["prompt"],
            "publisher_persona": "NHHC Communications Specialist & Children's Author",
            "editorial_voice": "Enthusiastic educator who respects kids' intelligence and loves naval history"
        },
        "book_type": "Middle Grade Non-Fiction (Ages 9-12)",
        "target_audience": "Middle readers, Navy families, homeschoolers, history teachers",
        "content_focus": "Primary source introduction, naval history, leadership education"
    }

    # Create tournament configuration
    tournament_config = TournamentConfig(
        ideas_per_imprint=10,  # 10 different adaptation approaches
        llm_model="gemini/gemini-2.5-pro",  # With grounding enabled
        evaluation_criteria=[
            "Authenticity: Uses real Graybook content, not fictional additions",
            "Age-Appropriateness: Truly works for 9-12 year olds",
            "Educational Value: Teaches history, critical thinking, primary source analysis",
            "Engagement: Kids would actually read this",
            "Inspiration: Encourages dreams of service, leadership, or history careers",
            "Practicality: Can be produced at reasonable cost"
        ],
        auto_run=True,
        save_results=True
    )

    print("Tournament Configuration:")
    print(f"  Number of approaches: {tournament_config.ideas_per_imprint}")
    print(f"  LLM model: {tournament_config.llm_model}")
    print(f"  Evaluation criteria: {len(tournament_config.evaluation_criteria)}")
    for i, criterion in enumerate(tournament_config.evaluation_criteria, 1):
        print(f"    {i}. {criterion}")
    print()

    # Generate ideas
    print("Generating 10 middle reader adaptation approaches...")
    print("This may take several minutes...")
    print()

    ideas = generate_imprint_ideas(
        imprint_name="Warships & Navies - Volume 9",
        config=imprint_config,
        tournament_config=tournament_config
    )

    if not ideas:
        print("ERROR: Failed to generate ideas")
        return

    print(f"✓ Generated {len(ideas)} adaptation approaches")
    print()

    # Display sample ideas
    print("Sample Generated Approaches:")
    print("-" * 80)
    for i, idea in enumerate(ideas[:5], 1):
        print(f"{i}. {idea.get('title', 'Untitled')}")
        print(f"   Concept: {idea.get('logline', 'No description')[:120]}...")
        print(f"   Target: {idea.get('target_audience', 'Unknown')}")
        print()

    if len(ideas) > 5:
        print(f"... and {len(ideas) - 5} more approaches")
        print()

    # Save ideas to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("tournaments/nimitz_volume_9")
    output_dir.mkdir(parents=True, exist_ok=True)

    ideas_file = output_dir / f"volume_9_adaptation_ideas_{timestamp}.json"
    with open(ideas_file, 'w', encoding='utf-8') as f:
        json.dump({
            "volume": "Nimitz Graybook Volume 9: Middle Reader Adaptation",
            "generated_at": datetime.now().isoformat(),
            "model": tournament_config.llm_model,
            "count": len(ideas),
            "ideas": ideas
        }, f, indent=2)

    print(f"✓ Saved ideas to: {ideas_file}")
    print()

    # Create tournament summary
    summary_file = output_dir / f"tournament_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "tournament_name": "Nimitz Volume 9: Middle Reader Adaptation Tournament",
            "volume": "Volume 9",
            "created_at": datetime.now().isoformat(),
            "total_ideas": len(ideas),
            "model_used": tournament_config.llm_model,
            "evaluation_criteria": tournament_config.evaluation_criteria,
            "prompt_source": str(prompts_file),
            "ideas_file": str(ideas_file),
            "top_ideas": ideas[:5]  # Save top 5 for quick preview
        }, f, indent=2)

    print(f"✓ Saved tournament summary to: {summary_file}")
    print()

    # Create markdown report
    md_file = output_dir / f"VOLUME_9_TOURNAMENT_RESULTS_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Nimitz Graybook Volume 9: Middle Reader Adaptation Tournament\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Model:** {tournament_config.llm_model}\n\n")
        f.write(f"## Mission\n\n")
        f.write("Create a middle reader adaptation (ages 9-12) that:\n")
        f.write("- Makes primary sources exciting and accessible\n")
        f.write("- Teaches historical thinking and document analysis\n")
        f.write("- Inspires interest in Navy, leadership, and service\n")
        f.write("- Works as classroom resource and independent reading\n\n")

        f.write(f"## Evaluation Criteria\n\n")
        for i, criterion in enumerate(tournament_config.evaluation_criteria, 1):
            f.write(f"{i}. {criterion}\n")
        f.write("\n")

        f.write(f"## Top 5 Adaptation Approaches\n\n")
        for i, idea in enumerate(ideas[:5], 1):
            f.write(f"### {i}. {idea.get('title', 'Untitled')}\n\n")
            f.write(f"**Concept:** {idea.get('logline', 'No description')}\n\n")
            f.write(f"**Target Audience:** {idea.get('target_audience', 'Ages 9-12')}\n\n")
            if 'description' in idea:
                f.write(f"**Description:** {idea.get('description')}\n\n")
            f.write("---\n\n")

        if len(ideas) > 5:
            f.write(f"## All {len(ideas)} Generated Ideas\n\n")
            for i, idea in enumerate(ideas, 1):
                f.write(f"{i}. **{idea.get('title', 'Untitled')}**\n")

    print(f"✓ Saved markdown report to: {md_file}")
    print()

    # Display statistics
    print("=" * 80)
    print("TOURNAMENT CREATION COMPLETE")
    print("=" * 80)
    print()
    print("Statistics:")
    print(f"  Total approaches generated: {len(ideas)}")
    print(f"  Volume: Nimitz Graybook Volume 9")
    print(f"  Focus: Middle Reader Adaptation (Ages 9-12)")
    print(f"  Format: Educational companion to Volumes 0-8")
    print()
    print("Output files:")
    print(f"  Ideas JSON: {ideas_file}")
    print(f"  Summary: {summary_file}")
    print(f"  Report: {md_file}")
    print()
    print("Next steps:")
    print("  1. Review generated approaches in the markdown report")
    print("  2. Select winning approach (top-ranked by tournament)")
    print("  3. Develop sample chapter using winning format")
    print("  4. Test with actual middle readers")
    print("  5. Refine and produce Volume 9")
    print()
    print("=" * 80)


if __name__ == "__main__":
    create_volume_9_tournament()
