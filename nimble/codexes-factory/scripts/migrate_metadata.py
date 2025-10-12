#!/usr/bin/env python3
"""
LSI Metadata Migration Utility

This script helps migrate existing metadata to the enhanced LSI field format,
populating missing LSI-specific fields and validating completeness.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from codexes.modules.distribution.lsi_configuration import LSIConfiguration


class MetadataMigrator:
    """Utility class for migrating metadata to enhanced LSI format."""
    
    def __init__(self, config_path: Optional[str] = None, use_llm: bool = True):
        """
        Initialize the metadata migrator.
        
        Args:
            config_path: Path to LSI configuration file
            use_llm: Whether to use LLM for field completion
        """
        self.config_path = config_path
        self.use_llm = use_llm
        
        # Initialize components
        if config_path:
            self.config = LSIConfiguration(config_path)
        else:
            self.config = LSIConfiguration()
        
        if use_llm:
            try:
                self.llm_completer = LLMFieldCompleter()
                logging.info("LLM field completer initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize LLM completer: {e}")
                self.llm_completer = None
                self.use_llm = False
        else:
            self.llm_completer = None
        
        # Initialize generator for validation
        self.generator = LsiAcsGenerator(
            template_path="templates/LSI_ACS_header.csv",
            config_path=config_path
        )
    
    def migrate_single_metadata(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """
        Migrate a single metadata object to enhanced LSI format.
        
        Args:
            metadata: Original metadata object
            
        Returns:
            Dictionary with migration results
        """
        migration_result = {
            'original_metadata': asdict(metadata),
            'enhanced_metadata': None,
            'fields_added': [],
            'fields_completed': [],
            'validation_result': None,
            'success': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Create enhanced metadata copy
            enhanced_metadata = CodexMetadata(**asdict(metadata))
            
            # Step 2: Apply configuration defaults
            fields_added = self._apply_configuration_defaults(enhanced_metadata)
            migration_result['fields_added'] = fields_added
            
            # Step 3: Use LLM completion if available
            if self.use_llm and self.llm_completer:
                try:
                    completed_metadata = self.llm_completer.complete_missing_fields(enhanced_metadata)
                    
                    # Track which fields were completed
                    fields_completed = []
                    for field_name in dir(completed_metadata):
                        if not field_name.startswith('_') and not callable(getattr(completed_metadata, field_name)):
                            original_value = getattr(enhanced_metadata, field_name, None)
                            completed_value = getattr(completed_metadata, field_name, None)
                            
                            if (not original_value or (isinstance(original_value, str) and not original_value.strip())) and \
                               completed_value and (not isinstance(completed_value, str) or completed_value.strip()):
                                fields_completed.append(field_name)
                    
                    enhanced_metadata = completed_metadata
                    migration_result['fields_completed'] = fields_completed
                    
                except Exception as e:
                    migration_result['warnings'].append(f"LLM completion failed: {e}")
            
            # Step 4: Validate enhanced metadata
            validation_result = self.generator.validate_submission(enhanced_metadata)
            migration_result['validation_result'] = {
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'has_blocking_errors': validation_result.has_blocking_errors()
            }
            
            # Step 5: Apply suggested fixes if validation failed
            if not validation_result.is_valid:
                enhanced_metadata = self._apply_validation_fixes(enhanced_metadata, validation_result)
                
                # Re-validate after fixes
                revalidation_result = self.generator.validate_submission(enhanced_metadata)
                migration_result['validation_result']['after_fixes'] = {
                    'is_valid': revalidation_result.is_valid,
                    'errors': revalidation_result.errors,
                    'warnings': revalidation_result.warnings
                }
            
            migration_result['enhanced_metadata'] = asdict(enhanced_metadata)
            migration_result['success'] = True
            
        except Exception as e:
            migration_result['errors'].append(f"Migration failed: {e}")
            logging.error(f"Migration failed for {metadata.title}: {e}")
        
        return migration_result
    
    def _apply_configuration_defaults(self, metadata: CodexMetadata) -> List[str]:
        """Apply configuration defaults to metadata."""
        fields_added = []
        
        # LSI-specific fields that can be populated from configuration
        config_field_mapping = {
            'lightning_source_account': 'lightning_source_account',
            'cover_submission_method': 'cover_submission_method',
            'text_block_submission_method': 'text_block_submission_method',
            'carton_pack_quantity': 'carton_pack_quantity',
            'territorial_rights': 'territorial_rights',
            'returnability': 'returnability',
            'order_type_eligibility': 'order_type_eligibility',
            'edition_number': 'edition_number',
            'edition_description': 'edition_description',
            'metadata_contact_dictionary': 'metadata_contact_dictionary'
        }
        
        for metadata_field, config_field in config_field_mapping.items():
            current_value = getattr(metadata, metadata_field, None)
            if not current_value:
                config_value = self.config.get_default_value(config_field)
                if config_value:
                    setattr(metadata, metadata_field, config_value)
                    fields_added.append(metadata_field)
        
        # Apply imprint-specific defaults if imprint is set
        if metadata.imprint:
            imprint_config = self.config.get_imprint_config(metadata.imprint)
            if imprint_config:
                for field, value in imprint_config.default_values.items():
                    if hasattr(metadata, field) and not getattr(metadata, field, None):
                        setattr(metadata, field, value)
                        fields_added.append(field)
        
        return fields_added
    
    def _apply_validation_fixes(self, metadata: CodexMetadata, validation_result) -> CodexMetadata:
        """Apply suggested fixes from validation results."""
        
        for field_result in validation_result.field_results:
            if not field_result.is_valid and field_result.suggested_value:
                if hasattr(metadata, field_result.field_name):
                    setattr(metadata, field_result.field_name, field_result.suggested_value)
                    logging.info(f"Applied validation fix for {field_result.field_name}: {field_result.suggested_value}")
        
        # Common fixes for missing required fields
        if not metadata.title:
            metadata.title = "Untitled Book"
        
        if not metadata.author:
            metadata.author = "Unknown Author"
        
        if not metadata.publisher:
            metadata.publisher = self.config.get_default_value('publisher') or "Independent Publisher"
        
        # ISBN format fixes
        if metadata.isbn13:
            metadata.isbn13 = self._fix_isbn_format(metadata.isbn13)
        
        return metadata
    
    def _fix_isbn_format(self, isbn: str) -> str:
        """Fix common ISBN format issues."""
        if not isbn:
            return isbn
        
        # Remove all non-digit characters
        clean_isbn = ''.join(c for c in str(isbn) if c.isdigit())
        
        # Handle ISBN-10 to ISBN-13 conversion
        if len(clean_isbn) == 10:
            # Convert ISBN-10 to ISBN-13
            isbn13_base = '978' + clean_isbn[:-1]
            check_digit = self._calculate_isbn13_check_digit(isbn13_base)
            return isbn13_base + str(check_digit)
        
        return clean_isbn
    
    def _calculate_isbn13_check_digit(self, isbn12: str) -> int:
        """Calculate ISBN-13 check digit."""
        total = 0
        for i, digit in enumerate(isbn12):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit
    
    def migrate_batch(self, metadata_list: List[CodexMetadata], output_dir: str = "migrated_metadata") -> Dict[str, Any]:
        """
        Migrate a batch of metadata objects.
        
        Args:
            metadata_list: List of metadata objects to migrate
            output_dir: Directory to save migration results
            
        Returns:
            Dictionary with batch migration results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        batch_result = {
            'total_processed': len(metadata_list),
            'successful_migrations': 0,
            'failed_migrations': 0,
            'results': [],
            'summary': {
                'fields_added_total': 0,
                'fields_completed_total': 0,
                'validation_issues': 0
            }
        }
        
        for i, metadata in enumerate(metadata_list):
            logging.info(f"Migrating metadata {i+1}/{len(metadata_list)}: {metadata.title}")
            
            # Migrate single metadata
            result = self.migrate_single_metadata(metadata)
            batch_result['results'].append(result)
            
            if result['success']:
                batch_result['successful_migrations'] += 1
                batch_result['summary']['fields_added_total'] += len(result['fields_added'])
                batch_result['summary']['fields_completed_total'] += len(result['fields_completed'])
                
                if result['validation_result'] and not result['validation_result']['is_valid']:
                    batch_result['summary']['validation_issues'] += 1
                
                # Save enhanced metadata
                if result['enhanced_metadata']:
                    output_file = os.path.join(output_dir, f"enhanced_metadata_{i+1:04d}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result['enhanced_metadata'], f, indent=2, ensure_ascii=False)
            else:
                batch_result['failed_migrations'] += 1
        
        # Save batch summary
        summary_file = os.path.join(output_dir, "migration_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, indent=2, ensure_ascii=False)
        
        return batch_result
    
    def analyze_metadata_completeness(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """
        Analyze metadata completeness for LSI requirements.
        
        Args:
            metadata: Metadata object to analyze
            
        Returns:
            Dictionary with completeness analysis
        """
        # LSI field categories
        lsi_field_categories = {
            'required_fields': [
                'title', 'author', 'isbn13', 'publisher', 'page_count', 'list_price_usd'
            ],
            'lsi_account_fields': [
                'lightning_source_account', 'metadata_contact_dictionary'
            ],
            'submission_fields': [
                'cover_submission_method', 'text_block_submission_method',
                'jacket_path_filename', 'interior_path_filename', 'cover_path_filename'
            ],
            'contributor_fields': [
                'contributor_one_bio', 'contributor_one_affiliations',
                'contributor_one_professional_position', 'contributor_one_location'
            ],
            'physical_fields': [
                'weight_lbs', 'carton_pack_quantity', 'trim_width_in', 'trim_height_in',
                'interior_color', 'interior_paper', 'cover_type'
            ],
            'marketing_fields': [
                'summary_short', 'keywords', 'review_quotes', 'bisac_codes'
            ],
            'territorial_fields': [
                'territorial_rights', 'us_wholesale_discount', 'uk_wholesale_discount',
                'eu_wholesale_discount', 'returnability'
            ]
        }
        
        analysis = {
            'total_lsi_fields': 0,
            'populated_fields': 0,
            'empty_fields': 0,
            'category_analysis': {},
            'completion_percentage': 0.0,
            'missing_required': [],
            'recommendations': []
        }
        
        all_lsi_fields = []
        for category_fields in lsi_field_categories.values():
            all_lsi_fields.extend(category_fields)
        
        analysis['total_lsi_fields'] = len(all_lsi_fields)
        
        # Analyze each category
        for category, fields in lsi_field_categories.items():
            category_analysis = {
                'total_fields': len(fields),
                'populated_fields': 0,
                'empty_fields': [],
                'completion_percentage': 0.0
            }
            
            for field in fields:
                value = getattr(metadata, field, None)
                if value and (not isinstance(value, str) or value.strip()):
                    category_analysis['populated_fields'] += 1
                    analysis['populated_fields'] += 1
                else:
                    category_analysis['empty_fields'].append(field)
                    analysis['empty_fields'] += 1
                    
                    if category == 'required_fields':
                        analysis['missing_required'].append(field)
            
            category_analysis['completion_percentage'] = (
                category_analysis['populated_fields'] / category_analysis['total_fields'] * 100
            )
            
            analysis['category_analysis'][category] = category_analysis
        
        analysis['completion_percentage'] = analysis['populated_fields'] / analysis['total_lsi_fields'] * 100
        
        # Generate recommendations
        if analysis['missing_required']:
            analysis['recommendations'].append(
                f"Critical: Missing required fields: {', '.join(analysis['missing_required'])}"
            )
        
        if analysis['category_analysis']['marketing_fields']['completion_percentage'] < 50:
            analysis['recommendations'].append(
                "Consider using LLM completion for marketing fields (summary, keywords, etc.)"
            )
        
        if analysis['category_analysis']['contributor_fields']['completion_percentage'] < 25:
            analysis['recommendations'].append(
                "Contributor information is sparse - consider enhancing author bio and affiliations"
            )
        
        return analysis


def load_metadata_from_json(file_path: str) -> CodexMetadata:
    """Load metadata from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return CodexMetadata(**data)


def save_metadata_to_json(metadata: CodexMetadata, file_path: str):
    """Save metadata to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)


def main():
    """Main CLI interface for metadata migration."""
    parser = argparse.ArgumentParser(description="Migrate metadata to enhanced LSI format")
    
    parser.add_argument('input', help="Input metadata file (JSON) or directory")
    parser.add_argument('-o', '--output', default='migrated_metadata', 
                       help="Output directory for migrated metadata")
    parser.add_argument('-c', '--config', help="LSI configuration file path")
    parser.add_argument('--no-llm', action='store_true', 
                       help="Disable LLM field completion")
    parser.add_argument('--analyze-only', action='store_true',
                       help="Only analyze completeness, don't migrate")
    parser.add_argument('-v', '--verbose', action='store_true',
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize migrator
    migrator = MetadataMigrator(
        config_path=args.config,
        use_llm=not args.no_llm
    )
    
    # Process input
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file migration
        logging.info(f"Processing single file: {input_path}")
        
        try:
            metadata = load_metadata_from_json(str(input_path))
            
            if args.analyze_only:
                # Analyze completeness only
                analysis = migrator.analyze_metadata_completeness(metadata)
                print(f"\n=== Metadata Completeness Analysis ===")
                print(f"Title: {metadata.title}")
                print(f"Overall completion: {analysis['completion_percentage']:.1f}%")
                print(f"Populated fields: {analysis['populated_fields']}/{analysis['total_lsi_fields']}")
                
                if analysis['missing_required']:
                    print(f"\n❌ Missing required fields: {', '.join(analysis['missing_required'])}")
                
                print(f"\n📊 Category Analysis:")
                for category, cat_analysis in analysis['category_analysis'].items():
                    print(f"  {category}: {cat_analysis['completion_percentage']:.1f}% "
                          f"({cat_analysis['populated_fields']}/{cat_analysis['total_fields']})")
                
                if analysis['recommendations']:
                    print(f"\n💡 Recommendations:")
                    for rec in analysis['recommendations']:
                        print(f"  - {rec}")
            else:
                # Migrate metadata
                result = migrator.migrate_single_metadata(metadata)
                
                if result['success']:
                    # Save enhanced metadata
                    os.makedirs(args.output, exist_ok=True)
                    output_file = os.path.join(args.output, "enhanced_metadata.json")
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result['enhanced_metadata'], f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Migration successful!")
                    print(f"   Enhanced metadata saved to: {output_file}")
                    print(f"   Fields added: {len(result['fields_added'])}")
                    print(f"   Fields completed: {len(result['fields_completed'])}")
                    
                    if result['validation_result']['is_valid']:
                        print(f"   ✅ Validation passed")
                    else:
                        print(f"   ⚠️  Validation issues: {len(result['validation_result']['errors'])} errors")
                else:
                    print(f"❌ Migration failed: {result['errors']}")
                    
        except Exception as e:
            logging.error(f"Failed to process file {input_path}: {e}")
            return 1
    
    elif input_path.is_dir():
        # Batch migration
        logging.info(f"Processing directory: {input_path}")
        
        # Find all JSON files
        json_files = list(input_path.glob("*.json"))
        
        if not json_files:
            print(f"No JSON files found in {input_path}")
            return 1
        
        # Load all metadata
        metadata_list = []
        for json_file in json_files:
            try:
                metadata = load_metadata_from_json(str(json_file))
                metadata_list.append(metadata)
            except Exception as e:
                logging.error(f"Failed to load {json_file}: {e}")
        
        if not metadata_list:
            print("No valid metadata files found")
            return 1
        
        if args.analyze_only:
            # Batch analysis
            print(f"\n=== Batch Metadata Analysis ({len(metadata_list)} files) ===")
            
            total_completion = 0
            missing_required_count = 0
            
            for i, metadata in enumerate(metadata_list):
                analysis = migrator.analyze_metadata_completeness(metadata)
                total_completion += analysis['completion_percentage']
                
                if analysis['missing_required']:
                    missing_required_count += 1
                
                print(f"{i+1:3d}. {metadata.title[:50]:<50} {analysis['completion_percentage']:5.1f}%")
            
            avg_completion = total_completion / len(metadata_list)
            print(f"\nAverage completion: {avg_completion:.1f}%")
            print(f"Files with missing required fields: {missing_required_count}/{len(metadata_list)}")
        else:
            # Batch migration
            batch_result = migrator.migrate_batch(metadata_list, args.output)
            
            print(f"\n=== Batch Migration Results ===")
            print(f"Total processed: {batch_result['total_processed']}")
            print(f"Successful: {batch_result['successful_migrations']}")
            print(f"Failed: {batch_result['failed_migrations']}")
            print(f"Fields added total: {batch_result['summary']['fields_added_total']}")
            print(f"Fields completed total: {batch_result['summary']['fields_completed_total']}")
            print(f"Validation issues: {batch_result['summary']['validation_issues']}")
            print(f"\nResults saved to: {args.output}")
    
    else:
        print(f"Input path not found: {input_path}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())