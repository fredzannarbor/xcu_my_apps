#!/usr/bin/env python3
"""
Command-line tool to expand imprint concepts into fully detailed ExpandedImprint objects.

Supports both single file processing (backward compatibility) and batch processing from CSV files.

Usage:
    # Single file processing (backward compatibility)
    python tools/expand_imprint_cli.py -i input.txt -o output.json
    
    # CSV batch processing
    python tools/expand_imprint_cli.py --csv input.csv --output-dir output/
    
    # Directory batch processing
    python tools/expand_imprint_cli.py --directory csv_files/ --output-dir output/
    
    # With custom column mapping
    python tools/expand_imprint_cli.py --csv input.csv --output-dir output/ --column-mapping concept:imprint_concept
    
    # With attribute filtering
    python tools/expand_imprint_cli.py --csv input.csv --output-dir output/ --attributes branding,design_specifications
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.imprint_concept import ImprintConceptParser
from codexes.modules.imprint_builder.imprint_expander import ImprintExpander, LLMCaller
from enhanced_imprint_expander import EnhancedImprintExpander

# Import batch processing components
from codexes.modules.imprint_builder.batch_processor import BatchProcessor
from codexes.modules.imprint_builder.batch_models import (
    BatchConfig,
    OutputConfig,
    ProcessingOptions,
    ErrorHandlingConfig,
    NamingStrategy,
    OrganizationStrategy,
    ErrorHandlingMode
)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Expand imprint concepts from text files or CSV files to complete JSON specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file processing (backward compatibility)
  %(prog)s -i concept.txt -o output.json
  
  # CSV batch processing
  %(prog)s --csv imprints.csv --output-dir output/
  
  # Directory batch processing
  %(prog)s --directory csv_files/ --output-dir output/
  
  # With custom column mapping
  %(prog)s --csv input.csv --output-dir output/ --column-mapping concept:imprint_concept,name:imprint_name
  
  # With attribute filtering
  %(prog)s --csv input.csv --output-dir output/ --attributes branding,design_specifications
  
  # With subattribute filtering
  %(prog)s --csv input.csv --output-dir output/ --attributes branding --subattributes imprint_name,mission_statement
        """
    )
    
    # Processing mode arguments (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    # Single file mode (backward compatibility)
    mode_group.add_argument(
        "-i", "--input-file",
        type=Path,
        help="Text file containing single imprint concept description"
    )
    
    # CSV batch mode
    mode_group.add_argument(
        "--csv",
        type=Path,
        help="CSV file containing multiple imprint concepts"
    )
    
    # Directory batch mode
    mode_group.add_argument(
        "--directory",
        type=Path,
        help="Directory containing CSV files to process"
    )
    
    # Output arguments
    parser.add_argument(
        "-o", "--output-file",
        type=Path,
        help="Output JSON file (required for single file mode)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for batch processing (required for CSV/directory modes)"
    )
    
    # Batch processing options
    parser.add_argument(
        "--column-mapping",
        type=str,
        help="Column mapping in format 'csv_col:target_col,csv_col2:target_col2' (e.g., 'concept:imprint_concept')"
    )
    
    parser.add_argument(
        "--attributes",
        type=str,
        help="Comma-separated list of attributes to focus on (e.g., 'branding,design_specifications')"
    )
    
    parser.add_argument(
        "--subattributes",
        type=str,
        help="Comma-separated list of subattributes to focus on (e.g., 'imprint_name,color_palette')"
    )
    
    # Output organization options
    parser.add_argument(
        "--naming-strategy",
        choices=["imprint_name", "row_number", "hybrid"],
        default="imprint_name",
        help="File naming strategy for batch processing (default: imprint_name)"
    )
    
    parser.add_argument(
        "--organization-strategy",
        choices=["flat", "by_source", "by_imprint"],
        default="by_source",
        help="Directory organization strategy for batch processing (default: by_source)"
    )
    
    # Processing options
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing for batch operations"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=True,
        help="Continue processing other items when errors occur (default: True)"
    )
    
    # Error handling options
    parser.add_argument(
        "--error-mode",
        choices=["fail_fast", "continue_on_error", "collect_errors"],
        default="continue_on_error",
        help="Error handling mode (default: continue_on_error)"
    )
    
    parser.add_argument(
        "--max-errors",
        type=int,
        default=100,
        help="Maximum errors per file before stopping (default: 100)"
    )
    
    # General options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Don't create index file for batch processing"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )

    return parser.parse_args()


