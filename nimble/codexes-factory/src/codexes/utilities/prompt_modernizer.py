#!/usr/bin/env python3
"""
Prompt Modernizer Utility

This utility converts old-style prompt configurations to the modern messages format
that works with the current LLM caller infrastructure.

Usage:
    python src/codexes/utilities/prompt_modernizer.py <input_file> [output_file]
    
If no output_file is specified, the input file will be updated in place.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_prompt_to_messages(prompt_key: str, prompt_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an old-style prompt configuration to the modern messages format.
    
    Args:
        prompt_key: The key/name of the prompt
        prompt_config: The original prompt configuration
        
    Returns:
        Updated prompt configuration with messages format
    """
    # If already in messages format, return as-is
    if "messages" in prompt_config:
        return prompt_config
    
    # Extract the old prompt text
    old_prompt = prompt_config.get("prompt", "")
    if not old_prompt:
        logger.warning(f"No prompt text found for {prompt_key}")
        return prompt_config
    
    # Determine appropriate system message based on prompt content and tags
    tags = prompt_config.get("tags", [])
    system_content = generate_system_message(prompt_key, tags, old_prompt)
    
    # Determine appropriate parameters
    params = determine_parameters(prompt_key, tags, old_prompt)
    
    # Create the new messages format
    new_config = {
        "params": params,
        "messages": [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user", 
                "content": old_prompt
            }
        ],
        "tags": tags
    }
    
    # Preserve any additional fields that might be important
    for key, value in prompt_config.items():
        if key not in ["prompt", "tags"] and key not in new_config:
            new_config[key] = value
    
    return new_config


def generate_system_message(prompt_key: str, tags: List[str], prompt_text: str) -> str:
    """
    Generate an appropriate system message based on the prompt characteristics.
    """
    # Check for JSON requirement
    requires_json = any(indicator in prompt_text.lower() for indicator in [
        "json", "respond as a single", "return as a", "output should be", "format as"
    ])
    
    # Determine role based on tags and prompt key
    if any(tag in tags for tag in ["metadata", "bibliographic", "publishing"]):
        role = "professional book metadata specialist"
    elif any(tag in tags for tag in ["author", "biography"]):
        role = "professional biographer and publishing expert"
    elif any(tag in tags for tag in ["abstract", "summary"]):
        role = "professional editor and content summarizer"
    elif any(tag in tags for tag in ["glossary", "technical"]):
        role = "subject matter expert and technical writer"
    elif any(tag in tags for tag in ["index", "organization"]):
        role = "professional indexer and book organization specialist"
    elif any(tag in tags for tag in ["marketing", "audience"]):
        role = "book marketing specialist"
    elif any(tag in tags for tag in ["creative", "writing"]):
        role = "professional creative writer"
    elif "lsi" in prompt_key.lower():
        role = "LSI metadata specialist"
    elif "toc" in prompt_key.lower() or "table of contents" in prompt_text.lower():
        role = "book formatting specialist"
    elif "cover" in prompt_key.lower():
        role = "book marketing copywriter"
    else:
        role = "professional publishing specialist"
    
    system_msg = f"You are a {role}."
    
    if requires_json:
        system_msg += " You MUST respond ONLY in valid JSON format. Do not include any text outside the JSON structure."
    
    return system_msg


def determine_parameters(prompt_key: str, tags: List[str], prompt_text: str) -> Dict[str, Any]:
    """
    Determine appropriate parameters based on the prompt characteristics.
    """
    # Default parameters
    params = {
        "temperature": 0.5,
        "max_tokens": 1000
    }
    
    # Adjust temperature based on task type
    if any(tag in tags for tag in ["creative", "writing", "motivation"]):
        params["temperature"] = 0.7
    elif any(tag in tags for tag in ["metadata", "technical", "classification"]):
        params["temperature"] = 0.3
    elif "abstract" in tags or "summary" in tags:
        params["temperature"] = 0.4
    
    # Adjust max_tokens based on expected output length
    if "short" in prompt_text.lower() or "brief" in prompt_text.lower():
        params["max_tokens"] = 300
    elif "long" in prompt_text.lower() or "detailed" in prompt_text.lower():
        params["max_tokens"] = 1500
    elif "annotation" in prompt_key.lower() or "4000 characters" in prompt_text:
        params["max_tokens"] = 1500
    elif any(word in prompt_text.lower() for word in ["biography", "glossary", "index"]):
        params["max_tokens"] = 800
    elif "toc" in prompt_key.lower() or "table of contents" in prompt_text.lower():
        params["max_tokens"] = 800
    
    return params


def modernize_prompt_file(input_path: Path, output_path: Path = None) -> None:
    """
    Modernize all prompts in a JSON file.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path for the output file (defaults to input_path)
    """
    if output_path is None:
        output_path = input_path
    
    logger.info(f"Processing {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {input_path}: {e}")
        return
    
    # Track conversions
    converted_count = 0
    skipped_count = 0
    
    # Process each prompt in the file
    for prompt_key, prompt_config in data.items():
        if isinstance(prompt_config, dict):
            if "prompt" in prompt_config and "messages" not in prompt_config:
                logger.info(f"Converting {prompt_key}")
                data[prompt_key] = convert_prompt_to_messages(prompt_key, prompt_config)
                converted_count += 1
            else:
                logger.debug(f"Skipping {prompt_key} (already modern or invalid format)")
                skipped_count += 1
        else:
            logger.debug(f"Skipping {prompt_key} (not a dict)")
            skipped_count += 1
    
    # Save the updated file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved modernized prompts to {output_path}")
        logger.info(f"   Converted: {converted_count}, Skipped: {skipped_count}")
    except Exception as e:
        logger.error(f"Failed to save {output_path}: {e}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Convert old-style prompts to modern messages format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_file", help="Input JSON file with prompts to convert")
    parser.add_argument("output_file", nargs="?", help="Output file (defaults to input_file)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_file) if args.output_file else None
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist")
        sys.exit(1)
    
    modernize_prompt_file(input_path, output_path)


if __name__ == "__main__":
    main()