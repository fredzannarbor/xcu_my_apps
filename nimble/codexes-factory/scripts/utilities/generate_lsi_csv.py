#!/usr/bin/env python3
"""
LSI CSV Generation Script

This script generates complete LSI format CSVs with all fields properly filled in.
It can be used from the command line or imported as a module.

Usage:
    python generate_lsi_csv.py --input metadata.json --output output.csv --config config.json --template template.csv --enable-llm

    or

    python generate_lsi_csv.py --batch metadata_dir --output output_dir --config config.json --template template.csv --enable-llm
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Add the src directory to the Python path
sys.path.append(os.path.abspath('src'))

# Import required modules
try:
    from src.codexes.modules.metadata.metadata_models import CodexMetadata
    from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
    from src.codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
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

def load_metadata_from_json(json_path: str) -> CodexMetadata:
    """
    Load metadata from a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        CodexMetadata object
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the JSON has a 'metadata' key
        if 'metadata' in data:
            metadata_dict = data['metadata']
        else:
            metadata_dict = data
        
        # Create CodexMetadata object
        metadata = CodexMetadata()
        
        # Update metadata fields from dictionary
        for key, value in metadata_dict.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        
        return metadata
    except Exception as e:
        logger.error(f"Failed to load metadata from {json_path}: {e}")
        raise

