"""
Logging filters for the Codexes Factory system.

This module provides custom logging filters to improve log readability
and reduce noise from verbose third-party libraries like LiteLLM.
"""

import logging
import os
from typing import Set, List


def log_success(logger: logging.Logger, message: str, level: int = logging.INFO) -> None:
    """
    Log a success message that will always appear regardless of logger level.
    
    This function temporarily lowers the logger and handler levels to ensure success messages
    containing ✅ or 📊 always appear in output.
    
    Args:
        logger: The logger to use
        message: The message to log (should contain ✅ or 📊)
        level: The logging level to use (default: INFO)
    """
    if '✅' in message or '📊' in message:
        # Store original levels for restoration
        original_logger_level = logger.level
        original_handler_levels = []
        
        # Also check parent loggers up the hierarchy
        current_logger = logger
        original_parent_levels = []
        
        try:
            # Set logger level to allow the message through
            logger.setLevel(min(level, logging.DEBUG))
            
            # Handle parent loggers in the hierarchy
            while current_logger.parent and current_logger.parent != current_logger:
                current_logger = current_logger.parent
                original_parent_levels.append((current_logger, current_logger.level))
                current_logger.setLevel(min(level, logging.DEBUG))
            
            # Handle all handlers in the logger hierarchy
            all_loggers = [logger] + [parent for parent, _ in original_parent_levels]
            for log in all_loggers:
                for handler in log.handlers:
                    original_handler_levels.append((handler, handler.level))
                    # Set handler level to allow the message through
                    handler.setLevel(min(level, logging.DEBUG))
            
            # Log the message
            logger.log(level, message)
            
        finally:
            # Restore all original levels
            logger.setLevel(original_logger_level)
            
            # Restore parent logger levels
            for parent_logger, original_level in original_parent_levels:
                parent_logger.setLevel(original_level)
            
            # Restore handler levels
            for handler, original_level in original_handler_levels:
                handler.setLevel(original_level)
    else:
        # For non-success messages, use normal logging
        logger.log(level, message)


class SuccessMessageFilter(logging.Filter):
    """
    Filter that ensures success messages with ✅ always appear in output.
    
    This filter allows all messages containing the success icon ✅ to pass through
    regardless of the logger's level configuration.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to always allow success messages through.
        
        Args:
            record: The log record to evaluate
            
        Returns:
            True if the record should be logged, False otherwise
        """
        try:
            message = record.getMessage()
            # Always allow messages with success icon or statistics icon
            if '✅' in message or '📊' in message:
                return True
        except Exception:
            # If we can't get the message, use default behavior
            pass
        
        # For all other messages, use default filtering behavior
        return True


class SuccessAwareHandler(logging.StreamHandler):
    """
    A custom handler that ensures success messages always get through
    regardless of handler level settings.
    """
    
    def handle(self, record: logging.LogRecord) -> bool:
        """
        Handle a record, but always allow success messages through regardless of level.
        
        This overrides the base handle() method to bypass level checking for success messages.
        
        Args:
            record: The log record to handle
            
        Returns:
            True if the record was handled
        """
        # Check if this is a success message
        try:
            message = record.getMessage()
            is_success_message = '✅' in message or '📊' in message
        except Exception:
            is_success_message = False
        
        # If it's a success message, bypass level checking
        if is_success_message:
            # Apply filters
            if self.filter(record):
                self.acquire()
                try:
                    self.emit(record)
                finally:
                    self.release()
            return True
        else:
            # For non-success messages, use normal handling with level check
            return super().handle(record)


