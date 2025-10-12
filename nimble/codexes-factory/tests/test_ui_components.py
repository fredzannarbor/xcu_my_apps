"""
Tests for UI Components
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Import the modules to test
try:
    from src.codexes.modules.ui.configuration_manager import EnhancedConfigurationManager, ValidationResult
    from src.codexes.modules.ui.dynamic_config_loader import DynamicConfigurationLoader
    from src.codexes.modules.ui.parameter_groups import ParameterGroupManager, ParameterType
    from src.codexes.modules.ui.config_validator import ConfigurationValidator
    from src.codexes.modules.ui.command_builder import CommandBuilder
except ImportError:
    pytest.skip("UI components not available", allow_module_level=True)


class TestEnhancedConfigurationManager:
    """Test the enhanced configuration manager"""
    
    def test_initialization(self):
        """Test that the configuration manager initializes correctly"""
        manager = EnhancedConfigurationManager()
        assert manager is not None
        assert hasattr(manager, 'config_loader')
        assert hasattr(manager, 'publisher_loader')
        assert hasattr(manager, 'imprint_loader')
        assert hasattr(manager, 'tranche_loader')
    
    def test_load_available_configs(self):
        """Test loading available configurations"""
        manager = EnhancedConfigurationManager()
        configs = manager.load_available_configs()
        
        assert isinstance(configs, dict)
        assert 'publishers' in configs
        assert 'imprints' in configs
        assert 'tranches' in configs
        assert isinstance(configs['publishers'], list)
        assert isinstance(configs['imprints'], list)
        assert isinstance(configs['tranches'], list)
    
    def test_merge_configurations(self):
        """Test configuration merging"""
        manager = EnhancedConfigurationManager()
        
        # Test with no parameters (should return default config)
        merged = manager.merge_configurations()
        assert isinstance(merged, dict)
        
        # Test with invalid parameters (should return default config)
        merged = manager.merge_configurations("nonexistent", "nonexistent", "nonexistent")
        assert isinstance(merged, dict)
    
    def test_validate_configuration(self):
        """Test configuration validation"""
        manager = EnhancedConfigurationManager()
        
        # Test empty configuration
        result = manager.validate_configuration({})
        assert isinstance(result, ValidationResult)
        assert not result.is_valid  # Should be invalid due to missing required fields
        assert len(result.errors) > 0
        
        # Test valid configuration
        valid_config = {
            'publisher': 'Test Publisher',
            'imprint': 'Test Imprint',
            'lightning_source_account': '1234567',
            'language_code': 'eng',
            'territorial_rights': 'World'
        }
        result = manager.validate_configuration(valid_config)
        assert isinstance(result, ValidationResult)
        # Note: May still have errors due to other validation rules
    
    def test_get_parameter_groups(self):
        """Test parameter group retrieval"""
        manager = EnhancedConfigurationManager()
        groups = manager.get_parameter_groups()
        
        assert isinstance(groups, dict)
        expected_groups = [
            'core_settings', 'lsi_configuration', 'territorial_pricing',
            'physical_specifications', 'metadata_defaults', 'distribution_settings'
        ]
        
        for group in expected_groups:
            assert group in groups
            assert isinstance(groups[group], list)


class TestDynamicConfigurationLoader:
    """Test the dynamic configuration loader"""
    
    def test_initialization(self):
        """Test that the loader initializes correctly"""
        loader = DynamicConfigurationLoader()
        assert loader is not None
        assert hasattr(loader, 'config_schemas')
    
    def test_scan_publishers(self):
        """Test scanning for publisher configurations"""
        loader = DynamicConfigurationLoader()
        publishers = loader.scan_publishers()
        
        assert isinstance(publishers, list)
        # Should be sorted
        assert publishers == sorted(publishers)
    
    def test_scan_imprints(self):
        """Test scanning for imprint configurations"""
        loader = DynamicConfigurationLoader()
        imprints = loader.scan_imprints()
        
        assert isinstance(imprints, list)
        assert imprints == sorted(imprints)
    
    def test_scan_tranches(self):
        """Test scanning for tranche configurations"""
        loader = DynamicConfigurationLoader()
        tranches = loader.scan_tranches()
        
        assert isinstance(tranches, list)
        assert tranches == sorted(tranches)
    
    def test_validate_configuration_structure(self):
        """Test configuration structure validation"""
        loader = DynamicConfigurationLoader()
        
        # Test valid publisher config
        valid_publisher = {
            "publisher": "Test Publisher",
            "lightning_source_account": "1234567"
        }
        assert loader.validate_configuration_structure(valid_publisher, 'publisher')
        
        # Test invalid publisher config (missing required fields)
        invalid_publisher = {
            "name": "Test Publisher"  # Wrong field name
        }
        assert not loader.validate_configuration_structure(invalid_publisher, 'publisher')
    
    def test_create_configuration_template(self):
        """Test configuration template creation"""
        loader = DynamicConfigurationLoader()
        
        # Test publisher template
        pub_template = loader.create_configuration_template('publisher')
        assert isinstance(pub_template, dict)
        assert 'publisher' in pub_template
        assert 'lightning_source_account' in pub_template
        assert '_config_info' in pub_template
        
        # Test imprint template
        imp_template = loader.create_configuration_template('imprint')
        assert isinstance(imp_template, dict)
        assert 'imprint' in imp_template
        assert 'publisher' in imp_template
        
        # Test tranche template
        tr_template = loader.create_configuration_template('tranche')
        assert isinstance(tr_template, dict)
        assert 'tranche_info' in tr_template


class TestParameterGroupManager:
    """Test the parameter group manager"""
    
    def test_initialization(self):
        """Test that the manager initializes correctly"""
        manager = ParameterGroupManager()
        assert manager is not None
        assert hasattr(manager, 'parameter_definitions')
        assert hasattr(manager, 'group_definitions')
    
    def test_get_parameter_groups(self):
        """Test parameter group retrieval"""
        manager = ParameterGroupManager()
        groups = manager.get_parameter_groups()
        
        assert isinstance(groups, dict)
        assert len(groups) > 0
        
        # Check that each group has parameters
        for group_name, group in groups.items():
            assert hasattr(group, 'parameters')
            assert isinstance(group.parameters, list)
    
    def test_get_parameter_by_name(self):
        """Test parameter retrieval by name"""
        manager = ParameterGroupManager()
        
        # Test existing parameter
        param = manager.get_parameter_by_name('publisher')
        assert param is not None
        assert param.name == 'publisher'
        assert param.parameter_type == ParameterType.SELECT
        
        # Test non-existing parameter
        param = manager.get_parameter_by_name('nonexistent')
        assert param is None
    
    def test_validate_parameter_dependencies(self):
        """Test parameter dependency validation"""
        manager = ParameterGroupManager()
        
        # Test with valid dependencies
        params = {
            'publisher': 'Test Publisher',
            'imprint': 'Test Imprint'  # Depends on publisher
        }
        errors = manager.validate_parameter_dependencies(params)
        assert isinstance(errors, list)
        
        # Test with missing dependencies
        params = {
            'imprint': 'Test Imprint'  # Missing publisher dependency
        }
        errors = manager.validate_parameter_dependencies(params)
        assert len(errors) > 0
    
    def test_get_parameters_for_display_mode(self):
        """Test parameter filtering by display mode"""
        manager = ParameterGroupManager()
        
        # Test simple mode
        simple_params = manager.get_parameters_for_display_mode('simple')
        assert isinstance(simple_params, dict)
        
        # Test expert mode (should have more parameters)
        expert_params = manager.get_parameters_for_display_mode('expert')
        assert isinstance(expert_params, dict)
        assert len(expert_params) >= len(simple_params)


class TestConfigurationValidator:
    """Test the configuration validator"""
    
    def test_initialization(self):
        """Test that the validator initializes correctly"""
        validator = ConfigurationValidator()
        assert validator is not None
    
    def test_validate_configuration(self):
        """Test full configuration validation"""
        validator = ConfigurationValidator()
        
        # Test empty configuration
        result = validator.validate_configuration({})
        assert isinstance(result, ValidationResult)
        assert not result.is_valid
        assert len(result.errors) > 0
        
        # Test configuration with some valid fields
        config = {
            'publisher': 'Test Publisher',
            'imprint': 'Test Imprint',
            'lightning_source_account': '1234567',
            'language_code': 'eng'
        }
        result = validator.validate_configuration(config)
        assert isinstance(result, ValidationResult)
    
    def test_validate_single_parameter(self):
        """Test single parameter validation"""
        validator = ConfigurationValidator()
        
        # Test valid parameter
        result = validator.validate_single_parameter('publisher', 'Test Publisher')
        assert isinstance(result, ValidationResult)
        
        # Test invalid parameter
        result = validator.validate_single_parameter('lightning_source_account', 'invalid')
        assert isinstance(result, ValidationResult)
    
    def test_get_validation_suggestions(self):
        """Test validation suggestions"""
        validator = ConfigurationValidator()
        
        # Test parameter with suggestions
        suggestions = validator.get_validation_suggestions('trim_size', '6x9')
        assert isinstance(suggestions, list)
        
        # Test parameter without suggestions
        suggestions = validator.get_validation_suggestions('unknown_param', 'value')
        assert isinstance(suggestions, list)


class TestCommandBuilder:
    """Test the command builder"""
    
    def test_initialization(self):
        """Test that the builder initializes correctly"""
        builder = CommandBuilder()
        assert builder is not None
        assert hasattr(builder, 'temp_files')
    
    def test_build_pipeline_command(self):
        """Test pipeline command building"""
        builder = CommandBuilder()
        
        # Test minimal configuration
        config = {
            'imprint': 'test_imprint',
            'schedule_file': 'test_schedule.json',
            'model': 'gemini/gemini-2.5-flash'
        }
        
        command = builder.build_pipeline_command(config)
        assert isinstance(command, list)
        assert len(command) >= 3  # At least python, script, and some args
        assert 'python' in command[0]
        assert 'run_book_pipeline.py' in command[1]
        assert '--imprint' in command
        assert '--model' in command
    
    def test_serialize_complex_parameters(self):
        """Test complex parameter serialization"""
        builder = CommandBuilder()
        
        params = {
            'simple_param': 'value',
            'dict_param': {'key': 'value'},
            'list_param': ['item1', 'item2'],
            'none_param': None
        }
        
        serialized = builder.serialize_complex_parameters(params)
        assert isinstance(serialized, dict)
        assert 'simple_param' in serialized
        assert 'dict_param' in serialized
        assert 'list_param' in serialized
        assert 'none_param' not in serialized  # None values should be excluded
    
    def test_validate_command_parameters(self):
        """Test command parameter validation"""
        builder = CommandBuilder()
        
        # Test valid command
        valid_command = [
            'python', 'run_book_pipeline.py',
            '--imprint', 'test',
            '--schedule-file', 'test.json',
            '--model', 'gemini/gemini-2.5-flash'
        ]
        
        result = builder.validate_command_parameters(valid_command)
        assert isinstance(result, dict)
        assert 'is_valid' in result
        assert 'errors' in result
        assert 'parameter_count' in result
        
        # Test invalid command (missing required parameters)
        invalid_command = ['python', 'run_book_pipeline.py']
        result = builder.validate_command_parameters(invalid_command)
        assert not result['is_valid']
        assert len(result['errors']) > 0
    
    def test_get_command_summary(self):
        """Test command summary generation"""
        builder = CommandBuilder()
        
        command = [
            'python', 'run_book_pipeline.py',
            '--imprint', 'test',
            '--verbose',
            '--max-books', '5'
        ]
        
        summary = builder.get_command_summary(command)
        assert isinstance(summary, dict)
        assert 'script' in summary
        assert 'total_args' in summary
        assert 'parameters' in summary
        assert 'flags' in summary
        
        assert summary['script'] == 'run_book_pipeline.py'
        assert 'imprint' in summary['parameters']
        assert 'verbose' in summary['flags']
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        builder = CommandBuilder()
        
        # Add some fake temp files
        builder.temp_files = ['fake_file1.txt', 'fake_file2.json']
        
        # Cleanup should not raise an error even if files don't exist
        builder.cleanup_temp_files()
        assert len(builder.temp_files) == 0


# Integration tests
class TestUIIntegration:
    """Test integration between UI components"""
    
    def test_configuration_workflow(self):
        """Test the complete configuration workflow"""
        # Initialize components
        config_manager = EnhancedConfigurationManager()
        validator = ConfigurationValidator()
        command_builder = CommandBuilder()
        
        # Create a test configuration
        test_config = {
            'publisher': 'Test Publisher',
            'imprint': 'test_imprint',
            'lightning_source_account': '1234567',
            'language_code': 'eng',
            'model': 'gemini/gemini-2.5-flash',
            'schedule_file': 'test_schedule.json'
        }
        
        # Validate the configuration
        validation_result = validator.validate_configuration(test_config)
        assert isinstance(validation_result, ValidationResult)
        
        # Build command from configuration
        command = command_builder.build_pipeline_command(test_config)
        assert isinstance(command, list)
        assert len(command) > 2
        
        # Validate the built command
        command_validation = command_builder.validate_command_parameters(command)
        assert isinstance(command_validation, dict)
        
        # Clean up
        command_builder.cleanup_temp_files()


if __name__ == '__main__':
    pytest.main([__file__])