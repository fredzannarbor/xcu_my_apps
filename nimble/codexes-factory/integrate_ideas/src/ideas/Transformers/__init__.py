# ideas/transformers/__init__.py

"""
Transformer module for converting between different idea representations.

This module provides functionality to transform Ideas into BookIdeas with support
for various transformation patterns including one-to-one, one-to-many, and
many-to-many relationships.

Main Components:
    - IdeaTransformer: Core transformer class for idea conversion
    - transform_utils: Utility functions for transformation operations
"""

from typing import Optional
import logging

# Import core components
from src.ideas.Transformers.idea_transformer import IdeaTransformer

# Set up module-level logger
logger = logging.getLogger(__name__)

# Version info
__version__ = '0.1.0'

# Public API
__all__ = [
    'IdeaTransformer',
]


# Convenience function to create a transformer with default settings
def create_transformer(logger: Optional[logging.Logger] = None) -> IdeaTransformer:
    """
    Create a new IdeaTransformer instance with optional custom logger.

    Args:
        logger: Optional custom logger for the transformer

    Returns:
        IdeaTransformer: Configured transformer instance
    """
    return IdeaTransformer(logger=logger)


# Optional: Add any module initialization code here
def _initialize_module():
    """Initialize any required module-level resources"""
    logger.debug("Initializing transformers module")


_initialize_module()
