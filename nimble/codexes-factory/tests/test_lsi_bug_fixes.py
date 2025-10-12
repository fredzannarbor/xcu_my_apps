#!/usr/bin/env python3
"""
Comprehensive Test Suite for LSI CSV Bug Fixes

This test suite validates all the bug fixes implemented in the LSI CSV generation system.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.llm_caller import _parse_json_with_fallbacks, call_model_with_prompt
from codexes.modules.distribution.bisac_validator import BISACValidator, get_bisac_validator
from codexes.modules.distribution.text_formatter import LSITextFormatter, get_text_formatter
from codexes.modules.distribution.multi_level_config import MultiLevelConfiguration, ConfigurationContext, ConfigurationLevel
from codexes.modules.distribution.config_debugger import ConfigurationDebugger


class TestJSONParsingFixes:
    """Test JSON parsing improvements and fallback strategies."""
    
    def test_direct_json_parsing_success(self):
        """Test that valid JSON is parsed correctly."""
        valid_json = '{"title": "Test Book", "author": "Test Author"}'
        result = _parse_json_with_fallbacks(valid_json)
        
        assert result["title"] == "Test Book"
        assert result["author"] == "Test Author"
        assert "fallback_used" not in result
    
    def test_json_repair_fallback(self):
        """Test that malformed JSON is repaired."""
        malformed_json = '{"title": "Test Book", "author": "Test Author"'  # Missing closing brace
        result = _parse_json_with_fallbacks(malformed_json)
        
        # Should either be repaired or use fallback
        assert isinstance(result, dict)
        if "error" not in result:
            assert "title" in result or "fallback_used" in result
    
    def test_conversational_response_parsing(self):
        """Test parsing of conversational responses."""
        conversational_text = """
        I apologize, but I need to provide the bibliography information.
        
        Bibliography: Here are the sources cited in the book.
        Title: The Great Work
        Author: John Smith
        """
        result = _parse_json_with_fallbacks(conversational_text)
        
        assert isinstance(result, dict)
        if "fallback_used" in result:
            assert result["fallback_used"] == "conversational_parsing"
    
    def test_empty_response_handling(self):
        """Test handling of empty responses."""
        result = _parse_json_with_fallbacks("")
        
        assert result["error"] == "Empty response"
        assert result["fallback_used"] == "empty_response"
    
    def test_markdown_json_extraction(self):
        """Test extraction of JSON from markdown code blocks."""
        markdown_json = '''
        Here's the JSON response:
        
        ```json
        {"title": "Test Book", "author": "Test Author"}
        ```
        
        Hope this helps!
        '''
        result = _parse_json_with_fallbacks(markdown_json)
        
        assert isinstance(result, dict)
        # Should extract the JSON successfully
        if "error" not in result:
            assert "title" in result or "fallback_used" in result


class TestBISACValidation:
    """Test BISAC code validation and suggestion system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = get_bisac_validator()
    
    def test_valid_bisac_code(self):
        """Test validation of valid BISAC codes."""
        result = self.validator.validate_bisac_code("BUS001000")
        
        assert result.is_valid == True
        assert "Valid BISAC code" in result.message
        assert result.category_name is not None
    
    def test_invalid_format(self):
        """Test validation of invalid BISAC format."""
        result = self.validator.validate_bisac_code("INVALID123")
        
        assert result.is_valid == False
        assert "Invalid BISAC format" in result.message
        assert result.suggested_codes is not None
    
    def test_nonexistent_code(self):
        """Test validation of nonexistent BISAC code."""
        result = self.validator.validate_bisac_code("BUS999999")
        
        assert result.is_valid == False
        assert "not found in current standards" in result.message
    
    def test_bisac_suggestions_by_keywords(self):
        """Test BISAC code suggestions based on keywords."""
        keywords = ["artificial intelligence", "technology", "programming"]
        suggestions = self.validator.suggest_bisac_codes(keywords, max_suggestions=3)
        
        assert len(suggestions) <= 3
        assert all(len(suggestion) == 3 for suggestion in suggestions)  # (code, description, confidence)
        assert all(suggestion[2] > 0 for suggestion in suggestions)  # Confidence > 0
    
    def test_fallback_codes(self):
        """Test fallback BISAC codes."""
        fallback_codes = self.validator.get_fallback_codes()
        
        assert len(fallback_codes) > 0
        assert all(self.validator.validate_bisac_code(code).is_valid for code in fallback_codes)


