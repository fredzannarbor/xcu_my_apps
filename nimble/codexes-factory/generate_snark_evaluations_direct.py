#!/usr/bin/env python3
"""
Generate 40 publishing/institutional decision-maker evaluations for "The Hunting of the Snark"
Using direct LiteLLM calls
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Direct litellm import
import litellm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Read the text content
TEXT_PATH = "/Users/fred/xcu_my_apps/nimble/archives/Codexes2Gemini/Codexes2Gemini/data/pg19/train/train/13.txt"
OUTPUT_PATH = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark/publishing_feedback.jsonl"


def read_snark_text() -> str:
    """Read The Hunting of the Snark text."""
    with open(TEXT_PATH, 'r', encoding='utf-8') as f:
        return f.read()


# Define the 40 decision maker personas
PERSONAS = {
    "School Librarian": [
        {
            "name": "Maria Chen",
            "institution": "Urban Elementary School Library",
            "focus": "Elementary collection development, 800 students, limited budget",
            "constraints": "Budget $5000/year, high circulation expectations, diverse readership"
        },
        {
            "name": "Robert Williams",
            "institution": "Middle School Media Center",
            "focus": "Middle grades reading programs, maker space integration",
            "constraints": "Competing with digital media, need high-interest texts"
        },
        {
            "name": "Diane Foster",
            "institution": "Private School Library",
            "focus": "Classical literature program, college prep emphasis",
            "constraints": "Parent expectations for 'serious' classics, traditional canon"
        },
        {
            "name": "James Martinez",
            "institution": "Rural K-8 Library",
            "focus": "Multi-grade collection, limited resources",
            "constraints": "Single copy purchases, must serve grades K-8"
        },
        {
            "name": "Sandra Kim",
            "institution": "Charter School Library",
            "focus": "Project-based learning support, interdisciplinary texts",
            "constraints": "New collection, need versatile materials"
        },
        {
            "name": "Thomas Brown",
            "institution": "Suburban Middle School",
            "focus": "Advanced reader programs, poetry units",
            "constraints": "High-achieving students, parent book challenges"
        },
        {
            "name": "Patricia O'Neill",
            "institution": "Catholic School Library",
            "focus": "Values-aligned literature, classics emphasis",
            "constraints": "Modest budget, traditional preferences"
        },
        {
            "name": "Michael Zhang",
            "institution": "STEM Magnet School",
            "focus": "Logic puzzles, math connections in literature",
            "constraints": "Science/math focus, limited humanities budget"
        },
        {
            "name": "Jennifer Lopez",
            "institution": "Arts-Focused Charter School",
            "focus": "Creative writing inspiration, illustrated books",
            "constraints": "Need visual appeal, performance tie-ins"
        },
        {
            "name": "David Thompson",
            "institution": "Title I Elementary School",
            "focus": "Struggling readers, high-interest/low-readability",
            "constraints": "Grant-funded purchases, demonstrated need"
        }
    ],
    "Curriculum Director": [
        {
            "name": "Dr. Lisa Anderson",
            "district": "Large Urban District",
            "focus": "Common Core alignment, standardized test preparation",
            "constraints": "4000+ teachers, state assessment pressure"
        },
        {
            "name": "Dr. Mark Stevens",
            "district": "Suburban School District",
            "focus": "Gifted programs, AP Literature preparation",
            "constraints": "High parental expectations, college readiness metrics"
        },
        {
            "name": "Dr. Angela Johnson",
            "district": "Rural County Schools",
            "focus": "Multi-grade classrooms, resource sharing",
            "constraints": "Limited professional development, aging materials"
        },
        {
            "name": "Dr. Richard Green",
            "district": "Charter School Network",
            "focus": "Classical education model, Great Books curriculum",
            "constraints": "Standardized across 12 schools, traditionalist board"
        },
        {
            "name": "Dr. Maria Gonzalez",
            "district": "Bilingual Education District",
            "focus": "English language learners, accessible classics",
            "constraints": "80% ELL population, scaffolding requirements"
        },
        {
            "name": "Dr. Kenneth White",
            "district": "Military Base Schools",
            "focus": "Mobile population, standardized curriculum",
            "constraints": "Transient students, national alignment needed"
        },
        {
            "name": "Dr. Susan Park",
            "district": "Progressive Independent Schools",
            "focus": "Student-centered learning, choice-based reading",
            "constraints": "Minimal required texts, student engagement priority"
        },
        {
            "name": "Dr. James Wilson",
            "district": "Catholic Diocese Schools",
            "focus": "Classical liberal arts, moral formation",
            "constraints": "Traditional canon, limited innovation budget"
        },
        {
            "name": "Dr. Rachel Cohen",
            "district": "Arts Integration District",
            "focus": "Cross-curricular connections, creative expression",
            "constraints": "Visual/performing arts integration required"
        },
        {
            "name": "Dr. Christopher Lee",
            "district": "STEM-Focused Charter Network",
            "focus": "Science/math connections in literature",
            "constraints": "Justify humanities spending, logic/reasoning focus"
        }
    ],
    "Trade Publisher": [
        {
            "name": "Sarah Mitchell",
            "company": "Penguin Random House Classics",
            "focus": "Adult classics reprints, annotated editions",
            "constraints": "Crowded market, need differentiation"
        },
        {
            "name": "John Harper",
            "company": "Scholastic Children's",
            "focus": "School market editions, curriculum tie-ins",
            "constraints": "Price point under $10, bulk sales model"
        },
        {
            "name": "Emily Rodriguez",
            "company": "Chronicle Books",
            "focus": "Illustrated editions, gift market",
            "constraints": "High production costs, boutique positioning"
        },
        {
            "name": "Daniel Kim",
            "company": "Dover Publications",
            "focus": "Affordable classics, public domain",
            "constraints": "Low margins, high volume needed"
        },
        {
            "name": "Amanda Foster",
            "company": "Norton Critical Editions",
            "focus": "Academic market, scholarly apparatus",
            "constraints": "College-level only, limited K-12 appeal"
        },
        {
            "name": "Robert Chang",
            "company": "Candlewick Press",
            "focus": "High-quality children's literature",
            "constraints": "Higher price points, bookstore-focused"
        },
        {
            "name": "Jessica Taylor",
            "company": "HarperCollins Children's",
            "focus": "Modern classics program, diverse list",
            "constraints": "Competing priorities, limited slots"
        },
        {
            "name": "Michael Brown",
            "company": "Simon & Schuster Children's",
            "focus": "Middle grade bestsellers, contemporary focus",
            "constraints": "Victorian texts hard sell, need clear hook"
        },
        {
            "name": "Laura Davis",
            "company": "Abrams Books for Young Readers",
            "focus": "Illustrated classics, art-forward editions",
            "constraints": "High production costs, $25+ retail"
        },
        {
            "name": "David Wilson",
            "company": "Macmillan Children's",
            "focus": "Curriculum adoption, educational market",
            "constraints": "Must demonstrate classroom utility"
        }
    ],
    "Literary Agent": [
        {
            "name": "Catherine Wells",
            "agency": "Curtis Brown Ltd",
            "focus": "Children's book adaptations, graphic novel rights",
            "constraints": "Need contemporary angle, illustrator partnerships"
        },
        {
            "name": "Jonathan Pierce",
            "agency": "Writers House",
            "focus": "Middle grade reimaginings, commercial fiction",
            "constraints": "Must have film/TV potential"
        },
        {
            "name": "Rebecca Santos",
            "agency": "ICM Partners",
            "focus": "Multimedia rights, brand extensions",
            "constraints": "Looking for franchise potential"
        },
        {
            "name": "Martin Fletcher",
            "agency": "Janklow & Nesbit",
            "focus": "Literary retellings, prestige projects",
            "constraints": "Need established author, critical acclaim potential"
        },
        {
            "name": "Sophia Chen",
            "agency": "The Book Group",
            "focus": "Diverse voices, contemporary adaptations",
            "constraints": "Must update for modern sensibilities"
        },
        {
            "name": "William Bennett",
            "agency": "Trident Media Group",
            "focus": "Commercial viability, mass market appeal",
            "constraints": "Need clear comp titles, sales projections"
        },
        {
            "name": "Alexandra Morgan",
            "agency": "United Talent Agency",
            "focus": "Film/TV adaptation rights, celebrity talent",
            "constraints": "Visual storytelling potential essential"
        },
        {
            "name": "Peter Harrison",
            "agency": "Sterling Lord Literistic",
            "focus": "Literary fiction, experimental retellings",
            "constraints": "Artistic merit over commercial concerns"
        },
        {
            "name": "Nicole Anderson",
            "agency": "Pippin Properties",
            "focus": "Picture book adaptations, early readers",
            "constraints": "Need age-appropriate simplification"
        },
        {
            "name": "Marcus Thompson",
            "agency": "Creative Artists Agency",
            "focus": "High-profile projects, A-list talent",
            "constraints": "Need major name attachment, large advances"
        }
    ]
}


def create_evaluation_prompt(persona_type: str, persona: Dict[str, Any], text_excerpt: str) -> str:
    """Create a detailed prompt for persona evaluation."""

    prompt = f"""You are {persona['name']}, a {persona_type} professional.

