#!/usr/bin/env python3
"""
Generate detailed chapter-by-chapter outlines for Not A Miracle Readers books.
Uses supplementary materials and book synopses to create comprehensive chapter breakdowns.
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


def generate_chapter_outline(idea, config, llm_model, supplementary_content=None):
    """Generate detailed chapter-by-chapter outline for a single book idea."""

    title = idea.get('title', 'Untitled')
    word_count = idea.get('word_count', 10000)

    # Calculate chapters (aim for ~800-1200 words per chapter)
    num_chapters = max(8, min(12, word_count // 1000))

    protagonist = idea.get('protagonist', {})

    # Build prompt
    prompt_parts = []

    if supplementary_content:
        prompt_parts.append(supplementary_content)
        prompt_parts.append("\n" + "=" * 80 + "\n")
        prompt_parts.append("Use the above materials to inform character development and thematic integration.\n\n")

    prompt_parts.append(f"""Create a detailed chapter-by-chapter outline for "{title}".

BOOK DETAILS:
Title: {title}
Logline: {idea.get('logline', '')}
Setting: {idea.get('setting', '')}
Target Word Count: {word_count}
Recommended Chapters: {num_chapters}

PROTAGONIST:
Name: {protagonist.get('name', 'N/A')}
Age: {protagonist.get('age', 9)}
Ethnicity: {protagonist.get('ethnicity', 'N/A')}
Family: {protagonist.get('family', 'N/A')}
Personality: {protagonist.get('personality', 'N/A')}

PLOT STRUCTURE:
Primary Focus (A-plot): {idea.get('primary_skill_focus', '')}
Secondary Focus (B-plot): {idea.get('secondary_skill_focus', '')}
Contemporary Hook: {idea.get('contemporary_hook', '')}

SYNOPSIS:
{idea.get('synopsis', '')}

CHARACTER ARC:
{idea.get('character_arc', '')}

THEMATIC MESSAGE:
{idea.get('thematic_message', '')}

TARGET AUDIENCE APPEAL:
{idea.get('target_audience_appeal', '')}

CHAPTER OUTLINE REQUIREMENTS:

Create {num_chapters} chapters with the following for EACH chapter:

1. chapter_number: 1-{num_chapters}
2. chapter_title: Compelling, age-appropriate title that hints at content
3. estimated_word_count: Target words (total should equal ~{word_count})
4. setting_details: Where and when the chapter takes place
5. characters_present: Which characters appear in this chapter
6. plot_summary: Detailed 4-6 sentence summary of what happens
7. emotional_beats: Key emotional moments and character feelings
8. skill_focus_integration: How A-plot or B-plot themes are woven in
9. contemporary_hook_usage: How the pop culture element appears (if applicable)
10. dialogue_highlights: 2-3 key exchanges or quotes that capture the chapter
11. scene_breakdown: List of 3-5 scenes within the chapter with brief descriptions
12. chapter_purpose: What this chapter accomplishes for overall arc
13. foreshadowing_elements: Any setup for later chapters
14. cliffhanger_or_transition: How chapter ends and connects to next

STRUCTURE GUIDELINES:
- Chapters 1-3: Setup (introduce protagonist, setting, problem, contemporary hook)
- Chapters 4-6: Rising action (complications, struggles, B-plot introduction)
- Chapters 7-9: Climax building (A-plot and B-plot converge, tension peaks)
- Chapters 10-{num_chapters}: Resolution (growth, understanding, thematic payoff)

