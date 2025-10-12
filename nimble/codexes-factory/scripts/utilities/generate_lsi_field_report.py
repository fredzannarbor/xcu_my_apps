#!/usr/bin/env python3
"""
LSI Field Completion Report Generator

This script analyzes LSI CSV files and generates a report showing which fields are being completed
by which strategy and their actual values.
"""

import os
import sys
import json
import csv
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath('src'))

# Import required modules
try:
    from src.codexes.modules.metadata.metadata_models import CodexMetadata
    from src.codexes.modules.distribution.field_mapping import FieldMappingRegistry
    from src.codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
    from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration
    from src.codexes.core.logging_config import setup_application_logging, get_logging_manager
except ImportError as e:
    # Initialize basic logging for error reporting
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Import error: {e}")
    logger.error("This script requires the codexes modules to be installed.")
    sys.exit(1)

# Set up logging using LoggingConfigManager
setup_application_logging()
logger = logging.getLogger(__name__)

def analyze_csv_file(csv_path: str) -> Dict[str, Any]:
    """
    Analyze an LSI CSV file to extract field values.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary with field names and values
    """
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = next(reader)
            
            # Create dictionary of field names and values
            field_values = {}
            for i, header in enumerate(headers):
                if i < len(data):
                    field_values[header] = data[i]
                else:
                    field_values[header] = ""
            
            return field_values
    except Exception as e:
        logger.error(f"Failed to analyze CSV file {csv_path}: {e}")
        return {}

