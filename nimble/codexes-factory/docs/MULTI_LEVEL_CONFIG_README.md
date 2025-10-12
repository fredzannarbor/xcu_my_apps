# Multi-Level Configuration System

This document provides an overview of the multi-level configuration system implemented in the LSI Field Enhancement Phase 4 project.

## Overview

The multi-level configuration system provides a hierarchical approach to managing configuration values with priority-based resolution. This system allows for flexible configuration management across different levels of specificity, from global defaults to book-specific overrides.

## Architecture

### Configuration Levels

The system supports five levels of configuration in priority order (highest to lowest):

1. **Field Overrides** - Highest priority, runtime overrides
2. **Book-Specific** - Configuration for individual books (by ISBN)
3. **Imprint-Specific** - Configuration for publishing imprints
4. **Publisher-Specific** - Configuration for publishers
5. **Global Defaults** - Lowest priority, system-wide defaults

### Priority Resolution

When a configuration value is requested, the system searches through levels in priority order and returns the first value found. This allows for cascading configuration where more specific levels override more general ones.

## Implementation

### Core Classes

#### MultiLevelConfiguration

The main configuration management class:

```python
class MultiLevelConfiguration:
    def __init__(self, config_dir: str = "configs"):
        # Initialize with configuration directory
        
    def get_value(self, key: str, context: ConfigurationContext = None, 
                  default: Any = None) -> Any:
        # Get configuration value with priority resolution
        
    def set_value(self, key: str, value: Any, level: ConfigurationLevel,
                  context: ConfigurationContext = None) -> bool:
        # Set configuration value at specified level
```

#### ConfigurationContext

Provides context for configuration resolution:

```python
@dataclass
class ConfigurationContext:
    book_isbn: Optional[str] = None
    imprint_name: Optional[str] = None
    publisher_name: Optional[str] = None
    field_overrides: Dict[str, Any] = field(default_factory=dict)
```

#### ConfigurationEntry

Represents a configuration value with metadata:

```python
@dataclass
class ConfigurationEntry:
    value: Any
    level: ConfigurationLevel
    source: str = ""
    description: str = ""
    last_modified: str = ""
```

### Configuration Levels Detail

#### 1. Field Overrides (Highest Priority)

Runtime overrides that take precedence over all other configuration sources:

```python
context = ConfigurationContext(
    field_overrides={
        "us_wholesale_discount": "99",
        "special_instructions": "Rush order"
    }
)
```

**Use Cases:**
- Runtime parameter overrides
- User-specific customizations
- Temporary configuration changes
- A/B testing configurations

#### 2. Book-Specific Configuration

Configuration specific to individual books, identified by ISBN:

**File Location:** `configs/books/{isbn}.json`

```json
{
  "title": "Advanced Python Programming",
  "author": "John Smith",
  "isbn13": "9781234567890",
  "us_wholesale_discount": "55",
  "special_instructions": "Handle with care",
  "custom_trim_size": "7x10"
}
```

**Use Cases:**
- Book-specific pricing
- Special handling instructions
- Custom specifications
- One-off overrides

#### 3. Imprint-Specific Configuration

Configuration for publishing imprints (brands within a publisher):

**File Location:** `configs/imprints/{imprint_name}.json`

```json
{
  "imprint": "Tech Books Press",
  "language_code": "eng",
  "binding_type": "paperback",
  "us_wholesale_discount": "45",
  "territorial_rights": "World",
  "default_genre": "Technology"
}
```

**Use Cases:**
- Brand-specific defaults
- Imprint-level pricing
- Genre-specific settings
- Marketing preferences

#### 4. Publisher-Specific Configuration

Configuration for publishers:

**File Location:** `configs/publishers/{publisher_name}.json`

```json
{
  "publisher": "Academic Press Inc.",
  "us_wholesale_discount": "40",
  "uk_wholesale_discount": "35",
  "contact_email": "orders@academicpress.com",
  "lightning_source_account": "LSI123456",
  "default_territorial_rights": "US Only"
}
```

