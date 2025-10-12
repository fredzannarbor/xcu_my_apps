#!/usr/bin/env python3
"""
Test script for LLM field completion.

This script tests the LLM field completion functionality to ensure that all LLM completions
are properly saved to metadata.llm_completions before filtering via field mapping strategies.
"""

import os
import sys
import json
import logging
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

def test_llm_completions():
    """Test LLM field completion functionality."""
    logger.info("Starting LLM field completion test")
    
    # Create a test metadata object
    metadata = CodexMetadata(
        title="Test Book",
        author="Test Author",
        isbn13="9781234567890",
        publisher="Test Publisher",
        imprint="Test Imprint",
        summary_short="",  # Empty field that should be completed
        summary_long="This is a test book about testing LLM field completion.",
        bisac_codes="COM000000",  # Computer - General
        page_count=100,
        trim_width_in=6,
        trim_height_in=9,
        publication_date="2025-07-18"
    )
    
    # Create an LLM field completer
    llm_completer = LLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/lsi_field_completion_prompts.json"
    )
    
    # Create a field mapping registry
    registry = FieldMappingRegistry()
    
    # Register LLM completion strategies for testing
    registry.register_strategy("Short Description", 
                             LLMCompletionStrategy(llm_completer, "summary_short", "create_short_description"))
    
    registry.register_strategy("BISAC Category 2", 
                             LLMCompletionStrategy(llm_completer, "bisac_category_2", "suggest_bisac_codes"))
    
    registry.register_strategy("BISAC Category 3", 
                             LLMCompletionStrategy(llm_completer, "bisac_category_3", "suggest_bisac_codes"))
    
    registry.register_strategy("Contributor Bio", 
                             LLMCompletionStrategy(llm_completer, "contributor_one_bio", "generate_contributor_bio"))
    
    # Complete missing fields
    logger.info("Completing missing fields")
    metadata = llm_completer.complete_missing_fields(
        metadata=metadata,
        book_content="This is a test book about testing LLM field completion. " * 50,  # Dummy content
        save_to_disk=False  # Don't save to disk for testing
    )
    
    # Check if llm_completions were saved
    if hasattr(metadata, 'llm_completions'):
        logger.info(f"Found {len(metadata.llm_completions)} LLM completions in metadata")
        for prompt_key, completion in metadata.llm_completions.items():
            logger.info(f"Prompt key: {prompt_key}")
            if isinstance(completion, dict):
                for key, value in completion.items():
                    if not key.startswith("_"):  # Skip metadata keys
                        logger.info(f"  {key}: {value[:50]}..." if isinstance(value, str) else f"  {key}: {value}")
    else:
        logger.error("No llm_completions found in metadata")
    
    # Apply field mappings
    logger.info("Applying field mappings")
    lsi_headers = ["Short Description", "BISAC Category 2", "BISAC Category 3", "Contributor Bio"]
    field_values = registry.apply_mappings(metadata, lsi_headers)
    
    # Check if field values were mapped correctly
    logger.info("Field mapping results:")
    for header, value in field_values.items():
        logger.info(f"{header}: {value[:50]}..." if value and isinstance(value, str) else f"{header}: {value}")
    
    # Check if all fields were populated
    empty_fields = [header for header, value in field_values.items() if not value]
    if empty_fields:
        logger.warning(f"Empty fields: {empty_fields}")
    else:
        logger.info("All fields were populated successfully")
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"llm_completion_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "title": metadata.title,
                "author": metadata.author,
                "isbn13": metadata.isbn13,
                "publisher": metadata.publisher,
                "imprint": metadata.imprint
            },
            "llm_completions": metadata.llm_completions,
            "field_values": field_values
        }, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return metadata, field_values

if __name__ == "__main__":
    test_llm_completions()