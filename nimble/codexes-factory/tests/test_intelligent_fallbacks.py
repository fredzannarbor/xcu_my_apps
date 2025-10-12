#!/usr/bin/env python3
"""
Test script for intelligent fallback values in LLM field completion.

This script tests the intelligent fallback value generation in the EnhancedLLMFieldCompleter
to ensure that it provides appropriate fallback values for different field types.
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
from codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter

def test_intelligent_fallbacks():
    """Test intelligent fallback value generation in LLM field completion."""
    logger.info("Starting intelligent fallback value test")
    
    # Create test metadata objects for different book types
    test_books = [
        # Business book
        CodexMetadata(
            title="Strategic Management in the Digital Age",
            author="Jane Smith",
            isbn13="9781234567890",
            publisher="Business Press",
            imprint="Management Series",
            summary_short="A guide to strategic management in the digital era.",
            summary_long="This comprehensive guide explores strategic management principles and practices in the digital age, offering insights for modern business leaders.",
            bisac_codes="BUS063000",  # Business & Economics / Strategic Planning
            page_count=250,
            trim_width_in=6,
            trim_height_in=9,
            publication_date="2025-07-18"
        ),
        # Computer science book
        CodexMetadata(
            title="Python Programming for Data Science",
            author="John Doe",
            isbn13="9789876543210",
            publisher="Tech Books",
            imprint="Programming Series",
            summary_short="Learn Python programming for data science applications.",
            summary_long="This book teaches Python programming with a focus on data science applications, covering key libraries and techniques for data analysis and visualization.",
            bisac_codes="COM051010",  # Computers / Programming / Python
            page_count=350,
            trim_width_in=7,
            trim_height_in=9,
            publication_date="2025-08-15"
        ),
        # Fiction book
        CodexMetadata(
            title="The Lost Garden",
            author="Emily Johnson",
            isbn13="9785432109876",
            publisher="Literary Press",
            imprint="Fiction Classics",
            summary_short="A captivating tale of mystery and discovery.",
            summary_long="In this captivating novel, a young woman discovers a hidden garden that holds secrets to her family's past, leading her on a journey of self-discovery and redemption.",
            bisac_codes="FIC019000",  # Fiction / Literary
            page_count=320,
            trim_width_in=5.5,
            trim_height_in=8.5,
            publication_date="2025-09-10"
        )
    ]
    
    # Create an enhanced LLM field completer
    llm_completer = EnhancedLLMFieldCompleter(
        model_name="gemini/gemini-2.5-flash",
        prompts_path="prompts/enhanced_lsi_field_completion_prompts.json"
    )
    
    # Test fallback values for each book type and prompt key
    prompt_keys = [
        "generate_contributor_bio",
        "suggest_bisac_codes",
        "generate_keywords",
        "create_short_description",
        "suggest_thema_subjects",
        "determine_audience",
        "determine_age_range",
        "extract_lsi_contributor_info",
        "suggest_series_info",
        "generate_enhanced_annotation",
        "generate_illustration_info",
        "generate_enhanced_toc"
    ]
    
    results = {}
    
    for i, book in enumerate(test_books):
        book_type = ["Business", "Computer Science", "Fiction"][i]
        logger.info(f"Testing fallback values for {book_type} book: {book.title}")
        
        book_results = {}
        
        for prompt_key in prompt_keys:
            logger.info(f"Testing fallback value for prompt key: {prompt_key}")
            
            # Get fallback value using the _provide_fallback_value method
            fallback_value = llm_completer._provide_fallback_value(prompt_key, book)
            
            # Log the fallback value
            if isinstance(fallback_value, dict):
                logger.info(f"Fallback value: {json.dumps(fallback_value, indent=2)}")
            else:
                logger.info(f"Fallback value: {fallback_value[:100]}..." if len(str(fallback_value)) > 100 else fallback_value)
            
            # Store the fallback value in the results
            book_results[prompt_key] = fallback_value
        
        results[book.title] = book_results
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"intelligent_fallbacks_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_intelligent_fallbacks()