def load_book_content(content_path: Optional[str]) -> Optional[str]:
    """
    Load book content from a file.
    
    Args:
        content_path: Path to the book content file
        
    Returns:
        Book content as string or None if path is None
    """
    if not content_path:
        return None
    
    try:
        with open(content_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load book content from {content_path}: {e}")
        return None

def analyze_csv_completeness(csv_path: str) -> Dict[str, Any]:
    """
    Analyze the completeness of the generated CSV file.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary with analysis results
    """
    import csv
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = next(reader)
            
            total_fields = len(headers)
            populated_fields = sum(1 for value in data if value.strip())
            empty_fields = total_fields - populated_fields
            
            # Analyze which fields are populated and which are empty
            populated_field_names = [headers[i] for i in range(len(headers)) if i < len(data) and data[i].strip()]
            empty_field_names = [headers[i] for i in range(len(headers)) if i < len(data) and not data[i].strip()]
            
            return {
                "total_fields": total_fields,
                "populated_fields": populated_fields,
                "empty_fields": empty_fields,
                "populated_field_names": populated_field_names,
                "empty_field_names": empty_field_names,
                "completeness_percentage": (populated_fields / total_fields) * 100 if total_fields > 0 else 0
            }
    except Exception as e:
        logger.error(f"Failed to analyze CSV completeness: {e}")
        return {
            "total_fields": 0,
            "populated_fields": 0,
            "empty_fields": 0,
            "populated_field_names": [],
            "empty_field_names": [],
            "completeness_percentage": 0
        }

def generate_lsi_csv(
    metadata: Union[CodexMetadata, str],
    output_path: str,
    template_path: str = "templates/LSI_ACS_header.csv",
    config_path: Optional[str] = None,
    tranche_name: Optional[str] = None,
    book_content: Optional[str] = None,
    enable_llm: bool = False,
    model_name: str = "gemini/gemini-2.5-flash",
    log_directory: str = "logs/lsi_generation"
) -> Dict[str, Any]:
    """
    Generate LSI CSV from metadata.
    
    Args:
        metadata: CodexMetadata object or path to JSON file
        output_path: Path to save the CSV file
        template_path: Path to the LSI template CSV file
        config_path: Path to the LSI configuration file
        book_content: Book content as string or path to file
        enable_llm: Whether to enable LLM field completion
        model_name: LLM model name to use for field completion
        log_directory: Directory for detailed logging
        
    Returns:
        Dictionary with generation results
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        os.makedirs(log_directory, exist_ok=True)
        
        # Load metadata if it's a string (path to JSON file)
        if isinstance(metadata, str):
            metadata = load_metadata_from_json(metadata)
        
        # Load book content if it's a string (path to file)
        if isinstance(book_content, str) and os.path.isfile(book_content):
            book_content = load_book_content(book_content)
        
        # Complete missing fields with LLM if enabled
        if enable_llm:
            logger.info("Completing missing fields with LLM...")
            try:
                field_completer = LLMFieldCompleter(model_name=model_name)
                metadata = field_completer.complete_missing_fields(metadata, book_content)
                logger.info("LLM field completion successful")
            except Exception as e:
                logger.warning(f"LLM field completion failed: {e}. Proceeding with original metadata.")
        
        # Initialize LSI ACS Generator
        logger.info("Initializing LSI ACS Generator...")
        
        # If tranche name is provided, use tranche configuration
        if tranche_name:
            try:
                from src.codexes.modules.distribution.tranche_config_loader import TrancheConfigLoader
                logger.info(f"Using tranche configuration: {tranche_name}")
                tranche_loader = TrancheConfigLoader()
                tranche_context = tranche_loader.get_tranche_context(tranche_name)
                
                # Get field exclusions from tranche config
                field_exclusions = tranche_loader.get_tranche_field_exclusions(tranche_name)
                if field_exclusions:
                    logger.info(f"Tranche field exclusions: {field_exclusions}")
                
                # Get annotation boilerplate from tranche config
                annotation_boilerplate = tranche_loader.get_tranche_annotation_boilerplate(tranche_name)
                if annotation_boilerplate:
                    logger.info(f"Using annotation boilerplate from tranche config")
                    
                    # Apply annotation boilerplate using the AnnotationProcessor
                    from src.codexes.modules.distribution.annotation_processor import AnnotationProcessor
                    AnnotationProcessor.process_annotation(metadata, annotation_boilerplate)
                    logger.info("Applied annotation boilerplate to annotation fields")
            except Exception as e:
                logger.warning(f"Failed to load tranche configuration: {e}. Proceeding without tranche config.")
        
        lsi_generator = LsiAcsGenerator(
            template_path=template_path,
            config_path=config_path,
            log_directory=log_directory,
            tranche_name=tranche_name
        )
        
        # Generate LSI CSV
        logger.info(f"Generating LSI CSV to {output_path}...")
        result = lsi_generator.generate_with_validation(metadata, output_path)
        
        # Analyze CSV completeness
        analysis = None
        if result.success and os.path.exists(output_path):
            analysis = analyze_csv_completeness(output_path)
            logger.info(f"CSV generation successful. Completeness: {analysis['completeness_percentage']:.2f}%")
            
            # Log empty fields
            if analysis['empty_fields'] > 0:
                logger.info(f"Empty fields: {analysis['empty_fields']} out of {analysis['total_fields']}")
                for field in analysis['empty_field_names'][:10]:  # Show first 10 empty fields
                    logger.debug(f"Empty field: {field}")
                if len(analysis['empty_field_names']) > 10:
                    logger.debug(f"... and {len(analysis['empty_field_names']) - 10} more empty fields")
        
        return {
            "success": result.success,
            "output_path": output_path,
            "analysis": analysis,
            "validation_result": result.validation_result if hasattr(result, 'validation_result') else None
        }
    except Exception as e:
        logger.error(f"Failed to generate LSI CSV: {e}", exc_info=True)
        return {
            "success": False,
            "output_path": output_path,
            "error": str(e)
        }

def process_batch(
    input_dir: str,
    output_dir: str,
    template_path: str = "templates/LSI_ACS_header.csv",
    config_path: Optional[str] = None,
    tranche_name: Optional[str] = None,
    enable_llm: bool = False,
    model_name: str = "gemini/gemini-2.5-flash",
    log_directory: str = "logs/lsi_generation"
) -> Dict[str, Any]:
    """
    Process a batch of metadata files.
    
    Args:
        input_dir: Directory containing metadata JSON files
        output_dir: Directory to save CSV files
        template_path: Path to the LSI template CSV file
        config_path: Path to the LSI configuration file
        enable_llm: Whether to enable LLM field completion
        model_name: LLM model name to use for field completion
        log_directory: Directory for detailed logging
        
    Returns:
        Dictionary with batch processing results
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all JSON files in the input directory
        json_files = list(Path(input_dir).glob("*.json"))
        json_files.sort()
        if not json_files:
            logger.warning(f"No JSON files found in {input_dir}")
            return {
                "success": False,
                "error": f"No JSON files found in {input_dir}"
            }
        
        logger.info(f"Found {len(json_files)} JSON files in {input_dir}")
        
        # Process each JSON file
        results = []
        metadata_list = []
        for json_file in json_files:
            try:
                # Load metadata
                metadata = load_metadata_from_json(str(json_file))
                metadata_list.append(metadata)
                
                # Complete missing fields with LLM if enabled
                if enable_llm:
                    logger.info(f"Completing missing fields for {json_file.name} with LLM...")
                    try:
                        field_completer = LLMFieldCompleter(model_name=model_name)
                        metadata = field_completer.complete_missing_fields(metadata)
                        logger.info(f"LLM field completion successful for {json_file.name}")
                    except Exception as e:
                        logger.warning(f"LLM field completion failed for {json_file.name}: {e}")
                
                # Generate individual CSV file
                output_path = os.path.join(output_dir, f"{json_file.stem}.csv")
                result = generate_lsi_csv(
                    metadata=metadata,
                    output_path=output_path,
                    template_path=template_path,
                    config_path=config_path,
                    tranche_name=tranche_name,
                    enable_llm=False,  # Already completed fields above
                    log_directory=log_directory
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {json_file}: {e}")
                results.append({
                    "success": False,
                    "file": str(json_file),
                    "error": str(e)
                })
        
        # Generate batch CSV file
        if metadata_list:
            logger.info("Generating batch CSV file...")
            batch_output_path = os.path.join(output_dir, f"batch_lsi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            # Initialize LSI ACS Generator
            lsi_generator = LsiAcsGenerator(
                template_path=template_path,
                config_path=config_path,
                log_directory=log_directory
            )
            
            # Generate batch CSV
            batch_result = lsi_generator.generate_batch_csv(metadata_list, batch_output_path)
            
            if batch_result.success:
                logger.info(f"Batch CSV generation successful: {batch_output_path}")
            else:
                logger.error(f"Batch CSV generation failed")
        
        # Return batch processing results
        return {
            "success": all(result.get("success", False) for result in results),
            "total_files": len(json_files),
            "successful_files": sum(1 for result in results if result.get("success", False)),
            "failed_files": sum(1 for result in results if not result.get("success", False)),
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to process batch: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function to parse arguments and generate LSI CSV."""
    parser = argparse.ArgumentParser(description="Generate LSI CSV from metadata")
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", help="Path to metadata JSON file")
    input_group.add_argument("--batch", help="Path to directory containing metadata JSON files")
    
    # Output options
    parser.add_argument("--output", required=True, help="Path to save CSV file or directory for batch processing")
    
    # Configuration options
    parser.add_argument("--template", default="templates/LSI_ACS_header.csv", help="Path to LSI template CSV file")
    parser.add_argument("--config", help="Path to LSI configuration file")
    parser.add_argument("--tranche", help="Name of the tranche configuration to use (e.g., 'xynapse_tranche_1')")
    parser.add_argument("--log-dir", default="logs/lsi_generation", help="Directory for detailed logging")
    
    # LLM options
    parser.add_argument("--enable-llm", action="store_true", help="Enable LLM field completion")
    parser.add_argument("--model", default="gemini/gemini-2.5-flash", help="LLM model name to use for field completion")
    
    # Book content options
    parser.add_argument("--content", help="Path to book content file")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Generate LSI CSV
    if args.input:
        # Single file processing
        result = generate_lsi_csv(
            metadata=args.input,
            output_path=args.output,
            template_path=args.template,
            config_path=args.config,
            tranche_name=args.tranche,
            book_content=args.content,
            enable_llm=args.enable_llm,
            model_name=args.model,
            log_directory=args.log_dir
        )
        
        # Print result
        if result["success"]:
            print(f"LSI CSV generation successful: {result['output_path']}")
            if "analysis" in result and result["analysis"]:
                print(f"Completeness: {result['analysis']['completeness_percentage']:.2f}%")
                print(f"Populated fields: {result['analysis']['populated_fields']} out of {result['analysis']['total_fields']}")
        else:
            print(f"LSI CSV generation failed: {result.get('error', 'Unknown error')}")
    else:
        # Batch processing
        result = process_batch(
            input_dir=args.batch,
            output_dir=args.output,
            template_path=args.template,
            config_path=args.config,
            tranche_name=args.tranche,
            enable_llm=args.enable_llm,
            model_name=args.model,
            log_directory=args.log_dir
        )
        
        # Print result
        if result["success"]:
            print(f"Batch processing successful: {result['successful_files']} out of {result['total_files']} files processed")
        else:
            print(f"Batch processing failed: {result.get('error', 'Unknown error')}")
            print(f"Successful files: {result.get('successful_files', 0)} out of {result.get('total_files', 0)}")

if __name__ == "__main__":
    main()