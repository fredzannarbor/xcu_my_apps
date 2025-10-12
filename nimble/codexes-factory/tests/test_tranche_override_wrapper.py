"""
Tests for TrancheOverrideWrapper
"""

import pytest
from unittest.mock import Mock, MagicMock
from codexes.modules.distribution.tranche_override_wrapper import (
    TrancheOverrideWrapper, wrap_registry_with_tranche_overrides, TrancheAwareStrategy
)
from codexes.modules.distribution.field_mapping import MappingStrategy, MappingContext
from codexes.modules.distribution.tranche_override_manager import TrancheOverrideManager
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestTrancheOverrideWrapper:
    """Test cases for TrancheOverrideWrapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_strategy = Mock(spec=MappingStrategy)
        self.override_manager = Mock(spec=TrancheOverrideManager)
        self.wrapper = TrancheOverrideWrapper(self.base_strategy, self.override_manager)
        
    def test_map_field_no_override(self):
        """Test mapping field with no override."""
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.field_name = "Test Field"
        
        # Configure mocks
        self.base_strategy.map_field.return_value = "base_value"
        self.override_manager.apply_overrides.return_value = "base_value"
        self.override_manager.get_override_type.return_value = "none"
        
        result = self.wrapper.map_field(metadata, context)
        
        assert result == "base_value"
        self.base_strategy.map_field.assert_called_once_with(metadata, context)
        self.override_manager.apply_overrides.assert_called_once_with(
            field_name="Test Field",
            llm_value="base_value",
            tranche_value=None,
            field_type="replace"
        )
        
    def test_map_field_with_override(self):
        """Test mapping field with override applied."""
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.field_name = "Test Field"
        
        # Configure mocks
        self.base_strategy.map_field.return_value = "base_value"
        self.override_manager.apply_overrides.return_value = "override_value"
        self.override_manager.get_override_type.return_value = "replace"
        
        result = self.wrapper.map_field(metadata, context)
        
        assert result == "override_value"
        self.base_strategy.map_field.assert_called_once_with(metadata, context)
        self.override_manager.apply_overrides.assert_called_once()
        
    def test_map_field_error_handling(self):
        """Test error handling in map_field."""
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.field_name = "Test Field"
        
        # Configure mocks to raise exception
        self.override_manager.apply_overrides.side_effect = Exception("Override error")
        self.base_strategy.map_field.return_value = "fallback_value"
        
        result = self.wrapper.map_field(metadata, context)
        
        assert result == "fallback_value"
        
    def test_map_field_complete_failure(self):
        """Test complete failure handling."""
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.field_name = "Test Field"
        
        # Configure both to fail
        self.override_manager.apply_overrides.side_effect = Exception("Override error")
        self.base_strategy.map_field.side_effect = Exception("Base error")
        
        result = self.wrapper.map_field(metadata, context)
        
        assert result == ""
        
    def test_validate_input(self):
        """Test input validation delegation."""
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        
        self.base_strategy.validate_input.return_value = True
        
        result = self.wrapper.validate_input(metadata, context)
        
        assert result is True
        self.base_strategy.validate_input.assert_called_once_with(metadata, context)


class TestWrapRegistryWithTrancheOverrides:
    """Test cases for wrap_registry_with_tranche_overrides function."""
    
    def test_wrap_registry_no_config(self):
        """Test wrapping registry with no tranche config."""
        registry = Mock()
        
        result = wrap_registry_with_tranche_overrides(registry, None)
        
        assert result is registry
        registry.get_registered_fields.assert_not_called()
        
    def test_wrap_registry_with_config(self):
        """Test wrapping registry with tranche config."""
        registry = Mock()
        registry.get_registered_fields.return_value = ["Field1", "Field2"]
        
        strategy1 = Mock(spec=MappingStrategy)
        strategy2 = Mock(spec=MappingStrategy)
        registry.get_strategy.side_effect = [strategy1, strategy2]
        
        tranche_config = {
            'field_overrides': {'Field1': 'override_value'},
            'append_fields': ['Field2']
        }
        
        result = wrap_registry_with_tranche_overrides(registry, tranche_config)
        
        assert result is registry
        assert registry.register_strategy.call_count == 2
        
        # Check that wrapped strategies were registered
        calls = registry.register_strategy.call_args_list
        assert calls[0][0][0] == "Field1"
        assert isinstance(calls[0][0][1], TrancheOverrideWrapper)
        assert calls[1][0][0] == "Field2"
        assert isinstance(calls[1][0][1], TrancheOverrideWrapper)
        
    def test_wrap_registry_missing_strategy(self):
        """Test wrapping registry when strategy is missing."""
        registry = Mock()
        registry.get_registered_fields.return_value = ["Field1"]
        registry.get_strategy.return_value = None
        
        tranche_config = {'field_overrides': {}}
        
        result = wrap_registry_with_tranche_overrides(registry, tranche_config)
        
        assert result is registry
        registry.register_strategy.assert_not_called()


class TestTrancheAwareStrategy:
    """Test cases for TrancheAwareStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = TrancheAwareStrategy()
        
    def test_get_tranche_config(self):
        """Test getting tranche config from context."""
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'field_overrides': {'test': 'value'}
            }
        }
        
        result = self.strategy.get_tranche_config(context)
        
        assert result == {'field_overrides': {'test': 'value'}}
        
    def test_get_tranche_config_no_config(self):
        """Test getting tranche config with no context config."""
        context = Mock(spec=MappingContext)
        context.config = None
        
        result = self.strategy.get_tranche_config(context)
        
        assert result == {}
        
    def test_get_tranche_override(self):
        """Test getting tranche override value."""
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'field_overrides': {'test_field': 'override_value'}
            }
        }
        
        result = self.strategy.get_tranche_override('test_field', context)
        
        assert result == 'override_value'
        
    def test_get_tranche_override_missing(self):
        """Test getting tranche override for missing field."""
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'field_overrides': {}
            }
        }
        
        result = self.strategy.get_tranche_override('missing_field', context)
        
        assert result is None
        
    def test_is_append_field(self):
        """Test checking if field is append type."""
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'append_fields': ['append_field']
            }
        }
        
        assert self.strategy.is_append_field('append_field', context) is True
        assert self.strategy.is_append_field('other_field', context) is False
        
    def test_is_append_field_no_config(self):
        """Test checking append field with no config."""
        context = Mock(spec=MappingContext)
        context.config = None
        
        result = self.strategy.is_append_field('any_field', context)
        
        assert result is False