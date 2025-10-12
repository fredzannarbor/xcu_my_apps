#!/usr/bin/env python3
"""
Debug script for mnemonics generation in the Codexes Factory pipeline.
This script focuses specifically on generating mnemonics for a book.
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from codexes.core import llm_caller, prompt_manager
except ModuleNotFoundError:
    from src.codexes.core import llm_caller, prompt_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def generate_mnemonics(book_data, model_name="gemini/gemini-2.5-pro"):
    """Generate mnemonics for a book using the specified model."""
    
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')
    quotes = book_data.get("quotes", [])
    
    # Format quotes for the prompt
    quotes_text = ""
    if quotes:
        quotes_text = "\n\nQuotations in this book:\n"
        for i, quote in enumerate(quotes, 1):
            q_text = quote.get("quote", "")
            q_author = quote.get("author", "Unknown")
            q_source = quote.get("source", "Unknown")
            quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
    
    book_content = f"Title: {title}\n\nDescription: {description}{quotes_text}"
    
    # Prepare substitutions for the prompt
    substitutions = {
        "book_content": book_content,
        "title": title,
        "topic": title,
        "description": description,
        "quotes_per_book": len(quotes),
    }
    
    # Load and prepare the mnemonics prompt
    prompt_template_file = Path('imprints/xynapse_traces/prompts.json')
    formatted_prompts = prompt_manager.load_and_prepare_prompts(
        prompt_file_path=prompt_template_file,
        prompt_keys=["mnemonics_prompt"],
        substitutions=substitutions
    )
    
    if not formatted_prompts:
        logger.error(f"Could not load or prepare the mnemonics prompt for book '{title}'.")
        return None
    
    # Call the LLM to generate mnemonics
    responses = llm_caller.get_responses_from_multiple_models(
        prompt_configs=formatted_prompts, 
        models=[model_name],
        response_format_type="json_object", 
        per_model_params={
            "gemini/gemini-2.5-pro": {
                "max_tokens": 2000,
                "temperature": 0.7
            }
        }
    )
    
    # Process the response
    for model_name, model_responses in responses.items():
        for response_item in model_responses:
            if response_item.get('prompt_key') == "mnemonics_prompt":
                parsed_content = response_item.get('parsed_content')
                if parsed_content and isinstance(parsed_content, dict) and 'mnemonics_tex' in parsed_content:
                    mnemonics_tex = parsed_content['mnemonics_tex']
                    logger.info(f"Successfully generated mnemonics_tex content ({len(mnemonics_tex)} characters)")
                    
                    # Save the mnemonics to a file for inspection
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = Path("output/debug")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    output_file = output_dir / f"mnemonics_{timestamp}.tex"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(mnemonics_tex)
                    logger.info(f"Saved mnemonics to {output_file}")
                    
                    return mnemonics_tex
    
    logger.error("Failed to generate mnemonics")
    return None

def load_book_data(json_path):
    """Load book data from a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load book data from {json_path}: {e}")
        return None

def main():
    """Main function to debug mnemonics generation."""
    # Check if a processed JSON file exists in the output directory
    processed_dir = Path("output/xynapse_traces_build/processed_json")
    json_files = list(processed_dir.glob("*.json"))
    
    if not json_files:
        logger.error("No processed JSON files found. Please run the pipeline first.")
        return
    
    # Use the first JSON file found
    json_path = json_files[0]
    logger.info(f"Using book data from {json_path}")
    
    # Load the book data
    book_data = load_book_data(json_path)
    if not book_data:
        return
    
    # Generate mnemonics
    mnemonics_tex = generate_mnemonics(book_data)
    
    if mnemonics_tex:
        # Update the book data with the generated mnemonics
        book_data["mnemonics_tex"] = mnemonics_tex
        
        # Save the updated book data
        updated_path = json_path.with_name(f"{json_path.stem}_with_mnemonics.json")
        with open(updated_path, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Updated book data saved to {updated_path}")
        
        # Print the command to run the pipeline with the updated book data
        logger.info("\nTo run the pipeline with the updated book data, use:")
        logger.info(f"python run_book_pipeline.py --imprint xynapse_traces --schedule-file data/books.csv --model gemini/gemini-2.5-pro --max-books 1 --start-stage 3 --end-stage 3 --skip-lsi")

if __name__ == "__main__":
    main()