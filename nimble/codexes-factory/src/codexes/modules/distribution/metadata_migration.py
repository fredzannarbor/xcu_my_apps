# src/codexes/modules/distribution/metadata_migration.py

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
from pathlib import Path

from ..metadata.metadata_models import CodexMetadata
from .llm_field_completer import LLMFieldCompleter
from .lsi_configuration import LSIConfiguration

logger = logging.getLogger(__name__)


class MetadataMigrationUtility:
    """
    Utility for migrating existing metadata to the new LSI-enhanced format.
    
    This class provides methods to:
    1. Migrate existing metadata objects to include new LSI fields
    2. Validate migrated metadata completeness
    3. Populate missing LSI fields from existing data
    4. Batch process multiple metadata files
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 field_completer: Optional[LLMFieldCompleter] = None):
        """
        Initialize the migration utility.
        
        Args:
            config_path: Path to LSI configuration file
            field_completer: LLMFieldCompleter instance for auto-completion
        """
        self.config = LSIConfiguration(config_path) if config_path else None
        self.field_completer = field_completer or LLMFieldCompleter()
        
        # Track migration statistics
        self.migration_stats = {
            'total_processed': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'fields_populated': 0,
            'validation_errors': 0
        }
    
    def migrate_metadata_object(self, 
                               old_metadata: Dict[str, Any],
                               auto_complete: bool = True,
                               model: str = "gpt-3.5-turbo") -> Tuple[CodexMetadata, List[str]]:
        """
        Migrate a single metadata object to the new format.
        
        Args:
            old_metadata: Dictionary containing old metadata
            auto_complete: Whether to auto-complete missing LSI fields
            model: LLM model to use for auto-completion
            
        Returns:
            Tuple of (migrated_metadata, validation_warnings)
        """
        warnings = []
        
        try:
            # Create new metadata object from old data
            if isinstance(old_metadata, dict):
                # Filter out any keys that don't exist in the new model
                valid_fields = {k: v for k, v in old_metadata.items() 
                              if hasattr(CodexMetadata, k)}
                migrated_metadata = CodexMetadata(**valid_fields)
            else:
                # Assume it's already a CodexMetadata object
                migrated_metadata = old_metadata
            
            # Apply default values for new LSI fields
            migrated_metadata = self._apply_lsi_defaults(migrated_metadata)
            
            # Auto-complete missing fields if requested
            if auto_complete:
                try:
                    migrated_metadata = self.field_completer.complete_missing_fields(
                        metadata=migrated_metadata,
                        model=model
                    )
                    logger.info("Auto-completion successful for metadata migration")
                except Exception as e:
                    warnings.append(f"Auto-completion failed: {e}")
                    logger.warning(f"Auto-completion failed during migration: {e}")
            
            # Validate the migrated metadata
            validation_warnings = self._validate_migrated_metadata(migrated_metadata)
            warnings.extend(validation_warnings)
            
            self.migration_stats['successful_migrations'] += 1
            
        except Exception as e:
            logger.error(f"Failed to migrate metadata: {e}")
            self.migration_stats['failed_migrations'] += 1
            # Return a basic metadata object with warnings
            migrated_metadata = CodexMetadata()
            warnings.append(f"Migration failed: {e}")
        
        self.migration_stats['total_processed'] += 1
        return migrated_metadata, warnings
    
    def migrate_metadata_file(self, 
                            input_path: str, 
                            output_path: Optional[str] = None,
                            auto_complete: bool = True,
                            model: str = "gpt-3.5-turbo") -> bool:
        """
        Migrate a metadata file to the new format.
        
        Args:
            input_path: Path to the input metadata JSON file
            output_path: Path for the output file (if None, overwrites input)
            auto_complete: Whether to auto-complete missing LSI fields
            model: LLM model to use for auto-completion
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            # Load existing metadata
            with open(input_path, 'r', encoding='utf-8') as f:
                old_metadata = json.load(f)
            
            logger.info(f"Migrating metadata file: {input_path}")
            
            # Migrate the metadata
            migrated_metadata, warnings = self.migrate_metadata_object(
                old_metadata, auto_complete, model
            )
            
            # Determine output path
            if output_path is None:
                output_path = input_path
            
            # Save migrated metadata
            migrated_metadata.save_to_file(output_path)
            
            # Log warnings if any
            if warnings:
                logger.warning(f"Migration warnings for {input_path}: {warnings}")
            
            logger.info(f"Successfully migrated metadata to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate metadata file {input_path}: {e}")
            return False
    
    def batch_migrate_directory(self, 
                              input_dir: str, 
                              output_dir: Optional[str] = None,
                              pattern: str = "*.json",
                              auto_complete: bool = True,
                              model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        Batch migrate all metadata files in a directory.
        
        Args:
            input_dir: Directory containing metadata files
            output_dir: Output directory (if None, overwrites in place)
            pattern: File pattern to match (default: *.json)
            auto_complete: Whether to auto-complete missing LSI fields
            model: LLM model to use for auto-completion
            
        Returns:
            Dictionary with migration results and statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir) if output_dir else input_path
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all metadata files
        metadata_files = list(input_path.glob(pattern))
        
        if not metadata_files:
            logger.warning(f"No metadata files found in {input_dir} matching pattern {pattern}")
            return {'success': False, 'message': 'No files found'}
        
        logger.info(f"Found {len(metadata_files)} metadata files to migrate")
        
        # Reset statistics
        self.migration_stats = {
            'total_processed': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'fields_populated': 0,
            'validation_errors': 0
        }
        
        results = {
            'successful_files': [],
            'failed_files': [],
            'warnings': {}
        }
        
        # Migrate each file
        for file_path in metadata_files:
            try:
                output_file_path = output_path / file_path.name
                success = self.migrate_metadata_file(
                    str(file_path), 
                    str(output_file_path),
                    auto_complete,
                    model
                )
                
                if success:
                    results['successful_files'].append(str(file_path))
                else:
                    results['failed_files'].append(str(file_path))
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results['failed_files'].append(str(file_path))
        
        # Add statistics to results
        results['statistics'] = self.migration_stats.copy()
        results['success'] = len(results['failed_files']) == 0
        
        logger.info(f"Batch migration completed. Success: {len(results['successful_files'])}, "
                   f"Failed: {len(results['failed_files'])}")
        
        return results
    
    def validate_metadata_completeness(self, 
                                     metadata: CodexMetadata) -> Dict[str, Any]:
        """
        Validate the completeness of migrated metadata.
        
        Args:
            metadata: Metadata object to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_complete': True,
            'missing_critical_fields': [],
            'missing_optional_fields': [],
            'populated_lsi_fields': [],
            'completion_percentage': 0.0
        }
        
        # Define critical fields that must be present
        critical_fields = [
            'title', 'author', 'isbn13', 'publisher', 'publication_date',
            'page_count', 'list_price_usd'
        ]
        
        # Define important LSI fields
        lsi_fields = [
            'contributor_one_bio', 'contributor_one_affiliations',
            'contributor_one_professional_position', 'contributor_one_location',
            'weight_lbs', 'territorial_rights', 'cover_submission_method',
            'text_block_submission_method', 'carton_pack_quantity'
        ]
        
        # Check critical fields
        for field in critical_fields:
            value = getattr(metadata, field, None)
            if not value or (isinstance(value, (int, float)) and value == 0):
                validation_result['missing_critical_fields'].append(field)
                validation_result['is_complete'] = False
        
        # Check LSI fields
        populated_count = 0
        for field in lsi_fields:
            value = getattr(metadata, field, None)
            if value and str(value).strip():
                validation_result['populated_lsi_fields'].append(field)
                populated_count += 1
            else:
                validation_result['missing_optional_fields'].append(field)
        
        # Calculate completion percentage
        total_fields = len(critical_fields) + len(lsi_fields)
        populated_critical = len(critical_fields) - len(validation_result['missing_critical_fields'])
        total_populated = populated_critical + populated_count
        validation_result['completion_percentage'] = (total_populated / total_fields) * 100
        
        return validation_result
    
    def generate_migration_report(self, 
                                metadata: CodexMetadata,
                                output_path: Optional[str] = None) -> str:
        """
        Generate a detailed migration report for a metadata object.
        
        Args:
            metadata: Migrated metadata object
            output_path: Path to save the report (optional)
            
        Returns:
            Report content as string
        """
        validation = self.validate_metadata_completeness(metadata)
        
        report_lines = [
            "# Metadata Migration Report",
            f"Generated: {metadata.processing_timestamp}",
            "",
            "## Basic Information",
            f"Title: {metadata.title}",
            f"Author: {metadata.author}",
            f"ISBN: {metadata.isbn13}",
            f"Publisher: {metadata.publisher}",
            "",
            "## Migration Status",
            f"Overall Completion: {validation['completion_percentage']:.1f}%",
            f"Critical Fields Complete: {'✓' if not validation['missing_critical_fields'] else '✗'}",
            "",
            "## LSI Field Population"
        ]
        
        # Add populated LSI fields
        if validation['populated_lsi_fields']:
            report_lines.append("### Populated Fields:")
            for field in validation['populated_lsi_fields']:
                value = getattr(metadata, field, '')
                report_lines.append(f"- {field}: {str(value)[:50]}...")
        
        # Add missing fields
        if validation['missing_optional_fields']:
            report_lines.append("\n### Missing Optional Fields:")
            for field in validation['missing_optional_fields']:
                report_lines.append(f"- {field}")
        
        # Add critical missing fields
        if validation['missing_critical_fields']:
            report_lines.append("\n### Missing Critical Fields:")
            for field in validation['missing_critical_fields']:
                report_lines.append(f"- {field} (REQUIRED)")
        
        # Add recommendations
        report_lines.extend([
            "",
            "## Recommendations",
            "- Review missing critical fields and populate manually",
            "- Consider running auto-completion for missing optional fields",
            "- Validate ISBN format and pricing information",
            "- Verify territorial rights and submission preferences"
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save report if path provided
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"Migration report saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save migration report: {e}")
        
        return report_content
    
    def _apply_lsi_defaults(self, metadata: CodexMetadata) -> CodexMetadata:
        """
        Apply default values for new LSI fields.
        
        Args:
            metadata: Metadata object to update
            
        Returns:
            Updated metadata object
        """
        # Apply configuration defaults if available
        if self.config:
            # Apply default values from configuration
            if not metadata.lightning_source_account:
                metadata.lightning_source_account = self.config.get_default_value('lightning_source_account')
            
            if not metadata.cover_submission_method:
                metadata.cover_submission_method = self.config.get_default_value('cover_submission_method')
            
            if not metadata.text_block_submission_method:
                metadata.text_block_submission_method = self.config.get_default_value('text_block_submission_method')
        
        # Apply standard defaults
        if not metadata.territorial_rights:
            metadata.territorial_rights = 'World'
        
        if not metadata.carton_pack_quantity:
            metadata.carton_pack_quantity = '1'
        
        if not metadata.cover_submission_method:
            metadata.cover_submission_method = 'FTP'
        
        if not metadata.text_block_submission_method:
            metadata.text_block_submission_method = 'FTP'
        
        # Generate file paths if ISBN is available
        if metadata.isbn13 and not metadata.interior_path_filename:
            safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:20]
            metadata.publisher_reference_id = safe_title or metadata.isbn13
            metadata.interior_path_filename = f"ftp2lsi/{metadata.publisher_reference_id}/{metadata.isbn13}_interior.pdf"
            metadata.cover_path_filename = f"ftp2lsi/{metadata.publisher_reference_id}/{metadata.isbn13}_cover.pdf"
        
        return metadata
    
    def _validate_migrated_metadata(self, metadata: CodexMetadata) -> List[str]:
        """
        Validate migrated metadata and return warnings.
        
        Args:
            metadata: Metadata object to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check for critical missing fields
        if not metadata.title:
            warnings.append("Title is missing")
        
        if not metadata.author:
            warnings.append("Author is missing")
        
        if not metadata.isbn13:
            warnings.append("ISBN13 is missing")
        elif len(metadata.isbn13.replace('-', '')) != 13:
            warnings.append("ISBN13 format appears invalid")
        
        if not metadata.publisher:
            warnings.append("Publisher is missing")
        
        if metadata.list_price_usd <= 0:
            warnings.append("List price is not set or invalid")
        
        if metadata.page_count <= 0:
            warnings.append("Page count is not set or invalid")
        
        # Check LSI-specific fields
        if not metadata.territorial_rights:
            warnings.append("Territorial rights not specified")
        
        if not metadata.contributor_one_bio and metadata.author:
            warnings.append("Contributor biography is missing")
        
        return warnings
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """
        Get current migration statistics.
        
        Returns:
            Dictionary with migration statistics
        """
        return self.migration_stats.copy()


