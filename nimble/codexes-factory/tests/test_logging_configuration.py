"""
Tests for logging configuration functionality.

This module tests the configuration file-based logging system including:
- Configuration file loading and parsing
- Environment-specific overrides
- Statistics reporting configuration
- LiteLLM filter configuration
- Dynamic configuration updates
"""

import json
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.logging_config import (
    LoggingConfigManager,
    get_logging_manager,
    setup_application_logging,
    get_statistics_config,
    get_litellm_filter_config
)
from src.codexes.core.statistics_reporter import StatisticsReporter
from src.codexes.core.token_usage_tracker import TokenUsageTracker


class TestLoggingConfiguration(unittest.TestCase):
    """Test logging configuration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_logging_config.json')
        
        # Sample configuration for testing
        self.test_config = {
            "version": 1,
            "settings": {
                "litellm_filtering": {
                    "enabled": True,
                    "debug_mode_override": False
                },
                "statistics_reporting": {
                    "enabled": True,
                    "detail_level": "standard",
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True
                },
                "log_levels": {
                    "application": "INFO",
                    "litellm": "WARNING",
                    "openai": "WARNING",
                    "httpx": "WARNING"
                },
                "output_formats": {
                    "console_format": "standard",
                    "file_format": "detailed",
                    "timestamp_format": "%Y-%m-%d %H:%M:%S"
                },
                "handlers": {
                    "console_enabled": True,
                    "file_enabled": True,
                    "error_file_enabled": True,
                    "console_level": "INFO",
                    "file_level": "DEBUG",
                    "error_file_level": "ERROR"
                },
                "files": {
                    "application_log": "logs/test_application.log",
                    "error_log": "logs/test_errors.log",
                    "statistics_log": "logs/test_statistics.log",
                    "encoding": "utf-8"
                },
                "environment_overrides": {
                    "development": {
                        "log_levels": {
                            "application": "DEBUG"
                        },
                        "handlers": {
                            "console_level": "DEBUG"
                        }
                    },
                    "production": {
                        "log_levels": {
                            "application": "WARNING"
                        },
                        "handlers": {
                            "console_level": "ERROR"
                        }
                    }
                }
            },
            "detail_levels": {
                "minimal": {
                    "include_model_breakdown": False,
                    "include_prompt_breakdown": False,
                    "include_cost_analysis": False
                },
                "standard": {
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True
                },
                "detailed": {
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True,
                    "include_timing_analysis": True,
                    "include_performance_metrics": True
                }
            },
            "format_templates": {
                "simple": "%(levelname)s - %(message)s",
                "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            }
        }
        
        # Write test configuration to file
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
        
        # Reset global logging manager
        try:
            import src.codexes.core.logging_config as logging_config_module
            logging_config_module._logging_manager = None
        except ImportError:
            pass
    
    def test_config_file_loading(self):
        """Test that configuration files are loaded correctly."""
        manager = LoggingConfigManager(self.config_file)
        
        # Verify configuration was loaded
        self.assertIsNotNone(manager._config_data)
        self.assertEqual(manager._config_data['version'], 1)
        
        # Verify specific settings
        settings = manager._config_data['settings']
        self.assertTrue(settings['litellm_filtering']['enabled'])
        self.assertEqual(settings['statistics_reporting']['detail_level'], 'standard')
        self.assertEqual(settings['log_levels']['application'], 'INFO')
    
    def test_default_config_fallback(self):
        """Test fallback to default configuration when file doesn't exist."""
        non_existent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        manager = LoggingConfigManager(non_existent_file)
        
        # Should have default configuration
        self.assertIsNotNone(manager._config_data)
        self.assertIn('settings', manager._config_data)
    
    def test_environment_overrides(self):
        """Test environment-specific configuration overrides."""
        manager = LoggingConfigManager(self.config_file)
        
        # Test development environment overrides
        dev_overrides = manager._get_environment_overrides('development')
        self.assertEqual(dev_overrides['log_levels']['application'], 'DEBUG')
        self.assertEqual(dev_overrides['handlers']['console_level'], 'DEBUG')
        
        # Test production environment overrides
        prod_overrides = manager._get_environment_overrides('production')
        self.assertEqual(prod_overrides['log_levels']['application'], 'WARNING')
        self.assertEqual(prod_overrides['handlers']['console_level'], 'ERROR')
    
    def test_statistics_config_retrieval(self):
        """Test retrieval of statistics reporting configuration."""
        manager = LoggingConfigManager(self.config_file)
        stats_config = manager.get_statistics_config()
        
        self.assertTrue(stats_config['enabled'])
        self.assertEqual(stats_config['detail_level'], 'standard')
        self.assertTrue(stats_config['include_model_breakdown'])
        self.assertTrue(stats_config['include_prompt_breakdown'])
        self.assertTrue(stats_config['include_cost_analysis'])
    
    def test_statistics_config_detail_levels(self):
        """Test different detail levels for statistics configuration."""
        # Test minimal detail level
        self.test_config['settings']['statistics_reporting']['detail_level'] = 'minimal'
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f, indent=2)
        
        manager = LoggingConfigManager(self.config_file)
        stats_config = manager.get_statistics_config()
        
        self.assertEqual(stats_config['detail_level'], 'minimal')
        self.assertFalse(stats_config['include_model_breakdown'])
        self.assertFalse(stats_config['include_prompt_breakdown'])
        self.assertFalse(stats_config['include_cost_analysis'])
        
        # Test detailed detail level
        self.test_config['settings']['statistics_reporting']['detail_level'] = 'detailed'
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f, indent=2)
        
        manager = LoggingConfigManager(self.config_file)
        stats_config = manager.get_statistics_config()
        
        self.assertEqual(stats_config['detail_level'], 'detailed')
        self.assertTrue(stats_config['include_timing_analysis'])
        self.assertTrue(stats_config['include_performance_metrics'])
    
    def test_litellm_filter_config(self):
        """Test LiteLLM filter configuration retrieval."""
        manager = LoggingConfigManager(self.config_file)
        filter_config = manager.get_litellm_filter_config()
        
        self.assertTrue(filter_config['enabled'])
        self.assertFalse(filter_config['debug_mode_override'])
    
    def test_log_file_paths(self):
        """Test log file path configuration."""
        manager = LoggingConfigManager(self.config_file)
        file_paths = manager.get_log_file_paths()
        
        self.assertEqual(file_paths['application_log'], 'logs/test_application.log')
        self.assertEqual(file_paths['error_log'], 'logs/test_errors.log')
        self.assertEqual(file_paths['statistics_log'], 'logs/test_statistics.log')
    
    def test_config_merging(self):
        """Test configuration merging functionality."""
        manager = LoggingConfigManager(self.config_file)
        
        base_config = {
            'level1': {
                'level2': {
                    'key1': 'value1',
                    'key2': 'value2'
                }
            }
        }
        
        overrides = {
            'level1': {
                'level2': {
                    'key2': 'new_value2',
                    'key3': 'value3'
                }
            }
        }
        
        merged = manager._merge_config(base_config, overrides)
        
        self.assertEqual(merged['level1']['level2']['key1'], 'value1')
        self.assertEqual(merged['level1']['level2']['key2'], 'new_value2')
        self.assertEqual(merged['level1']['level2']['key3'], 'value3')
    
    def test_dynamic_config_updates(self):
        """Test dynamic configuration updates."""
        manager = LoggingConfigManager(self.config_file)
        
        # Update configuration
        updates = {
            'settings': {
                'statistics_reporting': {
                    'detail_level': 'minimal'
                }
            }
        }
        
        manager.update_config(updates)
        
        # Verify update was applied
        stats_config = manager.get_statistics_config()
        self.assertEqual(stats_config['detail_level'], 'minimal')
    
    def test_config_save(self):
        """Test saving configuration to file."""
        manager = LoggingConfigManager(self.config_file)
        
        # Modify configuration
        manager._config_data['settings']['statistics_reporting']['detail_level'] = 'detailed'
        
        # Save to new file
        new_config_file = os.path.join(self.temp_dir, 'saved_config.json')
        manager.save_config(new_config_file)
        
        # Verify file was saved correctly
        self.assertTrue(os.path.exists(new_config_file))
        
        with open(new_config_file, 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['settings']['statistics_reporting']['detail_level'], 'detailed')
        
        # Clean up
        os.unlink(new_config_file)
    
    @patch('src.codexes.core.logging_config.logging.config.dictConfig')
    def test_logging_setup_with_config(self, mock_dict_config):
        """Test logging setup with configuration file."""
        manager = LoggingConfigManager(self.config_file)
        manager.setup_logging()
        
        # Verify dictConfig was called
        mock_dict_config.assert_called_once()
        
        # Verify configuration structure
        config_arg = mock_dict_config.call_args[0][0]
        self.assertEqual(config_arg['version'], 1)
        self.assertIn('formatters', config_arg)
        self.assertIn('handlers', config_arg)
        self.assertIn('loggers', config_arg)
    
    def test_global_functions(self):
        """Test global convenience functions."""
        # Test get_logging_manager
        manager = get_logging_manager(self.config_file)
        self.assertIsInstance(manager, LoggingConfigManager)
        
        # Test get_statistics_config
        stats_config = get_statistics_config()
        self.assertIsInstance(stats_config, dict)
        self.assertIn('enabled', stats_config)
        
        # Test get_litellm_filter_config
        filter_config = get_litellm_filter_config()
        self.assertIsInstance(filter_config, dict)
        self.assertIn('enabled', filter_config)


