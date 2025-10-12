"""
LSI Field Completion Reporter Module

This module provides functionality for generating reports on LSI field completion status.
It helps track which fields were completed, how they were completed, and provides statistics
on field completion quality.
"""

import os
import json
import csv
import logging
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import FieldMappingRegistry, MappingStrategy, DirectMappingStrategy, DefaultMappingStrategy, ComputedMappingStrategy

logger = logging.getLogger(__name__)


@dataclass
class FieldCompletionData:
    """Data class representing completion data for a single field."""
    field_name: str
    strategy_type: str
    value: str
    source: str
    is_empty: bool


@dataclass
class ReportStatistics:
    """Data class representing statistics for a field completion report."""
    total_fields: int
    populated_fields: int
    empty_fields: int
    completion_percentage: float
    strategy_counts: Dict[str, int] = field(default_factory=dict)
    source_counts: Dict[str, int] = field(default_factory=dict)


class LSIFieldCompletionReporter:
    """
    Reporter for LSI field completion status.
    
    This class provides functionality for generating reports on LSI field completion status,
    including which fields were completed, how they were completed, and statistics on field
    completion quality.
    """
    
    def __init__(self, registry: FieldMappingRegistry):
        """
        Initialize the LSI field completion reporter.
        
        Args:
            registry: FieldMappingRegistry instance to use for field mapping
        """
        self.registry = registry
        logger.info("LSI Field Completion Reporter initialized")
    
    def generate_field_strategy_report(self, metadata: CodexMetadata, lsi_headers: List[str],
                                     output_dir: str = "output/reports",
                                     formats: List[str] = ["csv", "html", "json"]) -> Dict[str, str]:
        """
        Generate a report on field completion strategies and results.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            output_dir: Directory to save reports
            formats: List of report formats to generate (csv, html, json)
            
        Returns:
            Dictionary mapping format to output file path
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            isbn = getattr(metadata, 'isbn13', 'unknown')
            
            # Generate report data
            report_data = self._generate_report_data(metadata, lsi_headers)
            
            # Calculate statistics
            stats = self._calculate_statistics(report_data)
            
            # Generate reports in requested formats
            output_files = {}
            
            if "csv" in formats:
                csv_path = os.path.join(output_dir, f"field_report_{isbn}_{timestamp}.csv")
                self._generate_csv_report(report_data, csv_path)
                output_files["csv"] = csv_path
            
            if "html" in formats:
                html_path = os.path.join(output_dir, f"field_report_{isbn}_{timestamp}.html")
                self._generate_html_report(report_data, metadata, stats, html_path)
                output_files["html"] = html_path
            
            if "json" in formats:
                json_path = os.path.join(output_dir, f"field_report_{isbn}_{timestamp}.json")
                self._generate_json_report(report_data, metadata, stats, json_path)
                output_files["json"] = json_path
            
            logger.info(f"Generated field strategy report for {metadata.title} in {len(formats)} formats")
            return output_files
            
        except Exception as e:
            logger.error(f"Error generating field strategy report: {e}")
            return {}
    
    def _generate_report_data(self, metadata: CodexMetadata, lsi_headers: List[str]) -> List[FieldCompletionData]:
        """
        Generate report data for each field.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            
        Returns:
            List of FieldCompletionData objects
        """
        report_data = []
        
        for header in lsi_headers:
            strategy = self.registry.get_strategy(header)
            strategy_type = type(strategy).__name__ if strategy else "None"
            
            # Get the field value
            value = ""
            if strategy:
                try:
                    # Create a minimal context
                    context = {
                        "field_name": header,
                        "lsi_headers": lsi_headers,
                        "current_row_data": {},
                        "metadata": metadata
                    }
                    
                    # Map the field
                    value = strategy.map_field(metadata, context)
                except Exception as e:
                    logger.warning(f"Error mapping field '{header}': {e}")
            
            # Determine the source of the value
            source = self._determine_field_source(metadata, header, strategy, value)
            
            # Check if the field is empty
            is_empty = not value or value.strip() == ""
            
            # Create field completion data
            field_data = FieldCompletionData(
                field_name=header,
                strategy_type=strategy_type,
                value=value,
                source=source,
                is_empty=is_empty
            )
            
            report_data.append(field_data)
        
        return report_data
    
    def _determine_field_source(self, metadata: CodexMetadata, field_name: str, 
                              strategy: Optional[MappingStrategy], value: str) -> str:
        """
        Determine the source of a field value.
        
        Args:
            metadata: CodexMetadata object
            field_name: Name of the field
            strategy: MappingStrategy used for the field
            value: Field value
            
        Returns:
            Source description string
        """
        if not value or value.strip() == "":
            return "Empty"
        
        if not strategy:
            return "None"
        
        if isinstance(strategy, DirectMappingStrategy):
            metadata_field = getattr(strategy, 'metadata_field', None)
            if metadata_field:
                return f"Direct ({metadata_field})"
            return "Direct"
        
        if isinstance(strategy, DefaultMappingStrategy):
            default_value = getattr(strategy, 'default_value', None)
            if default_value == value:
                return "Default"
            return "Default (modified)"
        
        if isinstance(strategy, ComputedMappingStrategy):
            # Check if the value came from LLM completions
            if hasattr(metadata, 'llm_completions') and metadata.llm_completions:
                for prompt_key, completion_data in metadata.llm_completions.items():
                    if isinstance(completion_data, dict):
                        for key, completion_value in completion_data.items():
                            if key != "_completion_metadata" and completion_value == value:
                                return f"LLM ({prompt_key})"
            
            return "Computed"
        
        return "Unknown"
    
    def _calculate_statistics(self, report_data: List[FieldCompletionData]) -> ReportStatistics:
        """
        Calculate statistics from report data.
        
        Args:
            report_data: List of FieldCompletionData objects
            
        Returns:
            ReportStatistics object
        """
        total_fields = len(report_data)
        empty_fields = sum(1 for data in report_data if data.is_empty)
        populated_fields = total_fields - empty_fields
        
        # Calculate completion percentage
        completion_percentage = (populated_fields / total_fields * 100) if total_fields > 0 else 0
        
        # Count strategy types
        strategy_counts = {}
        for data in report_data:
            if not data.is_empty and data.strategy_type != "None":
                strategy_counts[data.strategy_type] = strategy_counts.get(data.strategy_type, 0) + 1
        
        # Count sources
        source_counts = {}
        for data in report_data:
            if not data.is_empty and data.source not in ["Empty", "None"]:
                source_counts[data.source] = source_counts.get(data.source, 0) + 1
        
        return ReportStatistics(
            total_fields=total_fields,
            populated_fields=populated_fields,
            empty_fields=empty_fields,
            completion_percentage=completion_percentage,
            strategy_counts=strategy_counts,
            source_counts=source_counts
        )
    
    def _generate_csv_report(self, report_data: List[FieldCompletionData], output_path: str) -> None:
        """
        Generate a CSV report.
        
        Args:
            report_data: List of FieldCompletionData objects
            output_path: Path to save the CSV file
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(["Field Name", "Strategy Type", "Value", "Source", "Empty"])
                
                # Write data
                for data in report_data:
                    writer.writerow([
                        data.field_name,
                        data.strategy_type,
                        data.value[:100] + "..." if len(data.value) > 100 else data.value,
                        data.source,
                        "Yes" if data.is_empty else "No"
                    ])
            
            logger.info(f"Generated CSV report at {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
    
    def _generate_html_report(self, report_data: List[FieldCompletionData], 
                            metadata: CodexMetadata, stats: ReportStatistics, 
                            output_path: str) -> None:
        """
        Generate an HTML report.
        
        Args:
            report_data: List of FieldCompletionData objects
            metadata: CodexMetadata object
            stats: ReportStatistics object
            output_path: Path to save the HTML file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write HTML header
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>LSI Field Completion Report - {metadata.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .empty {{ color: red; }}
        .stats {{ display: flex; flex-wrap: wrap; }}
        .stat-box {{ background-color: #f2f2f2; border-radius: 5px; padding: 10px; margin: 10px; flex: 1; }}
        .chart {{ width: 100%; height: 20px; background-color: #eee; margin-top: 5px; }}
        .chart-fill {{ height: 100%; background-color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>LSI Field Completion Report</h1>
    <h2>Book Information</h2>
    <p><strong>Title:</strong> {metadata.title}</p>
    <p><strong>Author:</strong> {metadata.author}</p>
    <p><strong>ISBN:</strong> {metadata.isbn13}</p>
    <p><strong>Publisher:</strong> {metadata.publisher}</p>
    
    <h2>Completion Statistics</h2>
    <div class="stats">
        <div class="stat-box">
            <h3>Field Completion</h3>
            <p><strong>Total Fields:</strong> {stats.total_fields}</p>
            <p><strong>Populated Fields:</strong> {stats.populated_fields}</p>
            <p><strong>Empty Fields:</strong> {stats.empty_fields}</p>
            <p><strong>Completion Rate:</strong> {stats.completion_percentage:.1f}%</p>
            <div class="chart">
                <div class="chart-fill" style="width: {stats.completion_percentage}%;"></div>
            </div>
        </div>
        
        <div class="stat-box">
            <h3>Strategy Types</h3>
""")
                
                # Write strategy counts
                for strategy_type, count in stats.strategy_counts.items():
                    percentage = count / stats.populated_fields * 100 if stats.populated_fields > 0 else 0
                    f.write(f"            <p><strong>{strategy_type}:</strong> {count} ({percentage:.1f}%)</p>\n")
                
                f.write("""
        </div>
        
        <div class="stat-box">
            <h3>Data Sources</h3>
""")
                
                # Write source counts
                for source, count in stats.source_counts.items():
                    percentage = count / stats.populated_fields * 100 if stats.populated_fields > 0 else 0
                    f.write(f"            <p><strong>{source}:</strong> {count} ({percentage:.1f}%)</p>\n")
                
                f.write("""
        </div>
    </div>
    
    <h2>Field Details</h2>
    <table>
        <tr>
            <th>Field Name</th>
            <th>Strategy Type</th>
            <th>Value</th>
            <th>Source</th>
            <th>Status</th>
        </tr>
""")
                
                # Write field data
                for data in report_data:
                    status_class = "empty" if data.is_empty else ""
                    status_text = "Empty" if data.is_empty else "Populated"
                    
                    # Truncate long values
                    display_value = data.value
                    if len(display_value) > 100:
                        display_value = display_value[:100] + "..."
                    
                    # Escape HTML characters
                    display_value = display_value.replace("<", "&lt;").replace(">", "&gt;")
                    
                    f.write(f"""
        <tr>
            <td>{data.field_name}</td>
            <td>{data.strategy_type}</td>
            <td>{display_value}</td>
            <td>{data.source}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>""")
                
                # Write HTML footer
                f.write("""
    </table>
    
    <p><em>Report generated on {}</em></p>
</body>
</html>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            logger.info(f"Generated HTML report at {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
    
    def _generate_json_report(self, report_data: List[FieldCompletionData], 
                            metadata: CodexMetadata, stats: ReportStatistics, 
                            output_path: str) -> None:
        """
        Generate a JSON report.
        
        Args:
            report_data: List of FieldCompletionData objects
            metadata: CodexMetadata object
            stats: ReportStatistics object
            output_path: Path to save the JSON file
        """
        try:
            # Convert report data to dictionaries
            field_data = [asdict(data) for data in report_data]
            
            # Create report structure
            report = {
                "metadata": {
                    "title": metadata.title,
                    "author": metadata.author,
                    "isbn13": metadata.isbn13,
                    "publisher": metadata.publisher,
                    "report_date": datetime.now().isoformat()
                },
                "statistics": {
                    "total_fields": stats.total_fields,
                    "populated_fields": stats.populated_fields,
                    "empty_fields": stats.empty_fields,
                    "completion_percentage": stats.completion_percentage,
                    "strategy_counts": stats.strategy_counts,
                    "source_counts": stats.source_counts
                },
                "field_data": field_data
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Generated JSON report at {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
    
    def generate_markdown_report(self, metadata: CodexMetadata, lsi_headers: List[str], 
                               output_path: str) -> str:
        """
        Generate a Markdown report.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            output_path: Path to save the Markdown file
            
        Returns:
            Path to the generated report
        """
        try:
            # Generate report data
            report_data = self._generate_report_data(metadata, lsi_headers)
            
            # Calculate statistics
            stats = self._calculate_statistics(report_data)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# LSI Field Completion Report\n\n")
                f.write(f"## Book Information\n\n")
                f.write(f"- **Title:** {metadata.title}\n")
                f.write(f"- **Author:** {metadata.author}\n")
                f.write(f"- **ISBN:** {metadata.isbn13}\n")
                f.write(f"- **Publisher:** {metadata.publisher}\n\n")
                
                # Write statistics
                f.write(f"## Completion Statistics\n\n")
                f.write(f"- **Total Fields:** {stats.total_fields}\n")
                f.write(f"- **Populated Fields:** {stats.populated_fields}\n")
                f.write(f"- **Empty Fields:** {stats.empty_fields}\n")
                f.write(f"- **Completion Rate:** {stats.completion_percentage:.1f}%\n\n")
                
                # Write strategy counts
                f.write(f"### Strategy Types\n\n")
                for strategy_type, count in stats.strategy_counts.items():
                    percentage = count / stats.populated_fields * 100 if stats.populated_fields > 0 else 0
                    f.write(f"- **{strategy_type}:** {count} ({percentage:.1f}%)\n")
                f.write("\n")
                
                # Write source counts
                f.write(f"### Data Sources\n\n")
                for source, count in stats.source_counts.items():
                    percentage = count / stats.populated_fields * 100 if stats.populated_fields > 0 else 0
                    f.write(f"- **{source}:** {count} ({percentage:.1f}%)\n")
                f.write("\n")
                
                # Write empty fields
                f.write(f"## Empty Fields\n\n")
                empty_fields = [data.field_name for data in report_data if data.is_empty]
                if empty_fields:
                    for field in empty_fields:
                        f.write(f"- {field}\n")
                else:
                    f.write("No empty fields.\n")
                f.write("\n")
                
                # Write field details
                f.write(f"## Field Details\n\n")
                f.write("| Field Name | Strategy Type | Source | Status |\n")
                f.write("|------------|--------------|--------|--------|\n")
                
                for data in report_data:
                    status = "Empty" if data.is_empty else "Populated"
                    f.write(f"| {data.field_name} | {data.strategy_type} | {data.source} | {status} |\n")
                
                # Write footer
                f.write(f"\n\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
            
            logger.info(f"Generated Markdown report at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Markdown report: {e}")
            return ""