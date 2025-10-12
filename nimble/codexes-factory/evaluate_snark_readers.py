#!/usr/bin/env python3
"""
Generate 50 reading expert evaluations of "The Hunting of the Snark"
from diverse pedagogical perspectives.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment first
load_dotenv()

try:
    from nimble_llm_caller import NimbleLLMCaller
    USE_NIMBLE = True
    print("Using nimble_llm_caller")
except ImportError:
    print("Using litellm directly")
    USE_NIMBLE = False
    import litellm

    # Set API keys from environment
    litellm.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    litellm.openai_key = os.getenv("OPENAI_API_KEY")

    class NimbleLLMCaller:
        def __init__(self, model: str):
            self.model = model

        def call(self, messages: List[Dict], **kwargs) -> str:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content

# Read the source text
SOURCE_PATH = "/Users/fred/xcu_my_apps/nimble/archives/Codexes2Gemini/Codexes2Gemini/data/pg19/train/train/13.txt"
OUTPUT_PATH = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark/educators_feedback.jsonl"

with open(SOURCE_PATH, 'r', encoding='utf-8') as f:
    snark_text = f.read()

# Define the 50 reader personas across 5 archetypes
READER_PERSONAS = []

# 1. Literature Professors (10)
lit_prof_specialties = [
    "Victorian Literature",
    "Children's Literary Canon",
    "Nonsense Poetry Studies",
    "Comparative Literature",
    "Literary Modernism",
    "Poetry Analysis",
    "Cultural Studies",
    "Narrative Theory",
    "British Literature",
    "Genre Studies"
]

for specialty in lit_prof_specialties:
    READER_PERSONAS.append({
        "archetype": "Literature Professor",
        "specialty": specialty,
        "name": f"Dr. {specialty.split()[0]} Scholar",
        "perspective": f"University-level {specialty} professor evaluating literary merit, historical significance, and academic value for students studying classic children's literature"
    })

# 2. Elementary Teachers (10)
elementary_contexts = [
    ("4th Grade", "early intermediate readers"),
    ("5th Grade", "developing critical thinking"),
    ("6th Grade", "advanced vocabulary"),
    ("Gifted Program", "accelerated learners"),
    ("ESL Classroom", "English language learners"),
    ("Urban Public School", "diverse student population"),
    ("Rural School", "limited library resources"),
    ("Montessori", "self-directed learning"),
    ("STEAM Focus", "interdisciplinary approach"),
    ("Arts Integration", "creative expression focus")
]

for context, description in elementary_contexts:
    READER_PERSONAS.append({
        "archetype": "Elementary Teacher",
        "specialty": context,
        "name": f"{context} Teacher",
        "perspective": f"Elementary educator working with {description}, evaluating classroom applicability, engagement potential, and age-appropriateness"
    })

# 3. Reading Specialists (10)
reading_specialist_focuses = [
    ("Phonics & Decoding", "phonological awareness"),
    ("Comprehension Strategies", "meaning-making skills"),
    ("Vocabulary Development", "word knowledge building"),
    ("Fluency & Expression", "reading rate and prosody"),
    ("Literary Analysis Skills", "critical reading"),
    ("Reading Motivation", "engagement and interest"),
    ("Struggling Readers", "intervention strategies"),
    ("Advanced Readers", "enrichment and challenge"),
    ("Poetry Reading", "verse comprehension"),
    ("Critical Thinking", "higher-order thinking skills")
]

for focus, description in reading_specialist_focuses:
    READER_PERSONAS.append({
        "archetype": "Reading Specialist",
        "specialty": focus,
        "name": f"{focus} Specialist",
        "perspective": f"Certified reading specialist focusing on {description}, evaluating text complexity, instructional potential, and learning challenges"
    })

# 4. Poetry Teachers (10)
poetry_teacher_approaches = [
    ("Poetic Devices", "metaphor, alliteration, rhyme"),
    ("Verse Forms", "structure and meter"),
    ("Performance Poetry", "oral interpretation"),
    ("Poetry Writing", "student composition"),
    ("Contemporary Poetry", "modern connections"),
    ("Historical Poetry", "canonical works"),
    ("Humor in Poetry", "comedic verse"),
    ("Narrative Poetry", "story through verse"),
    ("Visual Poetry", "concrete and shape poems"),
    ("Poetry Workshop", "collaborative analysis")
]

for approach, focus_area in poetry_teacher_approaches:
    READER_PERSONAS.append({
        "archetype": "Poetry Teacher",
        "specialty": approach,
        "name": f"{approach} Instructor",
        "perspective": f"Poetry educator specializing in {focus_area}, evaluating poetic quality, teaching opportunities, and student accessibility"
    })

# 5. Librarians (10)
librarian_contexts = [
    ("School Library", "K-12 collection development"),
    ("Public Library Youth Services", "community programming"),
    ("Academic Library", "special collections"),
    ("Digital Resources", "e-book collections"),
    ("Diverse Books", "representation and inclusion"),
    ("Classic Literature", "canonical works preservation"),
    ("Circulation Analysis", "reader advisory"),
    ("Summer Reading", "recreational reading programs"),
    ("Book Clubs", "group discussion facilitation"),
    ("Literacy Programs", "community literacy support")
]

for context, focus in librarian_contexts:
    READER_PERSONAS.append({
        "archetype": "Librarian",
        "specialty": context,
        "name": f"{context} Librarian",
        "perspective": f"Professional librarian managing {focus}, evaluating collection value, circulation potential, and reader appeal"
    })

def generate_evaluation(persona: Dict[str, str], text: str, llm: NimbleLLMCaller) -> Dict[str, Any]:
    """Generate a detailed evaluation from a specific persona."""

    prompt = f"""You are a **{persona['name']}** with expertise in **{persona['specialty']}**.

