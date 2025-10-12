#!/usr/bin/env python3
"""
Test script to verify that the mnemonics prompt with messages format works correctly.
"""

import json
import sys
import os
import argparse
from pathlib import Path
import logging

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

def test_mnemonics_with_messages(prompt_file_path, book_json_path):
    """Test the mnemonics prompt with messages format."""
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
        mnemonics_prompt = prompts.get("mnemonics_prompt", {})
        if not mnemonics_prompt:
            logger.error("Failed to get mnemonics prompt")
            return False
        
        # Check if the prompt is in the messages format
        if "messages" not in mnemonics_prompt:
            logger.error("Mnemonics prompt is not in the messages format")
            return False
        
        # Replace $book_content$ placeholder with actual book content
        for i, message in enumerate(mnemonics_prompt["messages"]):
            if "content" in message:
                mnemonics_prompt["messages"][i]["content"] = message["content"].replace("$book_content$", book_content)
        
        # Save the prepared prompt
        with open("test_mnemonics_with_messages_output.json", 'w', encoding='utf-8') as f:
            json.dump(mnemonics_prompt, f, indent=2)
        logger.info("Saved prepared prompt to test_mnemonics_with_messages_output.json")
        
        # Check if the book content is included in the prompt
        prompt_content = ""
        for message in mnemonics_prompt["messages"]:
            prompt_content += message.get("content", "")
        
        if book_content in prompt_content:
            logger.info("✅ Book content is properly included in the prepared prompt")
        else:
            logger.error("❌ Book content is NOT properly included in the prepared prompt")
            
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
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing mnemonics with messages: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test mnemonics with messages")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    parser.add_argument("--book-json", default="sample_book.json", help="Path to the book JSON file")
    args = parser.parse_args()
    
    if test_mnemonics_with_messages(args.prompt_file, args.book_json):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())