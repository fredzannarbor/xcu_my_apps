"""
Series-Aware Description Processor for LSI Field Mapping

This module processes short descriptions to include series context
when applicable, replacing "This book" with "This book in the {series} series".
"""

from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


class SeriesDescriptionProcessor:
    """Processes descriptions to include series context when applicable."""
    
    def __init__(self):
        """Initialize the description processor."""
        pass
        
    def process_description(self, description: str, series_name: Optional[str]) -> str:
        """
        Process description to include series reference when applicable.
        
        Args:
            description: Original description text
            series_name: Name of the series (if any)
            
        Returns:
            Processed description with series context
        """
        if not description:
            return description or ""
            
        # If no valid series name, return original description
        if not self.has_series_context(series_name):
            logger.debug("No valid series context, returning original description")
            return description
            
        # Look for "This book" patterns and replace with series context
        processed = self._replace_this_book_patterns(description, series_name)
        
        if processed != description:
            logger.debug(f"Updated description with series context: '{series_name}'")
            
        return processed
        
    def has_series_context(self, series_name: Optional[str]) -> bool:
        """
        Check if series name is valid and should be included.
        
        Args:
            series_name: Series name to validate
            
        Returns:
            True if series name is valid and should be included
        """
        if not series_name:
            return False
            
        # Clean and validate series name
        cleaned_name = str(series_name).strip()
        
        # Must be non-empty after cleaning
        if not cleaned_name:
            return False
            
        # Must be reasonable length (not just whitespace or very short)
        if len(cleaned_name) < 2:
            return False
            
        # Exclude generic or placeholder names
        excluded_names = {
            'n/a', 'na', 'none', 'null', 'undefined', 'unknown',
            'series', 'book series', 'untitled', 'tbd', 'tba'
        }
        
        if cleaned_name.lower() in excluded_names:
            return False
            
        return True
        
    def _replace_this_book_patterns(self, description: str, series_name: str) -> str:
        """
        Replace "This book" patterns with series-aware versions.
        
        Args:
            description: Original description
            series_name: Name of the series
            
        Returns:
            Description with replaced patterns
        """
        # Clean series name for insertion
        clean_series = series_name.strip()
        
        # Define replacement patterns
        patterns = [
            # "This book" at start of sentence
            (r'\bThis book\b', f'This book in the {clean_series} series'),
            # "this book" (lowercase)
            (r'\bthis book\b', f'this book in the {clean_series} series'),
        ]
        
        processed = description
        
        for pattern, replacement in patterns:
            # Use word boundaries to avoid partial matches
            if re.search(pattern, processed):
                processed = re.sub(pattern, replacement, processed)
                logger.debug(f"Replaced pattern '{pattern}' with '{replacement}'")
                
        return processed
        
    def extract_series_from_description(self, description: str) -> Optional[str]:
        """
        Extract series name from description if it contains series references.
        
        Args:
            description: Description text to analyze
            
        Returns:
            Extracted series name or None
        """
        if not description:
            return None
            
        # Look for common series patterns
        patterns = [
            r'in the ([^.]+) series',
            r'part of the ([^.]+) series',
            r'from the ([^.]+) series',
            r'([^.]+) series book',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                series_name = match.group(1).strip()
                if self.has_series_context(series_name):
                    logger.debug(f"Extracted series name from description: '{series_name}'")
                    return series_name
                    
        return None
        
    def validate_processed_description(self, description: str, series_name: Optional[str]) -> bool:
        """
        Validate that a processed description correctly includes series context.
        
        Args:
            description: Processed description
            series_name: Expected series name
            
        Returns:
            True if description correctly includes series context
        """
        if not self.has_series_context(series_name):
            # If no series, description should not contain series references
            return 'series' not in description.lower()
            
        # If series exists, check that it's properly referenced
        series_pattern = f'in the {re.escape(series_name.strip())} series'
        return bool(re.search(series_pattern, description, re.IGNORECASE))
        
    def get_series_aware_replacement(self, original_phrase: str, series_name: str) -> str:
        """
        Get series-aware replacement for a specific phrase.
        
        Args:
            original_phrase: Original phrase to replace
            series_name: Series name to include
            
        Returns:
            Series-aware replacement phrase
        """
        clean_series = series_name.strip()
        
        # Handle different phrase patterns
        phrase_lower = original_phrase.lower().strip()
        
        if phrase_lower == 'this book':
            return f'this book in the {clean_series} series'
        elif phrase_lower == 'This book':
            return f'This book in the {clean_series} series'
        elif phrase_lower.startswith('this book'):
            # Handle cases like "This book offers..."
            return original_phrase.replace('This book', f'This book in the {clean_series} series', 1)
        elif phrase_lower.startswith('this book'):
            return original_phrase.replace('this book', f'this book in the {clean_series} series', 1)
        else:
            # For other phrases, just append series context
            return f'{original_phrase} in the {clean_series} series'