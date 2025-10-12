"""
Tests for the Imprint-Ideation Bridge component.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from codexes.ui.components.imprint_ideation_bridge import (
    ImprintIdeationBridge, 
    IntegrationMode, 
    ImprintContext
)
from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestImprintIdeationBridge:
    """Test cases for the ImprintIdeationBridge component."""
    
    @pytest.fixture
    def sample_imprint_config(self):
        """Sample imprint configuration for testing."""
        return {
            "imprint": "Test Imprint",
            "publisher": "Test Publisher",
            "contact_email": "test@example.com",
            "branding": {
                "tagline": "Testing the Future",
                "brand_colors": {
                    "primary": "#000000",
                    "secondary": "#FFFFFF"
                }
            },
            "publishing_focus": {
                "primary_genres": ["Science Fiction", "Fantasy"],
                "target_audience": "Young Adult",
                "specialization": "Speculative Fiction"
            },
            "metadata_defaults": {
                "bisac_category_preferences": ["YAF000000", "YAF019000"],
                "default_age_range": {
                    "min_age": "13",
                    "max_age": "18"
                }
            },
            "workflow_settings": {
                "require_manual_review": True
            }
        }
    
    @pytest.fixture
    def sample_codex_object(self):
        """Sample CodexObject for testing."""
        return CodexObject(
            title="Test Story",
            content="A young wizard discovers a magical portal to another world.",
            object_type=CodexObjectType.IDEA,
            genre="Fantasy",
            target_audience="Young Adult",
            word_count=12
        )
    
    @pytest.fixture
    def bridge_with_mock_config(self, sample_imprint_config):
        """ImprintIdeationBridge with mocked configuration loading."""
        with patch.object(ImprintIdeationBridge, '_load_available_imprints') as mock_load:
            # Create a temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(sample_imprint_config, f)
                config_path = f.name
            
            # Create mock imprint context
            imprint_context = ImprintContext(
                name="Test Imprint",
                publisher="Test Publisher",
                config_path=config_path,
                branding=sample_imprint_config["branding"],
                publishing_focus=sample_imprint_config["publishing_focus"],
                constraints={
                    "preferred_genres": ["Science Fiction", "Fantasy"],
                    "target_audience": "Young Adult",
                    "age_range": {"min_age": "13", "max_age": "18"}
                },
                guidance={
                    "brand_tagline": "Testing the Future",
                    "specialization": "Speculative Fiction",
                    "requires_review": True
                }
            )
            
            mock_load.return_value = {"Test Imprint": imprint_context}
            
            bridge = ImprintIdeationBridge()
            
            # Clean up temp file
            Path(config_path).unlink()
            
            return bridge
    
    def test_initialization(self, bridge_with_mock_config):
        """Test bridge initialization."""
        bridge = bridge_with_mock_config
        
        assert len(bridge.available_imprints) == 1
        assert "Test Imprint" in bridge.available_imprints
        assert len(bridge.integration_modes) == 3
        assert IntegrationMode.IMPRINT_DRIVEN in bridge.integration_modes
    
    def test_extract_imprint_constraints(self, sample_imprint_config):
        """Test constraint extraction from imprint configuration."""
        bridge = ImprintIdeationBridge()
        constraints = bridge._extract_imprint_constraints(sample_imprint_config)
        
        assert "preferred_genres" in constraints
        assert constraints["preferred_genres"] == ["Science Fiction", "Fantasy"]
        assert constraints["target_audience"] == "Young Adult"
        assert "age_range" in constraints
        assert constraints["age_range"]["min_age"] == "13"
    
    def test_extract_imprint_guidance(self, sample_imprint_config):
        """Test guidance extraction from imprint configuration."""
        bridge = ImprintIdeationBridge()
        guidance = bridge._extract_imprint_guidance(sample_imprint_config)
        
        assert guidance["brand_tagline"] == "Testing the Future"
        assert guidance["specialization"] == "Speculative Fiction"
        assert guidance["requires_review"] is True
    
    def test_apply_imprint_constraints(self, bridge_with_mock_config, sample_codex_object):
        """Test applying imprint constraints to a CodexObject."""
        bridge = bridge_with_mock_config
        
        # Remove genre to test constraint application
        sample_codex_object.genre = ""
        
        result = bridge.apply_imprint_constraints(sample_codex_object, "Test Imprint")
        
        assert result.genre == "Science Fiction"  # First preferred genre
        assert "imprint:test_imprint" in result.tags
        assert len(result.processing_history) > 1  # Should have constraint application entry
    
    def test_validate_content_for_imprint(self, bridge_with_mock_config, sample_codex_object):
        """Test content validation against imprint constraints."""
        bridge = bridge_with_mock_config
        
        validation = bridge.validate_content_for_imprint(sample_codex_object, "Test Imprint")
        
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        # Should have suggestions about manual review
        assert any("manual review" in suggestion.lower() for suggestion in validation["suggestions"])
    
    def test_validate_content_with_warnings(self, bridge_with_mock_config, sample_codex_object):
        """Test content validation that produces warnings."""
        bridge = bridge_with_mock_config
        
        # Set a genre that's not in preferred list
        sample_codex_object.genre = "Horror"
        
        validation = bridge.validate_content_for_imprint(sample_codex_object, "Test Imprint")
        
        assert validation["valid"] is True  # Still valid, just warnings
        assert len(validation["warnings"]) > 0
        assert any("Horror" in warning for warning in validation["warnings"])
    
    def test_export_to_pipeline(self, bridge_with_mock_config, sample_codex_object):
        """Test exporting CodexObjects to pipeline format."""
        bridge = bridge_with_mock_config
        
        # Mock the config file reading for export
        with patch('builtins.open') as mock_open:
            mock_config = {
                "imprint": "Test Imprint",
                "publisher": "Test Publisher",
                "default_book_settings": {
                    "language_code": "eng",
                    "binding_type": "paperback"
                },
                "metadata_defaults": {
                    "edition_number": "1",
                    "bisac_category_preferences": ["YAF000000"]
                },
                "lsi_specific_settings": {
                    "publisher_reference_id": "TEST"
                }
            }
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
            
            result = bridge.export_to_pipeline([sample_codex_object], "Test Imprint")
        
        assert result["success"] is True
        assert len(result["exported_objects"]) == 1
        
        exported_obj = result["exported_objects"][0]
        assert exported_obj["codex_object_uuid"] == sample_codex_object.uuid
        assert exported_obj["title"] == sample_codex_object.title
        assert "metadata" in exported_obj
        assert "validation" in exported_obj
    
    def test_export_unknown_imprint(self, bridge_with_mock_config, sample_codex_object):
        """Test exporting with unknown imprint."""
        bridge = bridge_with_mock_config
        
        result = bridge.export_to_pipeline([sample_codex_object], "Unknown Imprint")
        
        assert result["success"] is False
        assert "Unknown imprint" in result["error"]
    
    def test_integration_modes(self, bridge_with_mock_config):
        """Test integration mode definitions."""
        bridge = bridge_with_mock_config
        
        assert IntegrationMode.IMPRINT_DRIVEN in bridge.integration_modes
        assert IntegrationMode.EXPORT_TO_PIPELINE in bridge.integration_modes
        assert IntegrationMode.BIDIRECTIONAL_SYNC in bridge.integration_modes
        
        # Check mode details
        imprint_driven = bridge.integration_modes[IntegrationMode.IMPRINT_DRIVEN]
        assert "Brand-consistent content generation" in imprint_driven["features"]
        
        export_mode = bridge.integration_modes[IntegrationMode.EXPORT_TO_PIPELINE]
        assert "CodexObject to CodexMetadata conversion" in export_mode["features"]
    
    def test_apply_imprint_metadata(self, bridge_with_mock_config, sample_codex_object):
        """Test applying imprint metadata to CodexMetadata."""
        bridge = bridge_with_mock_config
        
        # Create CodexMetadata from CodexObject
        metadata = sample_codex_object.to_codex_metadata()
        
        # Get imprint context
        imprint_context = bridge.available_imprints["Test Imprint"]
        
        # Mock config file reading
        with patch('builtins.open') as mock_open:
            mock_config = {
                "imprint": "Test Imprint",
                "publisher": "Test Publisher",
                "default_book_settings": {
                    "language_code": "eng",
                    "territorial_rights": "World"
                },
                "metadata_defaults": {
                    "edition_number": "1",
                    "bisac_category_preferences": ["YAF000000"]
                },
                "lsi_specific_settings": {
                    "publisher_reference_id": "TEST"
                }
            }
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
            
            result_metadata = bridge._apply_imprint_metadata(metadata, imprint_context)
        
        assert result_metadata.imprint == "Test Imprint"
        assert result_metadata.publisher == "Test Publisher"
        assert result_metadata.language == "eng"
        assert result_metadata.territorial_rights == "World"
        assert result_metadata.edition_number == "1"
        assert result_metadata.publisher_reference_id == "TEST"
    
    def test_validate_pipeline_compatibility(self, bridge_with_mock_config):
        """Test pipeline compatibility validation."""
        bridge = bridge_with_mock_config
        imprint_context = bridge.available_imprints["Test Imprint"]
        
        # Test valid metadata
        valid_metadata = CodexMetadata()
        valid_metadata.title = "Test Book"
        valid_metadata.imprint = "Test Imprint"
        valid_metadata.publisher = "Test Publisher"
        valid_metadata.summary_long = "A test book summary"
        valid_metadata.word_count = 1000
        
        validation = bridge._validate_pipeline_compatibility(valid_metadata, imprint_context)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        
        # Test invalid metadata (missing required fields)
        invalid_metadata = CodexMetadata()
        validation = bridge._validate_pipeline_compatibility(invalid_metadata, imprint_context)
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert any("title" in error.lower() for error in validation["errors"])


if __name__ == "__main__":
    pytest.main([__file__])