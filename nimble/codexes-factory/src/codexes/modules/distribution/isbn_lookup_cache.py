"""
ISBN lookup caching system to prevent duplicate API calls.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


class ISBNLookupCache:
    """Intelligent ISBN lookup with persistent caching"""
    
    def __init__(self, cache_file: str = "isbn_cache.json", cache_expiry_days: int = 30):
        self.cache_file = cache_file
        self.cache_expiry_days = cache_expiry_days
        self.cache_data = self._load_cache()
        self.processed_documents: Set[str] = set()
        self._load_processed_documents()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load existing cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # Clean expired entries
                    return self._clean_expired_entries(cache)
            return {'isbn_data': {}, 'processed_documents': []}
        except Exception as e:
            logger.error(f"Error loading ISBN cache: {e}")
            return {'isbn_data': {}, 'processed_documents': []}
    
    def _clean_expired_entries(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """Remove expired cache entries"""
        try:
            current_time = datetime.now()
            cleaned_cache = {'isbn_data': {}, 'processed_documents': cache.get('processed_documents', [])}
            
            for isbn, data in cache.get('isbn_data', {}).items():
                if 'lookup_timestamp' in data:
                    lookup_time = datetime.fromisoformat(data['lookup_timestamp'])
                    if current_time - lookup_time < timedelta(days=self.cache_expiry_days):
                        cleaned_cache['isbn_data'][isbn] = data
                else:
                    # Keep entries without timestamp for backward compatibility
                    cleaned_cache['isbn_data'][isbn] = data
            
            return cleaned_cache
        except Exception as e:
            logger.error(f"Error cleaning expired cache entries: {e}")
            return cache
    
    def _load_processed_documents(self):
        """Load list of processed documents"""
        try:
            self.processed_documents = set(self.cache_data.get('processed_documents', []))
        except Exception as e:
            logger.error(f"Error loading processed documents: {e}")
            self.processed_documents = set()
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            # Update processed documents list
            self.cache_data['processed_documents'] = list(self.processed_documents)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving ISBN cache: {e}")
    
    def _generate_document_id(self, content: str) -> str:
        """Generate unique document ID from content hash"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def lookup_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """Lookup ISBN with caching to avoid duplicate API calls"""
        try:
            # Clean ISBN (remove hyphens, spaces)
            clean_isbn = isbn.replace('-', '').replace(' ', '').strip()
            
            # Check cache first
            if clean_isbn in self.cache_data['isbn_data']:
                logger.info(f"ISBN {clean_isbn} found in cache")
                return self.cache_data['isbn_data'][clean_isbn]
            
            # If not in cache, would make API call here
            # For now, return None to indicate cache miss
            logger.info(f"ISBN {clean_isbn} not found in cache - would require API call")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up ISBN {isbn}: {e}")
            return None
    
    def scan_document_for_isbns(self, document_id: str, content: str) -> List[str]:
        """Scan document for ISBNs, avoiding duplicate scans"""
        try:
            # Generate document hash if not provided
            if not document_id:
                document_id = self._generate_document_id(content)
            
            # Check if document already processed
            if self.is_document_processed(document_id):
                logger.info(f"Document {document_id} already processed for ISBNs")
                return []
            
            # Scan for ISBN patterns
            import re
            isbn_patterns = [
                r'ISBN[-\s]?(?:13[-\s]?)?:?\s*(\d{3}[-\s]?\d{1}[-\s]?\d{3}[-\s]?\d{5}[-\s]?\d{1})',  # ISBN-13
                r'ISBN[-\s]?(?:10[-\s]?)?:?\s*(\d{1}[-\s]?\d{3}[-\s]?\d{5}[-\s]?\d{1})',  # ISBN-10
                r'(\d{13})',  # Raw 13-digit numbers
                r'(\d{10})'   # Raw 10-digit numbers
            ]
            
            found_isbns = []
            for pattern in isbn_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_isbn = match.replace('-', '').replace(' ', '')
                    if self._validate_isbn(clean_isbn):
                        found_isbns.append(clean_isbn)
            
            # Mark document as processed
            self.processed_documents.add(document_id)
            self._save_cache()
            
            logger.info(f"Found {len(found_isbns)} ISBNs in document {document_id}")
            return list(set(found_isbns))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error scanning document for ISBNs: {e}")
            return []
    
    def _validate_isbn(self, isbn: str) -> bool:
        """Basic ISBN validation"""
        try:
            if len(isbn) == 10:
                # ISBN-10 validation
                if not isbn[:-1].isdigit():
                    return False
                return True  # Simplified validation
            elif len(isbn) == 13:
                # ISBN-13 validation
                if not isbn.isdigit():
                    return False
                return isbn.startswith(('978', '979'))
            return False
        except Exception:
            return False
    
    def cache_isbn_data(self, isbn: str, data: Dict[str, Any]) -> None:
        """Cache ISBN lookup results for future use"""
        try:
            clean_isbn = isbn.replace('-', '').replace(' ', '').strip()
            
            # Add timestamp
            data['lookup_timestamp'] = datetime.now().isoformat()
            data['source'] = data.get('source', 'api_lookup')
            
            self.cache_data['isbn_data'][clean_isbn] = data
            self._save_cache()
            
            logger.info(f"Cached data for ISBN {clean_isbn}")
            
        except Exception as e:
            logger.error(f"Error caching ISBN data: {e}")
    
    def is_document_processed(self, document_id: str) -> bool:
        """Check if document has already been scanned for ISBNs"""
        return document_id in self.processed_documents
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            return {
                'total_cached_isbns': len(self.cache_data['isbn_data']),
                'processed_documents': len(self.processed_documents),
                'cache_file_size': os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0,
                'cache_expiry_days': self.cache_expiry_days
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        try:
            self.cache_data = {'isbn_data': {}, 'processed_documents': []}
            self.processed_documents = set()
            self._save_cache()
            logger.info("ISBN cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def validate_cache_integrity(self) -> bool:
        """Validate cache file integrity"""
        try:
            if not os.path.exists(self.cache_file):
                return True  # No cache file is valid
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check required structure
            required_keys = ['isbn_data', 'processed_documents']
            for key in required_keys:
                if key not in data:
                    return False
            
            # Validate ISBN data structure
            for isbn, isbn_data in data['isbn_data'].items():
                if not isinstance(isbn_data, dict):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Cache integrity validation failed: {e}")
            return False