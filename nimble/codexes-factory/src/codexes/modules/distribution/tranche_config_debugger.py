
"""
Tranche Configuration Debugger

This module provides debugging and validation tools for tranche configuration application.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TrancheConfigDebugger:
    """Debug and validate tranche configuration application."""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.debug_enabled = True
    
    def debug_tranche_loading(self, tranche_name: str) -> Dict[str, Any]:
        """Debug tranche configuration loading process."""
        debug_info = {
            "tranche_name": tranche_name,
            "config_path": None,
            "exists": False,
            "loaded_successfully": False,
            "config_keys": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if tranche config file exists
            tranche_path = self.config_dir / "tranches" / f"{tranche_name}.json"
            debug_info["config_path"] = str(tranche_path)
            debug_info["exists"] = tranche_path.exists()
            
            if not tranche_path.exists():
                debug_info["errors"].append(f"Tranche config file not found: {tranche_path}")
                return debug_info
            
            # Try to load the configuration
            with open(tranche_path, 'r') as f:
                config = json.load(f)
            
            debug_info["loaded_successfully"] = True
            debug_info["config_keys"] = list(config.keys())
            
            # Validate expected tranche configuration sections
            expected_sections = [
                "series_info", "contributor_info", "annotation_boilerplate",
                "table_of_contents_template", "file_paths", "blank_fields"
            ]
            
            for section in expected_sections:
                if section not in config:
                    debug_info["warnings"].append(f"Missing expected section: {section}")
                else:
                    logger.info(f"Found tranche section: {section}")
            
            # Validate annotation boilerplate specifically
            if "annotation_boilerplate" in config:
                boilerplate = config["annotation_boilerplate"]
                if not isinstance(boilerplate, dict):
                    debug_info["errors"].append("annotation_boilerplate must be a dictionary")
                else:
                    if "suffix" not in boilerplate:
                        debug_info["warnings"].append("annotation_boilerplate missing 'suffix' key")
                    if "prefix" not in boilerplate:
                        debug_info["warnings"].append("annotation_boilerplate missing 'prefix' key")
            
            logger.info(f"Tranche config debug complete for {tranche_name}")
            
        except json.JSONDecodeError as e:
            debug_info["errors"].append(f"Invalid JSON in tranche config: {e}")
        except Exception as e:
            debug_info["errors"].append(f"Error loading tranche config: {e}")
        
        return debug_info
    
    def validate_tranche_application(self, tranche_name: str, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that tranche configuration is properly applied to metadata."""
        validation_result = {
            "tranche_name": tranche_name,
            "applied_correctly": True,
            "missing_applications": [],
            "successful_applications": [],
            "errors": []
        }
        
        try:
            # Load tranche config
            tranche_path = self.config_dir / "tranches" / f"{tranche_name}.json"
            if not tranche_path.exists():
                validation_result["errors"].append(f"Tranche config not found: {tranche_path}")
                validation_result["applied_correctly"] = False
                return validation_result
            
            with open(tranche_path, 'r') as f:
                tranche_config = json.load(f)
            
            # Check series information application
            if "series_info" in tranche_config:
                series_info = tranche_config["series_info"]
                if "series_name" in series_info:
                    expected_series = series_info["series_name"]
                    actual_series = metadata_dict.get("series_name", "")
                    if actual_series == expected_series:
                        validation_result["successful_applications"].append(f"Series name: {expected_series}")
                    else:
                        validation_result["missing_applications"].append(
                            f"Series name not applied: expected '{expected_series}', got '{actual_series}'"
                        )
                        validation_result["applied_correctly"] = False
            
            # Check contributor information application
            if "contributor_info" in tranche_config:
                contrib_info = tranche_config["contributor_info"]
                for key, expected_value in contrib_info.items():
                    actual_value = metadata_dict.get(key, "")
                    if actual_value == expected_value:
                        validation_result["successful_applications"].append(f"{key}: applied correctly")
                    else:
                        validation_result["missing_applications"].append(
                            f"{key} not applied: expected '{expected_value}', got '{actual_value}'"
                        )
                        validation_result["applied_correctly"] = False
            
            # Check annotation boilerplate application
            if "annotation_boilerplate" in tranche_config:
                boilerplate = tranche_config["annotation_boilerplate"]
                annotation = metadata_dict.get("annotation_summary", "")
                
                if "suffix" in boilerplate and boilerplate["suffix"]:
                    if boilerplate["suffix"] in annotation:
                        validation_result["successful_applications"].append("Annotation suffix applied")
                    else:
                        validation_result["missing_applications"].append("Annotation suffix not applied")
                        validation_result["applied_correctly"] = False
                
                if "prefix" in boilerplate and boilerplate["prefix"]:
                    if annotation.startswith(boilerplate["prefix"]):
                        validation_result["successful_applications"].append("Annotation prefix applied")
                    else:
                        validation_result["missing_applications"].append("Annotation prefix not applied")
                        validation_result["applied_correctly"] = False
            
        except Exception as e:
            validation_result["errors"].append(f"Error validating tranche application: {e}")
            validation_result["applied_correctly"] = False
        
        return validation_result
