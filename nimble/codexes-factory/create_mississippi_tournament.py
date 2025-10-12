"""
Create Ideation Tournament for Mississippi Miracle Books
Generates 128 book title ideas for children's picture books and early readers.
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


def create_mississippi_miracle_tournament():
    """Create tournament for Mississippi Miracle Books with 128 titles."""

    print("=" * 80)
    print("MISSISSIPPI MIRACLE BOOKS - IDEATION TOURNAMENT")
    print("=" * 80)
    print()

    # Load imprint config
    imprint_config_path = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/configs/imprints/mississippi_miracle_books.json")

    if not imprint_config_path.exists():
        print(f"ERROR: Imprint config not found at {imprint_config_path}")
        return

    with open(imprint_config_path, 'r') as f:
        config = json.load(f)

    print(f"✓ Loaded imprint config: {config['imprint']}")
    print(f"  Focus: {config['wizard_configuration']['charter'][:100]}...")
    print()

    # Create tournament configuration
    tournament_config = TournamentConfig(
        ideas_per_imprint=128,
        llm_model="anthropic/claude-sonnet-4-5-20250929",
        evaluation_criteria=[
            "Alignment with imprint mission",
            "Market viability for children's books",
            "Educational value and empowerment messaging",
            "Representation and diversity",
            "Commercial appeal to educators and parents",
            "Originality and creativity"
        ],
        auto_run=True,
        save_results=True
    )

    print("Tournament Configuration:")
    print(f"  Number of titles: {tournament_config.ideas_per_imprint}")
    print(f"  LLM model: {tournament_config.llm_model}")
    print(f"  Evaluation criteria: {len(tournament_config.evaluation_criteria)}")
    print()

    # Generate ideas
    print("Generating 128 book title ideas...")
    print("This may take several minutes...")
    print()

    ideas = generate_imprint_ideas(
        imprint_name="Mississippi Miracle Books",
        config=config,
        tournament_config=tournament_config
    )

    if not ideas:
        print("ERROR: Failed to generate ideas")
        return

    print(f"✓ Generated {len(ideas)} book title ideas")
    print()

    # Display sample ideas
    print("Sample Generated Ideas:")
    print("-" * 80)
    for i, idea in enumerate(ideas[:5], 1):
        print(f"{i}. {idea.get('title', 'Untitled')}")
        print(f"   Logline: {idea.get('logline', 'No logline')[:80]}...")
        print(f"   Genre: {idea.get('genre', 'Unknown')}")
        print()

    if len(ideas) > 5:
        print(f"... and {len(ideas) - 5} more ideas")
        print()

    # Save ideas to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("tournaments/mississippi_miracle_books")
    output_dir.mkdir(parents=True, exist_ok=True)

    ideas_file = output_dir / f"mississippi_miracle_books_ideas_{timestamp}.json"
    with open(ideas_file, 'w', encoding='utf-8') as f:
        json.dump({
            "imprint": "Mississippi Miracle Books",
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
            "tournament_name": "Mississippi Miracle Books Tournament",
            "imprint": "Mississippi Miracle Books",
            "created_at": datetime.now().isoformat(),
            "total_ideas": len(ideas),
            "model_used": tournament_config.llm_model,
            "evaluation_criteria": tournament_config.evaluation_criteria,
            "config_source": str(imprint_config_path),
            "ideas_file": str(ideas_file),
            "top_ideas": ideas[:10]  # Save top 10 for quick preview
        }, f, indent=2)

    print(f"✓ Saved tournament summary to: {summary_file}")
    print()

    # Display statistics
    print("=" * 80)
    print("TOURNAMENT CREATION COMPLETE")
    print("=" * 80)
    print()
    print("Statistics:")
    print(f"  Total ideas generated: {len(ideas)}")
    print(f"  Imprint: Mississippi Miracle Books")
    print(f"  Focus: Children's Picture Books & Early Readers")
    print(f"  Target audience: K-4 readers (ages 5-10)")
    print()
    print("Output files:")
    print(f"  Ideas: {ideas_file}")
    print(f"  Summary: {summary_file}")
    print()
    print("Next steps:")
    print("  1. Review generated ideas in the JSON files")
    print("  2. Open Ideation Dashboard to view tournament")
    print("  3. Use Enhanced Imprint Creator batch operations for further refinement")
    print()


if __name__ == "__main__":
    create_mississippi_miracle_tournament()
