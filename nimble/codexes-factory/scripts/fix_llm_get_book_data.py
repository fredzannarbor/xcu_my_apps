#!/usr/bin/env python3
"""
Script to fix the llm_get_book_data.py file to properly handle the mnemonics prompt.
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
    """Fix the llm_get_book_data.py file to properly handle the mnemonics prompt."""
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
        
        # Add the document placeholder
        new_substitutions_dict = substitutions_dict.replace(
            '"book_content": f"Title: {title}\\n\\nDescription: {description}{quotes_text}",',
            '"book_content": f"Title: {title}\\n\\nDescription: {description}{quotes_text}",\n        "document": f"Title: {title}\\n\\nDescription: {description}{quotes_text}",'
        )
        
        # Replace the substitutions dictionary
        new_content = content.replace(substitutions_dict, new_substitutions_dict)
        
        # Write the updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Updated {file_path} to add the document placeholder")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing llm_get_book_data.py: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix llm_get_book_data.py")
    parser.add_argument("--file-path", default="src/codexes/modules/builders/llm_get_book_data.py", help="Path to the llm_get_book_data.py file")
    args = parser.parse_args()
    
    if fix_llm_get_book_data(args.file_path):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())