#!/usr/bin/env python3
"""
Optimized high-speed reader panel execution using parallel processing.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import time

from run_maya_reader_panels import (
    create_children_personas,
    create_parent_personas,
    create_expert_personas,
    create_purchasing_personas,
    load_maya_story,
    save_panel_results,
    PANEL_SIZES
)

from src.codexes.core.llm_integration import LLMCaller
from src.codexes.modules.ideation.synthetic_reader import SyntheticReaderPanel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Add flush to all log messages
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


def evaluate_persona_batch(panel_name: str, personas: List, book_idea,
                          start_idx: int, batch_size: int,
                          model: str = "ollama/gemma3:270m") -> List:
    """Evaluate a batch of personas in parallel."""
    llm_caller = LLMCaller()
    panel = SyntheticReaderPanel(llm_caller)

    feedback_list = []
    end_idx = min(start_idx + batch_size, len(personas))

    for i in range(start_idx, end_idx):
        persona = personas[i]
        try:
            feedback = panel._evaluate_single_idea(
                book_idea,
                persona,
                book_idea.generation_metadata['idea_id'],
                model=model
            )

            if feedback:
                feedback_list.append(feedback)
                logger.info(f"{panel_name}: {i+1}/{len(personas)} - Rating: {feedback.overall_rating:.1f}/10")
        except Exception as e:
            logger.error(f"Error with {persona.name}: {e}")

    return feedback_list


def run_panel_parallel(panel_name: str, personas: List, book_idea,
                      model: str = "ollama/gemma3:270m",
                      num_workers: int = 4) -> List:
    """Run panel evaluations in parallel batches."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting {panel_name} - {len(personas)} reviews")
    logger.info(f"Model: {model}, Workers: {num_workers}")
    logger.info(f"{'='*60}")

    start_time = time.time()
    all_feedback = []

    # Calculate batch size
    batch_size = max(1, len(personas) // num_workers)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        for i in range(0, len(personas), batch_size):
            future = executor.submit(
                evaluate_persona_batch,
                panel_name,
                personas,
                book_idea,
                i,
                batch_size,
                model
            )
            futures.append(future)

        for future in as_completed(futures):
            try:
                feedback = future.result()
                all_feedback.extend(feedback)
            except Exception as e:
                logger.error(f"Batch failed: {e}")

    elapsed = time.time() - start_time
    logger.info(f"\n{panel_name} Complete: {len(all_feedback)} reviews in {elapsed:.1f}s")
    logger.info(f"Rate: {len(all_feedback)/elapsed*60:.1f} reviews/minute")

    return all_feedback


def main():
    """Run optimized parallel panel execution."""
    logger.info("="*80)
    logger.info("OPTIMIZED MAYA READER PANELS - PARALLEL EXECUTION")
    logger.info("="*80)

    # Configuration - using faster model
    model = "ollama/gemma3:270m"  # Much faster than deepseek-r1
    num_workers = 8  # Parallel workers per panel
    output_dir = Path('data/reader_panels/maya_story_reel')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load story
    book_idea = load_maya_story()

    # Create all personas
    logger.info("\nCreating personas...")
    all_panels = {
        'children_9_10': create_children_personas(),
        'parents': create_parent_personas(),
        'reading_experts': create_expert_personas(),
        'purchasing': create_purchasing_personas()
    }

    total_personas = sum(len(p) for p in all_panels.values())
    logger.info(f"Total personas: {total_personas}")
    logger.info(f"Model: {model}")
    logger.info(f"Workers per panel: {num_workers}")

    # Run all panels in parallel
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        panel_futures = {}

        for panel_name, personas in all_panels.items():
            future = executor.submit(
                run_panel_parallel,
                panel_name,
                personas,
                book_idea,
                model,
                num_workers
            )
            panel_futures[future] = panel_name

        results = {}
        for future in as_completed(panel_futures):
            panel_name = panel_futures[future]
            try:
                feedback = future.result()
                results[panel_name] = feedback

                # Save immediately
                save_panel_results(panel_name, feedback, output_dir)

            except Exception as e:
                logger.error(f"Panel {panel_name} failed: {e}")

    # Summary
    total_elapsed = time.time() - start_time
    total_reviews = sum(len(f) for f in results.values())

    logger.info("\n" + "="*80)
    logger.info("EXECUTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Total Time: {total_elapsed/60:.1f} minutes")
    logger.info(f"Total Reviews: {total_reviews}/{total_personas}")
    logger.info(f"Rate: {total_reviews/(total_elapsed/60):.1f} reviews/minute")

    for panel_name, feedback in results.items():
        if feedback:
            avg_rating = sum(f.overall_rating for f in feedback) / len(feedback)
            logger.info(f"\n{panel_name}:")
            logger.info(f"  Reviews: {len(feedback)}")
            logger.info(f"  Avg Rating: {avg_rating:.1f}/10")

    logger.info(f"\nResults saved to: {output_dir}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
