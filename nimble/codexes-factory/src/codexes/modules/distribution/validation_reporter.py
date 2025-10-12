#!/usr/bin/env python3

"""
Comprehensive Validation Reporter

This module provides detailed validation reporting capabilities for LSI CSV generation,
including field completeness analysis, validation dashboards, and actionable suggestions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import csv

from .lsi_field_validator import LSIFieldValidator, LSIValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Available report formats."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    CSV = "csv"


@dataclass
class FieldCompletenessScore:
    """Field completeness scoring information."""
    field_name: str
    total_records: int
    populated_records: int
    completeness_percentage: float
    quality_score: float  # 0-100 based on validation results
    common_issues: List[str]
    suggestions: List[str]


@dataclass
class ValidationSummary:
    """Summary of validation results."""
    total_records: int
    valid_records: int
    invalid_records: int
    overall_success_rate: float
    total_errors: int
    total_warnings: int
    total_info_issues: int
    field_completeness_scores: List[FieldCompletenessScore]
    most_problematic_fields: List[Tuple[str, int]]  # (field_name, issue_count)
    validation_timestamp: datetime


@dataclass
class ValidationDashboard:
    """Comprehensive validation dashboard data."""
    summary: ValidationSummary
    detailed_results: List[LSIValidationResult]
    field_analysis: Dict[str, Any]
    recommendations: List[str]
    export_ready: bool


class ValidationReporter:
    """Comprehensive validation reporting system."""
    
    def __init__(self, output_dir: str = "logs/validation_reports"):
        """Initialize the validation reporter."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validator = LSIFieldValidator()
    
    def generate_comprehensive_report(self, validation_results: List[LSIValidationResult],
                                    report_format: ReportFormat = ReportFormat.TEXT,
                                    include_suggestions: bool = True) -> str:
        """Generate a comprehensive validation report."""
        
        # Create validation summary
        summary = self._create_validation_summary(validation_results)
        
        # Generate field analysis
        field_analysis = self._analyze_field_performance(validation_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(summary, field_analysis) if include_suggestions else []
        
        # Create dashboard
        dashboard = ValidationDashboard(
            summary=summary,
            detailed_results=validation_results,
            field_analysis=field_analysis,
            recommendations=recommendations,
            export_ready=True
        )
        
        # Generate report in requested format
        if report_format == ReportFormat.TEXT:
            return self._generate_text_report(dashboard)
        elif report_format == ReportFormat.JSON:
            return self._generate_json_report(dashboard)
        elif report_format == ReportFormat.HTML:
            return self._generate_html_report(dashboard)
        elif report_format == ReportFormat.CSV:
            return self._generate_csv_report(dashboard)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
    
    def save_validation_report(self, validation_results: List[LSIValidationResult],
                             filename_prefix: str = "validation_report",
                             formats: List[ReportFormat] = None) -> List[str]:
        """Save validation reports in multiple formats."""
        if formats is None:
            formats = [ReportFormat.TEXT, ReportFormat.JSON]
        
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for format_type in formats:
            try:
                report_content = self.generate_comprehensive_report(
                    validation_results, format_type
                )
                
                # Determine file extension
                extension_map = {
                    ReportFormat.TEXT: "txt",
                    ReportFormat.JSON: "json",
                    ReportFormat.HTML: "html",
                    ReportFormat.CSV: "csv"
                }
                
                filename = f"{filename_prefix}_{timestamp}.{extension_map[format_type]}"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                saved_files.append(str(filepath))
                logger.info(f"Saved validation report: {filepath}")
                
            except Exception as e:
                logger.error(f"Failed to save report in {format_type.value} format: {e}")
        
        return saved_files
    
    def create_validation_dashboard(self, validation_results: List[LSIValidationResult]) -> ValidationDashboard:
        """Create a comprehensive validation dashboard."""
        summary = self._create_validation_summary(validation_results)
        field_analysis = self._analyze_field_performance(validation_results)
        recommendations = self._generate_recommendations(summary, field_analysis)
        
        return ValidationDashboard(
            summary=summary,
            detailed_results=validation_results,
            field_analysis=field_analysis,
            recommendations=recommendations,
            export_ready=True
        )
    
    def _create_validation_summary(self, validation_results: List[LSIValidationResult]) -> ValidationSummary:
        """Create validation summary from results."""
        total_records = len(validation_results)
        valid_records = sum(1 for result in validation_results if result.is_valid)
        invalid_records = total_records - valid_records
        
        overall_success_rate = (valid_records / total_records * 100) if total_records > 0 else 0
        
        total_errors = sum(result.error_count for result in validation_results)
        total_warnings = sum(result.warning_count for result in validation_results)
        total_info_issues = sum(result.info_count for result in validation_results)
        
        # Calculate field completeness scores
        field_completeness_scores = self._calculate_field_completeness(validation_results)
        
        # Find most problematic fields
        field_issue_counts = {}
        for result in validation_results:
            for field_name, field_result in result.field_results.items():
                if not field_result.is_valid:
                    field_issue_counts[field_name] = field_issue_counts.get(field_name, 0) + 1
        
        most_problematic_fields = sorted(
            field_issue_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return ValidationSummary(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            overall_success_rate=overall_success_rate,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info_issues=total_info_issues,
            field_completeness_scores=field_completeness_scores,
            most_problematic_fields=most_problematic_fields,
            validation_timestamp=datetime.now()
        )
    
    def _calculate_field_completeness(self, validation_results: List[LSIValidationResult]) -> List[FieldCompletenessScore]:
        """Calculate field completeness scores."""
        field_stats = {}
        total_records = len(validation_results)
        
        # Collect field statistics
        for result in validation_results:
            for field_name, field_result in result.field_results.items():
                if field_name not in field_stats:
                    field_stats[field_name] = {
                        'total': 0,
                        'populated': 0,
                        'valid': 0,
                        'issues': []
                    }
                
                field_stats[field_name]['total'] += 1
                
                if field_result.value is not None and field_result.value != '':
                    field_stats[field_name]['populated'] += 1
                
                if field_result.is_valid:
                    field_stats[field_name]['valid'] += 1
                else:
                    for issue in field_result.issues:
                        field_stats[field_name]['issues'].append(issue.message)
        
        # Calculate scores
        completeness_scores = []
        for field_name, stats in field_stats.items():
            populated_records = stats['populated']
            completeness_percentage = (populated_records / total_records * 100) if total_records > 0 else 0
            
            # Quality score based on validation success rate
            quality_score = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            # Find common issues
            issue_counts = {}
            for issue in stats['issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            common_issues = [
                issue for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            ]
            
            # Generate suggestions
            suggestions = self._generate_field_suggestions(field_name, completeness_percentage, quality_score, common_issues)
            
            completeness_scores.append(FieldCompletenessScore(
                field_name=field_name,
                total_records=stats['total'],
                populated_records=populated_records,
                completeness_percentage=completeness_percentage,
                quality_score=quality_score,
                common_issues=common_issues,
                suggestions=suggestions
            ))
        
        # Sort by completeness percentage (ascending) to highlight problematic fields
        return sorted(completeness_scores, key=lambda x: x.completeness_percentage)
    
    def _generate_field_suggestions(self, field_name: str, completeness: float, 
                                  quality: float, common_issues: List[str]) -> List[str]:
        """Generate suggestions for improving field quality."""
        suggestions = []
        
        if completeness < 50:
            suggestions.append(f"Field '{field_name}' has low completeness ({completeness:.1f}%). Consider improving data collection or adding fallback values.")
        
        if quality < 80:
            suggestions.append(f"Field '{field_name}' has quality issues ({quality:.1f}% valid). Review validation rules and data sources.")
        
        # Specific suggestions based on field name
        field_lower = field_name.lower()
        
        if 'isbn' in field_lower and quality < 90:
            suggestions.append("ISBN validation issues detected. Ensure ISBNs are properly formatted (10 or 13 digits).")
        
        if 'bisac' in field_lower and quality < 90:
            suggestions.append("BISAC code validation issues. Ensure codes follow format: 3 letters + 6 digits (e.g., FIC014000).")
        
        if 'price' in field_lower and quality < 90:
            suggestions.append("Price validation issues. Ensure prices are valid decimal numbers with 2 decimal places.")
        
        if 'description' in field_lower and completeness < 70:
            suggestions.append("Description fields are important for discoverability. Consider using LLM generation for missing descriptions.")
        
        if 'author' in field_lower and completeness < 90:
            suggestions.append("Author information is critical. Ensure all books have proper author attribution.")
        
        # Suggestions based on common issues
        for issue in common_issues:
            if 'too long' in issue.lower():
                suggestions.append(f"Text length issues in '{field_name}'. Implement intelligent truncation at sentence boundaries.")
            elif 'required field' in issue.lower():
                suggestions.append(f"'{field_name}' is required but often missing. Add validation to data entry process.")
            elif 'invalid format' in issue.lower():
                suggestions.append(f"Format validation issues in '{field_name}'. Review and standardize input formats.")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _analyze_field_performance(self, validation_results: List[LSIValidationResult]) -> Dict[str, Any]:
        """Analyze field performance across all records."""
        analysis = {
            'field_success_rates': {},
            'field_error_patterns': {},
            'field_dependencies': {},
            'improvement_opportunities': []
        }
        
        # Calculate success rates per field
        field_totals = {}
        field_successes = {}
        
        for result in validation_results:
            for field_name, field_result in result.field_results.items():
                field_totals[field_name] = field_totals.get(field_name, 0) + 1
                if field_result.is_valid:
                    field_successes[field_name] = field_successes.get(field_name, 0) + 1
        
        for field_name in field_totals:
            success_rate = (field_successes.get(field_name, 0) / field_totals[field_name]) * 100
            analysis['field_success_rates'][field_name] = success_rate
        
        # Analyze error patterns
        for result in validation_results:
            for field_name, field_result in result.field_results.items():
                if not field_result.is_valid:
                    if field_name not in analysis['field_error_patterns']:
                        analysis['field_error_patterns'][field_name] = {}
                    
                    for issue in field_result.issues:
                        error_type = issue.rule_violated or 'UNKNOWN'
                        analysis['field_error_patterns'][field_name][error_type] = \
                            analysis['field_error_patterns'][field_name].get(error_type, 0) + 1
        
        # Identify improvement opportunities
        for field_name, success_rate in analysis['field_success_rates'].items():
            if success_rate < 80:
                analysis['improvement_opportunities'].append({
                    'field': field_name,
                    'success_rate': success_rate,
                    'priority': 'HIGH' if success_rate < 50 else 'MEDIUM',
                    'common_errors': list(analysis['field_error_patterns'].get(field_name, {}).keys())[:3]
                })
        
        return analysis
    
    def _generate_recommendations(self, summary: ValidationSummary, 
                                field_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Overall recommendations
        if summary.overall_success_rate < 80:
            recommendations.append(
                f"Overall validation success rate is {summary.overall_success_rate:.1f}%. "
                "Focus on improving data quality and validation processes."
            )
        
        if summary.total_errors > summary.total_records * 0.1:
            recommendations.append(
                "High error rate detected. Review data sources and implement stricter input validation."
            )
        
        # Field-specific recommendations
        low_completeness_fields = [
            score for score in summary.field_completeness_scores 
            if score.completeness_percentage < 70
        ]
        
        if low_completeness_fields:
            field_names = [score.field_name for score in low_completeness_fields[:3]]
            recommendations.append(
                f"Low completeness in critical fields: {', '.join(field_names)}. "
                "Consider implementing fallback data sources or LLM generation."
            )
        
        # Error pattern recommendations
        for opportunity in field_analysis['improvement_opportunities'][:5]:
            field_name = opportunity['field']
            success_rate = opportunity['success_rate']
            common_errors = opportunity['common_errors']
            
            if common_errors:
                recommendations.append(
                    f"Field '{field_name}' has {success_rate:.1f}% success rate. "
                    f"Common issues: {', '.join(common_errors)}. "
                    "Review validation rules and data processing logic."
                )
        
        # Technical recommendations
        if summary.total_warnings > summary.total_errors:
            recommendations.append(
                "Many validation warnings detected. Consider upgrading warnings to errors "
                "for critical fields to improve data quality."
            )
        
        # Process improvement recommendations
        recommendations.append(
            "Implement automated validation in the data entry process to catch issues early."
        )
        
        recommendations.append(
            "Set up regular validation monitoring to track data quality trends over time."
        )
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_text_report(self, dashboard: ValidationDashboard) -> str:
        """Generate text format validation report."""
        lines = []
        summary = dashboard.summary
        
        # Header
        lines.append("LSI CSV VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {summary.validation_timestamp}")
        lines.append("")
        
        # Executive Summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 30)
        lines.append(f"Total Records Processed: {summary.total_records}")
        lines.append(f"Valid Records: {summary.valid_records} ({summary.overall_success_rate:.1f}%)")
        lines.append(f"Invalid Records: {summary.invalid_records}")
        lines.append(f"Total Issues: {summary.total_errors + summary.total_warnings + summary.total_info_issues}")
        lines.append(f"  - Errors: {summary.total_errors}")
        lines.append(f"  - Warnings: {summary.total_warnings}")
        lines.append(f"  - Info: {summary.total_info_issues}")
        lines.append("")
        
        # Field Completeness Analysis
        lines.append("FIELD COMPLETENESS ANALYSIS")
        lines.append("-" * 40)
        lines.append(f"{'Field Name':<30} {'Completeness':<12} {'Quality':<10} {'Issues'}")
        lines.append("-" * 70)
        
        for score in summary.field_completeness_scores[:15]:  # Top 15 fields
            issues_count = len(score.common_issues)
            lines.append(
                f"{score.field_name:<30} "
                f"{score.completeness_percentage:>8.1f}% "
                f"{score.quality_score:>8.1f}% "
                f"{issues_count:>6}"
            )
        lines.append("")
        
        # Most Problematic Fields
        if summary.most_problematic_fields:
            lines.append("MOST PROBLEMATIC FIELDS")
            lines.append("-" * 30)
            for field_name, issue_count in summary.most_problematic_fields[:10]:
                lines.append(f"  {field_name}: {issue_count} issues")
            lines.append("")
        
        # Recommendations
        if dashboard.recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 20)
            for i, recommendation in enumerate(dashboard.recommendations, 1):
                lines.append(f"{i}. {recommendation}")
                lines.append("")
        
        # Field-Specific Suggestions
        lines.append("FIELD-SPECIFIC SUGGESTIONS")
        lines.append("-" * 35)
        for score in summary.field_completeness_scores:
            if score.suggestions and (score.completeness_percentage < 80 or score.quality_score < 80):
                lines.append(f"{score.field_name}:")
                for suggestion in score.suggestions:
                    lines.append(f"  • {suggestion}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, dashboard: ValidationDashboard) -> str:
        """Generate JSON format validation report."""
        report_data = {
            'metadata': {
                'report_type': 'LSI_CSV_Validation',
                'generated_at': dashboard.summary.validation_timestamp.isoformat(),
                'version': '1.0'
            },
            'summary': asdict(dashboard.summary),
            'field_analysis': dashboard.field_analysis,
            'recommendations': dashboard.recommendations,
            'detailed_results': [
                {
                    'record_index': i,
                    'is_valid': result.is_valid,
                    'error_count': result.error_count,
                    'warning_count': result.warning_count,
                    'failed_fields': result.get_failed_fields(),
                    'issues': [
                        {
                            'field': issue.field_name,
                            'severity': issue.severity.value,
                            'message': issue.message,
                            'rule_violated': issue.rule_violated
                        }
                        for issue in result.get_all_issues()
                    ]
                }
                for i, result in enumerate(dashboard.detailed_results)
            ]
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_html_report(self, dashboard: ValidationDashboard) -> str:
        """Generate HTML format validation report."""
        summary = dashboard.summary
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LSI CSV Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 10px; background-color: #e8f4f8; border-radius: 5px; }}
        .metric h3 {{ margin: 0; color: #2c3e50; }}
        .metric p {{ margin: 5px 0; font-size: 24px; font-weight: bold; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
        .recommendations ul {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LSI CSV Validation Report</h1>
        <p>Generated: {summary.validation_timestamp}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Records</h3>
            <p>{summary.total_records}</p>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <p class="{'success' if summary.overall_success_rate >= 80 else 'warning' if summary.overall_success_rate >= 60 else 'error'}">{summary.overall_success_rate:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Total Errors</h3>
            <p class="error">{summary.total_errors}</p>
        </div>
        <div class="metric">
            <h3>Total Warnings</h3>
            <p class="warning">{summary.total_warnings}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Field Completeness Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Field Name</th>
                    <th>Completeness</th>
                    <th>Quality Score</th>
                    <th>Common Issues</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for score in summary.field_completeness_scores[:20]:
            completeness_class = 'success' if score.completeness_percentage >= 80 else 'warning' if score.completeness_percentage >= 60 else 'error'
            quality_class = 'success' if score.quality_score >= 80 else 'warning' if score.quality_score >= 60 else 'error'
            
            html += f"""
                <tr>
                    <td>{score.field_name}</td>
                    <td class="{completeness_class}">{score.completeness_percentage:.1f}%</td>
                    <td class="{quality_class}">{score.quality_score:.1f}%</td>
                    <td>{len(score.common_issues)} issues</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
"""
        
        if dashboard.recommendations:
            html += """
    <div class="section">
        <h2>Recommendations</h2>
        <div class="recommendations">
            <ul>
"""
            for recommendation in dashboard.recommendations:
                html += f"                <li>{recommendation}</li>\n"
            
            html += """
            </ul>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def _generate_csv_report(self, dashboard: ValidationDashboard) -> str:
        """Generate CSV format validation report."""
        lines = []
        
        # Header
        lines.append("Field Name,Completeness %,Quality Score %,Total Records,Populated Records,Common Issues Count")
        
        # Field data
        for score in dashboard.summary.field_completeness_scores:
            lines.append(
                f'"{score.field_name}",'
                f'{score.completeness_percentage:.2f},'
                f'{score.quality_score:.2f},'
                f'{score.total_records},'
                f'{score.populated_records},'
                f'{len(score.common_issues)}'
            )
        
        return "\n".join(lines)


def generate_validation_report(validation_results: List[LSIValidationResult],
                             output_dir: str = "logs/validation_reports",
                             formats: List[ReportFormat] = None) -> List[str]:
    """Convenience function to generate validation reports."""
    reporter = ValidationReporter(output_dir)
    return reporter.save_validation_report(validation_results, formats=formats)


def create_validation_dashboard_data(validation_results: List[LSIValidationResult]) -> Dict[str, Any]:
    """Create validation dashboard data for web interfaces."""
    reporter = ValidationReporter()
    dashboard = reporter.create_validation_dashboard(validation_results)
    
    return {
        'summary': asdict(dashboard.summary),
        'field_analysis': dashboard.field_analysis,
        'recommendations': dashboard.recommendations,
        'charts_data': {
            'success_rate_by_field': {
                field_name: dashboard.field_analysis['field_success_rates'].get(field_name, 0)
                for field_name in list(dashboard.field_analysis['field_success_rates'].keys())[:20]
            },
            'completeness_distribution': [
                {
                    'field': score.field_name,
                    'completeness': score.completeness_percentage,
                    'quality': score.quality_score
                }
                for score in dashboard.summary.field_completeness_scores[:15]
            ]
        }
    }