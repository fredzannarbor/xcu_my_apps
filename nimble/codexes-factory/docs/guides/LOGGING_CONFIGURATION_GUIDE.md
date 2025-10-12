# Logging Configuration Guide

This guide explains how to use the new logging configuration system in Codexes Factory.

## Overview

The logging configuration system provides:

- **File-based configuration**: Configure logging behavior through JSON files
- **Environment-specific overrides**: Different settings for development, production, and testing
- **LiteLLM filtering control**: Enable/disable filtering of verbose LiteLLM messages
- **Statistics reporting configuration**: Control the detail level and content of pipeline statistics
- **Dynamic configuration updates**: Change settings at runtime
- **Multiple output formats**: Support for different log formats and destinations
- **Success message guarantee**: Messages with ✅ or 📊 icons ALWAYS appear regardless of logging level

## Configuration File Structure

The main configuration file is located at `configs/logging_config.json`. Here's the structure:

```json
{
  "version": 1,
  "settings": {
    "litellm_filtering": {
      "enabled": true,
      "debug_mode_override": false
    },
    "statistics_reporting": {
      "enabled": true,
      "detail_level": "standard",
      "include_model_breakdown": true,
      "include_prompt_breakdown": true,
      "include_cost_analysis": true
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
      "console_enabled": true,
      "file_enabled": true,
      "error_file_enabled": true,
      "console_level": "INFO",
      "file_level": "DEBUG",
      "error_file_level": "ERROR"
    },
    "files": {
      "application_log": "logs/application.log",
      "error_log": "logs/errors.log",
      "statistics_log": "logs/statistics.log",
      "encoding": "utf-8"
    },
    "environment_overrides": {
      "development": {
        "log_levels": {
          "application": "DEBUG"
        }
      },
      "production": {
        "log_levels": {
          "application": "WARNING"
        }
      }
    }
  },
  "detail_levels": {
    "minimal": {
      "include_model_breakdown": false,
      "include_prompt_breakdown": false,
      "include_cost_analysis": false
    },
    "standard": {
      "include_model_breakdown": true,
      "include_prompt_breakdown": true,
      "include_cost_analysis": true
    },
    "detailed": {
      "include_model_breakdown": true,
      "include_prompt_breakdown": true,
      "include_cost_analysis": true,
      "include_timing_analysis": true,
      "include_performance_metrics": true
    }
  },
  "format_templates": {
    "simple": "%(levelname)s - %(message)s",
    "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
  }
}
```

## Basic Usage

### Setting up logging with default configuration

```python
from src.codexes.core.logging_config import setup_application_logging

# Use default configuration
setup_application_logging()
```

### Using a custom configuration file

```python
from src.codexes.core.logging_config import setup_application_logging

# Use custom configuration file
setup_application_logging(config_file='path/to/custom_config.json')
```

### Environment-specific configuration

```python
from src.codexes.core.logging_config import setup_application_logging

# Apply environment-specific overrides
setup_application_logging(environment='production')
```

## Configuration Options

### LiteLLM Filtering

Controls whether verbose LiteLLM messages are filtered out:

```json
"litellm_filtering": {
  "enabled": true,           // Enable/disable filtering
  "debug_mode_override": false  // Show LiteLLM messages in debug mode
}
```

### Statistics Reporting

Controls the behavior of pipeline statistics reporting:

```json
"statistics_reporting": {
  "enabled": true,                    // Enable/disable statistics reporting
  "detail_level": "standard",         // Level of detail: minimal, summary, standard, detailed
  "include_model_breakdown": true,    // Show per-model statistics
  "include_prompt_breakdown": true,   // Show per-prompt statistics
  "include_cost_analysis": true       // Show cost analysis
}
```

#### Detail Levels

- **minimal**: Basic statistics only (calls, tokens, cost)
- **summary**: Basic statistics plus model breakdown
- **standard**: Summary plus prompt breakdown and cost analysis
- **detailed**: Standard plus timing analysis and performance metrics

### Log Levels

Set logging levels for different components:

```json
"log_levels": {
  "application": "INFO",    // Your application logs
  "litellm": "WARNING",     // LiteLLM library logs
  "openai": "WARNING",      // OpenAI client logs
  "httpx": "WARNING"        // HTTP client logs
}
```

### Output Formats

Configure how log messages are formatted:

```json
"output_formats": {
  "console_format": "standard",           // Format for console output
  "file_format": "detailed",              // Format for file output
  "timestamp_format": "%Y-%m-%d %H:%M:%S" // Timestamp format
}
```

Available formats:
- **simple**: `%(levelname)s - %(message)s`
- **standard**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **detailed**: `%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s`

### Handlers

Control which log handlers are enabled:

```json
"handlers": {
  "console_enabled": true,      // Enable console output
  "file_enabled": true,         // Enable file output
  "error_file_enabled": true,   // Enable separate error file
  "console_level": "INFO",      // Minimum level for console
  "file_level": "DEBUG",        // Minimum level for file
  "error_file_level": "ERROR"   // Minimum level for error file
}
```

### File Paths

Configure where log files are written:

```json
"files": {
  "application_log": "logs/application.log",
  "error_log": "logs/errors.log",
  "statistics_log": "logs/statistics.log",
  "encoding": "utf-8"
}
```

## Environment Overrides

You can specify different settings for different environments:

```json
"environment_overrides": {
  "development": {
    "log_levels": {
      "application": "DEBUG"
    },
    "litellm_filtering": {
      "debug_mode_override": true
    }
  },
  "production": {
    "log_levels": {
      "application": "WARNING"
    },
    "handlers": {
      "console_level": "ERROR"
    }
  },
  "testing": {
    "handlers": {
      "console_level": "ERROR",
      "file_enabled": false
    },
    "statistics_reporting": {
      "enabled": false
    }
  }
}
```

## Advanced Usage

### Dynamic Configuration Updates

```python
from src.codexes.core.logging_config import get_logging_manager

manager = get_logging_manager()

# Update configuration at runtime
updates = {
    'settings': {
        'statistics_reporting': {
            'detail_level': 'detailed'
        }
    }
}

manager.update_config(updates)
```

### Getting Configuration Values

```python
from src.codexes.core.logging_config import (
    get_statistics_config,
    get_litellm_filter_config
)

# Get statistics configuration
stats_config = get_statistics_config()
print(f"Detail level: {stats_config['detail_level']}")

# Get filter configuration
filter_config = get_litellm_filter_config()
print(f"Filtering enabled: {filter_config['enabled']}")
```

### Using StatisticsReporter with Configuration

```python
from src.codexes.core.statistics_reporter import StatisticsReporter

# Reporter will automatically use configuration from logging config
reporter = StatisticsReporter()

# Or provide explicit configuration
custom_config = {
    "enabled": True,
    "detail_level": "minimal",
    "include_model_breakdown": False
}
reporter = StatisticsReporter(custom_config)
```

### Saving Configuration

```python
from src.codexes.core.logging_config import get_logging_manager

manager = get_logging_manager()

# Modify configuration
manager._config_data['settings']['statistics_reporting']['detail_level'] = 'detailed'

# Save to file
manager.save_config('configs/updated_logging_config.json')
```

## Environment Variables

The system respects these environment variables:

- `ENVIRONMENT`: Sets the environment for overrides (development, production, testing)
- `DEBUG`: When set to 'true', enables debug mode

## Integration with Existing Code

The configuration system is designed to be backward compatible. Existing code will continue to work with default settings, and you can gradually adopt the new configuration options.

### Pipeline Integration

The logging configuration is automatically applied when you use:

```python
from src.codexes.core.logging_config import setup_application_logging

# Set up logging at the start of your pipeline
setup_application_logging()

# Your existing pipeline code continues to work unchanged
```

### Statistics Integration

The StatisticsReporter automatically uses the configuration:

```python
from src.codexes.core.statistics_reporter import StatisticsReporter
from src.codexes.core.token_usage_tracker import TokenUsageTracker

# Create tracker and reporter
tracker = TokenUsageTracker()
reporter = StatisticsReporter()  # Uses configuration automatically

# At the end of your pipeline
reporter.report_pipeline_statistics(tracker)
```

## Troubleshooting

### Configuration File Not Found

If the configuration file is not found, the system falls back to default settings and logs a warning.

### Invalid Configuration

If the configuration file contains invalid JSON or missing required fields, the system falls back to defaults and logs an error.

### Missing Format Templates

Make sure all format names referenced in handlers are defined in the `format_templates` section.

### Permission Issues

Ensure the application has write permissions to the log directory specified in the configuration.

## Success Message Guarantee

The system ensures that important success and statistics messages always appear in output, regardless of the configured logging levels. This is achieved through:

### Automatic Success Message Detection

Messages containing these icons are automatically treated as critical and will always appear:
- ✅ (Success icon)
- 📊 (Statistics icon)

### Using the log_success Function

For custom code, you can use the `log_success` function to ensure messages always appear:

```python
from src.codexes.core.logging_filters import log_success

logger = logging.getLogger('my_module')
logger.setLevel(logging.ERROR)  # High level that would block INFO

# This message will appear despite the high logger level
log_success(logger, "Operation completed successfully ✅", logging.INFO)
```

### StatisticsReporter Integration

The StatisticsReporter automatically uses `log_success` for all statistics headers, ensuring that pipeline statistics are always visible even in production environments with high logging levels.

## Examples

See `examples/logging_configuration_example.py` for complete working examples of all configuration features.

See `examples/success_message_example.py` for a demonstration of success message guarantee functionality.