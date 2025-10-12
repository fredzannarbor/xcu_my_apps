"""
Tests for the JSON parser utility.
"""

import pytest
import json

from nimble_llm_caller.utils.json_parser import JSONParser


class TestJSONParser:
    """Test cases for JSONParser class."""
    
    def test_initialization(self):
        """Test JSONParser initialization."""
        parser = JSONParser()
        assert parser is not None
    
    def test_parse_valid_json(self, sample_json_responses):
        """Test parsing valid JSON."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["valid_json"])
        
        assert isinstance(result, dict)
        assert result["title"] == "Test Title"
        assert result["summary"] == "Test summary"
    
    def test_parse_json_with_markdown(self, sample_json_responses):
        """Test parsing JSON wrapped in markdown code blocks."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["json_with_markdown"])
        
        assert isinstance(result, dict)
        assert result["title"] == "Test Title"
        assert result["summary"] == "Test summary"
    
    def test_parse_malformed_json(self, sample_json_responses):
        """Test parsing malformed JSON with repair."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["malformed_json"])
        
        # Should attempt repair and return something useful
        assert result is not None
        # The exact result depends on json_repair implementation
    
    def test_parse_conversational_response(self, sample_json_responses):
        """Test parsing conversational response."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["conversational_response"])
        
        # Should extract some structured information
        assert result is not None
        if isinstance(result, dict):
            assert "fallback_used" in result
    
    def test_parse_empty_response(self, sample_json_responses):
        """Test parsing empty response."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["empty_response"])
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["fallback_used"] == "empty_response"
    
    def test_parse_none_response(self, sample_json_responses):
        """Test parsing None response."""
        parser = JSONParser()
        
        result = parser.parse(sample_json_responses["none_response"])
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["fallback_used"] == "empty_response"
    
    def test_clean_parsed_data(self):
        """Test cleaning parsed data."""
        parser = JSONParser()
        
        dirty_data = {
            "title": "  Test Title  ",
            "summary": "Test summary\n\n",
            "empty_field": "",
            "none_field": None,
            "nested": {
                "field": "  value  "
            }
        }
        
        cleaned = parser.clean_parsed_data(dirty_data)
        
        assert cleaned["title"] == "Test Title"
        assert cleaned["summary"] == "Test summary"
        assert "empty_field" not in cleaned or cleaned["empty_field"] == ""
        assert cleaned["nested"]["field"] == "value"
    
    def test_validate_required_keys_success(self):
        """Test successful validation of required keys."""
        parser = JSONParser()
        
        data = {"title": "Test", "author": "Author", "summary": "Summary"}
        required_keys = ["title", "author"]
        
        result = parser.validate_required_keys(data, required_keys)
        
        assert result["valid"] is True
        assert len(result["missing_keys"]) == 0
    
    def test_validate_required_keys_missing(self):
        """Test validation with missing required keys."""
        parser = JSONParser()
        
        data = {"title": "Test"}
        required_keys = ["title", "author", "summary"]
        
        result = parser.validate_required_keys(data, required_keys)
        
        assert result["valid"] is False
        assert "author" in result["missing_keys"]
        assert "summary" in result["missing_keys"]
    
    def test_validate_required_keys_non_dict(self):
        """Test validation with non-dictionary data."""
        parser = JSONParser()
        
        result = parser.validate_required_keys("not a dict", ["key"])
        
        assert result["valid"] is False
        assert len(result["missing_keys"]) == 1