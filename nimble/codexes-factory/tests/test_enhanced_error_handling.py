#!/usr/bin/env python3
"""
Test script for enhanced error handling in LLM field completion.

This script tests the enhanced error handling functionality in the EnhancedLLMFieldCompleter
to ensure that it properly handles errors and provides fallback values.
"""

import os
import sys
import json
import logging
import time
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
from codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter

def test_error_handling():
    """Test enhanced error handling in LLM field completion."""
    logger.info("Starting enhanced error handling test")
    
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
    
    # Create an enhanced LLM field completer
    llm_completer = EnhancedLLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/enhanced_lsi_field_completion_prompts.json"
    )
    
    # Test retry logic by simulating a failure
    logger.info("Testing retry logic with simulated failure")
    
    # Monkey patch the _process_prompt method to simulate a failure
    original_process_prompt = llm_completer._process_prompt
    
    def mock_process_prompt(prompt_key, metadata, book_content=None, max_retries=3, initial_delay=1):
        """Mock _process_prompt method that simulates a failure."""
        if prompt_key == "create_short_description":
            # Simulate a failure for the first two attempts
            if metadata.llm_completion_attempts.get(prompt_key, 0) < 3:
                logger.info(f"Simulating failure for attempt {metadata.llm_completion_attempts.get(prompt_key, 0)}")
                raise Exception("Simulated failure")
            else:
                # Succeed on the third attempt
                logger.info("Simulating success on third attempt")
                return "This is a test short description that succeeded after retries."
        else:
            # Use the original method for other prompts
            return original_process_prompt(prompt_key, metadata, book_content, max_retries, initial_delay)
    
    # Replace the _process_prompt method with our mock
    llm_completer._process_prompt = mock_process_prompt
    
    # Complete missing fields with retry logic
    logger.info("Completing missing fields with retry logic")
    metadata = llm_completer.complete_missing_fields(
        metadata=metadata,
        book_content="This is a test book about testing LLM field completion. " * 50,  # Dummy content
        save_to_disk=False,  # Don't save to disk for testing
        max_retries=3,
        initial_delay=1  # Use a short delay for testing
    )
    
    # Check if the field was completed after retries
    if hasattr(metadata, 'llm_completions') and "create_short_description" in metadata.llm_completions:
        result = metadata.llm_completions["create_short_description"]
        logger.info(f"Field completed after retries: {result}")
    else:
        logger.error("Field was not completed after retries")
    
    # Check retry tracking
    if hasattr(metadata, 'llm_completion_attempts'):
        logger.info(f"Retry tracking: {metadata.llm_completion_attempts}")
    
    # Test fallback values by simulating a complete failure
    logger.info("Testing fallback values with simulated complete failure")
    
    # Monkey patch the _process_prompt method to simulate a complete failure
    def mock_process_prompt_failure(prompt_key, metadata, book_content=None, max_retries=3, initial_delay=1):
        """Mock _process_prompt method that always fails."""
        if prompt_key == "suggest_bisac_codes":
            # Always fail for this prompt
            logger.info(f"Simulating complete failure for {prompt_key}")
            raise Exception("Simulated complete failure")
        else:
            # Use the original method for other prompts
            return original_process_prompt(prompt_key, metadata, book_content, max_retries, initial_delay)
    
    # Replace the _process_prompt method with our mock
    llm_completer._process_prompt = mock_process_prompt_failure
    
    # Complete missing fields with fallback values
    logger.info("Completing missing fields with fallback values")
    metadata = llm_completer.complete_missing_fields(
        metadata=metadata,
        book_content="This is a test book about testing LLM field completion. " * 50,  # Dummy content
        save_to_disk=False,  # Don't save to disk for testing
        max_retries=2,
        initial_delay=1  # Use a short delay for testing
    )
    
    # Check if the fallback value was used
    if hasattr(metadata, 'llm_completions') and "suggest_bisac_codes" in metadata.llm_completions:
        result = metadata.llm_completions["suggest_bisac_codes"]
        logger.info(f"Fallback value used: {result}")
    else:
        logger.error("Fallback value was not used")
    
    # Check failure tracking
    if hasattr(metadata, 'llm_completion_failures'):
        logger.info(f"Failure tracking: {metadata.llm_completion_failures}")
    
    # Restore the original _process_prompt method
    llm_completer._process_prompt = original_process_prompt
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"error_handling_test_{timestamp}.json")
    
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
            "llm_completion_attempts": metadata.llm_completion_attempts,
            "llm_completion_failures": metadata.llm_completion_failures
        }, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return metadata

if __name__ == "__main__":
    test_error_handling()