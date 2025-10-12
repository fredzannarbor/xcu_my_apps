#!/usr/bin/env python3
"""
Script to debug the prompt format and find any hidden placeholders.
"""

import json
import sys
import os
import argparse
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def find_placeholders(text):
    """Find all placeholders in the text using regex."""
    # This regex matches {placeholder} patterns
    pattern = r'\{([^{}]+)\}'
    return re.findall(pattern, text)

def debug_prompt_format(prompt_file_path):
    """Debug the prompt format and find any hidden placeholders."""
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
        
        # Find all placeholders
        placeholders = find_placeholders(current_prompt)
        
        # Print the placeholders
        logger.info(f"Found {len(placeholders)} placeholders in the prompt:")
        for i, placeholder in enumerate(placeholders, 1):
            logger.info(f"  {i}. {placeholder}")
        
        # Check for hidden characters
        for i, char in enumerate(current_prompt):
            if ord(char) < 32 or ord(char) > 126:
                logger.warning(f"Found hidden character at position {i}: ord={ord(char)}, hex={hex(ord(char))}")
        
        # Print the prompt with line numbers
        logger.info("Prompt with line numbers:")
        for i, line in enumerate(current_prompt.split('\n'), 1):
            print(f"{i:3d}: {line}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error debugging prompt format: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug prompt format")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    args = parser.parse_args()
    
    if debug_prompt_format(args.prompt_file):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())