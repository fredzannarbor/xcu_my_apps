"""
Data structure validation system for UI robustness.

Ensures all UI data objects have required attributes with sensible defaults
and maintains consistent structure across components.
"""

from typing import Any, Dict, List, Optional, Union
import logging
from copy import deepcopy

from .safety_patterns import (
    ATTRIBUTE_DEFAULTS, 
    safe_dict_get, 
    safe_getattr,
    log_none_encounter
)

logger = logging.getLogger(__name__)


class UIDataValidator:
    """
    Validates and normalizes data objects before UI consumption.
    
    Ensures all required attributes exist with appropriate defaults
    to prevent None value errors in the UI.
    """
    
    def __init__(self):
        self.validation_stats = {
            'validations_performed': 0,
            'none_values_fixed': 0,
            'missing_attributes_added': 0
        }
    
    def validate_design_specs(self, design_specs: Optional[Dict]) -> Dict:
        """
        Ensure design specs have all required attributes.
        
        Args:
            design_specs: Design specifications dictionary (can be None)
            
        Returns:
            Validated design specs with all required attributes
        """
        self.validation_stats['validations_performed'] += 1
        
        if design_specs is None:
            log_none_encounter('validate_design_specs', 'design_specs')
            design_specs = {}
            self.validation_stats['none_values_fixed'] += 1
        
        defaults = ATTRIBUTE_DEFAULTS['design_specs']
        validated = self._ensure_attributes(design_specs, defaults, 'design_specs')
        
        # Ensure nested structures are properly initialized
        validated['typography'] = self._validate_typography(validated.get('typography'))
        validated['color_palette'] = self._validate_color_palette(validated.get('color_palette'))
        validated['trim_sizes'] = self._validate_trim_sizes(validated.get('trim_sizes'))
        validated['layout_preferences'] = self._validate_layout_preferences(validated.get('layout_preferences'))
        
        return validated
    
    def validate_publishing_info(self, publishing_info: Optional[Dict]) -> Dict:
        """
        Ensure publishing info has all required attributes.
        
        Args:
            publishing_info: Publishing information dictionary (can be None)
            
        Returns:
            Validated publishing info with all required attributes
        """
        self.validation_stats['validations_performed'] += 1
        
        if publishing_info is None:
            log_none_encounter('validate_publishing_info', 'publishing_info')
            publishing_info = {}
            self.validation_stats['none_values_fixed'] += 1
        
        defaults = ATTRIBUTE_DEFAULTS['publishing_info']
        validated = self._ensure_attributes(publishing_info, defaults, 'publishing_info')
        
        # Ensure list attributes are properly initialized
        validated['primary_genres'] = list(validated.get('primary_genres') or [])
        validated['distribution_channels'] = list(validated.get('distribution_channels') or [])
        validated['marketing_keywords'] = list(validated.get('marketing_keywords') or [])
        
        # Ensure string attributes are not None
        validated['target_audience'] = str(validated.get('target_audience') or '')
        
        return validated
    
    def validate_branding_info(self, branding_info: Optional[Dict]) -> Dict:
        """
        Ensure branding info has all required attributes.
        
        Args:
            branding_info: Branding information dictionary (can be None)
            
        Returns:
            Validated branding info with all required attributes
        """
        self.validation_stats['validations_performed'] += 1
        
        if branding_info is None:
            log_none_encounter('validate_branding_info', 'branding_info')
            branding_info = {}
            self.validation_stats['none_values_fixed'] += 1
        
        defaults = ATTRIBUTE_DEFAULTS['branding_info']
        validated = self._ensure_attributes(branding_info, defaults, 'branding_info')
        
        # Ensure list attributes are properly initialized
        validated['brand_values'] = list(validated.get('brand_values') or [])
        validated['brand_colors'] = list(validated.get('brand_colors') or [])
        
        return validated
    
    def validate_validation_results(self, validation_results: Optional[Dict]) -> Dict:
        """
        Ensure validation results have all required attributes.
        
        Args:
            validation_results: Validation results dictionary (can be None)
            
        Returns:
            Validated results with all required attributes
        """
        self.validation_stats['validations_performed'] += 1
        
        if validation_results is None:
            log_none_encounter('validate_validation_results', 'validation_results')
            validation_results = {}
            self.validation_stats['none_values_fixed'] += 1
        
        defaults = ATTRIBUTE_DEFAULTS['validation_results']
        validated = self._ensure_attributes(validation_results, defaults, 'validation_results')
        
        # Ensure list attributes are properly initialized
        validated['errors'] = list(validated.get('errors') or [])
        validated['warnings'] = list(validated.get('warnings') or [])
        validated['info'] = list(validated.get('info') or [])
        
        # Ensure boolean attribute is properly set
        validated['is_valid'] = bool(validated.get('is_valid', False))
        
        return validated
    
    def _ensure_attributes(self, obj: Dict, defaults: Dict, context: str) -> Dict:
        """
        Ensure object has all required attributes from defaults.
        
        Args:
            obj: Object to validate
            defaults: Default values for missing attributes
            context: Context for logging
            
        Returns:
            Object with all required attributes
        """
        validated = deepcopy(obj) if obj else {}
        
        for attr, default_value in defaults.items():
            if attr not in validated or validated[attr] is None:
                validated[attr] = deepcopy(default_value)
                self.validation_stats['missing_attributes_added'] += 1
                logger.debug(f"Added missing attribute '{attr}' in {context}")
        
        return validated
    
    def _validate_typography(self, typography: Optional[Dict]) -> Dict:
        """Validate typography settings."""
        if typography is None:
            return {
                'font_family': '',
                'font_size': 12,
                'line_height': 1.5,
                'margins': {},
                'headers': {}
            }
        return dict(typography)
    
    def _validate_color_palette(self, color_palette: Optional[Dict]) -> Dict:
        """Validate color palette settings."""
        if color_palette is None:
            return {
                'primary': '#000000',
                'secondary': '#666666',
                'accent': '#0066cc',
                'background': '#ffffff',
                'text': '#333333'
            }
        return dict(color_palette)
    
    def _validate_trim_sizes(self, trim_sizes: Optional[List]) -> List:
        """Validate trim sizes list."""
        if trim_sizes is None:
            return ['6x9', '5.5x8.5', '8.5x11']
        return list(trim_sizes)
    
    def _validate_layout_preferences(self, layout_preferences: Optional[Dict]) -> Dict:
        """Validate layout preferences."""
        if layout_preferences is None:
            return {
                'chapter_breaks': 'page',
                'page_numbering': 'bottom_center',
                'header_style': 'simple',
                'margins': {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}
            }
        return dict(layout_preferences)
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics for monitoring."""
        return deepcopy(self.validation_stats)
    
    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            'validations_performed': 0,
            'none_values_fixed': 0,
            'missing_attributes_added': 0
        }


class AttributeDefaultProvider:
    """
    Provides type-appropriate defaults for missing attributes.
    
    Ensures all objects have required attributes with sensible defaults
    to prevent AttributeError exceptions.
    """
    
    @staticmethod
    def get_default_for_attribute(category: str, attribute: str) -> Any:
        """
        Get default value for specific attribute.
        
        Args:
            category: Category name (e.g., 'design_specs')
            attribute: Attribute name
            
        Returns:
            Default value for the attribute
        """
        category_defaults = ATTRIBUTE_DEFAULTS.get(category, {})
        return deepcopy(category_defaults.get(attribute, None))
    
    @staticmethod
    def ensure_attribute_exists(obj: Any, attribute: str, default: Any) -> Any:
        """
        Ensure object has specified attribute with default value.
        
        Args:
            obj: Object to check
            attribute: Attribute name
            default: Default value if attribute missing
            
        Returns:
            Attribute value or default
        """
        return safe_getattr(obj, attribute, default)
    
    @staticmethod
    def get_safe_dict_attribute(obj: Any, dict_attr: str, key: str, default: Any = None) -> Any:
        """
        Safely get nested dictionary attribute.
        
        Args:
            obj: Object containing dictionary attribute
            dict_attr: Name of dictionary attribute
            key: Key to look up in dictionary
            default: Default value if not found
            
        Returns:
            Dictionary value or default
        """
        dict_value = safe_getattr(obj, dict_attr, {})
        return safe_dict_get(dict_value, key, default)


class StructureNormalizer:
    """
    Ensures consistent object structure across UI components.
    
    Normalizes data structures to prevent structural inconsistencies
    that could cause UI errors.
    """
    
    def __init__(self, validator: UIDataValidator):
        self.validator = validator
    
    def normalize_imprint_data(self, imprint_data: Optional[Dict]) -> Dict:
        """
        Normalize complete imprint data structure.
        
        Args:
            imprint_data: Raw imprint data (can be None)
            
        Returns:
            Normalized imprint data with consistent structure
        """
        if imprint_data is None:
            imprint_data = {}
        
        normalized = {
            'design_specs': self.validator.validate_design_specs(
                imprint_data.get('design_specs')
            ),
            'publishing_info': self.validator.validate_publishing_info(
                imprint_data.get('publishing_info')
            ),
            'branding_info': self.validator.validate_branding_info(
                imprint_data.get('branding_info')
            ),
            'validation_results': self.validator.validate_validation_results(
                imprint_data.get('validation_results')
            )
        }
        
        # Ensure top-level metadata exists
        normalized['metadata'] = dict(imprint_data.get('metadata') or {})
        normalized['status'] = str(imprint_data.get('status') or 'draft')
        normalized['created_at'] = imprint_data.get('created_at')
        normalized['updated_at'] = imprint_data.get('updated_at')
        
        return normalized
    
    def normalize_form_data(self, form_data: Optional[Dict]) -> Dict:
        """
        Normalize form data to ensure consistent structure.
        
        Args:
            form_data: Raw form data (can be None)
            
        Returns:
            Normalized form data
        """
        if form_data is None:
            return {}
        
        normalized = {}
        for key, value in form_data.items():
            if value is None:
                # Determine appropriate default based on key patterns
                if key.endswith('_list') or key.endswith('_items') or 'genres' in key:
                    normalized[key] = []
                elif key.endswith('_dict') or key.endswith('_config') or 'settings' in key:
                    normalized[key] = {}
                elif key.endswith('_flag') or key.endswith('_enabled') or key.startswith('is_'):
                    normalized[key] = False
                else:
                    normalized[key] = ''
            else:
                normalized[key] = value
        
        return normalized
    
    def ensure_list_structure(self, obj: Any, list_attributes: List[str]) -> Any:
        """
        Ensure specified attributes are lists.
        
        Args:
            obj: Object to normalize
            list_attributes: List of attribute names that should be lists
            
        Returns:
            Object with list attributes normalized
        """
        if obj is None:
            return {}
        
        if isinstance(obj, dict):
            normalized = deepcopy(obj)
            for attr in list_attributes:
                if attr in normalized and not isinstance(normalized[attr], list):
                    if normalized[attr] is None:
                        normalized[attr] = []
                    else:
                        # Try to convert to list
                        try:
                            normalized[attr] = list(normalized[attr])
                        except (TypeError, ValueError):
                            normalized[attr] = []
            return normalized
        
        return obj
    
    def ensure_dict_structure(self, obj: Any, dict_attributes: List[str]) -> Any:
        """
        Ensure specified attributes are dictionaries.
        
        Args:
            obj: Object to normalize
            dict_attributes: List of attribute names that should be dicts
            
        Returns:
            Object with dict attributes normalized
        """
        if obj is None:
            return {}
        
        if isinstance(obj, dict):
            normalized = deepcopy(obj)
            for attr in dict_attributes:
                if attr in normalized and not isinstance(normalized[attr], dict):
                    if normalized[attr] is None:
                        normalized[attr] = {}
                    else:
                        # Try to convert to dict if it's a reasonable structure
                        normalized[attr] = {}
            return normalized
        
        return obj