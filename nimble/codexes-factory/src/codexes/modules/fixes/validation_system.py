"""
Comprehensive validation and safety check system for all fix components.

This module provides validation and safety checks across all components in the
final fix punch list to ensure data integrity and prevent errors.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    component: str
    check_name: str
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ValidationSystem:
    """Comprehensive validation system for all fix components."""
    
    def __init__(self):
        self.validation_results: List[ValidationResult] = []
    
    def validate_isbn_input(self, isbn: str) -> ValidationResult:
        """Validate ISBN input format and structure."""
        result = ValidationResult(
            is_valid=True,
            component="ISBNFormatter",
            check_name="isbn_input_validation"
        )
        
        if not isbn:
            result.is_valid = False
            result.error_message = "ISBN cannot be empty"
            return result
        
        # Remove hyphens and spaces for validation
        clean_isbn = re.sub(r'[-\s]', '', isbn)
        
        if not clean_isbn.isdigit():
            result.is_valid = False
            result.error_message = "ISBN must contain only digits and hyphens"
            return result
        
        if len(clean_isbn) not in [10, 13]:
            result.is_valid = False
            result.error_message = f"ISBN must be 10 or 13 digits, got {len(clean_isbn)}"
            return result
        
        # Validate check digit for ISBN-13
        if len(clean_isbn) == 13:
            if not self._validate_isbn13_check_digit(clean_isbn):
                result.is_valid = False
                result.error_message = "Invalid ISBN-13 check digit"
                return result
        
        logger.info(f"ISBN validation passed for: {isbn}")
        return result
    
    def validate_barcode_positioning(self, position: Dict[str, float], 
                                   cover_dimensions: Dict[str, float]) -> ValidationResult:
        """Validate barcode positioning and safety spaces."""
        result = ValidationResult(
            is_valid=True,
            component="ISBNBarcodeGenerator",
            check_name="barcode_positioning_validation"
        )
        
        required_fields = ['x', 'y']
        for field in required_fields:
            if field not in position:
                result.is_valid = False
                result.error_message = f"Missing required position field: {field}"
                return result
        
        # Validate position is within cover bounds
        if position['x'] < 0 or position['y'] < 0:
            result.is_valid = False
            result.error_message = "Barcode position cannot be negative"
            return result
        
        if 'width' in cover_dimensions and 'height' in cover_dimensions:
            if position['x'] > cover_dimensions['width']:
                result.is_valid = False
                result.error_message = "Barcode X position exceeds cover width"
                return result
            
            if position['y'] > cover_dimensions['height']:
                result.is_valid = False
                result.error_message = "Barcode Y position exceeds cover height"
                return result
        
        # Check minimum safety spaces (0.125 inches minimum)
        min_safety_space = 0.125
        if position['x'] < min_safety_space:
            result.warnings.append(f"Barcode X position may be too close to edge: {position['x']}")
        
        if position['y'] < min_safety_space:
            result.warnings.append(f"Barcode Y position may be too close to edge: {position['y']}")
        
        logger.info(f"Barcode positioning validation completed for position: {position}")
        return result
    
    def validate_dotgrid_spacing(self, dotgrid_position: Dict[str, float], 
                                page_specs: Dict[str, float]) -> ValidationResult:
        """Validate dotgrid positioning meets spacing requirements."""
        result = ValidationResult(
            is_valid=True,
            component="DotgridLayoutManager",
            check_name="dotgrid_spacing_validation"
        )
        
        required_fields = ['y']
        for field in required_fields:
            if field not in dotgrid_position:
                result.is_valid = False
                result.error_message = f"Missing required dotgrid position field: {field}"
                return result
        
        # Validate minimum spacing from header (0.5 inches)
        min_header_spacing = 0.5
        if 'header_height' in page_specs and 'margin_top' in page_specs:
            header_bottom = page_specs['margin_top'] + page_specs['header_height']
            spacing = dotgrid_position['y'] - header_bottom
            
            if spacing < min_header_spacing:
                result.is_valid = False
                result.error_message = f"Dotgrid spacing from header ({spacing:.3f}) is less than minimum ({min_header_spacing})"
                return result
        
        # Validate position is within page bounds
        if 'height' in page_specs:
            if dotgrid_position['y'] > page_specs['height']:
                result.is_valid = False
                result.error_message = "Dotgrid Y position exceeds page height"
                return result
        
        logger.info(f"Dotgrid spacing validation passed for position: {dotgrid_position}")
        return result
    
    def validate_subtitle_length(self, subtitle: str, imprint: str, 
                               max_length: int = 38) -> ValidationResult:
        """Validate subtitle length against imprint requirements."""
        result = ValidationResult(
            is_valid=True,
            component="SubtitleValidator",
            check_name="subtitle_length_validation"
        )
        
        if not subtitle:
            result.warnings.append("Subtitle is empty")
            return result
        
        current_length = len(subtitle)
        
        # Check against imprint-specific limits
        if imprint == "xynapse_traces" and current_length > max_length:
            result.is_valid = False
            result.error_message = f"Subtitle length ({current_length}) exceeds {imprint} limit ({max_length})"
            return result
        
        # General warning for very long subtitles
        if current_length > 50:
            result.warnings.append(f"Subtitle is quite long ({current_length} characters)")
        
        logger.info(f"Subtitle length validation passed: {current_length} characters for {imprint}")
        return result
    
    def validate_spine_width_calculation(self, page_count: int, 
                                       calculated_width: float) -> ValidationResult:
        """Validate spine width calculation results."""
        result = ValidationResult(
            is_valid=True,
            component="SpineWidthCalculator",
            check_name="spine_width_validation"
        )
        
        if page_count <= 0:
            result.is_valid = False
            result.error_message = "Page count must be positive"
            return result
        
        if calculated_width <= 0:
            result.is_valid = False
            result.error_message = "Calculated spine width must be positive"
            return result
        
        # Validate reasonable spine width ranges
        min_expected_width = page_count * 0.0015  # Very thin paper
        max_expected_width = page_count * 0.008   # Very thick paper
        
        if calculated_width < min_expected_width:
            result.warnings.append(f"Spine width ({calculated_width:.4f}) seems unusually thin for {page_count} pages")
        
        if calculated_width > max_expected_width:
            result.warnings.append(f"Spine width ({calculated_width:.4f}) seems unusually thick for {page_count} pages")
        
        # Check for extremely thin books that might have printing issues
        if calculated_width < 0.0625:  # Less than 1/16 inch
            result.warnings.append("Very thin spine may cause printing difficulties")
        
        logger.info(f"Spine width validation passed: {calculated_width:.4f} for {page_count} pages")
        return result
    
    def validate_template_modification_safety(self, template_path: str, 
                                            backup_exists: bool = False) -> ValidationResult:
        """Validate safety of template modifications."""
        result = ValidationResult(
            is_valid=True,
            component="TemplateModifier",
            check_name="template_safety_validation"
        )
        
        template_file = Path(template_path)
        
        if not template_file.exists():
            result.is_valid = False
            result.error_message = f"Template file does not exist: {template_path}"
            return result
        
        if not template_file.suffix == '.tex':
            result.warnings.append("Template file does not have .tex extension")
        
        if not backup_exists:
            result.warnings.append("No backup exists for template modification")
        
        # Check if template is writable
        if not template_file.is_file() or not template_file.parent.exists():
            result.is_valid = False
            result.error_message = f"Cannot write to template location: {template_path}"
            return result
        
        logger.info(f"Template modification safety validation passed for: {template_path}")
        return result
    
    def validate_llm_response(self, response: str, expected_max_length: int = 38) -> ValidationResult:
        """Validate LLM-generated subtitle response."""
        result = ValidationResult(
            is_valid=True,
            component="SubtitleValidator",
            check_name="llm_response_validation"
        )
        
        if not response:
            result.is_valid = False
            result.error_message = "LLM response is empty"
            return result
        
        # Clean the response (remove quotes, extra whitespace)
        cleaned_response = response.strip().strip('"\'')
        
        if len(cleaned_response) > expected_max_length:
            result.is_valid = False
            result.error_message = f"LLM response length ({len(cleaned_response)}) exceeds limit ({expected_max_length})"
            return result
        
        # Check for potentially problematic characters
        if any(char in cleaned_response for char in ['\n', '\r', '\t']):
            result.warnings.append("LLM response contains whitespace characters")
        
        logger.info(f"LLM response validation passed: '{cleaned_response}'")
        return result
    
    def validate_configuration_values(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration values for all components."""
        result = ValidationResult(
            is_valid=True,
            component="ConfigurationValidator",
            check_name="configuration_validation"
        )
        
        # Validate spine width configuration
        if 'spine_width' in config:
            spine_config = config['spine_width']
            if 'fallback_width' in spine_config:
                if spine_config['fallback_width'] <= 0:
                    result.is_valid = False
                    result.error_message = "Fallback spine width must be positive"
                    return result
        
        # Validate subtitle configuration
        if 'xynapse_traces' in config:
            xynapse_config = config['xynapse_traces']
            if 'subtitle_max_length' in xynapse_config:
                if xynapse_config['subtitle_max_length'] <= 0:
                    result.is_valid = False
                    result.error_message = "Subtitle max length must be positive"
                    return result
        
        # Validate LLM configuration
        if 'subtitle_generation' in config:
            llm_config = config['subtitle_generation']
            if 'retry_attempts' in llm_config:
                if llm_config['retry_attempts'] < 1:
                    result.warnings.append("LLM retry attempts should be at least 1")
        
        logger.info("Configuration validation completed")
        return result
    
    def run_comprehensive_validation(self, validation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Run all validation checks and return comprehensive results."""
        results = []
        
        # Run all applicable validations based on provided data
        if 'isbn' in validation_data:
            results.append(self.validate_isbn_input(validation_data['isbn']))
        
        if 'barcode_position' in validation_data and 'cover_dimensions' in validation_data:
            results.append(self.validate_barcode_positioning(
                validation_data['barcode_position'],
                validation_data['cover_dimensions']
            ))
        
        if 'dotgrid_position' in validation_data and 'page_specs' in validation_data:
            results.append(self.validate_dotgrid_spacing(
                validation_data['dotgrid_position'],
                validation_data['page_specs']
            ))
        
        if 'subtitle' in validation_data and 'imprint' in validation_data:
            results.append(self.validate_subtitle_length(
                validation_data['subtitle'],
                validation_data['imprint'],
                validation_data.get('max_length', 38)
            ))
        
        if 'page_count' in validation_data and 'spine_width' in validation_data:
            results.append(self.validate_spine_width_calculation(
                validation_data['page_count'],
                validation_data['spine_width']
            ))
        
        if 'template_path' in validation_data:
            results.append(self.validate_template_modification_safety(
                validation_data['template_path'],
                validation_data.get('backup_exists', False)
            ))
        
        if 'llm_response' in validation_data:
            results.append(self.validate_llm_response(
                validation_data['llm_response'],
                validation_data.get('expected_max_length', 38)
            ))
        
        if 'config' in validation_data:
            results.append(self.validate_configuration_values(validation_data['config']))
        
        self.validation_results.extend(results)
        
        # Log summary
        total_checks = len(results)
        failed_checks = sum(1 for r in results if not r.is_valid)
        warnings_count = sum(len(r.warnings) for r in results)
        
        logger.info(f"Comprehensive validation completed: {total_checks} checks, "
                   f"{failed_checks} failures, {warnings_count} warnings")
        
        return results
    
    def _validate_isbn13_check_digit(self, isbn13: str) -> bool:
        """Validate ISBN-13 check digit using the standard algorithm."""
        if len(isbn13) != 13:
            return False
        
        # Calculate check digit
        total = 0
        for i, digit in enumerate(isbn13[:-1]):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        calculated_check_digit = (10 - (total % 10)) % 10
        actual_check_digit = int(isbn13[-1])
        
        return calculated_check_digit == actual_check_digit