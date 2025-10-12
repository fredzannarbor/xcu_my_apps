"""
Tests for TrancheOverrideManager
"""

import pytest
from codexes.modules.distribution.tranche_override_manager import TrancheOverrideManager


class TestTrancheOverrideManager:
    """Test cases for TrancheOverrideManager."""
    
    def test_init_empty_config(self):
        """Test initialization with empty config."""
        manager = TrancheOverrideManager()
        assert manager.field_overrides == {}
        assert manager.append_fields == set()
        assert manager.blank_fields == set()
        
    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {
            'field_overrides': {'Series Name': 'Test Series'},
            'append_fields': ['annotation_boilerplate'],
            'blank_fields': ['US-Ingram-Only* Suggested List Price (mode 2)']
        }
        manager = TrancheOverrideManager(config)
        assert manager.field_overrides == {'Series Name': 'Test Series'}
        assert manager.append_fields == {'annotation_boilerplate'}
        assert manager.blank_fields == {'US-Ingram-Only* Suggested List Price (mode 2)'}
        
    def test_should_override_none(self):
        """Test should_override with None value."""
        manager = TrancheOverrideManager()
        assert not manager.should_override(None)
        
    def test_should_override_empty_string(self):
        """Test should_override with empty string."""
        manager = TrancheOverrideManager()
        assert manager.should_override("")
        
    def test_should_override_valid_value(self):
        """Test should_override with valid value."""
        manager = TrancheOverrideManager()
        assert manager.should_override("Test Value")
        assert manager.should_override(123)
        assert manager.should_override(True)
        
    def test_is_append_field(self):
        """Test is_append_field method."""
        config = {'append_fields': ['annotation_boilerplate', 'description']}
        manager = TrancheOverrideManager(config)
        assert manager.is_append_field('annotation_boilerplate')
        assert manager.is_append_field('description')
        assert not manager.is_append_field('Series Name')
        
    def test_is_blank_field(self):
        """Test is_blank_field method."""
        config = {'blank_fields': ['US-Ingram-Only* Suggested List Price (mode 2)']}
        manager = TrancheOverrideManager(config)
        assert manager.is_blank_field('US-Ingram-Only* Suggested List Price (mode 2)')
        assert not manager.is_blank_field('Series Name')
        
    def test_apply_overrides_no_tranche_value(self):
        """Test apply_overrides with no tranche value."""
        manager = TrancheOverrideManager()
        result = manager.apply_overrides('Series Name', 'LLM Value')
        assert result == 'LLM Value'
        
    def test_apply_overrides_replace(self):
        """Test apply_overrides with replace behavior."""
        config = {'field_overrides': {'Series Name': 'Tranche Series'}}
        manager = TrancheOverrideManager(config)
        result = manager.apply_overrides('Series Name', 'LLM Value')
        assert result == 'Tranche Series'
        
    def test_apply_overrides_append(self):
        """Test apply_overrides with append behavior."""
        config = {
            'field_overrides': {'annotation_boilerplate': ' Additional text.'},
            'append_fields': ['annotation_boilerplate']
        }
        manager = TrancheOverrideManager(config)
        result = manager.apply_overrides('annotation_boilerplate', 'Base text.')
        assert result == 'Base text. Additional text.'
        
    def test_apply_overrides_append_empty_base(self):
        """Test apply_overrides with append behavior and empty base."""
        config = {
            'field_overrides': {'annotation_boilerplate': 'Additional text.'},
            'append_fields': ['annotation_boilerplate']
        }
        manager = TrancheOverrideManager(config)
        result = manager.apply_overrides('annotation_boilerplate', '')
        assert result == 'Additional text.'
        
    def test_apply_overrides_blank_field(self):
        """Test apply_overrides with blank field."""
        config = {'blank_fields': ['US-Ingram-Only* Suggested List Price (mode 2)']}
        manager = TrancheOverrideManager(config)
        result = manager.apply_overrides('US-Ingram-Only* Suggested List Price (mode 2)', 'Some Value')
        assert result == ""
        
    def test_apply_overrides_explicit_tranche_value(self):
        """Test apply_overrides with explicitly provided tranche value."""
        manager = TrancheOverrideManager()
        result = manager.apply_overrides('Series Name', 'LLM Value', 'Explicit Value')
        assert result == 'Explicit Value'
        
    def test_get_field_override(self):
        """Test get_field_override method."""
        config = {'field_overrides': {'Series Name': 'Test Series'}}
        manager = TrancheOverrideManager(config)
        assert manager.get_field_override('Series Name') == 'Test Series'
        assert manager.get_field_override('Other Field') is None
        
    def test_has_override(self):
        """Test has_override method."""
        config = {'field_overrides': {'Series Name': 'Test Series'}}
        manager = TrancheOverrideManager(config)
        assert manager.has_override('Series Name')
        assert not manager.has_override('Other Field')
        
    def test_get_override_type(self):
        """Test get_override_type method."""
        config = {
            'field_overrides': {'Series Name': 'Test Series'},
            'append_fields': ['annotation_boilerplate'],
            'blank_fields': ['US-Ingram-Only* Suggested List Price (mode 2)']
        }
        manager = TrancheOverrideManager(config)
        assert manager.get_override_type('Series Name') == 'replace'
        assert manager.get_override_type('annotation_boilerplate') == 'append'
        assert manager.get_override_type('US-Ingram-Only* Suggested List Price (mode 2)') == 'blank'
        assert manager.get_override_type('Other Field') == 'none'