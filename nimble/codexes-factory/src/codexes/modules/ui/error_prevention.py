"""
Comprehensive error prevention layer for UI robustness.

This module provides utilities for preventing common UI errors,
graceful degradation, and comprehensive None value protection.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Callable, Union
from functools import wraps
import streamlit as st

from .safety_patterns import (
    safe_getattr, safe_dict_get, safe_iteration, safe_len,
    validate_not_none, log_none_encounter
)

logger = logging.getLogger(__name__)


class UIErrorPrevention:
    """
    Comprehensive error prevention for UI components.
    
    Provides utilities for preventing common UI errors and
    implementing graceful degradation patterns.
    """
    
    def __init__(self):
        self.error_stats = {
            'none_values_prevented': 0,
            'attribute_errors_prevented': 0,
            'type_errors_prevented': 0,
            'key_errors_prevented': 0,
            'graceful_degradations': 0
        }
    
    def prevent_none_access(self, obj: Any, context: str = "unknown") -> Any:
        """
        Prevent None access errors by providing safe defaults.
        
        Args:
            obj: Object to validate (can be None)
            context: Context for logging
            
        Returns:
            Object or safe default if None
        """
        if obj is None:
            self.error_stats['none_values_prevented'] += 1
            log_none_encounter(context, 'object_access')
            return {}  # Safe default for most UI contexts
        return obj
    
    def safe_attribute_chain(self, obj: Any, *attributes: str, default: Any = None) -> Any:
        """
        Safely access a chain of attributes with None protection.
        
        Args:
            obj: Starting object
            *attributes: Chain of attribute names
            default: Default value if any step fails
            
        Returns:
            Final attribute value or default
        """
        current = obj
        for attr in attributes:
            if current is None:
                self.error_stats['attribute_errors_prevented'] += 1
                return default
            
            try:
                current = getattr(current, attr, None)
            except AttributeError:
                self.error_stats['attribute_errors_prevented'] += 1
                return default
        
        return current if current is not None else default
    
    def safe_nested_dict_get(self, data: Dict, *keys: str, default: Any = None) -> Any:
        """
        Safely access nested dictionary values.
        
        Args:
            data: Dictionary to access
            *keys: Chain of keys to access
            default: Default value if any step fails
            
        Returns:
            Nested value or default
        """
        current = data
        for key in keys:
            if not isinstance(current, dict) or current is None:
                self.error_stats['key_errors_prevented'] += 1
                return default
            
            current = current.get(key)
            if current is None:
                self.error_stats['key_errors_prevented'] += 1
                return default
        
        return current
    
    def safe_collection_operation(self, collection: Any, operation: Callable, 
                                default: Any = None, context: str = "collection_op") -> Any:
        """
        Safely perform operations on collections with None protection.
        
        Args:
            collection: Collection to operate on
            operation: Function to apply to collection
            default: Default value if operation fails
            context: Context for logging
            
        Returns:
            Operation result or default
        """
        if collection is None:
            self.error_stats['type_errors_prevented'] += 1
            log_none_encounter(context, 'collection')
            return default
        
        try:
            return operation(collection)
        except (TypeError, AttributeError, ValueError) as e:
            self.error_stats['type_errors_prevented'] += 1
            logger.warning(f"Collection operation failed in {context}: {e}")
            return default
    
    def graceful_degradation(self, primary_func: Callable, fallback_func: Callable,
                           context: str = "operation") -> Any:
        """
        Implement graceful degradation pattern.
        
        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails
            context: Context for logging
            
        Returns:
            Result from primary or fallback function
        """
        try:
            result = primary_func()
            if result is not None:
                return result
        except Exception as e:
            logger.warning(f"Primary function failed in {context}: {e}")
        
        try:
            self.error_stats['graceful_degradations'] += 1
            return fallback_func()
        except Exception as e:
            logger.error(f"Fallback function also failed in {context}: {e}")
            return None
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error prevention statistics."""
        return self.error_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset error prevention statistics."""
        self.error_stats = {
            'none_values_prevented': 0,
            'attribute_errors_prevented': 0,
            'type_errors_prevented': 0,
            'key_errors_prevented': 0,
            'graceful_degradations': 0
        }


class StreamlitErrorGuard:
    """
    Error guard specifically for Streamlit UI components.
    
    Provides decorators and utilities for protecting Streamlit
    widgets and operations from common errors.
    """
    
    def __init__(self):
        self.error_prevention = UIErrorPrevention()
    
    def safe_widget(self, widget_func: Callable, error_message: str = "Widget error") -> Callable:
        """
        Decorator to make Streamlit widgets safe from errors.
        
        Args:
            widget_func: Streamlit widget function
            error_message: Message to show on error
            
        Returns:
            Safe widget function
        """
        @wraps(widget_func)
        def wrapper(*args, **kwargs):
            try:
                # Ensure all arguments are not None where critical
                safe_args = []
                for arg in args:
                    if isinstance(arg, (list, dict)) and not arg:
                        # Provide safe defaults for empty collections
                        safe_args.append(arg if arg is not None else ([] if isinstance(arg, list) else {}))
                    else:
                        safe_args.append(arg)
                
                # Ensure critical kwargs have safe defaults
                if 'options' in kwargs and not kwargs['options']:
                    kwargs['options'] = ['']  # Safe default for selectbox
                
                if 'value' in kwargs and kwargs['value'] is None:
                    # Determine appropriate default based on widget type
                    if 'selectbox' in widget_func.__name__:
                        kwargs['value'] = kwargs.get('options', [''])[0] if kwargs.get('options') else ''
                    elif 'number_input' in widget_func.__name__:
                        kwargs['value'] = 0
                    elif 'checkbox' in widget_func.__name__:
                        kwargs['value'] = False
                    else:
                        kwargs['value'] = ''
                
                return widget_func(*safe_args, **kwargs)
                
            except Exception as e:
                logger.error(f"Widget error: {e}")
                st.error(f"{error_message}: {str(e)}")
                
                # Return safe default based on widget type
                if 'selectbox' in widget_func.__name__:
                    return ''
                elif 'number_input' in widget_func.__name__:
                    return 0
                elif 'checkbox' in widget_func.__name__:
                    return False
                elif 'multiselect' in widget_func.__name__:
                    return []
                else:
                    return ''
        
        return wrapper
    
    def safe_session_state_access(self, key: str, default: Any = None) -> Any:
        """
        Safely access Streamlit session state.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Session state value or default
        """
        try:
            if key in st.session_state:
                value = st.session_state[key]
                return value if value is not None else default
            return default
        except Exception as e:
            logger.warning(f"Session state access error for key '{key}': {e}")
            return default
    
    def safe_session_state_update(self, updates: Dict[str, Any]) -> bool:
        """
        Safely update Streamlit session state.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for key, value in updates.items():
                # Ensure we don't store None values that could cause issues
                if value is not None:
                    st.session_state[key] = value
                elif key not in st.session_state:
                    # Only set None if key doesn't exist and we need a placeholder
                    st.session_state[key] = self._get_safe_default_for_key(key)
            return True
        except Exception as e:
            logger.error(f"Session state update error: {e}")
            return False
    
    def _get_safe_default_for_key(self, key: str) -> Any:
        """Get safe default value based on key name patterns."""
        key_lower = key.lower()
        
        if 'config' in key_lower or 'settings' in key_lower:
            return {}
        elif 'list' in key_lower or 'items' in key_lower or 'genres' in key_lower:
            return []
        elif 'count' in key_lower or 'number' in key_lower or 'index' in key_lower:
            return 0
        elif 'enabled' in key_lower or 'flag' in key_lower or key_lower.startswith('is_'):
            return False
        else:
            return ''
    
    def display_error_safely(self, error: Exception, context: str = "operation") -> None:
        """
        Display error information safely without exposing sensitive details.
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
        # Log full error details for debugging
        logger.error(f"Error in {context}: {error}")
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        # Display user-friendly error message
        if isinstance(error, (AttributeError, TypeError)):
            st.error(f"⚠️ Data structure issue in {context}. Using default values.")
        elif isinstance(error, KeyError):
            st.error(f"⚠️ Missing configuration in {context}. Using defaults.")
        elif isinstance(error, ValueError):
            st.error(f"⚠️ Invalid data format in {context}. Please check inputs.")
        else:
            st.error(f"⚠️ Unexpected error in {context}. Operation completed with defaults.")


class GracefulDegradationManager:
    """
    Manager for implementing graceful degradation patterns.
    
    Provides utilities for handling missing data, failed operations,
    and providing meaningful fallbacks.
    """
    
    def __init__(self):
        self.degradation_stats = {
            'missing_data_handled': 0,
            'failed_operations_recovered': 0,
            'fallbacks_used': 0
        }
    
    def handle_missing_data(self, data: Any, data_type: str, context: str = "unknown") -> Any:
        """
        Handle missing or None data with appropriate fallbacks.
        
        Args:
            data: Data that might be None or missing
            data_type: Type of data expected ('config', 'list', 'string', etc.)
            context: Context for logging
            
        Returns:
            Data or appropriate fallback
        """
        if data is not None and data != '':
            return data
        
        self.degradation_stats['missing_data_handled'] += 1
        log_none_encounter(context, f'missing_{data_type}')
        
        # Provide appropriate fallback based on data type
        fallbacks = {
            'config': {},
            'list': [],
            'string': '',
            'number': 0,
            'boolean': False,
            'validation_results': {
                'is_valid': False,
                'errors': [],
                'warnings': ['Data validation skipped due to missing data']
            }
        }
        
        return fallbacks.get(data_type, None)
    
    def recover_from_operation_failure(self, operation_name: str, error: Exception,
                                     fallback_result: Any = None) -> Any:
        """
        Recover from failed operations with graceful fallbacks.
        
        Args:
            operation_name: Name of the failed operation
            error: Exception that occurred
            fallback_result: Result to return as fallback
            
        Returns:
            Fallback result
        """
        self.degradation_stats['failed_operations_recovered'] += 1
        logger.warning(f"Operation '{operation_name}' failed: {error}")
        
        # Provide operation-specific fallbacks
        operation_fallbacks = {
            'config_load': {},
            'validation': {'is_valid': False, 'errors': [str(error)], 'warnings': []},
            'scan_files': [],
            'generate_artifacts': {'status': 'failed', 'error': str(error)},
            'parse_data': {}
        }
        
        if fallback_result is not None:
            return fallback_result
        
        return operation_fallbacks.get(operation_name, None)
    
    def provide_user_feedback(self, issue_type: str, context: str, 
                            severity: str = "info") -> None:
        """
        Provide user-friendly feedback about degraded functionality.
        
        Args:
            issue_type: Type of issue encountered
            context: Context where issue occurred
            severity: Severity level (info, warning, error)
        """
        messages = {
            'missing_data': f"Some data is missing in {context}. Using default values.",
            'failed_operation': f"Operation in {context} encountered issues. Continuing with available data.",
            'partial_functionality': f"Limited functionality in {context} due to data issues.",
            'configuration_issue': f"Configuration problem in {context}. Using system defaults."
        }
        
        message = messages.get(issue_type, f"Issue in {context}. Continuing with fallback behavior.")
        
        if severity == "error":
            st.error(f"⚠️ {message}")
        elif severity == "warning":
            st.warning(f"⚠️ {message}")
        else:
            st.info(f"ℹ️ {message}")
    
    def get_degradation_stats(self) -> Dict[str, int]:
        """Get graceful degradation statistics."""
        return self.degradation_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset degradation statistics."""
        self.degradation_stats = {
            'missing_data_handled': 0,
            'failed_operations_recovered': 0,
            'fallbacks_used': 0
        }


