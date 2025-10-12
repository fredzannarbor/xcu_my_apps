# LSI Field Enhancement System - Migration Guide

## Overview

This guide helps users migrate from the basic LSI ACS Generator to the enhanced LSI Field Enhancement System. The new system provides comprehensive field mapping, validation, configuration management, and LLM-powered field completion while maintaining backward compatibility.

## Table of Contents

1. [What's New](#whats-new)
2. [Backward Compatibility](#backward-compatibility)
3. [Migration Steps](#migration-steps)
4. [Configuration Migration](#configuration-migration)
5. [Code Updates](#code-updates)
6. [Testing Migration](#testing-migration)
7. [Troubleshooting](#troubleshooting)

## What's New

### Enhanced Features

#### 1. Comprehensive Field Mapping
- **Before**: Limited field mapping (~30 fields)
- **After**: Complete mapping for 100+ LSI fields
- **Benefit**: Full LSI template support without manual editing

#### 2. Intelligent Field Completion
- **Before**: Empty fields left blank
- **After**: LLM-powered intelligent completion
- **Benefit**: Reduced manual data entry and improved metadata quality

#### 3. Advanced Validation
- **Before**: Basic validation
- **After**: Multi-level validation with error recovery
- **Benefit**: Higher submission success rates

#### 4. Configuration Management
- **Before**: Hardcoded values
- **After**: Hierarchical configuration system
- **Benefit**: Support for multiple publishers and imprints

#### 5. Comprehensive Logging
- **Before**: Basic logging
- **After**: Detailed performance and field-level logging
- **Benefit**: Better troubleshooting and monitoring

### New Components

```
Enhanced LSI System
├── Field Mapping Registry (NEW)
├── LLM Field Completer (NEW)
├── Configuration Management (NEW)
├── Validation Pipeline (ENHANCED)
├── Logging Manager (NEW)
└── Generation Reporter (NEW)
```

## Backward Compatibility

### Existing Code Compatibility

The enhanced system maintains backward compatibility with existing code:

```python
# OLD CODE - Still works
from src.codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator

generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
generator.generate(metadata, "output.csv")
```

```python
# NEW CODE - Enhanced features
from src.codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator

generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/my_config.json",  # NEW: Configuration support
    log_directory="logs/lsi_generation"    # NEW: Enhanced logging
)

# OLD method still works
generator.generate(metadata, "output.csv")

# NEW method with validation and reporting
result = generator.generate_with_validation(metadata, "output.csv")
```

### Metadata Model Compatibility

Existing CodexMetadata objects work without changes:

```python
# Existing metadata objects work as-is
metadata = CodexMetadata(
    title="My Book",
    author="Author Name",
    isbn13="9781234567890",
    publisher="My Publisher"
)

# Enhanced system automatically handles missing fields
result = generator.generate_with_validation(metadata, "output.csv")
```

## Migration Steps

### Step 1: Update Dependencies

Ensure you have the latest version with enhanced features:

```bash
# Update the package
pip install --upgrade codexes

# Or if using local development
pip install -e .
```

### Step 2: Create Configuration Files

Create configuration files for your publishing setup:

```bash
# Create configuration directory structure
mkdir -p configs/publishers
mkdir -p configs/imprints
mkdir -p configs/examples
```

**Basic Configuration** (`configs/my_lsi_config.json`):
```json
{
  "defaults": {
    "publisher": "Your Publisher Name",
    "lightning_source_account": "YOUR_ACCOUNT_NUMBER",
    "cover_submission_method": "FTP",
    "text_block_submission_method": "FTP",
    "rendition_booktype": "Perfect Bound",
    "us_wholesale_discount": "40",
    "returnability": "Yes-Destroy"
  },
  "field_overrides": {
    "metadata_contact_dictionary": "Editorial Department"
  },
  "territorial_configs": {
    "US": {
      "wholesale_discount_percent": "40",
      "returnability": "Yes-Destroy",
      "currency": "USD",
      "pricing_multiplier": 1.0
    },
    "UK": {
      "wholesale_discount_percent": "40",
      "returnability": "Yes-Destroy",
      "currency": "GBP",
      "pricing_multiplier": 0.79
    }
  }
}
```

### Step 3: Update Initialization Code

Update your generator initialization:

```python
# OLD INITIALIZATION
generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")

# NEW INITIALIZATION (recommended)
generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/my_lsi_config.json",
    log_directory="logs/lsi_generation"
)
```

### Step 4: Update Generation Calls

Migrate to the enhanced generation method:

```python
# OLD METHOD (still works)
generator.generate(metadata, "output.csv")

# NEW METHOD (recommended)
result = generator.generate_with_validation(metadata, "output.csv")

# Check results
if result.success:
    print(f"Generated successfully: {result.populated_fields_count} fields populated")
else:
    print("Generation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Step 5: Add LLM Field Completion (Optional)

Enhance your metadata with LLM completion:

```python
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter

# Initialize completer
completer = LLMFieldCompleter()

# Enhance metadata before generation
enhanced_metadata = completer.complete_missing_fields(metadata)

# Generate with enhanced metadata
result = generator.generate_with_validation(enhanced_metadata, "output.csv")
```

## Configuration Migration

### Migrating Hardcoded Values

If you have hardcoded values in your current implementation, migrate them to configuration:

**Before** (hardcoded in code):
```python
def custom_field_mapping(metadata):
    return {
        'Publisher': 'My Publisher LLC',
        'Lightning Source Account #': '1234567',
        'Cover/Jacket Submission Method': 'FTP',
        'US Wholesale Discount': '45%'
    }
```

**After** (configuration-driven):
```json
{
  "defaults": {
    "publisher": "My Publisher LLC",
    "lightning_source_account": "1234567",
    "cover_submission_method": "FTP",
    "us_wholesale_discount": "45"
  }
}
```

### Publisher-Specific Configurations

Migrate publisher-specific logic to configuration files:

**Before** (code-based logic):
```python
def get_discount_rate(publisher):
    if publisher == "Academic Press":
        return "20%"
    elif publisher == "Fiction House":
        return "45%"
    else:
        return "40%"
```

**After** (configuration-based):

`configs/publishers/academic_press.json`:
```json
{
  "defaults": {
    "publisher": "Academic Press",
    "us_wholesale_discount": "20",
    "returnability": "Yes-Return"
  }
}
```

`configs/publishers/fiction_house.json`:
```json
{
  "defaults": {
    "publisher": "Fiction House",
    "us_wholesale_discount": "45",
    "returnability": "Yes-Destroy"
  }
}
```

## Code Updates

### Update Import Statements

No changes needed for basic imports, but new features require additional imports:

```python
# Basic imports (unchanged)
from src.codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from src.codexes.modules.metadata.metadata_models import CodexMetadata

# New feature imports
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration
from src.codexes.modules.distribution.field_mapping import (
    FieldMappingRegistry, DirectMappingStrategy, ComputedMappingStrategy
)
```

### Update Error Handling

Enhance error handling with new validation features:

```python
# OLD ERROR HANDLING
try:
    generator.generate(metadata, output_path)
    print("Generation successful")
except Exception as e:
    print(f"Generation failed: {e}")

# NEW ERROR HANDLING (recommended)
try:
    result = generator.generate_with_validation(metadata, output_path)
    
    if result.success:
        print(f"Generation successful: {result.populated_fields_count} fields populated")
        
        # Check for warnings
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
    else:
        print("Generation failed:")
        for error in result.errors:
            print(f"  - {error}")
        
        # Attempt automatic fixes if validation failed
        if result.validation_result and not result.validation_result.is_valid:
            print("Attempting automatic fixes...")
            fixed_metadata = apply_suggested_fixes(metadata, result.validation_result)
            retry_result = generator.generate_with_validation(fixed_metadata, output_path)
            
except Exception as e:
    print(f"Critical error: {e}")
```

### Update Batch Processing

Enhance batch processing with new features:

```python
# OLD BATCH PROCESSING
def process_books(metadata_list, output_dir):
    generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
    
    for i, metadata in enumerate(metadata_list):
        output_path = f"{output_dir}/book_{i+1}.csv"
        try:
            generator.generate(metadata, output_path)
            print(f"Processed book {i+1}")
        except Exception as e:
            print(f"Failed to process book {i+1}: {e}")

# NEW BATCH PROCESSING (recommended)
def process_books_enhanced(metadata_list, output_dir):
    generator = LsiAcsGenerator(
        template_path="templates/LSI_ACS_header.csv",
        config_path="configs/batch_config.json",
        log_directory="logs/batch_processing"
    )
    
    completer = LLMFieldCompleter()
    
    results = []
    
    for i, metadata in enumerate(metadata_list):
        try:
            # Enhance metadata
            enhanced_metadata = completer.complete_missing_fields(metadata)
            
            # Generate with validation
            output_path = f"{output_dir}/book_{i+1:04d}.csv"
            result = generator.generate_with_validation(enhanced_metadata, output_path)
            
            results.append(result)
            
            if result.success:
                print(f"✅ Book {i+1}: {metadata.title}")
            else:
                print(f"❌ Book {i+1}: {len(result.errors)} errors")
                
        except Exception as e:
            print(f"❌ Book {i+1}: Critical error - {e}")
            results.append(None)
    
    # Summary
    successful = sum(1 for r in results if r and r.success)
    print(f"\nBatch complete: {successful}/{len(metadata_list)} successful")
    
    return results
```

## Testing Migration

### Validation Testing

Test your migration with validation:

```python
def test_migration():
    """Test migration from old to new system."""
    
    # Test data
    test_metadata = CodexMetadata(
        title="Migration Test Book",
        author="Test Author",
        isbn13="9781234567890",
        publisher="Test Publisher"
    )
    
    # Test old method still works
    print("Testing backward compatibility...")
    generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
    
    try:
        generator.generate(test_metadata, "test_old_method.csv")
        print("✅ Old method works")
    except Exception as e:
        print(f"❌ Old method failed: {e}")
    
    # Test new method
    print("Testing new features...")
    enhanced_generator = LsiAcsGenerator(
        template_path="templates/LSI_ACS_header.csv",
        config_path="configs/test_config.json",
        log_directory="logs/test"
    )
    
    try:
        result = enhanced_generator.generate_with_validation(test_metadata, "test_new_method.csv")
        
        if result.success:
            print("✅ New method works")
            print(f"   Populated fields: {result.populated_fields_count}")
            print(f"   Empty fields: {result.empty_fields_count}")
        else:
            print("❌ New method validation failed")
            for error in result.errors:
                print(f"   - {error}")
                
    except Exception as e:
        print(f"❌ New method failed: {e}")
    
    # Compare outputs
    print("Comparing outputs...")
    compare_csv_files("test_old_method.csv", "test_new_method.csv")

def compare_csv_files(file1, file2):
    """Compare two CSV files for differences."""
    import csv
    
    try:
        with open(file1, 'r', encoding='utf-8-sig') as f1, \
             open(file2, 'r', encoding='utf-8-sig') as f2:
            
            reader1 = csv.DictReader(f1)
            reader2 = csv.DictReader(f2)
            
            row1 = next(reader1)
            row2 = next(reader2)
            
            differences = []
            improvements = []
            
            for field in row1.keys():
                val1 = row1.get(field, '')
                val2 = row2.get(field, '')
                
                if val1 != val2:
                    if val1 == '' and val2 != '':
                        improvements.append(f"{field}: '{val1}' → '{val2}'")
                    else:
                        differences.append(f"{field}: '{val1}' → '{val2}'")
            
            print(f"Improvements (new fields populated): {len(improvements)}")
            for improvement in improvements[:5]:  # Show first 5
                print(f"  + {improvement}")
            
            if differences:
                print(f"Differences: {len(differences)}")
                for diff in differences[:5]:  # Show first 5
                    print(f"  ~ {diff}")
            
    except Exception as e:
        print(f"Error comparing files: {e}")
```

### Performance Testing

Compare performance between old and new systems:

```python
import time

def performance_comparison():
    """Compare performance between old and new systems."""
    
    test_metadata = create_test_metadata_collection()
    
    # Test old system
    print("Testing old system performance...")
    old_generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
    
    start_time = time.time()
    for i, metadata in enumerate(test_metadata.values()):
        old_generator.generate(metadata, f"temp/old_{i}.csv")
    old_time = time.time() - start_time
    
    # Test new system
    print("Testing new system performance...")
    new_generator = LsiAcsGenerator(
        template_path="templates/LSI_ACS_header.csv",
        config_path="configs/test_config.json"
    )
    
    start_time = time.time()
    for i, metadata in enumerate(test_metadata.values()):
        result = new_generator.generate_with_validation(metadata, f"temp/new_{i}.csv")
    new_time = time.time() - start_time
    
    print(f"Old system: {old_time:.2f} seconds")
    print(f"New system: {new_time:.2f} seconds")
    print(f"Performance ratio: {new_time/old_time:.2f}x")
```

## Troubleshooting

### Common Migration Issues

#### Issue 1: Configuration File Not Found

**Error**: `FileNotFoundError: Configuration file not found`

**Solution**:
```python
# Check if config file exists
import os
config_path = "configs/my_config.json"
if not os.path.exists(config_path):
    print(f"Config file missing: {config_path}")
    # Create default config or use None for no config
    generator = LsiAcsGenerator("templates/LSI_ACS_header.csv", config_path=None)
```

#### Issue 2: New Fields Not Populated

**Error**: Many fields still empty in output

**Solution**:
```python
# Enable LLM field completion
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter

completer = LLMFieldCompleter()
enhanced_metadata = completer.complete_missing_fields(metadata)
result = generator.generate_with_validation(enhanced_metadata, output_path)
```

#### Issue 3: Validation Errors

**Error**: `Validation failed with blocking errors`

**Solution**:
```python
# Debug validation issues
validation_result = generator.validate_submission(metadata)

for field_result in validation_result.field_results:
    if not field_result.is_valid:
        print(f"Field '{field_result.field_name}': {field_result.error_message}")
        if field_result.suggested_value:
            print(f"  Suggested fix: {field_result.suggested_value}")
            # Apply suggested fix
            setattr(metadata, field_result.field_name, field_result.suggested_value)
```

#### Issue 4: Performance Degradation

**Error**: New system slower than old system

**Solution**:
```python
# Disable LLM completion for performance-critical applications
generator = LsiAcsGenerator(
    template_path="templates/LSI_ACS_header.csv",
    config_path="configs/minimal_config.json"  # Minimal config
)

# Use basic generation method
generator.generate(metadata, output_path)  # Skip validation for speed

# Or optimize batch processing
def optimized_batch_processing(metadata_list):
    # Pre-initialize components
    generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
    
    # Process without individual validation
    for metadata in metadata_list:
        generator.generate(metadata, f"output/{metadata.isbn13}.csv")
```

### Migration Checklist

- [ ] Updated to latest version
- [ ] Created configuration files
- [ ] Updated initialization code
- [ ] Tested backward compatibility
- [ ] Tested new features
- [ ] Updated error handling
- [ ] Performance tested
- [ ] Documentation updated
- [ ] Team trained on new features

### Rollback Plan

If migration issues occur, you can rollback:

```python
# Rollback to old method
def rollback_to_old_system():
    """Rollback to basic LSI generation."""
    
    # Use minimal initialization
    generator = LsiAcsGenerator("templates/LSI_ACS_header.csv")
    
    # Use old generation method
    generator.generate(metadata, output_path)
    
    print("Rolled back to basic LSI generation")
```

### Getting Help

If you encounter issues during migration:

1. **Check Documentation**: Review the comprehensive documentation in `docs/`
2. **Run Diagnostics**: Use the built-in diagnostic tools
3. **Check Logs**: Review detailed logs in the log directory
4. **Test with Minimal Data**: Use simple test cases to isolate issues
5. **Contact Support**: Reach out with specific error messages and context

The migration process is designed to be smooth and backward-compatible. Take your time to test thoroughly in a development environment before deploying to production.