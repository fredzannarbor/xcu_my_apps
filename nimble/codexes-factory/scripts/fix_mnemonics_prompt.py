#!/usr/bin/env python3
"""
Script to fix the mnemonics prompt in prompts.json to use the correct placeholder format.
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

def fix_mnemonics_prompt(prompt_file_path):
    """Fix the mnemonics prompt to use the correct placeholder format."""
    try:
        # Load the prompts file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        # Check if the mnemonics_prompt exists
        if "mnemonics_prompt" not in prompts:
            logger.error(f"mnemonics_prompt not found in {prompt_file_path}")
            return False
        
        # Get the current prompt
        current_prompt = prompts["mnemonics_prompt"]["prompt"]
        
        # Check if the prompt already uses the correct format
        if "{book_content}" in current_prompt and "Concept:\n{book_content}" not in current_prompt:
            logger.info("Prompt already uses the correct format")
            return True
        
        # Replace "Concept:\n{book_content}" with just "{book_content}"
        new_prompt = current_prompt.replace("Concept:\n{book_content}", "{book_content}")
        
        # Update the prompt
        prompts["mnemonics_prompt"]["prompt"] = new_prompt
        
        # Save the updated prompts file
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)
        
        logger.info(f"Updated mnemonics prompt in {prompt_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing mnemonics prompt: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix mnemonics prompt")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    args = parser.parse_args()
    
    if fix_mnemonics_prompt(args.prompt_file):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())