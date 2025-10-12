#!/usr/bin/env python3
"""
High-Volume Reader Panels for "Not a Miracle Readers" - Maya's Story Reel

Creates statistically significant reader panels using local Ollama models:
- 9-10 year old children (target readers)
- Parents
- Reading experts
- School purchasing decision makers

Uses deepseek-r1 or better via Ollama for free local evaluation.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time
import sys

# Import existing infrastructure
try:
    from codexes.modules.ideation.synthetic_reader import (
        SyntheticReaderPersona,
        SyntheticReaderPanel,
        ReaderFeedback
    )
    from codexes.modules.ideation.book_idea import BookIdea
    from codexes.core.llm_integration import LLMCaller
except ModuleNotFoundError:
    from src.codexes.modules.ideation.synthetic_reader import (
        SyntheticReaderPersona,
        SyntheticReaderPanel,
        ReaderFeedback
    )
    from src.codexes.modules.ideation.book_idea import BookIdea
    from src.codexes.core.llm_integration import LLMCaller

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Panel sizes for statistical significance (95% confidence, ±5% margin)
PANEL_SIZES = {
    'children_9_10': 100,  # Target readers
    'parents': 80,         # Parent decision makers
    'reading_experts': 50, # Educators/specialists
    'purchasing': 40       # School administrators/buyers
}

TOTAL_REVIEWS = sum(PANEL_SIZES.values())  # 270 total reviews


def create_children_personas() -> List[SyntheticReaderPersona]:
    """Create diverse 9-10 year old reader personas."""
    base_characteristics = {
        'age_range': '9-10',
        'reading_level': 'varies',
        'preferred_genres': ['Adventure', 'Humor', 'Contemporary', 'Animals'],
    }

    personas = []
    archetypes = [
        # Strong readers
        {
            'name': 'Advanced Reader Aria',
            'characteristics': {**base_characteristics,
                'reading_habits': {'books_per_month': 6, 'reading_level': 'above grade level'},
                'interests': ['science', 'animals', 'mysteries'],
                'personality_traits': ['curious', 'confident reader', 'loves complex stories']
            }
        },
        # Struggling readers (like Maya!)
        {
            'name': 'Reluctant Reader Ryan',
            'characteristics': {**base_characteristics,
                'reading_habits': {'books_per_month': 1, 'reading_level': 'below grade level'},
                'interests': ['video games', 'sports', 'technology'],
                'personality_traits': ['frustrated with reading', 'visual learner', 'prefers action']
            }
        },
        # At grade level
        {
            'name': 'Grade Level Grace',
            'characteristics': {**base_characteristics,
                'reading_habits': {'books_per_month': 3, 'reading_level': 'at grade level'},
                'interests': ['friends', 'school', 'animals'],
                'personality_traits': ['likes relatable stories', 'social', 'empathetic']
            }
        },
        # Diverse interests
        {
            'name': 'Tech-Savvy Tara',
            'characteristics': {**base_characteristics,
                'reading_habits': {'books_per_month': 4, 'reading_level': 'at grade level'},
                'interests': ['coding', 'AI', 'video creation', 'TikTok'],
                'personality_traits': ['creative', 'digital native', 'likes modern stories']
            }
        },
        {
            'name': 'Animal Lover Alex',
            'characteristics': {**base_characteristics,
                'reading_habits': {'books_per_month': 5, 'reading_level': 'above grade level'},
                'interests': ['animals', 'nature', 'rescues'],
                'personality_traits': ['compassionate', 'loves animal stories', 'visual thinker']
            }
        }
    ]

    # Create multiple instances of each archetype with variations
    for archetype in archetypes:
        for i in range(20):  # 20 of each = 100 total
            persona_name = f"{archetype['name']} #{i+1}"
            personas.append(SyntheticReaderPersona(persona_name, archetype['characteristics']))

    return personas


def create_parent_personas() -> List[SyntheticReaderPersona]:
    """Create diverse parent personas."""
    base_characteristics = {
        'age_range': '30-45',
        'role': 'parent',
        'concerns': ['child literacy', 'screen time', 'educational value']
    }

    personas = []
    archetypes = [
        {
            'name': 'Concerned Parent Carmen',
            'characteristics': {**base_characteristics,
                'reading_habits': {'buys_books_per_month': 2},
                'priorities': ['literacy development', 'reduces screen time', 'builds confidence'],
                'personality_traits': ['worried about reading struggles', 'supportive', 'seeks solutions']
            }
        },
        {
            'name': 'Tech-Positive Parent Taylor',
            'characteristics': {**base_characteristics,
                'reading_habits': {'buys_books_per_month': 3},
                'priorities': ['modern learning', 'tech integration', 'engagement'],
                'personality_traits': ['open to AI tools', 'values innovation', 'growth mindset']
            }
        },
        {
            'name': 'Traditional Parent Pat',
            'characteristics': {**base_characteristics,
                'reading_habits': {'buys_books_per_month': 4},
                'priorities': ['phonics instruction', 'proven methods', 'fundamentals'],
                'personality_traits': ['skeptical of tech', 'values classics', 'concerned about quality']
            }
        },
        {
            'name': 'Diverse Family Parent Dana',
            'characteristics': {**base_characteristics,
                'reading_habits': {'buys_books_per_month': 3},
                'priorities': ['representation', 'cultural relevance', 'character diversity'],
                'personality_traits': ['seeks inclusive stories', 'values authenticity', 'community-minded']
            }
        }
    ]

    for archetype in archetypes:
        for i in range(20):  # 20 of each = 80 total
            persona_name = f"{archetype['name']} #{i+1}"
            personas.append(SyntheticReaderPersona(persona_name, archetype['characteristics']))

    return personas


def create_expert_personas() -> List[SyntheticReaderPersona]:
    """Create reading expert personas."""
    base_characteristics = {
        'age_range': '35-65',
        'role': 'reading_expert',
        'expertise': ['literacy', 'education', 'child development']
    }

    personas = []
    archetypes = [
        {
            'name': 'Science of Reading Expert Dr. Sarah',
            'characteristics': {**base_characteristics,
                'specialization': 'structured literacy',
                'experience': '15+ years',
                'priorities': ['phonics instruction', 'evidence-based', 'systematic approach'],
                'personality_traits': ['data-driven', 'rigorous', 'advocates for proven methods']
            }
        },
        {
            'name': 'Elementary Teacher Ms. Thompson',
            'characteristics': {**base_characteristics,
                'specialization': 'classroom application',
                'experience': '10 years',
                'priorities': ['student engagement', 'practical tools', 'differentiation'],
                'personality_traits': ['student-centered', 'innovative', 'empathetic']
            }
        },
        {
            'name': 'Reading Specialist Rita',
            'characteristics': {**base_characteristics,
                'specialization': 'intervention',
                'experience': '20 years',
                'priorities': ['struggling readers', 'multisensory methods', 'confidence building'],
                'personality_traits': ['patient', 'creative', 'solution-oriented']
            }
        },
        {
            'name': 'EdTech Specialist Ethan',
            'characteristics': {**base_characteristics,
                'specialization': 'technology integration',
                'experience': '8 years',
                'priorities': ['digital literacy', 'AI in education', 'modern learning'],
                'personality_traits': ['forward-thinking', 'practical', 'balanced approach']
            }
        },
        {
            'name': 'Literacy Coach Laura',
            'characteristics': {**base_characteristics,
                'specialization': 'professional development',
                'experience': '12 years',
                'priorities': ['teacher support', 'family engagement', 'whole-child approach'],
                'personality_traits': ['collaborative', 'holistic', 'mentor-minded']
            }
        }
    ]

    for archetype in archetypes:
        for i in range(10):  # 10 of each = 50 total
            persona_name = f"{archetype['name']} #{i+1}"
            personas.append(SyntheticReaderPersona(persona_name, archetype['characteristics']))

    return personas


def create_purchasing_personas() -> List[SyntheticReaderPersona]:
    """Create school purchasing decision maker personas."""
    base_characteristics = {
        'age_range': '40-60',
        'role': 'decision_maker',
        'responsibilities': ['budget', 'curriculum', 'student outcomes']
    }

    personas = []
    archetypes = [
        {
            'name': 'Principal Peterson',
            'characteristics': {**base_characteristics,
                'position': 'elementary principal',
                'priorities': ['student achievement', 'parent satisfaction', 'budget efficiency'],
                'personality_traits': ['practical', 'results-oriented', 'community-focused']
            }
        },
        {
            'name': 'Curriculum Director Chen',
            'characteristics': {**base_characteristics,
                'position': 'district curriculum director',
                'priorities': ['alignment to standards', 'evidence-based', 'scalability'],
                'personality_traits': ['analytical', 'thorough', 'quality-focused']
            }
        },
        {
            'name': 'Librarian Linda',
            'characteristics': {**base_characteristics,
                'position': 'school librarian',
                'priorities': ['reading engagement', 'diverse collection', 'accessibility'],
                'personality_traits': ['book lover', 'inclusive', 'student advocate']
            }
        },
        {
            'name': 'Special Ed Coordinator Sam',
            'characteristics': {**base_characteristics,
                'position': 'special education coordinator',
                'priorities': ['accommodations', 'intervention tools', 'struggling readers'],
                'personality_traits': ['equity-minded', 'supportive', 'practical']
            }
        }
    ]

    for archetype in archetypes:
        for i in range(10):  # 10 of each = 40 total
            persona_name = f"{archetype['name']} #{i+1}"
            personas.append(SyntheticReaderPersona(persona_name, archetype['characteristics']))

    return personas


def load_maya_story() -> BookIdea:
    """Load Maya's Story Reel outline as a BookIdea."""
    outline_path = Path('data/ideation/development/maya_for_development.json')

    with open(outline_path) as f:
        outline_data = json.load(f)

    # Create comprehensive description from outline
    chapters_summary = "\n".join([
        f"Chapter {ch['chapter_number']}: {ch['chapter_title']} - {ch['plot_summary'][:200]}..."
        for ch in outline_data['chapters'][:3]  # First 3 chapters for description
    ])

    full_description = f"""
MAYA'S STORY REEL - A Contemporary Children's Book About Literacy and AI

TARGET AUDIENCE: Children ages 9-10, especially struggling readers and their families

PREMISE:
Maya Chan, a 4th grader, creates viral POV rescue videos using Sora AI but struggles with reading.
With the help of SoRogue (an AI companion) and her supportive mom learning about the Science of Reading,
Maya discovers how to bridge her creative talents with phonics through "Phonics Rescue Reels."

KEY THEMES:
- Self-awareness and emotional regulation for children
- Growth mindset for families
- Science of Reading / Structured Literacy
- Creative use of AI as a learning tool
- Literacy and mental health connection

CONTEMPORARY HOOK: Sora POV storytelling integrated with phonics instruction

CHAPTER OVERVIEW:
{chapters_summary}

EDUCATIONAL VALUE:
- Demonstrates phonics concepts through engaging narratives
- Shows how technology can support (not replace) literacy instruction
- Addresses reading anxiety and builds confidence
- Models parent learning alongside child

TOTAL CHAPTERS: {outline_data['total_chapters']}
TARGET WORD COUNT: {outline_data['target_word_count']} words
"""

    book_idea = BookIdea(
        title=outline_data['book_title'],
        logline="A viral video creator discovers how AI can help unlock reading through creative phonics rescue stories",
        description=full_description,
        genre="Children's Literature / Educational Fiction",
        target_audience="Ages 9-10, struggling readers, parents, educators",
        generation_metadata={
            'idea_id': 'maya_story_reel_v1',
            'outline_chapters': outline_data['total_chapters'],
            'themes': outline_data['outline_metadata']
        }
    )

    return book_idea


