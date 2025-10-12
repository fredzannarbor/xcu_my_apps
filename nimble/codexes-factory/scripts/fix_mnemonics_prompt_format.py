#!/usr/bin/env python3
"""
Script to fix the mnemonics prompt format to use a different approach that avoids conflicts with LaTeX curly braces.
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

def fix_mnemonics_prompt_format(prompt_file_path):
    """Fix the mnemonics prompt format to use a different approach."""
    try:
        # Load the prompts file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        # Check if the mnemonics_prompt exists
        if "mnemonics_prompt" not in prompts:
            logger.error(f"mnemonics_prompt not found in {prompt_file_path}")
            return False
        
        # Create a new prompt using messages format instead of a single prompt string
        prompts["mnemonics_prompt"] = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in creating mnemonics to help readers remember key concepts from books. Your task is to create 5-7 creative mnemonics based on the book content provided by the user. Focus specifically on the book's content, not on the art of mnemonics itself."
                },
                {
                    "role": "user",
                    "content": "Based on the following book content, generate a list of 5-7 creative mnemonics to help readers remember the key themes, concepts, and insights from the book's quotations. Return as a valid JSON object with one key 'mnemonics_tex' containing complete LaTeX code ready to be saved as a .tex file. The LaTeX should NOT include \\documentclass, \\begin{document}, or \\end{document} - just the content that will be included in the main document. Each mnemonic acronym and its explanation should total no more than 80 tokens.\n\nExample format:\n\n% Mnemonics for Key Themes in This Book\n\\chapter*{Mnemonics}\n\\addcontentsline{toc}{chapter}{Mnemonics}\n\n\\textbf{C.L.E.A.R. Thinking} (from the critical thinking quotations)\n\n\\begin{itemize}\n    \\item \\textbf{C}hallenge assumptions\n    \\item \\textbf{L}ook for evidence\n    \\item \\textbf{E}valuate alternatives\n    \\item \\textbf{A}pply reasoning\n    \\item \\textbf{R}eflect on outcomes\n\\end{itemize}\n\nBook Content:\n$book_content$"
                }
            ],
            "params": {
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "tags": [
                "returns_tex",
                "pilsa",
                "back matter",
                "content-generation",
                "json"
            ]
        }
        
        # Save the updated prompts file
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)
        
        logger.info(f"Updated mnemonics prompt format in {prompt_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing mnemonics prompt format: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix mnemonics prompt format")
    parser.add_argument("--prompt-file", default="prompts/prompts.json", help="Path to the prompts JSON file")
    args = parser.parse_args()
    
    if fix_mnemonics_prompt_format(args.prompt_file):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())