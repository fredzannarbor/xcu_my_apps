#!/usr/bin/env python3
"""
Test script to simulate the full book pipeline.
"""

import json
import sys
import os
import argparse
from pathlib import Path
import logging
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def load_module(module_path):
    """Load a Python module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error loading module from {module_path}: {e}")
        return None

def test_full_book_pipeline(book_json_path):
    """Test the full book pipeline."""
    try:
        # Add src to path for imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Load the llm_get_book_data module
        llm_get_book_data = load_module("src/codexes/modules/builders/llm_get_book_data.py")
        if not llm_get_book_data:
            logger.error("Failed to load llm_get_book_data module")
            return False
        
        # Load the book data
        book_data = load_json_file(book_json_path)
        if not book_data:
            logger.error(f"Failed to load book data from {book_json_path}")
            return False
        
        # Create a temporary output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        raw_output_dir = output_dir / "raw_json_responses"
        raw_output_dir.mkdir(exist_ok=True)
        processed_output_dir = output_dir / "processed_json"
        processed_output_dir.mkdir(exist_ok=True)
        
        # Set up the configuration
        config = {
            "model": "gemini/gemini-2.5-flash",
            "model_params": {
                "gemini/gemini-2.5-flash": {
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            },
            "prompt_template_file": "prompts/prompts.json"
        }
        
        # Process the book
        logger.info("Processing book...")
        book_json_data, llm_stats = llm_get_book_data.process_book(
            book_data=book_data,
            prompt_template_file=config["prompt_template_file"],
            model_name=config["model"],
            per_model_params=config["model_params"],
            raw_output_dir=raw_output_dir,
            safe_basename="test_book",
            prompt_keys=["mnemonics_prompt"],
            catalog_only=False
        )
        
        # Check if the book was processed successfully
        if not book_json_data:
            logger.error("Failed to process book")
            return False
        
        # Check if the mnemonics_tex field was generated
        if "mnemonics_tex" not in book_json_data:
            logger.error("mnemonics_tex field was not generated")
            return False
        
        # Save the processed book data
        with open(processed_output_dir / "test_book.json", 'w', encoding='utf-8') as f:
            json.dump(book_json_data, f, indent=2)
        logger.info(f"Saved processed book data to {processed_output_dir / 'test_book.json'}")
        
        # Print the mnemonics_tex field
        logger.info("mnemonics_tex field:")
        print(book_json_data.get("mnemonics_tex", ""))
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing full book pipeline: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test full book pipeline")
    parser.add_argument("--book-json", default="sample_book.json", help="Path to the book JSON file")
    args = parser.parse_args()
    
    if test_full_book_pipeline(args.book_json):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())