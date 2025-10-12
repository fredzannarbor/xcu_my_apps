#!/usr/bin/env python3
"""
Generate ideation tournament for Not A Miracle Readers imprint - Version 2
Creates 16 book ideas with detailed synopses using supplementary materials.

REVISED PARAMETERS:
- Blue state urban/suburban/exurban settings (middle 30-80% income range public schools)
- Less culturally diverse protagonists, include some primary ethnicity (white) kids
- More culturally diverse McGuffins/hooks (pop culture, TikTok trends, current kid interests)
- Contemporary 2025 references
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
    """Generate book ideas with detailed synopses - REVISED VERSION."""
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
        max_tokens = max_context - supplementary_tokens - 3000

        supplementary_content = load_imprint_supplementary_materials(
            config,
            use_supplementary=True,
            max_tokens=supplementary_tokens
        )

        if supplementary_content:
            print(f"  ✓ Loaded supplementary materials (using {max_context} token context)")

    # Build REVISED prompt
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

REVISED CREATIVE REQUIREMENTS (2025):

SETTINGS - Blue State Public Schools (Middle Class Families):
- Urban/suburban/exurban areas in blue states (CA, NY, MA, IL, WA, OR, CO, etc.)
- Public schools serving middle 30-80% income range families
- Each book must have a DIFFERENT, specific setting
- Examples: Silicon Valley suburb, Brooklyn brownstone neighborhood, Portland inner-ring suburb, Denver exurban community, Boston public school district, Seattle tech corridor suburb, etc.

PROTAGONISTS - More Ethnically Diverse Mix:
- Include PRIMARY ETHNICITY protagonists (white kids from various backgrounds)
- Mix of ethnic backgrounds reflecting blue state public school demographics
- Ages 9-10, realistic family situations (two parents, single parent, blended families)
- Real contemporary kid personalities and interests

CONTEMPORARY HOOKS & McGUFFINS (2025 Pop Culture):
Use CULTURALLY DIVERSE hooks that resonate with 9-10 year olds RIGHT NOW:
- TikTok trends: BookTok, ASMR, "get ready with me", dance challenges, POV videos, storytelling trends
- Popular media: Bluey references, Inside Out 2 emotional concepts, current animated shows
- Gaming: Roblox, Minecraft builds, Among Us references, mobile games
- YouTube culture: MrBeast challenges, science experiments, craft videos
- Hobbies: slime making, friendship bracelet trends, fidget toys, collectibles (Squishmallows, Pokemon cards)
- Sports/activities: parkour, skateboarding, coding clubs, robotics, esports
- Social issues kids know: climate anxiety, screen time debates, AI in school
- Music: current kid-friendly artists, viral songs, music production apps
- Food trends: boba tea culture, viral recipes, TikTok food trends

PLOT STRUCTURE:
- A Plot (Primary): Focus on ONE emotional skill, practical resource, or understanding from supplementary materials
- B Plot (Secondary): Secondary thread about ANOTHER skill/resource/understanding
- Integrate the pop culture hook authentically into the story

TARGET READERS:
- Knowledge workers (professionals, educators, tech workers) in blue states
- Kids in well-resourced public schools (not private, not struggling districts)
- Families engaged with current culture and media
- Parents who follow educational trends and research

For each concept, provide:
1. title: Compelling, modern title (can reference pop culture)
2. logline: One-sentence hook
3. setting: Specific blue state urban/suburban/exurban location with public school context
4. protagonist: Name, age (9-10), ethnicity (include white kids!), family situation, personality
5. primary_skill_focus: Which emotional skill, practical resource, or understanding is the A plot
6. secondary_skill_focus: Which skill/resource/understanding is the B plot
7. contemporary_hook: The 2025 pop culture/trend element (TikTok, gaming, etc.)
8. synopsis: DETAILED 3-4 paragraph synopsis covering:
   - Opening with contemporary hook integrated naturally
   - Plot developments showing A and B plot interweaving
   - Character growth tied to Science of Reading themes
   - Climax and resolution
   - Thematic resonance
9. character_arc: How protagonist grows/changes
10. thematic_message: What readers (kids AND parents) take away
11. target_audience_appeal: Why this resonates with blue state knowledge worker families
12. word_count: 8000-12000 words
13. persona_appeal_score: 0.0-1.0

Return JSON:
{{
  "ideas": [
    {{
      "title": "...",
      "logline": "...",
      "setting": "...",
      "protagonist": {{"name": "...", "age": 9, "ethnicity": "...", "family": "...", "personality": "..."}},
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
                    "content": "You are an expert children's book concept generator specializing in contemporary early chapter books (ages 9-10) set in blue state public schools. You create culturally current stories featuring diverse protagonists (including white kids) with authentic 2025 pop culture hooks that help families navigate Science of Reading-based school systems."
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
            prompt_name=f"generate_synopsis_ideas_{imprint_name}_v2"
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


def save_ideas_to_tournament(ideas, imprint_name, version="v2"):
    """Save ideas to tournament directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tournament_dir = Path("tournaments") / imprint_name.lower().replace(" ", "_")
    tournament_dir.mkdir(parents=True, exist_ok=True)

    # Save ideas
    ideas_file = tournament_dir / f"{imprint_name.lower().replace(' ', '_')}_ideas_{version}_{timestamp}.json"
    with open(ideas_file, 'w', encoding='utf-8') as f:
        json.dump({"ideas": ideas, "count": len(ideas), "version": version}, f, indent=2)

    print(f"\n✓ Saved {len(ideas)} ideas to: {ideas_file}")
    return ideas_file


def main():
    print("=" * 80)
    print("Not A Miracle Readers - Ideation Tournament Generator V2")
    print("(Blue State Settings + Pop Culture Hooks + Diverse Protagonists)")
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

    print(f"Generation Plan V2:")
    print(f"  Total ideas needed: {total_ideas}")
    print(f"  LLM model: {llm_model}")
    print(f"  Use supplementary materials: {use_supplementary}")
    print(f"  Detail level: Synopsis (detailed)")
    print(f"  Settings: Blue state urban/suburban/exurban")
    print(f"  Protagonists: Diverse (including white kids)")
    print(f"  Hooks: 2025 pop culture (TikTok, gaming, trends)")
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
    print("IDEA SUMMARIES (V2 - Blue State + Pop Culture)")
    print("=" * 80)
    for i, idea in enumerate(ideas, 1):
        protagonist = idea.get('protagonist', {})
        print(f"\n{i}. {idea.get('title', 'Untitled')}")
        print(f"   Logline: {idea.get('logline', 'N/A')}")
        print(f"   Setting: {idea.get('setting', 'N/A')[:80]}...")
        print(f"   Protagonist: {protagonist.get('name', 'N/A')} ({protagonist.get('ethnicity', 'N/A')}, age {protagonist.get('age', 'N/A')})")
        print(f"   Hook: {idea.get('contemporary_hook', 'N/A')[:70]}...")
        print(f"   Primary Focus: {idea.get('primary_skill_focus', 'N/A')}")
        print(f"   Secondary Focus: {idea.get('secondary_skill_focus', 'N/A')}")
        print(f"   Score: {idea.get('persona_appeal_score', 0.0)}")

    # Save ideas
    ideas_file = save_ideas_to_tournament(ideas, "not_a_miracle_readers", "v2")

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