# Global instances for easy access
ui_error_prevention = UIErrorPrevention()
streamlit_error_guard = StreamlitErrorGuard()
graceful_degradation_manager = GracefulDegradationManager()


# Convenience functions for common use cases
def safe_streamlit_widget(widget_func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute a Streamlit widget with error protection.
    
    Args:
        widget_func: Streamlit widget function
        *args: Widget arguments
        **kwargs: Widget keyword arguments
        
    Returns:
        Widget result or safe default
    """
    return streamlit_error_guard.safe_widget(widget_func)(*args, **kwargs)


def safe_session_access(key: str, default: Any = None) -> Any:
    """
    Safely access Streamlit session state.
    
    Args:
        key: Session state key
        default: Default value
        
    Returns:
        Session state value or default
    """
    return streamlit_error_guard.safe_session_state_access(key, default)


def safe_session_update(updates: Dict[str, Any]) -> bool:
    """
    Safely update Streamlit session state.
    
    Args:
        updates: Updates to apply
        
    Returns:
        True if successful
    """
    return streamlit_error_guard.safe_session_state_update(updates)


def handle_missing_data(data: Any, data_type: str, context: str = "unknown") -> Any:
    """
    Handle missing data with graceful degradation.
    
    Args:
        data: Data that might be missing
        data_type: Expected data type
        context: Context for logging
        
    Returns:
        Data or appropriate fallback
    """
    return graceful_degradation_manager.handle_missing_data(data, data_type, context)


def recover_from_failure(operation: str, error: Exception, fallback: Any = None) -> Any:
    """
    Recover from operation failure with graceful fallback.
    
    Args:
        operation: Name of failed operation
        error: Exception that occurred
        fallback: Fallback result
        
    Returns:
        Fallback result
    """
    return graceful_degradation_manager.recover_from_operation_failure(operation, error, fallback)