def get_field_strategies(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Get the mapping strategy for each LSI field.
    
    Args:
        config_path: Path to the LSI configuration file
        
    Returns:
        Dictionary with field names and strategy types
    """
    try:
        # Initialize configuration
        config = LSIConfiguration(config_path)
        
        # Create field mapping registry
        registry = create_comprehensive_lsi_registry(config)
        
        # Get all registered fields
        field_names = registry.get_registered_fields()
        
        # Get strategy type for each field
        field_strategies = {}
        for field_name in field_names:
            strategy = registry.get_strategy(field_name)
            if strategy:
                strategy_type = type(strategy).__name__
                field_strategies[field_name] = strategy_type
            else:
                field_strategies[field_name] = "None"
        
        return field_strategies
    except Exception as e:
        logger.error(f"Failed to get field strategies: {e}")
        return {}

def get_llm_completions(metadata_path: str) -> Dict[str, Any]:
    """
    Get LLM completions from a metadata file.
    
    Args:
        metadata_path: Path to the metadata JSON file
        
    Returns:
        Dictionary with LLM completions
    """
    try:
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata file not found: {metadata_path}")
            return {}
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the JSON has llm_completions
        if 'llm_completions' in data:
            return data['llm_completions']
        elif 'metadata' in data and 'llm_completions' in data['metadata']:
            return data['metadata']['llm_completions']
        else:
            logger.warning(f"No LLM completions found in {metadata_path}")
            return {}
    except Exception as e:
        logger.error(f"Failed to get LLM completions from {metadata_path}: {e}")
        return {}

def generate_field_report(
    csv_path: str,
    output_path: str,
    config_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    format: str = "csv"
) -> bool:
    """
    Generate a field completion report.
    
    Args:
        csv_path: Path to the LSI CSV file
        output_path: Path to save the report
        config_path: Path to the LSI configuration file
        metadata_path: Path to the metadata JSON file
        format: Output format (csv, html, or markdown)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Get field values from CSV
        field_values = analyze_csv_file(csv_path)
        if not field_values:
            logger.error(f"No field values found in {csv_path}")
            return False
        
        # Get field strategies
        field_strategies = get_field_strategies(config_path)
        
        # Get LLM completions
        llm_completions = {}
        if metadata_path:
            llm_completions = get_llm_completions(metadata_path)
        
        # Create report data
        report_data = []
        for field_name, value in field_values.items():
            strategy = field_strategies.get(field_name, "Unknown")
            
            # Determine source
            source = "Default"
            if value:
                if strategy == "DirectMappingStrategy":
                    source = "Direct"
                elif strategy == "ComputedMappingStrategy":
                    source = "Computed"
                elif strategy == "DefaultMappingStrategy":
                    source = "Default"
                elif strategy == "ConditionalMappingStrategy":
                    source = "Conditional"
                elif strategy == "LLMCompletionStrategy":
                    source = "LLM"
            
            # Check if field is in LLM completions
            llm_value = None
            for completion_key, completion_value in llm_completions.items():
                if isinstance(completion_value, dict):
                    for k, v in completion_value.items():
                        if k.lower() == field_name.lower() or field_name.lower() in k.lower():
                            llm_value = v
                            source = f"LLM ({completion_key})"
                            break
                elif field_name.lower() in completion_key.lower():
                    llm_value = completion_value
                    source = f"LLM ({completion_key})"
                    break
            
            # Add to report data
            report_data.append({
                "Field Name": field_name,
                "Strategy": strategy,
                "Value": value[:100] + "..." if value and len(value) > 100 else value,
                "Source": source,
                "Empty": "Yes" if not value else "No",
                "LLM Value": llm_value[:100] + "..." if llm_value and len(str(llm_value)) > 100 else llm_value
            })
        
        # Sort report data by empty status and field name
        report_data.sort(key=lambda x: (x["Empty"] == "No", x["Field Name"]))
        
        # Generate report
        if format.lower() == "html":
            _generate_csv_report(report_data, output_path)  # Fallback to CSV for now
        elif format.lower() == "markdown":
            _generate_markdown_report(report_data, output_path)
        else:
            _generate_csv_report(report_data, output_path)
        
        logger.info(f"Field completion report generated: {output_path}")
        
        # Print summary
        total_fields = len(report_data)
        empty_fields = sum(1 for item in report_data if item["Empty"] == "Yes")
        populated_fields = total_fields - empty_fields
        
        logger.info(f"Total fields: {total_fields}")
        logger.info(f"Populated fields: {populated_fields} ({populated_fields / total_fields * 100:.2f}%)")
        logger.info(f"Empty fields: {empty_fields} ({empty_fields / total_fields * 100:.2f}%)")
        
        # Print strategy breakdown
        strategy_counts = {}
        for item in report_data:
            if item["Empty"] == "No":  # Only count populated fields
                strategy = item["Strategy"]
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        logger.info("Strategy breakdown for populated fields:")
        for strategy, count in strategy_counts.items():
            logger.info(f"  {strategy}: {count} ({count / populated_fields * 100:.2f}%)")
        
        return True
    except Exception as e:
        logger.error(f"Failed to generate field report: {e}", exc_info=True)
        return False

def _generate_csv_report(report_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a CSV report.
    
    Args:
        report_data: List of dictionaries with report data
        output_path: Path to save the CSV file
    """
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        if not report_data:
            logger.warning("No report data to write")
            return
        
        writer = csv.DictWriter(f, fieldnames=report_data[0].keys())
        writer.writeheader()
        writer.writerows(report_data)

def _generate_markdown_report(report_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a Markdown report.
    
    Args:
        report_data: List of dictionaries with report data
        output_path: Path to save the Markdown file
    """
    # Calculate summary statistics
    total_fields = len(report_data)
    empty_fields = sum(1 for item in report_data if item["Empty"] == "Yes")
    populated_fields = total_fields - empty_fields
    populated_percentage = populated_fields / total_fields * 100 if total_fields > 0 else 0
    empty_percentage = empty_fields / total_fields * 100 if total_fields > 0 else 0
    
    # Calculate strategy breakdown
    strategy_counts = {}
    for item in report_data:
        if item["Empty"] == "No":  # Only count populated fields
            strategy = item["Strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    # Create markdown content
    markdown = f"""# LSI Field Completion Report

## Summary

- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Total fields: {total_fields}
- Populated fields: {populated_fields} ({populated_percentage:.2f}%)
- Empty fields: {empty_fields} ({empty_percentage:.2f}%)

## Strategy Breakdown

| Strategy | Count | Percentage |
|----------|-------|------------|
"""
    
    # Add strategy rows
    for strategy, count in strategy_counts.items():
        percentage = count / populated_fields * 100 if populated_fields > 0 else 0
        markdown += f"| {strategy} | {count} | {percentage:.2f}% |\n"
    
    # Add field details
    markdown += """
## Field Details

| Field Name | Strategy | Value | Source | Empty |
|------------|----------|-------|--------|-------|
"""
    
    # Add field rows (simplified to avoid formatting issues)
    for item in report_data:
        value = item["Value"] if item["Value"] else ""
        
        # Escape pipe characters in values and truncate long values
        value = str(value).replace("|", "\\|")
        if len(value) > 50:
            value = value[:50] + "..."
        
        markdown += f"| {item['Field Name']} | {item['Strategy']} | {value} | {item['Source']} | {item['Empty']} |\n"
    
    # Write markdown file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

def find_metadata_file(csv_path: str) -> Optional[str]:
    """
    Find the corresponding metadata file for a CSV file.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Path to the metadata file or None if not found
    """
    try:
        # Get the base name without extension
        base_name = os.path.splitext(os.path.basename(csv_path))[0]
        
        # Look for metadata file in various locations
        possible_paths = [
            # Same directory
            os.path.join(os.path.dirname(csv_path), f"{base_name}.json"),
            # metadata/ directory parallel to csv directory
            os.path.join(os.path.dirname(os.path.dirname(csv_path)), "metadata", f"{base_name}.json"),
            # processed_json/ directory
            os.path.join(os.path.dirname(os.path.dirname(csv_path)), "processed_json", f"{base_name}.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found metadata file: {path}")
                return path
        
        logger.warning(f"No metadata file found for {csv_path}")
        return None
    except Exception as e:
        logger.error(f"Error finding metadata file: {e}")
        return None

def main():
    """Main function to parse arguments and generate field report."""
    parser = argparse.ArgumentParser(description="Generate LSI field completion report")
    
    # Input options
    parser.add_argument("--csv", required=True, help="Path to LSI CSV file")
    parser.add_argument("--metadata", help="Path to metadata JSON file")
    
    # Output options
    parser.add_argument("--output", required=True, help="Path to save the report")
    
    # Configuration options
    parser.add_argument("--config", help="Path to LSI configuration file")
    parser.add_argument("--format", choices=["csv", "html", "markdown"], default="csv", help="Output format")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Find metadata file if not specified
    metadata_path = args.metadata
    if not metadata_path:
        metadata_path = find_metadata_file(args.csv)
    
    # Generate field report
    success = generate_field_report(
        csv_path=args.csv,
        output_path=args.output,
        config_path=args.config,
        metadata_path=metadata_path,
        format=args.format
    )
    
    if success:
        print(f"Field completion report generated: {args.output}")
    else:
        print("Failed to generate field completion report")
        sys.exit(1)

if __name__ == "__main__":
    main()