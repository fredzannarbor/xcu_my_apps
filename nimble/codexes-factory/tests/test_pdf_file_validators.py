# tests/test_pdf_file_validators.py

import pytest
import os
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from codexes.modules.verifiers.field_validators import (
    PDFValidator,
    FileExistenceValidator
)
from codexes.modules.verifiers.validation_framework import ValidationSeverity
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestPDFValidator:
    """Test PDFValidator class"""
    
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.validator = PDFValidator(ftp_staging_path=self.temp_dir)
        self.metadata = CodexMetadata(
            isbn13="9780132350884",
            page_count=200,
            trim_size="6 x 9"
        )
    
    def teardown_method(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_can_validate(self):
        assert self.validator.can_validate("interior_path_filename") is True
        assert self.validator.can_validate("cover_path_filename") is True
        assert self.validator.can_validate("jacket_path_filename") is True
        assert self.validator.can_validate("trim_size") is True
        assert self.validator.can_validate("page_count") is True
        assert self.validator.can_validate("isbn13") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_file_path(self):
        result = self.validator.validate("interior_path_filename", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "No file path specified" in result.warning_message
    
    def test_file_not_found(self):
        result = self.validator.validate("interior_path_filename", "nonexistent.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File not found in FTP staging area" in result.error_message
    
    def test_non_pdf_file(self):
        # Create a non-PDF file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = self.validator.validate("interior_path_filename", "test.txt", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File must be PDF format" in result.error_message
    
    def test_incorrect_file_naming_convention(self):
        # Create a PDF file with wrong name
        test_file = os.path.join(self.temp_dir, "wrong_name.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        result = self.validator.validate("interior_path_filename", "wrong_name.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File naming convention error" in result.error_message
        assert "9780132350884_interior.pdf" in result.suggested_value
    
    @patch('subprocess.run')
    def test_pdf_format_check_success(self, mock_subprocess):
        # Create a properly named PDF file
        test_file = os.path.join(self.temp_dir, "9780132350884_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        # Mock pdfinfo output indicating PDF/X-1a compliance
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PDF version: 1.4\nPDF/X-1a compliant\nPages: 200"
        mock_subprocess.return_value = mock_result
        
        result = self.validator.validate("interior_path_filename", "9780132350884_interior.pdf", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid PDF file" in result.info_message
    
    @patch('subprocess.run')
    def test_pdf_format_check_no_compliance(self, mock_subprocess):
        # Create a properly named PDF file
        test_file = os.path.join(self.temp_dir, "9780132350884_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        # Mock pdfinfo output without PDF/X-1a compliance
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PDF version: 1.4\nPages: 200"
        mock_subprocess.return_value = mock_result
        
        result = self.validator.validate("interior_path_filename", "9780132350884_interior.pdf", self.metadata)
        assert result.is_valid is True
        # The result should be WARNING when PDF format compliance cannot be verified
        assert result.severity == ValidationSeverity.WARNING
        assert "PDF format compliance cannot be verified" in result.message
    
    @patch('subprocess.run')
    def test_pdf_page_count_mismatch(self, mock_subprocess):
        # Create a properly named PDF file
        test_file = os.path.join(self.temp_dir, "9780132350884_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        # Mock pdfinfo output with different page count
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PDF version: 1.4\nPages: 150\nPage size: 432 x 648 pts (6 x 9 inches)"
        mock_subprocess.return_value = mock_result
        
        result = self.validator.validate("interior_path_filename", "9780132350884_interior.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Page count mismatch" in result.error_message
        assert "PDF has 150 pages, metadata specifies 200 pages" in result.error_message
    
    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_pdfinfo_not_available(self, mock_subprocess):
        # Create a properly named PDF file
        test_file = os.path.join(self.temp_dir, "9780132350884_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        result = self.validator.validate("interior_path_filename", "9780132350884_interior.pdf", self.metadata)
        assert result.is_valid is True
        # When pdfinfo is not available, the PDF format check returns a warning, which should be propagated
        assert result.severity == ValidationSeverity.WARNING
        assert "PDF format validation tools not available" in result.message
    
    def test_validate_trim_size_standard(self):
        result = self.validator.validate("trim_size", "6 x 9", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Standard trim size" in result.info_message
    
    def test_validate_trim_size_custom(self):
        result = self.validator.validate("trim_size", "6.5 x 9.25", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Custom trim size" in result.info_message
    
    def test_validate_trim_size_unusual(self):
        result = self.validator.validate("trim_size", "2 x 3", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Unusual trim size" in result.warning_message
    
    def test_validate_trim_size_invalid_format(self):
        result = self.validator.validate("trim_size", "invalid format", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid trim size format" in result.error_message
    
    def test_validate_page_count_valid(self):
        result = self.validator.validate("page_count", 200, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid page count" in result.info_message
    
    def test_validate_page_count_too_short(self):
        result = self.validator.validate("page_count", 20, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Very short book" in result.warning_message
        assert "LSI minimum is typically 24 pages" in result.warning_message
    
    def test_validate_page_count_odd(self):
        result = self.validator.validate("page_count", 199, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Odd page count" in result.warning_message
        assert "Perfect bound books typically have even page counts" in result.warning_message
    
    def test_validate_page_count_very_long(self):
        result = self.validator.validate("page_count", 1500, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Very long book" in result.warning_message
    
    def test_validate_page_count_invalid(self):
        result = self.validator.validate("page_count", "not a number", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid page count format" in result.error_message
    
    def test_validate_page_count_zero(self):
        result = self.validator.validate("page_count", 0, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Page count not specified" in result.warning_message
    
    def test_validate_page_count_negative(self):
        result = self.validator.validate("page_count", -5, self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid page count" in result.error_message
        assert "Must be at least 1 page" in result.error_message
    
    def test_file_naming_convention_validation_no_isbn(self):
        metadata_no_isbn = CodexMetadata()
        result = self.validator.validate("isbn13", "", metadata_no_isbn)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "No ISBN provided" in result.info_message
    
    def test_file_naming_convention_validation_with_issues(self):
        metadata_with_files = CodexMetadata(
            isbn13="9780132350884",
            interior_path_filename="wrong_interior.pdf",
            cover_path_filename="9780132350884_cover.pdf"
        )
        result = self.validator.validate("isbn13", "9780132350884", metadata_with_files)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File naming convention issues" in result.error_message
        assert "Interior file should be named: 9780132350884_interior.pdf" in result.error_message
    
    def test_file_naming_convention_validation_correct(self):
        metadata_with_files = CodexMetadata(
            isbn13="9780132350884",
            interior_path_filename="9780132350884_interior.pdf",
            cover_path_filename="9780132350884_cover.pdf"
        )
        result = self.validator.validate("isbn13", "9780132350884", metadata_with_files)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "File naming convention is correct" in result.info_message


class TestFileExistenceValidator:
    """Test FileExistenceValidator class"""
    
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.validator = FileExistenceValidator(ftp_staging_path=self.temp_dir)
        self.metadata = CodexMetadata()
    
    def teardown_method(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_can_validate(self):
        assert self.validator.can_validate("interior_path_filename") is True
        assert self.validator.can_validate("cover_path_filename") is True
        assert self.validator.can_validate("jacket_path_filename") is True
        assert self.validator.can_validate("cover_image_path") is True
        assert self.validator.can_validate("cover_thumbnail_path") is True
        assert self.validator.can_validate("marketing_image") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_file_path(self):
        result = self.validator.validate("interior_path_filename", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "No file path specified" in result.info_message
    
    def test_file_exists_ftp_staging(self):
        # Create a test file in FTP staging area with sufficient content to avoid small file warning
        test_file = os.path.join(self.temp_dir, "test_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("test content " * 10000)  # Make it large enough to avoid small file warning
        
        result = self.validator.validate("interior_path_filename", "test_interior.pdf", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "File exists" in result.info_message
        assert "KB)" in result.info_message  # Should show file size
    
    def test_file_not_found_ftp_staging(self):
        result = self.validator.validate("interior_path_filename", "nonexistent.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File not found" in result.error_message
    
    def test_file_exists_other_path(self):
        # Create a test file for non-FTP staging paths
        test_file = os.path.join(self.temp_dir, "cover.jpg")
        with open(test_file, 'w') as f:
            f.write("test image content")
        
        result = self.validator.validate("cover_image_path", test_file, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "File exists" in result.info_message
    
    def test_file_not_found_other_path(self):
        result = self.validator.validate("cover_image_path", "/nonexistent/path/image.jpg", self.metadata)
        assert result.is_valid is True  # Warning, not error for non-FTP files
        assert result.severity == ValidationSeverity.WARNING
        assert "File not found" in result.warning_message
    
    def test_path_is_directory(self):
        # Create a directory instead of file
        test_dir = os.path.join(self.temp_dir, "test_directory")
        os.makedirs(test_dir)
        
        result = self.validator.validate("interior_path_filename", "test_directory", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Path exists but is not a file" in result.error_message
    
    def test_empty_file(self):
        # Create an empty file
        test_file = os.path.join(self.temp_dir, "empty.pdf")
        with open(test_file, 'w') as f:
            pass  # Create empty file
        
        result = self.validator.validate("interior_path_filename", "empty.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File is empty" in result.error_message
    
    def test_large_file_warning(self):
        # Create a large file (simulate by mocking os.path.getsize)
        test_file = os.path.join(self.temp_dir, "large.pdf")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with patch('os.path.getsize', return_value=150 * 1024 * 1024):  # 150MB
            result = self.validator.validate("interior_path_filename", "large.pdf", self.metadata)
            assert result.is_valid is True
            assert result.severity == ValidationSeverity.WARNING
            assert "Large file size" in result.warning_message
            assert "Consider optimizing" in result.warning_message
    
    def test_small_pdf_warning(self):
        # Create a small PDF file
        test_file = os.path.join(self.temp_dir, "small.pdf")
        with open(test_file, 'w') as f:
            f.write("small")  # Very small content
        
        result = self.validator.validate("interior_path_filename", "small.pdf", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Small PDF file" in result.warning_message
        assert "Verify file integrity" in result.warning_message
    
    @patch('os.path.getsize', side_effect=OSError("Permission denied"))
    def test_file_access_error(self, mock_getsize):
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.pdf")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = self.validator.validate("interior_path_filename", "test.pdf", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Cannot access file" in result.error_message


class TestPDFValidatorIntegration:
    """Integration tests for PDF validation with real-world scenarios"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.validator = PDFValidator(ftp_staging_path=self.temp_dir)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_complete_pdf_validation_success(self, mock_subprocess):
        """Test complete PDF validation with all checks passing"""
        # Create properly named PDF file
        test_file = os.path.join(self.temp_dir, "9780132350884_interior.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        # Mock successful pdfinfo output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
PDF version: 1.4
PDF/X-1a compliant
Pages: 200
Page size: 432 x 648 pts (6 x 9 inches)
"""
        mock_subprocess.return_value = mock_result
        
        metadata = CodexMetadata(
            isbn13="9780132350884",
            page_count=200,
            trim_size="6 x 9"
        )
        
        result = self.validator.validate("interior_path_filename", "9780132350884_interior.pdf", metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid PDF file" in result.info_message
    
    @patch('subprocess.run')
    def test_complete_pdf_validation_with_issues(self, mock_subprocess):
        """Test PDF validation with multiple issues"""
        # Create improperly named PDF file
        test_file = os.path.join(self.temp_dir, "wrong_name.pdf")
        with open(test_file, 'w') as f:
            f.write("fake pdf content")
        
        metadata = CodexMetadata(
            isbn13="9780132350884",
            page_count=200,
            trim_size="6 x 9"
        )
        
        result = self.validator.validate("interior_path_filename", "wrong_name.pdf", metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "File naming convention error" in result.error_message
    
    def test_trim_size_consistency_validation(self):
        """Test trim size validation with various formats"""
        test_cases = [
            ("6 x 9", True, ValidationSeverity.INFO),
            ("6.5 x 9.25", True, ValidationSeverity.INFO),
            ("2 x 3", True, ValidationSeverity.WARNING),  # Unusual size
            ("invalid", False, ValidationSeverity.ERROR),
            ("", True, ValidationSeverity.WARNING),  # Empty
        ]
        
        for trim_size, expected_valid, expected_severity in test_cases:
            result = self.validator.validate("trim_size", trim_size, CodexMetadata())
            assert result.is_valid == expected_valid
            assert result.severity == expected_severity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])