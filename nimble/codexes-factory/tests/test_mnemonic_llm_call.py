#!/usr/bin/env python3
"""
Test script to debug the LLM call process for mnemonics generation.
This script loads a book JSON file, prepares the content, and simulates the LLM call process
without actually making the API call.
"""

import json
import sys
import os
import argparse
from pathlib import Path
import logging
import pprint

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Try importing with the standard module path
try:
    from codexes.core import prompt_manager
except ImportError:
    # Fall back to src-prefixed imports when running from project root
    from codexes.core import prompt_manager

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
    stream = book_data.get('stream', 'General')
    
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
    
    substitutions = {
        "book_content": f"Title: {title}\n\nDescription: {description}{quotes_text}",
        "topic": title,
        "stream": stream,
        "description": description,
        "quotes_per_book": book_data.get("quotes_per_book", len(quotes) if quotes else 10),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", "")
    }
    
    return substitutions

def main():
    parser = argparse.ArgumentParser(description="Test mnemonic LLM call process")
    parser.add_argument("--book-json", required=True, help="Path to the book JSON file")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    parser.add_argument("--output", help="Path to save the prepared prompt (optional)")
    args = parser.parse_args()
    
    # Load the book data
    book_data = load_json_file(args.book_json)
    if not book_data:
        logger.error("Failed to load book data. Exiting.")
        return 1

    # Load the mock quotes and add them to the book_data
    mock_quotes_data = load_json_file('test_mock_quotes.json')
    if mock_quotes_data and "quotes" in mock_quotes_data:
        book_data["quotes"] = mock_quotes_data["quotes"]
        logger.info(f"Loaded {len(book_data['quotes'])} mock quotes.")
    
    # Prepare the substitutions
    substitutions = prepare_book_content(book_data)
    # Add the document placeholder
    substitutions["document"] = substitutions["book_content"]
    logger.info(f"Prepared substitutions with {len(substitutions['book_content'])} characters of book content")
    
    # Load and prepare the prompts using the actual prompt_manager
    try:
        formatted_prompts = prompt_manager.load_and_prepare_prompts(
            prompt_file_path=args.prompt_file,
            prompt_keys=["mnemonics_prompt"],
            substitutions=substitutions
        )
        
        if not formatted_prompts:
            logger.error("Failed to prepare mnemonics prompt")
            return 1

        mnemonics_prompt = None
        for prompt in formatted_prompts:
            if prompt.get("key") == "mnemonics_prompt":
                mnemonics_prompt = prompt.get("prompt_config")
                break
        
        if not mnemonics_prompt:
            logger.error("Failed to prepare mnemonics prompt")
            return 1
        
        # Display the prepared prompt
        print("\n" + "="*80)
        print("PREPARED PROMPT:")
        print("="*80)
        
        # If the prompt is in the new format with messages
        if "messages" in mnemonics_prompt:
            for i, message in enumerate(mnemonics_prompt["messages"]):
                print(f"Message {i+1} ({message['role']}):")
                print("-" * 40)
                print(message["content"][:2000] + "..." if len(message["content"]) > 2000 else message["content"])
                print()
        # If the prompt is in the old format with a single prompt string
        elif "prompt" in mnemonics_prompt:
            print(mnemonics_prompt["prompt"][:2000] + "..." if len(mnemonics_prompt["prompt"]) > 2000 else mnemonics_prompt["prompt"])
        else:
            print("Unknown prompt format:")
            pprint.pprint(mnemonics_prompt)
        
        # Save the prepared prompt if requested
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(mnemonics_prompt, f, indent=2)
                logger.info(f"Saved prepared prompt to {args.output}")
            except Exception as e:
                logger.error(f"Error saving prepared prompt to {args.output}: {e}")
        
        # Check if the book content is actually included in the prepared prompt
        book_content = substitutions["book_content"]
        prompt_content = ""
        
        if "messages" in mnemonics_prompt:
            for message in mnemonics_prompt["messages"]:
                prompt_content += message["content"]
        elif "prompt" in mnemonics_prompt:
            prompt_content = mnemonics_prompt["prompt"]
            
        if book_content in prompt_content:
            logger.info("✅ Book content is properly included in the prepared prompt")
        else:
            logger.error("❌ Book content is NOT properly included in the prepared prompt")
            
            # Try to find where the substitution should have happened
            if "{book_content}" in prompt_content:
                logger.error("The {book_content} placeholder was not replaced")
            else:
                logger.error("The {book_content} placeholder was replaced, but with different content")
                
                # Check if any part of the book content is included
                title = book_data.get("title", "")
                if title in prompt_content:
                    logger.info(f"✅ Title '{title}' is included in the prompt")
                else:
                    logger.error(f"❌ Title '{title}' is NOT included in the prompt")
                    
                # Check if any quotes are included
                if book_data.get("quotes"):
                    first_quote = book_data["quotes"][0]["quote"]
                    if first_quote in prompt_content:
                        logger.info(f"✅ First quote is included in the prompt")
                    else:
                        logger.error(f"❌ First quote is NOT included in the prompt")
        
    except Exception as e:
        logger.error(f"Error preparing prompts: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())