Your background:
"""

    if persona_type == "School Librarian":
        prompt += f"""- Institution: {persona['institution']}
- Focus: {persona['focus']}
- Constraints: {persona['constraints']}
"""
    elif persona_type == "Curriculum Director":
        prompt += f"""- District: {persona['district']}
- Focus: {persona['focus']}
- Constraints: {persona['constraints']}
"""
    elif persona_type == "Trade Publisher":
        prompt += f"""- Company: {persona['company']}
- Focus: {persona['focus']}
- Constraints: {persona['constraints']}
"""
    else:  # Literary Agent
        prompt += f"""- Agency: {persona['agency']}
- Focus: {persona['focus']}
- Constraints: {persona['constraints']}
"""

    prompt += f"""

You are evaluating "The Hunting of the Snark: An Agony in Eight Fits" by Lewis Carroll for potential acquisition, adoption, or representation.

BOOK DETAILS:
- Title: The Hunting of the Snark: An Agony in Eight Fits
- Author: Lewis Carroll (Charles Dodgson)
- Original Publication: 1876 (149 years old)
- Genre: Victorian nonsense poetry
- Format: Narrative poem in 8 chapters ("Fits"), 853 lines
- Target Age (original): Children (Victorian era - roughly 9-12 by modern standards)
- Status: Public domain
- Cultural Significance: Classic of English literature, companion piece to "Jabberwocky"

