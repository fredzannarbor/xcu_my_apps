# tests/test_file_system_integration.py

import pytest
import os
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from codexes.modules.verifiers.field_validators import (
    PDFValidator,
    FileExistenceValidator
)
from codexes.modules.verifiers.validation_framework import ValidationSeverity
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestFileSystemIntegration:
    """Comprehensive file system integration tests for LSI field enhancement
    
    Tests Requirements 3.6, 3.7, 3.8:
    - 3.6: Digital files available in ftp2lsi staging area with proper naming
    - 3.7: PDF X-1a format verification
    - 3.8: Interior PDF matching page count and trim sizes
    """
    
    def setup_method(self):
        """Set up test environment with temporary FTP staging area"""
        self.temp_dir = tempfile.mkdtemp()
        self.ftp_staging_path = os.path.join(self.temp_dir, "ftp2lsi")
        os.makedirs(self.ftp_staging_path, exist_ok=True)
        
        self.pdf_validator = PDFValidator(ftp_staging_path=self.ftp_staging_path)
        self.file_validator = FileExistenceValidator(ftp_staging_path=self.ftp_staging_path)
        
        # Sample metadata for testing
        self.sample_metadata = CodexMetadata(
            isbn13="9780132350884",
            page_count=200,
            trim_size="6 x 9",
            interior_path_filename="9780132350884_interior.pdf",
            cover_path_filename="9780132350884_cover.pdf"
        )
    
    def teardown_method(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_pdf_file(self, file_path: str, size_kb: int = 100):
        """Helper method to create mock PDF files with specified size"""
        content = "Mock PDF content " * (size_kb * 1024 // 17)  # Approximate size
        with open(file_path, 'w') as f:
            f.write(content)


class TestFTPStagingAreaValidation(TestFileSystemIntegration):
    """Test Requirement 3.6: Digital files validation in ftp2lsi staging area"""
    
    def test_ftp_staging_area_structure(self):
        """Test that FTP staging area exists and is accessible"""
        assert os.path.exists(self.ftp_staging_path)
        assert os.path.isdir(self.ftp_staging_path)
        assert os.access(self.ftp_staging_path, os.R_OK | os.W_OK)
    
    def test_interior_file_naming_convention_correct(self):
        """Test correct interior file naming: ISBN_interior.pdf"""
        # Create correctly named interior file
        interior_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(interior_file, size_kb=1000)
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        # Should pass naming convention check
        assert result.is_valid is True
        assert "File naming convention" not in result.error_message
    
    def test_interior_file_naming_convention_incorrect(self):
        """Test incorrect interior file naming"""
        # Create incorrectly named interior file
        wrong_file = os.path.join(self.ftp_staging_path, "interior.pdf")
        self._create_mock_pdf_file(wrong_file, size_kb=1000)
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "interior.pdf", 
            self.sample_metadata
        )
        
        # Should fail naming convention check
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File naming convention error" in result.error_message
        assert "9780132350884_interior.pdf" in result.suggested_value
    
    def test_cover_file_naming_convention_correct(self):
        """Test correct cover file naming: ISBN_cover.pdf"""
        # Create correctly named cover file
        cover_file = os.path.join(self.ftp_staging_path, "9780132350884_cover.pdf")
        self._create_mock_pdf_file(cover_file, size_kb=500)
        
        result = self.pdf_validator.validate(
            "cover_path_filename", 
            "9780132350884_cover.pdf", 
            self.sample_metadata
        )
        
        # Should pass naming convention check
        assert result.is_valid is True
        assert "File naming convention" not in result.error_message
    
    def test_cover_file_naming_convention_incorrect(self):
        """Test incorrect cover file naming"""
        # Create incorrectly named cover file
        wrong_file = os.path.join(self.ftp_staging_path, "cover.pdf")
        self._create_mock_pdf_file(wrong_file, size_kb=500)
        
        result = self.pdf_validator.validate(
            "cover_path_filename", 
            "cover.pdf", 
            self.sample_metadata
        )
        
        # Should fail naming convention check
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File naming convention error" in result.error_message
        assert "9780132350884_cover.pdf" in result.suggested_value
    
    def test_files_missing_from_ftp_staging(self):
        """Test validation when files are missing from FTP staging area"""
        # Don't create any files
        
        # Test interior file missing
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File not found in FTP staging area" in result.error_message
        
        # Test cover file missing
        result = self.pdf_validator.validate(
            "cover_path_filename", 
            "9780132350884_cover.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File not found in FTP staging area" in result.error_message
    
    def test_files_exist_in_ftp_staging(self):
        """Test validation when files exist in FTP staging area"""
        # Create both files
        interior_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        cover_file = os.path.join(self.ftp_staging_path, "9780132350884_cover.pdf")
        
        self._create_mock_pdf_file(interior_file, size_kb=1000)
        self._create_mock_pdf_file(cover_file, size_kb=500)
        
        # Test interior file exists
        result = self.file_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "File exists" in result.info_message
        
        # Test cover file exists
        result = self.file_validator.validate(
            "cover_path_filename", 
            "9780132350884_cover.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "File exists" in result.info_message
    
    def test_file_size_validation(self):
        """Test file size validation for PDF files"""
        # Test very small file (suspicious)
        small_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(small_file, size_kb=1)  # 1KB - very small
        
        result = self.file_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Small PDF file" in result.warning_message
        
        # Test very large file (warning)
        with patch('os.path.getsize', return_value=150 * 1024 * 1024):  # 150MB
            result = self.file_validator.validate(
                "interior_path_filename", 
                "9780132350884_interior.pdf", 
                self.sample_metadata
            )
            
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.WARNING
            assert "Large file size" in result.warning_message
    
    def test_empty_file_validation(self):
        """Test validation of empty files"""
        # Create empty file
        empty_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        result = self.file_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File is empty" in result.error_message
    
    def test_directory_instead_of_file(self):
        """Test validation when path points to directory instead of file"""
        # Create directory with same name as expected file
        dir_path = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        os.makedirs(dir_path)
        
        result = self.file_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Path exists but is not a file" in result.error_message


class TestPDFFormatValidation(TestFileSystemIntegration):
    """Test Requirement 3.7: PDF X-1a format verification"""
    
    @patch('subprocess.run')
    def test_pdf_x1a_format_compliant(self, mock_subprocess):
        """Test PDF X-1a format compliance detection"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output indicating PDF/X-1a compliance
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
Creator: Adobe InDesign
Producer: Adobe PDF Library
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid PDF file" in result.info_message
        
        # Verify pdfinfo was called (may be called multiple times for different validations)
        assert mock_subprocess.call_count >= 1
        call_args = mock_subprocess.call_args[0][0]
        assert "pdfinfo" in call_args
        assert pdf_file in call_args
    
    @patch('subprocess.run')
    def test_pdf_x1a_format_non_compliant(self, mock_subprocess):
        """Test PDF without X-1a compliance"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output without PDF/X-1a compliance
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.7
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
Creator: Microsoft Word
Producer: Microsoft Print to PDF
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "PDF format compliance cannot be verified" in result.message
    
    @patch('subprocess.run')
    def test_pdf_format_validation_tool_unavailable(self, mock_subprocess):
        """Test behavior when pdfinfo tool is not available"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo not found
        mock_subprocess.side_effect = FileNotFoundError("pdfinfo not found")
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "PDF format validation tools not available" in result.message
    
    @patch('subprocess.run')
    def test_pdf_format_validation_error(self, mock_subprocess):
        """Test behavior when pdfinfo returns error"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo error
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Couldn't open file"
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Cannot read PDF file" in result.error_message
    
    def test_non_pdf_file_format(self):
        """Test validation of non-PDF files"""
        # Create non-PDF file
        txt_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.txt")
        with open(txt_file, 'w') as f:
            f.write("This is not a PDF file")
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.txt", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File must be PDF format" in result.error_message


class TestPDFSpecificationValidation(TestFileSystemIntegration):
    """Test Requirement 3.8: Interior PDF matching page count and trim sizes"""
    
    @patch('subprocess.run')
    def test_page_count_matches_metadata(self, mock_subprocess):
        """Test PDF page count matches metadata specification"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output with matching page count
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid PDF file" in result.info_message
    
    @patch('subprocess.run')
    def test_page_count_mismatch(self, mock_subprocess):
        """Test PDF page count doesn't match metadata"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output with different page count
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 150
Page size: 432 x 648 pts (6 x 9 inches)
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Page count mismatch" in result.error_message
        assert "PDF has 150 pages, metadata specifies 200 pages" in result.error_message
    
    @patch('subprocess.run')
    def test_trim_size_matches_pdf_dimensions(self, mock_subprocess):
        """Test PDF dimensions match trim size specification"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output with matching dimensions (6x9 = 432x648 pts)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid PDF file" in result.info_message
    
    @patch('subprocess.run')
    def test_trim_size_mismatch_pdf_dimensions(self, mock_subprocess):
        """Test PDF dimensions don't match trim size"""
        # Create PDF file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock pdfinfo output with different dimensions (8.5x11 instead of 6x9)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 612 x 792 pts (8.5 x 11 inches)
"""
        mock_subprocess.return_value = mock_result
        
        result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Trim size mismatch" in result.error_message
    
    def test_trim_size_validation_standard_sizes(self):
        """Test validation of standard trim sizes"""
        standard_sizes = [
            "5 x 8",
            "5.25 x 8", 
            "5.5 x 8.5",
            "6 x 9",
            "6.14 x 9.21",  # A5
            "7 x 10",
            "8.5 x 11"
        ]
        
        for trim_size in standard_sizes:
            metadata = CodexMetadata(trim_size=trim_size)
            result = self.pdf_validator.validate("trim_size", trim_size, metadata)
            
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.INFO
            assert "Standard trim size" in result.info_message
    
    def test_trim_size_validation_custom_sizes(self):
        """Test validation of custom trim sizes"""
        custom_sizes = [
            "6.5 x 9.25",
            "5.75 x 8.25"
        ]
        
        for trim_size in custom_sizes:
            metadata = CodexMetadata(trim_size=trim_size)
            result = self.pdf_validator.validate("trim_size", trim_size, metadata)
            
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.INFO
            assert "Custom trim size" in result.info_message
        
        # Test size that's actually in standard sizes
        standard_size = "7.5 x 9.25"
        metadata = CodexMetadata(trim_size=standard_size)
        result = self.pdf_validator.validate("trim_size", standard_size, metadata)
        
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        # This one should be recognized as standard, not custom
        assert "Standard trim size" in result.info_message
    
    def test_trim_size_validation_unusual_sizes(self):
        """Test validation of unusual trim sizes"""
        unusual_sizes = [
            "2 x 3",      # Too small
            "1 x 20"      # Weird aspect ratio
        ]
        
        for trim_size in unusual_sizes:
            metadata = CodexMetadata(trim_size=trim_size)
            result = self.pdf_validator.validate("trim_size", trim_size, metadata)
            
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.WARNING
            assert "Unusual trim size" in result.warning_message
        
        # Test size that's large but still within reasonable bounds
        large_size = "12 x 15"
        metadata = CodexMetadata(trim_size=large_size)
        result = self.pdf_validator.validate("trim_size", large_size, metadata)
        
        # This should be treated as custom, not unusual (within bounds)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Custom trim size" in result.info_message
    
    def test_trim_size_validation_invalid_format(self):
        """Test validation of invalid trim size formats"""
        invalid_formats = [
            "invalid format",
            "6 by 9",        # Wrong separator
            "six by nine",   # Text instead of numbers
        ]
        
        for trim_size in invalid_formats:
            metadata = CodexMetadata(trim_size=trim_size)
            result = self.pdf_validator.validate("trim_size", trim_size, metadata)
            
            assert result.is_valid is False
            assert result.severity == ValidationSeverity.ERROR
            assert "Invalid trim size format" in result.error_message or "Cannot parse trim size" in result.error_message
        
        # Test empty trim size
        empty_metadata = CodexMetadata(trim_size="")
        result = self.pdf_validator.validate("trim_size", "", empty_metadata)
        assert result.severity == ValidationSeverity.WARNING
        assert "Trim size not specified" in result.warning_message
        
        # Test format that gets parsed correctly (6x9 -> 6 x 9)
        parseable_format = "6x9"
        metadata = CodexMetadata(trim_size=parseable_format)
        result = self.pdf_validator.validate("trim_size", parseable_format, metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Custom trim size" in result.info_message


class TestFileSystemMockingReliability(TestFileSystemIntegration):
    """Test file system operations with mocked scenarios for reliable testing"""
    
    def test_file_access_permission_denied(self):
        """Test behavior when file access is denied"""
        # Create file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock permission denied error
        with patch('os.path.getsize', side_effect=PermissionError("Permission denied")):
            result = self.file_validator.validate(
                "interior_path_filename", 
                "9780132350884_interior.pdf", 
                self.sample_metadata
            )
            
            assert result.is_valid is False
            assert result.severity == ValidationSeverity.ERROR
            assert "Cannot access file" in result.error_message
    
    def test_file_system_io_error(self):
        """Test behavior with general I/O errors"""
        # Create file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Mock I/O error - need to catch the exception in the validator
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('os.path.getsize', side_effect=OSError("I/O error")):
            result = self.file_validator.validate(
                "interior_path_filename", 
                "9780132350884_interior.pdf", 
                self.sample_metadata
            )
            
            assert result.is_valid is False
            assert result.severity == ValidationSeverity.ERROR
            assert "Cannot access file" in result.error_message
    
    def test_network_path_handling(self):
        """Test handling of network paths and UNC paths"""
        # Test with network path format
        network_path = "//server/share/ftp2lsi"
        validator = PDFValidator(ftp_staging_path=network_path)
        
        # Should handle gracefully even if path doesn't exist
        result = validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File not found" in result.error_message
    
    def test_concurrent_file_access(self):
        """Test behavior with concurrent file access scenarios"""
        # Create file
        pdf_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        self._create_mock_pdf_file(pdf_file, size_kb=1000)
        
        # Simulate file being locked/in use - this will cause PDF format validation to fail
        with patch('subprocess.run', side_effect=OSError("File is being used by another process")):
            result = self.pdf_validator.validate(
                "interior_path_filename", 
                "9780132350884_interior.pdf", 
                self.sample_metadata
            )
            
            # The validator should handle the error gracefully but report it as an error
            assert result.is_valid is False
            assert result.severity == ValidationSeverity.ERROR
            assert "Error validating PDF format" in result.error_message
    
    def test_symlink_handling(self):
        """Test handling of symbolic links"""
        # Create actual file
        actual_file = os.path.join(self.temp_dir, "actual_interior.pdf")
        self._create_mock_pdf_file(actual_file, size_kb=1000)
        
        # Create symlink in FTP staging area
        symlink_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        try:
            os.symlink(actual_file, symlink_file)
            
            result = self.file_validator.validate(
                "interior_path_filename", 
                "9780132350884_interior.pdf", 
                self.sample_metadata
            )
            
            # Should follow symlink and validate the target
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.INFO
            assert "File exists" in result.info_message
            
        except OSError:
            # Skip test if symlinks not supported on this system
            pytest.skip("Symbolic links not supported on this system")
    
    def _create_mock_pdf_file(self, file_path: str, size_kb: int = 100):
        """Helper method to create mock PDF files with specified size"""
        content = "Mock PDF content " * (size_kb * 1024 // 17)  # Approximate size
        with open(file_path, 'w') as f:
            f.write(content)


class TestEndToEndFileSystemValidation(TestFileSystemIntegration):
    """End-to-end file system validation tests"""
    
    @patch('subprocess.run')
    def test_complete_file_system_validation_success(self, mock_subprocess):
        """Test complete file system validation with all requirements met"""
        # Create properly named and formatted files
        interior_file = os.path.join(self.ftp_staging_path, "9780132350884_interior.pdf")
        cover_file = os.path.join(self.ftp_staging_path, "9780132350884_cover.pdf")
        
        self._create_mock_pdf_file(interior_file, size_kb=1000)
        self._create_mock_pdf_file(cover_file, size_kb=500)
        
        # Mock successful PDF validation
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
"""
        mock_subprocess.return_value = mock_result
        
        # Test interior file validation
        interior_result = self.pdf_validator.validate(
            "interior_path_filename", 
            "9780132350884_interior.pdf", 
            self.sample_metadata
        )
        
        # Test cover file validation
        cover_result = self.pdf_validator.validate(
            "cover_path_filename", 
            "9780132350884_cover.pdf", 
            self.sample_metadata
        )
        
        # Both should pass all validations
        assert interior_result.is_valid is True
        assert interior_result.severity == ValidationSeverity.INFO
        assert cover_result.is_valid is True
        assert cover_result.severity == ValidationSeverity.INFO
    
    def test_complete_file_system_validation_with_issues(self):
        """Test file system validation with multiple issues"""
        # Create files with various issues
        wrong_interior = os.path.join(self.ftp_staging_path, "wrong_interior.pdf")
        missing_cover = "9780132350884_cover.pdf"  # File doesn't exist
        
        self._create_mock_pdf_file(wrong_interior, size_kb=1)  # Small file, wrong name
        
        # Test interior file with wrong name
        interior_result = self.pdf_validator.validate(
            "interior_path_filename", 
            "wrong_interior.pdf", 
            self.sample_metadata
        )
        
        # Test missing cover file
        cover_result = self.pdf_validator.validate(
            "cover_path_filename", 
            missing_cover, 
            self.sample_metadata
        )
        
        # Should identify multiple issues
        assert interior_result.is_valid is False
        assert "File naming convention error" in interior_result.error_message
        
        assert cover_result.is_valid is False
        assert "File not found" in cover_result.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])