**Use Cases:**
- Publisher-wide defaults
- Account information
- Contact details
- Business rules

#### 5. Global Defaults (Lowest Priority)

System-wide default values:

**File Location:** `configs/default_lsi_config.json`

```json
{
  "language_code": "eng",
  "binding_type": "paperback",
  "interior_color": "BW",
  "carton_pack_quantity": "24",
  "territorial_rights": "World",
  "returnability": "Yes",
  "us_wholesale_discount": "40"
}
```

**Use Cases:**
- System defaults
- Fallback values
- Standard industry settings
- Base configuration

## Features

### Priority-Based Resolution

The system automatically resolves configuration values using priority order:

```python
# Example resolution for "us_wholesale_discount"
# 1. Check field overrides: Not found
# 2. Check book-specific (ISBN: 9781234567890): "55" ← FOUND
# 3. Would check imprint-specific: "50" (not reached)
# 4. Would check publisher-specific: "45" (not reached)
# 5. Would check global default: "40" (not reached)
# Result: "55"
```

### Context-Aware Configuration

Configuration resolution adapts based on provided context:

```python
# Different contexts yield different results
context1 = ConfigurationContext()  # Uses global defaults
context2 = ConfigurationContext(publisher_name="tech_publisher")  # Includes publisher config
context3 = ConfigurationContext(
    publisher_name="tech_publisher",
    imprint_name="ai_books",
    book_isbn="9781234567890"
)  # Full hierarchy
```

### Validation System

Built-in validation ensures configuration integrity:

```python
# Add validation rules
config.add_validation_rule("us_wholesale_discount", 
                          ConfigurationValidator.validate_percentage)

config.add_validation_rule("contact_email", 
                          ConfigurationValidator.validate_email)

# Validation is automatically applied when setting values
success = config.set_value("us_wholesale_discount", "150", level)  # False - invalid percentage
```

### Configuration Introspection

Detailed information about configuration sources and values:

```python
info = config.get_configuration_info("us_wholesale_discount", context)
# Returns:
{
    "key": "us_wholesale_discount",
    "value": "55",
    "level": "book_specific",
    "source": "/path/to/configs/books/9781234567890.json",
    "description": "Book-specific discount rate",
    "last_modified": "2024-03-15T10:30:00",
    "available_levels": [
        {"level": "book_specific", "value": "55", "source": "..."},
        {"level": "imprint_specific", "value": "50", "source": "..."},
        {"level": "publisher_specific", "value": "45", "source": "..."},
        {"level": "global_default", "value": "40", "source": "..."}
    ]
}
```

### File Management

Automatic loading and saving of configuration files:

```python
# Load configuration from file
config.load_configuration_file("custom_config.json", ConfigurationLevel.PUBLISHER_SPECIFIC)

# Save configuration to file
config.save_configuration_file("backup_config.json", ConfigurationLevel.GLOBAL_DEFAULT)
```

## Built-in Validators

The system includes common validation functions:

### Percentage Validator
```python
ConfigurationValidator.validate_percentage("45")    # True
ConfigurationValidator.validate_percentage("150")   # False
ConfigurationValidator.validate_percentage("-10")   # False
```

### Email Validator
```python
ConfigurationValidator.validate_email("user@example.com")  # True
ConfigurationValidator.validate_email("invalid-email")     # False
```

### ISBN Validator
```python
ConfigurationValidator.validate_isbn("9781234567890")  # True
ConfigurationValidator.validate_isbn("invalid-isbn")  # False
```

### Date Format Validator
```python
ConfigurationValidator.validate_date_format("2024-03-15")  # True
ConfigurationValidator.validate_date_format("invalid")     # False
```

### Choice Validator
```python
language_validator = ConfigurationValidator.validate_choice(["eng", "spa", "fre"])
language_validator("eng")  # True
language_validator("xyz")  # False
```

