"""
Configuration Validation Framework for Streamlit UI
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .configuration_manager import ValidationResult, ValidationError, ValidationWarning


class ConfigurationValidator:
    """Validate configuration parameters with real-time feedback"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.lsi_valid_values = self._load_lsi_valid_values()
    
    def _load_lsi_valid_values(self) -> Dict[str, List[str]]:
        """Load LSI valid values from reference files"""
        valid_values = {}
        
        # Load valid rendition booktypes
        rendition_file = Path("lsi_valid_rendition_booktypes.txt")
        if rendition_file.exists():
            try:
                with open(rendition_file, 'r') as f:
                    valid_values['rendition_booktype'] = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.logger.warning(f"Could not load valid rendition booktypes: {e}")
        
        # Load valid contributor codes
        contributor_file = Path("lsi_valid_contributor_codes.csv")
        if contributor_file.exists():
            try:
                with open(contributor_file, 'r') as f:
                    lines = f.readlines()[1:]  # Skip header
                    valid_values['contributor_codes'] = [line.split(',')[0].strip() for line in lines if line.strip()]
            except Exception as e:
                self.logger.warning(f"Could not load valid contributor codes: {e}")
        
        return valid_values
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """Comprehensive configuration validation"""
        errors = []
        warnings = []
        parameter_status = {}
        
        # Validate required fields
        errors.extend(self._validate_required_fields(config, parameter_status))
        
        # Validate LSI parameters
        errors.extend(self._validate_lsi_parameters(config, parameter_status))
        
        # Validate territorial pricing
        warnings.extend(self._validate_territorial_pricing(config, parameter_status))
        
        # Validate physical specifications
        errors.extend(self._validate_physical_specifications(config, parameter_status))
        
        # Validate parameter dependencies
        errors.extend(self._validate_parameter_dependencies(config, parameter_status))
        
        # Set default status for parameters not yet validated
        for key in config.keys():
            if key not in parameter_status:
                parameter_status[key] = "valid"
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            parameter_status=parameter_status
        )
    
    def _validate_required_fields(self, config: Dict[str, Any], parameter_status: Dict[str, str]) -> List[ValidationError]:
        """Validate required fields"""
        errors = []
        required_fields = [
            ('publisher', 'Publisher'),
            ('imprint', 'Imprint'),
            ('lightning_source_account', 'Lightning Source Account'),
            ('language_code', 'Language Code'),
            ('model', 'Primary LLM Model')
        ]
        
        for field_key, field_name in required_fields:
            value = config.get(field_key)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    field_name=field_key,
                    error_message=f"{field_name} is required",
                    error_type="required_field"
                ))
                parameter_status[field_key] = "error"
            else:
                parameter_status[field_key] = "valid"
        
        return errors
    
    def _validate_lsi_parameters(self, config: Dict[str, Any], parameter_status: Dict[str, str]) -> List[ValidationError]:
        """Validate LSI-specific parameters"""
        errors = []
        
        # Validate Lightning Source Account format
        ls_account = config.get('lightning_source_account', '')
        if ls_account:
            if not str(ls_account).isdigit():
                errors.append(ValidationError(
                    field_name='lightning_source_account',
                    error_message="Lightning Source Account must be numeric",
                    error_type="format_error"
                ))
                parameter_status['lightning_source_account'] = "error"
            elif len(str(ls_account)) < 6:
                errors.append(ValidationError(
                    field_name='lightning_source_account',
                    error_message="Lightning Source Account should be at least 6 digits",
                    error_type="format_error"
                ))
                parameter_status['lightning_source_account'] = "warning"
        
        # Validate rendition booktype
        rendition_booktype = config.get('rendition_booktype', '')
        if rendition_booktype and 'rendition_booktype' in self.lsi_valid_values:
            valid_types = self.lsi_valid_values['rendition_booktype']
            if rendition_booktype not in valid_types:
                errors.append(ValidationError(
                    field_name='rendition_booktype',
                    error_message=f"Invalid rendition booktype: {rendition_booktype}",
                    error_type="invalid_value",
                    suggested_values=valid_types[:5]  # Show first 5 suggestions
                ))
                parameter_status['rendition_booktype'] = "error"
        
        # Validate submission methods
        submission_methods = ['FTP', 'Upload', 'Email']
        for method_field in ['cover_submission_method', 'text_block_submission_method']:
            method = config.get(method_field, '')
            if method and method not in submission_methods:
                errors.append(ValidationError(
                    field_name=method_field,
                    error_message=f"Invalid submission method: {method}",
                    error_type="invalid_value",
                    suggested_values=submission_methods
                ))
                parameter_status[method_field] = "error"
        
        return errors
    
    def _validate_territorial_pricing(self, config: Dict[str, Any], parameter_status: Dict[str, str]) -> List[ValidationWarning]:
        """Validate territorial pricing configuration"""
        warnings = []
        
        # Check wholesale discount percentages
        discount_fields = [
            'us_wholesale_discount',
            'uk_wholesale_discount',
            'eu_wholesale_discount',
            'ca_wholesale_discount',
            'au_wholesale_discount'
        ]
        
        for field in discount_fields:
            discount = config.get(field)
            if discount is not None:
                try:
                    discount_val = float(discount)
                    if discount_val < 0 or discount_val > 100:
                        warnings.append(ValidationWarning(
                            field_name=field,
                            warning_message=f"Wholesale discount should be between 0-100%",
                            warning_type="range_warning"
                        ))
                        parameter_status[field] = "warning"
                    elif discount_val < 20:
                        warnings.append(ValidationWarning(
                            field_name=field,
                            warning_message=f"Low wholesale discount may affect distribution",
                            warning_type="business_warning"
                        ))
                        parameter_status[field] = "warning"
                except ValueError:
                    warnings.append(ValidationWarning(
                        field_name=field,
                        warning_message=f"Invalid discount value: {discount}",
                        warning_type="format_warning"
                    ))
                    parameter_status[field] = "warning"
        
        # Validate territorial configs
        territorial_configs = config.get('territorial_configs', {})
        for territory, territory_config in territorial_configs.items():
            if not isinstance(territory_config, dict):
                continue
                
            # Check required fields for each territory
            required_territory_fields = ['currency', 'pricing_multiplier']
            for field in required_territory_fields:
                if field not in territory_config:
                    warnings.append(ValidationWarning(
                        field_name=f'territorial_configs.{territory}.{field}',
                        warning_message=f"Missing {field} for territory {territory}",
                        warning_type="missing_optional"
                    ))
        
        return warnings
    
    def _validate_physical_specifications(self, config: Dict[str, Any], parameter_status: Dict[str, str]) -> List[ValidationError]:
        """Validate physical book specifications"""
        errors = []
        
        # Validate page count
        page_count = config.get('page_count')
        if page_count is not None:
            try:
                page_count_val = int(page_count)
                if page_count_val <= 0:
                    errors.append(ValidationError(
                        field_name='page_count',
                        error_message="Page count must be positive",
                        error_type="range_error"
                    ))
                    parameter_status['page_count'] = "error"
                elif page_count_val < 24:
                    errors.append(ValidationError(
                        field_name='page_count',
                        error_message="Page count should be at least 24 for most POD services",
                        error_type="business_error"
                    ))
                    parameter_status['page_count'] = "warning"
                elif page_count_val > 2000:
                    errors.append(ValidationError(
                        field_name='page_count',
                        error_message="Page count exceeds typical POD limits",
                        error_type="business_error"
                    ))
                    parameter_status['page_count'] = "warning"
            except ValueError:
                errors.append(ValidationError(
                    field_name='page_count',
                    error_message=f"Invalid page count: {page_count}",
                    error_type="format_error"
                ))
                parameter_status['page_count'] = "error"
        
        # Validate trim size
        trim_size = config.get('trim_size', '')
        if trim_size:
            # Check if it's a standard size or custom format
            standard_sizes = ['5x8', '5.5x8.5', '6x9', '7x10', '8x10', '8.5x11']
            if trim_size not in standard_sizes and trim_size != 'Custom':
                # Check if it's a valid custom format (e.g., "6.5x9.25")
                if not re.match(r'^\d+(\.\d+)?x\d+(\.\d+)?$', trim_size):
                    errors.append(ValidationError(
                        field_name='trim_size',
                        error_message=f"Invalid trim size format: {trim_size}",
                        error_type="format_error",
                        suggested_values=standard_sizes
                    ))
                    parameter_status['trim_size'] = "error"
        
        # Validate binding type
        binding_type = config.get('binding_type', '')
        if binding_type:
            valid_bindings = ['paperback', 'hardcover', 'spiral', 'saddle-stitched']
            if binding_type.lower() not in [b.lower() for b in valid_bindings]:
                errors.append(ValidationError(
                    field_name='binding_type',
                    error_message=f"Invalid binding type: {binding_type}",
                    error_type="invalid_value",
                    suggested_values=valid_bindings
                ))
                parameter_status['binding_type'] = "error"
        
        return errors
    
    def _validate_parameter_dependencies(self, config: Dict[str, Any], parameter_status: Dict[str, str]) -> List[ValidationError]:
        """Validate parameter dependencies"""
        errors = []
        
        # Pipeline stage dependencies
        start_stage = config.get('start_stage')
        end_stage = config.get('end_stage')
        
        if start_stage is not None and end_stage is not None:
            try:
                start_val = int(start_stage)
                end_val = int(end_stage)
                
                if start_val > end_val:
                    errors.append(ValidationError(
                        field_name='end_stage',
                        error_message="End stage must be greater than or equal to start stage",
                        error_type="dependency_error"
                    ))
                    parameter_status['end_stage'] = "error"
                    
                if start_val < 1 or start_val > 4:
                    errors.append(ValidationError(
                        field_name='start_stage',
                        error_message="Start stage must be between 1 and 4",
                        error_type="range_error"
                    ))
                    parameter_status['start_stage'] = "error"
                    
                if end_val < 1 or end_val > 4:
                    errors.append(ValidationError(
                        field_name='end_stage',
                        error_message="End stage must be between 1 and 4",
                        error_type="range_error"
                    ))
                    parameter_status['end_stage'] = "error"
                    
            except ValueError:
                errors.append(ValidationError(
                    field_name='start_stage',
                    error_message="Invalid stage number",
                    error_type="format_error"
                ))
                parameter_status['start_stage'] = "error"
        
        # Book selection dependencies
        begin_with_book = config.get('begin_with_book')
        end_with_book = config.get('end_with_book')
        
        if begin_with_book is not None and end_with_book is not None:
            try:
                begin_val = int(begin_with_book)
                end_val = int(end_with_book)
                
                if end_val > 0 and begin_val > end_val:
                    errors.append(ValidationError(
                        field_name='end_with_book',
                        error_message="End book number must be greater than begin book number",
                        error_type="dependency_error"
                    ))
                    parameter_status['end_with_book'] = "error"
                    
            except ValueError:
                pass  # Will be caught by individual field validation
        
        return errors
    
    def validate_single_parameter(self, param_name: str, param_value: Any, config_context: Dict[str, Any] = None) -> ValidationResult:
        """Validate a single parameter in real-time"""
        errors = []
        warnings = []
        parameter_status = {param_name: "valid"}
        
        if config_context is None:
            config_context = {}
        
        # Create a temporary config with just this parameter
        temp_config = config_context.copy()
        temp_config[param_name] = param_value
        
        # Run relevant validation based on parameter name
        if param_name in ['publisher', 'imprint', 'lightning_source_account', 'language_code', 'model']:
            errors.extend(self._validate_required_fields({param_name: param_value}, parameter_status))
        
        if param_name in ['lightning_source_account', 'rendition_booktype', 'cover_submission_method', 'text_block_submission_method']:
            errors.extend(self._validate_lsi_parameters(temp_config, parameter_status))
        
        if param_name in ['us_wholesale_discount', 'uk_wholesale_discount', 'eu_wholesale_discount']:
            warnings.extend(self._validate_territorial_pricing(temp_config, parameter_status))
        
        if param_name in ['page_count', 'trim_size', 'binding_type']:
            errors.extend(self._validate_physical_specifications(temp_config, parameter_status))
        
        if param_name in ['start_stage', 'end_stage', 'begin_with_book', 'end_with_book']:
            errors.extend(self._validate_parameter_dependencies(temp_config, parameter_status))
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            parameter_status=parameter_status
        )
    
    def get_validation_suggestions(self, param_name: str, param_value: Any) -> List[str]:
        """Get validation suggestions for a parameter"""
        suggestions = []
        
        if param_name == 'rendition_booktype' and 'rendition_booktype' in self.lsi_valid_values:
            # Return fuzzy matches for rendition booktype
            valid_types = self.lsi_valid_values['rendition_booktype']
            if param_value:
                # Simple fuzzy matching
                param_lower = str(param_value).lower()
                matches = [vt for vt in valid_types if param_lower in vt.lower()]
                suggestions.extend(matches[:5])
        
        elif param_name == 'trim_size':
            suggestions = ['5x8', '5.5x8.5', '6x9', '7x10', '8x10', '8.5x11', 'Custom']
        
        elif param_name == 'binding_type':
            suggestions = ['paperback', 'hardcover', 'spiral', 'saddle-stitched']
        
        elif param_name in ['cover_submission_method', 'text_block_submission_method']:
            suggestions = ['FTP', 'Upload', 'Email']
        
        elif param_name == 'language_code':
            suggestions = ['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'jpn', 'kor', 'zho']
        
        elif param_name == 'audience':
            suggestions = ['General Adult', 'Young Adult', 'Children', 'Academic', 'Professional']
        
        return suggestions