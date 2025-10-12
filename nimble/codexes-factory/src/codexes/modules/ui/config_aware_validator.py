"""
Configuration-Aware Validation Framework
Extends the base validator to consider configuration selection context
"""

import logging
from typing import Dict, Any, List, Optional
from .config_validator import ConfigurationValidator
from .configuration_manager import ValidationResult, ValidationError, ValidationWarning
from .config_synchronizer import ConfigurationSynchronizer

logger = logging.getLogger(__name__)

class ConfigurationAwareValidator(ConfigurationValidator):
    """Enhanced validator that considers configuration selection context"""
    
    def __init__(self):
        super().__init__()
        self.config_sync = ConfigurationSynchronizer()
    
    def validate_with_config_context(
        self, 
        form_data: Dict[str, Any],
        config_selection: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """Validate considering both form data and configuration selection"""
        try:
            # Get configuration selection if not provided
            if config_selection is None:
                config_selection = self.config_sync.get_configuration_values()
            
            # Merge configuration selection into validation context
            validation_data = form_data.copy()
            
            # Use configuration values for empty required fields
            config_field_mapping = {
                'publisher': 'publisher',
                'imprint': 'imprint',
                'tranche': 'tranche'
            }
            
            for form_field, config_field in config_field_mapping.items():
                form_value = validation_data.get(form_field)
                config_value = config_selection.get(config_field, '')
                
                # Use configuration value if form value is empty
                if not form_value and config_value:
                    validation_data[form_field] = config_value
                    logger.debug(f"Using configuration value for {form_field}: {config_value}")
            
            # Run validation on merged data
            result = self.validate_configuration(validation_data)
            
            # Enhance error messages with configuration context
            enhanced_errors = []
            for error in result.errors:
                enhanced_error = self._enhance_error_with_config_context(
                    error, form_data, config_selection
                )
                enhanced_errors.append(enhanced_error)
            
            # Create enhanced result
            enhanced_result = ValidationResult(
                is_valid=result.is_valid,
                errors=enhanced_errors,
                warnings=result.warnings,
                parameter_status=result.parameter_status
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Configuration-aware validation failed: {e}")
            # Fallback to standard validation
            return self.validate_configuration(form_data)
    
    def _enhance_error_with_config_context(
        self, 
        error: ValidationError, 
        form_data: Dict[str, Any],
        config_selection: Dict[str, str]
    ) -> ValidationError:
        """Enhance validation error with configuration context"""
        try:
            field_name = error.field_name
            
            # Check if this is a configuration-related field
            if field_name in ['publisher', 'imprint', 'tranche']:
                form_value = form_data.get(field_name, '')
                config_value = config_selection.get(field_name, '')
                
                # If form is empty but config has value, suggest using configuration
                if not form_value and config_value:
                    enhanced_message = f"{error.error_message}. Available from configuration: '{config_value}'"
                    suggested_fix = f"This value is available from your configuration selection above"
                    
                    return ConfigAwareValidationError(
                        field_name=field_name,
                        error_message=enhanced_message,
                        error_type=error.error_type,
                        suggested_values=error.suggested_values,
                        config_context={
                            'config_value': config_value,
                            'form_value': form_value,
                            'suggested_fix': suggested_fix
                        }
                    )
                
                # If both form and config are empty, suggest configuration selection
                elif not form_value and not config_value:
                    enhanced_message = f"{error.error_message}. Please select a {field_name} in the Configuration Selection section above"
                    
                    return ConfigAwareValidationError(
                        field_name=field_name,
                        error_message=enhanced_message,
                        error_type=error.error_type,
                        suggested_values=error.suggested_values,
                        config_context={
                            'config_value': config_value,
                            'form_value': form_value,
                            'suggested_fix': f"Select a {field_name} in the Configuration Selection section"
                        }
                    )
            
            # Return original error if no enhancement needed
            return error
            
        except Exception as e:
            logger.error(f"Error enhancing validation error: {e}")
            return error
    
    def validate_configuration_sync_status(self) -> ValidationResult:
        """Validate the current configuration synchronization status"""
        try:
            sync_status = self.config_sync.get_sync_status()
            errors = []
            warnings = []
            parameter_status = {}
            
            for field_name, status in sync_status.items():
                if not status.value:
                    # Field is empty
                    if field_name in ['publisher', 'imprint']:
                        errors.append(ValidationError(
                            field_name=field_name,
                            error_message=f"Required field '{field_name}' is missing or empty",
                            error_type="required_field"
                        ))
                        parameter_status[field_name] = "error"
                    else:
                        parameter_status[field_name] = "valid"
                elif status.is_overridden:
                    # Field has user override
                    warnings.append(ValidationWarning(
                        field_name=field_name,
                        warning_message=f"Field '{field_name}' has been manually overridden from configuration value",
                        warning_type="user_override"
                    ))
                    parameter_status[field_name] = "warning"
                else:
                    # Field is synchronized with configuration
                    parameter_status[field_name] = "valid"
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                parameter_status=parameter_status
            )
            
        except Exception as e:
            logger.error(f"Configuration sync status validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field_name="sync_status",
                    error_message=f"Configuration sync validation failed: {e}",
                    error_type="system_error"
                )],
                warnings=[],
                parameter_status={}
            )

class ConfigAwareValidationError(ValidationError):
    """Validation error with configuration context"""
    
    def __init__(
        self, 
        field_name: str, 
        error_message: str, 
        error_type: str,
        suggested_values: Optional[List[str]] = None,
        config_context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(field_name, error_message, error_type, suggested_values)
        self.config_context = config_context or {}
    
    def get_suggested_fix(self) -> str:
        """Get context-aware fix suggestion"""
        return self.config_context.get('suggested_fix', f"Provide a value for {self.field_name}")
    
    def get_config_value(self) -> str:
        """Get the configuration value for this field"""
        return self.config_context.get('config_value', '')
    
    def get_form_value(self) -> str:
        """Get the form value for this field"""
        return self.config_context.get('form_value', '')
    
    def is_config_available(self) -> bool:
        """Check if configuration value is available for this field"""
        return bool(self.config_context.get('config_value'))

class ConfigAwareValidationWarning(ValidationWarning):
    """Validation warning with configuration context"""
    
    def __init__(
        self, 
        field_name: str, 
        warning_message: str, 
        warning_type: str,
        config_context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(field_name, warning_message, warning_type)
        self.config_context = config_context or {}