#!/usr/bin/env python3
"""
Script to completely rewrite the mnemonics prompt in prompts.json.
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

def rewrite_mnemonics_prompt(prompt_file_path):
    """Completely rewrite the mnemonics prompt."""
    try:
        # Load the prompts file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        # Check if the mnemonics_prompt exists
        if "mnemonics_prompt" not in prompts:
            logger.error(f"mnemonics_prompt not found in {prompt_file_path}")
            return False
        
        # Create a new prompt with the correct format
        new_prompt = r"""Based on the quotations and content in the provided book, generate a list of 5-7 creative mnemonics to help readers remember the key themes, concepts, and insights from the book's quotations. Focus specifically on the book's content, not on the art of mnemonics itself. Return as a valid JSON object with one key 'mnemonics_tex' containing complete LaTeX code ready to be saved as a .tex file. The LaTeX should NOT include \documentclass, \begin{document}, or \end{document} - just the content that will be included in the main document. Each mnemonic acronym and its explanation should total no more than 80 tokens."""
        
        # Update the prompt
        prompts["mnemonics_prompt"]["prompt"] = new_prompt.replace('\\', '\\\\')
        
        # Save the updated prompts file
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)
        
        logger.info(f"Rewrote mnemonics prompt in {prompt_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error rewriting mnemonics prompt: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Rewrite mnemonics prompt")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    args = parser.parse_args()
    
    if rewrite_mnemonics_prompt(args.prompt_file):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())