def create_migration_script():
    """
    Create a standalone migration script for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate metadata to LSI-enhanced format')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-c', '--config', help='LSI configuration file path')
    parser.add_argument('--no-auto-complete', action='store_true', 
                       help='Disable auto-completion of missing fields')
    parser.add_argument('--model', default='gpt-3.5-turbo', 
                       help='LLM model for auto-completion')
    parser.add_argument('--batch', action='store_true', 
                       help='Batch process directory')
    parser.add_argument('--report', help='Generate migration report to file')
    
    args = parser.parse_args()
    
    # Initialize migration utility
    migrator = MetadataMigrationUtility(config_path=args.config)
    
    if args.batch:
        # Batch migration
        results = migrator.batch_migrate_directory(
            input_dir=args.input,
            output_dir=args.output,
            auto_complete=not args.no_auto_complete,
            model=args.model
        )
        
        print(f"Batch migration completed:")
        print(f"  Successful: {len(results['successful_files'])}")
        print(f"  Failed: {len(results['failed_files'])}")
        print(f"  Statistics: {results['statistics']}")
        
    else:
        # Single file migration
        success = migrator.migrate_metadata_file(
            input_path=args.input,
            output_path=args.output,
            auto_complete=not args.no_auto_complete,
            model=args.model
        )
        
        if success:
            print(f"Successfully migrated {args.input}")
            
            # Generate report if requested
            if args.report:
                with open(args.output or args.input, 'r') as f:
                    migrated_data = json.load(f)
                migrated_metadata = CodexMetadata(**migrated_data)
                report = migrator.generate_migration_report(migrated_metadata, args.report)
                print(f"Migration report saved to {args.report}")
        else:
            print(f"Failed to migrate {args.input}")


if __name__ == '__main__':
    create_migration_script()