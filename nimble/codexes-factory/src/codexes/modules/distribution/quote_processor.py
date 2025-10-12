"""
Quote processor module for early quotation assembly and verification.
Handles quotation extraction, validation, and metadata generation.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class QuoteProcessor:
    """Processes and validates quotations for use in catalog metadata."""
    
    def __init__(self):
        self.processed_quotes = []
        self.verification_log = []
        
    def extract_and_validate_quotes(self, book_data: Dict[str, Any]) -> Tuple[List[Dict], Dict]:
        """
        Extract quotes from book data and validate them.
        Returns tuple of (processed_quotes, validation_summary)
        """
        quotes = book_data.get('quotes', [])
        if not quotes:
            logger.warning("No quotes found in book data")
            return [], {'total': 0, 'valid': 0, 'invalid': 0}
        
        processed_quotes = []
        validation_summary = {'total': len(quotes), 'valid': 0, 'invalid': 0}
        
        for i, quote in enumerate(quotes):
            processed_quote = self._validate_single_quote(quote, i + 1)
            if processed_quote:
                processed_quotes.append(processed_quote)
                validation_summary['valid'] += 1
            else:
                validation_summary['invalid'] += 1
                
        self.processed_quotes = processed_quotes
        logger.info(f"Processed {len(processed_quotes)} valid quotes out of {len(quotes)} total")
        
        return processed_quotes, validation_summary
    
    def _validate_single_quote(self, quote: Dict[str, Any], quote_id: int) -> Optional[Dict[str, Any]]:
        """Validate a single quote and return processed version."""
        try:
            # Required fields
            quote_text = quote.get('quote', '').strip()
            author = quote.get('author', '').strip()
            source = quote.get('source', '').strip()
            
            if not quote_text:
                logger.warning(f"Quote {quote_id}: Missing quote text")
                return None
                
            if not author:
                logger.warning(f"Quote {quote_id}: Missing author")
                return None
                
            if not source:
                logger.warning(f"Quote {quote_id}: Missing source")
                return None
            
            # Create processed quote
            processed_quote = {
                'id': quote_id,
                'quote': quote_text,
                'author': author,
                'source': source,
                'date_first_published': quote.get('date_first_published', 'N.D.'),
                'editor_note': quote.get('editor_note', ''),
                'word_count': len(quote_text.split()),
                'character_count': len(quote_text),
                'validation_status': 'valid'
            }
            
            # Add to verification log
            self.verification_log.append({
                'quote_id': quote_id,
                'author': author,
                'source': source,
                'word_count': processed_quote['word_count'],
                'status': 'valid',
                'notes': ''
            })
            
            return processed_quote
            
        except Exception as e:
            logger.error(f"Error validating quote {quote_id}: {e}")
            self.verification_log.append({
                'quote_id': quote_id,
                'author': quote.get('author', 'Unknown'),
                'source': quote.get('source', 'Unknown'),
                'word_count': 0,
                'status': 'error',
                'notes': str(e)
            })
            return None
    
    def generate_catalog_metadata(self, processed_quotes: List[Dict]) -> Dict[str, Any]:
        """Generate catalog metadata based on processed quotes."""
        if not processed_quotes:
            return {}
        
        total_words = sum(q['word_count'] for q in processed_quotes)
        unique_authors = len(set(q['author'] for q in processed_quotes))
        unique_sources = len(set(q['source'] for q in processed_quotes))
        
        # Calculate reading time (assuming 200 words per minute)
        estimated_reading_time = max(1, total_words // 200)
        
        return {
            'quote_count': len(processed_quotes),
            'total_word_count': total_words,
            'unique_authors': unique_authors,
            'unique_sources': unique_sources,
            'estimated_reading_time_minutes': estimated_reading_time,
            'content_density': 'high' if total_words > 5000 else 'medium' if total_words > 2000 else 'light'
        }
    
    def get_verification_log(self) -> List[Dict]:
        """Return the verification log for inclusion in backmatter."""
        return self.verification_log
    
    def extract_bibliography_sources(self, processed_quotes: List[Dict]) -> List[Dict]:
        """Extract unique sources for bibliography generation."""
        sources = {}
        
        for quote in processed_quotes:
            source_key = f"{quote['author']}_{quote['source']}"
            if source_key not in sources:
                sources[source_key] = {
                    'author': quote['author'],
                    'title': quote['source'],
                    'date_published': quote['date_first_published'],
                    'isbn': None  # To be filled by ISBN lookup
                }
        
        return list(sources.values())