# tests/test_metadata_migration.py

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from codexes.modules.distribution.metadata_migration import MetadataMigrationUtility
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter


class TestMetadataMigrationUtility:
    """Test suite for metadata migration utility."""
    
    @pytest.fixture
    def sample_old_metadata(self):
        """Sample old metadata format for testing."""
        return {
            'title': 'The Art of Programming',
            'author': 'John Doe',
            'isbn13': '978-1234567890',
            'publisher': 'Tech Books Inc',
            'publication_date': '2023-01-15',
            'page_count': 250,
            'list_price_usd': 29.99,
            'summary_short': 'A comprehensive guide to programming',
            'summary_long': 'This book covers all aspects of modern programming...',
            'keywords': 'programming; software; development',
            'bisac_codes': 'COM051000; COM051010'
            # Note: Missing all the new LSI fields
        }
    
    @pytest.fixture
    def mock_field_completer(self):
        """Mock field completer for testing."""
        completer = Mock(spec=LLMFieldCompleter)
        completer.complete_missing_fields.return_value = CodexMetadata(
            title='The Art of Programming',
            author='John Doe',
            contributor_one_bio='John Doe is a software engineer with 15 years of experience.',
            contributor_one_affiliations='Tech University',
            contributor_one_professional_position='Senior Software Engineer',
            weight_lbs='1.2',
            territorial_rights='World'
        )
        return completer
    
    def test_migration_utility_initialization(self):
        """Test migration utility initialization."""
        migrator = MetadataMigrationUtility()
        
        assert migrator.field_completer is not None
        assert isinstance(migrator.migration_stats, dict)
        assert migrator.migration_stats['total_processed'] == 0
    
    def test_migrate_metadata_object_basic(self, sample_old_metadata, mock_field_completer):
        """Test basic metadata object migration."""
        migrator = MetadataMigrationUtility(field_completer=mock_field_completer)
        
        migrated_metadata, warnings = migrator.migrate_metadata_object(
            sample_old_metadata, 
            auto_complete=True
        )
        
        # Verify basic fields are preserved
        assert migrated_metadata.title == 'The Art of Programming'
        assert migrated_metadata.author == 'John Doe'
        assert migrated_metadata.isbn13 == '978-1234567890'
        
        # Verify new LSI fields have defaults
        assert migrated_metadata.territorial_rights == 'World'
        assert migrated_metadata.cover_submission_method == 'FTP'
        assert migrated_metadata.carton_pack_quantity == '1'
        
        # Verify auto-completion was called
        mock_field_completer.complete_missing_fields.assert_called_once()
        
        # Verify statistics
        assert migrator.migration_stats['successful_migrations'] == 1
        assert migrator.migration_stats['total_processed'] == 1
    
    def test_migrate_metadata_object_without_auto_complete(self, sample_old_metadata):
        """Test metadata migration without auto-completion."""
        migrator = MetadataMigrationUtility()
        
        migrated_metadata, warnings = migrator.migrate_metadata_object(
            sample_old_metadata, 
            auto_complete=False
        )
        
        # Verify basic fields are preserved
        assert migrated_metadata.title == 'The Art of Programming'
        assert migrated_metadata.author == 'John Doe'
        
        # Verify LSI defaults are applied
        assert migrated_metadata.territorial_rights == 'World'
        assert migrated_metadata.cover_submission_method == 'FTP'
        
        # Verify file paths are generated
        assert migrated_metadata.publisher_reference_id != ''
        assert 'ftp2lsi' in migrated_metadata.interior_path_filename
        assert migrated_metadata.isbn13 in migrated_metadata.interior_path_filename
    
    def test_migrate_metadata_file(self, sample_old_metadata, mock_field_completer):
        """Test migration of a metadata file."""
        migrator = MetadataMigrationUtility(field_completer=mock_field_completer)
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_input:
            json.dump(sample_old_metadata, temp_input, indent=2)
            input_path = temp_input.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_output:
            output_path = temp_output.name
        
        try:
            # Migrate the file
            success = migrator.migrate_metadata_file(
                input_path=input_path,
                output_path=output_path,
                auto_complete=True
            )
            
            assert success
            
            # Verify output file exists and contains migrated data
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                migrated_data = json.load(f)
            
            assert migrated_data['title'] == 'The Art of Programming'
            assert migrated_data['territorial_rights'] == 'World'
            assert 'contributor_one_bio' in migrated_data
            
        finally:
            # Clean up
            os.unlink(input_path)
            os.unlink(output_path)
    
    def test_batch_migrate_directory(self, sample_old_metadata, mock_field_completer):
        """Test batch migration of a directory."""
        migrator = MetadataMigrationUtility(field_completer=mock_field_completer)
        
        # Create temporary directory with multiple metadata files
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / 'input'
            output_dir = Path(temp_dir) / 'output'
            input_dir.mkdir()
            output_dir.mkdir()
            
            # Create multiple test files
            for i in range(3):
                test_metadata = sample_old_metadata.copy()
                test_metadata['title'] = f'Test Book {i+1}'
                test_metadata['isbn13'] = f'978-123456789{i}'
                
                with open(input_dir / f'metadata_{i+1}.json', 'w') as f:
                    json.dump(test_metadata, f, indent=2)
            
            # Run batch migration
            results = migrator.batch_migrate_directory(
                input_dir=str(input_dir),
                output_dir=str(output_dir),
                auto_complete=True
            )
            
            # Verify results
            assert results['success']
            assert len(results['successful_files']) == 3
            assert len(results['failed_files']) == 0
            assert results['statistics']['successful_migrations'] == 3
            
            # Verify output files exist
            for i in range(3):
                output_file = output_dir / f'metadata_{i+1}.json'
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    migrated_data = json.load(f)
                assert migrated_data['title'] == f'Test Book {i+1}'
                assert migrated_data['territorial_rights'] == 'World'
    
    def test_validate_metadata_completeness(self):
        """Test metadata completeness validation."""
        migrator = MetadataMigrationUtility()
        
        # Test complete metadata
        complete_metadata = CodexMetadata(
            title='Complete Book',
            author='Complete Author',
            isbn13='978-1234567890',
            publisher='Complete Publisher',
            publication_date='2023-01-15',
            page_count=200,
            list_price_usd=25.99,
            contributor_one_bio='Author bio',
            contributor_one_affiliations='University',
            weight_lbs='1.0',
            territorial_rights='World'
        )
        
        validation = migrator.validate_metadata_completeness(complete_metadata)
        
        assert validation['is_complete']
        assert len(validation['missing_critical_fields']) == 0
        assert len(validation['populated_lsi_fields']) > 0
        assert validation['completion_percentage'] > 80
        
        # Test incomplete metadata
        incomplete_metadata = CodexMetadata(
            title='Incomplete Book',
            # Missing many critical fields
        )
        
        validation = migrator.validate_metadata_completeness(incomplete_metadata)
        
        assert not validation['is_complete']
        assert len(validation['missing_critical_fields']) > 0
        assert validation['completion_percentage'] <= 50
    
    def test_generate_migration_report(self):
        """Test migration report generation."""
        migrator = MetadataMigrationUtility()
        
        metadata = CodexMetadata(
            title='Test Book',
            author='Test Author',
            isbn13='978-1234567890',
            publisher='Test Publisher',
            contributor_one_bio='Test bio',
            territorial_rights='World'
        )
        
        report = migrator.generate_migration_report(metadata)
        
        assert '# Metadata Migration Report' in report
        assert 'Test Book' in report
        assert 'Test Author' in report
        assert 'Migration Status' in report
        assert 'LSI Field Population' in report
        assert 'Recommendations' in report
    
    def test_apply_lsi_defaults(self):
        """Test application of LSI default values."""
        migrator = MetadataMigrationUtility()
        
        metadata = CodexMetadata(
            title='Test Book',
            isbn13='978-1234567890'
        )
        
        updated_metadata = migrator._apply_lsi_defaults(metadata)
        
        # Verify defaults are applied
        assert updated_metadata.territorial_rights == 'World'
        assert updated_metadata.carton_pack_quantity == '1'
        assert updated_metadata.cover_submission_method == 'FTP'
        assert updated_metadata.text_block_submission_method == 'FTP'
        
        # Verify file paths are generated
        assert updated_metadata.publisher_reference_id != ''
        assert 'ftp2lsi' in updated_metadata.interior_path_filename
        assert updated_metadata.isbn13 in updated_metadata.interior_path_filename
    
    def test_validate_migrated_metadata(self):
        """Test validation of migrated metadata."""
        migrator = MetadataMigrationUtility()
        
        # Test metadata with missing critical fields
        incomplete_metadata = CodexMetadata(
            title='',  # Missing
            author='Test Author',
            isbn13='invalid-isbn',  # Invalid format
            list_price_usd=0  # Invalid price
        )
        
        warnings = migrator._validate_migrated_metadata(incomplete_metadata)
        
        assert len(warnings) > 0
        assert any('Title is missing' in w for w in warnings)
        assert any('ISBN13 format appears invalid' in w for w in warnings)
        assert any('List price is not set or invalid' in w for w in warnings)
        
        # Test complete metadata
        complete_metadata = CodexMetadata(
            title='Complete Book',
            author='Complete Author',
            isbn13='978-1234567890',
            publisher='Complete Publisher',
            publication_date='2023-01-15',
            page_count=200,
            list_price_usd=25.99,
            territorial_rights='World'
        )
        
        warnings = migrator._validate_migrated_metadata(complete_metadata)
        
        # Should have minimal warnings for complete metadata
        assert len([w for w in warnings if 'missing' in w.lower()]) <= 1
    
    def test_migration_statistics_tracking(self, sample_old_metadata):
        """Test migration statistics tracking."""
        migrator = MetadataMigrationUtility()
        
        # Initial statistics
        stats = migrator.get_migration_statistics()
        assert stats['total_processed'] == 0
        assert stats['successful_migrations'] == 0
        
        # Migrate some metadata
        migrator.migrate_metadata_object(sample_old_metadata, auto_complete=False)
        migrator.migrate_metadata_object(sample_old_metadata, auto_complete=False)
        
        # Check updated statistics
        stats = migrator.get_migration_statistics()
        assert stats['total_processed'] == 2
        assert stats['successful_migrations'] == 2
        assert stats['failed_migrations'] == 0
    
    def test_error_handling_in_migration(self):
        """Test error handling during migration."""
        migrator = MetadataMigrationUtility()
        
        # Test with invalid metadata
        invalid_metadata = "not a dictionary"
        
        migrated_metadata, warnings = migrator.migrate_metadata_object(
            invalid_metadata, 
            auto_complete=False
        )
        
        # Should return a basic metadata object with warnings
        assert isinstance(migrated_metadata, CodexMetadata)
        assert len(warnings) > 0
        assert any('Migration failed' in w for w in warnings)
        
        # Check statistics
        stats = migrator.get_migration_statistics()
        assert stats['failed_migrations'] > 0


if __name__ == '__main__':
    pytest.main([__file__])