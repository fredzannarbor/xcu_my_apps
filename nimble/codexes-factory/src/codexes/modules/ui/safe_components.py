"""
Safe UI component wrappers for Streamlit.

This module provides safety wrappers for Streamlit widgets and components
that prevent None value errors and provide graceful degradation.
"""

import streamlit as st
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

from .safety_patterns import (
    safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
    validate_not_none, log_none_encounter
)
from .error_prevention import (
    safe_session_access, safe_session_update, handle_missing_data,
    graceful_degradation_manager
)

logger = logging.getLogger(__name__)


class SafeStreamlitComponents:
    """
    Wrapper for Streamlit widgets with comprehensive None protection.
    
    Provides safe versions of common Streamlit widgets that handle
    None values gracefully and provide appropriate defaults.
    """
    
    def __init__(self):
        self.widget_stats = {
            'widgets_created': 0,
            'none_values_handled': 0,
            'errors_prevented': 0
        }
    
    def safe_selectbox(self, label: str, options: Optional[List], 
                      value: Any = None, index: Optional[int] = None,
                      help: Optional[str] = None, key: Optional[str] = None,
                      **kwargs) -> Any:
        """
        Safe selectbox that handles None options and values.
        
        Args:
            label: Widget label
            options: List of options (can be None)
            value: Default value
            index: Default index
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Selected value or safe default
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure options is a valid list
            safe_options = list(safe_iteration(options)) if options else ['']
            if not safe_options:
                safe_options = ['']
                self.widget_stats['none_values_handled'] += 1
                log_none_encounter('safe_selectbox', 'empty_options')
            
            # Determine safe index
            safe_index = 0
            if index is not None and 0 <= index < len(safe_options):
                safe_index = index
            elif value is not None and value in safe_options:
                safe_index = safe_options.index(value)
            
            # Create widget with safe parameters
            return st.selectbox(
                label,
                options=safe_options,
                index=safe_index,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_selectbox: {e}")
            st.error(f"Widget error: {label}")
            return safe_options[0] if safe_options else ''
    
    def safe_multiselect(self, label: str, options: Optional[List],
                        default: Optional[List] = None, help: Optional[str] = None,
                        key: Optional[str] = None, **kwargs) -> List:
        """
        Safe multiselect that handles None options and defaults.
        
        Args:
            label: Widget label
            options: List of options (can be None)
            default: Default selections
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Selected values or empty list
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure options is a valid list
            safe_options = list(safe_iteration(options)) if options else []
            if not safe_options:
                self.widget_stats['none_values_handled'] += 1
                log_none_encounter('safe_multiselect', 'empty_options')
                return []
            
            # Ensure default is a valid list with valid options
            safe_default = []
            if default:
                safe_default = [item for item in safe_iteration(default) 
                              if item in safe_options]
            
            return st.multiselect(
                label,
                options=safe_options,
                default=safe_default,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_multiselect: {e}")
            st.error(f"Widget error: {label}")
            return []
    
    def safe_text_input(self, label: str, value: Any = None,
                       placeholder: Optional[str] = None, help: Optional[str] = None,
                       key: Optional[str] = None, **kwargs) -> str:
        """
        Safe text input that handles None values.
        
        Args:
            label: Widget label
            value: Default value
            placeholder: Placeholder text
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Input text or empty string
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure value is a string
            safe_value = str(value) if value is not None else ''
            safe_placeholder = str(placeholder) if placeholder is not None else None
            
            return st.text_input(
                label,
                value=safe_value,
                placeholder=safe_placeholder,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_text_input: {e}")
            st.error(f"Widget error: {label}")
            return ''
    
    def safe_text_area(self, label: str, value: Any = None, height: Optional[int] = None,
                      help: Optional[str] = None, key: Optional[str] = None,
                      **kwargs) -> str:
        """
        Safe text area that handles None values.
        
        Args:
            label: Widget label
            value: Default value
            height: Widget height
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Input text or empty string
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure value is a string
            safe_value = str(value) if value is not None else ''
            
            return st.text_area(
                label,
                value=safe_value,
                height=height,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_text_area: {e}")
            st.error(f"Widget error: {label}")
            return ''
    
    def safe_number_input(self, label: str, value: Optional[Union[int, float]] = None,
                         min_value: Optional[Union[int, float]] = None,
                         max_value: Optional[Union[int, float]] = None,
                         step: Optional[Union[int, float]] = None,
                         help: Optional[str] = None, key: Optional[str] = None,
                         **kwargs) -> Union[int, float]:
        """
        Safe number input that handles None values and bounds.
        
        Args:
            label: Widget label
            value: Default value
            min_value: Minimum value
            max_value: Maximum value
            step: Step size
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Input number or safe default
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Determine if we should use int or float
            use_int = (isinstance(step, int) if step is not None else True)
            
            # Set safe defaults
            if use_int:
                safe_value = int(value) if value is not None else (min_value or 0)
                safe_min = int(min_value) if min_value is not None else None
                safe_max = int(max_value) if max_value is not None else None
                safe_step = int(step) if step is not None else 1
            else:
                safe_value = float(value) if value is not None else float(min_value or 0)
                safe_min = float(min_value) if min_value is not None else None
                safe_max = float(max_value) if max_value is not None else None
                safe_step = float(step) if step is not None else 1.0
            
            # Ensure value is within bounds
            if safe_min is not None and safe_value < safe_min:
                safe_value = safe_min
            if safe_max is not None and safe_value > safe_max:
                safe_value = safe_max
            
            return st.number_input(
                label,
                value=safe_value,
                min_value=safe_min,
                max_value=safe_max,
                step=safe_step,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_number_input: {e}")
            st.error(f"Widget error: {label}")
            return 0
    
    def safe_checkbox(self, label: str, value: Optional[bool] = None,
                     help: Optional[str] = None, key: Optional[str] = None,
                     **kwargs) -> bool:
        """
        Safe checkbox that handles None values.
        
        Args:
            label: Widget label
            value: Default value
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Checkbox state or False
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure value is a boolean
            safe_value = bool(value) if value is not None else False
            
            return st.checkbox(
                label,
                value=safe_value,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_checkbox: {e}")
            st.error(f"Widget error: {label}")
            return False
    
    def safe_color_picker(self, label: str, value: Optional[str] = None,
                         help: Optional[str] = None, key: Optional[str] = None,
                         **kwargs) -> str:
        """
        Safe color picker that handles None values.
        
        Args:
            label: Widget label
            value: Default color value
            help: Help text
            key: Widget key
            **kwargs: Additional widget arguments
            
        Returns:
            Color value or default black
        """
        self.widget_stats['widgets_created'] += 1
        
        try:
            # Ensure value is a valid color string
            safe_value = str(value) if value is not None else '#000000'
            
            # Basic validation for hex color
            if not safe_value.startswith('#') or len(safe_value) != 7:
                safe_value = '#000000'
                self.widget_stats['none_values_handled'] += 1
            
            return st.color_picker(
                label,
                value=safe_value,
                help=help,
                key=key,
                **kwargs
            )
            
        except Exception as e:
            self.widget_stats['errors_prevented'] += 1
            logger.error(f"Error in safe_color_picker: {e}")
            st.error(f"Widget error: {label}")
            return '#000000'
    
    def get_widget_stats(self) -> Dict[str, int]:
        """Get widget creation and error statistics."""
        return self.widget_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset widget statistics."""
        self.widget_stats = {
            'widgets_created': 0,
            'none_values_handled': 0,
            'errors_prevented': 0
        }


class SafeDisplayManager:
    """
    Manager for safely displaying potentially None data.
    
    Provides utilities for displaying data with graceful handling
    of None values and missing information.
    """
    
    def __init__(self):
        self.display_stats = {
            'displays_rendered': 0,
            'none_values_displayed': 0,
            'fallbacks_used': 0
        }
    
    def safe_metric(self, label: str, value: Any, delta: Any = None,
                   help: Optional[str] = None, **kwargs) -> None:
        """
        Safely display a metric with None value handling.
        
        Args:
            label: Metric label
            value: Metric value (can be None)
            delta: Delta value (can be None)
            help: Help text
            **kwargs: Additional arguments
        """
        self.display_stats['displays_rendered'] += 1
        
        try:
            # Handle None value
            if value is None:
                safe_value = 'N/A'
                self.display_stats['none_values_displayed'] += 1
            elif isinstance(value, (int, float)):
                safe_value = value
            else:
                safe_value = str(value)
            
            # Handle None delta
            safe_delta = None
            if delta is not None:
                if isinstance(delta, (int, float)):
                    safe_delta = delta
                else:
                    safe_delta = str(delta)
            
            st.metric(
                label=label,
                value=safe_value,
                delta=safe_delta,
                help=help,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Error in safe_metric: {e}")
            st.error(f"Metric display error: {label}")
    
    def safe_write(self, *args, **kwargs) -> None:
        """
        Safely write content with None value handling.
        
        Args:
            *args: Content to write
            **kwargs: Additional arguments
        """
        self.display_stats['displays_rendered'] += 1
        
        try:
            # Filter out None values and convert to strings
            safe_args = []
            for arg in args:
                if arg is None:
                    safe_args.append('N/A')
                    self.display_stats['none_values_displayed'] += 1
                else:
                    safe_args.append(arg)
            
            if safe_args:
                st.write(*safe_args, **kwargs)
            else:
                st.write('No content to display')
                self.display_stats['fallbacks_used'] += 1
                
        except Exception as e:
            logger.error(f"Error in safe_write: {e}")
            st.error("Content display error")
    
    def safe_json(self, obj: Any, expanded: bool = True) -> None:
        """
        Safely display JSON with None value handling.
        
        Args:
            obj: Object to display as JSON
            expanded: Whether to expand the JSON display
        """
        self.display_stats['displays_rendered'] += 1
        
        try:
            if obj is None:
                st.json({'message': 'No data available'})
                self.display_stats['none_values_displayed'] += 1
            elif isinstance(obj, dict) and not obj:
                st.json({'message': 'Empty data'})
                self.display_stats['fallbacks_used'] += 1
            else:
                st.json(obj, expanded=expanded)
                
        except Exception as e:
            logger.error(f"Error in safe_json: {e}")
            st.error("JSON display error")
            st.json({'error': 'Could not display data'})
    
    def safe_table(self, data: Any) -> None:
        """
        Safely display table data with None value handling.
        
        Args:
            data: Data to display as table
        """
        self.display_stats['displays_rendered'] += 1
        
        try:
            if data is None:
                st.info("No table data available")
                self.display_stats['none_values_displayed'] += 1
            elif hasattr(data, '__len__') and len(data) == 0:
                st.info("Table is empty")
                self.display_stats['fallbacks_used'] += 1
            else:
                st.table(data)
                
        except Exception as e:
            logger.error(f"Error in safe_table: {e}")
            st.error("Table display error")
    
    def safe_success(self, message: Any) -> None:
        """Safely display success message."""
        safe_message = str(message) if message is not None else "Operation completed"
        st.success(safe_message)
    
    def safe_error(self, message: Any) -> None:
        """Safely display error message."""
        safe_message = str(message) if message is not None else "An error occurred"
        st.error(safe_message)
    
    def safe_warning(self, message: Any) -> None:
        """Safely display warning message."""
        safe_message = str(message) if message is not None else "Warning"
        st.warning(safe_message)
    
    def safe_info(self, message: Any) -> None:
        """Safely display info message."""
        safe_message = str(message) if message is not None else "Information"
        st.info(safe_message)
    
    def display_validation_results(self, validation_results: Any, 
                                 context: str = "validation") -> None:
        """
        Safely display validation results with comprehensive None handling.
        
        Args:
            validation_results: Validation results object
            context: Context for display
        """
        self.display_stats['displays_rendered'] += 1
        
        try:
            if not validate_not_none(validation_results, context, 'validation_results'):
                st.info("No validation results available")
                self.display_stats['none_values_displayed'] += 1
                return
            
            # Safe access to validation attributes
            is_valid = safe_getattr(validation_results, 'is_valid', False)
            errors = safe_getattr(validation_results, 'errors', [])
            warnings = safe_getattr(validation_results, 'warnings', [])
            
            # Display validation status
            if is_valid:
                st.success("✅ Validation passed")
            else:
                st.error("❌ Validation failed")
            
            # Display errors
            error_count = safe_len(errors)
            if error_count > 0:
                st.error(f"**Errors ({error_count}):**")
                for error in safe_iteration(errors):
                    if error:  # Additional None check
                        st.write(f"• {error}")
            
            # Display warnings
            warning_count = safe_len(warnings)
            if warning_count > 0:
                st.warning(f"**Warnings ({warning_count}):**")
                for warning in safe_iteration(warnings):
                    if warning:  # Additional None check
                        st.write(f"• {warning}")
            
            if error_count == 0 and warning_count == 0 and is_valid:
                st.info("No issues found")
                
        except Exception as e:
            logger.error(f"Error displaying validation results: {e}")
            st.error(f"Error displaying {context} results")
    
    def get_display_stats(self) -> Dict[str, int]:
        """Get display statistics."""
        return self.display_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset display statistics."""
        self.display_stats = {
            'displays_rendered': 0,
            'none_values_displayed': 0,
            'fallbacks_used': 0
        }


class SafeFormHandler:
    """
    Handler for safely managing form data with None value protection.
    
    Provides utilities for collecting, validating, and processing
    form data with comprehensive None value handling.
    """
    
    def __init__(self):
        self.form_stats = {
            'forms_processed': 0,
            'none_values_handled': 0,
            'validation_errors': 0
        }
    
    def collect_form_data(self, form_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely collect form data with None value protection.
        
        Args:
            form_fields: Dictionary of form field values
            
        Returns:
            Cleaned form data with None values handled
        """
        self.form_stats['forms_processed'] += 1
        
        if not validate_not_none(form_fields, 'form_collection', 'form_fields'):
            return {}
        
        cleaned_data = {}
        
        for field_name, field_value in (form_fields or {}).items():
            if field_value is None:
                # Provide appropriate default based on field name
                if 'list' in field_name.lower() or 'items' in field_name.lower():
                    cleaned_data[field_name] = []
                elif 'config' in field_name.lower() or 'settings' in field_name.lower():
                    cleaned_data[field_name] = {}
                elif 'count' in field_name.lower() or 'number' in field_name.lower():
                    cleaned_data[field_name] = 0
                elif 'enabled' in field_name.lower() or field_name.lower().startswith('is_'):
                    cleaned_data[field_name] = False
                else:
                    cleaned_data[field_name] = ''
                
                self.form_stats['none_values_handled'] += 1
                log_none_encounter('form_collection', field_name)
            else:
                cleaned_data[field_name] = field_value
        
        return cleaned_data
    
    def validate_form_data(self, form_data: Dict[str, Any], 
                          required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate form data and provide validation results.
        
        Args:
            form_data: Form data to validate
            required_fields: List of required field names
            
        Returns:
            Validation results with errors and warnings
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not validate_not_none(form_data, 'form_validation', 'form_data'):
            validation_result['is_valid'] = False
            validation_result['errors'].append('No form data provided')
            self.form_stats['validation_errors'] += 1
            return validation_result
        
        # Check required fields
        for field in safe_iteration(required_fields):
            if field not in form_data or not form_data[field]:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f'Required field missing: {field}')
                self.form_stats['validation_errors'] += 1
        
        # Check for empty values that might indicate issues
        for field_name, field_value in (form_data or {}).items():
            if field_value == '' and 'optional' not in field_name.lower():
                validation_result['warnings'].append(f'Empty value for field: {field_name}')
        
        return validation_result
    
    def process_form_submission(self, form_data: Dict[str, Any],
                              processor_func: Callable[[Dict[str, Any]], Any],
                              context: str = "form_processing") -> Any:
        """
        Safely process form submission with error handling.
        
        Args:
            form_data: Form data to process
            processor_func: Function to process the form data
            context: Context for error reporting
            
        Returns:
            Processing result or None on error
        """
        self.form_stats['forms_processed'] += 1
        
        try:
            # Clean form data first
            cleaned_data = self.collect_form_data(form_data)
            
            # Process with the provided function
            return processor_func(cleaned_data)
            
        except Exception as e:
            logger.error(f"Error processing form in {context}: {e}")
            st.error(f"Form processing error: {str(e)}")
            return None
    
    def get_form_stats(self) -> Dict[str, int]:
        """Get form processing statistics."""
        return self.form_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset form processing statistics."""
        self.form_stats = {
            'forms_processed': 0,
            'none_values_handled': 0,
            'validation_errors': 0
        }


# Global instances for easy access
safe_components = SafeStreamlitComponents()
safe_display = SafeDisplayManager()
safe_forms = SafeFormHandler()


# Convenience functions for common use cases
def create_safe_selectbox(label: str, options: Optional[List], **kwargs) -> Any:
    """Create a safe selectbox widget."""
    return safe_components.safe_selectbox(label, options, **kwargs)


def create_safe_multiselect(label: str, options: Optional[List], **kwargs) -> List:
    """Create a safe multiselect widget."""
    return safe_components.safe_multiselect(label, options, **kwargs)


def display_safe_metric(label: str, value: Any, **kwargs) -> None:
    """Display a metric safely."""
    safe_display.safe_metric(label, value, **kwargs)


def display_validation_safely(validation_results: Any, context: str = "validation") -> None:
    """Display validation results safely."""
    safe_display.display_validation_results(validation_results, context)


def process_form_safely(form_data: Dict[str, Any], processor: Callable) -> Any:
    """Process form data safely."""
    return safe_forms.process_form_submission(form_data, processor)