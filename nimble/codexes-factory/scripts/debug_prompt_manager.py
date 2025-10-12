#!/usr/bin/env python3
"""
Script to debug the prompt manager and see what's happening with the mnemonics prompt.
"""

import json
import sys
import os
import argparse
from pathlib import Path
import logging
import re

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

def prepare_book_content(book_data):
    """Prepare the book content for the mnemonics prompt."""
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')
    
    # For mnemonics prompt, we need to include the quotes if they exist
    quotes = book_data.get("quotes", [])
    quotes_text = ""
    
    if quotes:
        quotes_text = "\n\nQuotations in this book:\n"
        # Use all quotes but be mindful of potential token limits
        num_quotes = len(quotes)
        
        # If there are many quotes, provide a summary of themes and authors
        if num_quotes > 30:
            # Include a sample of quotes (first 10, middle 10, last 10)
            sample_quotes = quotes[:10] + quotes[num_quotes//2-5:num_quotes//2+5] + quotes[-10:]
            
            # Get all unique authors
            all_authors = set(quote.get("author", "Unknown") for quote in quotes)
            authors_text = ", ".join(list(all_authors)[:20])  # Limit to 20 authors if there are many
            if len(all_authors) > 20:
                authors_text += f", and {len(all_authors) - 20} more"
                
            # Add summary information
            quotes_text += f"This book contains {num_quotes} quotes from authors including {authors_text}.\n"
            quotes_text += f"Here is a representative sample of {len(sample_quotes)} quotes:\n\n"
            
            # Add the sample quotes
            for i, quote in enumerate(sample_quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
        else:
            # If there aren't too many quotes, include all of them
            for i, quote in enumerate(quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
    
    book_content = f"Title: {title}\n\nDescription: {description}{quotes_text}"
    return book_content

def debug_prompt_manager(prompt_file_path, book_json_path):
    """Debug the prompt manager and see what's happening with the mnemonics prompt."""
    try:
        # Load the prompts file
        prompts = load_json_file(prompt_file_path)
        if not prompts:
            logger.error(f"Failed to load prompts from {prompt_file_path}")
            return False
        
        # Load the book data
        book_data = load_json_file(book_json_path)
        if not book_data:
            logger.error(f"Failed to load book data from {book_json_path}")
            return False
        
        # Prepare the book content
        book_content = prepare_book_content(book_data)
        logger.info(f"Prepared book content ({len(book_content)} characters)")
        
        # Get the mnemonics prompt
        mnemonics_prompt = prompts.get("mnemonics_prompt", {}).get("prompt", "")
        if not mnemonics_prompt:
            logger.error("Failed to get mnemonics prompt")
            return False
        
        # Find all placeholders in the prompt
        placeholders = re.findall(r'\{([^{}]+)\}', mnemonics_prompt)
        logger.info(f"Found {len(placeholders)} placeholders in the prompt: {placeholders}")
        
        # Create a substitutions dictionary with all placeholders
        substitutions = {
            "book_content": book_content,
            "document": book_content
        }
        
        # Add all other placeholders with dummy values
        for placeholder in placeholders:
            if placeholder not in substitutions:
                substitutions[placeholder] = f"DUMMY_{placeholder}"
        
        # Try to format the prompt
        try:
            formatted_prompt = mnemonics_prompt.format(**substitutions)
            logger.info("Successfully formatted the prompt")
            
            # Save the formatted prompt
            with open("debug_formatted_prompt.txt", 'w', encoding='utf-8') as f:
                f.write(formatted_prompt)
            logger.info("Saved formatted prompt to debug_formatted_prompt.txt")
            
            return True
        except Exception as e:
            logger.error(f"Error formatting the prompt: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Error debugging prompt manager: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug prompt manager")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    parser.add_argument("--book-json", default="sample_book.json", help="Path to the book JSON file")
    args = parser.parse_args()
    
    if debug_prompt_manager(args.prompt_file, args.book_json):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())