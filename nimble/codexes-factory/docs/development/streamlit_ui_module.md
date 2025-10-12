# Streamlit UI Module

This module provides enhanced Streamlit UI components for the Codexes Factory book production pipeline.

## Components

### Core Components
- `configuration_manager.py` - Central configuration management with multi-level inheritance
- `dynamic_config_loader.py` - Dynamic discovery and loading of configuration files
- `parameter_groups.py` - Parameter organization and metadata management
- `config_validator.py` - Real-time configuration validation framework
- `command_builder.py` - Command-line argument generation and serialization
- `streamlit_components.py` - Streamlit UI widgets and components

### Features

#### Multi-Level Configuration
- Publisher → Imprint → Tranche inheritance hierarchy
- Automatic configuration merging and validation
- Dynamic configuration discovery from file system

#### Complete Parameter Inspection
- Mandatory configuration preview before execution
- Command-line preview showing exact parameters
- Real-time validation with specific error messages
- Parameter dependency checking

#### Display Modes
- **Simple**: Basic parameters for quick setup
- **Advanced**: Additional LSI and distribution settings
- **Expert**: All parameters including debug options

#### Enhanced User Experience
- Expandable parameter groups for organization
- Real-time validation feedback
- Configuration export/import functionality
- Comprehensive help system and documentation

## Usage

### Basic Usage
```python
from codexes.modules.ui.streamlit_components import ConfigurationUI

# Initialize UI components
config_ui = ConfigurationUI()

# Render configuration selector
publisher, imprint, tranche = config_ui.render_configuration_selector()

# Render parameter groups
display_mode = config_ui.render_display_mode_selector()
parameter_groups = param_manager.get_parameters_for_display_mode(display_mode)

# Render complete configuration preview
config_ui.render_complete_configuration_preview(config_data)
```

### Configuration Management
```python
from codexes.modules.ui.configuration_manager import EnhancedConfigurationManager

# Initialize manager
manager = EnhancedConfigurationManager()

# Load available configurations
configs = manager.load_available_configs()

# Merge configurations with inheritance
merged_config = manager.merge_configurations(publisher, imprint, tranche)

# Validate configuration
validation_result = manager.validate_configuration(merged_config)
```

### Command Building
```python
from codexes.modules.ui.command_builder import CommandBuilder

# Initialize builder
builder = CommandBuilder()

# Build pipeline command
command = builder.build_pipeline_command(config_data)

# Validate command parameters
validation = builder.validate_command_parameters(command)

# Generate audit log
audit_path = builder.generate_command_audit_log(command, config_data)
```

## Integration

### Streamlit Pages
The UI components are integrated into Streamlit pages:

- `src/codexes/pages/10_Book_Pipeline.py` - Enhanced book pipeline interface
- `src/codexes/pages/Configuration_Management.py` - Configuration file management

### Configuration Files
The system works with configuration files in:

- `configs/publishers/` - Publisher-level configurations
- `configs/imprints/` - Imprint-level configurations  
- `configs/tranches/` - Tranche-level configurations

### Pipeline Integration
The enhanced UI integrates seamlessly with the existing pipeline:

- Generates proper command-line arguments for `run_book_pipeline.py`
- Handles file uploads and temporary file management
- Provides real-time execution monitoring
- Generates comprehensive audit logs

## Testing

Run tests with:
```bash
pytest tests/test_ui_components.py -v
```

Tests cover:
- Configuration management functionality
- Parameter validation and dependency checking
- Command building and serialization
- UI component integration

## Documentation

- `docs/STREAMLIT_UI_GUIDE.md` - Comprehensive user guide
- Inline help text for all parameters
- Configuration templates and examples
- Troubleshooting and best practices

## Requirements

Additional Python packages required:
- `jsonschema>=4.0.0` - JSON schema validation
- `streamlit>=1.28.0` - Web UI framework
- `pandas>=1.5.0` - Data manipulation
- `pathlib2>=2.3.0` - Path handling utilities

Install with:
```bash
pip install -r requirements_ui.txt
```