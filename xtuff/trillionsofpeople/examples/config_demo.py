#!/usr/bin/env python3
"""
Demonstration of the TrillionsOfPeople configuration management system.

This script shows how to use the ConfigManager to load configuration from
multiple sources with proper validation and security.
"""

import os
import tempfile
from pathlib import Path

from trillions_of_people.core.config import ConfigManager
from trillions_of_people.core.exceptions import ConfigurationError


def demo_basic_config():
    """Demonstrate basic configuration loading with defaults."""
    print("=== Basic Configuration Demo ===")
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    print(f"Default country: {config.default_country}")
    print(f"Default year: {config.default_year}")
    print(f"Max people per request: {config.max_people_per_request}")
    print(f"Image generation enabled: {config.enable_image_generation}")
    print(f"Log level: {config.log_level}")
    print()


def demo_env_config():
    """Demonstrate configuration loading from environment variables."""
    print("=== Environment Variables Demo ===")
    
    # Set some environment variables
    os.environ['TRILLIONS_DEFAULT_COUNTRY'] = 'Canada'
    os.environ['TRILLIONS_DEFAULT_YEAR'] = '2075'
    os.environ['TRILLIONS_MAX_PEOPLE_PER_REQUEST'] = '8'
    os.environ['TRILLIONS_LOG_LEVEL'] = 'DEBUG'
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    print(f"Country from env: {config.default_country}")
    print(f"Year from env: {config.default_year}")
    print(f"Max people from env: {config.max_people_per_request}")
    print(f"Log level from env: {config.log_level}")
    
    # Clean up
    for key in ['TRILLIONS_DEFAULT_COUNTRY', 'TRILLIONS_DEFAULT_YEAR', 
                'TRILLIONS_MAX_PEOPLE_PER_REQUEST', 'TRILLIONS_LOG_LEVEL']:
        os.environ.pop(key, None)
    print()


def demo_toml_config():
    """Demonstrate configuration loading from TOML file."""
    print("=== TOML Configuration Demo ===")
    
    # Create a temporary TOML config file
    toml_content = '''
[trillions_of_people]
default_country = "United Kingdom"
default_year = 2090
max_people_per_request = 12
enable_image_generation = false
log_level = "WARNING"
cache_ttl = 7200
request_timeout = 45
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(toml_content)
        f.flush()
        
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config(config_file=f.name)
            
            print(f"Country from TOML: {config.default_country}")
            print(f"Year from TOML: {config.default_year}")
            print(f"Max people from TOML: {config.max_people_per_request}")
            print(f"Image generation from TOML: {config.enable_image_generation}")
            print(f"Log level from TOML: {config.log_level}")
            print(f"Cache TTL from TOML: {config.cache_ttl}")
            print(f"Request timeout from TOML: {config.request_timeout}")
            
        finally:
            os.unlink(f.name)
    print()


def demo_precedence():
    """Demonstrate configuration precedence (CLI > Env > File > Defaults)."""
    print("=== Configuration Precedence Demo ===")
    
    # Create TOML file
    toml_content = '''
[trillions_of_people]
default_country = "France"
default_year = 2080
max_people_per_request = 6
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(toml_content)
        f.flush()
        
        try:
            # Set environment variable
            os.environ['TRILLIONS_DEFAULT_COUNTRY'] = 'Germany'
            
            # CLI overrides
            cli_overrides = {
                'default_country': 'Japan',
                'log_level': 'ERROR'
            }
            
            config_manager = ConfigManager()
            config = config_manager.load_config(
                config_file=f.name,
                cli_overrides=cli_overrides
            )
            
            print("Configuration sources and precedence:")
            print(f"  Country: {config.default_country} (CLI override wins)")
            print(f"  Year: {config.default_year} (from TOML file)")
            print(f"  Max people: {config.max_people_per_request} (from TOML file)")
            print(f"  Log level: {config.log_level} (CLI override wins)")
            
        finally:
            os.environ.pop('TRILLIONS_DEFAULT_COUNTRY', None)
            os.unlink(f.name)
    print()


def demo_validation():
    """Demonstrate configuration validation and error handling."""
    print("=== Configuration Validation Demo ===")
    
    config_manager = ConfigManager()
    
    # Test invalid environment variable
    os.environ['TRILLIONS_MAX_PEOPLE_PER_REQUEST'] = '2000'  # Too high
    
    try:
        config_manager.load_config()
        print("ERROR: Should have failed validation!")
    except ConfigurationError as e:
        print(f"✓ Caught validation error: {e}")
    finally:
        os.environ.pop('TRILLIONS_MAX_PEOPLE_PER_REQUEST', None)
    
    # Test invalid TOML file
    invalid_toml = '''
[trillions_of_people]
default_year = -500000
log_level = "INVALID_LEVEL"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(invalid_toml)
        f.flush()
        
        try:
            config_manager.load_config(config_file=f.name)
            print("ERROR: Should have failed validation!")
        except ConfigurationError as e:
            print(f"✓ Caught TOML validation error: {e}")
        finally:
            os.unlink(f.name)
    print()


def demo_sample_config():
    """Demonstrate sample configuration file creation."""
    print("=== Sample Configuration Demo ===")
    
    config_manager = ConfigManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        try:
            config_manager.create_sample_config(f.name)
            
            print(f"✓ Sample config created at: {f.name}")
            
            # Check file permissions
            stat = Path(f.name).stat()
            permissions = oct(stat.st_mode)[-3:]
            print(f"✓ File permissions: {permissions} (secure)")
            
            # Show first few lines
            content = Path(f.name).read_text()
            lines = content.split('\n')[:10]
            print("✓ Sample content (first 10 lines):")
            for line in lines:
                print(f"  {line}")
            
        finally:
            os.unlink(f.name)
    print()


def demo_api_key_security():
    """Demonstrate API key security validation."""
    print("=== API Key Security Demo ===")
    
    config_manager = ConfigManager()
    
    # Test various API key security issues
    test_keys = [
        ("test", "Obviously a test key"),
        ("sk-short", "Too short"),
        ("invalid-format", "Wrong format"),
        ("sk-1234567890123456789012345678901234567890123456", "Valid format")
    ]
    
    for key, description in test_keys:
        warnings = config_manager.validate_api_key_security(key, "openai")
        if warnings:
            print(f"⚠️  {description}: {', '.join(warnings)}")
        else:
            print(f"✓ {description}: No security warnings")
    print()


def main():
    """Run all configuration demos."""
    print("TrillionsOfPeople Configuration Management System Demo")
    print("=" * 55)
    print()
    
    try:
        demo_basic_config()
        demo_env_config()
        demo_toml_config()
        demo_precedence()
        demo_validation()
        demo_sample_config()
        demo_api_key_security()
        
        print("✓ All demos completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()