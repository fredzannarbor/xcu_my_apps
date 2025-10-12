"""
Logging filters and utilities for LLM operations.
"""

import logging
from typing import Any


def log_success(logger: logging.Logger, message: str) -> None:
    """
    Log a success message with INFO level.
    
    This function ensures success messages are always visible
    by using INFO level logging.
    
    Args:
        logger: Logger instance to use
        message: Success message to log
    """
    logger.info(message)


def log_error(logger: logging.Logger, message: str, exc_info: Any = None) -> None:
    """
    Log an error message with ERROR level.
    
    Args:
        logger: Logger instance to use
        message: Error message to log
        exc_info: Optional exception info
    """
    logger.error(message, exc_info=exc_info)


def log_warning(logger: logging.Logger, message: str) -> None:
    """
    Log a warning message with WARNING level.
    
    Args:
        logger: Logger instance to use
        message: Warning message to log
    """
    logger.warning(message)