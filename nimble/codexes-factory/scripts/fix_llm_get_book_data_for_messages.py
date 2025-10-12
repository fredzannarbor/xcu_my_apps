#!/usr/bin/env python3
"""
Script to fix the llm_get_book_data.py file to handle the new mnemonics prompt format.
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

def fix_llm_get_book_data(file_path):
    """Fix the llm_get_book_data.py file to handle the new mnemonics prompt format."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the prompt_manager.load_and_prepare_prompts call
        load_prompts_pattern = r'formatted_prompts\s*=\s*prompt_manager\.load_and_prepare_prompts\([^)]*\)'
        load_prompts_match = re.search(load_prompts_pattern, content, re.DOTALL)
        
        if not load_prompts_match:
            logger.error(f"Could not find prompt_manager.load_and_prepare_prompts call in {file_path}")
            return False
        
        # Get the load_prompts call
        load_prompts_call = load_prompts_match.group(0)
        
        # Add a custom handler for the mnemonics prompt
        new_content = content.replace(
            load_prompts_call,
            f"""# Custom handling for mnemonics prompt to avoid LaTeX curly brace issues
    mnemonics_prompt = None
    try:
        with open(prompt_template_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
            if "mnemonics_prompt" in prompts_data and "messages" in prompts_data["mnemonics_prompt"]:
                mnemonics_prompt = prompts_data["mnemonics_prompt"].copy()
                # Replace $book_content$ placeholder with actual book content
                for i, message in enumerate(mnemonics_prompt["messages"]):
                    if "content" in message:
                        mnemonics_prompt["messages"][i]["content"] = message["content"].replace("$book_content$", substitutions["book_content"])
    except Exception as e:
        logging.error(f"Error loading mnemonics prompt: {{e}}")
    
    # Load and prepare other prompts
    {load_prompts_call}
    
    # Add the custom mnemonics prompt if it was loaded
    if mnemonics_prompt:
        formatted_prompts["mnemonics_prompt"] = mnemonics_prompt"""
        )
        
        # Write the updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Updated {file_path} to handle the new mnemonics prompt format")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing llm_get_book_data.py: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix llm_get_book_data.py for messages format")
    parser.add_argument("--file-path", default="src/codexes/modules/builders/llm_get_book_data.py", help="Path to the llm_get_book_data.py file")
    args = parser.parse_args()
    
    if fix_llm_get_book_data(args.file_path):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())