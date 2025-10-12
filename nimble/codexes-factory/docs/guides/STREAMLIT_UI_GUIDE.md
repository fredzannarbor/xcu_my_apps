# Streamlit UI Configuration Guide

## Overview

The enhanced Streamlit UI provides comprehensive configuration management for the Codexes Factory book production pipeline. This guide covers all features and functionality of the enhanced interface.

## Key Features

### 1. Multi-Level Configuration Management
- **Publisher Configuration**: Company-level settings and defaults
- **Imprint Configuration**: Brand-level settings that inherit from publisher
- **Tranche Configuration**: Batch-level settings for specific book groups
- **Automatic Inheritance**: Settings cascade from default → publisher → imprint → tranche

### 2. Complete Parameter Inspection
- **Mandatory Preview**: All parameters must be reviewed before pipeline execution
- **Command Line Preview**: See exact command that will be executed
- **Configuration Statistics**: Parameter counts, validation status, and configuration hash
- **Organized View**: Parameters grouped by category with expandable sections

### 3. Display Modes
- **Simple Mode**: Basic settings for quick setup
- **Advanced Mode**: Additional LSI and distribution parameters
- **Expert Mode**: All parameters including debug and advanced features

### 4. Real-Time Validation
- **Parameter Validation**: Real-time validation with specific error messages
- **Dependency Checking**: Automatic validation of parameter dependencies
- **LSI Compliance**: Validation against Lightning Source requirements
- **Suggestion System**: Helpful suggestions for invalid values

## Getting Started

### Accessing the Enhanced UI

1. Start the Streamlit application
2. Navigate to the "Book Pipeline Runner" page
3. The enhanced interface will load automatically

### Basic Workflow

1. **Select Configuration**
   - Choose Publisher, Imprint, and Tranche from dropdowns
   - Click "Load Config" to merge configurations

2. **Choose Display Mode**
   - Select Simple, Advanced, or Expert mode
   - Mode determines which parameters are visible

3. **Configure Parameters**
   - Fill in required parameters (marked with *)
   - Use expandable sections to organize parameters
   - Real-time validation provides immediate feedback

4. **Review Configuration**
   - Complete Configuration Preview shows all parameters
   - Command Line Preview shows exact execution command
   - Validation tab shows any errors or warnings

5. **Execute Pipeline**
   - Click "Run Pipeline" only after validation passes
   - Monitor execution progress in real-time
   - Download generated files when complete

## Configuration Management

### Publisher Configuration

Publisher configurations contain company-level settings:

```json
{
  "_config_info": {
    "description": "Publisher configuration",
    "version": "1.0",
    "config_type": "publisher"
  },
  "publisher": "Company Name",
  "lightning_source_account": "1234567",
  "contact_email": "contact@company.com",
  "default_settings": {
    "language_code": "eng",
    "country_of_origin": "US",
    "territorial_rights": "World"
  },
  "pricing_strategy": {
    "us_wholesale_discount": "40",
    "uk_wholesale_discount": "40"
  }
}
```

### Imprint Configuration

Imprint configurations inherit from publisher and add brand-specific settings:

```json
{
  "_config_info": {
    "description": "Imprint configuration",
    "version": "1.0",
    "config_type": "imprint"
  },
  "imprint": "Brand Name",
  "publisher": "Company Name",
  "branding": {
    "tagline": "Brand tagline",
    "brand_colors": {
      "primary": "#000000",
      "secondary": "#FFFFFF"
    }
  },
  "default_book_settings": {
    "trim_size": "6x9",
    "binding_type": "paperback"
  }
}
```

### Tranche Configuration

Tranche configurations are for specific book batches:

```json
{
  "_config_info": {
    "description": "Tranche configuration",
    "version": "1.0",
    "config_type": "tranche"
  },
  "tranche_info": {
    "tranche_id": "batch-1",
    "book_count": 12,
    "target_month": "July 2025"
  },
  "publisher": "Company Name",
  "imprint": "Brand Name",
  "field_overrides": {
    "series_name": "Special Series"
  },
  "field_exclusions": ["Parent ISBN"]
}
```

## Parameter Groups

### Core Settings
- **Publisher**: Publishing company selection
- **Imprint**: Publishing brand selection  
- **Tranche**: Batch configuration selection
- **Schedule File**: JSON file with book information
- **Primary Model**: Main LLM for content generation
- **Verifier Model**: High-quality model for verification

### Pipeline Control
- **Start Stage**: Pipeline stage to begin from (1-4)
- **End Stage**: Pipeline stage to end at (1-4)
- **Max Books**: Maximum number of books to process
- **Book Range**: Specific book numbers to process
- **Prompt Selection**: Specific prompts to run

### LSI Configuration
- **Lightning Source Account**: Your LSI account number
- **Rendition Book Type**: Book binding specification
- **Submission Methods**: How files are submitted to LSI
- **Territorial Rights**: Geographic distribution rights
- **Returnability**: Return policy for unsold books

### Physical Specifications
- **Trim Size**: Book dimensions (e.g., 6x9)
- **Page Count**: Total number of pages
- **Binding Type**: paperback, hardcover, etc.
- **Interior Color**: Black & White or Color
- **Interior Paper**: White or Cream
- **Cover Type**: Matte or Gloss finish

### Territorial Pricing
- **US Wholesale Discount**: Discount percentage for US market
- **UK Wholesale Discount**: Discount percentage for UK market
- **EU Wholesale Discount**: Discount percentage for EU market
- **Canada/Australia**: Additional market discounts

### Metadata Defaults
- **Language Code**: ISO language code (eng, spa, etc.)
- **Country of Origin**: Publishing country
- **Audience**: Target audience (General Adult, etc.)
- **BISAC Category**: Subject classification
- **Edition Information**: Edition number and description
- **Series Information**: Series name if applicable
- **Contributor Roles**: Author, Editor, etc.

