# ideas/transformers/transform_utils.py

from typing import Dict, Any
import re


def sanitize_title(title: str) -> str:
    """Clean and format a title for use in BookIdea"""
    return " ".join(title.split()).strip()


def extract_themes(text: str) -> list:
    """Extract potential themes from text content"""
    # Implementation can be enhanced based on specific requirements
    return []


def validate_transformation(source: Dict[str, Any], target: Dict[str, Any]) -> bool:
    """Validate that all required fields were properly transformed"""
    required_fields = ['title', 'description_of_idea']
    return all(field in target and target[field] for field in required_fields)
