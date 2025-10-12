#!/usr/bin/env python3
"""
Generate 128 diverse book ideas for Not a Miracle Readers imprint
Following the ideation spec reverse-engineered from Maya's Story Reel
"""

import json
import os
from pathlib import Path

import logging
import litellm

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure litellm
litellm.telemetry = False

# Load ideation spec
SPEC_PATH = Path("configs/ideation_specs/not_a_miracle_readers_spec.json")
with open(SPEC_PATH, 'r') as f:
    SPEC = json.load(f)

# Output directory
OUTPUT_DIR = Path("data/ideation/not_a_miracle_readers/ideas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Contemporary hooks to rotate through
CONTEMPORARY_HOOKS = [
    "AI-powered video creation (Sora-style POV videos)",
    "Podcast production and audio storytelling",
    "Game design and Roblox modding",
    "Digital art and Procreate animation",
    "Age-appropriate social media content creation",
    "Coding and robotics (Scratch, Lego Mindstorms)",
    "Music production and GarageBand remixing",
    "Photography and visual storytelling (iPhone cinematography)",
    "Minecraft world building and redstone engineering",
    "Science experiments and YouTube channel hosting",
    "Stop-motion animation and claymation",
    "Comic book creation and webcomics",
    "Recipe development and cooking TikTok videos",
    "Nature documentation and wildlife photography",
    "STEM challenges and engineering projects",
    "Dance choreography and performance videos"
]

# Literacy skills to cover
LITERACY_SKILLS = [
    "Consonant blends (bl, cr, st, etc.)",
    "Vowel teams (ai, ea, oa, etc.)",
    "Silent letters (kn, wr, mb, etc.)",
    "R-controlled vowels (ar, er, ir, or, ur)",
    "Diphthongs (oi, oy, ou, ow)",
    "Phonemic awareness (sound manipulation)",
    "Syllable types and division",
    "Morphology (prefixes, suffixes, roots)",
    "Reading fluency (phrasing and expression)",
    "Vocabulary development (context clues)",
    "Reading comprehension (visualization)",
    "Reading comprehension (questioning strategies)",
    "Reading comprehension (summarizing)",
    "Reading comprehension (inferring)",
    "Written expression (sentence structure)",
    "Written expression (organization and planning)"
]

# Diverse protagonist backgrounds
PROTAGONIST_BACKGROUNDS = [
    {"ethnicity": "African American", "family": "Single mom household", "location": "Urban Atlanta"},
    {"ethnicity": "Latinx", "family": "Two-parent immigrant family", "location": "Rural Texas"},
    {"ethnicity": "Asian American", "family": "Grandparent-raised", "location": "Suburban California"},
    {"ethnicity": "White", "family": "Two moms", "location": "Small town Maine"},
    {"ethnicity": "Native American", "family": "Extended family on reservation", "location": "Arizona reservation"},
    {"ethnicity": "Middle Eastern", "family": "Recent refugee family", "location": "Urban Michigan"},
    {"ethnicity": "Mixed race (Black/White)", "family": "Blended family (step-siblings)", "location": "Suburban Maryland"},
    {"ethnicity": "South Asian", "family": "Two dads", "location": "Urban Seattle"},
    {"ethnicity": "Pacific Islander", "family": "Large multi-generational home", "location": "Hawaii"},
    {"ethnicity": "Latinx", "family": "Single dad household", "location": "Urban Chicago"},
    {"ethnicity": "White", "family": "Foster care placement", "location": "Rural Kentucky"},
    {"ethnicity": "African American", "family": "Two-parent middle-class", "location": "Suburban New Jersey"},
    {"ethnicity": "Asian American (Vietnamese)", "family": "Single mom, aunt helps", "location": "Urban Houston"},
    {"ethnicity": "White", "family": "Farm family (mom, dad, siblings)", "location": "Rural Iowa"},
    {"ethnicity": "Latinx (Puerto Rican)", "family": "Grandmother-raised", "location": "Urban New York"},
    {"ethnicity": "Mixed race (Asian/White)", "family": "Two moms, adopted", "location": "Suburban Oregon"}
]

def generate_idea_batch(start_idx: int, batch_size: int = 8, model: str = "xai/grok-4-latest"):
    """Generate a batch of book ideas using the spec"""

    # Prepare the generation prompt
    prompt = f"""You are a children's book editor generating diverse book ideas for the "Not a Miracle Readers" imprint.

IMPRINT MISSION: Create engaging middle-grade fiction (ages 9-12) that seamlessly integrates Science of Reading principles with contemporary hooks and character-driven narratives.

REQUIREMENTS FROM SPEC:
1. Protagonist: 9-10 years old, diverse background, specific reading struggle
2. Contemporary Hook: Current 2025 cultural phenomenon kids find exciting
3. Literacy Skill: One specific Science of Reading-aligned skill
4. Creative Integration: How protagonist's passion naturally teaches the skill
5. Quirky Setting: Realistic + imaginative spaces
6. Character Arc: Struggle → frustration → breakthrough → mastery → teaching others
7. Unique Element: One memorable twist

DIVERSITY REQUIREMENTS:
- Varied ethnicities, family structures, socioeconomic backgrounds
- Different learning profiles (dyslexia, ADHD, ELL, late bloomer, specific gaps)
- Geographic diversity (not just coastal cities)
- Interest diversity (STEM, arts, sports, nature, tech, making)

GENERATE {batch_size} BOOK IDEAS (Ideas #{start_idx + 1} to #{start_idx + batch_size})

For each idea, provide:
- Title (working title)
- Protagonist (name, age, background, specific struggle)
- Contemporary Hook (from 2025 cultural landscape)
- Literacy Skill (specific SoR-aligned skill)
- Creative Integration (how passion teaches skill)
- Setting (primary + secondary locations)
- Character Arc (emotional/skill growth)
- Unique Element (memorable twist)
- Pitch (one compelling paragraph)

Return as JSON array with this structure:
[
  {{
    "idea_number": {start_idx + 1},
    "title": "Working Title",
    "protagonist": {{
      "name": "First Last",
      "age": 10,
      "background": "Brief background (ethnicity, family, location)",
      "struggle": "Specific reading challenge"
    }},
    "contemporary_hook": "Current cultural element",
    "literacy_skill": "Specific SoR skill",
    "creative_integration": "How passion teaches skill",
    "setting": {{
      "primary": "Realistic location",
      "secondary": "Imaginative/unique space"
    }},
    "character_arc": "Growth journey",
    "unique_element": "Memorable twist",
    "pitch": "One paragraph pitch"
  }}
]

IMPORTANT:
- Ensure diversity across all {batch_size} ideas (different hooks, skills, backgrounds)
- Make contemporary hooks genuinely current for 2025
- Keep protagonist voices authentic to 9-10 year olds
- Balance educational rigor with engaging storytelling
"""

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,  # Higher creativity for idea generation
            response_format={"type": "json_object"}
        )

        # Parse response
        raw_content = response.choices[0].message.content
        ideas_data = json.loads(raw_content)

        # Handle both array and object responses
        if isinstance(ideas_data, dict):
            if "ideas" in ideas_data:
                ideas = ideas_data["ideas"]
            else:
                # Wrap single idea in array
                ideas = [ideas_data]
        else:
            ideas = ideas_data

        return ideas

    except Exception as e:
        logger.error(f"Error generating ideas batch {start_idx}: {e}")
        return []