## Usage Examples

### Basic Usage

```python
# Create configuration system
config = MultiLevelConfiguration("configs")

# Get configuration value with context
context = ConfigurationContext(
    publisher_name="tech_publisher",
    imprint_name="ai_books"
)

discount = config.get_value("us_wholesale_discount", context, default="40")
```

### Setting Configuration Values

```python
# Set global default
config.set_value(
    "new_field", 
    "default_value", 
    ConfigurationLevel.GLOBAL_DEFAULT,
    description="New configuration field"
)

# Set publisher-specific value
config.set_value(
    "contact_email",
    "publisher@example.com",
    ConfigurationLevel.PUBLISHER_SPECIFIC,
    context=ConfigurationContext(publisher_name="my_publisher")
)
```

### Using Field Overrides

```python
# Runtime overrides
context = ConfigurationContext(
    publisher_name="tech_publisher",
    field_overrides={
        "us_wholesale_discount": "99",
        "rush_order": "true"
    }
)

# Field overrides take highest priority
discount = config.get_value("us_wholesale_discount", context)  # Returns "99"
```

### Configuration Validation

```python
# Create configuration with validation
config = create_default_multi_level_config("configs")

# Validation is automatically applied
success = config.set_value("us_wholesale_discount", "45", ConfigurationLevel.GLOBAL_DEFAULT)  # True
success = config.set_value("us_wholesale_discount", "150", ConfigurationLevel.GLOBAL_DEFAULT)  # False
```

## Integration with LSI System

The multi-level configuration system integrates with the LSI field mapping system:

```python
# Enhanced field mappings can use multi-level configuration
def create_comprehensive_lsi_registry(config=None, llm_field_completer=None):
    registry = create_enhanced_field_mapping_registry()
    
    if isinstance(config, MultiLevelConfiguration):
        # Use multi-level configuration for enhanced resolution
        context = ConfigurationContext(
            publisher_name=get_current_publisher(),
            imprint_name=get_current_imprint()
        )
        
        # Get configuration values with proper priority resolution
        account_value = config.get_value("lightning_source_account", context)
        discount_value = config.get_value("us_wholesale_discount", context)
        
        # Register strategies with resolved values
        registry.register_strategy("Lightning Source Account", 
                                 DefaultMappingStrategy(account_value))
        registry.register_strategy("US Wholesale Discount", 
                                 DefaultMappingStrategy(discount_value))
    
    return registry
```

## File Structure

The configuration system expects the following directory structure:

```
configs/
├── default_lsi_config.json          # Global defaults
├── publishers/                       # Publisher-specific configs
│   ├── publisher1.json
│   ├── publisher2.json
│   └── ...
├── imprints/                        # Imprint-specific configs
│   ├── imprint1.json
│   ├── imprint2.json
│   └── ...
└── books/                           # Book-specific configs
    ├── 9781234567890.json
    ├── 9789876543210.json
    └── ...
```

## Testing

The multi-level configuration system can be tested using the test script:

```bash
python test_multi_level_config.py
```

This script tests:
- Basic configuration resolution
- Priority-based resolution
- Context-aware configuration
- Validation system
- File operations
- Configuration introspection

## Benefits

### Flexibility
- Supports multiple levels of configuration specificity
- Easy to override values at different levels
- Context-aware resolution

### Maintainability
- Clear separation of configuration concerns
- Centralized validation
- Comprehensive logging and introspection

### Scalability
- Efficient priority-based resolution
- File-based configuration storage
- Extensible validation system

### Reliability
- Built-in validation prevents invalid configurations
- Comprehensive error handling
- Detailed configuration tracking

This multi-level configuration system provides a robust foundation for managing complex configuration requirements in the LSI field enhancement system, ensuring that configuration values are resolved correctly based on context and priority while maintaining data integrity through validation.