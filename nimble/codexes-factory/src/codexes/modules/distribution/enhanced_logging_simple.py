#!/usr/bin/env python3

"""
Simple Enhanced Logging

A simplified version of enhanced logging for testing purposes.
"""

import logging
import sys
from pathlib import Path

def setup_logging(debug_mode: bool = False, log_dir: str = "logs"):
    """Set up simple logging for the application."""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.DEBUG if debug_mode else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path / "test.log")
        ]
    )
    
    # Create loggers
    app_logger = logging.getLogger("lsi_csv_generator")
    validation_logger = logging.getLogger("validation")
    field_completion_logger = logging.getLogger("field_completion")
    batch_processing_logger = logging.getLogger("batch_processing")
    
    return {
        "app": app_logger,
        "validation": validation_logger,
        "field_completion": field_completion_logger,
        "batch_processing": batch_processing_logger
    }