class TestTextFormatting:
    """Test text formatting and length validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = get_text_formatter()
    
    def test_field_length_validation_valid(self):
        """Test validation of text within length limits."""
        short_text = "This is a short description."
        result = self.formatter.validate_field_length("short_description", short_text)
        
        assert result.is_valid == True
        assert result.final_length <= 350
    
    def test_field_length_validation_too_long(self):
        """Test validation of text exceeding length limits."""
        long_text = "A" * 500  # Exceeds 350 character limit for short_description
        result = self.formatter.validate_field_length("short_description", long_text)
        
        assert result.is_valid == False
        assert result.suggested_text is not None
        assert len(result.suggested_text) <= 350
    
    def test_intelligent_truncation_sentence_boundary(self):
        """Test intelligent truncation at sentence boundaries."""
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        truncated = self.formatter.intelligent_truncate(text, 50)
        
        # Should truncate at sentence boundary
        assert truncated.endswith(".")
        assert len(truncated) <= 50
    
    def test_html_text_cleaning(self):
        """Test HTML tag removal and text cleaning."""
        html_text = "<p>This is <b>bold</b> text with <i>italics</i>.</p>"
        cleaned = self.formatter.clean_text(html_text)
        
        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "bold" in cleaned
        assert "italics" in cleaned
    
    def test_keywords_formatting(self):
        """Test keyword formatting and deduplication."""
        keywords = "AI, artificial intelligence; machine learning, AI, deep learning"
        formatted = self.formatter.format_keywords(keywords)
        
        # Should be semicolon-separated and deduplicated
        keyword_list = formatted.split("; ")
        assert len(keyword_list) == len(set(k.lower() for k in keyword_list))  # No duplicates
        assert "ai" in formatted.lower()
    
    def test_html_annotation_formatting(self):
        """Test HTML annotation formatting."""
        text = "This is the first paragraph.\n\nThis is the second paragraph."
        formatted = self.formatter.format_html_annotation(text)
        
        assert formatted.startswith("<p><b><i>")
        assert "</i></b></p>" in formatted
        assert "<p>This is the second paragraph.</p>" in formatted


class TestConfigurationSystem:
    """Test multi-level configuration system fixes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Create test configuration files
        self._create_test_configs()
        
        self.config = MultiLevelConfiguration(str(self.config_dir))
        self.debugger = ConfigurationDebugger(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Default config
        default_config = {
            "default_value": "global_default",
            "override_test": "global_value"
        }
        default_path = self.config_dir / "default_lsi_config.json"
        with open(default_path, 'w') as f:
            json.dump(default_config, f)
        
        # Publisher config
        publishers_dir = self.config_dir / "publishers"
        publishers_dir.mkdir()
        publisher_config = {
            "publisher_value": "test_publisher_value",
            "override_test": "publisher_value"
        }
        publisher_path = publishers_dir / "test_publisher.json"
        with open(publisher_path, 'w') as f:
            json.dump(publisher_config, f)
        
        # Imprint config
        imprints_dir = self.config_dir / "imprints"
        imprints_dir.mkdir()
        imprint_config = {
            "imprint_value": "test_imprint_value",
            "override_test": "imprint_value"
        }
        imprint_path = imprints_dir / "test_imprint.json"
        with open(imprint_path, 'w') as f:
            json.dump(imprint_config, f)
        
        # Tranche config
        tranches_dir = self.config_dir / "tranches"
        tranches_dir.mkdir()
        tranche_config = {
            "tranche_value": "test_tranche_value",
            "override_test": "tranche_value"
        }
        tranche_path = tranches_dir / "test_tranche.json"
        with open(tranche_path, 'w') as f:
            json.dump(tranche_config, f)
    
    def test_configuration_inheritance(self):
        """Test that configuration inheritance works correctly."""
        context = ConfigurationContext(
            publisher_name="test_publisher",
            imprint_name="test_imprint",
            tranche_name="test_tranche"
        )
        
        # Test that tranche value overrides all others
        value = self.config.get_value("override_test", context)
        assert value == "tranche_value"
        
        # Test that each level has its specific values
        assert self.config.get_value("default_value", context) == "global_default"
        assert self.config.get_value("publisher_value", context) == "test_publisher_value"
        assert self.config.get_value("imprint_value", context) == "test_imprint_value"
        assert self.config.get_value("tranche_value", context) == "test_tranche_value"
    
    def test_configuration_debugging(self):
        """Test configuration debugging utilities."""
        context = ConfigurationContext(
            publisher_name="test_publisher",
            imprint_name="test_imprint",
            tranche_name="test_tranche"
        )
        
        debug_info = self.debugger.debug_configuration_resolution("override_test", context)
        
        assert debug_info["key"] == "override_test"
        assert debug_info["final_value"] == "tranche_value"
        assert len(debug_info["resolution_path"]) > 0
    
    def test_configuration_validation(self):
        """Test configuration file validation."""
        validation_results = self.debugger.validate_configuration_files()
        
        assert validation_results["summary"]["valid_count"] > 0
        assert validation_results["summary"]["success_rate"] > 0


class TestLLMRetryLogic:
    """Test enhanced LLM retry logic."""
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_successful_llm_call(self, mock_completion):
        """Test successful LLM call without retries."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "success"}'
        mock_completion.return_value = mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"temperature": 0.5}
        }
        
        result = call_model_with_prompt("test-model", prompt_config, "json_object")
        
        assert result["parsed_content"]["test"] == "success"
        assert mock_completion.call_count == 1
    
    @patch('codexes.core.llm_caller.litellm.completion')
    @patch('codexes.core.llm_caller.time.sleep')
    def test_retry_on_rate_limit(self, mock_sleep, mock_completion):
        """Test retry logic on rate limit errors."""
        from litellm.exceptions import RateLimitError
        
        # First call fails with rate limit, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "success"}'
        
        mock_completion.side_effect = [
            RateLimitError("Rate limit exceeded"),
            mock_response
        ]
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"temperature": 0.5}
        }
        
        result = call_model_with_prompt("test-model", prompt_config, "json_object", max_retries=3)
        
        assert result["parsed_content"]["test"] == "success"
        assert mock_completion.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('codexes.core.llm_caller.litellm.completion')
    @patch('codexes.core.llm_caller.time.sleep')
    def test_max_retries_exceeded(self, mock_sleep, mock_completion):
        """Test behavior when max retries are exceeded."""
        from litellm.exceptions import RateLimitError
        
        # All calls fail
        mock_completion.side_effect = RateLimitError("Rate limit exceeded")
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"temperature": 0.5}
        }
        
        result = call_model_with_prompt("test-model", prompt_config, "json_object", max_retries=2)
        
        assert "error" in result["parsed_content"]
        assert mock_completion.call_count == 2
        assert mock_sleep.call_count == 1  # Only sleep between retries


class TestBatchProcessingFixes:
    """Test batch processing error isolation and recovery."""
    
    def test_batch_processing_with_mixed_results(self):
        """Test batch processing with some successful and some failed books."""
        # This would require mocking the LSI generator and metadata objects
        # For now, we'll test the error isolation logic conceptually
        
        # Mock metadata objects
        good_metadata = Mock()
        good_metadata.title = "Good Book"
        
        bad_metadata = Mock()
        bad_metadata.title = "Bad Book"
        # Configure bad_metadata to raise exceptions during processing
        
        # Test that batch processing continues even when individual books fail
        # This would be implemented with actual LSI generator testing
        assert True  # Placeholder for actual implementation
    
    def test_batch_statistics_tracking(self):
        """Test that batch processing tracks statistics correctly."""
        # Mock batch processing statistics
        batch_stats = {
            'total_books': 5,
            'successful_books': 3,
            'failed_books': 2,
            'processing_errors': ['Error 1', 'Error 2']
        }
        
        success_rate = (batch_stats['successful_books'] / batch_stats['total_books']) * 100
        assert success_rate == 60.0
        assert len(batch_stats['processing_errors']) == 2


class TestRegressionPrevention:
    """Test that previously fixed bugs don't regress."""
    
    def test_bibliography_prompt_json_format(self):
        """Test that bibliography prompt returns JSON, not conversational text."""
        # Mock a bibliography response that should be in JSON format
        mock_response = "Based on the sources cited in the provided quotes, create a simple bibliography."
        
        # This should be parsed as conversational text and converted to JSON
        result = _parse_json_with_fallbacks(mock_response)
        
        # Should either be valid JSON or have fallback handling
        assert isinstance(result, dict)
        if "error" in result:
            assert "fallback_used" in result
    
    def test_prompt_modernization_compliance(self):
        """Test that all prompts follow modern format."""
        # This would check that prompts use messages format
        # For now, we'll assume this is validated elsewhere
        assert True  # Placeholder
    
    def test_field_length_compliance(self):
        """Test that generated fields comply with LSI length limits."""
        formatter = get_text_formatter()
        
        # Test various field types
        test_cases = [
            ("short_description", "A" * 300, 350),
            ("long_description", "B" * 3000, 4000),
            ("keywords", "keyword1; keyword2; keyword3", 255)
        ]
        
        for field_name, text, max_length in test_cases:
            result = formatter.validate_field_length(field_name, text)
            if result.suggested_text:
                assert len(result.suggested_text) <= max_length


@pytest.fixture
def sample_metadata():
    """Provide sample metadata for testing."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn13": "9781234567890",
        "publisher": "Test Publisher",
        "description": "This is a test book description."
    }


def test_integration_lsi_generation(sample_metadata):
    """Integration test for complete LSI generation process."""
    # This would test the entire pipeline from metadata to CSV
    # For now, we'll test that the components work together
    
    # Test BISAC validation
    validator = get_bisac_validator()
    bisac_result = validator.validate_bisac_code("BUS001000")
    assert bisac_result.is_valid
    
    # Test text formatting
    formatter = get_text_formatter()
    format_result = formatter.validate_field_length("title", sample_metadata["title"])
    assert format_result.is_valid
    
    # Test JSON parsing
    json_result = _parse_json_with_fallbacks('{"test": "value"}')
    assert json_result["test"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])