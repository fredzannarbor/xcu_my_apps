#!/usr/bin/env python3
"""
Script to rewrite the mnemonics prompt in the imprint-specific prompts.json file.
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
    """Rewrite the mnemonics prompt in the imprint-specific prompts.json file."""
    try:
        # Load the prompts file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        # Check if the mnemonics_prompt exists
        if "mnemonics_prompt" not in prompts:
            logger.error(f"mnemonics_prompt not found in {prompt_file_path}")
            return False
        
        # Create a new prompt with the correct format
        new_prompt = """Based on the quotations and content in the provided book, generate a list of three creative mnemonics to help readers remember the key themes, concepts, and insights from the book's quotations. Focus specifically on the book's content, not on the art of mnemonics itself. Return as a valid JSON object with one key 'mnemonics_tex' containing complete LaTeX code ready to be saved as a .tex file. The LaTeX should NOT include \\documentclass, \\begin{document}, or \\end{document} - just the content that will be included in the main document. Each mnemonic acronym and its explanation should total no more than 80 tokens.

Example format:

% Mnemonics for Key Themes in This Book
\\chapter*{Mnemonics}
\\addcontentsline{toc}{chapter}{Mnemonics}

\\textbf{P}ersistence \\textbf{A}wareness \\textbf{T}rust \\textbf{H}umility (\\textbf{PATH})

\\vspace{1em}

These concepts from the book's quotations remind us that:

\\begin{itemize}
    \\item \\textbf{P}ersistence overcomes obstacles (from Smith's quote on page 12)
    \\item \\textbf{A}wareness of our surroundings leads to insight (from Johnson's observation)
    \\item \\textbf{T}rust in the process yields results (central theme in multiple quotations)
    \\item \\textbf{H}umility opens us to learning (reflected in the Einstein quote)
\\end{itemize}

\\vspace{2em}

\\textbf{C.L.E.A.R. Thinking} (from the critical thinking quotations)

\\begin{itemize}
    \\item \\textbf{C}hallenge assumptions
    \\item \\textbf{L}ook for evidence
    \\item \\textbf{E}valuate alternatives
    \\item \\textbf{A}pply reasoning
    \\item \\textbf{R}eflect on outcomes
\\end{itemize}

{book_content}"""
        
        # Update the prompt
        prompts["mnemonics_prompt"]["prompt"] = new_prompt
        
        # Save the updated prompts file
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)
        
        logger.info(f"Rewrote mnemonics prompt in {prompt_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error rewriting mnemonics prompt: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Rewrite imprint-specific mnemonics prompt")
    parser.add_argument("--prompt-file", default="imprints/xynapse_traces/prompts.json", help="Path to the imprint-specific prompts JSON file")
    args = parser.parse_args()
    
    if rewrite_mnemonics_prompt(args.prompt_file):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())