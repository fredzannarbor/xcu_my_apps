#!/usr/bin/env python3
"""
Evaluate "The Hunting of the Snark" from 100 diverse 9-12 year old child reader perspectives.

This script generates authentic feedback from different child reader archetypes considering:
- Modern context (video games, streaming, contemporary humor)
- Reading preferences and abilities
- Age-appropriate expectations
- 2025 children's literature standards
"""

import json
import random
import logging
from pathlib import Path
from typing import Dict, List
import sys
from dotenv import load_dotenv
import litellm

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress litellm noise
litellm.suppress_debug_info = True
litellm.set_verbose = False


# Child reader archetypes with detailed characteristics
READER_ARCHETYPES = {
    "Advanced Reader": {
        "age_range": (10, 12),
        "characteristics": [
            "Loves wordplay, puns, and clever language",
            "Enjoys poetry and appreciates rhyme schemes",
            "Likes analyzing meaning and symbolism",
            "Reads above grade level",
            "Appreciates classic literature",
            "Has patience for complex narratives",
            "Enjoys intellectual challenges in reading"
        ],
        "modern_context": [
            "Compares books to Percy Jackson, Harry Potter series",
            "May watch BookTok/BookTube content",
            "Participates in reading challenges",
            "Familiar with fantasy series with complex worldbuilding"
        ]
    },
    "Reluctant Reader": {
        "age_range": (9, 10),
        "characteristics": [
            "Prefers action-packed, fast-paced stories",
            "Likes visual elements (illustrations, comics)",
            "Shorter attention span for reading",
            "Prefers contemporary stories to classics",
            "Gets bored with slow beginnings",
            "Likes relatable, modern characters",
            "Would rather play video games or watch videos"
        ],
        "modern_context": [
            "Compares everything to Minecraft, Roblox, Fortnite",
            "Prefers graphic novels like Dog Man, Big Nate",
            "Watches YouTube gaming videos",
            "Short-form content preference (TikTok generation)"
        ]
    },
    "Grade Level": {
        "age_range": (9, 11),
        "characteristics": [
            "Reads at expected level for age",
            "Likes funny, entertaining stories",
            "Enjoys adventure with clear plots",
            "Appreciates relatable characters",
            "Likes series books (predictable structure)",
            "Prefers happy endings",
            "Enjoys school/friend stories"
        ],
        "modern_context": [
            "Reads Diary of a Wimpy Kid, Dork Diaries",
            "Likes movies/books with humor",
            "Familiar with current slang and memes",
            "Enjoys stories about school, friends, family"
        ]
    },
    "Fantasy Lover": {
        "age_range": (9, 12),
        "characteristics": [
            "Loves magical creatures and quests",
            "Enjoys imaginative worldbuilding",
            "Likes heroes and adventures",
            "Appreciates mysterious, mythical elements",
            "Enjoys collecting creature facts",
            "Likes maps, illustrations of fantasy worlds",
            "Wants clear magic systems and rules"
        ],
        "modern_context": [
            "Plays Pokemon, reads Wings of Fire",
            "Watches Avatar, How to Train Your Dragon",
            "Familiar with fantasy tropes from games",
            "Expects detailed creature descriptions"
        ]
    },
    "Poetry Enthusiast": {
        "age_range": (10, 12),
        "characteristics": [
            "Appreciates rhythm, rhyme, meter",
            "Enjoys reading aloud",
            "Likes creative language use",
            "Appreciates musicality in words",
            "Enjoys memorizing favorite verses",
            "Likes Shel Silverstein, Jack Prelutsky",
            "Appreciates humor in poetry"
        ],
        "modern_context": [
            "May write own poetry or songs",
            "Familiar with song lyrics analysis",
            "Appreciates Hamilton, musical theater",
            "Likes spoken word, poetry slams"
        ]
    }
}


def create_child_persona(archetype: str, archetype_data: Dict, index: int) -> Dict:
    """Create a detailed child reader persona."""
    age = random.randint(archetype_data["age_range"][0], archetype_data["age_range"][1])

    # Diverse names representing different backgrounds
    names = [
        "Emma", "Liam", "Olivia", "Noah", "Ava", "Mateo", "Sophia", "Lucas",
        "Isabella", "Ethan", "Mia", "Aiden", "Amelia", "Jayden", "Harper",
        "Mason", "Zoe", "Diego", "Layla", "Carter", "Chloe", "Santiago",
        "Aria", "Muhammad", "Luna", "Kai", "Aaliyah", "Chen", "Nora", "Arjun",
        "Camila", "Yuki", "Ellie", "Andre", "Sadie", "Rashid", "Maya", "Finn",
        "Leah", "Kofi", "Ella", "Jin", "Grace", "Ahmed", "Lily", "Ravi",
        "Abigail", "Jamal", "Emily", "Tariq"
    ]

    name = random.choice(names)

    # Select characteristics
    char_subset = random.sample(archetype_data["characteristics"],
                                min(4, len(archetype_data["characteristics"])))
    context_subset = random.sample(archetype_data["modern_context"],
                                  min(2, len(archetype_data["modern_context"])))

    # Additional diversity factors
    reading_locations = ["before bed", "during lunch", "on the bus", "at recess",
                        "after homework", "on weekends", "during library time"]
    favorite_subjects = ["science", "art", "math", "PE", "music", "history", "lunch"]

    return {
        "name": name,
        "age": age,
        "archetype": archetype,
        "grade": age - 5,  # Approximate grade level
        "characteristics": char_subset,
        "modern_context": context_subset,
        "reads_when": random.choice(reading_locations),
        "favorite_subject": random.choice(favorite_subjects),
        "persona_id": f"{archetype.lower().replace(' ', '_')}_{index}"
    }


