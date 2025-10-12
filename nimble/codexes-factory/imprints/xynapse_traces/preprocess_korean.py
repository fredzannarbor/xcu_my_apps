#!/usr/bin/env python3
"""
Korean Text Preprocessor for LaTeX Files

This script processes all .tex files in a build directory and wraps Korean text
with the \korean{} command to ensure proper font rendering.
"""

import os
import re
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(mv t
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Korean Unicode range (Hangul Syllables: U+AC00 to U+D7A3)
KOREAN_PATTERN = re.compile(r'[\uAC00-\uD7A3]+')

def wrap_korean_text(text):
    """
    Find Korean text and wrap it with \korean{} command.
    Skip text that's already wrapped.
    """
    # Don't process text that's already inside a \korean{} command
    result = ""
    pos = 0
    in_korean_command = False
    
    while pos < len(text):
        # Check if we're at the start of a \korean command
        if text[pos:pos+8] == "\\korean{":
            in_korean_command = True
            result += text[pos:pos+8]
            pos += 8
        # Check if we're at the end of a \korean command
        elif in_korean_command and text[pos] == "}":
            in_korean_command = False
            result += text[pos]
            pos += 1
        # If we're inside a \korean command, don't process
        elif in_korean_command:
            result += text[pos]
            pos += 1
        else:
            # Look for Korean text outside \korean{} commands
            match = KOREAN_PATTERN.search(text, pos)
            if match and match.start() == pos:
                # Found Korean text, wrap it
                korean_text = match.group(0)
                result += f"\\korean{{{korean_text}}}"
                pos += len(korean_text)
            else:
                # No Korean text at current position
                result += text[pos]
                pos += 1
    
    return result

def process_tex_file(file_path):
    """Process a single .tex file to wrap Korean text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process the content
        processed_content = wrap_korean_text(content)
        
        # Write back if changes were made
        if processed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            logger.info(f"Processed Korean text in {file_path}")
            return True
        else:
            logger.debug(f"No changes needed in {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory):
    """Process all .tex files in the given directory."""
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        logger.error(f"Directory not found: {directory}")
        return False
    
    count = 0
    for file_path in directory_path.glob('**/*.tex'):
        if process_tex_file(file_path):
            count += 1
    
    logger.info(f"Processed Korean text in {count} files")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python preprocess_korean.py <build_directory>")
        sys.exit(1)
    
    build_dir = sys.argv[1]
    logger.info(f"Processing Korean text in .tex files in {build_dir}")
    
    if process_directory(build_dir):
        logger.info("Korean text preprocessing completed successfully")
        sys.exit(0)
    else:
        logger.error("Korean text preprocessing failed")
        sys.exit(1)