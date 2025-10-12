"""
Centralized logging configuration for Trillions of People.
Based on the codexes-factory logging pattern.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


class LoggingManager:
    """Centralized logging manager with environment-specific configurations."""

    def __init__(self):
        self._loggers = {}
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration based on environment."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        simple_formatter = logging.Formatter("%(levelname)s - %(message)s")

        # File handler for all logs
        file_handler = logging.FileHandler(log_dir / "trillions_of_people.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(simple_formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Reduce noise from external libraries
        self._configure_external_loggers()

    def _configure_external_loggers(self):
        """Configure external library loggers to reduce noise."""
        external_loggers = [
            "litellm",
            "httpx",
            "requests",
            "urllib3",
            "streamlit",
        ]

        for logger_name in external_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger for the given name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger

        return self._loggers[name]


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return get_logging_manager().get_logger(name)