def generate_evaluation_prompt(persona: Dict, book_text: str) -> str:
    """Generate a prompt for LLM to evaluate the book from child's perspective."""

    prompt = f"""You are simulating an authentic book review from a {persona['age']}-year-old child named {persona['name']} who is in {persona['grade']}th grade in 2025.

READER PROFILE - {persona['name']}:
- Age: {persona['age']} years old
- Reader Type: {persona['archetype']}
- Characteristics: {', '.join(persona['characteristics'])}
- Modern Context: {', '.join(persona['modern_context'])}
- Usually reads: {persona['reads_when']}
- Favorite subject: {persona['favorite_subject']}

BOOK TO EVALUATE:
"The Hunting of the Snark: An Agony in Eight Fits" by Lewis Carroll (1876)
- Nonsense poetry about a crew hunting a mythical creature called a Snark
- Written in rhyming verse across 8 chapters ("Fits")
- Features absurd characters with alliterative names (Bellman, Baker, Beaver, Butcher)
- Full of wordplay, made-up words, and Victorian humor

YOUR TASK:
Evaluate this book HONESTLY from {persona['name']}'s perspective as a {persona['age']}-year-old {persona['archetype']} in 2025.

Consider:
1. Would this appeal to kids like {persona['name']} who {persona['characteristics'][0].lower()}?
2. How does this compare to what kids read today? (not what kids read in 1876!)
3. Is the language accessible for {persona['age']}-year-olds in 2025?
4. Would {persona['name']} finish this book or put it down?
5. How does this compare to modern children's books, YouTube, games, etc.?

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "market_appeal": <0-10 score>,
    "genre_fit": <0-10 score>,
    "audience_alignment": <0-10 score>,
    "overall_rating": <average of three scores>,
    "detailed_feedback": "<2-3 paragraphs of honest reaction from {persona['name']}'s perspective. Use age-appropriate language. Be specific about what works and what doesn't. Compare to things kids know in 2025.>",
    "favorite_parts": ["<specific part they liked>", "<another part>"],
    "confusing_parts": ["<what didn't make sense>", "<what was boring>"],
    "recommendations": "<What would make this better for modern kids?>",
    "concerns": "<What might not work for today's children?>",
    "would_recommend_to": "<What type of kid would like this?>",
    "comparison": "<What modern book/game/show is this like?>"
}}

IMPORTANT:
- Be HONEST - most modern kids would find Victorian nonsense poetry challenging
- Use age-appropriate language and references
- Think about what {persona['age']}-year-olds actually like in 2025
- Consider attention spans, modern humor, visual media competition
- Don't be overly positive if the book wouldn't actually appeal to this child

Here are a few excerpts from the book to inform your evaluation:

{book_text[:2000]}

Remember: You're writing as if you ARE {persona['name']}, a {persona['age']}-year-old in 2025. Be authentic!"""

    return prompt


def evaluate_from_persona(persona: Dict, book_text: str, model: str = "gpt-4o-mini") -> Dict:
    """Get evaluation from one child persona using LLM."""

    prompt = generate_evaluation_prompt(persona, book_text)

    try:
        # Call litellm directly
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Higher temperature for more varied responses
            max_tokens=1500
        )

        # Extract response text
        response_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        evaluation = json.loads(response_text)

        # Add persona metadata
        evaluation["persona"] = {
            "name": persona["name"],
            "age": persona["age"],
            "archetype": persona["archetype"],
            "grade": persona["grade"],
            "persona_id": persona["persona_id"]
        }

        return evaluation

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for {persona['name']}: {e}")
        logger.error(f"Response was: {response[:500]}")
        return None
    except Exception as e:
        logger.error(f"Error evaluating from persona {persona['name']}: {e}")
        return None


