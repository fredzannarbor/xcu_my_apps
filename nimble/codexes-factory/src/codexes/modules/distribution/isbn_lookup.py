"""
ISBN lookup service for bibliography generation.
Attempts to find ISBNs for books using various APIs and databases.
"""

import logging
import requests
import time
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class ISBNLookupService:
    """Service to lookup ISBNs for books using various APIs."""
    
    def __init__(self):
        self.cache = {}
        self.rate_limit_delay = 0.5  # seconds between requests
        
    def lookup_isbn(self, author: str, title: str) -> Optional[str]:
        """
        Lookup ISBN for a book by author and title.
        Returns ISBN-13 if found, None otherwise.
        """
        cache_key = f"{author}_{title}".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try multiple lookup methods
        isbn = None
        
        # Method 1: OpenLibrary API
        isbn = self._lookup_openlibrary(author, title)
        
        if not isbn:
            # Method 2: Google Books API (if available)
            isbn = self._lookup_google_books(author, title)
        
        # Cache the result (even if None)
        self.cache[cache_key] = isbn
        
        # Rate limiting
        time.sleep(self.rate_limit_delay)
        
        return isbn
    
    def _lookup_openlibrary(self, author: str, title: str) -> Optional[str]:
        """Lookup ISBN using OpenLibrary API."""
        try:
            # Clean up search terms
            author_clean = author.replace(',', '').strip()
            title_clean = title.replace(':', '').replace(',', '').strip()
            
            # Search OpenLibrary
            search_url = "https://openlibrary.org/search.json"
            params = {
                'author': author_clean,
                'title': title_clean,
                'limit': 5
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get('docs', [])
            
            for doc in docs:
                # Look for ISBN-13 first, then ISBN-10
                isbns = doc.get('isbn', [])
                for isbn in isbns:
                    if len(isbn) == 13 and isbn.startswith('978'):
                        logger.info(f"Found ISBN-13 for '{title}' by {author}: {isbn}")
                        return isbn
                    elif len(isbn) == 10:
                        # Convert ISBN-10 to ISBN-13
                        isbn13 = self._convert_isbn10_to_isbn13(isbn)
                        if isbn13:
                            logger.info(f"Found ISBN-10 for '{title}' by {author}, converted to ISBN-13: {isbn13}")
                            return isbn13
            
            logger.debug(f"No ISBN found for '{title}' by {author} in OpenLibrary")
            return None
            
        except Exception as e:
            logger.warning(f"Error looking up ISBN for '{title}' by {author} in OpenLibrary: {e}")
            return None
    
    def _lookup_google_books(self, author: str, title: str) -> Optional[str]:
        """Lookup ISBN using Google Books API (basic implementation)."""
        try:
            # This is a basic implementation - in production you might want to use an API key
            search_url = "https://www.googleapis.com/books/v1/volumes"
            query = f'inauthor:"{author}" intitle:"{title}"'
            params = {
                'q': query,
                'maxResults': 5
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                volume_info = item.get('volumeInfo', {})
                industry_identifiers = volume_info.get('industryIdentifiers', [])
                
                for identifier in industry_identifiers:
                    if identifier.get('type') == 'ISBN_13':
                        isbn = identifier.get('identifier')
                        logger.info(f"Found ISBN-13 for '{title}' by {author} in Google Books: {isbn}")
                        return isbn
            
            logger.debug(f"No ISBN found for '{title}' by {author} in Google Books")
            return None
            
        except Exception as e:
            logger.warning(f"Error looking up ISBN for '{title}' by {author} in Google Books: {e}")
            return None
    
    def _convert_isbn10_to_isbn13(self, isbn10: str) -> Optional[str]:
        """Convert ISBN-10 to ISBN-13."""
        try:
            if len(isbn10) != 10:
                return None
            
            # Remove any hyphens or spaces
            isbn10 = isbn10.replace('-', '').replace(' ', '')
            
            # Add 978 prefix
            isbn13_base = '978' + isbn10[:-1]  # Remove check digit
            
            # Calculate new check digit
            check_sum = 0
            for i, digit in enumerate(isbn13_base):
                if i % 2 == 0:
                    check_sum += int(digit)
                else:
                    check_sum += int(digit) * 3
            
            check_digit = (10 - (check_sum % 10)) % 10
            isbn13 = isbn13_base + str(check_digit)
            
            return isbn13
            
        except Exception as e:
            logger.warning(f"Error converting ISBN-10 to ISBN-13: {e}")
            return None
    
    def lookup_multiple_isbns(self, sources: List[Dict]) -> List[Dict]:
        """Lookup ISBNs for multiple sources."""
        updated_sources = []
        
        for source in sources:
            author = source.get('author', '')
            title = source.get('title', '')
            
            if author and title:
                isbn = self.lookup_isbn(author, title)
                source_copy = source.copy()
                source_copy['isbn'] = isbn
                updated_sources.append(source_copy)
                
                if isbn:
                    logger.info(f"Found ISBN for '{title}' by {author}: {isbn}")
                else:
                    logger.debug(f"No ISBN found for '{title}' by {author}")
            else:
                updated_sources.append(source)
        
        return updated_sources