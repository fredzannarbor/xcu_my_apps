# LSI Configuration System Documentation

## Overview

The LSI Configuration System provides hierarchical configuration management for Lightning Source Inc. (LSI) ACS file generation. It supports multiple publishers, imprints, and territorial configurations with a clear precedence hierarchy.

## Configuration Structure

```
configs/
├── default_lsi_config.json     # Global defaults and base configuration
├── publishers/                 # Publisher-specific configurations
│   └── nimble_books.json      # Example publisher config
├── imprints/                  # Imprint-specific configurations
│   └── xynapse_traces.json    # Example imprint config
└── docs/readme/codexes_factory_ai_assisted_publishing_platform_v32.md                  # This documentation
```

## Configuration Precedence

The system uses the following precedence order (highest to lowest):

1. **Field Overrides** (global) - Highest priority
2. **Imprint-specific Field Overrides**
3. **Territorial Configuration Values**
4. **Imprint Default Values**
5. **Global Default Values** - Lowest priority

## Configuration File Format

All configuration files use JSON format with the following structure:

### Global Configuration (`default_lsi_config.json`)

```json
{
  "defaults": {
    "publisher": "Publisher Name",
    "imprint": "Default Imprint",
    "lightning_source_account": "account_number",
    "cover_submission_method": "FTP",
    "text_block_submission_method": "FTP",
    "rendition_booktype": "Perfect Bound",
    "carton_pack_quantity": "1",
    "territorial_rights": "World",
    "returnability": "Yes-Destroy",
    "order_type_eligibility": "POD"
  },
  "field_overrides": {
    "field_name": "override_value"
  },
  "territorial_configs": {
    "US": {
      "wholesale_discount_percent": "40",
      "returnability": "Yes-Destroy",
      "currency": "USD",
      "pricing_multiplier": 1.0
    }
  }
}
```

### Publisher Configuration (`publishers/*.json`)

```json
{
  "publisher_name": "Publisher Name",
  "defaults": {
    "publisher": "Publisher Name",
    "lightning_source_account": "account_number"
  },
  "territorial_configs": {
    "US": {
      "wholesale_discount_percent": "40",
      "returnability": "Yes-Destroy",
      "currency": "USD",
      "pricing_multiplier": 1.0,
      "additional_fields": {
        "us_wholesale_discount": "40"
      }
    }
  }
}
```

### Imprint Configuration (`imprints/*.json`)

```json
{
  "imprint_name": "Imprint Name",
  "publisher": "Publisher Name",
  "defaults": {
    "imprint": "Imprint Name",
    "lsi_special_category": "Category"
  },
  "field_overrides": {
    "lsi_flexfield1": "Custom Value"
  },
  "territorial_configs": {
    "US": {
      "wholesale_discount_percent": "45",
      "returnability": "Yes-Destroy",
      "currency": "USD",
      "pricing_multiplier": 1.0
    }
  }
}
```

## Supported LSI Fields

### Core Fields
- `publisher` - Publisher name
- `imprint` - Imprint name
- `lightning_source_account` - LSI account number
- `cover_submission_method` - FTP, Email, or Portal
- `text_block_submission_method` - FTP, Email, or Portal
- `rendition_booktype` - Perfect Bound, Hardcover, etc.

### Physical Specifications
- `carton_pack_quantity` - Books per carton
- `weight_lbs` - Book weight in pounds
- `territorial_rights` - Distribution rights (World, US, etc.)

### Pricing and Distribution
- `wholesale_discount_percent` - Wholesale discount percentage
- `returnability` - Yes-Destroy, Yes-Return, No
- `order_type_eligibility` - POD, Stock, Both

### Special LSI Fields
- `lsi_special_category` - Special category designation
- `stamped_text_left` - Left stamped text
- `stamped_text_center` - Center stamped text
- `stamped_text_right` - Right stamped text
- `lsi_flexfield1` through `lsi_flexfield5` - Flexible fields

### Edition Information
- `edition_number` - Edition number
- `edition_description` - Edition description

## Territorial Configurations

The system supports territorial-specific configurations for different markets:

### Supported Territories
- **US** - United States (USD)
- **UK** - United Kingdom (GBP)
- **EU** - European Union (EUR)
- **CA** - Canada (CAD)
- **AU** - Australia (AUD)

### Territorial Fields
- `wholesale_discount_percent` - Territory-specific discount
- `returnability` - Territory-specific return policy
- `currency` - Territory currency code
- `pricing_multiplier` - Currency conversion multiplier
- `additional_fields` - Territory-specific custom fields

## Usage Examples

### Basic Configuration Loading

```python
from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration

# Load default configuration
config = LSIConfiguration()

# Load specific configuration file
config = LSIConfiguration(config_path="configs/custom_config.json")

# Load from specific directory
config = LSIConfiguration(config_dir="custom_configs")
```

### Getting Field Values

```python
# Get default value
default_publisher = config.get_default_value("publisher")

# Get field with imprint context
imprint_value = config.get_field_value("lsi_special_category", imprint="Xynapse Traces")

# Get field with territorial context
territorial_discount = config.get_field_value(
    "wholesale_discount_percent", 
    imprint="Xynapse Traces", 
    territory="UK"
)
```

### Configuration Validation

```python
# Validate configuration
warnings = config.validate_configuration()
for warning in warnings:
    print(f"Warning: {warning}")
```

## Best Practices

### 1. Configuration Organization
- Use separate files for different publishers and imprints
- Keep territorial configurations consistent across imprints
- Document custom field meanings in comments

### 2. Field Naming
- Use consistent field names across configurations
- Follow LSI field naming conventions
- Use descriptive names for flex fields

### 3. Default Values
- Provide sensible defaults for all common fields
- Use empty strings for optional fields
- Set appropriate territorial multipliers

### 4. Validation
- Regularly validate configurations
- Test with sample metadata
- Verify LSI compliance

## Troubleshooting

### Common Issues

1. **Missing Configuration Files**
   - Ensure all referenced files exist
   - Check file permissions
   - Verify JSON syntax

2. **Invalid JSON**
   - Use JSON validators
   - Check for trailing commas
   - Verify quote marks

3. **Missing Required Fields**
   - Check validation warnings
   - Ensure publisher and account information
   - Verify territorial configurations

### Error Messages

- `Configuration file not found` - Check file path
- `Invalid JSON` - Validate JSON syntax
- `Missing default value for required field` - Add to defaults section

## Migration Guide

### From Legacy Configuration

1. Export existing configuration values
2. Create new JSON structure
3. Map old field names to new format
4. Test with sample data
5. Validate configuration

### Adding New Territories

1. Add to `territorial_configs` section
2. Include required fields:
   - `wholesale_discount_percent`
   - `returnability`
   - `currency`
   - `pricing_multiplier`
3. Test with sample metadata
4. Update documentation