MARKET CONTEXT:
- Classic text with name recognition from Carroll's Alice books
- Competing against modern illustrated editions and adaptations
- Question of modern relevance vs. cultural literacy value
- Availability of free public domain versions online
- Numerous existing editions already in market

Here is an excerpt from the text (beginning of poem):

{text_excerpt}

Based on your professional role and institutional constraints, provide a comprehensive evaluation with these components:

1. MARKET APPEAL SCORE (0-10): Rate the commercial or institutional value of this work in today's market from YOUR specific perspective. Consider:
   - Current demand for Victorian classics
   - Competition from existing editions
   - Budget justification
   - Circulation/sales potential
   - Modern reader interest

2. GENRE FIT SCORE (0-10): Rate how well this work fits in the current children's poetry/literature market. Consider:
   - Quality compared to modern alternatives
   - Accessibility for target age
   - Genre positioning challenges
   - Victorian language barriers
   - "Nonsense poetry" as a category today

3. AUDIENCE ALIGNMENT SCORE (0-10): Rate how well this matches modern 9-12 year old reader needs and interests. Consider:
   - Relevance to contemporary children
   - Reading level appropriateness
   - Engagement/entertainment value
   - Cultural references accessibility
   - Competition from modern content

4. DETAILED FEEDBACK (250-400 words): Provide your professional assessment addressing:
   - Why you would or wouldn't acquire/adopt/represent this work
   - Specific strengths and weaknesses from your perspective
   - How it compares to alternatives in your portfolio/collection
   - Realistic assessment of success potential
   - Deal-breakers or must-haves for consideration

5. RECOMMENDATIONS (150-250 words): If you were to move forward, what would you need?
   - Format recommendations (illustrated, annotated, graphic novel, etc.)
   - Price point requirements
   - Marketing/positioning strategy
   - Additional content needed (introductions, study guides, etc.)
   - Partnerships or tie-ins required
   - What would make this commercially/institutionally viable

6. CONCERNS (150-250 words): What are the major obstacles or risks?
   - Market challenges
   - Accessibility issues
   - Competition concerns
   - Budget/pricing problems
   - Obsolescence risks
   - Return on investment doubts

Be REALISTIC and HONEST. Don't inflate scores because it's a "classic." Many classics struggle in modern markets. Consider your actual institutional priorities, budget constraints, and what you know about your audience/customers.

