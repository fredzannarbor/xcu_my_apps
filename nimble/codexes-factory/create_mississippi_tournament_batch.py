"""
Create Ideation Tournament for Mississippi Miracle Books - Batch Version
Generates 128 book title ideas in multiple batches to ensure we get all titles.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from codexes.modules.batch_operations.ideation_integration import (
        generate_imprint_ideas,
        _create_ideation_prompt
    )
    from codexes.modules.batch_operations.models import TournamentConfig
    from codexes.core.llm_caller import call_model_with_prompt
    from codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model
except ImportError:
    from src.codexes.modules.batch_operations.ideation_integration import (
        generate_imprint_ideas,
        _create_ideation_prompt
    )
    from src.codexes.modules.batch_operations.models import TournamentConfig
    from src.codexes.core.llm_caller import call_model_with_prompt
    from src.codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model


def generate_ideas_batch(imprint_name, config, num_ideas, batch_num, llm_model, use_supplementary=False):
    """Generate a single batch of ideas."""
    publisher_persona = config.get("publisher_persona", {})
    publishing_focus = config.get("publishing_focus", {})
    wizard_config = config.get("wizard_configuration", {})

    persona_name = publisher_persona.get("persona_name", "Unknown Publisher")
    persona_bio = publisher_persona.get("persona_bio", "")
    editorial_philosophy = publisher_persona.get("editorial_philosophy", "")
    preferred_topics = publisher_persona.get("preferred_topics", "")

    genres = publishing_focus.get("primary_genres", wizard_config.get("genres", []))
    target_audience = publishing_focus.get("target_audience", "General readers")
    charter = wizard_config.get("charter", "")

    # Load supplementary materials if enabled
    supplementary_content = None
    max_tokens = 16000

    if use_supplementary:
        max_context = get_largest_context_model(llm_model)
        supplementary_tokens = int(max_context * 0.3)
        max_tokens = max_context - supplementary_tokens - 2000

        supplementary_content = load_imprint_supplementary_materials(
            config,
            use_supplementary=True,
            max_tokens=supplementary_tokens
        )

        if supplementary_content:
            print(f"  ✓ Loaded supplementary materials (using {max_context} token context)")

    # Build prompt
    prompt_parts = []

    if supplementary_content:
        prompt_parts.append(supplementary_content)
        prompt_parts.append("\n" + "=" * 80 + "\n")
        prompt_parts.append("The above materials provide context. Use them to inform your book concept generation.\n\n")

    prompt_parts.append(f"""Generate {num_ideas} compelling, diverse book concepts for the imprint "{imprint_name}".

IMPRINT CONTEXT:
Charter: {charter}
Primary Genres: {", ".join(genres) if isinstance(genres, list) else genres}
Target Audience: {target_audience}

PUBLISHER PERSONA:
Name: {persona_name}
Background: {persona_bio}
Editorial Philosophy: {editorial_philosophy}
Preferred Topics: {preferred_topics}

BATCH #{batch_num}: Please ensure these ideas are DISTINCT and not duplicates of previous batches.
Focus on variety across themes, settings, characters, and topics while staying true to the imprint's mission.

Generate {num_ideas} unique book concepts that would be perfect for this imprint.

For each concept, provide:
1. title: A compelling, marketable title
2. logline: A one-sentence hook (15-25 words)
3. description: 2-3 paragraph description focusing on the story, characters, and themes
4. genre: Specific genre (Picture Book - [subgenre] or Early Reader - [subgenre])
5. target_audience: Specific audience segment within K-4 (e.g., "5-7 year olds", "emerging readers", "families exploring identity")
6. word_count: Estimated word count (Picture Books: 200-800 words; Early Readers: 1000-2000 words)
7. market_appeal: Why this would sell well (2-3 sentences focusing on parent/educator appeal)
8. imprint_fit: Why this fits Mississippi Miracle Books perfectly (2-3 sentences)
9. persona_appeal_score: How much Elena Bridges would love this (0.0-1.0, be selective)

