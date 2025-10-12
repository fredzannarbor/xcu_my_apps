"""
Core safety pattern library for UI robustness.

This module provides autofix-resistant patterns for safe data access
that prevent None value errors and maintain stability through code formatting.
"""

from typing import Any, Dict, List, Optional, Union, Callable
import logging

logger = logging.getLogger(__name__)

# Default value registry - immutable defaults to prevent accidental modification
DEFAULT_VALUES = {
    'dict': {},
    'list': [],
    'str': '',
    'int': 0,
    'float': 0.0,
    'bool': False,
    'set': set(),
    'tuple': ()
}

# Attribute defaults for common UI data structures
ATTRIBUTE_DEFAULTS = {
    'design_specs': {
        'typography': {},
        'color_palette': {},
        'trim_sizes': [],
        'layout_preferences': {},
        'visual_elements': {},
        'style_guide': {}
    },
    'publishing_info': {
        'primary_genres': [],
        'target_audience': '',
        'publication_details': {},
        'distribution_channels': [],
        'marketing_keywords': []
    },
    'branding_info': {
        'brand_values': [],
        'visual_identity': {},
        'messaging': {},
        'tone_guidelines': {},
        'brand_colors': []
    },
    'validation_results': {
        'errors': [],
        'warnings': [],
        'info': [],
        'is_valid': False
    }
}


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Safely get attribute from object with default fallback.
    
    This pattern is autofix-resistant as it uses standard Python getattr().
    
    Args:
        obj: Object to get attribute from (can be None)
        attr: Attribute name
        default: Default value if attribute doesn't exist or obj is None
        
    Returns:
        Attribute value or default
    """
    if obj is None:
        return default
    return getattr(obj, attr, default)


def safe_dict_get(dictionary: Optional[Dict], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with None protection.
    
    Uses (dict or {}).get() pattern that autofix preserves.
    
    Args:
        dictionary: Dictionary to access (can be None)
        key: Key to look up
        default: Default value if key doesn't exist or dict is None
        
    Returns:
        Dictionary value or default
    """
    return (dictionary or {}).get(key, default)


def safe_list_access(collection: Optional[List], index: int, default: Any = None) -> Any:
    """
    Safely access list element with bounds checking.
    
    Args:
        collection: List to access (can be None)
        index: Index to access
        default: Default value if index out of bounds or list is None
        
    Returns:
        List element or default
    """
    if not collection or index >= len(collection) or index < 0:
        return default
    return collection[index]


def safe_iteration(collection: Optional[Union[List, tuple, set]]) -> Union[List, tuple, set]:
    """
    Safely prepare collection for iteration.
    
    Uses (collection or []) pattern that autofix preserves.
    
    Args:
        collection: Collection to iterate over (can be None)
        
    Returns:
        Collection or empty list if None
    """
    return collection or []


def safe_len(collection: Optional[Union[List, Dict, str, tuple, set]]) -> int:
    """
    Safely get length of collection.
    
    Args:
        collection: Collection to measure (can be None)
        
    Returns:
        Length of collection or 0 if None
    """
    return len(collection or [])


def safe_join(collection: Optional[List[str]], separator: str = ', ') -> str:
    """
    Safely join string collection with separator.
    
    Args:
        collection: Collection of strings to join (can be None)
        separator: String to use as separator
        
    Returns:
        Joined string or empty string if collection is None/empty
    """
    if not collection:
        return ''
    return separator.join(str(item) for item in collection if item is not None)


def safe_string_format(template: str, **kwargs) -> str:
    """
    Safely format string with None value protection.
    
    Args:
        template: String template to format
        **kwargs: Format arguments (None values converted to empty strings)
        
    Returns:
        Formatted string with None values handled
    """
    safe_kwargs = {k: (v if v is not None else '') for k, v in kwargs.items()}
    try:
        return template.format(**safe_kwargs)
    except (KeyError, ValueError) as e:
        logger.warning(f"String formatting failed: {e}, returning template")
        return template


def safe_max(collection: Optional[List[Union[int, float]]], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely get maximum value from numeric collection.
    
    Args:
        collection: Collection of numbers (can be None)
        default: Default value if collection is None/empty
        
    Returns:
        Maximum value or default
    """
    if not collection:
        return default
    try:
        return max(collection)
    except (TypeError, ValueError):
        return default


def safe_min(collection: Optional[List[Union[int, float]]], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely get minimum value from numeric collection.
    
    Args:
        collection: Collection of numbers (can be None)
        default: Default value if collection is None/empty
        
    Returns:
        Minimum value or default
    """
    if not collection:
        return default
    try:
        return min(collection)
    except (TypeError, ValueError):
        return default


def safe_sum(collection: Optional[List[Union[int, float]]], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely sum numeric collection.
    
    Args:
        collection: Collection of numbers (can be None)
        default: Default value if collection is None/empty
        
    Returns:
        Sum of values or default
    """
    if not collection:
        return default
    try:
        return sum(collection)
    except (TypeError, ValueError):
        return default


def safe_filter(collection: Optional[List], predicate: Callable[[Any], bool]) -> List:
    """
    Safely filter collection with predicate.
    
    Args:
        collection: Collection to filter (can be None)
        predicate: Function to test each element
        
    Returns:
        Filtered list or empty list if collection is None
    """
    if not collection:
        return []
    try:
        return [item for item in collection if predicate(item)]
    except (TypeError, AttributeError):
        return []


def safe_map(collection: Optional[List], func: Callable[[Any], Any]) -> List:
    """
    Safely map function over collection.
    
    Args:
        collection: Collection to map over (can be None)
        func: Function to apply to each element
        
    Returns:
        Mapped list or empty list if collection is None
    """
    if not collection:
        return []
    try:
        return [func(item) for item in collection]
    except (TypeError, AttributeError):
        return []


def get_default_for_type(value_type: str) -> Any:
    """
    Get appropriate default value for given type.
    
    Args:
        value_type: Type name as string
        
    Returns:
        Default value for the type
    """
    return DEFAULT_VALUES.get(value_type, None)


def get_attribute_default(category: str, attribute: str) -> Any:
    """
    Get default value for specific attribute category.
    
    Args:
        category: Category name (e.g., 'design_specs')
        attribute: Attribute name
        
    Returns:
        Default value for the attribute
    """
    category_defaults = ATTRIBUTE_DEFAULTS.get(category, {})
    return category_defaults.get(attribute, None)


def log_none_encounter(context: str, attribute: str) -> None:
    """
    Log when None values are encountered for monitoring.
    
    Args:
        context: Context where None was encountered
        attribute: Attribute that was None
    """
    logger.warning(f"None value encountered in {context} for attribute: {attribute}")


def validate_not_none(value: Any, context: str, attribute: str) -> bool:
    """
    Validate that value is not None and log if it is.
    
    Args:
        value: Value to check
        context: Context for logging
        attribute: Attribute name for logging
        
    Returns:
        True if value is not None, False otherwise
    """
    if value is None:
        log_none_encounter(context, attribute)
        return False
    return True