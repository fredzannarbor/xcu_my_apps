#!/usr/bin/env python3
"""
Generate ideation tournament for Not A Miracle Readers imprint.
Creates 16 book ideas with detailed synopses using supplementary materials.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from codexes.core.llm_caller import call_model_with_prompt
    from codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt
    from src.codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model


def generate_ideas_with_synopses(imprint_name, config, num_ideas, llm_model, use_supplementary=True):
    """Generate book ideas with detailed synopses."""
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
    specialization = publishing_focus.get("specialization", "")

    # Load supplementary materials
    supplementary_content = None
    max_tokens = 16000

    if use_supplementary:
        max_context = get_largest_context_model(llm_model)
        supplementary_tokens = int(max_context * 0.3)
        max_tokens = max_context - supplementary_tokens - 3000  # Reserve space for long synopses

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
        prompt_parts.append("The above materials provide critical context about Science of Reading success factors. Use this information to inform your book concepts.\n\n")

    prompt_parts.append(f"""Generate {num_ideas} compelling book concepts for the imprint "{imprint_name}".

IMPRINT CONTEXT:
Charter: {charter}
Specialization: {specialization}
Primary Genres: {", ".join(genres) if isinstance(genres, list) else genres}
Target Audience: {target_audience}

PUBLISHER PERSONA:
Name: {persona_name}
Background: {persona_bio}
Editorial Philosophy: {editorial_philosophy}
Preferred Topics: {preferred_topics}

CREATIVE REQUIREMENTS:
Target Readers: Knowledge workers living in blue states with kids in public schools OR their child (eldest, age 9-10)
Contemporary Hooks: Use current, topical situations that resonate with modern families
Settings: Each book must have a DIFFERENT, diverse setting (urban, suburban, rural, different regions)
Plot Structure:
- A Plot (Primary): Focus on ONE emotional skill, practical resource, or understanding from the supplementary materials
- B Plot (Secondary): Secondary thread about ANOTHER skill/resource/understanding from the materials
Depth: Develop each idea to SYNOPSIS LEVEL with detailed plot, character arcs, and thematic resonance

For each concept, provide:
1. title: A compelling, marketable title
2. logline: A one-sentence hook that captures the essence
3. setting: Specific, vivid setting description (must be unique for each book)
4. protagonist: Name, age (9-10), background, personality
5. primary_skill_focus: Which emotional skill, practical resource, or understanding is the A plot (from supplementary materials)
6. secondary_skill_focus: Which skill/resource/understanding is the B plot (from supplementary materials)
7. contemporary_hook: The current/topical element that makes this relevant NOW
8. synopsis: DETAILED 3-4 paragraph synopsis covering:
   - Opening situation and protagonist's challenge
   - Key plot developments and character growth
   - How the A plot and B plot interweave
   - Climax and resolution
   - Thematic resonance with Science of Reading success factors
9. character_arc: How the protagonist grows/changes
10. thematic_message: What readers (kids AND parents) will take away
11. target_audience_appeal: Why this resonates with knowledge workers in blue states / their 9-10 year old
12. word_count: Estimated word count (typically 8000-12000 for early chapter books)
13. persona_appeal_score: How much the publisher would love this (0.0-1.0)

Return a JSON object with this structure:
{{
  "ideas": [
    {{
      "title": "...",
      "logline": "...",
      "setting": "...",
      "protagonist": {{"name": "...", "age": 9, "background": "...", "personality": "..."}},
      "primary_skill_focus": "...",
      "secondary_skill_focus": "...",
      "contemporary_hook": "...",
      "synopsis": "...",
      "character_arc": "...",
      "thematic_message": "...",
      "target_audience_appeal": "...",
      "word_count": 10000,
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
                    "content": "You are an expert children's book concept generator specializing in early chapter books (ages 9-10) that help families navigate Science of Reading-based school systems. You create contemporary, emotionally resonant stories with diverse settings and authentic characters."
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
            prompt_name=f"generate_synopsis_ideas_{imprint_name}"
        )

        if response and "parsed_content" in response:
            ideas_data = response["parsed_content"]

            if isinstance(ideas_data, dict) and "ideas" in ideas_data:
                ideas = ideas_data["ideas"]
                print(f"  ✓ Generated {len(ideas)} ideas with synopses")
                return ideas
            else:
                print(f"  ⚠ Unexpected response format")
                return []
        else:
            print("  ⚠ No valid response from LLM")
            return []

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def save_ideas_to_tournament(ideas, imprint_name):
    """Save ideas to tournament directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tournament_dir = Path("tournaments") / imprint_name.lower().replace(" ", "_")
    tournament_dir.mkdir(parents=True, exist_ok=True)

    # Save ideas
    ideas_file = tournament_dir / f"{imprint_name.lower().replace(' ', '_')}_ideas_{timestamp}.json"
    with open(ideas_file, 'w', encoding='utf-8') as f:
        json.dump({"ideas": ideas, "count": len(ideas)}, f, indent=2)

    print(f"\n✓ Saved {len(ideas)} ideas to: {ideas_file}")
    return ideas_file


def main():
    print("=" * 80)
    print("Not A Miracle Readers - Ideation Tournament Generator")
    print("=" * 80)
    print()

    # Load imprint config
    config_path = Path("configs/imprints/not_a_miracle_readers.json")
    print(f"Loading config: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    print(f"  Imprint: {config['imprint']}")
    print(f"  Specialization: {config['publishing_focus']['specialization'][:100]}...")
    print()

    # Configuration
    llm_model = "gemini/gemini-2.5-flash"  # Large context window
    total_ideas = 16
    use_supplementary = True

    print(f"Generation Plan:")
    print(f"  Total ideas needed: {total_ideas}")
    print(f"  LLM model: {llm_model}")
    print(f"  Use supplementary materials: {use_supplementary}")
    print(f"  Detail level: Synopsis (detailed)")
    print()

    # Generate ideas
    print(f"Generating {total_ideas} ideas with detailed synopses...")
    print()

    ideas = generate_ideas_with_synopses(
        imprint_name="Not A Miracle Readers",
        config=config,
        num_ideas=total_ideas,
        llm_model=llm_model,
        use_supplementary=use_supplementary
    )

    if not ideas:
        print("\n✗ Failed to generate ideas. Exiting.")
        return

    print(f"\n✓ Generated {len(ideas)} ideas successfully!")
    print()

    # Display idea summaries
    print("=" * 80)
    print("IDEA SUMMARIES")
    print("=" * 80)
    for i, idea in enumerate(ideas, 1):
        print(f"\n{i}. {idea.get('title', 'Untitled')}")
        print(f"   Logline: {idea.get('logline', 'N/A')}")
        print(f"   Setting: {idea.get('setting', 'N/A')}")
        print(f"   Primary Focus: {idea.get('primary_skill_focus', 'N/A')}")
        print(f"   Secondary Focus: {idea.get('secondary_skill_focus', 'N/A')}")
        print(f"   Contemporary Hook: {idea.get('contemporary_hook', 'N/A')}")
        print(f"   Score: {idea.get('persona_appeal_score', 0.0)}")

    # Save ideas
    ideas_file = save_ideas_to_tournament(ideas, "not_a_miracle_readers")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Review generated ideas in: {ideas_file}")
    print(f"2. Create tournament using Ideation Dashboard")
    print(f"3. Run tournament evaluation to determine winner")
    print()


if __name__ == "__main__":
    main()