def main():
    """Generate all 128 ideas in batches"""

    logger.info("Starting generation of 128 Not a Miracle Readers ideas")

    all_ideas = []
    batch_size = 8
    total_batches = 128 // batch_size  # 16 batches

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size

        logger.info(f"Generating batch {batch_num + 1}/{total_batches} (Ideas {start_idx + 1}-{start_idx + batch_size})")

        batch_ideas = generate_idea_batch(start_idx, batch_size)

        if batch_ideas:
            all_ideas.extend(batch_ideas)

            # Save intermediate progress
            progress_file = OUTPUT_DIR / f"ideas_progress_{len(all_ideas)}.json"
            with open(progress_file, 'w') as f:
                json.dump({
                    "total_generated": len(all_ideas),
                    "target": 128,
                    "ideas": all_ideas
                }, f, indent=2)

            logger.info(f"  ✓ Generated {len(batch_ideas)} ideas (Total: {len(all_ideas)}/128)")
        else:
            logger.error(f"  ✗ Failed to generate batch {batch_num + 1}")

    # Save final output
    if len(all_ideas) > 0:
        output_file = OUTPUT_DIR / "all_128_ideas.json"
        with open(output_file, 'w') as f:
            json.dump({
                "imprint": "Not a Miracle Readers",
                "spec_version": "1.0",
                "total_ideas": len(all_ideas),
                "generation_date": "2025-10-10",
                "ideas": all_ideas
            }, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info(f"GENERATION COMPLETE!")
        logger.info(f"Total ideas generated: {len(all_ideas)}/128")
        logger.info(f"Output file: {output_file}")
        logger.info(f"{'='*60}\n")

        # Create summary
        summary_file = OUTPUT_DIR / "ideas_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Not a Miracle Readers - 128 Book Ideas\n\n")
            f.write(f"**Generated:** 2025-10-10\n")
            f.write(f"**Spec Version:** 1.0\n")
            f.write(f"**Total Ideas:** {len(all_ideas)}\n\n")
            f.write("---\n\n")

            for idea in all_ideas:
                f.write(f"## Idea #{idea.get('idea_number', 'N/A')}: {idea.get('title', 'Untitled')}\n\n")
                f.write(f"**Protagonist:** {idea.get('protagonist', {}).get('name', 'N/A')} ({idea.get('protagonist', {}).get('age', 'N/A')})\n\n")
                f.write(f"**Background:** {idea.get('protagonist', {}).get('background', 'N/A')}\n\n")
                f.write(f"**Struggle:** {idea.get('protagonist', {}).get('struggle', 'N/A')}\n\n")
                f.write(f"**Contemporary Hook:** {idea.get('contemporary_hook', 'N/A')}\n\n")
                f.write(f"**Literacy Skill:** {idea.get('literacy_skill', 'N/A')}\n\n")
                f.write(f"**Pitch:** {idea.get('pitch', 'N/A')}\n\n")
                f.write("---\n\n")

        logger.info(f"Summary file created: {summary_file}")

    else:
        logger.error("No ideas were generated!")

if __name__ == "__main__":
    main()
