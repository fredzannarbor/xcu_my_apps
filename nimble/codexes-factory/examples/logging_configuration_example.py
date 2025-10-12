#!/usr/bin/env python3
"""
Example demonstrating the logging configuration system.

This script shows how to:
1. Use the default logging configuration
2. Load custom configuration from a file
3. Update configuration dynamically
4. Use different detail levels for statistics reporting
"""

import json
import logging
import tempfile
from pathlib import Path

# Add the src directory to the path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.logging_config import (
    LoggingConfigManager,
    setup_application_logging,
    get_statistics_config,
    get_litellm_filter_config
)
from src.codexes.core.statistics_reporter import StatisticsReporter
from src.codexes.core.token_usage_tracker import TokenUsageTracker


def example_default_configuration():
    """Example using default logging configuration."""
    print("=== Example 1: Default Configuration ===")
    
    # Set up logging with default configuration
    setup_application_logging()
    
    logger = logging.getLogger('codexes.example')
    logger.info("This is a test message with default configuration")
    
    # Get statistics configuration
    stats_config = get_statistics_config()
    print(f"Statistics reporting enabled: {stats_config['enabled']}")
    print(f"Detail level: {stats_config['detail_level']}")
    print(f"Include model breakdown: {stats_config['include_model_breakdown']}")
    
    # Get LiteLLM filter configuration
    filter_config = get_litellm_filter_config()
    print(f"LiteLLM filtering enabled: {filter_config['enabled']}")
    print()


def example_custom_configuration():
    """Example using custom configuration from file."""
    print("=== Example 2: Custom Configuration ===")
    
    # Create a custom configuration
    custom_config = {
        "version": 1,
        "settings": {
            "litellm_filtering": {
                "enabled": True,
                "debug_mode_override": True
            },
            "statistics_reporting": {
                "enabled": True,
                "detail_level": "detailed",
                "include_model_breakdown": True,
                "include_prompt_breakdown": True,
                "include_cost_analysis": True
            },
            "log_levels": {
                "application": "DEBUG",
                "litellm": "INFO",
                "openai": "INFO",
                "httpx": "INFO"
            },
            "output_formats": {
                "console_format": "simple",
                "file_format": "standard",
                "timestamp_format": "%H:%M:%S"
            },
            "handlers": {
                "console_enabled": True,
                "file_enabled": False,
                "error_file_enabled": False,
                "console_level": "DEBUG"
            }
        },
        "detail_levels": {
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
            "standard": "%(asctime)s - %(levelname)s - %(message)s"
        }
    }
    
    # Write configuration to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(custom_config, f, indent=2)
        config_file = f.name
    
    try:
        # Create logging manager with custom configuration
        manager = LoggingConfigManager(config_file)
        manager.setup_logging()
        
        logger = logging.getLogger('codexes.example')
        logger.debug("This is a debug message with custom configuration")
        logger.info("This is an info message with custom configuration")
        
        # Get updated statistics configuration
        stats_config = manager.get_statistics_config()
        print(f"Statistics detail level: {stats_config['detail_level']}")
        print(f"Include timing analysis: {stats_config.get('include_timing_analysis', False)}")
        print(f"Include performance metrics: {stats_config.get('include_performance_metrics', False)}")
        
    finally:
        # Clean up temporary file
        os.unlink(config_file)
    
    print()


def example_environment_overrides():
    """Example showing environment-specific configuration overrides."""
    print("=== Example 3: Environment Overrides ===")
    
    # Create configuration with environment overrides
    config_with_overrides = {
        "settings": {
            "statistics_reporting": {
                "enabled": True,
                "detail_level": "standard"
            },
            "log_levels": {
                "application": "INFO"
            },
            "environment_overrides": {
                "development": {
                    "log_levels": {
                        "application": "DEBUG"
                    },
                    "statistics_reporting": {
                        "detail_level": "detailed"
                    }
                },
                "production": {
                    "log_levels": {
                        "application": "WARNING"
                    },
                    "statistics_reporting": {
                        "detail_level": "minimal"
                    }
                }
            }
        },
        "format_templates": {
            "simple": "%(levelname)s - %(message)s",
            "standard": "%(asctime)s - %(levelname)s - %(message)s",
            "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
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
        }
    }
    
    # Write configuration to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_with_overrides, f, indent=2)
        config_file = f.name
    
    try:
        # Test different environments
        for env in ['development', 'production']:
            print(f"--- Environment: {env} ---")
            
            manager = LoggingConfigManager(config_file)
            manager.setup_logging(environment=env)
            
            stats_config = manager.get_statistics_config()
            print(f"Detail level: {stats_config['detail_level']}")
            print(f"Include model breakdown: {stats_config['include_model_breakdown']}")
            print(f"Include timing analysis: {stats_config.get('include_timing_analysis', False)}")
            print()
            
    finally:
        # Clean up temporary file
        os.unlink(config_file)


