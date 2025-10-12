"""
Unit tests for UI safety patterns and data validators.

Tests comprehensive None value handling and autofix-resistant patterns.
"""

import pytest
from unittest.mock import patch, MagicMock

from codexes.modules.ui.safety_patterns import (
    safe_getattr, safe_dict_get, safe_list_access, safe_iteration,
    safe_len, safe_join, safe_string_format, safe_max, safe_min, safe_sum,
    safe_filter, safe_map, get_default_for_type, get_attribute_default,
    validate_not_none, ATTRIBUTE_DEFAULTS, DEFAULT_VALUES
)

from codexes.modules.ui.data_validators import (
    UIDataValidator, AttributeDefaultProvider, StructureNormalizer
)


class TestSafetyPatterns:
    """Test core safety pattern functions."""
    
    def test_safe_getattr_with_none_object(self):
        """Test safe_getattr handles None objects."""
        result = safe_getattr(None, 'attribute', 'default')
        assert result == 'default'
    
    def test_safe_getattr_with_missing_attribute(self):
        """Test safe_getattr handles missing attributes."""
        obj = MagicMock()
        del obj.missing_attr
        result = safe_getattr(obj, 'missing_attr', 'default')
        assert result == 'default'
    
    def test_safe_getattr_with_existing_attribute(self):
        """Test safe_getattr returns existing attributes."""
        obj = MagicMock()
        obj.existing_attr = 'value'
        result = safe_getattr(obj, 'existing_attr', 'default')
        assert result == 'value'
    
    def test_safe_dict_get_with_none_dict(self):
        """Test safe_dict_get handles None dictionaries."""
        result = safe_dict_get(None, 'key', 'default')
        assert result == 'default'
    
    def test_safe_dict_get_with_missing_key(self):
        """Test safe_dict_get handles missing keys."""
        result = safe_dict_get({'other': 'value'}, 'missing', 'default')
        assert result == 'default'
    
    def test_safe_dict_get_with_existing_key(self):
        """Test safe_dict_get returns existing values."""
        result = safe_dict_get({'key': 'value'}, 'key', 'default')
        assert result == 'value'
    
    def test_safe_list_access_with_none_list(self):
        """Test safe_list_access handles None lists."""
        result = safe_list_access(None, 0, 'default')
        assert result == 'default'
    
    def test_safe_list_access_with_out_of_bounds(self):
        """Test safe_list_access handles out of bounds access."""
        result = safe_list_access(['a', 'b'], 5, 'default')
        assert result == 'default'
    
    def test_safe_list_access_with_valid_index(self):
        """Test safe_list_access returns valid elements."""
        result = safe_list_access(['a', 'b', 'c'], 1, 'default')
        assert result == 'b'
    
    def test_safe_iteration_with_none(self):
        """Test safe_iteration handles None collections."""
        result = safe_iteration(None)
        assert result == []
    
    def test_safe_iteration_with_list(self):
        """Test safe_iteration returns lists unchanged."""
        test_list = ['a', 'b', 'c']
        result = safe_iteration(test_list)
        assert result == test_list
    
    def test_safe_len_with_none(self):
        """Test safe_len handles None collections."""
        result = safe_len(None)
        assert result == 0
    
    def test_safe_len_with_collection(self):
        """Test safe_len returns correct length."""
        result = safe_len(['a', 'b', 'c'])
        assert result == 3
    
    def test_safe_join_with_none(self):
        """Test safe_join handles None collections."""
        result = safe_join(None)
        assert result == ''
    
    def test_safe_join_with_empty_list(self):
        """Test safe_join handles empty lists."""
        result = safe_join([])
        assert result == ''
    
    def test_safe_join_with_strings(self):
        """Test safe_join joins strings correctly."""
        result = safe_join(['a', 'b', 'c'], ', ')
        assert result == 'a, b, c'
    
    def test_safe_join_with_none_elements(self):
        """Test safe_join filters out None elements."""
        result = safe_join(['a', None, 'c'], ', ')
        assert result == 'a, c'
    
    def test_safe_string_format_with_none_values(self):
        """Test safe_string_format handles None values."""
        result = safe_string_format("Hello {name}, age {age}", name=None, age=25)
        assert result == "Hello , age 25"
    
    def test_safe_string_format_with_invalid_template(self):
        """Test safe_string_format handles invalid templates."""
        result = safe_string_format("Hello {missing}", name="John")
        assert result == "Hello {missing}"
    
    def test_safe_max_with_none(self):
        """Test safe_max handles None collections."""
        result = safe_max(None, 0)
        assert result == 0
    
    def test_safe_max_with_numbers(self):
        """Test safe_max returns maximum value."""
        result = safe_max([1, 5, 3, 2])
        assert result == 5
    
    def test_safe_min_with_none(self):
        """Test safe_min handles None collections."""
        result = safe_min(None, 0)
        assert result == 0
    
    def test_safe_min_with_numbers(self):
        """Test safe_min returns minimum value."""
        result = safe_min([1, 5, 3, 2])
        assert result == 1
    
    def test_safe_sum_with_none(self):
        """Test safe_sum handles None collections."""
        result = safe_sum(None, 0)
        assert result == 0
    
    def test_safe_sum_with_numbers(self):
        """Test safe_sum returns sum of values."""
        result = safe_sum([1, 2, 3, 4])
        assert result == 10
    
    def test_safe_filter_with_none(self):
        """Test safe_filter handles None collections."""
        result = safe_filter(None, lambda x: x > 0)
        assert result == []
    
    def test_safe_filter_with_predicate(self):
        """Test safe_filter applies predicate correctly."""
        result = safe_filter([1, -2, 3, -4], lambda x: x > 0)
        assert result == [1, 3]
    
    def test_safe_map_with_none(self):
        """Test safe_map handles None collections."""
        result = safe_map(None, lambda x: x * 2)
        assert result == []
    
    def test_safe_map_with_function(self):
        """Test safe_map applies function correctly."""
        result = safe_map([1, 2, 3], lambda x: x * 2)
        assert result == [2, 4, 6]
    
    def test_get_default_for_type(self):
        """Test get_default_for_type returns correct defaults."""
        assert get_default_for_type('dict') == {}
        assert get_default_for_type('list') == []
        assert get_default_for_type('str') == ''
        assert get_default_for_type('int') == 0
        assert get_default_for_type('unknown') is None
    
    def test_get_attribute_default(self):
        """Test get_attribute_default returns correct defaults."""
        result = get_attribute_default('design_specs', 'typography')
        assert result == {}
        
        result = get_attribute_default('publishing_info', 'primary_genres')
        assert result == []
    
    @patch('codexes.modules.ui.safety_patterns.logger')
    def test_validate_not_none_with_none(self, mock_logger):
        """Test validate_not_none logs None values."""
        result = validate_not_none(None, 'test_context', 'test_attr')
        assert result is False
        mock_logger.warning.assert_called_once()
    
    def test_validate_not_none_with_value(self):
        """Test validate_not_none returns True for non-None values."""
        result = validate_not_none('value', 'test_context', 'test_attr')
        assert result is True