Return your response as a valid JSON object with this structure:
{{
    "evaluator_name": "{persona['name']}",
    "evaluator_role": "{persona_type}",
    "market_appeal_score": <number 0-10>,
    "genre_fit_score": <number 0-10>,
    "audience_alignment_score": <number 0-10>,
    "detailed_feedback": "<your detailed professional assessment>",
    "recommendations": "<your specific recommendations>",
    "concerns": "<your major concerns and obstacles>",
    "verdict": "<Would you acquire/adopt/represent this? One sentence.>"
}}
"""

    return prompt


def generate_evaluation(persona_type: str, persona: Dict[str, Any], text_excerpt: str, model: str = "gemini/gemini-2.0-flash-exp") -> Dict[str, Any]:
    """Generate a single evaluation using LiteLLM."""

    prompt = create_evaluation_prompt(persona_type, persona, text_excerpt)

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        # Parse the response
        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        logger.error(f"Error generating evaluation for {persona['name']}: {e}")
        return {
            "evaluator_name": persona['name'],
            "evaluator_role": persona_type,
            "error": str(e)
        }


def main():
    """Generate all 40 evaluations."""

    logger.info("Reading The Hunting of the Snark text...")
    full_text = read_snark_text()

    # Create a substantial excerpt (first 3 Fits)
    lines = full_text.split('\n')
    excerpt_lines = []
    fit_count = 0
    for line in lines:
        excerpt_lines.append(line)
        if 'Fit the' in line:
            fit_count += 1
            if fit_count >= 4:  # Include through Fit the Third
                break

    text_excerpt = '\n'.join(excerpt_lines[:400])  # First 400 lines

    logger.info(f"Using excerpt of {len(text_excerpt)} characters")

    # Generate evaluations
    all_evaluations = []
    total_count = 0

    for persona_type, personas in PERSONAS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating {persona_type} evaluations...")
        logger.info(f"{'='*60}")

        for i, persona in enumerate(personas, 1):
            logger.info(f"\n{persona_type} {i}/10: {persona['name']}")

            evaluation = generate_evaluation(persona_type, persona, text_excerpt)

            # Add metadata
            evaluation['persona_type'] = persona_type
            evaluation['persona_details'] = persona
            evaluation['generated_at'] = str(Path(__file__).name)

            all_evaluations.append(evaluation)
            total_count += 1

            # Log summary
            if 'error' not in evaluation:
                logger.info(f"  Market Appeal: {evaluation.get('market_appeal_score', 'N/A')}/10")
                logger.info(f"  Genre Fit: {evaluation.get('genre_fit_score', 'N/A')}/10")
                logger.info(f"  Audience Alignment: {evaluation.get('audience_alignment_score', 'N/A')}/10")
                logger.info(f"  Verdict: {evaluation.get('verdict', 'N/A')}")
            else:
                logger.error(f"  ERROR: {evaluation['error']}")

            # Report progress every 10 evaluations
            if total_count % 10 == 0:
                logger.info(f"\n{'*'*60}")
                logger.info(f"PROGRESS: {total_count}/40 evaluations completed")
                logger.info(f"{'*'*60}\n")

    # Save to JSONL
    logger.info(f"\nSaving all evaluations to {OUTPUT_PATH}")
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for evaluation in all_evaluations:
            f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')

    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETE: Generated {len(all_evaluations)} evaluations")
    logger.info(f"Output: {OUTPUT_PATH}")
    logger.info(f"{'='*60}")

    # Calculate summary statistics
    scores_by_type = {}
    for eval in all_evaluations:
        if 'error' not in eval:
            ptype = eval['persona_type']
            if ptype not in scores_by_type:
                scores_by_type[ptype] = {
                    'market_appeal': [],
                    'genre_fit': [],
                    'audience_alignment': []
                }
            scores_by_type[ptype]['market_appeal'].append(eval.get('market_appeal_score', 0))
            scores_by_type[ptype]['genre_fit'].append(eval.get('genre_fit_score', 0))
            scores_by_type[ptype]['audience_alignment'].append(eval.get('audience_alignment_score', 0))

    logger.info("\nSUMMARY BY PERSONA TYPE:")
    for ptype, scores in scores_by_type.items():
        if scores['market_appeal']:
            avg_market = sum(scores['market_appeal']) / len(scores['market_appeal'])
            avg_genre = sum(scores['genre_fit']) / len(scores['genre_fit'])
            avg_audience = sum(scores['audience_alignment']) / len(scores['audience_alignment'])
            logger.info(f"\n{ptype}:")
            logger.info(f"  Avg Market Appeal: {avg_market:.1f}/10")
            logger.info(f"  Avg Genre Fit: {avg_genre:.1f}/10")
            logger.info(f"  Avg Audience Alignment: {avg_audience:.1f}/10")


if __name__ == "__main__":
    main()
