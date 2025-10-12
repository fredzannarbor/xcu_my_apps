# test_single_mnemonic.py
import json
import logging
import sys
import os
from pathlib import Path
import pandas as pd

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codexes.modules.builders import llm_get_book_data

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Tests the mnemonics prompt for a single book."""
    imprint = "xynapse_traces"
    schedule_file = f"imprints/{imprint}/xynapse_traces_schedule.json"
    prompt_template_file = f"imprints/{imprint}/prompts.json"
    model_name = "gemini/gemini-2.5-pro"
    
    # Load model params
    try:
        with open('temp_model_params.json', 'r') as f:
            model_params = json.load(f)
    except FileNotFoundError:
        logger.error("temp_model_params.json not found. Please create it.")
        sys.exit(1)

    # --- Load Schedule ---
    try:
        with open(schedule_file, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f).get("publishing_schedule", [])
        all_books = [book for month in schedule_data for book in month.get("books", [])]
        if not all_books:
            logger.error("No books found in the schedule.")
            sys.exit(1)
        book_data = all_books[0] # Use the first book for the test
    except Exception as e:
        logger.critical(f"Failed to load or parse schedule file {schedule_file}: {e}")
        sys.exit(1)

    logger.info(f"--- Testing with book: '{book_data.get('title')}' ---")

    # --- Stage 1: Get Quotes ---
    logger.info("--- Generating quotes... ---")
    quote_prompt_key = "imprint_quotes_prompt"
    
    book_json_data, llm_stats = llm_get_book_data.process_book(
        book_data=book_data,
        prompt_template_file=prompt_template_file,
        model_name=model_name,
        per_model_params=model_params,
        raw_output_dir=Path("test_output"),
        safe_basename="test_mnemonic",
        prompt_keys=[quote_prompt_key],
        catalog_only=False
    )

    if not book_json_data or not book_json_data.get("quotes"):
        logger.error("❌ Failed to generate quotes. Aborting test.")
        return

    logger.info(f"✅ Successfully generated {len(book_json_data.get('quotes', []))} quotes.")

    print("\n--- Generated Quotes ---")
    for i, quote in enumerate(book_json_data.get('quotes', []), 1):
        print(f"{i}. {quote.get('quote')} - {quote.get('author')}")
    print("------------------------")

    # --- Stage 2: Get Mnemonics ---
    logger.info("--- Generating mnemonics... ---")
    mnemonic_prompt_key = "mnemonics_prompt"

    reprompt_data = llm_get_book_data.reprompt_and_update(
        book_data=book_json_data,
        prompt_key=mnemonic_prompt_key,
        prompt_template_file=prompt_template_file,
        model_name=model_name,
        per_model_params=model_params
    )

    if reprompt_data and "mnemonics_tex" in reprompt_data:
        logger.info("✅ Successfully generated mnemonics!")
        print("\n--- Generated Mnemonics (LaTeX) ---")
        print(reprompt_data["mnemonics_tex"])
        print("------------------------------------")
    else:
        logger.error("❌ Failed to generate mnemonics.")
        print("\n--- Raw Reprompt Data ---")
        print(reprompt_data)
        print("-------------------------")


if __name__ == "__main__":
    main()
