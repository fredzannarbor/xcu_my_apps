import json
import logging
import os
import argparse
import uuid
from pathlib import Path

from openai import OpenAI
from typing import Dict, List, Any
import random
import sys
from collections import defaultdict
from dotenv import load_dotenv
from src.ideas.BookClasses.IdeaGeneratingMachine import ContinuousIdeaGenerator
from src.ideas.BookClasses.Model2BookIdeas import Models2BookIdeas
from src.ideas.Tournament import Tournament
# Import utilities from the companion file
from vibe_oral_history_utilities import load_json_file, save_json_file, save_markdown_file, read_stipulated_facts
import pandas as pd

import streamlit as st
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
# Load environment variables
load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    logger.error("XAI_API_KEY not found in .env file")
    raise ValueError("XAI_API_KEY is required")

# Initialize OpenAI-compatible client for xAI API
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

quote_tracking_data = []

def generate_quote(prompt, tone, word_count_range, speaker, event, retry_enabled=False, examples_content="", writing_model_name="grok-3-fast-beta"):
    """Generate a single quote using the xAI API with optional retry logic for word count."""
    word_min, word_max = map(int, word_count_range.split('-'))
    target_min = (word_min + word_max) // 2  # Aim for at least the midterm value if retry is enabled
    full_prompt = (
        f"Generate an oral history quote for a novelized oral history project. "
        f"Speaker: {speaker}, reflecting on {event}. "
        f"Tone: {tone}, insightful, pithy, first-person perspective. "
        f"Content: {prompt} "
        f"Word count: between {word_min} and {word_max} words. "
        f"Stay faithful to provided facts, using creative liberties for emotional depth. "
        f"The quote should be tightly edited and suitable for book publication. "
        f"The quote should sound like a highlight of an interview, the most quotable, interesting, and informative thing the person had to say on the topic. "
        f"The primary focus of the quote should be the external event being described with the speaker's experience secondary."
        f"Avoid overly conversational language, such as fillers like 'well,' 'you know,' 'I mean,' 'look,' 'I'll tell ya,' 'I gotta say,' 'ya know,' and similar phrases. "
        f"Use varied sentence structures. "
        f"Do not use contractions. "
        f"Do not directly address the listener. "
        f"Be concise and avoid unnecessary repetition. "
        f"Speakers who are normal humans should sound like our contemporaries, with a few exceptions. For example, they should not make reference to modern events or concepts unless specified. Their value system should be consistent with historical or contextual knowledge. "
        f"Speakers who are extraordinary beings should sound like a mix between formal, archaic tones and contemporary speech if appropriate to the context."
        f"Speakers who are anthropomorphized entities should sound like normal humans albeit with a tightly focused perspective on the world."
    )

    # Append examples to the prompt if provided
    if examples_content:
        full_prompt += f"\nFollow the style and tone of the following examples for guidance:\n{examples_content}"

    params = {
        "tone": tone,
        "word_count_range": word_count_range,
        "word_min": word_min,
        "word_max": word_max,
        "model": writing_model_name,
        "temperature": 0.8,  # Hardcoded as per current script
        "max_tokens": word_max * 2,
        "retry_enabled": retry_enabled
    }

    try:
        if retry_enabled:
            for attempt in range(3):  # Retry up to 3 times to meet target minimum if enabled
                response = client.chat.completions.create(
                    model=writing_model_name,  # Adjust model name as per xAI API
                    messages=[
                        {"role": "system",
                         "content": "You are {writing_model_name}, a helpful AI for generating creative, faithful narratives."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=word_max * 2,  # Approximate token count
                    temperature=0.8
                )
                quote = response.choices[0].message.content.strip()
                word_count = len(quote.split())
                if word_count >= target_min:
                    break
                logger.info(f"Quote for {speaker} retrying: {word_count} words below target {target_min}")
        else:
            response = client.chat.completions.create(
                model=writing_model_name,  # Adjust model name as per xAI API
                messages=[
                    {"role": "system",
                     "content": "You are Grok 3, a helpful AI for generating creative, faithful narratives."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=word_max * 2,  # Approximate token count
                temperature=0.8
            )
            quote = response.choices[0].message.content.strip()
            word_count = len(quote.split())

        if word_count < word_min or word_count > word_max:
            logger.warning(f"Quote for {speaker} ({event}) is {word_count} words, outside {word_min}-{word_max}")
        print(quote)

        # Append data to tracking list
        quote_tracking_data.append({
            "Speaker": speaker,
            "Event": event,
            "Prompt": full_prompt,
            "Parameters": str(params),  # Convert to string for CSV readability
            "Response": quote,
            "Word_Count": word_count,
            "Within_Range": word_min <= word_count <= word_max
        })

        return quote
    except Exception as e:
        logger.error(f"Failed to generate quote for {speaker} ({event}): {e}")
        error_response = f"[Error generating quote for {speaker}]"

        # Track error cases as well
        quote_tracking_data.append({
            "Speaker": speaker,
            "Event": event,
            "Prompt": full_prompt,
            "Parameters": str(params),
            "Response": error_response,
            "Word_Count": 0,
            "Within_Range": False
        })
        return error_response

def create_markdown_draft(high_level_spec, detailed_outline, section_limit=None, retry_quotes=False, examples_content=""):
    """Create a Markdown draft from the high-level spec and detailed outline with word count monitoring."""
    markdown_lines = []
    metadata_lines = []
    quote_counts = defaultdict(int)  # Track quote types
    total_word_count = 0
    section_count = 0

    # Non-printing Metadata
    metadata_lines.append(f"# {high_level_spec['title']}\n")
    metadata_lines.append(f"**{high_level_spec['description']}**\n")
    metadata_lines.append(f"**Interviewer: {high_level_spec['documentarian']['name']}**  \n")
    metadata_lines.append(
        f"{high_level_spec['documentarian']['role']} Speaking in a {high_level_spec['documentarian']['tone']} tone, "
        f"they guide us through the voices of those who witnessed the events.\n"
    )
    markdown_lines.append(f"**Word Count Target**: {high_level_spec['word_count_target']}\n")
    # Printing Metadata
    markdown_lines.append(f"# {high_level_spec['title']}\n")
    markdown_lines.append(f"**{high_level_spec['description']}**\n")

    # Interviewees Overview
    markdown_lines.append("## Cast of Characters\n")
    for category in high_level_spec['interviewees']['categories']:
        markdown_lines.append(f"- **{category['type']}**: {category['role']} (e.g., {', '.join(category['examples'])})")
    metadata_lines.append(f"\nTotal: {high_level_spec['interviewees']['total_count']}\n")

    # Chapters
    for chapter in detailed_outline['chapters']:
        markdown_lines.append(f"\n## Chapter: {chapter['title']}\n")
        markdown_lines.append(f"**Description**: {chapter['description']}\n")
        markdown_lines.append(f"**Stipulated Facts References**: {', '.join(chapter['stipulated_facts'])}\n")
        markdown_lines.append(f"**Word Count**: {chapter['word_count']}\n")

        # Scenes
        markdown_lines.append("\n### Scenes\n")
        for scene in chapter['scenes']:
            markdown_lines.append(f"- {scene}")
        markdown_lines.append("\n")

        chapter_word_count = 0  # Track word count for this chapter
        # Speakers and Quotes
        for speaker in chapter['speakers']:
            if section_limit is not None and section_count >= section_limit:
                break  # Stop adding sections if the limit is reached
            markdown_lines.append(f"### {speaker['name']}\n")
            speaker_word_count = 0  # Track word count for this speaker
            for quote in speaker['quotes']:
                markdown_lines.append(f"\n**{quote['event']}**  \n")
                markdown_lines.append(f"*Quote ({quote['type'].capitalize()})*\n")

                # Generate quote with adjusted ranges for higher word counts
                word_count_range_dict = {
                    'sentence': '40-50',    # Increased minimum from 20
                    'paragraph': '100-300', # Increased minimum from 100
                    'passage': '500-1500'   # Increased minimum from 500
                }
                word_count_range = word_count_range_dict.get(quote['type'].lower(),
                                                             '100-300')  # Default to 'paragraph' range
                quote_text = generate_quote(
                    prompt=quote['prompt'],
                    tone=quote['tone'],
                    speaker=speaker['name'],
                    event=quote['event'],
                    word_count_range=word_count_range,
                    retry_enabled=retry_quotes,
                    examples_content=examples_content  # Pass examples content to generate_quote
                )
                markdown_lines.append(f"> {quote_text}\n")
                quote_counts[quote['type']] += 1
                quote_word_count = len(quote_text.split())
                speaker_word_count += quote_word_count
                chapter_word_count += quote_word_count
                total_word_count += quote_word_count
            section_count += 1
            logger.info(f"Speaker {speaker['name']} word count: {speaker_word_count}")

        # After processing speakers, check if chapter is under target and add content if needed
        if chapter_word_count < chapter['word_count'] * 0.8:  # Allow 20% buffer
            shortfall = chapter['word_count'] - chapter_word_count
            logger.info(f"Chapter {chapter['title']} shortfall: {shortfall} words. Adding content.")
            additional_quotes = max(1, shortfall // 500)
            for i in range(additional_quotes):
                speaker = random.choice(chapter['speakers'])['name']
                quote_text = generate_quote(
                    prompt=f"Additional thoughts on {chapter['title']}.",
                    tone="reflective",
                    speaker=speaker,
                    event=chapter['title'],
                    word_count_range="400-600",
                    retry_enabled=retry_quotes,
                    examples_content=examples_content  # Pass examples content to generate_quote
                )
                markdown_lines.append(f"#### Additional Reflection by {speaker}\n")
                markdown_lines.append(f"> {quote_text}\n")
                quote_word_count = len(quote_text.split())
                chapter_word_count += quote_word_count
                total_word_count += quote_word_count
        logger.info(f"Chapter {chapter['title']} word count: {chapter_word_count} (Target: {chapter['word_count']})")

    # Post-generation adjustment: Add epilogue if total word count is still under target
    if total_word_count < high_level_spec['word_count_target']:
        shortfall = high_level_spec['word_count_target'] - total_word_count
        logger.info(f"Total word count shortfall: {shortfall}. Generating additional epilogue content.")
        additional_quotes_needed = max(1, shortfall // 500)  # Rough estimate, 500 words per quote
        markdown_lines.append("\n## Epilogue: Additional Reflections\n")
        for i in range(additional_quotes_needed):
            # Use a generic speaker or select from existing ones
            speaker = random.choice(high_level_spec['interviewees']['categories'][0]['examples'])
            quote_text = generate_quote(
                prompt="Reflect on the lasting impact of the central events.",
                tone="reflective",
                speaker=speaker,
                event="Post-Event Reflection",
                word_count_range="400-600",
                retry_enabled=retry_quotes,
                examples_content=examples_content  # Pass examples content to generate_quote
            )
            markdown_lines.append(f"### Reflection {i+1}: {speaker}\n")
            markdown_lines.append(f"> {quote_text}\n")
            total_word_count += len(quote_text.split())
        logger.info(f"Updated total word count after epilogue: {total_word_count}")

    # Report
    logger.info("--- Quote Report ---")
    for quote_type, count in quote_counts.items():
        logger.info(f"{quote_type.capitalize()} quotes: {count}")
    logger.info(f"Total word count: {total_word_count}")
    logger.info("--- End Quote Report ---")
    # Compile tracking data into DataFrame (we'll save it in main())
    tracking_df = pd.DataFrame(quote_tracking_data)
    logger.info(f"Compiled tracking DataFrame with {len(tracking_df)} quotes for model performance review.")

    return "\n".join(markdown_lines), tracking_df

def create_chapter_structure(title: str, description: str, word_count: int,
                             stipulated_facts: List[str], scenes: List[str]) -> Dict:
    """Creates a basic chapter structure."""
    return {
        "title": title,
        "description": description,
        "word_count": word_count,
        "stipulated_facts": stipulated_facts,
        "scenes": scenes,
        "speakers": []
    }


def generate_speaker_quote(event: str, interview_methods: Dict, style_guidelines: Dict,
                           documentarian: Dict) -> Dict:
    """Generates a quote structure for a speaker with weighted quote types for longer content."""
    # Weight quote types to favor longer content
    quote_types = ['sentence'] * 1 + ['paragraph'] * 6 + ['passage'] * 3  # Favor 'passage' for higher word count
    quote_type = random.choice(quote_types)

    # Randomly select interview method
    method = random.choice(interview_methods.get("techniques", []))

    return {
        "type": quote_type,  # Directly use the string value
        "event": event,
        "prompt": f"Using {method}: {event}",
        "tone": style_guidelines.get("tone", "respectful"),
        "documentarian_prompt": f"I asked about {event}"
    }


def create_detailed_outline_from_high_level(input_file: str | Dict, output_file: str) -> Dict:
    """
    Creates a detailed outline JSON file from a high-level specification.
    """
    # Handle input that's either a file path or direct dictionary
    try:
        if isinstance(input_file, dict):
            high_level_spec = input_file
        else:
            with open(input_file, 'r') as f:
                high_level_spec = json.load(f)
    except Exception as e:
        logging.error(f"Error reading input: {e}")
        raise

    # Extract key information
    word_count_target = high_level_spec.get("word_count_target", 60000)
    interviewees = high_level_spec.get("interviewees", {})
    interview_methods = high_level_spec.get("interview_methods", {})
    style_guidelines = high_level_spec.get("style_guidelines", {})
    documentarian = high_level_spec.get("documentarian", {})
    tournament_inspiration = high_level_spec.get("tournament_inspiration", {})
    if tournament_inspiration:
        logger.info(f"Building outline with inspiration from tournament winner: {tournament_inspiration.get('title', 'Untitled')}")
        # Ensure metadata exists before adding inspiration
        if "metadata" not in high_level_spec:
            high_level_spec["metadata"] = {}
        high_level_spec["metadata"]["inspiration"] = tournament_inspiration.get("title", "Untitled")

    # ... rest of the function remains unchanged ...
    # Define default narrative structure if not provided in HLS
    default_narrative_structure = [
        {
            "title": "The Foretellings",
            "description": "Voices reflect on prophecies or forewarnings of central events.",
            "word_count": int(word_count_target * 0.15),
            "stipulated_facts": ["Fact 1", "Fact 2"],
            "scenes": [
                "Early predictions are shared",
                "Key locations are identified",
                "Visions of upcoming events"
            ]
        },
        {
            "title": "The Announcement",
            "description": "The pivotal announcement and its immediate effects.",
            "word_count": int(word_count_target * 0.2),
            "stipulated_facts": ["Fact 3"],
            "scenes": [
                "A key message is delivered",
                "Initial reactions unfold",
                "Implications are realized"
            ]
        },
        {
            "title": "Journey to the Center",
            "description": "The challenging journey and search for a resting place.",
            "word_count": int(word_count_target * 0.2),
            "stipulated_facts": ["Fact 4"],
            "scenes": [
                "Preparation for travel",
                "The path to the destination",
                "Seeking a place to stay"
            ]
        }
    ]

    # Use narrative structure from HLS if available, otherwise use default
    narrative_structure = high_level_spec.get("narrative_structure", default_narrative_structure)
    if narrative_structure == default_narrative_structure:
        logger.info("Using default narrative structure as none was provided in high-level spec.")
    else:
        logger.info("Using narrative structure from high-level spec.")
        # Validate and adjust word counts if they don't sum to target
        total_specified_word_count = sum(chapter.get("word_count", 0) for chapter in narrative_structure)
        if total_specified_word_count != word_count_target:
            logger.warning(
                f"Narrative structure word count {total_specified_word_count} does not match target {word_count_target}. Adjusting proportionally.")
            if total_specified_word_count == 0:
                # If no word counts are specified, distribute evenly
                chapter_count = len(narrative_structure)
                for chapter in narrative_structure:
                    chapter["word_count"] = word_count_target // chapter_count
            else:
                # Adjust proportionally
                for chapter in narrative_structure:
                    chapter["word_count"] = int(
                        chapter.get("word_count", 0) * word_count_target / total_specified_word_count)

    # Initialize detailed outline
    detailed_outline = {"chapters": []}

    # Process each chapter
    for chapter_info in narrative_structure:
        chapter = create_chapter_structure(
            chapter_info["title"],
            chapter_info["description"],
            chapter_info["word_count"],
            chapter_info.get("stipulated_facts", []),
            chapter_info.get("scenes", [])
        )

        # Assign speakers to chapter
        speakers_per_chapter = random.randint(5, 7)  # As specified in high_level_spec

        # Get speakers from each category
        all_speakers = []
        for category in interviewees.get("categories", []):
            all_speakers.extend(category.get("examples", []))

        # Select random speakers for this chapter
        selected_speakers = random.sample(all_speakers, min(speakers_per_chapter, len(all_speakers)))

        # Generate speaker entries
        for speaker_name in selected_speakers:
            speaker_entry = {
                "name": speaker_name,
                "context": f"Residing in the Archives, reflecting on their role",
                "quotes": []
            }
            # Generate 3-8 quotes for each speaker to ensure higher word count (updated range), limited by available scenes
            available_scenes = chapter_info.get("scenes", [])
            if len(available_scenes) < 3:
                num_scenes_to_select = len(available_scenes)
            else:
                num_scenes_to_select = random.randint(3, min(8, len(available_scenes)))
            for scene in random.sample(available_scenes, num_scenes_to_select) if available_scenes else []:
                quote = generate_speaker_quote(
                    scene,
                    interview_methods,
                    style_guidelines,
                    documentarian
                )
                speaker_entry["quotes"].append(quote)
            chapter["speakers"].append(speaker_entry)

        detailed_outline["chapters"].append(chapter)

    # Add metadata
    detailed_outline["metadata"] = {
        "total_word_count": word_count_target,
        "documentarian": documentarian.get("name", ""),
        "style": style_guidelines.get("tone", "")
    }

    if not validate_outline(detailed_outline):
        logging.error("Generated outline failed validation")
        raise ValueError("Invalid outline generated")
    logging.debug(f"About to save outline with {len(detailed_outline['chapters'])} chapters")

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_outline, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully created detailed outline at {output_file}")
    except Exception as e:
        logging.error(f"Error writing output file: {e}")
        raise

    return detailed_outline


def validate_outline(outline: Dict) -> bool:
    """
    Validates the created outline against basic requirements.
    """
    try:
        # Basic structure checks
        if not outline.get("chapters"):
            logging.error("No chapters found in outline")
            return False

        total_words = 0
        for chapter in outline["chapters"]:
            # Check chapter structure
            required_fields = ["title", "description", "word_count", "speakers"]
            if not all(field in chapter for field in required_fields):
                logging.error(f"Missing required fields in chapter {chapter.get('title', 'unknown')}")
                return False

            total_words += chapter["word_count"]

            # Check speakers
            if not 5 <= len(chapter["speakers"]) <= 7:
                logging.warning(f"Chapter {chapter['title']} has {len(chapter['speakers'])} speakers")

        # Check total word count
        if total_words != outline["metadata"]["total_word_count"]:
            logging.warning(f"Total word count mismatch: {total_words} vs {outline['metadata']['total_word_count']}")

        return True

    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False


def generate_high_level_spec(description: str = None, word_count_target: int = 60000, writing_model_name: str = "grok-3-fast-beta",
                             stipulated_facts: List[Dict[str, str]] = None) -> Dict:
    """Generate a high-level specification for the oral history using LLM, incorporating stipulated facts."""
    if not description:
        description = (
            "Create an oral history novelization of a significant historical or cultural event, focusing on diverse perspectives "
            "from human, extraordinary, and conceptualized entities who witnessed the events. "
            "The narrative should explore emotional depth and contextual background while staying faithful "
            "to provided facts. Aim for a book-length work with multiple chapters."
        )

    # Build prompt with description
    prompt = (
        f"Generate a high-level specification (HLS) for a novelized oral history based on the following description: "
        f"'{description}'. The HLS should be a structured JSON object with the following fields: "
        f"- 'title': A compelling title for the work. "
        f"- 'description': A brief summary of the project (50-100 words). "
        f"- 'word_count_target': A target word count for the entire work (set to {word_count_target}). "
        f"- 'documentarian': An object with 'name', 'role', and 'tone' for the interviewer/narrator. "
        f"- 'interviewees': An object with 'total_count' (number of interviewees, default 20-30) and 'categories' "
        f"(list of categories like 'Humans', 'Extraordinary Beings', 'Conceptualized Entities', each with 'type', 'role', and 'examples'). "
        f"- 'interview_methods': An object with 'techniques' (list of methods like 'Direct Questioning', 'Story Prompting'). "
        f"- 'style_guidelines': An object with 'tone' (e.g., 'respectful') and 'quote_lengths' (list of types like 'sentence', 'paragraph', 'passage'). "
        f"- 'narrative_structure': A list of chapter objects, each with 'title', 'description', 'word_count', 'stipulated_facts' (list of relevant factual references), "
        f"and 'scenes' (list of key scenes or events for the chapter). Ensure the sum of chapter word counts matches the 'word_count_target'. "
        f"Ensure the output is a valid JSON string that can be parsed into a dictionary. Use sensible defaults if specific details are not provided."
    )

    # Append stipulated facts to the prompt if provided
    if stipulated_facts:
        prompt += "\n\nIncorporate the following stipulated facts as grounding for the narrative. Ensure the story aligns with these facts where relevant:\n"
        for fact in stipulated_facts:
            prompt += f"- Source: {fact['source']} (Type: {fact['type']}):\n{fact['content'][:500]}...\n"  # Limit content to avoid token overflow
        prompt += "Use these facts to inform the historical, cultural, or contextual elements of the narrative."

    try:
        response = client.chat.completions.create(
            model=writing_model_name,
            messages=[
                {"role": "system",
                 "content": "You are Grok 3, a helpful AI for generating creative, structured content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        hls_text = response.choices[0].message.content.strip()
        # Parse JSON from the response (assuming the LLM returns valid JSON)
        hls = json.loads(hls_text)
        # Store stipulated facts in HLS for downstream use
        if stipulated_facts:
            hls['stipulated_facts'] = stipulated_facts
        logger.info("Generated high-level specification successfully.")
        return hls
    except Exception as e:
        logger.error(f"Failed to generate high-level spec: {e}")
        raise


def review_high_level_spec(hls: Dict, auto_refine: bool = False, output_dir: str = "runs/run-default", writing_model_name="grok-3-fast-beta") -> Dict:
    """Allow automated refinement of the high-level spec without pausing for input."""
    if auto_refine:
        logger.info("Automatically refining high-level spec with LLM.")
        prompt = (
            f"Review and refine the following high-level specification for a novelized oral history: "
            f"{json.dumps(hls, indent=2)}. Ensure the structure remains consistent, improve clarity, coherence, and creativity, "
            f"and maintain sensible defaults. Return the refined specification as a valid JSON string."
        )
        try:
            response = client.chat.completions.create(
                model=writing_model_name,
                messages=[
                    {"role": "system", "content": f"You are {writing_model_name}, a helpful AI for refining structured content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            refined_hls_text = response.choices[0].message.content.strip()
            refined_hls = json.loads(refined_hls_text)
            logger.info("High-level spec refined by LLM.")
            return refined_hls
        except Exception as e:
            logger.error(f"Failed to refine high-level spec: {e}")
            return hls
    else:
        # Save the HLS for reference without pausing for input
        logger.info("Saving high-level spec without pausing for review.")
        save_json_file(hls, f"{output_dir}/temp_high_level_spec.json")
        logger.info(f"High-level spec saved to '{output_dir}/temp_high_level_spec.json' for reference.")
        return hls


def main():
    """Main function to process inputs and generate Markdown draft with HLS generation and review."""
    parser = argparse.ArgumentParser(description="Generate a Markdown draft for an oral history project.")
    parser.add_argument('--mode', choices=['full', 'hls_only', 'from_hls', 'detailed_outline'], default='full',
                        help="Mode to run: 'full' for complete workflow, 'hls_only' to generate/review HLS only, "
                             "'from_hls' to start from existing HLS, 'detailed_outline' to start from detailed outline.")
    parser.add_argument('--description', type=str, default=None,
                        help="Description for generating high-level spec. If not provided, a default is used.")
    parser.add_argument('--auto-refine', action='store_true',
                        help="Automatically refine HLS with LLM instead of pausing for human edit.")
    parser.add_argument('--limit-sections', type=int, default=None,
                        help="Maximum number of draft sections to create (default = None for unlimited).")
    parser.add_argument('--retry-quotes', action='store_true',
                        help="Enable retry logic for quote generation to meet word count targets (may slow down execution).")
    parser.add_argument('--base-dir', type=str, default="runs",
                        help="Base directory for saving run outputs (default = 'runs').")
    parser.add_argument('--word-count-target', type=int, default=60000,
                        help="Target word count for the entire project (default = 60000).")
    parser.add_argument('--generate-ideas', action='store_true',
                        help="Generate ideas for oral history topics using ContinuousIdeaGenerator before HLS.")
    parser.add_argument('--run-tournament', action='store_true',
                        help="Run a tournament to rank generated ideas and select the best for HLS or outline.")
    parser.add_argument('--idea-batch-size', type=int, default=5,
                        help="Number of ideas to generate per batch (default = 5).")
    parser.add_argument('--writing-model', type=str, default="grok-3-fast-beta", help="Model to use for writing (default = 'grok-3-fast-beta').")
    parser.add_argument('--idea-model', type=str, default="mistral",
                        help="Model to use for idea generation (default = 'mistral').")
    parser.add_argument('--idea-temperature', type=float, default=0.7,
                        help="Temperature for idea generation model (default = 0.7).")
    parser.add_argument('--stipulated-facts', type=str, nargs='*', default=[],
                        help="Paths to files (PDF, JSON, or text) containing stipulated facts for story grounding.")

    args = parser.parse_args()
    writing_model_name = args.writing_model
    try:
        # Generate a unique 8-digit UUID for this run
        run_id = str(uuid.uuid4())[:8]
        output_dir = f"{args.base_dir}/run-{run_id}"
        logger.info(f"Output directory for this run: {output_dir}")

        stipulated_facts = read_stipulated_facts(args.stipulated_facts) if args.stipulated_facts else []

        # Step 0: Optional Idea Generation and Tournament Selection
        selected_ideas = None
        if args.generate_ideas and args.mode in ['full', 'hls_only']:
            logger.info("Generating ideas for oral history topics...")
            # Custom description for idea generation if provided, else use a generic one
            idea_description = args.description if args.description else "Generate ideas for an oral history project focusing on significant events."
            idea_generator = ContinuousIdeaGenerator(
                ideas_per_batch=args.idea_batch_size,
                model=args.idea_model,
                temperature=args.idea_temperature,
                base_dir=output_dir,
                custom_prompt=args.description if args.description else None
            )
            # Override base_dir to match our run directory
            idea_generator.base_dir = Path(output_dir)
            idea_generator.resources_dir = Path(output_dir) / "resources"
            idea_generator.setup_directories()
            generated_ideas = idea_generator.generate_single_batch(
                mode=None,
                count=args.idea_batch_size
            )
            if generated_ideas is None:
                logger.error("Idea generation failed; no ideas were generated.")
                generated_ideas = {}
            else:
                logger.info(f"Generated {len(generated_ideas)} ideas.")
            save_json_file(generated_ideas, f"{output_dir}/generated_ideas.json")
            logger.info(f"Saved ideas to {output_dir}/generated_ideas.json")
            save_json_file(generated_ideas, f"{output_dir}/generated_ideas.json")
            logger.info(f"Generated {len(generated_ideas)} ideas and saved to {output_dir}/generated_ideas.json")

            if args.run_tournament and len(generated_ideas) > 1:
                logger.info("Running tournament to rank ideas...")
                logger.info("Running tournament to rank ideas using ContinuousIdeaGenerator...")
                batch_dir = Path(output_dir) / idea_generator.run_id if idea_generator.run_id else Path(
                    output_dir) / "tournament"
                batch_dir.mkdir(exist_ok=True)
                idea_generator.send_batch_results_to_tournament(batch_dir, generated_ideas)
                # Extract selected idea from saved results or fallback to first idea
                tournament_json_path = batch_dir / "tournament_matches.json"
                if tournament_json_path.exists():
                    try:
                        with open(tournament_json_path, 'r') as f:
                            tournament_data = json.load(f)
                        # Handle case where tournament_data is a list (e.g., list of rounds)
                        if isinstance(tournament_data, list) and len(tournament_data) > 0:
                            # Assume the last item in the list is the final round
                            last_round = tournament_data[-1]
                            if isinstance(last_round, dict) and 'winner' in last_round and last_round['winner']:
                                selected_ideas = last_round['winner']
                                save_json_file(selected_ideas, f"{output_dir}/selected_ideas.json")
                                logger.info(
                                    f"Selected top idea via tournament: {selected_ideas.get('title', 'Untitled')} saved to {output_dir}/selected_ideas.json")
                            else:
                                logger.warning(
                                    "No winner found in tournament data (list format); using first generated idea if available.")
                                selected_ideas = list(generated_ideas.values())[0] if generated_ideas else None
                        # Handle case where tournament_data is a dictionary with 'rounds' key
                        elif isinstance(tournament_data, dict) and tournament_data.get('rounds', []) and \
                                tournament_data['rounds'][-1].get('winners', []):
                            selected_ideas = tournament_data['rounds'][-1]['winners'][0]
                            save_json_file(selected_ideas, f"{output_dir}/selected_ideas.json")
                            logger.info(
                                        f"Selected top idea via tournament: {selected_ideas.get('title', 'Untitled')} saved to {output_dir}/selected_ideas.json")
                        else:
                            logger.warning(
                                "No winners found in tournament data (dict format); using first generated idea if available.")
                            selected_ideas = list(generated_ideas.values())[0] if generated_ideas else None
                    except Exception as e:
                        logger.error(f"Error reading tournament results: {e}")
                        selected_ideas = list(generated_ideas.values())[0] if generated_ideas else None
                else:
                    logger.warning("Tournament results not found; using first generated idea if available.")
                    selected_ideas = list(generated_ideas.values())[0] if generated_ideas else None
        if args.mode == 'full' or args.mode == 'hls_only':
            # Step 1: Generate high-level spec, potentially influenced by selected ideas
            # Step 1: Generate high-level spec, potentially influenced by selected ideas
            logger.info("Generating high-level specification...")
            # Start with the base description (user-provided or default)
            description = args.description
            if not description:
                description = "Create an oral history novelization of a significant historical or cultural event, focusing on diverse perspectives."
            # Append or integrate tournament winner's details if available
            if selected_ideas:
                tournament_desc = f"This project is inspired by the theme '{selected_ideas.get('title', 'Significant Event')}' with the concept: {selected_ideas.get('logline', 'Explore key historical moments.')}"

                description = f"The original theme was: \n\n{description}.\n\n The tournament winner's theme was: {tournament_desc}"
                logger.info(f"Incorporated tournament winner's theme into description.")
            else:
                logger.info(f"No tournament winner found; using provided description.")
                if args.description:
                    description = args.description
            logger.info(f"Description: {description}")
            high_level_spec = generate_high_level_spec(description, args.word_count_target, writing_model_name=args.writing_model, stipulated_facts=stipulated_facts)
            logger.info("High-level specification generated successfully.")
            st.success(f"High-level specification generated successfully.")
            # Optionally store selected_ideas in HLS for downstream use
            logger.info(description)
            high_level_spec['tournament_inspiration'] = selected_ideas if selected_ideas else {}
            logger.info("Tournament inspiration saved in high-level spec for downstream processes.")
            save_json_file(high_level_spec, f"{output_dir}/oral_history_high_level_spec.json")
            if args.mode == 'hls_only':
                logger.info("Stopping after HLS generation and review.")
                return

        elif args.mode == 'from_hls':
            # Load existing HLS
            current_hls = input("Enter the path to the existing HLS JSON file (e.g., runs/run-XXXXXXXX/oral_history_high_level_spec.json): ")
            high_level_spec = load_json_file(current_hls)
            output_dir = os.path.dirname(current_hls)  # Use the directory of the loaded HLS
            logger.info(f"Loaded existing high-level spec {current_hls}.")

        # Step 3: Generate detailed outline from HLS
        if args.mode in ['full', 'from_hls']:
            logger.info("Generating detailed outline from high-level spec...")
            st.info("Generating detailed outline from high-level spec...")
            detailed_outline = create_detailed_outline_from_high_level(
                high_level_spec, f"{output_dir}/oral_history_detailed_outline.json"
            )
        elif args.mode == 'detailed_outline':
            # Load existing detailed outline
            current_outline = input("Enter the path to the existing detailed outline JSON file: ")
            detailed_outline = load_json_file(current_outline)
            high_level_spec = load_json_file(os.path.join(os.path.dirname(current_outline), "oral_history_high_level_spec.json"))
            output_dir = os.path.dirname(current_outline)
            logger.info("Loaded existing detailed outline.")

        # Step 4: Generate Markdown draft

        if args.mode in ['full', 'from_hls', 'detailed_outline']:
            logger.info("Generating Markdown draft...")
            markdown_content, tracking_df = create_markdown_draft(
                high_level_spec,
                detailed_outline,
                args.limit_sections,
                retry_quotes=args.retry_quotes
            )
            output_path = f"{output_dir}/oral_history_draft.md"
            save_markdown_file(markdown_content, output_path)
            # Save tracking DataFrame to CSV
            tracking_csv_path = f"{output_dir}/quote_performance_tracking.csv"
            tracking_df.to_csv(tracking_csv_path, index=False)
            logger.info(f"Saved quote performance tracking DataFrame to {tracking_csv_path}")


    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()