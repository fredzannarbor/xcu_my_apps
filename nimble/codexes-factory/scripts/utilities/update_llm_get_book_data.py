#!/usr/bin/env python3
"""
Script to update the llm_get_book_data.py file with our custom implementation.
"""

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

def update_llm_get_book_data(file_path):
    """Update the llm_get_book_data.py file with our custom implementation."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the substitutions dictionary
        substitutions_pattern = r'substitutions\s*=\s*\{[^}]*\}'
        substitutions_match = re.search(substitutions_pattern, content, re.DOTALL)
        
        if not substitutions_match:
            logger.error(f"Could not find substitutions dictionary in {file_path}")
            return False
        
        # Get the substitutions dictionary
        substitutions_dict = substitutions_match.group(0)
        
        # Add the book_content preparation code
        book_content_prep = """
    # Prepare the book content for the mnemonics prompt
    book_content = f"Title: {title}\\n\\nDescription: {description}"
    
    # For mnemonics prompt, we need to include the quotes if they exist
    quotes = book_data.get("quotes", [])
    quotes_text = ""
    
    if quotes:
        quotes_text = "\\n\\nQuotations in this book:\\n"
        # Use all quotes but be mindful of potential token limits
        num_quotes = len(quotes)
        
        # If there are many quotes, provide a summary of themes and authors
        if num_quotes > 90:
            # Include a sample of quotes (first 10, middle 10, last 10)
            sample_quotes = quotes[:10] + quotes[num_quotes//2-5:num_quotes//2+5] + quotes[-10:]
            
            # Get all unique authors
            all_authors = set(quote.get("author", "Unknown") for quote in quotes)
            authors_text = ", ".join(list(all_authors)[:20])  # Limit to 20 authors if there are many
            if len(all_authors) > 20:
                authors_text += f", and {len(all_authors) - 20} more"
                
            # Add summary information
            quotes_text += f"This book contains {num_quotes} quotes from authors including {authors_text}.\\n"
            quotes_text += f"Here is a representative sample of {len(sample_quotes)} quotes:\\n\\n"
            
            # Add the sample quotes
            for i, quote in enumerate(sample_quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \\"{q_text}\\" - {q_author}, {q_source}\\n"
        else:
            # If there aren't too many quotes, include all of them
            for i, quote in enumerate(quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \\"{q_text}\\" - {q_author}, {q_source}\\n"
    
    book_content += quotes_text
"""
        
        # Replace the substitutions dictionary
        new_substitutions = """
    # Custom handling for mnemonics prompt to avoid LaTeX curly brace issues
    mnemonics_prompt = None
    try:
        with open(prompt_template_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
            if "mnemonics_prompt" in prompts_data and "messages" in prompts_data["mnemonics_prompt"]:
                mnemonics_prompt = prompts_data["mnemonics_prompt"].copy()
                # Replace $book_content$ placeholder with actual book content
                for i, message in enumerate(mnemonics_prompt["messages"]):
                    if "content" in message:
                        mnemonics_prompt["messages"][i]["content"] = message["content"].replace("$book_content$", book_content)
    except Exception as e:
        logging.error(f"Error loading mnemonics prompt: {e}")
    
    substitutions = {
        "book_content": book_content,
        "topic": title,
        "stream": stream,
        "description": description,
        "quotes_per_book": book_data.get("quotes_per_book", len(quotes) if quotes else 90),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", "")
    }
"""
        
        # Replace the substitutions dictionary
        new_content = content.replace(substitutions_dict, new_substitutions)
        
        # Find the prompt_manager.load_and_prepare_prompts call
        load_prompts_pattern = r'formatted_prompts\s*=\s*prompt_manager\.load_and_prepare_prompts\([^)]*\)'
        load_prompts_match = re.search(load_prompts_pattern, new_content, re.DOTALL)
        
        if not load_prompts_match:
            logger.error(f"Could not find prompt_manager.load_and_prepare_prompts call in {file_path}")
            return False
        
        # Get the load_prompts call
        load_prompts_call = load_prompts_match.group(0)
        
        # Add the custom mnemonics prompt handling
        new_load_prompts = f"""
    # Load and prepare prompts
    {load_prompts_call}
    
    # Add the custom mnemonics prompt if it was loaded
    if mnemonics_prompt:
        formatted_prompts["mnemonics_prompt"] = mnemonics_prompt
"""
        
        # Replace the load_prompts call
        new_content = new_content.replace(load_prompts_call, new_load_prompts)
        
        # Write the updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Updated {file_path} with custom implementation")
        return True
    
    except Exception as e:
        logger.error(f"Error updating llm_get_book_data.py: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Update llm_get_book_data.py")
    parser.add_argument("--file-path", default="src/codexes/modules/builders/llm_get_book_data.py", help="Path to the llm_get_book_data.py file")
    args = parser.parse_args()
    
    if update_llm_get_book_data(args.file_path):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())