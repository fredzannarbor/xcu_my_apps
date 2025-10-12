"""
Tests for updated TrancheConfigLoader methods
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from codexes.modules.distribution.tranche_config_loader import TrancheConfigLoader


class TestTrancheConfigLoaderUpdates:
    """Test cases for updated TrancheConfigLoader methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.tranches_dir = self.config_dir / "tranches"
        self.tranches_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test tranche config
        self.test_config = {
            "tranche_info": {"tranche_id": "test-tranche"},
            "publisher": "Test Publisher",
            "imprint": "Test Imprint",
            "field_overrides": {
                "Series Name": "Test Series",
                "annotation_boilerplate": " Additional text."
            },
            "append_fields": ["annotation_boilerplate"],
            "file_path_templates": {
                "interior": "interior/{title_slug}_interior.pdf",
                "cover": "covers/{title_slug}_cover.pdf"
            },
            "blank_fields": [
                "US-Ingram-Only* Suggested List Price (mode 2)",
                "US-Ingram-Only* Wholesale Discount % (Mode 2)"
            ]
        }
        
        # Write test config file
        config_file = self.tranches_dir / "test_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(self.test_config, f)
            
        self.loader = TrancheConfigLoader(str(self.config_dir))
        
    def test_get_field_overrides(self):
        """Test getting field overrides."""
        result = self.loader.get_field_overrides("test_tranche")
        
        expected = {
            "Series Name": "Test Series",
            "annotation_boilerplate": " Additional text."
        }
        assert result == expected
        
    def test_get_field_overrides_missing_tranche(self):
        """Test getting field overrides for missing tranche."""
        result = self.loader.get_field_overrides("missing_tranche")
        assert result == {}
        
    def test_get_append_fields(self):
        """Test getting append fields."""
        result = self.loader.get_append_fields("test_tranche")
        assert result == ["annotation_boilerplate"]
        
    def test_get_append_fields_empty(self):
        """Test getting append fields when none configured."""
        # Create config without append_fields
        config = {"tranche_info": {"tranche_id": "empty-tranche"}}
        config_file = self.tranches_dir / "empty_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
            
        result = self.loader.get_append_fields("empty_tranche")
        assert result == []
        
    def test_get_file_path_templates(self):
        """Test getting file path templates."""
        result = self.loader.get_file_path_templates("test_tranche")
        
        expected = {
            "interior": "interior/{title_slug}_interior.pdf",
            "cover": "covers/{title_slug}_cover.pdf"
        }
        assert result == expected
        
    def test_get_blank_fields(self):
        """Test getting blank fields."""
        result = self.loader.get_blank_fields("test_tranche")
        
        expected = [
            "US-Ingram-Only* Suggested List Price (mode 2)",
            "US-Ingram-Only* Wholesale Discount % (Mode 2)"
        ]
        assert result == expected
        
    def test_get_tranche_override_config(self):
        """Test getting complete override configuration."""
        result = self.loader.get_tranche_override_config("test_tranche")
        
        expected = {
            "field_overrides": {
                "Series Name": "Test Series",
                "annotation_boilerplate": " Additional text."
            },
            "append_fields": ["annotation_boilerplate"],
            "file_path_templates": {
                "interior": "interior/{title_slug}_interior.pdf",
                "cover": "covers/{title_slug}_cover.pdf"
            },
            "blank_fields": [
                "US-Ingram-Only* Suggested List Price (mode 2)",
                "US-Ingram-Only* Wholesale Discount % (Mode 2)"
            ]
        }
        assert result == expected
        
    def test_validate_tranche_config_valid(self):
        """Test validating valid tranche configuration."""
        result = self.loader.validate_tranche_config("test_tranche")
        
        assert result["errors"] == []
        assert len(result["warnings"]) == 0  # No warnings for properly structured config
        
    def test_validate_tranche_config_missing_required(self):
        """Test validating config with missing required fields."""
        # Create invalid config
        invalid_config = {"field_overrides": {"test": "value"}}
        config_file = self.tranches_dir / "invalid_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
            
        result = self.loader.validate_tranche_config("invalid_tranche")
        
        assert len(result["errors"]) > 0
        assert any("Missing required field" in error for error in result["errors"])
        
    def test_validate_tranche_config_invalid_types(self):
        """Test validating config with invalid field types."""
        # Create config with invalid types
        invalid_config = {
            "tranche_info": {"tranche_id": "invalid"},
            "publisher": "Test Publisher",
            "imprint": "Test Imprint",
            "field_overrides": "not_a_dict",  # Should be dict
            "append_fields": "not_a_list",    # Should be list
            "file_path_templates": ["not_a_dict"],  # Should be dict
            "blank_fields": {"not": "a_list"}  # Should be list
        }
        config_file = self.tranches_dir / "invalid_types_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
            
        result = self.loader.validate_tranche_config("invalid_types_tranche")
        
        assert len(result["errors"]) >= 4  # At least 4 type errors
        assert any("must be a dictionary" in error for error in result["errors"])
        assert any("must be a list" in error for error in result["errors"])
        
    def test_validate_tranche_config_invalid_templates(self):
        """Test validating config with invalid template types."""
        # Create config with invalid template types
        invalid_config = {
            "tranche_info": {"tranche_id": "invalid"},
            "publisher": "Test Publisher", 
            "imprint": "Test Imprint",
            "file_path_templates": {
                "interior": 123,  # Should be string
                "cover": ["not", "string"]  # Should be string
            }
        }
        config_file = self.tranches_dir / "invalid_templates_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
            
        result = self.loader.validate_tranche_config("invalid_templates_tranche")
        
        assert len(result["errors"]) >= 2  # At least 2 template errors
        assert any("must be a string" in error for error in result["errors"])
        
    def test_get_methods_with_missing_tranche(self):
        """Test all get methods with missing tranche."""
        missing_tranche = "nonexistent_tranche"
        
        assert self.loader.get_field_overrides(missing_tranche) == {}
        assert self.loader.get_append_fields(missing_tranche) == []
        assert self.loader.get_file_path_templates(missing_tranche) == {}
        assert self.loader.get_blank_fields(missing_tranche) == []
        
        override_config = self.loader.get_tranche_override_config(missing_tranche)
        expected_empty = {
            "field_overrides": {},
            "append_fields": [],
            "file_path_templates": {},
            "blank_fields": []
        }
        assert override_config == expected_empty