Return a JSON object with this structure:
{{
  "ideas": [
    {{
      "title": "...",
      "logline": "...",
      "description": "...",
      "genre": "...",
      "target_audience": "...",
      "word_count": 500,
      "market_appeal": "...",
      "imprint_fit": "...",
      "persona_appeal_score": 0.85
    }}
  ]
}}
""")

    prompt = "".join(prompt_parts)

    try:
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert children's book concept generator with deep knowledge of K-4 literacy, diverse representation, and empowerment narratives."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.85,
                "max_tokens": max_tokens
            }
        }

        response = call_model_with_prompt(
            model_name=llm_model,
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name=f"generate_ideas_batch_{batch_num}_{imprint_name}"
        )

        if response and "parsed_content" in response:
            ideas_data = response["parsed_content"]

            if isinstance(ideas_data, dict) and "ideas" in ideas_data:
                ideas = ideas_data["ideas"]
                print(f"  ✓ Batch {batch_num}: Generated {len(ideas)} ideas")
                return ideas
            else:
                print(f"  ✗ Batch {batch_num}: Unexpected response format")
                return []
        else:
            print(f"  ✗ Batch {batch_num}: No valid response from LLM")
            return []

    except Exception as e:
        print(f"  ✗ Batch {batch_num}: Error - {e}")
        return []


def create_mississippi_miracle_tournament():
    """Create tournament for Mississippi Miracle Books with 128 titles."""

    print("=" * 80)
    print("MISSISSIPPI MIRACLE BOOKS - IDEATION TOURNAMENT (128 TITLES)")
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
    print(f"  Publisher Persona: {config['publisher_persona']['persona_name']}")
    print(f"  Focus: {config['wizard_configuration']['charter'][:100]}...")
    print()

    # Configuration
    llm_model = "gemini/gemini-2.5-flash"
    total_ideas = 128
    batch_size = 32  # Generate 32 ideas per batch
    num_batches = total_ideas // batch_size
    use_supplementary = False  # Set to True to include supplementary materials

    print(f"Generation Plan:")
    print(f"  Total ideas needed: {total_ideas}")
    print(f"  Batch size: {batch_size}")
    print(f"  Number of batches: {num_batches}")
    print(f"  LLM model: {llm_model}")
    print(f"  Use supplementary materials: {use_supplementary}")
    print()

    # Generate ideas in batches
    all_ideas = []

    # Progress bar setup
    bar_length = 50

    for batch_num in range(1, num_batches + 1):
        # Calculate progress
        progress = batch_num / num_batches
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        print(f"\nBatch {batch_num}/{num_batches} [{bar}] {progress*100:.1f}%")
        print(f"Generating {batch_size} ideas...")

        ideas = generate_ideas_batch(
            imprint_name="Mississippi Miracle Books",
            config=config,
            num_ideas=batch_size,
            batch_num=batch_num,
            llm_model=llm_model,
            use_supplementary=use_supplementary
        )

        all_ideas.extend(ideas)

        print(f"  ✓ Batch complete: {len(ideas)} ideas generated")
        print(f"  Total ideas so far: {len(all_ideas)}/{total_ideas}")

        # Small delay between batches
        if batch_num < num_batches:
            time.sleep(2)

    print(f"✓ Generation complete: {len(all_ideas)} total ideas")
    print()

    # Display sample ideas from different batches
    print("Sample Generated Ideas (from different batches):")
    print("-" * 80)

    sample_indices = [0, 32, 64, 96, 120]  # One from each batch plus one near the end
    for idx in sample_indices:
        if idx < len(all_ideas):
            idea = all_ideas[idx]
            batch = (idx // 32) + 1
            print(f"Batch {batch}, Idea #{idx+1}: {idea.get('title', 'Untitled')}")
            print(f"  Logline: {idea.get('logline', 'No logline')}")
            print(f"  Genre: {idea.get('genre', 'Unknown')}")
            print(f"  Persona Appeal: {idea.get('persona_appeal_score', 0.0)}")
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
            "model": llm_model,
            "count": len(all_ideas),
            "batches": num_batches,
            "batch_size": batch_size,
            "ideas": all_ideas
        }, f, indent=2)

    print(f"✓ Saved {len(all_ideas)} ideas to: {ideas_file}")
    print()

    # Create tournament summary with top ideas
    top_ideas = sorted(all_ideas, key=lambda x: x.get('persona_appeal_score', 0.0), reverse=True)[:20]

    summary_file = output_dir / f"tournament_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "tournament_name": "Mississippi Miracle Books Tournament - 128 Titles",
            "imprint": "Mississippi Miracle Books",
            "created_at": datetime.now().isoformat(),
            "total_ideas": len(all_ideas),
            "batches_generated": num_batches,
            "model_used": llm_model,
            "evaluation_criteria": [
                "Alignment with imprint mission",
                "Market viability for children's books",
                "Educational value and empowerment messaging",
                "Representation and diversity",
                "Commercial appeal to educators and parents",
                "Originality and creativity"
            ],
            "config_source": str(imprint_config_path),
            "ideas_file": str(ideas_file),
            "top_20_ideas": top_ideas
        }, f, indent=2)

    print(f"✓ Saved tournament summary to: {summary_file}")
    print()

    # Display statistics
    print("=" * 80)
    print("TOURNAMENT CREATION COMPLETE")
    print("=" * 80)
    print()
    print("Statistics:")
    print(f"  Total ideas generated: {len(all_ideas)}")
    print(f"  Target: {total_ideas}")
    print(f"  Success rate: {len(all_ideas)/total_ideas*100:.1f}%")
    print(f"  Batches: {num_batches}")
    print(f"  Imprint: Mississippi Miracle Books")
    print(f"  Publisher Persona: {config['publisher_persona']['persona_name']}")
    print(f"  Focus: Children's Picture Books & Early Readers")
    print(f"  Target audience: K-4 readers (ages 5-10)")
    print()

    # Show top 5 ideas by persona appeal
    print("Top 5 Ideas by Publisher Persona Appeal:")
    print("-" * 80)
    for i, idea in enumerate(top_ideas[:5], 1):
        print(f"{i}. {idea.get('title', 'Untitled')} (Score: {idea.get('persona_appeal_score', 0.0):.2f})")
        print(f"   {idea.get('logline', 'No logline')}")
        print()

    print("Output files:")
    print(f"  Ideas: {ideas_file}")
    print(f"  Summary: {summary_file}")
    print()
    print("Next steps:")
    print("  1. Review generated ideas in the JSON files")
    print("  2. Open Ideation Dashboard (page 21) to create tournament")
    print("  3. Use Enhanced Imprint Creator batch operations for refinement")
    print()


if __name__ == "__main__":
    create_mississippi_miracle_tournament()
