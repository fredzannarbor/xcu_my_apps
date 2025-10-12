import logging
import sys
import os
import uuid
from datetime import datetime

def setup_logging(level="INFO"):
    """
    Sets up logging using the LoggingConfigManager.
    
    This function maintains backward compatibility while using the new
    centralized logging configuration system.
    """
    try:
        from .logging_config import setup_application_logging, get_logging_manager
        
        # Check if logging is already configured to prevent duplicate setup
        logging_manager = get_logging_manager()
        if logging_manager.is_configured():
            # Just update the level if needed
            current_level = getattr(logging, level.upper(), logging.INFO)
            logging.getLogger().setLevel(current_level)
            return
        
        # Set up logging with the new system
        setup_application_logging()
        
        # Apply LiteLLM filtering by default
        logging_manager.apply_litellm_filter()
        
        # Set the requested level
        current_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(current_level)
        
        logging.info(f"🚀 Logging configured using LoggingConfigManager. Level: {level}")
        
    except ImportError:
        # Fallback to the old logging setup if LoggingConfigManager is not available
        _setup_logging_fallback(level)

def _setup_logging_fallback(level="INFO"):
    """Fallback logging setup for backward compatibility."""
    # This check prevents adding handlers multiple times in Streamlit's reruns
    if logging.root.handlers and not isinstance(logging.root.handlers[0], logging.NullHandler):
        logging.getLogger().setLevel(getattr(logging, level.upper(), logging.INFO))
        return

    # To ensure logs are always written to the project's log directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"codexes_run_{timestamp}.log")
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers to prevent duplicate messages
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s')

    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create file handler
    fh = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    logging.info(f"🚀 Logging configured (fallback). Level: {level}. File: {log_filename}")


def read_markdown_file(markdown_file):
    """Reads a markdown file and returns its content."""
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Markdown file not found: {markdown_file}")
        return f"Content for '{os.path.basename(markdown_file)}' not found."
    except Exception as e:
        logging.error(f"Error reading markdown file {markdown_file}: {e}", exc_info=True)
        return "Error reading file."

def generate_shortuuid():
    new_id = uuid.uuid4().hex[:12]
    return new_id