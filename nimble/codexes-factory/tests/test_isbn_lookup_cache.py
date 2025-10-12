"""
Tests for ISBN lookup caching system.
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from src.codexes.modules.distribution.isbn_lookup_cache import ISBNLookupCache


class TestISBNLookupCache:
    
    def setup_method(self):
        """Set up test fixtures with temporary cache file"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.cache = ISBNLookupCache(cache_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_cache_persistence(self):
        """Test that ISBN cache persists across sessions"""
        isbn = "9781234567890"
        test_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'publisher': 'Test Publisher'
        }
        
        # Cache data
        self.cache.cache_isbn_data(isbn, test_data)
        
        # Create new cache instance with same file
        new_cache = ISBNLookupCache(cache_file=self.temp_file.name)
        
        # Should find cached data
        cached_data = new_cache.lookup_isbn(isbn)
        assert cached_data is not None
        assert cached_data['title'] == 'Test Book'
        assert cached_data['author'] == 'Test Author'
    
    def test_duplicate_scan_prevention(self):
        """Test that documents are not scanned multiple times"""
        content = "This book has ISBN 978-1234567890 in it."
        document_id = "test_doc_123"
        
        # First scan
        isbns1 = self.cache.scan_document_for_isbns(document_id, content)
        assert len(isbns1) > 0
        assert self.cache.is_document_processed(document_id)
        
        # Second scan should return empty list
        isbns2 = self.cache.scan_document_for_isbns(document_id, content)
        assert len(isbns2) == 0
    
    def test_isbn_pattern_detection(self):
        """Test ISBN pattern detection in content"""
        content = """
        This book references ISBN-13: 978-1234567890 and also
        ISBN-10: 1234567890. There's also a raw number 9780987654321.
        """
        
        isbns = self.cache.scan_document_for_isbns("test_doc", content)
        
        # Should find multiple ISBNs
        assert len(isbns) >= 2
        assert "9781234567890" in isbns or "1234567890" in isbns
    
    def test_cache_expiration(self):
        """Test that expired cache entries are cleaned"""
        isbn = "9781234567890"
        
        # Create expired entry
        expired_data = {
            'title': 'Expired Book',
            'lookup_timestamp': (datetime.now() - timedelta(days=35)).isoformat()
        }
        
        # Manually add to cache file
        cache_data = {'isbn_data': {isbn: expired_data}, 'processed_documents': []}
        with open(self.temp_file.name, 'w') as f:
            json.dump(cache_data, f)
        
        # Create new cache instance - should clean expired entries
        new_cache = ISBNLookupCache(cache_file=self.temp_file.name, cache_expiry_days=30)
        
        # Should not find expired entry
        result = new_cache.lookup_isbn(isbn)
        assert result is None
    
    def test_cache_validation(self):
        """Test cache file validation"""
        # Valid cache should pass validation
        assert self.cache.validate_cache_integrity()
        
        # Create invalid cache file
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json")
        
        # Should fail validation
        new_cache = ISBNLookupCache(cache_file=self.temp_file.name)
        assert not new_cache.validate_cache_integrity()
    
    def test_isbn_validation(self):
        """Test ISBN format validation"""
        # Valid ISBNs
        assert self.cache._validate_isbn("9781234567890")  # ISBN-13
        assert self.cache._validate_isbn("1234567890")     # ISBN-10
        
        # Invalid ISBNs
        assert not self.cache._validate_isbn("123")        # Too short
        assert not self.cache._validate_isbn("abcdefghij") # Non-numeric
        assert not self.cache._validate_isbn("1234567890123") # Wrong prefix
    
    def test_cache_stats(self):
        """Test cache statistics reporting"""
        # Add some test data
        self.cache.cache_isbn_data("9781234567890", {'title': 'Test Book 1'})
        self.cache.cache_isbn_data("9780987654321", {'title': 'Test Book 2'})
        self.cache.scan_document_for_isbns("doc1", "Some content")
        
        stats = self.cache.get_cache_stats()
        
        assert stats['total_cached_isbns'] == 2
        assert stats['processed_documents'] == 1
        assert 'cache_file_size' in stats
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Add some data
        self.cache.cache_isbn_data("9781234567890", {'title': 'Test Book'})
        self.cache.scan_document_for_isbns("doc1", "Some content")
        
        # Clear cache
        self.cache.clear_cache()
        
        # Should be empty
        stats = self.cache.get_cache_stats()
        assert stats['total_cached_isbns'] == 0
        assert stats['processed_documents'] == 0
    
    def test_error_handling(self):
        """Test error handling for corrupted cache"""
        # Test with non-existent directory
        invalid_cache = ISBNLookupCache(cache_file="/invalid/path/cache.json")
        
        # Should handle gracefully
        result = invalid_cache.lookup_isbn("9781234567890")
        assert result is None
        
        # Should not crash on cache operations
        invalid_cache.cache_isbn_data("9781234567890", {'title': 'Test'})
        invalid_cache.scan_document_for_isbns("doc1", "content")