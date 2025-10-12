#!/usr/bin/env python3
"""
Configuration Debugger

This module provides debugging utilities for the multi-level configuration system.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .multi_level_config import MultiLevelConfiguration, ConfigurationContext, ConfigurationLevel

logger = logging.getLogger(__name__)


class ConfigurationDebugger:
    """Debugging utilities for configuration system."""
    
    def __init__(self, config: MultiLevelConfiguration):
        """Initialize debugger with configuration instance."""
        self.config = config
    
    def debug_configuration_resolution(self, key: str, context: ConfigurationContext) -> Dict[str, Any]:
        """
        Debug how a configuration key is resolved.
        
        Args:
            key: Configuration key to debug
            context: Configuration context
            
        Returns:
            Detailed resolution information
        """
        debug_info = {
            "key": key,
            "context": {
                "book_isbn": context.book_isbn,
                "tranche_name": context.tranche_name,
                "imprint_name": context.imprint_name,
                "publisher_name": context.publisher_name,
                "field_overrides": list(context.field_overrides.keys()) if context.field_overrides else []
            },
            "resolution_path": [],
            "final_value": None,
            "final_source": None
        }
        
        # Check each level in priority order
        for level in ConfigurationLevel:
            try:
                config_dict = self.config._get_level_config(level, context)
                if key in config_dict:
                    entry = config_dict[key]
                    level_info = {
                        "level": level.value,
                        "value": entry.value,
                        "source": entry.source,
                        "description": entry.description,
                        "is_active": debug_info["final_value"] is None
                    }
                    debug_info["resolution_path"].append(level_info)
                    
                    # Set final value from highest priority match
                    if debug_info["final_value"] is None:
                        debug_info["final_value"] = entry.value
                        debug_info["final_source"] = entry.source
                else:
                    debug_info["resolution_path"].append({
                        "level": level.value,
                        "value": None,
                        "source": None,
                        "description": "Not found at this level",
                        "is_active": False
                    })
            except Exception as e:
                debug_info["resolution_path"].append({
                    "level": level.value,
                    "value": None,
                    "source": None,
                    "description": f"Error: {str(e)}",
                    "is_active": False
                })
        
        return debug_info
    
    def validate_configuration_files(self) -> Dict[str, Any]:
        """
        Validate all configuration files for syntax and structure.
        
        Returns:
            Validation results for all configuration files
        """
        validation_results = {
            "valid_files": [],
            "invalid_files": [],
            "missing_files": [],
            "summary": {}
        }
        
        # Check each configuration directory
        config_dirs = {
            "default": self.config.config_dir / "default_lsi_config.json",
            "publishers": self.config.config_dir / "publishers",
            "imprints": self.config.config_dir / "imprints", 
            "tranches": self.config.config_dir / "tranches",
            "books": self.config.config_dir / "books"
        }
        
        # Validate default config
        default_config = config_dirs["default"]
        if default_config.exists():
            result = self._validate_json_file(default_config)
            if result["valid"]:
                validation_results["valid_files"].append(result)
            else:
                validation_results["invalid_files"].append(result)
        else:
            validation_results["missing_files"].append({
                "file": str(default_config),
                "type": "default",
                "message": "Default configuration file missing"
            })
        
        # Validate directory-based configs
        for config_type, config_dir in config_dirs.items():
            if config_type == "default":
                continue
                
            if config_dir.exists() and config_dir.is_dir():
                for config_file in config_dir.glob("*.json"):
                    result = self._validate_json_file(config_file)
                    result["type"] = config_type
                    if result["valid"]:
                        validation_results["valid_files"].append(result)
                    else:
                        validation_results["invalid_files"].append(result)
        
        # Generate summary
        validation_results["summary"] = {
            "total_files": len(validation_results["valid_files"]) + len(validation_results["invalid_files"]),
            "valid_count": len(validation_results["valid_files"]),
            "invalid_count": len(validation_results["invalid_files"]),
            "missing_count": len(validation_results["missing_files"]),
            "success_rate": len(validation_results["valid_files"]) / max(1, len(validation_results["valid_files"]) + len(validation_results["invalid_files"])) * 100
        }
        
        return validation_results
    
    def _validate_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single JSON configuration file."""
        result = {
            "file": str(file_path),
            "valid": False,
            "errors": [],
            "warnings": [],
            "key_count": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            result["valid"] = True
            result["key_count"] = len(config_data) if isinstance(config_data, dict) else 0
            
            # Check for common issues
            if isinstance(config_data, dict):
                # Check for empty values
                empty_keys = [k for k, v in config_data.items() if v == "" or v is None]
                if empty_keys:
                    result["warnings"].append(f"Empty values for keys: {empty_keys}")
                
                # Check for suspicious values
                suspicious_keys = [k for k, v in config_data.items() if isinstance(v, str) and "TODO" in v.upper()]
                if suspicious_keys:
                    result["warnings"].append(f"TODO values for keys: {suspicious_keys}")
            
        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON syntax error: {str(e)}")
        except Exception as e:
            result["errors"].append(f"File error: {str(e)}")
        
        return result
    
    def generate_configuration_report(self, context: ConfigurationContext) -> str:
        """
        Generate a comprehensive configuration report.
        
        Args:
            context: Configuration context
            
        Returns:
            Formatted configuration report
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CONFIGURATION SYSTEM DEBUG REPORT")
        report_lines.append("=" * 80)
        
        # Context information
        report_lines.append("\nCONTEXT INFORMATION:")
        report_lines.append(f"  Book ISBN: {context.book_isbn or 'Not specified'}")
        report_lines.append(f"  Tranche: {context.tranche_name or 'Not specified'}")
        report_lines.append(f"  Imprint: {context.imprint_name or 'Not specified'}")
        report_lines.append(f"  Publisher: {context.publisher_name or 'Not specified'}")
        report_lines.append(f"  Field Overrides: {len(context.field_overrides) if context.field_overrides else 0}")
        
        # Configuration validation
        report_lines.append("\nCONFIGURATION FILE VALIDATION:")
        validation_results = self.validate_configuration_files()
        summary = validation_results["summary"]
        report_lines.append(f"  Total Files: {summary['total_files']}")
        report_lines.append(f"  Valid Files: {summary['valid_count']}")
        report_lines.append(f"  Invalid Files: {summary['invalid_count']}")
        report_lines.append(f"  Missing Files: {summary['missing_count']}")
        report_lines.append(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        # Invalid files details
        if validation_results["invalid_files"]:
            report_lines.append("\n  INVALID FILES:")
            for invalid_file in validation_results["invalid_files"]:
                report_lines.append(f"    {invalid_file['file']}: {', '.join(invalid_file['errors'])}")
        
        # Missing files details
        if validation_results["missing_files"]:
            report_lines.append("\n  MISSING FILES:")
            for missing_file in validation_results["missing_files"]:
                report_lines.append(f"    {missing_file['file']}: {missing_file['message']}")
        
        # All configurations
        report_lines.append("\nALL CONFIGURATIONS:")
        all_configs = self.config.list_all_configurations(context)
        for key, info in sorted(all_configs.items()):
            report_lines.append(f"  {key}:")
            report_lines.append(f"    Value: {info['value']}")
            report_lines.append(f"    Level: {info['level']}")
            report_lines.append(f"    Source: {info['source']}")
            if info['available_levels']:
                report_lines.append(f"    Available at {len(info['available_levels'])} levels")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)
    
    def test_configuration_inheritance(self, test_key: str = "test_inheritance") -> Dict[str, Any]:
        """
        Test configuration inheritance by setting values at different levels.
        
        Args:
            test_key: Key to use for testing
            
        Returns:
            Test results
        """
        test_results = {
            "test_key": test_key,
            "levels_tested": [],
            "inheritance_working": True,
            "errors": []
        }
        
        # Create test context
        test_context = ConfigurationContext(
            publisher_name="test_publisher",
            imprint_name="test_imprint", 
            tranche_name="test_tranche"
        )
        
        try:
            # Set values at different levels
            test_values = {
                ConfigurationLevel.GLOBAL_DEFAULT: "global_value",
                ConfigurationLevel.PUBLISHER_SPECIFIC: "publisher_value",
                ConfigurationLevel.IMPRINT_SPECIFIC: "imprint_value",
                ConfigurationLevel.TRANCHE_SPECIFIC: "tranche_value",
                ConfigurationLevel.FIELD_OVERRIDE: "override_value"
            }
            
            # Set test values
            for level, value in test_values.items():
                if level == ConfigurationLevel.FIELD_OVERRIDE:
                    test_context.field_overrides[test_key] = value
                else:
                    success = self.config.set_value(test_key, value, level, test_context)
                    if not success:
                        test_results["errors"].append(f"Failed to set value at {level.value}")
            
            # Test resolution at each level
            for level in ConfigurationLevel:
                if level == ConfigurationLevel.FIELD_OVERRIDE:
                    # Test with field override
                    resolved_value = self.config.get_value(test_key, test_context)
                    expected_value = "override_value"
                else:
                    # Test without field override
                    context_without_override = ConfigurationContext(
                        publisher_name="test_publisher",
                        imprint_name="test_imprint",
                        tranche_name="test_tranche"
                    )
                    resolved_value = self.config.get_value(test_key, context_without_override)
                    expected_value = test_values.get(level, "global_value")
                
                test_result = {
                    "level": level.value,
                    "expected": expected_value,
                    "actual": resolved_value,
                    "correct": resolved_value == expected_value
                }
                test_results["levels_tested"].append(test_result)
                
                if not test_result["correct"]:
                    test_results["inheritance_working"] = False
                    test_results["errors"].append(
                        f"Level {level.value}: expected '{expected_value}', got '{resolved_value}'"
                    )
        
        except Exception as e:
            test_results["inheritance_working"] = False
            test_results["errors"].append(f"Test exception: {str(e)}")
        
        return test_results


def debug_configuration_issue(config_dir: str = "configs", 
                             tranche_name: str = None,
                             imprint_name: str = None,
                             publisher_name: str = None) -> str:
    """
    Debug configuration issues with detailed reporting.
    
    Args:
        config_dir: Configuration directory
        tranche_name: Tranche name for context
        imprint_name: Imprint name for context
        publisher_name: Publisher name for context
        
    Returns:
        Detailed debug report
    """
    try:
        # Create configuration and debugger
        config = MultiLevelConfiguration(config_dir)
        debugger = ConfigurationDebugger(config)
        
        # Create context
        context = ConfigurationContext(
            tranche_name=tranche_name,
            imprint_name=imprint_name,
            publisher_name=publisher_name
        )
        
        # Generate comprehensive report
        report = debugger.generate_configuration_report(context)
        
        # Test inheritance
        inheritance_test = debugger.test_configuration_inheritance()
        
        report += "\n\nINHERITANCE TEST RESULTS:\n"
        report += f"Inheritance Working: {inheritance_test['inheritance_working']}\n"
        if inheritance_test['errors']:
            report += "Errors:\n"
            for error in inheritance_test['errors']:
                report += f"  - {error}\n"
        
        return report
        
    except Exception as e:
        return f"Debug failed: {str(e)}"