def example_statistics_reporter_configuration():
    """Example showing StatisticsReporter with different configurations."""
    print("=== Example 4: Statistics Reporter Configuration ===")
    
    # Create mock token usage data
    tracker = TokenUsageTracker()
    
    # Simulate some usage data (normally this would come from actual LLM calls)
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    # Test different detail levels
    detail_levels = ['minimal', 'summary', 'standard', 'detailed']
    
    for detail_level in detail_levels:
        print(f"--- Detail Level: {detail_level} ---")
        
        config = {
            "enabled": True,
            "detail_level": detail_level,
            "include_model_breakdown": detail_level in ['summary', 'standard', 'detailed'],
            "include_prompt_breakdown": detail_level in ['standard', 'detailed'],
            "include_cost_analysis": detail_level in ['summary', 'standard', 'detailed'],
            "include_timing_analysis": detail_level == 'detailed',
            "include_performance_metrics": detail_level == 'detailed'
        }
        
        reporter = StatisticsReporter(config)
        
        # Create a simple mock tracker for demonstration
        mock_tracker = MagicMock()
        mock_tracker.get_total_statistics.return_value = {
            'total_calls': 3,
            'total_tokens': 450,
            'total_input_tokens': 300,
            'total_output_tokens': 150,
            'total_cost': 0.0225,
            'duration_seconds': 5.2,
            'tokens_per_second': 86.5,
            'average_cost_per_call': 0.0075,
            'cost_available_calls': 3
        }
        
        mock_tracker.get_model_breakdown.return_value = {
            'gpt-3.5-turbo': MagicMock(
                call_count=2,
                total_tokens=300,
                total_input_tokens=200,
                total_output_tokens=100,
                total_cost=0.015,
                average_response_time=2.1
            ),
            'gpt-4': MagicMock(
                call_count=1,
                total_tokens=150,
                total_input_tokens=100,
                total_output_tokens=50,
                total_cost=0.0075,
                average_response_time=3.2
            )
        }
        
        mock_tracker.get_prompt_breakdown.return_value = {
            'completion_prompt': MagicMock(
                call_count=2,
                total_tokens=300,
                total_input_tokens=200,
                total_output_tokens=100,
                total_cost=0.015,
                models_used={'gpt-3.5-turbo': 2}
            ),
            'analysis_prompt': MagicMock(
                call_count=1,
                total_tokens=150,
                total_input_tokens=100,
                total_output_tokens=50,
                total_cost=0.0075,
                models_used={'gpt-4': 1}
            )
        }
        
        # Generate report
        reporter.report_pipeline_statistics(mock_tracker)
        print()


def example_dynamic_configuration_updates():
    """Example showing dynamic configuration updates."""
    print("=== Example 5: Dynamic Configuration Updates ===")
    
    # Start with default configuration
    manager = LoggingConfigManager()
    manager.setup_logging()
    
    print("Initial statistics configuration:")
    stats_config = manager.get_statistics_config()
    print(f"  Detail level: {stats_config['detail_level']}")
    print(f"  Include model breakdown: {stats_config['include_model_breakdown']}")
    
    # Update configuration dynamically
    updates = {
        'settings': {
            'statistics_reporting': {
                'detail_level': 'minimal',
                'include_model_breakdown': False,
                'include_prompt_breakdown': False,
                'include_cost_analysis': False
            }
        }
    }
    
    manager.update_config(updates)
    
    print("\nAfter dynamic update:")
    stats_config = manager.get_statistics_config()
    print(f"  Detail level: {stats_config['detail_level']}")
    print(f"  Include model breakdown: {stats_config['include_model_breakdown']}")
    print()


if __name__ == '__main__':
    print("Logging Configuration Examples")
    print("=" * 50)
    print()
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Run examples
    example_default_configuration()
    example_custom_configuration()
    example_environment_overrides()
    example_statistics_reporter_configuration()
    example_dynamic_configuration_updates()
    
    print("Examples completed successfully!")