Your perspective: {persona['perspective']}

You are evaluating Lewis Carroll's "The Hunting of the Snark: An Agony in Eight Fits" for use with 9-12 year old students in 2025.

BOOK CONTEXT:
- Victorian nonsense poetry classic (1876)
- 853 lines across 8 "Fits" (chapters)
- Famous for invented words, absurdist logic, wordplay
- Precursor to Alice in Wonderland
- Complex vocabulary and Victorian language patterns

TEXT EXCERPT (Full text provided for reference):
{text[:3000]}
[...text continues for 853 lines total...]

As a **{persona['archetype']}** specializing in **{persona['specialty']}**, provide a comprehensive professional evaluation:

1. **Market Appeal (0-10):** Rate the educational/literary value for students today. Consider relevance, engagement potential, and contemporary applicability.

2. **Genre Fit (0-10):** Rate the quality as children's literature/poetry. Consider literary merit, age-appropriateness, and genre standards.

3. **Audience Alignment (0-10):** Rate the appropriateness for 9-12 year olds in 2025. Consider accessibility, interest level, and developmental fit.

4. **Detailed Professional Feedback (150-250 words):**
   - What are the text's greatest strengths from your professional perspective?
   - What are the most significant challenges or limitations?
   - How does it compare to contemporary children's poetry/literature?
   - What specific pedagogical or literary concerns do you have?
   - Consider: archaic language, invented words, lack of annotations, Victorian context, abstract narrative

5. **Recommendations for Modern Use (100-150 words):**
   - How would you recommend using this text with students today?
   - What supplementary materials or context would be essential?
   - What scaffolding or support would students need?
   - Are there specific teaching strategies you'd recommend?

6. **Primary Concerns (75-100 words):**
   - What are your top 3 concerns about using this text with the target age group?
   - What might prevent it from being successful in today's classrooms/libraries?

Respond in this exact JSON format:
{{
    "persona_name": "{persona['name']}",
    "archetype": "{persona['archetype']}",
    "specialty": "{persona['specialty']}",
    "market_appeal_score": [0-10 with one decimal],
    "market_appeal_justification": "[brief explanation]",
    "genre_fit_score": [0-10 with one decimal],
    "genre_fit_justification": "[brief explanation]",
    "audience_alignment_score": [0-10 with one decimal],
    "audience_alignment_justification": "[brief explanation]",
    "detailed_feedback": "[150-250 words of professional analysis]",
    "recommendations": "[100-150 words of implementation guidance]",
    "primary_concerns": "[75-100 words listing top concerns]",
    "overall_recommendation": "[HIGHLY RECOMMENDED / RECOMMENDED WITH SUPPORT / CONDITIONAL / NOT RECOMMENDED]"
}}

