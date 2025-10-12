#!/usr/bin/env python3
"""
Test script for running the pipeline against rows 1-12 of xynapse_traces_schedule.json.

This script tests the complete pipeline to ensure it creates valid fully populated LSI CSV files
for the first 12 books in the xynapse_traces_schedule.json file, which is the top immediate priority
mentioned in the requirements.
"""

import os
import sys
import json
import logging
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline_test():
    """Run the pipeline against rows 1-12 of xynapse_traces_schedule.json."""
    logger.info("Starting pipeline test for xynapse_traces_schedule.json rows 1-12")
    
    # Define the command to run the pipeline
    cmd = [
        "python", "run_book_pipeline.py",
        "--imprint", "xynapse_traces",
        "--schedule-file", "imprints/xynapse_traces/xynapse_traces_schedule.json",
        "--model", "gemini/gemini-2.5-flash",
        "--max-books", "12",
        "--begin-with-book", "1",
        "--end-with-book", "12",
        "--enable-llm-completion",
        "--lsi-config", "configs/default_lsi_config.json",
        "--lsi-template", "templates/LSI_ACS_header.csv",
        "--start-stage", "1",
        "--end-stage", "4",
        "--no-litellm-log",
        "--terse-log"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the pipeline
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        # Log the output
        if result.stdout:
            logger.info("Pipeline stdout:")
            logger.info(result.stdout)
        
        if result.stderr:
            logger.error("Pipeline stderr:")
            logger.error(result.stderr)
        
        # Check the return code
        if result.returncode == 0:
            logger.info("Pipeline completed successfully!")
        else:
            logger.error(f"Pipeline failed with return code: {result.returncode}")
            return False
        
        # Check if the LSI CSV file was generated
        lsi_csv_path = Path("output/xynapse_traces_build/lsi_csv/xynapse_traces_batch_LSI.csv")
        if lsi_csv_path.exists():
            logger.info(f"LSI CSV file generated: {lsi_csv_path}")
            
            # Check the CSV file content
            with open(lsi_csv_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                logger.info(f"LSI CSV file has {len(lines)} lines (including header)")
                
                if len(lines) > 1:
                    # Check the header
                    header = lines[0].strip()
                    logger.info(f"CSV header: {header[:100]}...")
                    
                    # Count the number of data rows
                    data_rows = len(lines) - 1
                    logger.info(f"Number of data rows: {data_rows}")
                    
                    if data_rows >= 12:
                        logger.info("✅ LSI CSV file contains at least 12 data rows as expected")
                    else:
                        logger.warning(f"⚠️ LSI CSV file contains only {data_rows} data rows, expected at least 12")
                    
                    # Check field population for the first few rows
                    import csv
                    with open(lsi_csv_path, 'r', encoding='utf-8-sig') as csvfile:
                        reader = csv.DictReader(csvfile)
                        headers = reader.fieldnames
                        total_fields = len(headers)
                        logger.info(f"Total fields in CSV: {total_fields}")
                        
                        for i, row in enumerate(reader):
                            if i >= 3:  # Check first 3 rows
                                break
                            
                            populated_fields = sum(1 for value in row.values() if value and value.strip())
                            population_rate = (populated_fields / total_fields) * 100
                            
                            logger.info(f"Row {i+1}: {populated_fields}/{total_fields} fields populated ({population_rate:.1f}%)")
                            
                            # Check for specific critical fields
                            critical_fields = ["ISBN or SKU", "Title", "Publisher", "Contributor One"]
                            for field in critical_fields:
                                if field in row and row[field] and row[field].strip():
                                    logger.info(f"  ✅ {field}: {row[field][:50]}...")
                                else:
                                    logger.warning(f"  ⚠️ {field}: Empty or missing")
                else:
                    logger.error("LSI CSV file has no data rows")
                    return False
        else:
            logger.error(f"LSI CSV file not found at: {lsi_csv_path}")
            return False
        
        # Check if field reports were generated
        field_report_html = Path("output/xynapse_traces_build/lsi_csv").glob("field_report__*.html")
        field_report_files = list(field_report_html)
        if field_report_files:
            logger.info(f"Field report generated: {field_report_files[0]}")
        else:
            logger.warning("No field report HTML files found")
        
        # Check if LLM completions were saved
        metadata_dir = Path("output/xynapse_traces_build/metadata")
        if metadata_dir.exists():
            llm_completion_files = list(metadata_dir.glob("llm_completions_*.json"))
            if llm_completion_files:
                logger.info(f"Found {len(llm_completion_files)} LLM completion files")
                
                # Check one of the LLM completion files
                with open(llm_completion_files[0], 'r', encoding='utf-8') as f:
                    completion_data = json.load(f)
                    if "llm_completions" in completion_data:
                        num_completions = len(completion_data["llm_completions"])
                        logger.info(f"Sample LLM completion file has {num_completions} completions")
                        
                        if num_completions >= 10:
                            logger.info("✅ LLM completions appear to be working correctly")
                        else:
                            logger.warning(f"⚠️ Only {num_completions} LLM completions found, expected more")
                    else:
                        logger.warning("LLM completion file has no completions")
            else:
                logger.warning("No LLM completion files found")
        else:
            logger.warning("Metadata directory not found")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Pipeline timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        return False

def analyze_results():
    """Analyze the results of the pipeline test."""
    logger.info("Analyzing pipeline test results")
    
    # Check output directory structure
    output_dir = Path("output/xynapse_traces_build")
    if output_dir.exists():
        logger.info(f"Output directory exists: {output_dir}")
        
        # List subdirectories
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        logger.info(f"Subdirectories: {[d.name for d in subdirs]}")
        
        # Check LSI CSV directory
        lsi_dir = output_dir / "lsi_csv"
        if lsi_dir.exists():
            lsi_files = list(lsi_dir.glob("*"))
            logger.info(f"LSI CSV directory files: {[f.name for f in lsi_files]}")
        
        # Check processed JSON directory
        json_dir = output_dir / "processed_json"
        if json_dir.exists():
            json_files = list(json_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} processed JSON files")
        
        # Check covers directory
        covers_dir = output_dir / "covers"
        if covers_dir.exists():
            cover_files = list(covers_dir.glob("*"))
            logger.info(f"Found {len(cover_files)} cover files")
        
        # Check interiors directory
        interiors_dir = output_dir / "interiors"
        if interiors_dir.exists():
            interior_files = list(interiors_dir.glob("*"))
            logger.info(f"Found {len(interior_files)} interior files")
    else:
        logger.error(f"Output directory does not exist: {output_dir}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the pipeline against rows 1-12 of xynapse_traces_schedule.json")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze existing results without running the pipeline")
    args = parser.parse_args()
    
    if args.analyze_only:
        analyze_results()
    else:
        success = run_pipeline_test()
        if success:
            logger.info("✅ Pipeline test completed successfully!")
            analyze_results()
        else:
            logger.error("❌ Pipeline test failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()