### LLM & AI Configuration
- **Model Parameters**: Advanced model settings
- **Retry Configuration**: Retry attempts and delays
- **Field Completion**: AI-powered metadata completion
- **ISBN Assignment**: Automatic ISBN assignment
- **Monitoring**: LLM usage tracking

### Debug & Monitoring
- **Logging Levels**: Verbose, Terse, or Normal
- **Prompt Logs**: Show LLM prompts and responses
- **Debug Modes**: Additional debugging information
- **Performance Monitoring**: Execution metrics

### Advanced Configuration
- **File Management**: Custom file paths and directories
- **Report Formats**: Output report types
- **Catalog Settings**: Storefront catalog options
- **Build Options**: Temporary file handling

## Validation System

### Real-Time Validation
- Parameters are validated as you type
- Invalid values are highlighted in red
- Suggestions appear for common mistakes
- Dependencies are checked automatically

### Validation Types
- **Required Fields**: Must be filled in
- **Format Validation**: Correct data format
- **Range Validation**: Values within acceptable ranges
- **Dependency Validation**: Related parameters are consistent
- **LSI Compliance**: Meets Lightning Source requirements

### Error Messages
- **Specific Errors**: Exact problem description
- **Suggested Values**: List of valid options
- **Help Text**: Explanation of parameter purpose
- **Documentation Links**: Additional information

## Configuration Preview

### Mandatory Preview Section
Before pipeline execution, you must review:

1. **Configuration Statistics**
   - Total parameter count
   - Configured parameter count
   - Configuration hash for verification
   - Validation status

2. **Organized View**
   - Parameters grouped by category
   - Only non-empty parameters shown
   - Clear parameter names and values

3. **JSON View**
   - Complete configuration in JSON format
   - Useful for debugging and export

4. **Command Preview**
   - Exact command line that will be executed
   - All parameters and flags shown
   - Parameter count summary

5. **Validation Results**
   - Overall validation status
   - Detailed error and warning lists
   - Parameter status grid

## File Management

### Configuration Files
- **Upload**: Upload existing configuration files
- **Download**: Export current configuration
- **Templates**: Download configuration templates
- **Validation**: Validate configuration structure

### Schedule Files
- **Select Existing**: Choose from available schedule files
- **Upload Custom**: Upload your own schedule file
- **Format**: JSON format with book information

### Output Files
- **Interior PDFs**: Generated book interiors
- **Cover PDFs**: Generated book covers
- **LSI CSV Files**: Distribution metadata
- **Reports**: Validation and processing reports

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   - Check file permissions in configs/ directory
   - Verify JSON syntax in configuration files
   - Ensure required fields are present

2. **Validation Errors**
   - Review error messages carefully
   - Check parameter dependencies
   - Verify values against valid options

3. **Pipeline Execution Fails**
   - Ensure all required parameters are set
   - Check file paths and permissions
   - Review execution logs for details

4. **Missing Parameters**
   - Switch to Expert display mode
   - Check configuration inheritance
   - Verify parameter group visibility

### Getting Help

1. **Parameter Help Text**
   - Hover over parameter labels for help
   - Click help icons for detailed information

2. **Validation Messages**
   - Read error messages carefully
   - Use suggested values when provided

3. **Documentation**
   - Refer to this guide for detailed information
   - Check API documentation for technical details

4. **Configuration Examples**
   - Use provided templates as starting points
   - Study existing configurations for patterns

## Best Practices

### Configuration Management
- Use descriptive names for configurations
- Keep configurations organized by type
- Validate configurations before saving
- Back up important configurations

### Parameter Setting
- Start with Simple mode for basic setup
- Use Advanced mode for distribution settings
- Use Expert mode for debugging and advanced features
- Always review the complete configuration preview

### Pipeline Execution
- Validate configuration before running
- Monitor execution progress
- Save execution logs for troubleshooting
- Download generated files promptly

### File Organization
- Keep schedule files in consistent locations
- Use clear naming conventions
- Organize output files by project/batch
- Clean up temporary files regularly

## Advanced Features

### Configuration Inheritance
Understanding how settings cascade:
1. System defaults (built-in)
2. Publisher configuration
3. Imprint configuration  
4. Tranche configuration
5. UI form values (highest priority)

### Batch Processing
- Configure multiple books at once
- Use tranche configurations for consistency
- Monitor progress across all books
- Generate batch reports

### Custom Validation Rules
- Add custom validation logic
- Define parameter dependencies
- Create business rule validation
- Implement compliance checking

### Integration with External Systems
- Export configurations for external use
- Import configurations from other systems
- API integration for automated workflows
- Webhook support for notifications

## API Reference

### Configuration Manager
```python
from codexes.modules.ui.configuration_manager import EnhancedConfigurationManager

manager = EnhancedConfigurationManager()
configs = manager.load_available_configs()
merged = manager.merge_configurations(publisher, imprint, tranche)
validation = manager.validate_configuration(config)
```

### Parameter Groups
```python
from codexes.modules.ui.parameter_groups import ParameterGroupManager

param_manager = ParameterGroupManager()
groups = param_manager.get_parameter_groups()
param = param_manager.get_parameter_by_name('publisher')
```

### Command Builder
```python
from codexes.modules.ui.command_builder import CommandBuilder

builder = CommandBuilder()
command = builder.build_pipeline_command(config)
validation = builder.validate_command_parameters(command)
```

## Conclusion

The enhanced Streamlit UI provides comprehensive configuration management with complete parameter inspection, real-time validation, and seamless pipeline integration. By following this guide, you can effectively manage complex book production workflows with confidence and precision.