Return JSON:
{{
  "book_title": "{title}",
  "total_chapters": {num_chapters},
  "target_word_count": {word_count},
  "outline_metadata": {{
    "protagonist_name": "{protagonist.get('name', 'N/A')}",
    "primary_theme": "{idea.get('primary_skill_focus', '')}",
    "secondary_theme": "{idea.get('secondary_skill_focus', '')}",
    "contemporary_hook": "{idea.get('contemporary_hook', '')}"
  }},
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "...",
      "estimated_word_count": 900,
      "setting_details": "...",
      "characters_present": ["...", "..."],
      "plot_summary": "...",
      "emotional_beats": "...",
      "skill_focus_integration": "...",
      "contemporary_hook_usage": "...",
      "dialogue_highlights": ["...", "...", "..."],
      "scene_breakdown": [
        {{"scene_number": 1, "description": "..."}},
        {{"scene_number": 2, "description": "..."}}
      ],
      "chapter_purpose": "...",
      "foreshadowing_elements": "...",
      "cliffhanger_or_transition": "..."
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
                    "content": "You are an expert children's book editor and outliner, specializing in early chapter books for 9-10 year olds. You create detailed, scene-by-scene chapter outlines that integrate educational themes seamlessly with engaging contemporary narratives."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.7,
                "max_tokens": 16000
            }
        }

        response = call_model_with_prompt(
            model_name=llm_model,
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name=f"chapter_outline_{title.replace(' ', '_').lower()}"
        )

        if response and "parsed_content" in response:
            return response["parsed_content"]
        else:
            return None

    except Exception as e:
        print(f"  ✗ Error generating outline for '{title}': {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("Not A Miracle Readers - Chapter Outline Generator")
    print("=" * 80)
    print()

    # Load ideas
    ideas_file = Path("tournaments/not_a_miracle_readers/not_a_miracle_readers_ideas_v2_20251005_234522.json")
    print(f"Loading ideas from: {ideas_file}")

    with open(ideas_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ideas = data['ideas']
    print(f"  ✓ Loaded {len(ideas)} ideas")
    print()

    # Load config
    config_path = Path("configs/imprints/not_a_miracle_readers.json")
    print(f"Loading config: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    print(f"  ✓ Config loaded")
    print()

    # Load supplementary materials
    llm_model = "gemini/gemini-2.5-flash"
    max_context = get_largest_context_model(llm_model)
    supplementary_tokens = int(max_context * 0.2)

    print(f"Loading supplementary materials...")
    supplementary_content = load_imprint_supplementary_materials(
        config,
        use_supplementary=True,
        max_tokens=supplementary_tokens
    )

    if supplementary_content:
        print(f"  ✓ Loaded supplementary materials")
    print()

    # Generate outlines
    print(f"Generating chapter outlines for {len(ideas)} books...")
    print(f"  LLM model: {llm_model}")
    print()

    all_outlines = []

    for i, idea in enumerate(ideas, 1):
        title = idea.get('title', 'Untitled')
        print(f"\n[{i}/{len(ideas)}] Generating outline for: {title}")
        print(f"  Word count target: {idea.get('word_count', 10000)}")
        print(f"  Primary focus: {idea.get('primary_skill_focus', 'N/A')}")
        print(f"  Secondary focus: {idea.get('secondary_skill_focus', 'N/A')}")

        outline = generate_chapter_outline(
            idea=idea,
            config=config,
            llm_model=llm_model,
            supplementary_content=supplementary_content
        )

        if outline:
            all_outlines.append(outline)
            num_chapters = outline.get('total_chapters', 0)
            print(f"  ✓ Generated {num_chapters} chapter outline")
        else:
            print(f"  ✗ Failed to generate outline")

    print()
    print("=" * 80)
    print(f"GENERATION COMPLETE: {len(all_outlines)}/{len(ideas)} outlines created")
    print("=" * 80)
    print()

    # Save outlines
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("tournaments/not_a_miracle_readers/chapter_outlines")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save combined file
    combined_file = output_dir / f"all_chapter_outlines_{timestamp}.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump({
            "outlines": all_outlines,
            "count": len(all_outlines),
            "generated_at": timestamp,
            "model_used": llm_model
        }, f, indent=2)

    print(f"✓ Saved combined outlines to: {combined_file}")
    print()

    # Save individual files
    print("Saving individual outline files...")
    for outline in all_outlines:
        title = outline.get('book_title', 'untitled').lower().replace(' ', '_')
        individual_file = output_dir / f"{title}_outline.json"
        with open(individual_file, 'w', encoding='utf-8') as f:
            json.dump(outline, f, indent=2)
        print(f"  ✓ {individual_file.name}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for outline in all_outlines:
        print(f"\n{outline.get('book_title', 'Untitled')}")
        print(f"  Chapters: {outline.get('total_chapters', 0)}")
        print(f"  Target words: {outline.get('target_word_count', 0)}")
        protagonist = outline.get('outline_metadata', {}).get('protagonist_name', 'N/A')
        print(f"  Protagonist: {protagonist}")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Review outlines in: {output_dir}")
    print(f"2. Use outlines for manuscript development")
    print(f"3. Refine individual chapter outlines as needed")
    print()


if __name__ == "__main__":
    main()
