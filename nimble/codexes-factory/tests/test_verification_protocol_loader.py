#!/usr/bin/env python3
"""
Comprehensive tests for the verification protocol loader fix.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.prepress.partsofthebook_processor import VerificationProtocolLoader, PartsOfTheBookProcessor


class TestVerificationProtocolLoader:
    """Test the VerificationProtocolLoader class."""
    
    def test_loader_initialization(self):
        """Test loader initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = VerificationProtocolLoader(output_dir=temp_dir)
            
            assert loader.output_dir == Path(temp_dir)
            assert loader.templates_dir is None
            assert loader.imprint_dir is None
            assert loader.quotes == []
    
    def test_load_from_output_directory(self):
        """Test loading protocol from output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a custom protocol file
            protocol_content = "\\section{Custom Protocol}\nThis is a test protocol."
            protocol_file = temp_path / "verification_protocol.tex"
            protocol_file.write_text(protocol_content, encoding='utf-8')
            
            loader = VerificationProtocolLoader(output_dir=temp_path)
            result = loader.load_verification_protocol()
            
            assert "Custom Protocol" in result
            assert "test protocol" in result
    
    def test_load_from_templates_directory(self):
        """Test loading protocol from templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "output"
            templates_dir = temp_path / "templates"
            
            output_dir.mkdir()
            templates_dir.mkdir()
            
            # Create protocol in templates directory
            protocol_content = "\\section{Templates Protocol}\nFrom templates directory."
            protocol_file = templates_dir / "verification_protocol.tex"
            protocol_file.write_text(protocol_content, encoding='utf-8')
            
            loader = VerificationProtocolLoader(
                output_dir=output_dir,
                templates_dir=templates_dir
            )
            result = loader.load_verification_protocol()
            
            assert "Templates Protocol" in result
            assert "templates directory" in result
    
    def test_load_from_imprint_directory(self):
        """Test loading protocol from imprint directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "output"
            imprint_dir = temp_path / "imprint"
            
            output_dir.mkdir()
            imprint_dir.mkdir()
            
            # Create protocol in imprint directory
            protocol_content = "\\section{Imprint Protocol}\nFrom imprint directory."
            protocol_file = imprint_dir / "verification_protocol.tex"
            protocol_file.write_text(protocol_content, encoding='utf-8')
            
            loader = VerificationProtocolLoader(
                output_dir=output_dir,
                imprint_dir=imprint_dir
            )
            result = loader.load_verification_protocol()
            
            assert "Imprint Protocol" in result
            assert "imprint directory" in result
    
    def test_priority_order(self):
        """Test that files are loaded in correct priority order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "output"
            templates_dir = temp_path / "templates"
            imprint_dir = temp_path / "imprint"
            
            output_dir.mkdir()
            templates_dir.mkdir()
            imprint_dir.mkdir()
            
            # Create protocols in all directories
            (output_dir / "verification_protocol.tex").write_text("Output Protocol", encoding='utf-8')
            (templates_dir / "verification_protocol.tex").write_text("Templates Protocol", encoding='utf-8')
            (imprint_dir / "verification_protocol.tex").write_text("Imprint Protocol", encoding='utf-8')
            
            loader = VerificationProtocolLoader(
                output_dir=output_dir,
                templates_dir=templates_dir,
                imprint_dir=imprint_dir
            )
            result = loader.load_verification_protocol()
            
            # Should load from output directory (highest priority)
            assert "Output Protocol" in result
            assert "Templates Protocol" not in result
            assert "Imprint Protocol" not in result
    
    def test_default_protocol_creation(self):
        """Test default protocol creation when no files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = VerificationProtocolLoader(output_dir=temp_dir)
            
            quotes = [
                {'quote': 'Test quote 1', 'author': 'Author 1', 'is_verified': True},
                {'quote': 'Test quote 2', 'author': 'Author 2', 'is_verified': False},
            ]
            
            result = loader.load_verification_protocol(quotes)
            
            assert "Verification Protocol" in result
            assert "Processing Overview" in result
            assert "Verification Statistics" in result
            assert "Total Quotations: 2" in result
            assert "Verified Quotations: 1" in result
            assert "Verification Rate: 50.0" in result
    
    def test_statistics_calculation(self):
        """Test verification statistics calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = VerificationProtocolLoader(output_dir=temp_dir)
            
            quotes = [
                {'quote': 'Quote 1', 'author': 'Author A', 'source': 'Book 1', 'is_verified': True},
                {'quote': 'Quote 2', 'author': 'Author B', 'source': 'Book 2', 'is_verified': True},
                {'quote': 'Quote 3', 'author': 'Author A', 'source': 'Book 1', 'is_verified': False},
            ]
            
            loader.quotes = quotes
            stats = loader._calculate_verification_stats()
            
            assert stats['total_quotes'] == 3
            assert stats['verified_quotes'] == 2
            assert stats['unverified_quotes'] == 1
            assert stats['verification_percentage'] == 66.7
            assert stats['sources_count'] == 2
            assert stats['unique_authors'] == 2
            assert stats['verification_complete'] == False
    
    def test_empty_quotes_statistics(self):
        """Test statistics calculation with empty quotes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = VerificationProtocolLoader(output_dir=temp_dir)
            
            stats = loader._calculate_verification_stats()
            
            assert stats['total_quotes'] == 0
            assert stats['verified_quotes'] == 0
            assert stats['verification_percentage'] == 0
            assert stats['verification_complete'] == True
    
    def test_protocol_file_saving(self):
        """Test that default protocol is saved to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            loader = VerificationProtocolLoader(output_dir=temp_path)
            
            # Generate default protocol
            loader.load_verification_protocol()
            
            # Check that file was created
            protocol_file = temp_path / "verification_protocol.tex"
            assert protocol_file.exists()
            
            # Check content
            content = protocol_file.read_text(encoding='utf-8')
            assert "Verification Protocol" in content
            assert "Processing Overview" in content
    
    def test_error_handling_corrupted_file(self):
        """Test handling of corrupted protocol files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a file with invalid encoding that will cause UnicodeDecodeError
            protocol_file = temp_path / "verification_protocol.tex"
            with open(protocol_file, 'wb') as f:
                # Write truly invalid UTF-8 bytes
                f.write(b'\xff\xfe\x00\x00\xff\xff\x00\x00invalid\x80\x81\x82encoding')
            
            loader = VerificationProtocolLoader(output_dir=temp_path)
            
            # This should detect the corrupted file and fall back to default
            result = loader.load_verification_protocol()
            
            # Should fall back to default protocol when encoding fails
            assert result is not None
            assert len(result) > 0
            # Should contain default protocol content
            assert "Verification Protocol" in result
            assert "Processing Overview" in result
    
    def test_error_handling_permission_denied(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a directory instead of a file (will cause error)
            protocol_dir = temp_path / "verification_protocol.tex"
            protocol_dir.mkdir()
            
            # Use a different output directory to avoid save conflicts
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            loader = VerificationProtocolLoader(output_dir=output_dir, templates_dir=temp_path)
            result = loader.load_verification_protocol()
            
            # Should fall back to default protocol
            assert "Verification Protocol" in result


class TestPartsOfTheBookProcessorIntegration:
    """Test integration with PartsOfTheBookProcessor."""
    
    def test_verification_log_processing(self):
        """Test verification log processing with new loader."""
        processor = PartsOfTheBookProcessor()
        
        book_data = {
            'quotes': [
                {'quote': 'Test quote 1', 'author': 'Author 1', 'is_verified': True},
                {'quote': 'Test quote 2', 'author': 'Author 2', 'is_verified': False},
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_verification_log(
                book_data,
                output_dir=Path(temp_dir)
            )
            
            assert "Verification Log" in result
            assert "Verification Protocol" in result
            assert "Detailed Verification Log" in result
            assert "Test quote 1" in result
            assert "Test quote 2" in result
    
    def test_verification_status_storage(self):
        """Test that verification status is stored in book_data."""
        processor = PartsOfTheBookProcessor()
        
        book_data = {
            'quotes': [
                {'quote': 'Quote 1', 'is_verified': True},
                {'quote': 'Quote 2', 'is_verified': True},
                {'quote': 'Quote 3', 'is_verified': False},
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            processor.process_verification_log(
                book_data,
                output_dir=Path(temp_dir)
            )
            
            status = book_data.get('verification_status', {})
            assert status['verified_count'] == 2
            assert status['total_count'] == 3
            assert status['percentage'] == 66.7
    
    def test_empty_quotes_handling(self):
        """Test handling of empty quotes list."""
        processor = PartsOfTheBookProcessor()
        
        book_data = {'quotes': []}
        
        result = processor.process_verification_log(book_data)
        
        assert result == ""  # Should return empty string for no quotes


def main():
    """Run all tests manually."""
    print("=" * 60)
    print("VERIFICATION PROTOCOL LOADER TESTS")
    print("=" * 60)
    
    test_classes = [TestVerificationProtocolLoader, TestPartsOfTheBookProcessorIntegration]
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n🧪 Running {test_class.__name__}...")
        
        instance = test_class()
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                print(f"  • {test_method}...", end=" ")
                getattr(instance, test_method)()
                print("✅")
                passed_tests += 1
            except Exception as e:
                print(f"❌ - {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())