def read_input_file(input_path: Path) -> str:
    """Read and validate input file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError("Input file is empty")
        
        return content
    
    except Exception as e:
        raise RuntimeError(f"Error reading input file: {e}")


def create_llm_caller(use_real_llm: bool) -> LLMCaller:
    """Create appropriate LLM caller based on configuration."""
    if use_real_llm:
        # Try to import and use real LLM caller
        try:
            from codexes.core.llm_integration import LLMCaller as RealLLMCaller
            logging.info("Using real LLM caller")
            return RealLLMCaller()
        except ImportError as e:
            logging.warning(f"Real LLM caller not available ({e}), exiting")
            exit()
    else:
        logging.warning("LLM caller not available")
        exit()


def validate_arguments(args):
    """Validate command line arguments."""
    errors = []
    
    # Single file mode validation
    if args.input_file:
        if not args.output_file:
            errors.append("Single file mode requires --output-file (-o)")
        if args.output_dir:
            errors.append("Single file mode cannot use --output-dir")
        if args.csv or args.directory:
            errors.append("Cannot combine single file mode with CSV or directory mode")
    
    # Batch mode validation
    elif args.csv or args.directory:
        if not args.output_dir:
            errors.append("Batch processing requires --output-dir")
        if args.output_file:
            errors.append("Batch processing cannot use --output-file (-o)")
    
    # Column mapping validation
    if args.column_mapping:
        try:
            parse_column_mapping(args.column_mapping)
        except ValueError as e:
            errors.append(f"Invalid column mapping: {e}")
    
    # Worker validation
    if args.max_workers < 1:
        errors.append("--max-workers must be at least 1")
    
    if args.max_errors < 1:
        errors.append("--max-errors must be at least 1")
    
    return errors


def parse_column_mapping(mapping_str: str) -> Dict[str, str]:
    """Parse column mapping string into dictionary."""
    if not mapping_str:
        return {}
    
    mapping = {}
    try:
        for pair in mapping_str.split(','):
            if ':' not in pair:
                raise ValueError(f"Invalid mapping format: '{pair}'. Use 'source:target' format")
            
            source, target = pair.split(':', 1)
            source = source.strip()
            target = target.strip()
            
            if not source or not target:
                raise ValueError(f"Empty source or target in mapping: '{pair}'")
            
            mapping[source] = target
        
        return mapping
    
    except Exception as e:
        raise ValueError(f"Failed to parse column mapping: {e}")


def parse_list_argument(arg_str: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list."""
    if not arg_str:
        return None
    
    return [item.strip() for item in arg_str.split(',') if item.strip()]


def create_batch_config(args) -> BatchConfig:
    """Create batch configuration from command line arguments."""
    # Parse column mapping
    column_mapping = parse_column_mapping(args.column_mapping or "")
    
    # Parse attributes and subattributes
    attributes = parse_list_argument(args.attributes)
    subattributes = parse_list_argument(args.subattributes)
    
    # Create output config
    output_config = OutputConfig(
        base_directory=args.output_dir,
        naming_strategy=NamingStrategy(args.naming_strategy),
        organization_strategy=OrganizationStrategy(args.organization_strategy),
        create_index=not args.no_index,
        overwrite_existing=args.overwrite,
        create_subdirectories=True
    )
    
    # Create processing options
    processing_options = ProcessingOptions(
        parallel_processing=args.parallel,
        max_workers=args.max_workers,
        continue_on_error=args.continue_on_error,
        validate_output=True,
        timeout_seconds=300
    )
    
    # Create error handling config
    error_handling = ErrorHandlingConfig(
        mode=ErrorHandlingMode(args.error_mode),
        log_level="DEBUG" if args.verbose else "INFO",
        create_error_report=True,
        include_stack_traces=args.verbose,
        max_errors_per_file=args.max_errors
    )
    
    return BatchConfig(
        column_mapping=column_mapping,
        attributes=attributes,
        subattributes=subattributes,
        output_config=output_config,
        error_handling=error_handling,
        processing_options=processing_options
    )


def expand_imprint_concept(concept_text: str, use_real_llm: bool = False) -> dict:
    """Expand imprint concept into full ExpandedImprint specification."""
    
    # Create LLM caller
    llm_caller = create_llm_caller(use_real_llm)
    
    # Parse the concept
    parser = ImprintConceptParser(llm_caller)
    concept = parser.parse_concept(concept_text)
    
    # Choose expander based on LLM availability
    if use_real_llm:
        try:
            # Use enhanced expander with real LLM
            expander = EnhancedImprintExpander(llm_caller)
            result = expander.expand_concept(concept)
            logging.info("Used enhanced expander with real LLM")
        except Exception as e:
            logging.warning(f"Enhanced expander failed ({e}), falling back to standard expander")
            expander = ImprintExpander(llm_caller)
            expanded_imprint = expander.expand_concept(concept)
            result = expanded_imprint.to_dict()
    else:
        # Use standard expander with mock data
        logging.warning("No LLM module available, exiting")
        exit()
    
    # Add metadata
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'generator_version': '2.0.0',
        'input_concept': concept_text,
        'used_real_llm': use_real_llm,
        'expander_type': 'enhanced' if use_real_llm else 'standard',
        'llm_result' : result
    }
    
    return result


def write_output_file(output_path: Path, data: dict):
    """Write expanded imprint data to JSON file."""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logging.info(f"Successfully wrote expanded imprint to: {output_path}")
        
    except Exception as e:
        raise RuntimeError(f"Error writing output file: {e}")