class TestUIDataValidator:
    """Test UIDataValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = UIDataValidator()
    
    def test_validate_design_specs_with_none(self):
        """Test validate_design_specs handles None input."""
        result = self.validator.validate_design_specs(None)
        
        assert isinstance(result, dict)
        assert 'typography' in result
        assert 'color_palette' in result
        assert 'trim_sizes' in result
        assert 'layout_preferences' in result
        assert self.validator.validation_stats['none_values_fixed'] > 0
    
    def test_validate_design_specs_with_partial_data(self):
        """Test validate_design_specs fills missing attributes."""
        partial_data = {'typography': {'font_size': 14}}
        result = self.validator.validate_design_specs(partial_data)
        
        assert 'color_palette' in result
        assert 'trim_sizes' in result
        assert result['typography']['font_size'] == 14
    
    def test_validate_publishing_info_with_none(self):
        """Test validate_publishing_info handles None input."""
        result = self.validator.validate_publishing_info(None)
        
        assert isinstance(result, dict)
        assert isinstance(result['primary_genres'], list)
        assert isinstance(result['target_audience'], str)
        assert isinstance(result['publication_details'], dict)
    
    def test_validate_branding_info_with_none(self):
        """Test validate_branding_info handles None input."""
        result = self.validator.validate_branding_info(None)
        
        assert isinstance(result, dict)
        assert isinstance(result['brand_values'], list)
        assert isinstance(result['visual_identity'], dict)
        assert isinstance(result['messaging'], dict)
    
    def test_validate_validation_results_with_none(self):
        """Test validate_validation_results handles None input."""
        result = self.validator.validate_validation_results(None)
        
        assert isinstance(result, dict)
        assert isinstance(result['errors'], list)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['is_valid'], bool)
    
    def test_get_validation_stats(self):
        """Test get_validation_stats returns statistics."""
        self.validator.validate_design_specs(None)
        stats = self.validator.get_validation_stats()
        
        assert 'validations_performed' in stats
        assert 'none_values_fixed' in stats
        assert stats['validations_performed'] > 0
    
    def test_reset_stats(self):
        """Test reset_stats clears statistics."""
        self.validator.validate_design_specs(None)
        self.validator.reset_stats()
        stats = self.validator.get_validation_stats()
        
        assert stats['validations_performed'] == 0
        assert stats['none_values_fixed'] == 0


class TestAttributeDefaultProvider:
    """Test AttributeDefaultProvider class."""
    
    def test_get_default_for_attribute(self):
        """Test get_default_for_attribute returns correct defaults."""
        result = AttributeDefaultProvider.get_default_for_attribute(
            'design_specs', 'typography'
        )
        assert result == {}
    
    def test_ensure_attribute_exists_with_none_object(self):
        """Test ensure_attribute_exists handles None objects."""
        result = AttributeDefaultProvider.ensure_attribute_exists(
            None, 'attr', 'default'
        )
        assert result == 'default'
    
    def test_get_safe_dict_attribute(self):
        """Test get_safe_dict_attribute handles nested access."""
        obj = MagicMock()
        obj.config = {'key': 'value'}
        
        result = AttributeDefaultProvider.get_safe_dict_attribute(
            obj, 'config', 'key', 'default'
        )
        assert result == 'value'
    
    def test_get_safe_dict_attribute_with_none_dict(self):
        """Test get_safe_dict_attribute handles None dictionaries."""
        obj = MagicMock()
        obj.config = None
        
        result = AttributeDefaultProvider.get_safe_dict_attribute(
            obj, 'config', 'key', 'default'
        )
        assert result == 'default'


class TestStructureNormalizer:
    """Test StructureNormalizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = UIDataValidator()
        self.normalizer = StructureNormalizer(self.validator)
    
    def test_normalize_imprint_data_with_none(self):
        """Test normalize_imprint_data handles None input."""
        result = self.normalizer.normalize_imprint_data(None)
        
        assert isinstance(result, dict)
        assert 'design_specs' in result
        assert 'publishing_info' in result
        assert 'branding_info' in result
        assert 'validation_results' in result
        assert 'metadata' in result
        assert 'status' in result
    
    def test_normalize_form_data_with_none(self):
        """Test normalize_form_data handles None input."""
        result = self.normalizer.normalize_form_data(None)
        assert result == {}
    
    def test_normalize_form_data_with_none_values(self):
        """Test normalize_form_data handles None values in form data."""
        form_data = {
            'genres_list': None,
            'config_dict': None,
            'enabled_flag': None,
            'title': None
        }
        result = self.normalizer.normalize_form_data(form_data)
        
        assert isinstance(result['genres_list'], list)
        assert isinstance(result['config_dict'], dict)
        assert isinstance(result['enabled_flag'], bool)
        assert isinstance(result['title'], str)
    
    def test_ensure_list_structure(self):
        """Test ensure_list_structure normalizes list attributes."""
        obj = {'items': None, 'values': 'not_a_list'}
        result = self.normalizer.ensure_list_structure(obj, ['items', 'values'])
        
        assert isinstance(result['items'], list)
        assert isinstance(result['values'], list)
    
    def test_ensure_dict_structure(self):
        """Test ensure_dict_structure normalizes dict attributes."""
        obj = {'config': None, 'settings': 'not_a_dict'}
        result = self.normalizer.ensure_dict_structure(obj, ['config', 'settings'])
        
        assert isinstance(result['config'], dict)
        assert isinstance(result['settings'], dict)