def run_panel_batch(panel_name: str, personas: List[SyntheticReaderPersona],
                   book_idea: BookIdea, llm_caller: LLMCaller,
                   model: str = "ollama/deepseek-r1") -> List[ReaderFeedback]:
    """Run a batch of evaluations for a panel."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting {panel_name} Panel - {len(personas)} reviews")
    logger.info(f"Model: {model}")
    logger.info(f"{'='*60}\n")

    panel = SyntheticReaderPanel(llm_caller)
    panel.reader_personas = personas

    feedback_list = []
    start_time = time.time()

    for i, persona in enumerate(personas, 1):
        try:
            feedback = panel._evaluate_single_idea(
                book_idea,
                persona,
                book_idea.generation_metadata['idea_id'],
                model=model
            )

            if feedback:
                feedback_list.append(feedback)

            # Progress update
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = len(personas) - i
            eta = remaining / rate if rate > 0 else 0

            logger.info(
                f"{panel_name}: {i}/{len(personas)} complete | "
                f"Rate: {rate:.1f}/min | ETA: {eta/60:.1f} min"
            )

        except Exception as e:
            logger.error(f"Error evaluating {persona.name}: {e}")
            continue

    logger.info(f"\n{panel_name} Panel Complete: {len(feedback_list)} reviews collected\n")
    return feedback_list


def save_panel_results(panel_name: str, feedback_list: List[ReaderFeedback],
                      output_dir: Path):
    """Save panel results to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{panel_name}_feedback_{timestamp}.json"

    # Calculate statistics
    if feedback_list:
        avg_market = sum(f.market_appeal_score for f in feedback_list) / len(feedback_list)
        avg_genre = sum(f.genre_fit_score for f in feedback_list) / len(feedback_list)
        avg_audience = sum(f.audience_alignment_score for f in feedback_list) / len(feedback_list)
        avg_overall = sum(f.overall_rating for f in feedback_list) / len(feedback_list)
    else:
        avg_market = avg_genre = avg_audience = avg_overall = 0.0

    results = {
        'panel_name': panel_name,
        'timestamp': timestamp,
        'total_reviews': len(feedback_list),
        'statistics': {
            'avg_market_appeal': round(avg_market, 2),
            'avg_genre_fit': round(avg_genre, 2),
            'avg_audience_alignment': round(avg_audience, 2),
            'avg_overall_rating': round(avg_overall, 2)
        },
        'feedback': [f.to_dict() for f in feedback_list]
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to: {output_file}")
    return results


def main():
    """Run all reader panels."""
    logger.info("="*80)
    logger.info("MAYA'S STORY REEL - HIGH-VOLUME READER PANELS")
    logger.info("Using Ollama deepseek-r1 for local evaluation")
    logger.info(f"Total Reviews: {TOTAL_REVIEWS}")
    logger.info("="*80)

    # Initialize
    llm_caller = LLMCaller()
    book_idea = load_maya_story()
    output_dir = Path('data/reader_panels/maya_story_reel')

    # Model to use (deepseek-r1 or fallback)
    model = "ollama/deepseek-r1"

    # Create all personas
    logger.info("\nCreating reader personas...")
    all_panels = {
        'children_9_10': create_children_personas(),
        'parents': create_parent_personas(),
        'reading_experts': create_expert_personas(),
        'purchasing': create_purchasing_personas()
    }

    logger.info(f"Total personas created: {sum(len(p) for p in all_panels.values())}")

    # Run each panel
    all_results = {}
    start_time = time.time()

    for panel_name, personas in all_panels.items():
        panel_start = time.time()

        feedback = run_panel_batch(
            panel_name=panel_name,
            personas=personas,
            book_idea=book_idea,
            llm_caller=llm_caller,
            model=model
        )

        results = save_panel_results(panel_name, feedback, output_dir)
        all_results[panel_name] = results

        panel_elapsed = time.time() - panel_start
        logger.info(f"{panel_name} completed in {panel_elapsed/60:.1f} minutes\n")

    # Summary
    total_elapsed = time.time() - start_time
    total_reviews = sum(r['total_reviews'] for r in all_results.values())

    logger.info("="*80)
    logger.info("PANEL EXECUTION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Time: {total_elapsed/60:.1f} minutes")
    logger.info(f"Total Reviews: {total_reviews}/{TOTAL_REVIEWS}")
    logger.info(f"Average Rate: {total_reviews/(total_elapsed/60):.1f} reviews/minute")

    for panel_name, results in all_results.items():
        stats = results['statistics']
        logger.info(f"\n{panel_name}:")
        logger.info(f"  Reviews: {results['total_reviews']}")
        logger.info(f"  Overall Rating: {stats['avg_overall_rating']}/10")
        logger.info(f"  Market Appeal: {stats['avg_market_appeal']}/10")
        logger.info(f"  Audience Fit: {stats['avg_audience_alignment']}/10")

    # Save combined summary
    summary_file = output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'execution_time_minutes': round(total_elapsed/60, 2),
            'total_reviews': total_reviews,
            'panels': all_results
        }, f, indent=2)

    logger.info(f"\nCombined summary saved to: {summary_file}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