def validate_output(data: dict) -> bool:
    """Validate that the output contains all expected sections."""
    required_sections = [
        'concept',
        'branding', 
        'design_specifications',
        'publishing_strategy',
        'operational_framework',
        'marketing_approach',
        'financial_projections',
        'expanded_at'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in data:
            missing_sections.append(section)
    
    if missing_sections:
        logging.warning(f"Missing sections in output: {missing_sections}")
        return False
    
    # Validate key sub-attributes
    branding = data.get('branding', {})
    required_branding = ['imprint_name', 'mission_statement', 'brand_values']
    for field in required_branding:
        if not branding.get(field):
            logging.warning(f"Missing required branding field: {field}")
            return False
    
    design = data.get('design_specifications', {})
    if not design.get('typography', {}).get('primary_font'):
        logging.warning("Missing primary_font in typography")
        return False
    
    publishing = data.get('publishing_strategy', {})
    if not publishing.get('primary_genres'):
        logging.warning("Missing primary_genres in publishing strategy")
        return False
    
    logging.info("✅ Output validation passed - all required sections and fields present")
    return True


def process_single_file(args):
    """Process single text file (backward compatibility mode)."""
    logging.info(f"Processing single file: {args.input_file}")
    
    # Read input
    concept_text = read_input_file(args.input_file)
    logging.info(f"Read concept text ({len(concept_text)} characters)")
    
    # Expand concept using original method
    use_real_llm = True
    expanded_data = expand_imprint_concept(concept_text, use_real_llm)
    
    # Validate output
    if not validate_output(expanded_data):
        logging.error("Output validation failed")
        return False
    
    # Write output
    write_output_file(args.output_file, expanded_data)
    
    # Summary
    sections = len([k for k in expanded_data.keys() if not k.startswith('_')])
    total_fields = sum(len(v) if isinstance(v, dict) else 1 for v in expanded_data.values())
    
    logging.info(f"✅ Successfully generated expanded imprint:")
    logging.info(f"   - {sections} main sections")
    logging.info(f"   - {total_fields} total fields")
    logging.info(f"   - Output: {args.output_file}")
    
    return True


def process_batch(args):
    """Process CSV file or directory in batch mode."""
    # Create LLM caller
    llm_caller = create_llm_caller(True)
    
    # Create batch configuration
    config = create_batch_config(args)
    
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        logging.error("Configuration validation failed:")
        for error in config_errors:
            logging.error(f"  - {error}")
        return False
    
    # Create batch processor
    processor = BatchProcessor(llm_caller, config)
    
    # Process based on mode
    if args.csv:
        logging.info(f"Processing CSV file: {args.csv}")
        result = processor.process_csv_file(args.csv)
    elif args.directory:
        logging.info(f"Processing directory: {args.directory}")
        result = processor.process_directory(args.directory)
    else:
        logging.error("No input specified for batch processing")
        return False
    
    # Display results
    logging.info("🔄 Batch processing completed!")
    logging.info(f"   - Total processed: {result.total_processed}")
    logging.info(f"   - Successful: {result.successful}")
    logging.info(f"   - Failed: {result.failed}")
    logging.info(f"   - Success rate: {result.get_success_rate():.1f}%")
    logging.info(f"   - Processing time: {result.processing_time:.2f}s")
    
    if result.index_file:
        logging.info(f"   - Index file: {result.index_file}")
    
    # Show errors summary if any
    if result.errors:
        logging.warning(f"⚠️  {len(result.errors)} errors occurred:")
        error_types = {}
        for error in result.errors[:5]:  # Show first 5 errors
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
            logging.warning(f"   - {error.error_type}: {error.message}")
        
        if len(result.errors) > 5:
            logging.warning(f"   - ... and {len(result.errors) - 5} more errors")
    
    # Show warnings summary if any
    if result.warnings:
        logging.info(f"ℹ️  {len(result.warnings)} warnings occurred")
    
    # Get detailed summary
    summary = processor.get_processing_summary(result)
    
    if args.verbose:
        logging.info("📊 Detailed Summary:")
        logging.info(f"   - Average processing time: {summary['processing'].get('average_processing_time', 0):.2f}s")
        logging.info(f"   - Output directory: {summary['output']['base_directory']}")
        logging.info(f"   - Files written: {len(summary['output'].get('output_files', []))}")
        
        if summary['errors']['errors_by_type']:
            logging.info("   - Error breakdown:")
            for error_type, count in summary['errors']['errors_by_type'].items():
                logging.info(f"     * {error_type}: {count}")
    
    return result.successful > 0 or result.total_processed == 0


def main():
    """Main CLI function."""
    setup_logging()
    
    try:
        # Parse arguments
        args = parse_arguments()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Validate arguments
        validation_errors = validate_arguments(args)
        if validation_errors:
            logging.error("Argument validation failed:")
            for error in validation_errors:
                logging.error(f"  - {error}")
            sys.exit(1)
        
        # Process based on mode
        success = False
        
        if args.input_file:
            # Single file mode (backward compatibility)
            success = process_single_file(args)
        else:
            # Batch processing mode
            success = process_batch(args)
        
        if not success:
            sys.exit(1)
        
    except KeyboardInterrupt:
        logging.info("🛑 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()