Provide thoughtful, nuanced evaluation from your specific professional perspective. Be honest about limitations while recognizing literary value."""

    messages = [
        {"role": "user", "content": prompt}
    ]

    response = llm.call(messages, temperature=0.7, max_tokens=2000)

    # Parse JSON response
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            response = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.find("```") + 3
            json_end = response.find("```", json_start)
            response = response[json_start:json_end].strip()

        evaluation = json.loads(response)
        return evaluation
    except json.JSONDecodeError as e:
        print(f"JSON parsing error for {persona['name']}: {e}")
        print(f"Response: {response[:500]}")
        return None

def main():
    """Generate all 50 evaluations and save to JSONL."""

    # Use GPT-4o for high-quality evaluations (fallback to gpt-4-turbo if needed)
    llm = NimbleLLMCaller(model="gpt-4o")

    evaluations = []

    print(f"Generating 50 expert evaluations of 'The Hunting of the Snark'...")
    print(f"Output: {OUTPUT_PATH}\n")

    for i, persona in enumerate(READER_PERSONAS, 1):
        print(f"[{i}/50] Generating evaluation from {persona['name']} ({persona['archetype']})...")

        try:
            evaluation = generate_evaluation(persona, snark_text, llm)

            if evaluation:
                evaluations.append(evaluation)

                # Save incrementally to JSONL
                with open(OUTPUT_PATH, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')

                # Report every 10 evaluations
                if i % 10 == 0:
                    avg_market = sum(e.get('market_appeal_score', 0) for e in evaluations) / len(evaluations)
                    avg_genre = sum(e.get('genre_fit_score', 0) for e in evaluations) / len(evaluations)
                    avg_audience = sum(e.get('audience_alignment_score', 0) for e in evaluations) / len(evaluations)

                    print(f"\n{'='*70}")
                    print(f"PROGRESS REPORT: {i}/50 evaluations complete")
                    print(f"{'='*70}")
                    print(f"Average Scores (so far):")
                    print(f"  Market Appeal:       {avg_market:.2f}/10")
                    print(f"  Genre Fit:           {avg_genre:.2f}/10")
                    print(f"  Audience Alignment:  {avg_audience:.2f}/10")
                    print(f"{'='*70}\n")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Final summary
    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY: All 50 evaluations complete!")
    print(f"{'='*70}")

    if evaluations:
        avg_market = sum(e.get('market_appeal_score', 0) for e in evaluations) / len(evaluations)
        avg_genre = sum(e.get('genre_fit_score', 0) for e in evaluations) / len(evaluations)
        avg_audience = sum(e.get('audience_alignment_score', 0) for e in evaluations) / len(evaluations)

        print(f"\nFinal Average Scores:")
        print(f"  Market Appeal:       {avg_market:.2f}/10")
        print(f"  Genre Fit:           {avg_genre:.2f}/10")
        print(f"  Audience Alignment:  {avg_audience:.2f}/10")

        # Count recommendations
        recommendations = {}
        for e in evaluations:
            rec = e.get('overall_recommendation', 'UNKNOWN')
            recommendations[rec] = recommendations.get(rec, 0) + 1

        print(f"\nOverall Recommendations:")
        for rec, count in sorted(recommendations.items(), key=lambda x: x[1], reverse=True):
            print(f"  {rec}: {count} experts ({count/len(evaluations)*100:.1f}%)")

        print(f"\nArchetype Breakdown:")
        archetypes = {}
        for e in evaluations:
            arch = e.get('archetype', 'Unknown')
            archetypes[arch] = archetypes.get(arch, 0) + 1

        for arch, count in sorted(archetypes.items()):
            print(f"  {arch}: {count} evaluations")

        print(f"\nOutput saved to: {OUTPUT_PATH}")
        print(f"Total evaluations: {len(evaluations)}")

    return evaluations

if __name__ == "__main__":
    main()