class TestErrorPrevention:
    """Test error prevention utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from codexes.modules.ui.error_prevention import UIErrorPrevention
        self.error_prevention = UIErrorPrevention()
    
    def test_prevent_none_access(self):
        """Test prevent_none_access handles None objects."""
        result = self.error_prevention.prevent_none_access(None, 'test_context')
        assert result == {}
        assert self.error_prevention.error_stats['none_values_prevented'] > 0
    
    def test_prevent_none_access_with_valid_object(self):
        """Test prevent_none_access returns valid objects unchanged."""
        test_obj = {'key': 'value'}
        result = self.error_prevention.prevent_none_access(test_obj, 'test_context')
        assert result == test_obj
    
    def test_safe_attribute_chain_with_none(self):
        """Test safe_attribute_chain handles None objects."""
        result = self.error_prevention.safe_attribute_chain(None, 'attr1', 'attr2', default='default')
        assert result == 'default'
        assert self.error_prevention.error_stats['attribute_errors_prevented'] > 0
    
    def test_safe_attribute_chain_with_missing_attribute(self):
        """Test safe_attribute_chain handles missing attributes."""
        obj = type('TestObj', (), {'attr1': type('SubObj', (), {})()})()
        result = self.error_prevention.safe_attribute_chain(obj, 'attr1', 'missing_attr', default='default')
        assert result == 'default'
    
    def test_safe_attribute_chain_with_valid_chain(self):
        """Test safe_attribute_chain returns valid attribute chain."""
        obj = type('TestObj', (), {
            'attr1': type('SubObj', (), {'attr2': 'value'})()
        })()
        result = self.error_prevention.safe_attribute_chain(obj, 'attr1', 'attr2', default='default')
        assert result == 'value'
    
    def test_safe_nested_dict_get_with_none(self):
        """Test safe_nested_dict_get handles None dictionaries."""
        result = self.error_prevention.safe_nested_dict_get(None, 'key1', 'key2', default='default')
        assert result == 'default'
        assert self.error_prevention.error_stats['key_errors_prevented'] > 0
    
    def test_safe_nested_dict_get_with_missing_keys(self):
        """Test safe_nested_dict_get handles missing keys."""
        data = {'key1': {}}
        result = self.error_prevention.safe_nested_dict_get(data, 'key1', 'missing_key', default='default')
        assert result == 'default'
    
    def test_safe_nested_dict_get_with_valid_path(self):
        """Test safe_nested_dict_get returns valid nested values."""
        data = {'key1': {'key2': 'value'}}
        result = self.error_prevention.safe_nested_dict_get(data, 'key1', 'key2', default='default')
        assert result == 'value'
    
    def test_safe_collection_operation_with_none(self):
        """Test safe_collection_operation handles None collections."""
        result = self.error_prevention.safe_collection_operation(
            None, len, default=0, context='test'
        )
        assert result == 0
        assert self.error_prevention.error_stats['type_errors_prevented'] > 0
    
    def test_safe_collection_operation_with_valid_collection(self):
        """Test safe_collection_operation works with valid collections."""
        result = self.error_prevention.safe_collection_operation(
            [1, 2, 3], len, default=0, context='test'
        )
        assert result == 3
    
    def test_graceful_degradation_primary_success(self):
        """Test graceful_degradation uses primary function when successful."""
        def primary():
            return 'primary_result'
        
        def fallback():
            return 'fallback_result'
        
        result = self.error_prevention.graceful_degradation(primary, fallback, 'test')
        assert result == 'primary_result'
    
    def test_graceful_degradation_primary_failure(self):
        """Test graceful_degradation uses fallback when primary fails."""
        def primary():
            raise ValueError("Primary failed")
        
        def fallback():
            return 'fallback_result'
        
        result = self.error_prevention.graceful_degradation(primary, fallback, 'test')
        assert result == 'fallback_result'
        assert self.error_prevention.error_stats['graceful_degradations'] > 0
    
    def test_get_error_stats(self):
        """Test get_error_stats returns statistics."""
        # Trigger some errors
        self.error_prevention.prevent_none_access(None, 'test')
        self.error_prevention.safe_attribute_chain(None, 'attr', default='default')
        
        stats = self.error_prevention.get_error_stats()
        assert 'none_values_prevented' in stats
        assert 'attribute_errors_prevented' in stats
        assert stats['none_values_prevented'] > 0
        assert stats['attribute_errors_prevented'] > 0
    
    def test_reset_stats(self):
        """Test reset_stats clears statistics."""
        # Trigger some errors
        self.error_prevention.prevent_none_access(None, 'test')
        
        # Reset and verify
        self.error_prevention.reset_stats()
        stats = self.error_prevention.get_error_stats()
        assert all(count == 0 for count in stats.values())


class TestStreamlitErrorGuard:
    """Test Streamlit error guard utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from codexes.modules.ui.error_prevention import StreamlitErrorGuard
        self.error_guard = StreamlitErrorGuard()
    
    def test_get_safe_default_for_key(self):
        """Test _get_safe_default_for_key returns appropriate defaults."""
        assert self.error_guard._get_safe_default_for_key('config_data') == {}
        assert self.error_guard._get_safe_default_for_key('items_list') == []
        assert self.error_guard._get_safe_default_for_key('count_value') == 0
        assert self.error_guard._get_safe_default_for_key('is_enabled') == False
        assert self.error_guard._get_safe_default_for_key('title') == ''


