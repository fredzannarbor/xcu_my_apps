#!/usr/bin/env python3
"""
LSI System Integration Test

This script runs a comprehensive integration test of the LSI CSV generation system
to validate that all bug fixes work together correctly.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_lsi_integration():
    """Run comprehensive LSI integration test."""
    print("🚀 Starting LSI System Integration Test")
    print("=" * 60)
    
    # Test 1: JSON Parsing with Fallbacks
    print("\n1. Testing JSON Parsing with Fallbacks...")
    try:
        from codexes.core.llm_caller import _parse_json_with_fallbacks
        
        test_cases = [
            '{"title": "Test Book", "author": "Test Author"}',  # Valid JSON
            '{"title": "Test Book", "author": "Test Author"',   # Malformed JSON
            'Title: Test Book\nAuthor: Test Author',            # Conversational
            '',                                                 # Empty
        ]
        
        for i, test_case in enumerate(test_cases):
            result = _parse_json_with_fallbacks(test_case)
            assert isinstance(result, dict), f"Test case {i+1} failed"
            print(f"   ✅ Test case {i+1}: {type(result).__name__}")
        
        print("   ✅ JSON parsing with fallbacks: PASSED")
    except Exception as e:
        print(f"   ❌ JSON parsing test failed: {e}")
        return False
    
    # Test 2: BISAC Code Validation
    print("\n2. Testing BISAC Code Validation...")
    try:
        from codexes.modules.distribution.bisac_validator import get_bisac_validator
        
        validator = get_bisac_validator()
        
        # Test valid codes
        valid_codes = ['BUS001000', 'COM002000', 'SCI003000']
        for code in valid_codes:
            result = validator.validate_bisac_code(code)
            assert result.is_valid, f"Valid code {code} failed validation"
        
        # Test invalid codes
        invalid_codes = ['INVALID', 'BUS999999', '123456789']
        for code in invalid_codes:
            result = validator.validate_bisac_code(code)
            assert not result.is_valid, f"Invalid code {code} passed validation"
        
        # Test suggestions
        suggestions = validator.suggest_bisac_codes(['technology', 'programming'], max_suggestions=3)
        assert len(suggestions) <= 3, "Too many suggestions returned"
        assert all(len(s) == 3 for s in suggestions), "Invalid suggestion format"
        
        print("   ✅ BISAC validation: PASSED")
    except Exception as e:
        print(f"   ❌ BISAC validation test failed: {e}")
        return False
    
    # Test 3: Text Formatting and Validation
    print("\n3. Testing Text Formatting and Validation...")
    try:
        from codexes.modules.distribution.text_formatter import get_text_formatter
        
        formatter = get_text_formatter()
        
        # Test length validation
        short_text = "This is a short description."
        result = formatter.validate_field_length("short_description", short_text)
        assert result.is_valid, "Short text validation failed"
        
        # Test truncation
        long_text = "A" * 500  # Exceeds 350 character limit
        result = formatter.validate_field_length("short_description", long_text)
        assert not result.is_valid, "Long text should be invalid"
        assert result.suggested_text is not None, "No truncation suggested"
        assert len(result.suggested_text) <= 350, "Truncation failed"
        
        # Test HTML cleaning
        html_text = "<p>This is <b>bold</b> text.</p>"
        cleaned = formatter.clean_text(html_text)
        assert "<" not in cleaned, "HTML tags not removed"
        assert "bold" in cleaned, "Content was lost"
        
        # Test keyword formatting
        keywords = "AI, artificial intelligence; machine learning, AI"
        formatted = formatter.format_keywords(keywords)
        keyword_list = formatted.split("; ")
        assert len(keyword_list) == len(set(k.lower() for k in keyword_list)), "Duplicates not removed"
        
        print("   ✅ Text formatting: PASSED")
    except Exception as e:
        print(f"   ❌ Text formatting test failed: {e}")
        return False
    
    # Test 4: Configuration System
    print("\n4. Testing Configuration System...")
    try:
        from codexes.modules.distribution.multi_level_config import MultiLevelConfiguration, ConfigurationContext
        
        # Create temporary configuration
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir)
        
        # Create test configs
        default_config = {"default_value": "global", "override_test": "global"}
        default_path = config_dir / "default_lsi_config.json"
        with open(default_path, 'w') as f:
            json.dump(default_config, f)
        
        publishers_dir = config_dir / "publishers"
        publishers_dir.mkdir()
        publisher_config = {"publisher_value": "test_pub", "override_test": "publisher"}
        with open(publishers_dir / "test_pub.json", 'w') as f:
            json.dump(publisher_config, f)
        
        # Test configuration loading
        config = MultiLevelConfiguration(str(config_dir))
        context = ConfigurationContext(publisher_name="test_pub")
        
        # Test inheritance
        value = config.get_value("override_test", context)
        assert value == "publisher", f"Expected 'publisher', got '{value}'"
        
        default_value = config.get_value("default_value", context)
        assert default_value == "global", f"Expected 'global', got '{default_value}'"
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        print("   ✅ Configuration system: PASSED")
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False
    
    # Test 5: Integration Test
    print("\n5. Testing System Integration...")
    try:
        # Test that all components work together
        validator = get_bisac_validator()
        formatter = get_text_formatter()
        
        # Simulate processing a book
        book_data = {
            'title': 'The Art of Programming',
            'author': 'Jane Developer',
            'description': 'A comprehensive guide to programming best practices and techniques.',
            'bisac_code': 'COM051000'
        }
        
        # Validate BISAC
        bisac_result = validator.validate_bisac_code(book_data['bisac_code'])
        assert bisac_result.is_valid, "BISAC validation failed in integration"
        
        # Validate text fields
        title_result = formatter.validate_field_length('title', book_data['title'])
        assert title_result.is_valid, "Title validation failed in integration"
        
        desc_result = formatter.validate_field_length('short_description', book_data['description'])
        assert desc_result.is_valid, "Description validation failed in integration"
        
        # Test JSON parsing
        json_data = json.dumps(book_data)
        parsed_result = _parse_json_with_fallbacks(json_data)
        assert parsed_result['title'] == book_data['title'], "JSON parsing failed in integration"
        
        print("   ✅ System integration: PASSED")
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False
    
    # Test Summary
    print("\n" + "=" * 60)
    print("🎉 LSI System Integration Test: ALL TESTS PASSED")
    print("\nSystem Status:")
    print("   ✅ JSON parsing with fallback strategies")
    print("   ✅ BISAC code validation and suggestions")
    print("   ✅ Text formatting and intelligent truncation")
    print("   ✅ Multi-level configuration inheritance")
    print("   ✅ End-to-end system integration")
    print("\n🚀 LSI CSV generation system is ready for production!")
    
    return True


if __name__ == "__main__":
    success = test_lsi_integration()
    sys.exit(0 if success else 1)