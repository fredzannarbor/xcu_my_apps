#!/usr/bin/env python3
"""
Text Formatter for LSI Fields

This module provides text formatting, validation, and truncation utilities
for LSI CSV fields that have specific length and format requirements.
"""

import re
import html
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextValidationResult:
    """Result of text validation."""
    is_valid: bool
    message: str
    suggested_text: Optional[str] = None
    original_length: int = 0
    final_length: int = 0


class LSITextFormatter:
    """Formats and validates text for LSI field requirements."""
    
    # LSI field length limits
    FIELD_LIMITS = {
        'short_description': 350,
        'long_description': 4000,
        'annotation': 4000,
        'summary_short': 350,
        'summary_long': 4000,
        'keywords': 255,
        'title': 255,
        'subtitle': 255,
        'series_name': 255,
        'contributor_bio': 2000,
        'publisher_note': 1000,
        'back_cover_text': 2000
    }
    
    def __init__(self):
        """Initialize the text formatter."""
        pass
    
    def validate_field_length(self, field_name: str, text: str) -> TextValidationResult:
        """
        Validate text length against LSI field requirements.
        
        Args:
            field_name: Name of the LSI field
            text: Text to validate
            
        Returns:
            TextValidationResult with validation status and suggestions
        """
        if not text:
            return TextValidationResult(
                is_valid=True,
                message="Empty text is valid",
                original_length=0,
                final_length=0
            )
        
        # Clean the text first
        cleaned_text = self.clean_text(text)
        original_length = len(text)
        cleaned_length = len(cleaned_text)
        
        # Get field limit
        max_length = self.FIELD_LIMITS.get(field_name, 1000)
        
        if cleaned_length <= max_length:
            return TextValidationResult(
                is_valid=True,
                message=f"Text length valid ({cleaned_length}/{max_length} characters)",
                suggested_text=cleaned_text if cleaned_text != text else None,
                original_length=original_length,
                final_length=cleaned_length
            )
        else:
            # Generate truncated version
            truncated = self.intelligent_truncate(cleaned_text, max_length)
            return TextValidationResult(
                is_valid=False,
                message=f"Text too long ({cleaned_length}/{max_length} characters)",
                suggested_text=truncated,
                original_length=original_length,
                final_length=len(truncated)
            )
    
    def clean_text(self, text: str) -> str:
        """
        Clean text for LSI submission.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text suitable for LSI fields
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix common punctuation issues
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Ensure space after sentence endings
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)  # Multiple dots to ellipsis
        text = re.sub(r'[!]{2,}', '!', text)    # Multiple exclamations to single
        text = re.sub(r'[?]{2,}', '?', text)    # Multiple questions to single
        
        return text
    
    def intelligent_truncate(self, text: str, max_length: int) -> str:
        """
        Intelligently truncate text at natural boundaries.
        
        Args:
            text: Text to truncate
            max_length: Maximum allowed length
            
        Returns:
            Truncated text ending at a natural boundary
        """
        if len(text) <= max_length:
            return text
        
        # Try to truncate at sentence boundary
        truncated = self._truncate_at_sentence(text, max_length)
        if truncated:
            return truncated
        
        # Try to truncate at word boundary
        truncated = self._truncate_at_word(text, max_length)
        if truncated:
            return truncated
        
        # Last resort: hard truncate with ellipsis
        return text[:max_length-3] + "..."
    
    def _truncate_at_sentence(self, text: str, max_length: int) -> Optional[str]:
        """Truncate at the last complete sentence that fits."""
        if len(text) <= max_length:
            return text
        
        # Find sentence endings
        sentence_endings = []
        for match in re.finditer(r'[.!?]\s+', text):
            end_pos = match.end()
            if end_pos <= max_length:
                sentence_endings.append(end_pos)
        
        if sentence_endings:
            # Use the last sentence ending that fits
            truncate_pos = sentence_endings[-1]
            return text[:truncate_pos].rstrip()
        
        return None
    
    def _truncate_at_word(self, text: str, max_length: int) -> Optional[str]:
        """Truncate at the last complete word that fits."""
        if len(text) <= max_length:
            return text
        
        # Find the last space before max_length
        truncate_pos = text.rfind(' ', 0, max_length - 3)  # Leave room for ellipsis
        
        if truncate_pos > max_length * 0.8:  # Only if we don't lose too much text
            return text[:truncate_pos] + "..."
        
        return None
    
    def format_keywords(self, keywords: str) -> str:
        """
        Format keywords for LSI submission.
        
        Args:
            keywords: Raw keywords string
            
        Returns:
            Formatted keywords string
        """
        if not keywords:
            return ""
        
        # Split on various separators
        keyword_list = re.split(r'[;,\n\r]+', keywords)
        
        # Clean each keyword
        cleaned_keywords = []
        for keyword in keyword_list:
            keyword = keyword.strip()
            if keyword:
                # Remove quotes
                keyword = keyword.strip('"\'')
                # Normalize case (title case for multi-word, lowercase for single word)
                if ' ' in keyword:
                    keyword = keyword.title()
                else:
                    keyword = keyword.lower()
                cleaned_keywords.append(keyword)
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in cleaned_keywords:
            if keyword.lower() not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword.lower())
        
        # Join with semicolons (LSI standard)
        result = '; '.join(unique_keywords)
        
        # Validate length
        if len(result) > self.FIELD_LIMITS.get('keywords', 255):
            # Truncate by removing keywords from the end
            while len(result) > self.FIELD_LIMITS.get('keywords', 255) and '; ' in result:
                result = result.rsplit('; ', 1)[0]
        
        return result
    
    def format_html_annotation(self, text: str) -> str:
        """
        Format text for HTML annotation field with proper tags.
        
        Args:
            text: Raw text to format
            
        Returns:
            HTML-formatted text for LSI annotation field
        """
        if not text:
            return ""
        
        # Clean the text first
        text = self.clean_text(text)
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Format each paragraph
        formatted_paragraphs = []
        for i, paragraph in enumerate(paragraphs):
            if i == 0:
                # First paragraph gets bold italic treatment
                formatted_paragraphs.append(f"<p><b><i>{paragraph}</i></b></p>")
            else:
                formatted_paragraphs.append(f"<p>{paragraph}</p>")
        
        result = ''.join(formatted_paragraphs)
        
        # Validate length
        if len(result) > self.FIELD_LIMITS.get('annotation', 4000):
            # Truncate while preserving HTML structure
            result = self._truncate_html(result, self.FIELD_LIMITS.get('annotation', 4000))
        
        return result
    
    def _truncate_html(self, html_text: str, max_length: int) -> str:
        """Truncate HTML text while preserving tag structure."""
        if len(html_text) <= max_length:
            return html_text
        
        # Simple approach: remove paragraphs from the end until we fit
        paragraphs = re.findall(r'<p>.*?</p>', html_text, re.DOTALL)
        
        result = ""
        for paragraph in paragraphs:
            if len(result + paragraph) <= max_length:
                result += paragraph
            else:
                break
        
        return result if result else html_text[:max_length-10] + "...</p>"
    
    def validate_and_format_field(self, field_name: str, text: str) -> Dict[str, Any]:
        """
        Validate and format a field for LSI submission.
        
        Args:
            field_name: Name of the LSI field
            text: Text to validate and format
            
        Returns:
            Dictionary with validation results and formatted text
        """
        if not text:
            return {
                'is_valid': True,
                'formatted_text': '',
                'message': 'Empty field',
                'original_length': 0,
                'final_length': 0
            }
        
        # Special handling for different field types
        if field_name == 'keywords':
            formatted_text = self.format_keywords(text)
        elif field_name == 'annotation':
            formatted_text = self.format_html_annotation(text)
        else:
            formatted_text = self.clean_text(text)
        
        # Validate length
        validation_result = self.validate_field_length(field_name, formatted_text)
        
        return {
            'is_valid': validation_result.is_valid,
            'formatted_text': validation_result.suggested_text or formatted_text,
            'message': validation_result.message,
            'original_length': len(text),
            'final_length': validation_result.final_length,
            'truncated': validation_result.suggested_text is not None
        }


# Global formatter instance
_text_formatter = None

def get_text_formatter() -> LSITextFormatter:
    """Get the global text formatter instance."""
    global _text_formatter
    if _text_formatter is None:
        _text_formatter = LSITextFormatter()
    return _text_formatter