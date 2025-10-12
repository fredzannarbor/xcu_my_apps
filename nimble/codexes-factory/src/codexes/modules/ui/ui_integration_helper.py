"""
UI Integration Helper for applying safety patterns across all UI pages.

This module provides utilities for easily integrating safety patterns
into existing Streamlit UI components without major refactoring.
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Union, Callable
import logging

from .safety_patterns import (
    safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
    validate_not_none, log_none_encounter
)
from .safe_components import safe_components, safe_display
from .error_prevention import handle_missing_data, safe_session_access, safe_session_update
from .monitoring import ui_monitor

logger = logging.getLogger(__name__)


class UIIntegrationHelper:
    """
    Helper class for integrating safety patterns into existing UI pages.
    
    Provides drop-in replacements for common Streamlit widgets and operations
    that automatically apply safety patterns.
    """
    
    def __init__(self):
        self.integration_stats = {
            'widgets_wrapped': 0,
            'errors_prevented': 0,
            'none_values_handled': 0
        }
    
    def safe_selectbox(self, label: str, options: Optional[List], **kwargs) -> Any:
        """Drop-in replacement for st.selectbox with safety patterns."""
        self.integration_stats['widgets_wrapped'] += 1
        
        if safe_components:
            return safe_components.safe_selectbox(label, options, **kwargs)
        else:
            # Fallback implementation
            safe_options = list(safe_iteration(options)) if options else ['']
            if not safe_options:
                safe_options = ['']
                self.integration_stats['none_values_handled'] += 1
            
            # Safe index handling
            index = kwargs.get('index', 0)
            if index >= len(safe_options):
                index = 0
            
            kwargs['index'] = index
            return st.selectbox(label, options=safe_options, **kwargs)
    
    def safe_multiselect(self, label: str, options: Optional[List], **kwargs) -> List:
        """Drop-in replacement for st.multiselect with safety patterns."""
        self.integration_stats['widgets_wrapped'] += 1
        
        if safe_components:
            return safe_components.safe_multiselect(label, options, **kwargs)
        else:
            # Fallback implementation
            safe_options = list(safe_iteration(options)) if options else []
            if not safe_options:
                self.integration_stats['none_values_handled'] += 1
                return []
            
            # Safe default handling
            default = kwargs.get('default', [])
            safe_default = [item for item in safe_iteration(default) if item in safe_options]
            kwargs['default'] = safe_default
            
            return st.multiselect(label, options=safe_options, **kwargs)
    
    def safe_text_input(self, label: str, value: Any = None, **kwargs) -> str:
        """Drop-in replacement for st.text_input with safety patterns."""
        self.integration_stats['widgets_wrapped'] += 1
        
        if safe_components:
            return safe_components.safe_text_input(label, value, **kwargs)
        else:
            # Fallback implementation
            safe_value = str(value) if value is not None else ''
            return st.text_input(label, value=safe_value, **kwargs)
    
    def safe_number_input(self, label: str, value: Optional[Union[int, float]] = None, **kwargs) -> Union[int, float]:
        """Drop-in replacement for st.number_input with safety patterns."""
        self.integration_stats['widgets_wrapped'] += 1
        
        if safe_components:
            return safe_components.safe_number_input(label, value, **kwargs)
        else:
            # Fallback implementation
            min_value = kwargs.get('min_value', 0)
            safe_value = value if value is not None else min_value
            return st.number_input(label, value=safe_value, **kwargs)
    
    def safe_checkbox(self, label: str, value: Optional[bool] = None, **kwargs) -> bool:
        """Drop-in replacement for st.checkbox with safety patterns."""
        self.integration_stats['widgets_wrapped'] += 1
        
        if safe_components:
            return safe_components.safe_checkbox(label, value, **kwargs)
        else:
            # Fallback implementation
            safe_value = bool(value) if value is not None else False
            return st.checkbox(label, value=safe_value, **kwargs)
    
    def safe_session_state_access(self, key: str, default: Any = None) -> Any:
        """Safely access session state with None protection."""
        try:
            if key in st.session_state:
                value = st.session_state[key]
                if value is None:
                    self.integration_stats['none_values_handled'] += 1
                    return default
                return value
            return default
        except Exception as e:
            self.integration_stats['errors_prevented'] += 1
            logger.warning(f"Session state access error for key '{key}': {e}")
            return default
    
    def safe_session_state_update(self, key: str, value: Any) -> bool:
        """Safely update session state with error handling."""
        try:
            st.session_state[key] = value
            return True
        except Exception as e:
            self.integration_stats['errors_prevented'] += 1
            logger.error(f"Session state update error for key '{key}': {e}")
            return False
    
    def safe_display_metric(self, label: str, value: Any, **kwargs) -> None:
        """Safely display metrics with None protection."""
        if safe_display:
            safe_display.safe_metric(label, value, **kwargs)
        else:
            # Fallback implementation
            safe_value = value if value is not None else 'N/A'
            st.metric(label, safe_value, **kwargs)
    
    def safe_display_dataframe(self, data: Any, **kwargs) -> None:
        """Safely display dataframe with None protection."""
        if data is None:
            st.info("No data available")
            self.integration_stats['none_values_handled'] += 1
        elif hasattr(data, '__len__') and len(data) == 0:
            st.info("No data to display")
        else:
            st.dataframe(data, **kwargs)
    
    def safe_display_json(self, data: Any, **kwargs) -> None:
        """Safely display JSON with None protection."""
        if safe_display:
            safe_display.safe_json(data, **kwargs)
        else:
            # Fallback implementation
            if data is None:
                st.json({'message': 'No data available'})
                self.integration_stats['none_values_handled'] += 1
            else:
                st.json(data, **kwargs)
    
    def safe_form_data_collection(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Safely collect and clean form data."""
        if not validate_not_none(form_data, 'form_collection', 'form_data'):
            return {}
        
        cleaned_data = {}
        for key, value in (form_data or {}).items():
            if value is None:
                # Provide appropriate defaults based on key patterns
                if 'list' in key.lower() or 'items' in key.lower():
                    cleaned_data[key] = []
                elif 'config' in key.lower() or 'settings' in key.lower():
                    cleaned_data[key] = {}
                elif 'count' in key.lower() or 'number' in key.lower():
                    cleaned_data[key] = 0
                elif 'enabled' in key.lower() or key.lower().startswith('is_'):
                    cleaned_data[key] = False
                else:
                    cleaned_data[key] = ''
                
                self.integration_stats['none_values_handled'] += 1
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def get_integration_stats(self) -> Dict[str, int]:
        """Get integration statistics."""
        return self.integration_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset integration statistics."""
        self.integration_stats = {
            'widgets_wrapped': 0,
            'errors_prevented': 0,
            'none_values_handled': 0
        }


# Global instance for easy access
ui_helper = UIIntegrationHelper()


# Convenience functions that can be imported and used as drop-in replacements
def safe_selectbox(label: str, options: Optional[List], **kwargs) -> Any:
    """Safe selectbox - drop-in replacement for st.selectbox."""
    return ui_helper.safe_selectbox(label, options, **kwargs)


def safe_multiselect(label: str, options: Optional[List], **kwargs) -> List:
    """Safe multiselect - drop-in replacement for st.multiselect."""
    return ui_helper.safe_multiselect(label, options, **kwargs)


def safe_text_input(label: str, value: Any = None, **kwargs) -> str:
    """Safe text input - drop-in replacement for st.text_input."""
    return ui_helper.safe_text_input(label, value, **kwargs)


def safe_number_input(label: str, value: Optional[Union[int, float]] = None, **kwargs) -> Union[int, float]:
    """Safe number input - drop-in replacement for st.number_input."""
    return ui_helper.safe_number_input(label, value, **kwargs)


def safe_checkbox(label: str, value: Optional[bool] = None, **kwargs) -> bool:
    """Safe checkbox - drop-in replacement for st.checkbox."""
    return ui_helper.safe_checkbox(label, value, **kwargs)


def safe_session_get(key: str, default: Any = None) -> Any:
    """Safe session state access."""
    return ui_helper.safe_session_state_access(key, default)


def safe_session_set(key: str, value: Any) -> bool:
    """Safe session state update."""
    return ui_helper.safe_session_state_update(key, value)


def safe_metric(label: str, value: Any, **kwargs) -> None:
    """Safe metric display."""
    ui_helper.safe_display_metric(label, value, **kwargs)


def safe_dataframe(data: Any, **kwargs) -> None:
    """Safe dataframe display."""
    ui_helper.safe_display_dataframe(data, **kwargs)


def safe_json(data: Any, **kwargs) -> None:
    """Safe JSON display."""
    ui_helper.safe_display_json(data, **kwargs)


# Integration decorator for automatic safety pattern application
def with_ui_safety(func: Callable) -> Callable:
    """
    Decorator to automatically apply UI safety patterns to a function.
    
    This decorator wraps UI functions to provide automatic error handling
    and None value protection.
    """
    def wrapper(*args, **kwargs):
        try:
            # Record function usage
            ui_monitor.record_safety_pattern_usage('with_ui_safety', func.__name__)
            
            # Execute function with error protection
            result = func(*args, **kwargs)
            
            # Handle None results
            if result is None:
                ui_monitor.record_none_encounter(func.__name__, 'function_result')
                return handle_missing_data(None, 'dict', func.__name__)
            
            return result
            
        except Exception as e:
            ui_monitor.record_error_prevention(type(e).__name__, func.__name__)
            logger.error(f"Error in {func.__name__}: {e}")
            
            # Provide graceful fallback
            if 'display' in func.__name__.lower() or 'render' in func.__name__.lower():
                st.error(f"Error in {func.__name__}: {str(e)}")
                return None
            else:
                return handle_missing_data(None, 'dict', func.__name__)
    
    return wrapper


# Context manager for UI safety
class UISafety:
    """
    Context manager for applying UI safety patterns to a block of code.
    
    Usage:
        with UIStrategy():
            # UI code here will be protected
            result = some_ui_operation()
    """
    
    def __init__(self, context_name: str = "ui_operation"):
        self.context_name = context_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        ui_monitor.record_safety_pattern_usage('ui_safety_context', self.context_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            ui_monitor.record_performance_metric(self.context_name, duration)
        
        if exc_type is not None:
            ui_monitor.record_error_prevention(exc_type.__name__, self.context_name)
            logger.error(f"Error in UI safety context {self.context_name}: {exc_val}")
            
            # Don't suppress the exception, just log it
            return False
        
        return True