class TestStatisticsReporterConfiguration(unittest.TestCase):
    """Test StatisticsReporter configuration integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_logging_config.json')
        
        # Configuration with different detail levels
        self.test_config = {
            "settings": {
                "statistics_reporting": {
                    "enabled": True,
                    "detail_level": "standard",
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True
                }
            },
            "detail_levels": {
                "minimal": {
                    "include_model_breakdown": False,
                    "include_prompt_breakdown": False,
                    "include_cost_analysis": False
                },
                "standard": {
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
        
        # Reset global logging manager
        try:
            import src.codexes.core.logging_config as logging_config_module
            logging_config_module._logging_manager = None
        except ImportError:
            pass
    
    @patch('src.codexes.core.logging_config.get_statistics_config')
    def test_reporter_uses_config(self, mock_get_config):
        """Test that StatisticsReporter uses configuration."""
        mock_config = {
            "enabled": True,
            "detail_level": "minimal",
            "include_model_breakdown": False,
            "include_prompt_breakdown": False,
            "include_cost_analysis": False
        }
        mock_get_config.return_value = mock_config
        
        reporter = StatisticsReporter()
        self.assertEqual(reporter.config, mock_config)
        self.assertEqual(reporter.config['detail_level'], 'minimal')
    
    def test_reporter_with_explicit_config(self):
        """Test StatisticsReporter with explicitly provided configuration."""
        custom_config = {
            "enabled": True,
            "detail_level": "detailed",
            "include_model_breakdown": True,
            "include_prompt_breakdown": True,
            "include_cost_analysis": True,
            "include_timing_analysis": True,
            "include_performance_metrics": True
        }
        
        reporter = StatisticsReporter(custom_config)
        self.assertEqual(reporter.config, custom_config)
        self.assertEqual(reporter.config['detail_level'], 'detailed')
    
    def test_disabled_reporting(self):
        """Test that reporting is skipped when disabled."""
        config = {"enabled": False}
        reporter = StatisticsReporter(config)
        
        # Create a mock tracker
        tracker = MagicMock()
        
        with patch.object(reporter.logger, 'info') as mock_info:
            # Call report_pipeline_statistics
            reporter.report_pipeline_statistics(tracker)
            
            # Verify no logging occurred
            mock_info.assert_not_called()
    
    def test_minimal_detail_level(self):
        """Test minimal detail level reporting."""
        config = {
            "enabled": True,
            "detail_level": "minimal",
            "include_model_breakdown": False,
            "include_prompt_breakdown": False,
            "include_cost_analysis": False
        }
        
        reporter = StatisticsReporter(config)
        
        # Create a mock tracker with sample data
        tracker = MagicMock()
        tracker.get_total_statistics.return_value = {
            'total_calls': 5,
            'total_tokens': 1000,
            'total_cost': 0.05,
            'duration_seconds': 10.0
        }
        
        with patch.object(reporter.logger, 'info') as mock_info:
            # Call report_pipeline_statistics
            reporter.report_pipeline_statistics(tracker)
            
            # Verify minimal logging occurred
            mock_info.assert_called()
            
            # Verify model breakdown methods were not called
            tracker.get_model_breakdown.assert_not_called()
            tracker.get_prompt_breakdown.assert_not_called()


if __name__ == '__main__':
    unittest.main()