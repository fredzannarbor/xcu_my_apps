"""
Shared logging utility for xcu_my_apps workspace.

Provides centralized logging configuration for all applications.
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
    file_logging: bool = True
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)
        log_dir: Directory for log files. If None, uses default location
        level: Logging level (default: INFO)
        console: Whether to log to console (default: True)
        file_logging: Whether to log to file (default: True)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Format for log messages
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler
        if file_logging:
            # Determine log directory
            if log_dir is None:
                log_dir = Path("/Users/fred/xcu_my_apps/all_applications_runner/logs")

            # Create subdirectory for this app if needed
            app_name = name.split('.')[0] if '.' in name else name
            app_log_dir = log_dir / app_name
            app_log_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with date
            log_file = app_log_dir / f"{app_name}_{datetime.now().strftime('%Y%m%d')}.log"

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def configure_root_logger(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO
) -> None:
    """
    Configure the root logger for the entire application.

    Args:
        log_dir: Directory for log files
        level: Logging level
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path("/Users/fred/xcu_my_apps/all_applications_runner/logs")

    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
