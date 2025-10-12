"""
ValidationManager - Handles configuration validation without triggering UI refresh loops
"""

import streamlit as st
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: list
    warnings: list
    parameter_status: dict
    validation_timestamp: float

class ValidationManager:
    """Handles configuration validation without triggering UI refresh loops"""
    
    def __init__(self):
        self.validation_timeout = 5.0  # 5 second timeout for validation
        self.result_cache_ttl = 10.0   # 10 second result cache
        
        # Initialize session state if needed
        if 'validation_manager_state' not in st.session_state:
            st.session_state.validation_manager_state = {
                'validation_in_progress': False,
                'last_validation_timestamp': 0.0,
                'cached_results': {},
                'validation_count': 0,
                'prevent_loops': False
            }
    
    def validate_configuration_safe(self, config: Dict[str, Any]) -> Optional[ValidationResult]:
        """
        Validate configuration without causing rerun loops
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            ValidationResult or None if validation is blocked
        """
        current_time = time.time()
        state = st.session_state.validation_manager_state
        
        # Prevent multiple simultaneous validations
        if state['validation_in_progress']:
            logger.warning("Validation already in progress, skipping")
            return None
        
        # Prevent validation loops
        if state['prevent_loops']:
            logger.warning("Validation loops detected, blocking validation")
            return None
        
        # Check if we have a recent cached result
        config_hash = self._hash_config(config)
        if config_hash in state['cached_results']:
            cached_result, cache_time = state['cached_results'][config_hash]
            if current_time - cache_time < self.result_cache_ttl:
                logger.debug("Returning cached validation result")
                return cached_result
        
        # Set validation in progress
        state['validation_in_progress'] = True
        state['last_validation_timestamp'] = current_time
        state['validation_count'] += 1
        
        try:
            logger.info(f"Starting configuration validation (attempt #{state['validation_count']})")
            
            # Perform actual validation
            result = self._perform_validation(config)
            
            # Cache the result
            state['cached_results'][config_hash] = (result, current_time)
            
            # Clean old cache entries
            self._clean_cache(current_time)
            
            logger.info(f"Validation completed: {'VALID' if result.is_valid else 'INVALID'} "
                       f"({len(result.errors)} errors, {len(result.warnings)} warnings)")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            # Return a failed validation result
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                parameter_status={},
                validation_timestamp=current_time
            )
        
        finally:
            # Always clear the in-progress flag
            state['validation_in_progress'] = False
    
    def display_validation_results_stable(self, result: ValidationResult) -> None:
        """
        Display validation results without triggering reruns
        
        Args:
            result: ValidationResult to display
        """
        if not result:
            st.info("No validation results available")
            return
        
        # Prevent rerun loops during result display
        state = st.session_state.validation_manager_state
        state['prevent_loops'] = True
        
        try:
            # Display overall status
            if result.is_valid:
                st.success("✅ Configuration is valid and ready for execution")
            else:
                st.error(f"❌ Configuration has {len(result.errors)} error(s) that must be fixed")
            
            # Display validation timestamp
            validation_time = datetime.fromtimestamp(result.validation_timestamp)
            st.caption(f"Validated at: {validation_time.strftime('%H:%M:%S')}")
            
            # Display errors
            if result.errors:
                with st.expander("❌ Errors", expanded=True):
                    for i, error in enumerate(result.errors, 1):
                        st.error(f"{i}. {error}")
            
            # Display warnings
            if result.warnings:
                with st.expander("⚠️ Warnings", expanded=False):
                    for i, warning in enumerate(result.warnings, 1):
                        st.warning(f"{i}. {warning}")
            
            # Display parameter status summary
            if result.parameter_status:
                self._display_parameter_status(result.parameter_status)
        
        finally:
            # Re-enable validation after a short delay
            # Use a callback to clear the prevention flag
            if 'validation_clear_timer' not in st.session_state:
                st.session_state.validation_clear_timer = time.time() + 1.0
    
    def can_validate(self) -> bool:
        """
        Check if validation can be performed
        
        Returns:
            bool: True if validation is allowed
        """
        state = st.session_state.validation_manager_state
        current_time = time.time()
        
        # Clear prevention flag if enough time has passed
        if (state.get('prevent_loops', False) and 
            hasattr(st.session_state, 'validation_clear_timer') and
            current_time > st.session_state.validation_clear_timer):
            state['prevent_loops'] = False
            delattr(st.session_state, 'validation_clear_timer')
        
        return not state['validation_in_progress'] and not state.get('prevent_loops', False)
    
    def reset_validation_state(self):
        """Reset validation state to allow new validations"""
        state = st.session_state.validation_manager_state
        state['validation_in_progress'] = False
        state['prevent_loops'] = False
        if hasattr(st.session_state, 'validation_clear_timer'):
            delattr(st.session_state, 'validation_clear_timer')
        logger.info("Validation state reset")
    
    def clear_cache(self):
        """Clear validation result cache"""
        state = st.session_state.validation_manager_state
        state['cached_results'].clear()
        logger.info("Validation cache cleared")
    
    def _perform_validation(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Perform the actual configuration validation
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        parameter_status = {}
        
        # Basic validation checks
        required_fields = ['imprint', 'publisher']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
                parameter_status[field] = 'error'
            else:
                parameter_status[field] = 'valid'
        
        # Validate imprint exists
        imprint = config.get('imprint')
        if imprint:
            from pathlib import Path
            imprint_path = Path(f"configs/imprints/{imprint}.json")
            if not imprint_path.exists():
                errors.append(f"Imprint configuration file not found: {imprint_path}")
                parameter_status['imprint'] = 'error'
        
        # Validate publisher exists
        publisher = config.get('publisher')
        if publisher:
            from pathlib import Path
            publisher_path = Path(f"configs/publishers/{publisher}.json")
            if not publisher_path.exists():
                errors.append(f"Publisher configuration file not found: {publisher_path}")
                parameter_status['publisher'] = 'error'
        
        # Validate model settings
        model = config.get('model')
        if model:
            valid_models = [
                "gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro",
                "openai/gpt-4o", "openai/gpt-4-turbo",
                "anthropic/claude-3-opus", "anthropic/claude-3-sonnet", "anthropic/claude-3-haiku"
            ]
            if model not in valid_models:
                warnings.append(f"Model '{model}' may not be supported")
                parameter_status['model'] = 'warning'
            else:
                parameter_status['model'] = 'valid'
        
        # Validate numeric ranges
        max_books = config.get('max_books')
        if max_books is not None:
            try:
                max_books_int = int(max_books)
                if max_books_int <= 0:
                    errors.append("max_books must be greater than 0")
                    parameter_status['max_books'] = 'error'
                elif max_books_int > 100:
                    warnings.append("max_books is very high, this may take a long time")
                    parameter_status['max_books'] = 'warning'
                else:
                    parameter_status['max_books'] = 'valid'
            except (ValueError, TypeError):
                errors.append("max_books must be a valid integer")
                parameter_status['max_books'] = 'error'
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            parameter_status=parameter_status,
            validation_timestamp=time.time()
        )
    
    def _display_parameter_status(self, parameter_status: Dict[str, str]):
        """Display parameter status summary"""
        if not parameter_status:
            return
        
        # Group parameters by status
        status_groups = {'valid': [], 'warning': [], 'error': []}
        for param, status in parameter_status.items():
            if status in status_groups:
                status_groups[status].append(param)
        
        # Display in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status_groups['valid']:
                st.success(f"✅ Valid ({len(status_groups['valid'])})")
                for param in status_groups['valid'][:5]:  # Show first 5
                    st.write(f"• {param}")
                if len(status_groups['valid']) > 5:
                    st.caption(f"... and {len(status_groups['valid']) - 5} more")
        
        with col2:
            if status_groups['warning']:
                st.warning(f"⚠️ Warnings ({len(status_groups['warning'])})")
                for param in status_groups['warning']:
                    st.write(f"• {param}")
        
        with col3:
            if status_groups['error']:
                st.error(f"❌ Errors ({len(status_groups['error'])})")
                for param in status_groups['error']:
                    st.write(f"• {param}")
    
    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Create a hash of the configuration for caching"""
        import hashlib
        import json
        
        # Create a stable string representation
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _clean_cache(self, current_time: float):
        """Clean old entries from the validation cache"""
        state = st.session_state.validation_manager_state
        cache = state['cached_results']
        
        # Remove entries older than TTL
        expired_keys = []
        for key, (result, cache_time) in cache.items():
            if current_time - cache_time > self.result_cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired validation cache entries")