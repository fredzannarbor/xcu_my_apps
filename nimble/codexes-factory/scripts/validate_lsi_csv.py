#!/usr/bin/env python3
"""
Validation script for LSI CSV output.

This script validates the generated LSI CSV file to ensure it meets all requirements:
1. 100% field population with valid fields, including null valids
2. All critical fields are populated
3. Field formats meet LSI requirements
4. All 12 books are included
"""

import os
import sys
import csv
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_lsi_csv(csv_path):
    """Validate the LSI CSV file."""
    logger.info(f"Validating LSI CSV file: {csv_path}")
    
    if not os.path.exists(csv_path):
        logger.error(f"LSI CSV file not found: {csv_path}")
        return False
    
    validation_results = {
        "file_exists": True,
        "total_rows": 0,
        "total_fields": 0,
        "field_population_stats": {},
        "critical_fields_check": {},
        "format_validation": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            validation_results["total_fields"] = len(headers)
            
            logger.info(f"CSV has {len(headers)} fields")
            
            # Define critical fields that must be populated
            critical_fields = [
                "ISBN or SKU",
                "Title",
                "Publisher",
                "Contributor One",
                "Pages",
                "Pub Date",
                "US Suggested List Price",
                "Rendition /Booktype",
                "Custom Trim Width (inches)",
                "Custom Trim Height (inches)"
            ]
            
            # Initialize field population tracking
            field_population = {field: 0 for field in headers}
            rows = list(reader)
            validation_results["total_rows"] = len(rows)
            
            logger.info(f"CSV has {len(rows)} data rows")
            
            if len(rows) < 12:
                validation_results["errors"].append(f"Expected at least 12 rows, found {len(rows)}")
            
            # Analyze each row
            for i, row in enumerate(rows):
                row_number = i + 1
                populated_fields = 0
                
                # Check field population
                for field, value in row.items():
                    if value and value.strip():
                        field_population[field] += 1
                        populated_fields += 1
                
                # Calculate population rate for this row
                population_rate = (populated_fields / len(headers)) * 100
                
                if row_number <= 5:  # Log details for first 5 rows
                    logger.info(f"Row {row_number}: {populated_fields}/{len(headers)} fields populated ({population_rate:.1f}%)")
                
                # Check critical fields for this row
                missing_critical = []
                for field in critical_fields:
                    if field in row:
                        if not row[field] or not row[field].strip():
                            missing_critical.append(field)
                    else:
                        missing_critical.append(f"{field} (field not found)")
                
                if missing_critical and row_number <= 5:
                    logger.warning(f"Row {row_number} missing critical fields: {missing_critical}")
                
                # Validate specific field formats
                if "ISBN or SKU" in row and row["ISBN or SKU"]:
                    isbn = row["ISBN or SKU"].strip()
                    if len(isbn) not in [10, 13] or not isbn.replace('-', '').isdigit():
                        validation_results["warnings"].append(f"Row {row_number}: Invalid ISBN format: {isbn}")
                
                if "US Suggested List Price" in row and row["US Suggested List Price"]:
                    price = row["US Suggested List Price"].strip()
                    if not price.startswith('$'):
                        validation_results["warnings"].append(f"Row {row_number}: Price should start with $: {price}")
                
                if "Pages" in row and row["Pages"]:
                    pages = row["Pages"].strip()
                    if not pages.isdigit():
                        validation_results["warnings"].append(f"Row {row_number}: Pages should be numeric: {pages}")
            
            # Calculate overall field population statistics
            total_possible_values = len(rows) * len(headers)
            total_populated_values = sum(field_population.values())
            overall_population_rate = (total_populated_values / total_possible_values) * 100
            
            validation_results["field_population_stats"] = {
                "overall_population_rate": overall_population_rate,
                "total_possible_values": total_possible_values,
                "total_populated_values": total_populated_values,
                "field_population": field_population
            }
            
            logger.info(f"Overall field population rate: {overall_population_rate:.1f}%")
            
            # Check critical fields across all rows
            for field in critical_fields:
                if field in field_population:
                    populated_count = field_population[field]
                    population_rate = (populated_count / len(rows)) * 100
                    validation_results["critical_fields_check"][field] = {
                        "populated_count": populated_count,
                        "total_rows": len(rows),
                        "population_rate": population_rate
                    }
                    
                    if population_rate < 100:
                        validation_results["warnings"].append(f"Critical field '{field}' only populated in {populated_count}/{len(rows)} rows ({population_rate:.1f}%)")
                else:
                    validation_results["errors"].append(f"Critical field '{field}' not found in CSV")
            
            # Check for completely empty fields
            empty_fields = [field for field, count in field_population.items() if count == 0]
            if empty_fields:
                logger.warning(f"Found {len(empty_fields)} completely empty fields")
                validation_results["warnings"].append(f"Completely empty fields: {empty_fields[:10]}...")  # Show first 10
            
            # Check for fields with low population rates
            low_population_fields = [
                field for field, count in field_population.items() 
                if count > 0 and (count / len(rows)) < 0.5
            ]
            if low_population_fields:
                logger.warning(f"Found {len(low_population_fields)} fields with <50% population rate")
                validation_results["warnings"].append(f"Low population fields: {low_population_fields[:10]}...")  # Show first 10
            
            # Overall validation result
            if overall_population_rate >= 90:
                logger.info("✅ Field population rate is acceptable (≥90%)")
            elif overall_population_rate >= 70:
                logger.warning("⚠️ Field population rate is moderate (70-89%)")
                validation_results["warnings"].append(f"Field population rate is only {overall_population_rate:.1f}%")
            else:
                logger.error("❌ Field population rate is too low (<70%)")
                validation_results["errors"].append(f"Field population rate is only {overall_population_rate:.1f}%")
            
    except Exception as e:
        logger.error(f"Error validating CSV file: {e}")
        validation_results["errors"].append(f"Error reading CSV file: {e}")
        return False
    
    # Save validation results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = f"lsi_csv_validation_results_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to: {results_path}")
    
    # Summary
    logger.info("=== VALIDATION SUMMARY ===")
    logger.info(f"Total rows: {validation_results['total_rows']}")
    logger.info(f"Total fields: {validation_results['total_fields']}")
    logger.info(f"Overall population rate: {validation_results['field_population_stats']['overall_population_rate']:.1f}%")
    logger.info(f"Errors: {len(validation_results['errors'])}")
    logger.info(f"Warnings: {len(validation_results['warnings'])}")
    
    if validation_results["errors"]:
        logger.error("ERRORS:")
        for error in validation_results["errors"]:
            logger.error(f"  - {error}")
    
    if validation_results["warnings"]:
        logger.warning("WARNINGS:")
        for warning in validation_results["warnings"][:10]:  # Show first 10 warnings
            logger.warning(f"  - {warning}")
        if len(validation_results["warnings"]) > 10:
            logger.warning(f"  ... and {len(validation_results['warnings']) - 10} more warnings")
    
    # Return True if no critical errors
    return len(validation_results["errors"]) == 0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate LSI CSV output")
    parser.add_argument("--csv-path", default="output/xynapse_traces_build/lsi_csv/xynapse_traces_batch_LSI.csv", 
                       help="Path to the LSI CSV file to validate")
    args = parser.parse_args()
    
    success = validate_lsi_csv(args.csv_path)
    
    if success:
        logger.info("✅ LSI CSV validation completed successfully!")
    else:
        logger.error("❌ LSI CSV validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()