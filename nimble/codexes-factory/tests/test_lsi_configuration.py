"""
Unit tests for LSI Configuration System
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from codexes.modules.distribution.lsi_configuration import (
    LSIConfiguration, 
    ImprintConfig, 
    TerritorialConfig
)


class TestTerritorialConfig:
    """Test TerritorialConfig dataclass."""
    
    def test_territorial_config_creation(self):
        """Test creating a territorial configuration."""
        config = TerritorialConfig(
            territory_code="US",
            wholesale_discount_percent="40",
            returnability="Yes-Destroy",
            currency="USD",
            pricing_multiplier=1.0
        )
        
        assert config.territory_code == "US"
        assert config.wholesale_discount_percent == "40"
        assert config.returnability == "Yes-Destroy"
        assert config.currency == "USD"
        assert config.pricing_multiplier == 1.0
        assert config.additional_fields == {}
    
    def test_territorial_config_with_additional_fields(self):
        """Test territorial config with additional fields."""
        additional = {"custom_field": "custom_value"}
        config = TerritorialConfig(
            territory_code="UK",
            additional_fields=additional
        )
        
        assert config.territory_code == "UK"
        assert config.additional_fields == additional


class TestImprintConfig:
    """Test ImprintConfig dataclass."""
    
    def test_imprint_config_creation(self):
        """Test creating an imprint configuration."""
        config = ImprintConfig(
            imprint_name="Test Imprint",
            publisher="Test Publisher"
        )
        
        assert config.imprint_name == "Test Imprint"
        assert config.publisher == "Test Publisher"
        assert config.default_values == {}
        assert config.territorial_configs == {}
        assert config.field_overrides == {}
    
    def test_imprint_config_with_territorial_configs(self):
        """Test imprint config with territorial configurations."""
        territorial_config = TerritorialConfig(territory_code="US")
        config = ImprintConfig(
            imprint_name="Test Imprint",
            territorial_configs={"US": territorial_config}
        )
        
        assert "US" in config.territorial_configs
        assert config.territorial_configs["US"] == territorial_config


class TestLSIConfiguration:
    """Test LSIConfiguration class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_config = {
            "defaults": {
                "publisher": "Test Publisher",
                "imprint": "Test Imprint",
                "lightning_source_account": "123456"
            },
            "field_overrides": {
                "cover_submission_method": "FTP"
            },
            "imprint_configs": {
                "Test Imprint": {
                    "publisher": "Test Publisher",
                    "defaults": {
                        "lsi_special_category": "Fiction"
                    },
                    "field_overrides": {
                        "lsi_flexfield1": "Custom Value"
                    },
                    "territorial_configs": {
                        "US": {
                            "wholesale_discount_percent": "40",
                            "returnability": "Yes-Destroy",
                            "currency": "USD",
                            "pricing_multiplier": 1.0
                        }
                    }
                }
            },
            "territorial_configs": {
                "UK": {
                    "wholesale_discount_percent": "35",
                    "returnability": "Yes-Return",
                    "currency": "GBP",
                    "pricing_multiplier": 0.79
                }
            }
        }
    
    def test_init_without_config(self):
        """Test initialization without configuration file."""
        with patch('pathlib.Path.exists', return_value=False):
            config = LSIConfiguration()
            assert config.config_dir == Path("configs")
            assert config._defaults == {}
    
    def test_init_with_config_path(self):
        """Test initialization with specific config path."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            assert config.get_default_value("publisher") == "Test Publisher"
            assert config.get_field_override("cover_submission_method") == "FTP"
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            LSIConfiguration(config_path="nonexistent.json")
    
    def test_load_config_invalid_json(self):
        """Test loading invalid JSON config."""
        invalid_json = "{ invalid json }"
        
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with pytest.raises(ValueError, match="Invalid JSON"):
                LSIConfiguration(config_path="invalid.json")
    
    def test_get_default_value(self):
        """Test getting default values."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            assert config.get_default_value("publisher") == "Test Publisher"
            assert config.get_default_value("nonexistent") == ""
    
    def test_get_field_override(self):
        """Test getting field overrides."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            assert config.get_field_override("cover_submission_method") == "FTP"
            assert config.get_field_override("nonexistent") is None
    
    def test_get_imprint_config(self):
        """Test getting imprint configuration."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            imprint_config = config.get_imprint_config("Test Imprint")
            assert imprint_config is not None
            assert imprint_config.imprint_name == "Test Imprint"
            assert imprint_config.publisher == "Test Publisher"
            
            assert config.get_imprint_config("Nonexistent") is None
    
    def test_get_territorial_config(self):
        """Test getting territorial configuration."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            territorial_config = config.get_territorial_config("UK")
            assert territorial_config is not None
            assert territorial_config.territory_code == "UK"
            assert territorial_config.wholesale_discount_percent == "35"
            
            assert config.get_territorial_config("Nonexistent") is None
    
    def test_get_field_value_precedence(self):
        """Test field value precedence hierarchy."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            # Test global override (highest precedence)
            assert config.get_field_value("cover_submission_method") == "FTP"
            
            # Test imprint override
            assert config.get_field_value("lsi_flexfield1", imprint="Test Imprint") == "Custom Value"
            
            # Test territorial value
            assert config.get_field_value("wholesale_discount_percent", territory="UK") == "35"
            
            # Test imprint default
            assert config.get_field_value("lsi_special_category", imprint="Test Imprint") == "Fiction"
            
            # Test global default
            assert config.get_field_value("publisher") == "Test Publisher"
            
            # Test nonexistent field
            assert config.get_field_value("nonexistent") == ""
    
    def test_get_field_value_with_imprint_territorial(self):
        """Test field value with both imprint and territorial context."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            # Should get value from imprint's territorial config
            value = config.get_field_value(
                "wholesale_discount_percent", 
                imprint="Test Imprint", 
                territory="US"
            )
            assert value == "40"
            
            # Should fall back to global territorial config
            value = config.get_field_value(
                "wholesale_discount_percent", 
                imprint="Test Imprint", 
                territory="UK"
            )
            assert value == "35"
    
    def test_get_available_imprints(self):
        """Test getting available imprints."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            imprints = config.get_available_imprints()
            assert "Test Imprint" in imprints
    
    def test_get_available_territories(self):
        """Test getting available territories."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            territories = config.get_available_territories()
            assert "UK" in territories
            assert "US" in territories
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        # Test with missing required fields
        incomplete_config = {
            "defaults": {
                "publisher": "Test Publisher"
                # Missing lightning_source_account
            }
        }
        
        config_json = json.dumps(incomplete_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)):
            config = LSIConfiguration(config_path="test_config.json")
            
            warnings = config.validate_configuration()
            assert len(warnings) > 0
            assert any("lightning_source_account" in warning for warning in warnings)
    
    def test_save_configuration(self):
        """Test saving configuration to file."""
        config_json = json.dumps(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=config_json)) as mock_file:
            config = LSIConfiguration(config_path="test_config.json")
            
            # Reset mock for save operation
            mock_file.reset_mock()
            
            with patch("os.makedirs"):
                config.save_configuration("output_config.json")
            
            # Verify file was opened for writing
            mock_file.assert_called_with("output_config.json", 'w', encoding='utf-8')
    
    def test_territorial_field_value_mapping(self):
        """Test territorial field value mapping."""
        config = LSIConfiguration()
        territorial_config = TerritorialConfig(
            territory_code="US",
            wholesale_discount_percent="40",
            returnability="Yes-Destroy",
            currency="USD"
        )
        
        # Test standard territorial fields
        assert config._get_territorial_field_value(territorial_config, "wholesale_discount_percent") == "40"
        assert config._get_territorial_field_value(territorial_config, "returnability") == "Yes-Destroy"
        assert config._get_territorial_field_value(territorial_config, "currency") == "USD"
        assert config._get_territorial_field_value(territorial_config, "nonexistent") is None


class TestLSIConfigurationIntegration:
    """Integration tests for LSI Configuration with file system."""
    
    def test_load_from_directory_structure(self):
        """Test loading configuration from directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create directory structure
            (config_dir / "publishers").mkdir()
            (config_dir / "imprints").mkdir()
            
            # Create default config
            default_config = {
                "defaults": {
                    "publisher": "Default Publisher"
                }
            }
            with open(config_dir / "default_lsi_config.json", 'w') as f:
                json.dump(default_config, f)
            
            # Create publisher config
            publisher_config = {
                "defaults": {
                    "lightning_source_account": "123456"
                }
            }
            with open(config_dir / "publishers" / "test_publisher.json", 'w') as f:
                json.dump(publisher_config, f)
            
            # Create imprint config
            imprint_config = {
                "publisher": "Test Publisher",
                "defaults": {
                    "imprint": "Test Imprint"
                }
            }
            with open(config_dir / "imprints" / "test_imprint.json", 'w') as f:
                json.dump(imprint_config, f)
            
            # Load configuration
            config = LSIConfiguration(config_dir=str(config_dir))
            
            # Verify loaded values
            assert config.get_default_value("publisher") == "Default Publisher"
            assert config.get_default_value("lightning_source_account") == "123456"
            
            imprint_config_obj = config.get_imprint_config("test_imprint")
            assert imprint_config_obj is not None
            assert imprint_config_obj.publisher == "Test Publisher"
    
    def test_load_with_missing_directories(self):
        """Test loading configuration with missing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Don't create subdirectories - should not raise errors
            config = LSIConfiguration(config_dir=str(config_dir))
            
            # Should have empty configuration
            assert config.get_default_value("publisher") == ""
            assert config.get_available_imprints() == []