def main():
    """Main evaluation workflow."""

    # Read the book
    book_path = Path("/Users/fred/xcu_my_apps/nimble/archives/Codexes2Gemini/Codexes2Gemini/data/pg19/train/train/13.txt")
    with open(book_path, 'r', encoding='utf-8') as f:
        book_text = f.read()

    # Output directory
    output_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "children_feedback.jsonl"

    # Create 100 personas (20 of each archetype)
    personas = []
    for archetype_name, archetype_data in READER_ARCHETYPES.items():
        for i in range(20):
            persona = create_child_persona(archetype_name, archetype_data, i)
            personas.append(persona)

    # Shuffle for variety
    random.shuffle(personas)

    print(f"\n{'='*80}")
    print("EVALUATING 'THE HUNTING OF THE SNARK' FROM 100 CHILD PERSPECTIVES")
    print(f"{'='*80}\n")

    # Evaluate from each persona
    evaluations = []
    successful_evals = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, persona in enumerate(personas, 1):
            print(f"\n[{idx}/100] Evaluating from perspective of:")
            print(f"  - {persona['name']}, age {persona['age']} ({persona['archetype']})")
            print(f"  - {persona['characteristics'][0]}")

            evaluation = evaluate_from_persona(persona, book_text)

            if evaluation:
                # Write to JSONL file
                f.write(json.dumps(evaluation) + '\n')
                f.flush()  # Ensure it's written immediately

                evaluations.append(evaluation)
                successful_evals += 1

                print(f"  ✓ Rating: {evaluation['overall_rating']:.1f}/10")
                print(f"    Market Appeal: {evaluation['market_appeal']}/10 | "
                      f"Genre Fit: {evaluation['genre_fit']}/10 | "
                      f"Audience Alignment: {evaluation['audience_alignment']}/10")
            else:
                print(f"  ✗ Failed to generate evaluation")

            # Progress reports every 20 evaluations
            if idx % 20 == 0:
                avg_rating = sum(e['overall_rating'] for e in evaluations) / len(evaluations) if evaluations else 0
                print(f"\n{'─'*80}")
                print(f"PROGRESS REPORT - {idx}/100 complete ({successful_evals} successful)")
                print(f"Average Rating So Far: {avg_rating:.2f}/10")
                print(f"{'─'*80}\n")

    # Final summary
    print(f"\n{'='*80}")
    print("EVALUATION COMPLETE!")
    print(f"{'='*80}")
    print(f"\nSuccessfully generated {successful_evals}/100 evaluations")
    print(f"Results saved to: {output_file}")

    if evaluations:
        # Calculate statistics
        avg_market = sum(e['market_appeal'] for e in evaluations) / len(evaluations)
        avg_genre = sum(e['genre_fit'] for e in evaluations) / len(evaluations)
        avg_audience = sum(e['audience_alignment'] for e in evaluations) / len(evaluations)
        avg_overall = sum(e['overall_rating'] for e in evaluations) / len(evaluations)

        print(f"\nAVERAGE SCORES ACROSS ALL CHILD READERS:")
        print(f"  Market Appeal:      {avg_market:.2f}/10")
        print(f"  Genre Fit:          {avg_genre:.2f}/10")
        print(f"  Audience Alignment: {avg_audience:.2f}/10")
        print(f"  Overall Rating:     {avg_overall:.2f}/10")

        # Breakdown by archetype
        print(f"\nBREAKDOWN BY READER ARCHETYPE:")
        for archetype in READER_ARCHETYPES.keys():
            archetype_evals = [e for e in evaluations if e['persona']['archetype'] == archetype]
            if archetype_evals:
                avg_arch = sum(e['overall_rating'] for e in archetype_evals) / len(archetype_evals)
                print(f"  {archetype:20s}: {avg_arch:.2f}/10 ({len(archetype_evals)} readers)")

        # Generate summary report
        summary_file = output_dir / "summary_report.json"
        summary = {
            "total_evaluations": len(evaluations),
            "average_scores": {
                "market_appeal": avg_market,
                "genre_fit": avg_genre,
                "audience_alignment": avg_audience,
                "overall_rating": avg_overall
            },
            "by_archetype": {},
            "output_file": str(output_file)
        }

        for archetype in READER_ARCHETYPES.keys():
            archetype_evals = [e for e in evaluations if e['persona']['archetype'] == archetype]
            if archetype_evals:
                summary["by_archetype"][archetype] = {
                    "count": len(archetype_evals),
                    "average_rating": sum(e['overall_rating'] for e in archetype_evals) / len(archetype_evals),
                    "market_appeal": sum(e['market_appeal'] for e in archetype_evals) / len(archetype_evals),
                    "genre_fit": sum(e['genre_fit'] for e in archetype_evals) / len(archetype_evals),
                    "audience_alignment": sum(e['audience_alignment'] for e in archetype_evals) / len(archetype_evals)
                }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary report saved to: {summary_file}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