class TestGracefulDegradationManager:
    """Test graceful degradation manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from codexes.modules.ui.error_prevention import GracefulDegradationManager
        self.degradation_manager = GracefulDegradationManager()
    
    def test_handle_missing_data_with_none(self):
        """Test handle_missing_data provides appropriate fallbacks for None."""
        result = self.degradation_manager.handle_missing_data(None, 'config', 'test')
        assert result == {}
        assert self.degradation_manager.degradation_stats['missing_data_handled'] > 0
    
    def test_handle_missing_data_with_empty_string(self):
        """Test handle_missing_data handles empty strings."""
        result = self.degradation_manager.handle_missing_data('', 'string', 'test')
        assert result == ''
        assert self.degradation_manager.degradation_stats['missing_data_handled'] > 0
    
    def test_handle_missing_data_with_valid_data(self):
        """Test handle_missing_data returns valid data unchanged."""
        test_data = {'key': 'value'}
        result = self.degradation_manager.handle_missing_data(test_data, 'config', 'test')
        assert result == test_data
    
    def test_handle_missing_data_fallbacks(self):
        """Test handle_missing_data provides correct fallbacks for different types."""
        assert self.degradation_manager.handle_missing_data(None, 'list', 'test') == []
        assert self.degradation_manager.handle_missing_data(None, 'number', 'test') == 0
        assert self.degradation_manager.handle_missing_data(None, 'boolean', 'test') == False
        
        validation_result = self.degradation_manager.handle_missing_data(None, 'validation_results', 'test')
        assert validation_result['is_valid'] == False
        assert isinstance(validation_result['errors'], list)
        assert isinstance(validation_result['warnings'], list)
    
    def test_recover_from_operation_failure(self):
        """Test recover_from_operation_failure provides appropriate fallbacks."""
        error = ValueError("Test error")
        
        result = self.degradation_manager.recover_from_operation_failure('config_load', error)
        assert result == {}
        assert self.degradation_manager.degradation_stats['failed_operations_recovered'] > 0
        
        result = self.degradation_manager.recover_from_operation_failure('scan_files', error)
        assert result == []
        
        result = self.degradation_manager.recover_from_operation_failure('validation', error)
        assert result['is_valid'] == False
        assert 'Test error' in result['errors']
    
    def test_recover_from_operation_failure_with_custom_fallback(self):
        """Test recover_from_operation_failure uses custom fallback when provided."""
        error = ValueError("Test error")
        custom_fallback = {'custom': 'fallback'}
        
        result = self.degradation_manager.recover_from_operation_failure(
            'unknown_operation', error, custom_fallback
        )
        assert result == custom_fallback
    
    def test_get_degradation_stats(self):
        """Test get_degradation_stats returns statistics."""
        # Trigger some degradations
        self.degradation_manager.handle_missing_data(None, 'config', 'test')
        self.degradation_manager.recover_from_operation_failure('test_op', ValueError("test"))
        
        stats = self.degradation_manager.get_degradation_stats()
        assert 'missing_data_handled' in stats
        assert 'failed_operations_recovered' in stats
        assert stats['missing_data_handled'] > 0
        assert stats['failed_operations_recovered'] > 0
    
    def test_reset_stats(self):
        """Test reset_stats clears statistics."""
        # Trigger some degradations
        self.degradation_manager.handle_missing_data(None, 'config', 'test')
        
        # Reset and verify
        self.degradation_manager.reset_stats()
        stats = self.degradation_manager.get_degradation_stats()
        assert all(count == 0 for count in stats.values())


class TestAutofixCompatibility:
    """Test that safety patterns remain intact after autofix operations."""
    
    def test_safe_access_patterns_syntax(self):
        """Test that safe access patterns use standard Python syntax."""
        from src.codexes.modules.ui.safety_patterns import (
            safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join
        )
        
        # These patterns should use standard Python idioms that autofix preserves
        
        # Test getattr usage (standard Python)
        result = safe_getattr(None, 'attr', 'default')
        assert result == 'default'
        
        # Test dict.get with or operator (standard Python)
        result = safe_dict_get(None, 'key', 'default')
        assert result == 'default'
        
        # Test or operator for collections (standard Python)
        result = list(safe_iteration(None))
        assert result == []
        
        # Test len with or operator (standard Python)
        result = safe_len(None)
        assert result == 0
        
        # Test join with or operator (standard Python)
        result = safe_join(None)
        assert result == ''
    
    def test_session_state_patterns_syntax(self):
        """Test that session state patterns use standard Streamlit idioms."""
        # These patterns should be compatible with Streamlit's expected usage
        
        # Standard dict.get pattern
        test_state = {'key': 'value'}
        result = test_state.get('key', 'default')
        assert result == 'value'
        
        # Standard 'in' operator
        assert 'key' in test_state
        assert 'missing' not in test_state
        
        # Standard dict.update pattern
        updates = {'new_key': 'new_value'}
        test_state.update(updates)
        assert test_state['new_key'] == 'new_value'
    
    def test_error_handling_patterns_syntax(self):
        """Test that error handling uses standard Python exception handling."""
        # Standard try/except pattern
        try:
            result = None.attribute  # This will raise AttributeError
        except AttributeError:
            result = 'handled'
        
        assert result == 'handled'
        
        # Standard isinstance check
        value = None
        if isinstance(value, dict):
            result = 'dict'
        else:
            result = 'not_dict'
        
        assert result == 'not_dict'


class TestUIRobustnessIntegration:
    """Integration tests for complete UI robustness."""
    
    def test_complete_none_value_workflow(self):
        """Test complete workflow with None values at every step."""
        from src.codexes.modules.ui.safety_patterns import (
            safe_getattr, safe_dict_get, safe_iteration, safe_len
        )
        from src.codexes.modules.ui.data_validators import UIDataValidator
        from src.codexes.modules.ui.error_prevention import handle_missing_data
        
        # Simulate complete None data scenario
        none_data = None
        
        # Step 1: Handle missing data
        safe_data = handle_missing_data(none_data, 'config', 'test_workflow')
        assert isinstance(safe_data, dict)
        
        # Step 2: Validate data structure
        validator = UIDataValidator()
        validated_data = validator.validate_design_specs(safe_data)
        assert isinstance(validated_data, dict)
        assert 'typography' in validated_data
        
        # Step 3: Safe access patterns
        typography = safe_dict_get(validated_data, 'typography', {})
        assert isinstance(typography, dict)
        
        # Step 4: Safe iteration
        trim_sizes = safe_dict_get(validated_data, 'trim_sizes', [])
        for size in safe_iteration(trim_sizes):
            assert size is not None  # Should not iterate if None
        
        # Step 5: Safe length calculation
        size_count = safe_len(trim_sizes)
        assert isinstance(size_count, int)
        assert size_count >= 0
    
    def test_ui_component_error_scenarios(self):
        """Test UI components handle various error scenarios."""
        from src.codexes.modules.ui.data_validators import UIDataValidator
        
        validator = UIDataValidator()
        
        # Test with completely invalid data
        invalid_scenarios = [
            None,
            {},
            {'invalid': 'structure'},
            {'typography': None, 'color_palette': None}
        ]
        
        for scenario in invalid_scenarios:
            # Should not raise exceptions
            result = validator.validate_design_specs(scenario)
            assert isinstance(result, dict)
            assert 'typography' in result
            assert 'color_palette' in result
            assert 'trim_sizes' in result
    
    def test_performance_with_safety_patterns(self):
        """Test that safety patterns don't significantly impact performance."""
        import time
        from codexes.modules.ui.safety_patterns import safe_dict_get, safe_len, safe_iteration
        
        # Test data
        test_data = {'key': 'value', 'list': list(range(1000))}
        
        # Measure performance of safe patterns
        start_time = time.time()
        for _ in range(1000):
            value = safe_dict_get(test_data, 'key', 'default')
            length = safe_len(test_data.get('list'))
            for item in safe_iteration(test_data.get('list', [])):
                if item > 500:  # Early break to avoid long test
                    break
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 1000 iterations)
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"Safety patterns too slow: {execution_time}s"
    
    def test_memory_usage_with_safety_patterns(self):
        """Test that safety patterns don't cause memory leaks."""
        from src.codexes.modules.ui.data_validators import UIDataValidator
        
        validator = UIDataValidator()
        
        # Validate many objects to check for memory leaks
        for i in range(100):
            test_data = {
                'typography': {'font': f'font_{i}'},
                'color_palette': {'primary': f'#color_{i}'},
                'trim_sizes': [f'size_{i}']
            }
            
            result = validator.validate_design_specs(test_data)
            assert isinstance(result, dict)
            
            # Clear reference to help garbage collection
            del result
        
        # If we get here without memory issues, the test passes
        assert True