class LiteLLMFilter(logging.Filter):
    """
    Custom logging filter to suppress verbose LiteLLM messages while preserving important ones.
    
    This filter suppresses common LiteLLM noise including:
    - Cost calculation messages
    - Completion wrapper messages  
    - Utility messages
    - Debug information
    
    Critical errors and warnings are always allowed through.
    Debug mode can be enabled via environment variable to show all messages.
    """
    
    def __init__(self, debug_mode: bool = None):
        """
        Initialize the LiteLLM filter.
        
        Args:
            debug_mode: If True, allows all LiteLLM messages through.
                       If None, checks LITELLM_DEBUG environment variable.
        """
        super().__init__()
        
        # Determine debug mode
        if debug_mode is None:
            debug_mode = os.getenv('LITELLM_DEBUG', '').lower() in ('true', '1', 'yes', 'on')
        
        self.debug_mode = debug_mode
        
        # Message patterns to filter out (case-insensitive)
        self.filtered_patterns: Set[str] = {
            # Cost calculation messages
            'cost calculation',
            'calculating cost',
            'completion cost',
            'token cost',
            'usage cost',
            'pricing calculation',
            'selected model name for cost calculation',
            
            # Completion wrapper messages
            'completion wrapper',
            'wrapper function',
            'litellm completion',
            'completion call',
            'completed call, calling success_handler',
            'wrapper: completed call',
            
            # Utility and debug messages
            'litellm utils',
            'litellm debug',
            'litellm info',
            'model mapping',
            'provider mapping',
            'api key validation',
            'request headers',
            'response headers',
            'token counting',
            'model validation',
            'litellm completion() model=',
            'provider =',
            
            # Verbose operational messages
            'making request to',
            'received response from',
            'processing request',
            'request completed',
            'response processed',
            
            # Configuration messages
            'setting model',
            'configuring provider',
            'loading configuration',
            'initializing client',
            'initializing proxy',
        }
        
        # Logger names to filter (exact matches and prefixes)
        self.filtered_loggers: Set[str] = {
            'litellm',
            'litellm.main',
            'litellm.utils',
            'litellm.cost_calculator',
            'litellm.completion',
            'litellm.router',
            'litellm.proxy',
            'LiteLLM',  # Capital version
            'LiteLLM Proxy',
            'LiteLLM Router',
        }
        
        # Always allow these critical message patterns through
        self.critical_patterns: Set[str] = {
            'error',
            'exception',
            'failed',
            'failure',
            'timeout',
            'rate limit',
            'quota exceeded',
            'authentication',
            'unauthorized',
            'forbidden',
            'not found',
            'service unavailable',
            'internal server error',
            'bad gateway',
            'gateway timeout',
            'success',  # Always show success messages
            '✅',       # Always show success icon messages
            '📊',       # Always show statistics icon messages
        }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on LiteLLM message patterns.
        
        Args:
            record: The log record to evaluate
            
        Returns:
            True if the record should be logged, False if it should be filtered out
        """
        # In debug mode, allow all messages through
        if self.debug_mode:
            return True
        
        # Check if this is from a LiteLLM logger
        if not self._is_litellm_logger(record.name):
            return True
        
        # Always allow ERROR and CRITICAL level messages
        if record.levelno >= logging.ERROR:
            return True
        
        # Get the message content
        try:
            message = record.getMessage().lower()
        except Exception:
            # If we can't get the message, allow it through to be safe
            return True
        
        # Always allow critical messages through regardless of level
        if self._contains_critical_pattern(message):
            return True
        
        # Filter out INFO and DEBUG messages that match filtered patterns
        if record.levelno <= logging.INFO:
            if self._contains_filtered_pattern(message):
                return False
        
        # Allow WARNING and above, or messages that don't match filtered patterns
        return True
    
    def _is_litellm_logger(self, logger_name: str) -> bool:
        """Check if the logger name is from LiteLLM."""
        logger_name_lower = logger_name.lower()
        
        # Check exact matches
        if logger_name_lower in self.filtered_loggers:
            return True
        
        # Check prefixes
        for filtered_logger in self.filtered_loggers:
            if logger_name_lower.startswith(filtered_logger + '.'):
                return True
        
        return False
    
    def _contains_filtered_pattern(self, message: str) -> bool:
        """Check if the message contains any filtered patterns."""
        for pattern in self.filtered_patterns:
            if pattern in message:
                return True
        return False
    
    def _contains_critical_pattern(self, message: str) -> bool:
        """Check if the message contains any critical patterns that should always be shown."""
        return any(pattern in message for pattern in self.critical_patterns)
    
    def add_filtered_pattern(self, pattern: str) -> None:
        """
        Add a new pattern to filter out.
        
        Args:
            pattern: The pattern to add (case-insensitive)
        """
        self.filtered_patterns.add(pattern.lower())
    
    def remove_filtered_pattern(self, pattern: str) -> None:
        """
        Remove a pattern from the filter list.
        
        Args:
            pattern: The pattern to remove (case-insensitive)
        """
        self.filtered_patterns.discard(pattern.lower())
    
    def add_critical_pattern(self, pattern: str) -> None:
        """
        Add a new critical pattern that should always be shown.
        
        Args:
            pattern: The pattern to add (case-insensitive)
        """
        self.critical_patterns.add(pattern.lower())
    
    def get_filtered_patterns(self) -> List[str]:
        """Get a list of all filtered patterns."""
        return sorted(list(self.filtered_patterns))
    
    def get_critical_patterns(self) -> List[str]:
        """Get a list of all critical patterns."""
        return sorted(list(self.critical_patterns))
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug_mode
    
    def set_debug_mode(self, enabled: bool) -> None:
        """
        Enable or disable debug mode.
        
        Args:
            enabled: True to enable debug mode, False to disable
        """
        self.debug_mode = enabled


# Convenience function to create and configure the filter
def create_litellm_filter(debug_mode: bool = None) -> LiteLLMFilter:
    """
    Create a configured LiteLLM filter.
    
    Args:
        debug_mode: If True, allows all LiteLLM messages through.
                   If None, checks LITELLM_DEBUG environment variable.
    
    Returns:
        Configured LiteLLMFilter instance
    """
    return LiteLLMFilter(debug_mode=debug_mode)


# Convenience function to apply the filter to a logger
def apply_litellm_filter(logger_name: str = None, debug_mode: bool = None) -> LiteLLMFilter:
    """
    Apply the LiteLLM filter to a logger.
    
    Args:
        logger_name: Name of the logger to apply filter to. If None, applies to root logger.
        debug_mode: If True, allows all LiteLLM messages through.
                   If None, checks LITELLM_DEBUG environment variable.
    
    Returns:
        The created filter instance
    """
    filter_instance = create_litellm_filter(debug_mode=debug_mode)
    
    if logger_name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(logger_name)
    
    logger.addFilter(filter_instance)
    return filter_instance