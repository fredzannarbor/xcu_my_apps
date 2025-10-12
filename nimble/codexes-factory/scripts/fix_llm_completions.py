#!/usr/bin/env python3
"""
Fix LLM completions in existing metadata.

This script fixes the issue where only 2/12 LLM completions are showing up in metadata
by ensuring all LLM completions are properly saved to metadata.llm_completions.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the necessary modules
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from codexes.modules.distribution.field_mapping import FieldMappingRegistry, LLMCompletionStrategy

def load_metadata_from_json(json_path):
    """Load metadata from a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a CodexMetadata object from the JSON data
        metadata = CodexMetadata()
        
        # Load basic metadata fields
        for key, value in data.get('metadata', {}).items():
            setattr(metadata, key, value)
        
        # Load LLM completions if available
        if 'llm_completions' in data:
            metadata.llm_completions = data['llm_completions']
        
        return metadata
    except Exception as e:
        logger.error(f"Error loading metadata from {json_path}: {e}")
        return None

def fix_llm_completions(metadata_path, output_dir=None):
    """Fix LLM completions in existing metadata."""
    logger.info(f"Fixing LLM completions in {metadata_path}")
    
    # Load metadata from JSON file
    metadata = load_metadata_from_json(metadata_path)
    if not metadata:
        logger.error(f"Failed to load metadata from {metadata_path}")
        return None
    
    # Create an LLM field completer
    llm_completer = LLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/lsi_field_completion_prompts.json"
    )
    
    # Check if llm_completions exists
    if not hasattr(metadata, 'llm_completions') or not metadata.llm_completions:
        logger.warning(f"No LLM completions found in {metadata_path}")
        return metadata
    
    # Count LLM completions before fixing
    before_count = len(metadata.llm_completions)
    logger.info(f"Found {before_count} LLM completions before fixing")
    
    # Update metadata fields from LLM completions
    for prompt_key, completion in metadata.llm_completions.items():
        try:
            # Update metadata fields
            llm_completer._update_metadata_fields(metadata, prompt_key, completion)
            logger.info(f"Updated metadata fields for prompt {prompt_key}")
        except Exception as e:
            logger.error(f"Error updating metadata fields for prompt {prompt_key}: {e}")
    
    # Count LLM completions after fixing
    after_count = len(metadata.llm_completions)
    logger.info(f"Found {after_count} LLM completions after fixing")
    
    # Save fixed metadata to a new JSON file
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.dirname(metadata_path)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"fixed_metadata_{timestamp}.json")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {key: value for key, value in metadata.__dict__.items() if not key.startswith('_') and key != 'llm_completions'},
                "llm_completions": metadata.llm_completions
            }, f, indent=2, default=str)
        
        logger.info(f"Fixed metadata saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving fixed metadata to {output_path}: {e}")
    
    return metadata

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fix LLM completions in existing metadata.")
    parser.add_argument("metadata_path", help="Path to the metadata JSON file")
    parser.add_argument("--output-dir", help="Directory to save the fixed metadata")
    args = parser.parse_args()
    
    fix_llm_completions(args.metadata_path, args.output_dir)

if __name__ == "__main__":
    main()