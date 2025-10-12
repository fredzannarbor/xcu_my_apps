#!/usr/bin/env python3
"""
Test script to show how the book content is formulated and the prompt prepared for mnemonics generation.
This script loads a book JSON file, prepares the content for the mnemonics prompt, and displays the result
without actually submitting it to the LLM.
"""

import json
import sys
import os
import argparse
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
    """
    Prepare the book content for the mnemonics prompt.
    This is a copy of the logic from src/codexes/modules/builders/llm_get_book_data.py
    """
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

def load_prompt_template(prompt_file_path, prompt_key="mnemonics_prompt"):
    """Load the prompt template from the specified file."""
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            return prompts.get(prompt_key, {}).get("prompt", "")
    except Exception as e:
        logger.error(f"Error loading prompt template from {prompt_file_path}: {e}")
        return ""

def prepare_prompt(prompt_template, book_content):
    """Prepare the prompt by replacing placeholders with actual content."""
    return prompt_template.replace("{book_content}", book_content)

def main():
    parser = argparse.ArgumentParser(description="Test mnemonic prompt preparation")
    parser.add_argument("--book-json", required=True, help="Path to the book JSON file")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    parser.add_argument("--output", help="Path to save the prepared prompt (optional)")
    args = parser.parse_args()
    
    # Load the book data
    book_data = load_json_file(args.book_json)
    if not book_data:
        logger.error("Failed to load book data. Exiting.")
        return 1
    
    # Prepare the book content
    book_content = prepare_book_content(book_data)
    logger.info(f"Prepared book content ({len(book_content)} characters)")
    
    # Load the prompt template
    prompt_template = load_prompt_template(args.prompt_file)
    if not prompt_template:
        logger.error("Failed to load prompt template. Exiting.")
        return 1
    
    # Prepare the prompt
    prepared_prompt = prepare_prompt(prompt_template, book_content)
    logger.info(f"Prepared prompt ({len(prepared_prompt)} characters)")
    
    # Display the results
    print("\n" + "="*80)
    print("BOOK CONTENT:")
    print("="*80)
    print(book_content[:2000] + "..." if len(book_content) > 2000 else book_content)
    
    print("\n" + "="*80)
    print("PREPARED PROMPT:")
    print("="*80)
    print(prepared_prompt[:2000] + "..." if len(prepared_prompt) > 2000 else prepared_prompt)
    
    # Save the prepared prompt if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(prepared_prompt)
            logger.info(f"Saved prepared prompt to {args.output}")
        except Exception as e:
            logger.error(f"Error saving prepared prompt to {args.output}: {e}")
    
    # Check if the book content is actually included in the prepared prompt
    if book_content in prepared_prompt:
        logger.info("✅ Book content is properly included in the prepared prompt")
    else:
        logger.error("❌ Book content is NOT properly included in the prepared prompt")
        
        # Try to find where the substitution should have happened
        if "{book_content}" in prepared_prompt:
            logger.error("The {book_content} placeholder was not replaced")
        else:
            logger.error("The {book_content} placeholder was replaced, but with different content")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())