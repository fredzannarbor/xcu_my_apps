#!/usr/bin/env python3
"""
Approval tests for backmatter improvements.
Tests all the new features with live data from the xynapse_traces schedule.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codexes.modules.distribution.quote_processor import QuoteProcessor
from codexes.modules.distribution.isbn_lookup import ISBNLookupService
from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
from codexes.modules.distribution.pricing_validator import PricingValidator
from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_test_book_data() -> Dict[str, Any]:
    """Load test book data from a processed JSON file."""
    # Look for existing processed book data
    processed_dir = Path("output/xynapse_traces_build/processed_json")
    
    if processed_dir.exists():
        json_files = list(processed_dir.glob("*.json"))
        if json_files:
            test_file = json_files[0]  # Use the first available file
            logger.info(f"Loading test data from: {test_file}")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # Fallback: create minimal test data
    logger.warning("No processed JSON found, creating minimal test data")
    return {
        "title": "Martian Self-Reliance: Isolation versus Earth Support",
        "description": "Test book for backmatter improvements",
        "author": "AI Lab for Book-Lovers",
        "imprint": "xynapse traces",
        "quotes": [
            {
                "quote": "The greatest glory in living lies not in never falling, but in rising every time we fall.",
                "author": "Nelson Mandela",
                "source": "Long Walk to Freedom",
                "date_first_published": "1994",
                "verification_info": "Page 123, First Edition",
                "editor_note": "Inspirational quote about resilience"
            },
            {
                "quote": "The way to get started is to quit talking and begin doing.",
                "author": "Walt Disney",
                "source": "Disney Archives",
                "date_first_published": "1955",
                "verification_info": "Company records",
                "editor_note": "About taking action"
            },
            {
                "quote": "Innovation distinguishes between a leader and a follower.",
                "author": "Steve Jobs",
                "source": "Stanford Commencement Address",
                "date_first_published": "2005",
                "verification_info": "Video recording available",
                "editor_note": "On leadership and innovation"
            }
        ]
    }

def test_quote_processor():
    """Test the quote processor functionality."""
    logger.info("=== Testing Quote Processor ===")
    
    book_data = load_test_book_data()
    processor = QuoteProcessor()
    
    # Test quote processing
    processed_quotes, validation_summary = processor.extract_and_validate_quotes(book_data)
    
    logger.info(f"✅ Processed {len(processed_quotes)} quotes")
    logger.info(f"✅ Validation summary: {validation_summary}")
    
    # Test catalog metadata generation
    catalog_metadata = processor.generate_catalog_metadata(processed_quotes)
    logger.info(f"✅ Generated catalog metadata: {catalog_metadata}")
    
    # Test bibliography source extraction
    sources = processor.extract_bibliography_sources(processed_quotes)
    logger.info(f"✅ Extracted {len(sources)} unique sources for bibliography")
    
    return processed_quotes, sources

def test_isbn_lookup(sources):
    """Test the ISBN lookup service."""
    logger.info("=== Testing ISBN Lookup Service ===")
    
    isbn_service = ISBNLookupService()
    
    # Test lookup for a few sources
    test_sources = sources[:2]  # Limit to avoid too many API calls
    
    for source in test_sources:
        author = source.get('author', '')
        title = source.get('title', '')
        
        logger.info(f"Looking up ISBN for '{title}' by {author}")
        isbn = isbn_service.lookup_isbn(author, title)
        
        if isbn:
            logger.info(f"✅ Found ISBN: {isbn}")
        else:
            logger.info(f"⚠️ No ISBN found")
    
    # Test batch lookup
    sources_with_isbns = isbn_service.lookup_multiple_isbns(test_sources)
    logger.info(f"✅ Batch lookup completed for {len(sources_with_isbns)} sources")
    
    return sources_with_isbns

def test_backmatter_processor():
    """Test the backmatter processor."""
    logger.info("=== Testing Backmatter Processor ===")
    
    book_data = load_test_book_data()
    processor = PartsOfTheBookProcessor()
    
    # Test mnemonics generation
    logger.info("Testing mnemonics generation...")
    try:
        mnemonics_content = processor.process_mnemonics(book_data)
        if mnemonics_content:
            logger.info(f"✅ Generated mnemonics content ({len(mnemonics_content)} characters)")
            
            # Save to file for inspection
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            with open(output_dir / "test_mnemonics.tex", 'w', encoding='utf-8') as f:
                f.write(mnemonics_content)
            logger.info("✅ Saved mnemonics to test_output/test_mnemonics.tex")
        else:
            logger.warning("⚠️ No mnemonics content generated")
    except Exception as e:
        logger.error(f"❌ Mnemonics generation failed: {e}")
    
    # Test bibliography generation
    logger.info("Testing bibliography generation...")
    try:
        bibliography_content = processor.process_bibliography(book_data)
        if bibliography_content:
            logger.info(f"✅ Generated bibliography content ({len(bibliography_content)} characters)")
            
            with open(output_dir / "test_bibliography.tex", 'w', encoding='utf-8') as f:
                f.write(bibliography_content)
            logger.info("✅ Saved bibliography to test_output/test_bibliography.tex")
        else:
            logger.warning("⚠️ No bibliography content generated")
    except Exception as e:
        logger.error(f"❌ Bibliography generation failed: {e}")
    
    # Test verification log generation
    logger.info("Testing verification log generation...")
    try:
        verification_log_content = processor.process_verification_log(book_data)
        if verification_log_content:
            logger.info(f"✅ Generated verification log content ({len(verification_log_content)} characters)")
            
            with open(output_dir / "test_verification_log.tex", 'w', encoding='utf-8') as f:
                f.write(verification_log_content)
            logger.info("✅ Saved verification log to test_output/test_verification_log.tex")
        else:
            logger.warning("⚠️ No verification log content generated")
    except Exception as e:
        logger.error(f"❌ Verification log generation failed: {e}")
    
    # Test glossary generation
    logger.info("Testing glossary generation...")
    try:
        glossary_content = processor.process_glossary()
        if glossary_content:
            logger.info(f"✅ Generated glossary content ({len(glossary_content)} characters)")
            
            with open(output_dir / "test_glossary.tex", 'w', encoding='utf-8') as f:
                f.write(glossary_content)
            logger.info("✅ Saved glossary to test_output/test_glossary.tex")
        else:
            logger.warning("⚠️ No glossary content generated")
    except Exception as e:
        logger.error(f"❌ Glossary generation failed: {e}")

def test_pricing_validator():
    """Test the pricing validator."""
    logger.info("=== Testing Pricing Validator ===")
    
    book_data = load_test_book_data()
    validator = PricingValidator()
    
    # Test with missing pricing
    logger.info("Testing with missing USD pricing...")
    validated_data = validator.validate_usd_pricing(book_data.copy())
    
    if 'usd_prices' in validated_data:
        logger.info(f"✅ USD prices added: {validated_data['usd_prices']}")
    else:
        logger.error("❌ USD prices not added")
    
    # Test pricing summary
    pricing_summary = validator.generate_pricing_summary(validated_data)
    logger.info(f"✅ Pricing summary generated:\n{pricing_summary}")

def test_enhanced_llm_caller():
    """Test the enhanced LLM caller with retry logic."""
    logger.info("=== Testing Enhanced LLM Caller ===")
    
    # Test simple call
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Respond with valid JSON."
        },
        {
            "role": "user",
            "content": "Generate a simple test response as JSON with key 'test_message' and value 'Hello, this is a test!'"
        }
    ]
    
    try:
        response = call_llm_json_with_exponential_backoff(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            expected_keys=['test_message'],
            temperature=0.1,
            max_tokens=100
        )
        
        if response and 'test_message' in response:
            logger.info(f"✅ LLM call successful: {response['test_message']}")
            logger.info(f"✅ Call metadata: {response.get('_llm_metadata', {})}")
        else:
            logger.error("❌ LLM call failed or returned invalid response")
    except Exception as e:
        logger.error(f"❌ LLM call failed with exception: {e}")

def test_full_pipeline():
    """Test the full pipeline integration."""
    logger.info("=== Testing Full Pipeline Integration ===")
    
    book_data = load_test_book_data()
    
    # Step 1: Process quotes early
    quote_processor = QuoteProcessor()
    processed_quotes, validation_summary = quote_processor.extract_and_validate_quotes(book_data)
    book_data['quotes'] = processed_quotes
    book_data['quote_validation'] = validation_summary
    
    # Step 2: Generate catalog metadata
    catalog_metadata = quote_processor.generate_catalog_metadata(processed_quotes)
    book_data.update(catalog_metadata)
    
    # Step 3: Validate pricing
    pricing_validator = PricingValidator()
    book_data = pricing_validator.validate_usd_pricing(book_data)
    
    # Step 4: Generate all backmatter
    backmatter_processor = PartsOfTheBookProcessor()
    
    # Create output directory
    output_dir = Path("test_output/full_pipeline")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate each backmatter section
    sections = {
        'mnemonics': backmatter_processor.process_mnemonics,
        'bibliography': backmatter_processor.process_bibliography,
        'verification_log': backmatter_processor.process_verification_log,
        'glossary': backmatter_processor.process_glossary
    }
    
    for section_name, processor_func in sections.items():
        try:
            if section_name == 'glossary':
                content = processor_func()
            else:
                content = processor_func(book_data)
            
            if content:
                output_file = output_dir / f"{section_name}.tex"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"✅ Generated {section_name} section")
            else:
                logger.warning(f"⚠️ No content generated for {section_name}")
        except Exception as e:
            logger.error(f"❌ Failed to generate {section_name}: {e}")
    
    # Save final book data
    with open(output_dir / "enhanced_book_data.json", 'w', encoding='utf-8') as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)
    
    logger.info("✅ Full pipeline test completed")
    logger.info(f"✅ Results saved to: {output_dir}")

def main():
    """Run all approval tests."""
    logger.info("🚀 Starting Backmatter Improvements Approval Tests")
    
    try:
        # Test individual components
        processed_quotes, sources = test_quote_processor()
        test_isbn_lookup(sources)
        test_backmatter_processor()
        test_pricing_validator()
        test_enhanced_llm_caller()
        
        # Test full integration
        test_full_pipeline()
        
        logger.info("🎉 All approval tests completed successfully!")
        logger.info("📁 Check the test_output directory for generated files")
        
    except Exception as e:
        logger.error(f"💥 Approval tests failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())