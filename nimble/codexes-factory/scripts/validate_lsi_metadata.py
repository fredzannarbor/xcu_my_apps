#!/usr/bin/env python3
"""
LSI Metadata Validation Utility

This script validates metadata for LSI submission requirements and provides
detailed reports on validation issues and suggested fixes.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import asdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from codexes.modules.distribution.lsi_configuration import LSIConfiguration


class LSIMetadataValidator:
    """Comprehensive LSI metadata validation utility."""
    
    def __init__(self, config_path: str = None, template_path: str = "templates/LSI_ACS_header.csv"):
        """
        Initialize the validator.
        
        Args:
            config_path: Path to LSI configuration file
            template_path: Path to LSI template CSV file
        """
        self.config_path = config_path
        self.template_path = template_path
        
        # Initialize components
        try:
            self.generator = LsiAcsGenerator(
                template_path=template_path,
                config_path=config_path
            )
            logging.info("LSI generator initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize LSI generator: {e}")
            raise
        
        if config_path:
            try:
                self.config = LSIConfiguration(config_path)
                logging.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logging.warning(f"Failed to load configuration: {e}")
                self.config = LSIConfiguration()
        else:
            self.config = LSIConfiguration()
    
    def validate_single_metadata(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """
        Validate a single metadata object for LSI submission.
        
        Args:
            metadata: Metadata object to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_report = {
            'metadata_info': {
                'title': metadata.title,
                'author': metadata.author,
                'isbn13': metadata.isbn13,
                'publisher': metadata.publisher
            },
            'validation_result': None,
            'field_analysis': {},
            'completeness_analysis': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': [],
            'success': False
        }
        
        try:
            # Run comprehensive validation
            validation_result = self.generator.validate_submission(metadata)
            
            validation_report['validation_result'] = {
                'is_valid': validation_result.is_valid,
                'has_blocking_errors': validation_result.has_blocking_errors(),
                'total_errors': len(validation_result.errors),
                'total_warnings': len(validation_result.warnings),
                'errors': validation_result.errors,
                'warnings': validation_result.warnings
            }
            
            # Analyze individual field results
            field_analysis = {}
            for field_result in validation_result.field_results:
                field_analysis[field_result.field_name] = {
                    'is_valid': field_result.is_valid,
                    'error_message': field_result.error_message,
                    'warning_message': field_result.warning_message,
                    'suggested_value': field_result.suggested_value
                }
            
            validation_report['field_analysis'] = field_analysis
            
            # Analyze completeness
            completeness_analysis = self._analyze_completeness(metadata)
            validation_report['completeness_analysis'] = completeness_analysis
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metadata, validation_result, completeness_analysis)
            validation_report['recommendations'] = recommendations
            
            # Identify critical issues
            critical_issues = self._identify_critical_issues(validation_result)
            validation_report['critical_issues'] = critical_issues
            
            validation_report['success'] = True
            
        except Exception as e:
            validation_report['critical_issues'].append(f"Validation failed: {e}")
            logging.error(f"Validation failed for {metadata.title}: {e}")
        
        return validation_report
    
    def _analyze_completeness(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """Analyze metadata completeness for LSI requirements."""
        
        # Define LSI field categories with importance levels
        field_categories = {
            'critical_fields': {
                'fields': ['title', 'author', 'isbn13', 'publisher', 'page_count', 'list_price_usd'],
                'importance': 'Critical - Required for LSI submission'
            },
            'lsi_account_fields': {
                'fields': ['lightning_source_account', 'metadata_contact_dictionary'],
                'importance': 'High - Required for LSI processing'
            },
            'submission_fields': {
                'fields': ['cover_submission_method', 'text_block_submission_method'],
                'importance': 'High - Required for file submission'
            },
            'physical_specs': {
                'fields': ['trim_width_in', 'trim_height_in', 'binding', 'interior_color', 'weight_lbs'],
                'importance': 'Medium - Affects printing and shipping'
            },
            'marketing_fields': {
                'fields': ['summary_short', 'summary_long', 'keywords', 'bisac_codes'],
                'importance': 'Medium - Important for discoverability'
            },
            'contributor_fields': {
                'fields': ['contributor_one_bio', 'contributor_one_affiliations', 'contributor_one_professional_position'],
                'importance': 'Low - Enhances marketing but not required'
            },
            'territorial_fields': {
                'fields': ['territorial_rights', 'us_wholesale_discount', 'returnability'],
                'importance': 'Medium - Affects distribution'
            },
            'optional_fields': {
                'fields': ['series_name', 'series_number', 'illustration_count', 'review_quotes'],
                'importance': 'Low - Optional enhancements'
            }
        }
        
        completeness_analysis = {
            'overall_score': 0.0,
            'category_scores': {},
            'total_fields_analyzed': 0,
            'total_populated_fields': 0,
            'missing_critical': [],
            'missing_high_importance': [],
            'completion_grade': 'F'
        }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Weight mapping for importance levels
        importance_weights = {
            'Critical - Required for LSI submission': 3.0,
            'High - Required for LSI processing': 2.5,
            'High - Required for file submission': 2.5,
            'Medium - Affects printing and shipping': 2.0,
            'Medium - Important for discoverability': 2.0,
            'Medium - Affects distribution': 2.0,
            'Low - Enhances marketing but not required': 1.0,
            'Low - Optional enhancements': 0.5
        }
        
        for category, category_info in field_categories.items():
            fields = category_info['fields']
            importance = category_info['importance']
            weight = importance_weights.get(importance, 1.0)
            
            populated_count = 0
            missing_fields = []
            
            for field in fields:
                completeness_analysis['total_fields_analyzed'] += 1
                value = getattr(metadata, field, None)
                
                if value and (not isinstance(value, str) or value.strip()):
                    populated_count += 1
                    completeness_analysis['total_populated_fields'] += 1
                else:
                    missing_fields.append(field)
                    
                    # Track critical and high importance missing fields
                    if 'Critical' in importance:
                        completeness_analysis['missing_critical'].append(field)
                    elif 'High' in importance:
                        completeness_analysis['missing_high_importance'].append(field)
            
            category_score = (populated_count / len(fields)) * 100 if fields else 0
            completeness_analysis['category_scores'][category] = {
                'score': category_score,
                'populated': populated_count,
                'total': len(fields),
                'missing': missing_fields,
                'importance': importance,
                'weight': weight
            }
            
            # Add to weighted score
            total_weighted_score += category_score * weight
            total_weight += weight
        
        # Calculate overall weighted score
        completeness_analysis['overall_score'] = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # Assign grade
        score = completeness_analysis['overall_score']
        if score >= 90:
            completeness_analysis['completion_grade'] = 'A'
        elif score >= 80:
            completeness_analysis['completion_grade'] = 'B'
        elif score >= 70:
            completeness_analysis['completion_grade'] = 'C'
        elif score >= 60:
            completeness_analysis['completion_grade'] = 'D'
        else:
            completeness_analysis['completion_grade'] = 'F'
        
        return completeness_analysis
    
    def _generate_recommendations(self, metadata: CodexMetadata, validation_result, completeness_analysis) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Critical field recommendations
        if completeness_analysis['missing_critical']:
            recommendations.append(
                f"🚨 CRITICAL: Populate missing required fields: {', '.join(completeness_analysis['missing_critical'])}"
            )
        
        # High importance field recommendations
        if completeness_analysis['missing_high_importance']:
            recommendations.append(
                f"⚠️  HIGH PRIORITY: Add missing LSI fields: {', '.join(completeness_analysis['missing_high_importance'])}"
            )
        
        # Validation-specific recommendations
        if validation_result.has_blocking_errors():
            recommendations.append("🔴 Fix blocking validation errors before LSI submission")
        
        # ISBN recommendations
        if not metadata.isbn13 or len(metadata.isbn13.replace('-', '').replace(' ', '')) != 13:
            recommendations.append("📚 Ensure ISBN-13 is properly formatted (13 digits)")
        
        # Pricing recommendations
        if not metadata.list_price_usd or metadata.list_price_usd == 0:
            recommendations.append("💰 Set appropriate US list price for the book")
        
        # Marketing recommendations
        marketing_score = completeness_analysis['category_scores'].get('marketing_fields', {}).get('score', 0)
        if marketing_score < 50:
            recommendations.append("📈 Improve marketing fields (summary, keywords, BISAC codes) for better discoverability")
        
        # Physical specs recommendations
        physical_score = completeness_analysis['category_scores'].get('physical_specs', {}).get('score', 0)
        if physical_score < 50:
            recommendations.append("📏 Complete physical specifications (trim size, binding, paper type)")
        
        # Contributor recommendations
        if not metadata.contributor_one_bio:
            recommendations.append("👤 Add author biography to enhance book marketing")
        
        # LLM completion recommendation
        overall_score = completeness_analysis['overall_score']
        if overall_score < 70:
            recommendations.append("🤖 Consider using LLM field completion to populate missing fields automatically")
        
        # Configuration recommendations
        if not self.config_path:
            recommendations.append("⚙️  Use LSI configuration file to set publisher-specific defaults")
        
        return recommendations
    
    def _identify_critical_issues(self, validation_result) -> List[str]:
        """Identify critical issues that prevent LSI submission."""
        critical_issues = []
        
        # Check for blocking errors
        if validation_result.has_blocking_errors():
            for error in validation_result.errors:
                if any(keyword in error.lower() for keyword in ['required', 'missing', 'invalid', 'format']):
                    critical_issues.append(f"🚫 {error}")
        
        return critical_issues
    
    def validate_batch(self, metadata_list: List[CodexMetadata], output_dir: str = "validation_reports") -> Dict[str, Any]:
        """
        Validate a batch of metadata objects.
        
        Args:
            metadata_list: List of metadata objects to validate
            output_dir: Directory to save validation reports
            
        Returns:
            Dictionary with batch validation results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        batch_report = {
            'total_validated': len(metadata_list),
            'validation_summary': {
                'passed_validation': 0,
                'failed_validation': 0,
                'has_blocking_errors': 0,
                'average_completeness_score': 0.0,
                'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
            },
            'individual_reports': [],
            'common_issues': {},
            'recommendations_summary': {}
        }
        
        total_completeness_score = 0.0
        all_recommendations = []
        issue_counts = {}
        
        for i, metadata in enumerate(metadata_list):
            logging.info(f"Validating metadata {i+1}/{len(metadata_list)}: {metadata.title}")
            
            # Validate single metadata
            report = self.validate_single_metadata(metadata)
            batch_report['individual_reports'].append(report)
            
            if report['success']:
                # Update summary statistics
                validation_result = report['validation_result']
                completeness_analysis = report['completeness_analysis']
                
                if validation_result['is_valid']:
                    batch_report['validation_summary']['passed_validation'] += 1
                else:
                    batch_report['validation_summary']['failed_validation'] += 1
                
                if validation_result['has_blocking_errors']:
                    batch_report['validation_summary']['has_blocking_errors'] += 1
                
                # Track completeness scores and grades
                score = completeness_analysis['overall_score']
                total_completeness_score += score
                
                grade = completeness_analysis['completion_grade']
                batch_report['validation_summary']['grade_distribution'][grade] += 1
                
                # Collect recommendations
                all_recommendations.extend(report['recommendations'])
                
                # Count common issues
                for error in validation_result['errors']:
                    issue_counts[error] = issue_counts.get(error, 0) + 1
                
                # Save individual report
                report_file = os.path.join(output_dir, f"validation_report_{i+1:04d}.json")
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Calculate average completeness score
        if batch_report['total_validated'] > 0:
            batch_report['validation_summary']['average_completeness_score'] = (
                total_completeness_score / batch_report['total_validated']
            )
        
        # Identify common issues (appearing in >10% of books)
        threshold = max(1, len(metadata_list) * 0.1)
        batch_report['common_issues'] = {
            issue: count for issue, count in issue_counts.items() 
            if count >= threshold
        }
        
        # Summarize recommendations
        recommendation_counts = {}
        for rec in all_recommendations:
            # Extract recommendation type (first few words)
            rec_type = ' '.join(rec.split()[:3])
            recommendation_counts[rec_type] = recommendation_counts.get(rec_type, 0) + 1
        
        batch_report['recommendations_summary'] = recommendation_counts
        
        # Save batch summary
        summary_file = os.path.join(output_dir, "batch_validation_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_report, f, indent=2, ensure_ascii=False)
        
        return batch_report
    
    def generate_validation_report(self, report: Dict[str, Any]) -> str:
        """Generate a human-readable validation report."""
        lines = []
        
        # Header
        metadata_info = report['metadata_info']
        lines.append("=" * 80)
        lines.append(f"LSI METADATA VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Title: {metadata_info['title']}")
        lines.append(f"Author: {metadata_info['author']}")
        lines.append(f"ISBN: {metadata_info['isbn13']}")
        lines.append(f"Publisher: {metadata_info['publisher']}")
        lines.append("")
        
        # Validation summary
        if report['success'] and report['validation_result']:
            validation_result = report['validation_result']
            lines.append("VALIDATION SUMMARY")
            lines.append("-" * 40)
            
            if validation_result['is_valid']:
                lines.append("✅ Overall Status: PASSED")
            else:
                lines.append("❌ Overall Status: FAILED")
            
            lines.append(f"Errors: {validation_result['total_errors']}")
            lines.append(f"Warnings: {validation_result['total_warnings']}")
            lines.append(f"Blocking Errors: {'Yes' if validation_result['has_blocking_errors'] else 'No'}")
            lines.append("")
        
        # Completeness analysis
        if 'completeness_analysis' in report:
            completeness = report['completeness_analysis']
            lines.append("COMPLETENESS ANALYSIS")
            lines.append("-" * 40)
            lines.append(f"Overall Score: {completeness['overall_score']:.1f}% (Grade: {completeness['completion_grade']})")
            lines.append(f"Populated Fields: {completeness['total_populated_fields']}/{completeness['total_fields_analyzed']}")
            lines.append("")
            
            # Category breakdown
            lines.append("Category Breakdown:")
            for category, category_info in completeness['category_scores'].items():
                score = category_info['score']
                populated = category_info['populated']
                total = category_info['total']
                importance = category_info['importance']
                
                status_icon = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
                lines.append(f"  {status_icon} {category.replace('_', ' ').title()}: {score:.1f}% ({populated}/{total})")
                lines.append(f"     {importance}")
                
                if category_info['missing']:
                    lines.append(f"     Missing: {', '.join(category_info['missing'])}")
                lines.append("")
        
        # Critical issues
        if report['critical_issues']:
            lines.append("CRITICAL ISSUES")
            lines.append("-" * 40)
            for issue in report['critical_issues']:
                lines.append(f"  {issue}")
            lines.append("")
        
        # Recommendations
        if report['recommendations']:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 40)
            for i, rec in enumerate(report['recommendations'], 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
        
        # Detailed field analysis (if errors exist)
        if report['success'] and report['validation_result'] and report['validation_result']['total_errors'] > 0:
            lines.append("DETAILED FIELD ANALYSIS")
            lines.append("-" * 40)
            
            for field_name, field_info in report['field_analysis'].items():
                if not field_info['is_valid']:
                    lines.append(f"❌ {field_name}:")
                    lines.append(f"   Error: {field_info['error_message']}")
                    if field_info['suggested_value']:
                        lines.append(f"   Suggested: {field_info['suggested_value']}")
                    lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def load_metadata_from_json(file_path: str) -> CodexMetadata:
    """Load metadata from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return CodexMetadata(**data)


def main():
    """Main CLI interface for LSI metadata validation."""
    parser = argparse.ArgumentParser(description="Validate metadata for LSI submission")
    
    parser.add_argument('input', help="Input metadata file (JSON) or directory")
    parser.add_argument('-o', '--output', default='validation_reports',
                       help="Output directory for validation reports")
    parser.add_argument('-c', '--config', help="LSI configuration file path")
    parser.add_argument('-t', '--template', default='templates/LSI_ACS_header.csv',
                       help="LSI template CSV file path")
    parser.add_argument('--summary-only', action='store_true',
                       help="Show only summary, not detailed reports")
    parser.add_argument('-v', '--verbose', action='store_true',
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize validator
    try:
        validator = LSIMetadataValidator(
            config_path=args.config,
            template_path=args.template
        )
    except Exception as e:
        print(f"❌ Failed to initialize validator: {e}")
        return 1
    
    # Process input
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file validation
        logging.info(f"Validating single file: {input_path}")
        
        try:
            metadata = load_metadata_from_json(str(input_path))
            report = validator.validate_single_metadata(metadata)
            
            if report['success']:
                # Generate and display report
                readable_report = validator.generate_validation_report(report)
                print(readable_report)
                
                # Save detailed report
                if not args.summary_only:
                    os.makedirs(args.output, exist_ok=True)
                    report_file = os.path.join(args.output, "validation_report.json")
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    
                    readable_file = os.path.join(args.output, "validation_report.txt")
                    with open(readable_file, 'w', encoding='utf-8') as f:
                        f.write(readable_report)
                    
                    print(f"\nDetailed reports saved to: {args.output}")
            else:
                print(f"❌ Validation failed: {report.get('critical_issues', ['Unknown error'])}")
                
        except Exception as e:
            print(f"❌ Failed to validate file {input_path}: {e}")
            return 1
    
    elif input_path.is_dir():
        # Batch validation
        logging.info(f"Validating directory: {input_path}")
        
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
        
        # Batch validation
        batch_report = validator.validate_batch(metadata_list, args.output)
        
        # Display summary
        print(f"\n=== BATCH VALIDATION SUMMARY ===")
        print(f"Total files validated: {batch_report['total_validated']}")
        print(f"Passed validation: {batch_report['validation_summary']['passed_validation']}")
        print(f"Failed validation: {batch_report['validation_summary']['failed_validation']}")
        print(f"With blocking errors: {batch_report['validation_summary']['has_blocking_errors']}")
        print(f"Average completeness: {batch_report['validation_summary']['average_completeness_score']:.1f}%")
        
        print(f"\nGrade Distribution:")
        for grade, count in batch_report['validation_summary']['grade_distribution'].items():
            if count > 0:
                print(f"  Grade {grade}: {count} files")
        
        if batch_report['common_issues']:
            print(f"\nCommon Issues:")
            for issue, count in batch_report['common_issues'].items():
                print(f"  {count} files: {issue}")
        
        print(f"\nDetailed reports saved to: {args.output}")
    
    else:
        print(f"Input path not found: {input_path}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())