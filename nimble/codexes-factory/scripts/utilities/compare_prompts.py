#!/usr/bin/env python3
"""
Compare the results of the original prompts with the enhanced prompts.

This script tests both the original and enhanced prompts on the same book metadata
and compares the results to see if the enhanced prompts produce better results.
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

def load_metadata_from_json(json_path):
    """Load metadata from a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a CodexMetadata object from the JSON data
        metadata = CodexMetadata()
        
        # Load basic metadata fields
        for key, value in data.items():
            setattr(metadata, key, value)
        
        return metadata
    except Exception as e:
        logger.error(f"Error loading metadata from {json_path}: {e}")
        return None

def compare_prompts(metadata_path, output_dir=None):
    """Compare the results of the original prompts with the enhanced prompts."""
    logger.info(f"Comparing prompts using metadata from {metadata_path}")
    
    # Load metadata from JSON file
    metadata = load_metadata_from_json(metadata_path)
    if not metadata:
        logger.error(f"Failed to load metadata from {metadata_path}")
        return None
    
    # Create output directory if it doesn't exist
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.dirname(metadata_path)
    
    # Create a copy of the metadata for each prompt set
    original_metadata = metadata
    enhanced_metadata = metadata
    
    # Create LLM field completers for each prompt set
    original_completer = LLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/lsi_field_completion_prompts.json"
    )
    
    enhanced_completer = LLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/enhanced_lsi_field_completion_prompts.json"
    )
    
    # Complete missing fields using original prompts
    logger.info("Completing missing fields using original prompts...")
    original_metadata = original_completer.complete_missing_fields(
        metadata=original_metadata,
        book_content=None,
        save_to_disk=False
    )
    
    # Complete missing fields using enhanced prompts
    logger.info("Completing missing fields using enhanced prompts...")
    enhanced_metadata = enhanced_completer.complete_missing_fields(
        metadata=enhanced_metadata,
        book_content=None,
        save_to_disk=False
    )
    
    # Compare the results
    logger.info("Comparing results...")
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "metadata_path": metadata_path,
        "original_completions": original_metadata.llm_completions if hasattr(original_metadata, 'llm_completions') else {},
        "enhanced_completions": enhanced_metadata.llm_completions if hasattr(enhanced_metadata, 'llm_completions') else {},
        "comparison": {}
    }
    
    # Count the number of completions in each set
    original_count = len(comparison["original_completions"])
    enhanced_count = len(comparison["enhanced_completions"])
    
    logger.info(f"Original prompts: {original_count} completions")
    logger.info(f"Enhanced prompts: {enhanced_count} completions")
    
    # Compare the completions
    all_keys = set(comparison["original_completions"].keys()) | set(comparison["enhanced_completions"].keys())
    for key in all_keys:
        original_value = comparison["original_completions"].get(key, {})
        enhanced_value = comparison["enhanced_completions"].get(key, {})
        
        if key in comparison["original_completions"] and key in comparison["enhanced_completions"]:
            # Both have the key, compare the values
            comparison["comparison"][key] = {
                "status": "both",
                "original_length": len(json.dumps(original_value)),
                "enhanced_length": len(json.dumps(enhanced_value)),
                "difference": len(json.dumps(enhanced_value)) - len(json.dumps(original_value))
            }
        elif key in comparison["original_completions"]:
            # Only original has the key
            comparison["comparison"][key] = {
                "status": "original_only",
                "original_length": len(json.dumps(original_value)),
                "enhanced_length": 0,
                "difference": -len(json.dumps(original_value))
            }
        else:
            # Only enhanced has the key
            comparison["comparison"][key] = {
                "status": "enhanced_only",
                "original_length": 0,
                "enhanced_length": len(json.dumps(enhanced_value)),
                "difference": len(json.dumps(enhanced_value))
            }
    
    # Save the comparison to a JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"prompt_comparison_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    logger.info(f"Comparison saved to {output_path}")
    
    # Generate a summary report
    summary = {
        "original_count": original_count,
        "enhanced_count": enhanced_count,
        "both_count": sum(1 for key, value in comparison["comparison"].items() if value["status"] == "both"),
        "original_only_count": sum(1 for key, value in comparison["comparison"].items() if value["status"] == "original_only"),
        "enhanced_only_count": sum(1 for key, value in comparison["comparison"].items() if value["status"] == "enhanced_only"),
        "average_length_difference": sum(value["difference"] for value in comparison["comparison"].values()) / len(comparison["comparison"]) if comparison["comparison"] else 0
    }
    
    logger.info("Summary:")
    logger.info(f"  Original completions: {summary['original_count']}")
    logger.info(f"  Enhanced completions: {summary['enhanced_count']}")
    logger.info(f"  Both have: {summary['both_count']}")
    logger.info(f"  Original only: {summary['original_only_count']}")
    logger.info(f"  Enhanced only: {summary['enhanced_only_count']}")
    logger.info(f"  Average length difference: {summary['average_length_difference']:.2f} characters")
    
    return comparison

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Compare the results of the original prompts with the enhanced prompts.")
    parser.add_argument("metadata_path", help="Path to the metadata JSON file")
    parser.add_argument("--output-dir", help="Directory to save the comparison results")
    args = parser.parse_args()
    
    compare_prompts(args.metadata_path, args.output_dir)

if __name__ == "__main__":
    main()