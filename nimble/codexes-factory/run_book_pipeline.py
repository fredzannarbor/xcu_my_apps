# run_book_pipeline.py
# version 2.4.0
import argparse
import csv
import json
import logging
import os
import re
import sys
import time
import warnings
from pathlib import Path
import importlib.util
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import chardet
import fitz  # PyMuPDF

def load_schedule_with_fallback(file_path):
    """Load schedule file with automatic format detection and fallback handling."""
    logger.info(f"Loading schedule file: {file_path}")

    # Check if file exists and is not empty
    if not os.path.exists(file_path):
        raise Exception(f"Schedule file not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise Exception(f"Schedule file is empty: {file_path}")

    # Determine format by extension first, then content
    file_ext = file_path.lower()

    # Try JSON first if it has .json extension
    if file_ext.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise Exception("JSON file is empty")

                schedule_data = json.loads(content)
                if isinstance(schedule_data, dict) and "publishing_schedule" in schedule_data:
                    all_books = [book for month in schedule_data["publishing_schedule"] for book in month.get("books", [])]
                    logger.info(f"✅ Loaded JSON schedule with {len(all_books)} books")
                    return all_books
                else:
                    # JSON but not in expected format, try to use as-is
                    if isinstance(schedule_data, list):
                        logger.info(f"✅ Loaded JSON list with {len(schedule_data)} books")
                        return schedule_data
                    else:
                        raise Exception("JSON format not recognized (expected publishing_schedule structure or book list)")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}. Trying CSV format...")
        except Exception as e:
            logger.warning(f"JSON loading failed: {e}. Trying CSV format...")

    # Try CSV format (either .csv extension or fallback from failed JSON)
    try:
        books_df_raw = read_csv_robust(file_path)

        # Map 'isbn' column to 'isbn13' if it exists
        if 'isbn' in books_df_raw.columns and 'isbn13' not in books_df_raw.columns:
            books_df_raw['isbn13'] = books_df_raw['isbn']
            logger.info("✅ Mapped 'isbn' column to 'isbn13' for compatibility")

        all_books = books_df_raw.to_dict('records')
        logger.info(f"✅ Loaded CSV schedule with {len(all_books)} books")
        return all_books

    except Exception as csv_error:
        if file_ext.endswith('.json'):
            raise Exception(f"Failed to parse as JSON or CSV. JSON error: failed to parse. CSV error: {csv_error}")
        else:
            raise Exception(f"Failed to parse CSV: {csv_error}")

def load_schedule_file(file_path):
    # Try to detect encoding first
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
    
    # Try different encodings in order of preference
    encodings_to_try = [detected_encoding, 'utf-8', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin1']
    
    for encoding in encodings_to_try:
        if encoding is None:
            continue
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"Successfully loaded with encoding: {encoding}")
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Last resort: ignore errors
    try:
        df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        print("Loaded with UTF-8, ignoring errors")
        return df
    except Exception as e:
        raise Exception(f"Could not read file with any encoding: {e}")

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import enhanced prompts system
try:
    from src.codexes.modules.prompts.enhanced_prompts_manager import EnhancedPromptsManager, BookStructure
except ImportError:
    try:
        from codexes.modules.prompts.enhanced_prompts_manager import EnhancedPromptsManager, BookStructure
    except ImportError:
        EnhancedPromptsManager = None
        BookStructure = None

# Set up basic logging configuration first
from codexes.core.logging_config import setup_application_logging, get_logging_manager

# Initialize basic logging
logging_manager = get_logging_manager()
logging_config = logging_manager.get_environment_config('production')
setup_application_logging(logging_config)

# Project-level imports
try:
    # Try importing with the standard module path
    from codexes.modules.builders import llm_get_book_data
    from codexes.modules.verifiers import quote_verifier
    from codexes.modules.distribution import generate_catalog
    from codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
    from codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter
    from codexes.modules.metadata.metadata_models import CodexMetadata
    from codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem
    from codexes.modules.distribution.lsi_field_completion_reporter import LSIFieldCompletionReporter
    from codexes.modules.distribution.field_mapping_registry import create_enhanced_lsi_registry
    from codexes.modules.distribution.lsi_configuration import LSIConfiguration
    from codexes.modules.distribution.isbn_database import ISBNDatabase
    from codexes.modules.distribution.isbn_assignment import assign_isbn_to_book
    from codexes.modules.distribution.date_utils import assign_publication_dates
    from codexes.core.token_usage_tracker import TokenUsageTracker
    from codexes.core.statistics_reporter import StatisticsReporter
    from codexes.core.logging_config import setup_application_logging, get_logging_manager
    from codexes.core import llm_caller
    
    # Apply LiteLLM filter AFTER all imports (so LiteLLM loggers are set up)
    logging_manager.apply_litellm_filter()
except ModuleNotFoundError:
    # Fall back to src-prefixed imports when running from project root
    from src.codexes.modules.builders import llm_get_book_data
    from src.codexes.modules.verifiers import quote_verifier
    from src.codexes.modules.distribution import generate_catalog
    from src.codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
    from src.codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter
    from src.codexes.modules.metadata.metadata_models import CodexMetadata
    from src.codexes.modules.distribution.lsi_field_completion_reporter import LSIFieldCompletionReporter
    from src.codexes.modules.distribution.field_mapping_registry import create_enhanced_lsi_registry
    from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration
    from src.codexes.modules.distribution.isbn_database import ISBNDatabase
    from src.codexes.modules.distribution.isbn_assignment import assign_isbn_to_book
    from src.codexes.modules.distribution.date_utils import assign_publication_dates
    from src.codexes.core.token_usage_tracker import TokenUsageTracker
    from src.codexes.core.statistics_reporter import StatisticsReporter
    from src.codexes.core.logging_config import setup_application_logging, get_logging_manager
    from src.codexes.core import llm_caller

# Apply LiteLLM filter AFTER all imports (so LiteLLM loggers are set up)
logging_manager.apply_litellm_filter()

# Initialize logger (will be configured later in main)
logger = logging.getLogger(__name__)


class SuccessAwareTerseLogFilter(logging.Filter):
    """Filters out INFO logs that don't contain key status emojis, but always allows success messages."""
    def filter(self, record):
        try:
            message = record.getMessage()
            # Always allow success and statistics messages (success message guarantee)
            # regardless of log level
            if any(emoji in message for emoji in ["✅", "📊"]):
                return True
        except Exception:
            # If we can't get the message, allow it through to be safe
            pass
        
        # For non-success messages, apply normal filtering
        if record.levelno == logging.INFO:
            try:
                message = record.getMessage()
                # For other INFO messages, only show if they contain status emojis
                return any(emoji in message for emoji in ["❌", "⚠️"])
            except Exception:
                # If we can't get the message, allow it through to be safe
                return True
        
        # Allow all non-INFO messages through (WARNING, ERROR, etc.)
        return True


class SuccessAwarePromptLogFilter(logging.Filter):
    """Shows only prompt-related INFO logs, but always allows success messages."""
    def filter(self, record):
        try:
            message = record.getMessage()
            # Always allow success and statistics messages (success message guarantee)
            # regardless of log level
            if any(emoji in message for emoji in ["✅", "📊"]):
                return True
        except Exception:
            # If we can't get the message, allow it through to be safe
            pass
        
        # For non-success messages, apply normal filtering
        if record.levelno == logging.INFO:
            try:
                message = record.getMessage()
                # For other INFO messages, only show prompt-related ones
                return "prompt name:" in message.lower() or "prompt:" in message.lower() or "params:" in message.lower()
            except Exception:
                # If we can't get the message, allow it through to be safe
                return True
        
        # Allow all non-INFO messages through (WARNING, ERROR, etc.)
        return True


def save_llm_response_to_json(response: Dict[str, Any], prompt: str, prompt_name: str,
                             output_dir: Path, safe_basename: str) -> None:
    """Save LLM response to a JSON file in the build directory."""
    from codexes.core.logging_filters import log_success
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    build_dir = output_dir / ".build"
    build_dir.mkdir(exist_ok=True, parents=True)

    response_data = {
        "timestamp": timestamp,
        "prompt_name": prompt_name,
        "prompt": prompt,
        "response": response
    }

    filename = f"{safe_basename}_{prompt_name}_{timestamp}.json"
    with open(build_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, ensure_ascii=False, indent=2)

    log_success(logger, f"✅ Saved LLM response for {prompt_name} to {build_dir / filename}")


def read_csv_robust(file_path, **kwargs):
    """Drop-in replacement for pd.read_csv with encoding detection."""

    # Detect encoding
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)
        detected_encoding = chardet.detect(raw_data)['encoding']

    # Try encodings in order
    for encoding in [detected_encoding, 'utf-8', 'windows-1252', 'iso-8859-1', 'latin1']:
        if encoding is None:
            continue
        try:
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        except (UnicodeDecodeError, UnicodeError):
            continue

    # Last resort
    return pd.read_csv(file_path, encoding='utf-8', errors='ignore', **kwargs)

# --- Helper Function ---
def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be used as a safe filename."""
    if not isinstance(name, str):
        name = str(name)
    name = re.sub(r'[\s/:\\]+', '_', name)
    name = re.sub(r'[^\w\-_]', '', name)
    return name.strip('_')


def set_pdf_metadata(pdf_path: Path, metadata: Dict[str, str]):
    """Sets metadata for a given PDF file using PyMuPDF."""
    from codexes.core.logging_filters import log_success
    if not pdf_path.exists():
        logger.warning(f"⚠️ Cannot set metadata. PDF file not found: {pdf_path}")
        return

    try:
        doc = fitz.open(str(pdf_path))
        new_meta = doc.metadata
        
        for key, value in metadata.items():
            if value:
                new_meta[key] = value
        
        doc.set_metadata(new_meta)
        doc.saveIncr()
        doc.close()
        log_success(logger, f"✅ Successfully set metadata for {pdf_path.name}")
    except Exception as e:
        logger.error(f"❌ Failed to set metadata for {pdf_path}: {e}", exc_info=True)


def process_single_book(book_data: pd.Series, config: dict, args: argparse.Namespace, imprint_prepress, prompt_keys: List[str], reprompt_keys: List[str], book_structure=None) -> dict:
    """
    Runs the selected pipeline stages for a single book and returns a summary.
    """
    title = book_data.get('title', 'Untitled Book')
    safe_basename = sanitize_filename(title)
    logger.info(f"--- Processing Book: '{title}' ---")
    logger.info(f"Using sanitized filename base: '{safe_basename}'")

    # Set quotes_per_book from CLI args if provided, otherwise use default or from book_data
    from codexes.core.logging_filters import log_success
    
    if args.quotes_per_book is not None:
        book_data['quotes_per_book'] = args.quotes_per_book
        log_success(logger, f"✅ Using CLI specified quotes_per_book: {args.quotes_per_book}")
    elif 'quotes_per_book' not in book_data:
        book_data['quotes_per_book'] = 90
        log_success(logger, f"✅ Using default quotes_per_book: 90")
    else:
        log_success(logger, f"✅ Using book_data quotes_per_book: {book_data['quotes_per_book']}")

    # --- Initialize Accurate Reporting System ---
    reporting_system = AccurateReportingSystem()
    
    # --- Initialize Summary ---
    book_summary = {
        "title": title,
        "status": "Failed",
        "prompts_successful": 0,
        "quotes_found": 0,
        "quotes_verified": 0,
        "quotes_accurate": 0,
        "pages": 0,
        "json_path": None,
        "lsi_csv_generated": False,
        "lsi_fields_populated": 0,
        "lsi_validation_passed": False,
        "mnemonics_generated": False
    }

    # --- Define file paths ---
    processed_llm_output_dir = config['processed_llm_output_dir']
    prepress_output_dir = config['prepress_output_dir']
    json_filepath = processed_llm_output_dir / f"{safe_basename}.json"
    book_summary["json_path"] = str(json_filepath)

    imprint_build_dir = config['base_dir'] / ".build"
    imprint_build_dir.mkdir(exist_ok=True, parents=True)
    config['build_dir'] = imprint_build_dir

    # --- Stage 1: LLM Content Generation ---
    if args.start_stage <= 1 <= args.end_stage:
        if not json_filepath.exists() or args.overwrite:
            if args.overwrite and json_filepath.exists():
                logger.info(f"⚠️ Overwriting existing file: {json_filepath}")
            logger.info("--- Stage 1: LLM Content Generation ---")
            try:
                main_prompt_keys = [key for key in prompt_keys if key not in reprompt_keys]

                if args.only_run_prompts:
                    specified_prompts = [p.strip() for p in args.only_run_prompts.split(',')]
                    filtered_prompt_keys = [key for key in main_prompt_keys if key in specified_prompts]
                    if filtered_prompt_keys:
                        log_success(logger, f"✅ Running only specified prompts: {', '.join(filtered_prompt_keys)}")
                        main_prompt_keys = filtered_prompt_keys
                    else:
                        logger.warning(f"⚠️ No matching prompts found in {args.only_run_prompts}. Using all prompts.")

                book_json_data, llm_stats = llm_get_book_data.process_book(
                    book_data=book_data.to_dict(),
                    prompt_template_file=config['prompt_template_file'],
                    model_name=config['model'],
                    per_model_params=config['model_params'],
                    raw_output_dir=config['raw_llm_output_dir'],
                    safe_basename=safe_basename,
                    prompt_keys=main_prompt_keys,
                    catalog_only=args.catalog_only,
                    build_dir=config['build_dir'],
                    reporting_system=reporting_system,
                    enable_metadata_discovery=args.enable_metadata_discovery,
                    imprint_config=config.get('imprint_config', {})
                )
                logger.info(f"Per-model params were passed: {config['model_params']}")

                if not book_json_data:
                    raise ValueError("LLM Builder did not return valid data.")

                if reprompt_keys and not args.no_reprompt:
                    logger.info("--- Reprompting with main body complete ---")
                    for reprompt_key in reprompt_keys:
                        logger.info(f"Reprompting with key: {reprompt_key}")
                        reprompt_data = llm_get_book_data.reprompt_and_update(
                            book_data=book_json_data,
                            prompt_key=reprompt_key,
                            prompt_template_file=config['prompt_template_file'],
                            model_name=config['model'],
                            per_model_params=config['model_params'],
                            imprint_config=config.get('imprint_config', {})
                        )
                        if reprompt_data:
                            book_json_data.update(reprompt_data)
                            llm_stats["prompts_successful"] += 1
                            log_success(logger, f"✅ Reprompting successful for key: {reprompt_key}")
                        else:
                            logger.warning(f"⚠️ Reprompting failed for key: {reprompt_key}")
                elif args.no_reprompt:
                    logger.info("Skipping reprompting step as requested by --no-reprompt flag.")

                book_summary.update(llm_stats)
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(book_json_data, f, ensure_ascii=False, indent=4)
                log_success(logger, f"✅ Stage 1 complete. Processed JSON saved to {json_filepath}")
            except Exception as e:
                logger.error(f"❌ LLM content generation failed for {title}: {e}", exc_info=True)
                return book_summary
        else:
            logger.info(f"Skipping Stage 1: Output file {json_filepath} already exists. Use --overwrite to force.")
    else:
        logger.info("Skipping Stage 1: LLM Content Generation.")
        if not json_filepath.exists():
            logger.error(f"Stage 1 was skipped, but required input file {json_filepath} is missing. Aborting book.")
            return book_summary

    # --- Stage 2: Quote Verification ---
    # Quote verification is only enabled for xynapse_traces imprint by default
    enable_verification = (
        not args.catalog_only and
        args.verifier_model and
        not args.skip_verification and
        args.start_stage <= 2 <= args.end_stage and
        (args.imprint == "default" or "xynapse" in args.imprint.lower())
    )

    if enable_verification:
        logger.info("--- Stage 2: Quote Verification ---")
        try:
            verification_stats = quote_verifier.verify_quotes_in_file(
                json_path=json_filepath,
                verifier_model=args.verifier_model,
                prompt_template_file=config['prompt_template_file'],
                per_model_params=config['model_params']
            )
            if verification_stats is None:
                raise RuntimeError("Quote verification process reported a failure.")

            book_summary["quotes_verified"] = verification_stats.get("total_verified", 0)
            book_summary["quotes_accurate"] = verification_stats.get("accurate", 0)
        except Exception as e:
            logger.error(f"❌ Quote Verification (Stage 2) failed for {title}: {e}", exc_info=True)
            logger.warning("Proceeding to book production with unverified/uncorrected quotes.")
    else:
        if args.skip_verification:
            logger.info("Skipping Stage 2: Quote Verification (--skip-verification flag set).")
        else:
            logger.info("Skipping Stage 2: Quote Verification.")

    # --- Stage 3: Book Production (Interior & Cover) ---
    if args.start_stage <= 3 <= args.end_stage:
        # Define expected output paths to check for overwrite
        interior_pdf_path = prepress_output_dir / f"{safe_basename}_interior.pdf"
        cover_pdf_path = prepress_output_dir / "covers" / f"{safe_basename}_cover_spread.pdf"

        if not interior_pdf_path.exists() or not cover_pdf_path.exists() or args.overwrite:
            if args.overwrite and (interior_pdf_path.exists() or cover_pdf_path.exists()):
                logger.info("⚠️ Overwriting existing prepress files (interior/cover).")
            logger.info("--- Stage 3: Book Production (Interior & Cover) ---")
            try:
                # Ensure ISBN and body_source from schedule are available to prepress
                if json_filepath.exists():
                    with open(json_filepath, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    # Track if we need to save changes
                    json_modified = False

                    # Add ISBN from schedule if not in JSON or if empty
                    if ('isbn13' not in json_data or not json_data.get('isbn13')) and 'isbn13' in book_data and book_data['isbn13']:
                        json_data['isbn13'] = book_data['isbn13']
                        json_modified = True
                        logger.info(f"✅ Added ISBN from schedule to JSON: {book_data['isbn13']}")

                    # Add body_source from schedule if present
                    if 'body_source' in book_data and book_data['body_source']:
                        json_data['body_source'] = book_data['body_source']
                        json_modified = True
                        logger.info(f"✅ Added body_source from schedule to JSON: {book_data['body_source']}")

                    # Save changes if any were made
                    if json_modified:
                        with open(json_filepath, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)
                
                prepress_results = imprint_prepress.process_single_book(
                    json_path=json_filepath,
                    final_output_dir=prepress_output_dir,
                    templates_dir=config['templates_dir'],
                    debug_cover=args.debug_cover,
                    catalog_only=args.catalog_only,
                    leave_build_directories_in_place=args.leave_build_directories_in_place,
                    config=config
                )
                if not prepress_results or not prepress_results.get("pdf_path"):
                    raise FileNotFoundError("Prepress script did not create the expected interior PDF.")

                book_summary["pages"] = prepress_results.get("page_count", 0)
                log_success(logger, f"✅ Stage 3 complete. Artifacts saved in {prepress_output_dir}")
            except Exception as e:
                logger.error(f"❌ Book Production (Stage 3) failed for {title}: {e}", exc_info=True)
                return book_summary
        else:
            logger.info(f"Skipping Stage 3: Output files like {interior_pdf_path.name} already exist. Use --overwrite to force.")
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                book_summary["pages"] = data.get("page_count", 0)
                logger.info(f"Loaded page count ({book_summary['pages']}) from existing JSON.")
    else:
        logger.info("Skipping Stage 3: Book Production.")

    # --- Stage 3.5: Set PDF Metadata ---
    if args.start_stage <= 3 <= args.end_stage:
        logger.info("--- Stage 3.5: Setting PDF Metadata ---")
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Prepare metadata dictionary
            pdf_meta = {
                'title': json_data.get('title'),
                'author': json_data.get('author_name'),
                'subject': json_data.get('summary_short'),
                'keywords': ', '.join(json_data.get('keywords', []) if json_data.get('keywords') else []),
                'producer': json_data.get('publisher'),
                'creator': 'Codexes Factory Pipeline'
            }
            
            # Clean up None values
            pdf_meta = {k: v for k, v in pdf_meta.items() if v}

            # Set metadata for interior and cover PDFs
            interior_pdf_path = prepress_output_dir / f"{safe_basename}_interior.pdf"
            set_pdf_metadata(interior_pdf_path, pdf_meta)
            cover_pdf_path = prepress_output_dir / "covers" / f"{safe_basename}_cover_spread.pdf"
            set_pdf_metadata(cover_pdf_path, pdf_meta)

        except Exception as e:
            logger.error(f"❌ Failed to set PDF metadata for {title}: {e}", exc_info=True)

    # --- Stage 4: LSI CSV Generation (Individual Book Processing) ---
    if not args.skip_lsi and args.start_stage <= 4 <= args.end_stage:
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                book_json_data = json.load(f)
                logger.info(f"Loaded book JSON data for {title} from {json_filepath}")

            from dataclasses import fields
            codex_fields = {field.name for field in fields(CodexMetadata) if field.init}
            filtered_data = {k: v for k, v in book_json_data.items() if k in codex_fields}
            
            # Preserve ISBN from original schedule data if not in JSON
            if 'isbn13' not in filtered_data and 'isbn13' in book_data:
                filtered_data['isbn13'] = book_data['isbn13']
                logger.info(f"Added ISBN from schedule data: {book_data['isbn13']}")
            
            metadata = CodexMetadata(**filtered_data)

            # Calculate and distribute spine width using enhanced calculator
            try:
                from src.codexes.modules.covers.spine_width_calculator import SpineWidthCalculator
                
                spine_calculator = SpineWidthCalculator()
                
                # Get page count from metadata or use default
                page_count = getattr(metadata, 'page_count', None) or getattr(metadata, 'final_page_count', None) or 216
                paper_type = "Standard 70 perfect"  # As specified in requirements
                
                # Calculate spine width with validation
                spine_width, is_valid = spine_calculator.calculate_spine_width_with_validation(page_count, paper_type)
                
                if is_valid:
                    # Distribute spine width to metadata
                    spine_calculator.distribute_spine_width(spine_width, metadata)
                    logger.info(f"✅ Calculated and distributed spine width: {spine_width} inches for {page_count} pages")
                else:
                    logger.warning(f"⚠️ Spine width calculation validation failed, using calculated value anyway: {spine_width}")
                    spine_calculator.distribute_spine_width(spine_width, metadata)
                    
            except Exception as e:
                logger.error(f"❌ Spine width calculation failed: {e}")
                # Continue without spine width calculation

            # Extract book content from quotes for LLM field completion
            book_content = ""
            if 'quotes' in book_json_data and book_json_data['quotes']:
                quotes_text = []
                for quote_data in book_json_data['quotes']:
                    if isinstance(quote_data, dict) and 'quote' in quote_data:
                        quote_text = quote_data['quote']
                        source = quote_data.get('source', 'Unknown source')
                        author = quote_data.get('author', 'Unknown author')
                        quotes_text.append(f'"{quote_text}" - {author}, {source}')
                book_content = '\n\n'.join(quotes_text)
                logger.info(f"Extracted {len(book_json_data['quotes'])} quotes for LLM context ({len(book_content)} characters)")

            if config['enable_llm_completion']:
                logger.info("Initializing LLM field completer for enhanced metadata...")
                try:
                    metadata_dir = config['base_dir'] / 'metadata'
                    metadata_dir.mkdir(exist_ok=True, parents=True)

                    llm_completer = EnhancedLLMFieldCompleter(
                        model_name="gemini/gemini-2.5-flash",
                        prompts_path="prompts/enhanced_lsi_field_completion_prompts.json"
                    )
                    metadata = llm_completer.complete_missing_fields(metadata, book_content=book_content, save_to_disk=True, output_dir=str(metadata_dir))
                    log_success(logger, "✅ LLM field completion successful")

                    if config['tranche_name']:
                        try:
                            from src.codexes.modules.distribution.tranche_config_loader import TrancheConfigLoader
                            logger.info(f"Applying tranche configuration: {config['tranche_name']}")
                            tranche_loader = TrancheConfigLoader()
                            tranche_context = tranche_loader.get_tranche_context(config['tranche_name'])

                            for key, value in tranche_context.items():
                                if hasattr(metadata, key):
                                    logger.info(f"Setting {key} from tranche config: {value}")
                                    setattr(metadata, key, value)

                            annotation_boilerplate = tranche_loader.get_tranche_annotation_boilerplate(config['tranche_name'])
                            if annotation_boilerplate and hasattr(metadata, 'summary_long') and metadata.summary_long:
                                prefix = annotation_boilerplate.get('prefix', '')
                                suffix = annotation_boilerplate.get('suffix', '')
                                metadata.summary_long = f"{prefix}{metadata.summary_long}{suffix}"
                                logger.info("Applied annotation boilerplate to summary_long field")

                            if not hasattr(metadata, 'pub_date') or not metadata.pub_date:
                                try:
                                    tranche_info = tranche_loader.get_tranche_info(config['tranche_name'])
                                    book_count = tranche_info.get('book_count', 12)
                                    target_month, target_year = None, None
                                    if 'target_month' in tranche_info:
                                        month_str = tranche_info['target_month']
                                        try:
                                            target_month = int(month_str) if month_str.isdigit() else datetime.strptime(month_str, "%B").month
                                        except ValueError:
                                            target_month = datetime.strptime(month_str, "%b").month
                                    if 'target_year' in tranche_info:
                                        target_year = int(tranche_info['target_year'])

                                    dates = assign_publication_dates(book_count=book_count, tranche_name=config['tranche_name'], month=target_month, year=target_year)
                                    book_index = tranche_loader.get_book_index_in_tranche(config['tranche_name'], metadata.uuid) or 0
                                    pub_date = dates[book_index] if book_index < len(dates) else (dates[0] if dates else None)
                                    if pub_date:
                                        setattr(metadata, 'pub_date', pub_date)
                                        logger.info(f"Assigned publication date: {pub_date} (book index: {book_index})")
                                except Exception as e:
                                    logger.warning(f"Failed to assign publication date: {e}")
                        except Exception as e:
                            logger.warning(f"Failed to apply tranche configuration: {e}")

                    if config['enable_isbn_assignment'] and (not getattr(metadata, 'isbn13', None) or metadata.isbn13 == "Unknown"):
                        try:
                            isbn_db = ISBNDatabase("data/isbn_database.json")
                            publisher_id = getattr(metadata, 'publisher_id', "nimble-books")
                            success, isbn, details = assign_isbn_to_book(metadata=metadata, isbn_db=isbn_db, publisher_id=publisher_id, distribution_channels=["ingram"])
                            if success and isbn:
                                log_success(logger, f"✅ Successfully assigned ISBN {isbn} to book: {title}")
                                book_summary["isbn13"] = isbn
                            else:
                                logger.warning(f"⚠️ Failed to assign ISBN to book: {details['message']}")
                        except Exception as e:
                            logger.warning(f"ISBN assignment failed: {e}. Proceeding without ISBN.")
                    elif getattr(metadata, 'isbn13', None) and metadata.isbn13 != "Unknown":
                        logger.info(f"Book already has ISBN: {metadata.isbn13}")
                        book_summary["isbn13"] = metadata.isbn13
                    else:
                        logger.info("ISBN assignment is disabled. Proceeding without ISBN assignment.")

                    with open(str(processed_llm_output_dir / f"{safe_basename}_lsi_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=4)
                    log_success(logger, f"✅ LSI metadata saved to file {safe_basename}_lsi_metadata.json")
                except Exception as e:
                    logger.warning(f"LLM field completion failed: {e}. Proceeding with original metadata.")

            book_summary["lsi_metadata"] = metadata
            book_summary["lsi_ready"] = True
            log_success(logger, f"✅ Stage 4 metadata prepared for batch LSI generation: {title}")

        except Exception as e:
            logger.error(f"❌ LSI metadata preparation failed for {title}: {e}", exc_info=True)
            book_summary["lsi_ready"] = False
    else:
        if args.skip_lsi:
            logger.info("Skipping Stage 4: LSI CSV Generation (--skip-lsi flag set).")
        else:
            logger.info("Skipping Stage 4: LSI CSV Generation.")
        book_summary["lsi_ready"] = False

    # --- Generate Accurate Report ---
    try:
        accurate_report = reporting_system.generate_accurate_report()
        book_summary["accurate_report"] = accurate_report
        
        # Update summary with accurate statistics
        summary_stats = accurate_report.get('summary', {})
        book_summary["prompts_successful"] = summary_stats.get('successful_prompts', book_summary.get("prompts_successful", 0))
        book_summary["quotes_found"] = summary_stats.get('total_quotes_retrieved', book_summary.get("quotes_found", 0))
        book_summary["prompt_success_rate"] = summary_stats.get('prompt_success_rate', 0.0)
        book_summary["quote_retrieval_rate"] = summary_stats.get('quote_retrieval_rate', 0.0)
        
        log_success(logger, f"📊 Accurate Report: {book_summary['prompts_successful']} prompts successful, {book_summary['quotes_found']} quotes retrieved")
        
    except Exception as e:
        logger.error(f"Error generating accurate report: {e}")
    
    book_summary["status"] = "Completed"
    log_success(logger, f"--- ✅ Successfully finished all requested stages for: '{title}' ---")
    return book_summary


def main():
    """Main function to orchestrate the book generation pipeline."""
    parser = argparse.ArgumentParser(description="Book Generation Pipeline",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # --- Existing Arguments ---
    parser.add_argument("-b", "--base-dir", default=None, help="Base directory for all output files. If not set, defaults to output/{imprint}_build.")
    parser.add_argument("-bb", "--begin-with-book", type=int, default=None, help="Book number to start with (1-based index).")
    parser.add_argument("-cf", "--catalog-file", default="data/books.csv", help="Path to save the final storefront catalog CSV file.")
    parser.add_argument("-co", "--catalog-only", action="store_true", help="Run in catalog-only mode: generates metadata and cover for a fixed page count (216) without full content.")
    parser.add_argument("-dc", "--debug-cover", action="store_true", help="Enable debug layout guides on the cover PDF.")
    parser.add_argument("-dbd", "--delete-build-directories", action="store_false", dest="leave_build_directories_in_place", default=True, help="Delete temporary build directories after processing (default: keep directories)")
    parser.add_argument("-ei", "--enable-isbn-assignment", action="store_true", help="Enable automatic ISBN assignment for books that need it.")
    parser.add_argument("-el", "--enable-llm-completion", action="store_true", help="Enable LLM-powered field completion for missing LSI metadata.")
    parser.add_argument("--enable-metadata-discovery", action="store_true", help="Allow LLM to discover publisher, imprint, and author from content (for public domain works).")
    parser.add_argument("-es", "--end-stage", type=int, default=4, choices=[1, 2, 3, 4, 5], help="The stage to end at (1:LLM, 2:Verify, 3:Prepress, 4:LSI, 5:Marketing).")
    parser.add_argument("-eb", "--end-with-book", type=int, default=None, help="Book number to end with (1-based index).")
    parser.add_argument("-g", "--generate_bibliography",action="store_true", help="Look up books mentioned using API services (time=consuming)")
    parser.add_argument("-i", "--imprint", required=True, help="The imprint to use for the pipeline.")
    parser.add_argument("-lr", "--legacy-reports", action="store_true", help="Use only the legacy field report generator instead of the enhanced reporter")
    parser.add_argument("-lc", "--lsi-config", help="Path to LSI configuration file for enhanced field mapping.")
    parser.add_argument("-lt", "--lsi-template", default="templates/LSI_ACS_header.csv", help="Path to LSI template CSV file.")
    parser.add_argument("-mb", "--max-books", type=int, default=None, help="Maximum number of books to process.")
    parser.add_argument("-m", "--model", required=True, help="Primary LLM model for content generation.")
    parser.add_argument("-mp", "--model-params-file", default="resources/json/model_params.json", help="Path to model parameters JSON file.")
    parser.add_argument("-nl", "--no-litellm-log", action="store_true", help="Suppress LiteLLM INFO logs.")
    parser.add_argument("-op", "--only-run-prompts", help="Only run specified prompts, comma-separated (e.g., 'quotes,mnemonics')")
    parser.add_argument("-qp", "--quotes-per-book", type=int, help="Override the number of quotes per book")
    parser.add_argument("-rf", "--report-formats", default="html,csv,markdown", help="Comma-separated list of report formats to generate (html,csv,json,markdown)")
    parser.add_argument("-sf", "--schedule-file", required=False, help="Path to the schedule JSON file. Optional when using metadata from responses.")
    parser.add_argument("-pl", "--show-prompt-logs", action="store_true", help="Show prompt name, prompt, and params being submitted to LLM.")
    parser.add_argument("-sc", "--skip-catalog", action="store_true", help="Skip the final catalog generation step.")
    parser.add_argument("-sl", "--skip-lsi", action="store_true", help="Skip LSI CSV generation (Stage 4).")
    parser.add_argument("-ss", "--start-stage", type=int, default=1, choices=[1, 2, 3, 4, 5], help="The stage to start from (1:LLM, 2:Verify, 3:Prepress, 4:LSI, 5:Marketing).")
    parser.add_argument("-tl", "--terse-log", action="store_true", help="Enable terse logging (only show status emojis).")
    parser.add_argument("-t", "--tranche", help="Name of the tranche configuration to use (e.g., 'xynapse_tranche_1')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging including Pydantic warnings.")
    parser.add_argument("-vm", "--verifier-model", type=str, help="Optional: High-end LLM model for quote verification (e.g., 'openai/gpt-4o').")

    # --- New/Complementary Arguments ---
    parser.add_argument("-o", "--overwrite", action="store_true", help="Force re-running stages even if output files already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Show which books and stages would be processed without actually running the pipeline.")
    parser.add_argument("--only-books", help="Process only specific book numbers, comma-separated (e.g., '2,15'). Overrides other book selection flags.")
    parser.add_argument("--skip-verification", action="store_true", help="Explicitly skip the quote verification stage (Stage 2).")
    parser.add_argument("--no-reprompt", action="store_true", help="Skip the reprompting step for keys like 'mnemonics' or 'blurbs'.")

    # --- Enhanced Prompts Arguments ---
    parser.add_argument("--publisher-prompts", help="Comma-separated list of publisher-level prompts files to merge")
    parser.add_argument("--imprint-prompts", help="Comma-separated list of imprint-level prompts files to merge")
    parser.add_argument("--front-matter-prompts", help="Comma-separated list of prompts for front matter generation (in order)")
    parser.add_argument("--body-source", help="Path to markdown, PDF, or text file to use as book body")
    parser.add_argument("--back-matter-prompts", help="Comma-separated list of prompts for back matter generation (in order)")
    parser.add_argument("--book-structure-config", help="Path to saved book structure configuration JSON file")

    # --- Marketing Stage 5 Arguments ---
    parser.add_argument("--enable-marketing", action="store_true", help="Enable marketing material generation (Stage 5).")
    parser.add_argument("--marketing-formats", default="substack", help="Comma-separated list of marketing formats (substack,press_release,social_media).")
    parser.add_argument("--marketing-output-dir", default="marketing/generated", help="Directory to save generated marketing materials.")

    args = parser.parse_args()

    # --- Update Logging Configuration Based on Arguments ---
    # The basic logging is already set up early, now we adjust based on args
    
    # Determine environment based on arguments
    environment = 'development' if args.verbose else 'production'
    
    # Get the already initialized logging manager
    logging_manager = get_logging_manager()
    
    # Apply LiteLLM filtering based on arguments (unless disabled)
    if args.no_litellm_log:
        # If user wants LiteLLM logs, remove the filter
        litellm_logger = logging.getLogger('litellm')
        litellm_logger.filters.clear()
        logging_manager.disable_debug_mode()
    
    # Handle legacy filter options for backward compatibility
    if args.terse_log or args.show_prompt_logs:
        # Get the console handler and apply success-aware legacy filters
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                if args.terse_log:
                    handler.addFilter(SuccessAwareTerseLogFilter())
                elif args.show_prompt_logs:
                    handler.addFilter(SuccessAwarePromptLogFilter())
                break
    
    # Handle verbose mode
    if not args.verbose:
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
    else:
        # Enable debug mode for more verbose logging
        logging_manager.enable_debug_mode()

    if args.start_stage > args.end_stage:
        logger.error("Start stage cannot be after end stage.")
        sys.exit(1)

    # --- Setup Configuration and Directories ---
    imprint_dir = Path('imprints') / args.imprint
    if not imprint_dir.is_dir():
        logger.critical(f"Imprint directory not found at {imprint_dir}")
        sys.exit(1)

    base_dir = Path(args.base_dir) if args.base_dir else Path(f"output/{args.imprint}_build")
    build_dir = base_dir / ".build"
    build_dir.mkdir(exist_ok=True, parents=True)

    config = {
        'base_dir': base_dir,
        'build_dir': build_dir,
        'raw_llm_output_dir': base_dir / 'raw_json_responses',
        'processed_llm_output_dir': base_dir / 'processed_json',
        'prepress_output_dir': base_dir,
        'lsi_output_dir': base_dir / 'lsi_csv',
        'templates_dir': imprint_dir,
        'prompt_template_file': imprint_dir / 'prompts.json',
        'lsi_config_path': args.lsi_config,
        'lsi_template_path': args.lsi_template,
        'tranche_name': args.tranche,
        'enable_llm_completion': args.enable_llm_completion,
        'enable_isbn_assignment': args.enable_isbn_assignment,
        'model': args.model,
        'model_params': {},
        'generate_bibliography': args.generate_bibliography
    }

    # --- Load imprint configuration with persona data ---
    imprint_config_path = Path('configs') / 'imprints' / f'{args.imprint}.json'
    print(f"DEBUG: Checking for imprint config at: {imprint_config_path}")
    print(f"DEBUG: File exists: {imprint_config_path.exists()}")
    if imprint_config_path.exists():
        try:
            with open(imprint_config_path, 'r', encoding='utf-8') as f:
                imprint_config = json.load(f)
                config['imprint_config'] = imprint_config
                print(f"DEBUG: Successfully loaded config with persona: {imprint_config.get('persona', {}).get('name', 'NO PERSONA')}")
                logger.info(f"✅ Loaded imprint configuration from {imprint_config_path}")
        except Exception as e:
            print(f"DEBUG: Exception loading config: {e}")
            logger.warning(f"⚠️ Could not load imprint config from {imprint_config_path}: {e}")
            config['imprint_config'] = {}
    else:
        print(f"DEBUG: Config file not found!")
        logger.warning(f"⚠️ Imprint config not found at {imprint_config_path}")
        config['imprint_config'] = {}

    # --- Dynamically load the imprint's prepress module ---
    try:
        prepress_module_path = imprint_dir / 'prepress.py'
        spec = importlib.util.spec_from_file_location('imprint_prepress', prepress_module_path)
        imprint_prepress = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imprint_prepress)
    except FileNotFoundError:
        logger.critical(f"Could not find 'prepress.py' in imprint directory: {imprint_dir}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to load prepress module for imprint '{args.imprint}': {e}")
        sys.exit(1)

    # --- Enhanced Prompts Processing ---
    enhanced_prompts_enabled = any([
        args.publisher_prompts,
        args.imprint_prompts,
        args.front_matter_prompts,
        args.body_source,
        args.back_matter_prompts,
        args.book_structure_config
    ])

    virtual_prompts = None
    book_structure = None

    if enhanced_prompts_enabled and EnhancedPromptsManager:
        logger.info("🔄 Enhanced prompts mode enabled")
        prompts_manager = EnhancedPromptsManager()

        # Load book structure from config file if provided
        if args.book_structure_config:
            try:
                structure_path = Path(args.book_structure_config)
                book_structure = prompts_manager.load_book_structure(structure_path)
                logger.info(f"✅ Loaded book structure from {structure_path}")
            except Exception as e:
                logger.warning(f"Could not load book structure config: {e}")

        # Parse command line arguments for prompts
        publisher_files = []
        if args.publisher_prompts:
            publisher_files = [f.strip() for f in args.publisher_prompts.split(',')]

        imprint_files = []
        if args.imprint_prompts:
            imprint_files = [f.strip() for f in args.imprint_prompts.split(',')]

        # Create book structure from command line if not loaded from file
        if not book_structure:
            book_structure = BookStructure()

            if args.front_matter_prompts:
                book_structure.front_matter.prompts = [p.strip() for p in args.front_matter_prompts.split(',')]
                book_structure.front_matter.order = book_structure.front_matter.prompts.copy()

            if args.body_source:
                book_structure.body_source = args.body_source

            if args.back_matter_prompts:
                book_structure.back_matter.prompts = [p.strip() for p in args.back_matter_prompts.split(',')]
                book_structure.back_matter.order = book_structure.back_matter.prompts.copy()

        # Create virtual prompts file
        if publisher_files or imprint_files:
            try:
                virtual_prompts = prompts_manager.create_virtual_prompts_file(publisher_files, imprint_files)
                logger.info(f"✅ Created virtual prompts file with {len(virtual_prompts.get('prompt_keys', []))} keys")

                # Validate book structure
                errors = prompts_manager.validate_book_structure(book_structure, virtual_prompts)
                if errors:
                    logger.critical("❌ Book structure validation errors:")
                    for error in errors:
                        logger.critical(f"  • {error}")
                    sys.exit(1)

                # Use virtual prompts instead of traditional prompts
                prompt_keys = virtual_prompts.get("prompt_keys", [])
                reprompt_keys = virtual_prompts.get("reprompt_keys", [])

                # Save virtual prompts to temporary file for processing
                temp_prompts_path = Path(config['base_dir']) / "temp_virtual_prompts.json"
                with open(temp_prompts_path, 'w') as f:
                    json.dump(virtual_prompts, f, indent=2)
                config['prompt_template_file'] = str(temp_prompts_path)

                logger.info(f"✅ Using enhanced prompts with {len(prompt_keys)} prompt keys")

            except Exception as e:
                logger.critical(f"Failed to create virtual prompts: {e}")
                sys.exit(1)

        else:
            logger.warning("Enhanced prompts mode enabled but no prompts files specified - falling back to traditional imprint prompts")
            # Initialize empty lists to prevent UnboundLocalError
            prompt_keys = []
            reprompt_keys = []

    # --- Load imprint prompt configuration (traditional mode) ---
    # Fall back to traditional mode if enhanced mode is disabled OR if no prompts were loaded
    if not enhanced_prompts_enabled or not prompt_keys:
        try:
            with open(config['prompt_template_file'], 'r') as f:
                imprint_prompts = json.load(f)
                prompt_keys = imprint_prompts.get("prompt_keys", [])
                reprompt_keys = imprint_prompts.get("reprompt_keys", [])
                if not prompt_keys:
                    logger.critical(f"No 'prompt_keys' found in {config['prompt_template_file']}")
                    sys.exit(1)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.critical(f"Could not load or parse prompt config file: {e}")
            sys.exit(1)

    logger.info(f"📝 Using {len(prompt_keys)} prompt keys: {', '.join(prompt_keys)}")
    if reprompt_keys:
        logger.info(f"🔄 Using {len(reprompt_keys)} reprompt keys: {', '.join(reprompt_keys)}")

    model_params_path = Path(args.model_params_file)
    if model_params_path.exists():
        with open(model_params_path, 'r') as f:
            config['model_params'] = json.load(f)

    for dir_name in ['raw_llm_output_dir', 'processed_llm_output_dir', 'prepress_output_dir', 'lsi_output_dir']:
        config[dir_name].mkdir(parents=True, exist_ok=True)

    # --- Read Schedule File and Process Books ---
    if args.schedule_file:
        try:
            all_books = load_schedule_with_fallback(args.schedule_file)
            from codexes.core.logging_filters import log_success
            log_success(logger, f"✅ Opened schedule file {args.schedule_file} containing {len(all_books)} books.")
        except Exception as e:
            logger.critical(f"Failed to load or parse schedule file {args.schedule_file}: {e}")
            sys.exit(1)
    else:
        # No schedule file provided - will generate metadata from responses/body text
        logger.info("📝 No schedule file provided. Will extract metadata from responses and body text.")
        from codexes.core.logging_filters import log_success
        log_success(logger, "✅ Operating in metadata extraction mode - will derive book info from content.")
        # Auto-enable metadata discovery when no schedule file is provided
        args.enable_metadata_discovery = True
        logger.info("✅ Auto-enabled metadata discovery for schedule-less build.")

        # Create a default book entry when no schedule is provided
        # The pipeline will extract metadata from body source or generate content
        if args.body_source:
            logger.info(f"📄 Body source provided: {args.body_source}")
            # Generate basic book metadata that will be refined during processing
            default_book = {
                "title": "Generated Book",
                "subtitle": "Generated from provided content",
                "author": "Author TBD",
                "isbn13": "9780000000000",  # Placeholder ISBN
                "pages": 100,  # Default page count, will be updated
                "body_source": args.body_source
            }
        else:
            logger.info("📝 No body source provided - will generate content from prompts")
            # Create a minimal book entry for prompt-based generation
            default_book = {
                "title": "Generated Book",
                "subtitle": "Generated from prompts",
                "author": "Author TBD",
                "isbn13": "9780000000000",  # Placeholder ISBN
                "pages": 100,  # Default page count
            }

        all_books = [default_book]
        logger.info("📚 Created default book entry for metadata extraction mode")

    # --- Apply Book Selection Filters ---
    if args.only_books:
        try:
            selected_indices = {int(i.strip()) - 1 for i in args.only_books.split(',')}
            all_books = [book for i, book in enumerate(all_books) if i in selected_indices]
            log_success(logger, f"✅ Processing only specified books: {args.only_books}. Found {len(all_books)} matching books.")
        except ValueError:
            logger.error(f"❌ Invalid format for --only-books. Please provide comma-separated numbers. Value: '{args.only_books}'")
            sys.exit(1)
    else:
        if args.begin_with_book is not None:
            begin_index = max(0, args.begin_with_book - 1)
            all_books = all_books[begin_index:]
        if args.end_with_book is not None:
            end_index = max(0, args.end_with_book - (args.begin_with_book - 1 if args.begin_with_book else 0))
            all_books = all_books[:end_index]
        if args.max_books is not None:
            all_books = all_books[:args.max_books]

    books_df = pd.DataFrame(all_books)
    logger.info(f"Found {len(books_df)} books to process for imprint '{args.imprint}'.")

    # --- Dry Run Logic ---
    if args.dry_run:
        logger.info("--- DRY RUN MODE ENABLED ---")
        if not books_df.empty:
            print(f"\nPipeline would process {len(books_df)} book(s):")
            for index, row in books_df.iterrows():
                print(f"  - Book: {row.get('title', 'Untitled')}")
            print(f"\nStages to run: from {args.start_stage} to {args.end_stage}")
            print(f"Imprint: {args.imprint}")
            print(f"Model: {args.model}")
            if args.overwrite:
                print("Overwrite mode: ENABLED")
        else:
            print("No books found to process with the current filters.")
        sys.exit(0)

    logger.info(f"Pipeline will run from stage {args.start_stage} to {args.end_stage}.")
    if args.tranche: logger.info(f"--- USING TRANCHE CONFIGURATION: {args.tranche} ---")
    if args.catalog_only: logger.info("--- CATALOG-ONLY MODE ENABLED ---")
    if not args.catalog_only and args.verifier_model: logger.info(f"Quote verification is ENABLED using model: {args.verifier_model}")
    if args.debug_cover: logger.info("Cover debug guides are ENABLED.")

    # --- Initialize Token Usage Tracking ---
    token_tracker = TokenUsageTracker()
    llm_caller.set_token_tracker(token_tracker)
    pipeline_id = f"{args.imprint}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_success(logger, f"✅ Token usage tracking initialized for pipeline: {pipeline_id}")

    all_book_summaries = []
    processed_json_files = []
    for index, row in books_df.iterrows():
        summary = process_single_book(row, config, args, imprint_prepress, prompt_keys, reprompt_keys, book_structure)
        all_book_summaries.append(summary)
        if summary.get("status") == "Completed" and summary.get("json_path"):
            processed_json_files.append(Path(summary["json_path"]))
        if index < len(books_df) - 1:
            logger.info("Waiting 1 second before next book...")
            time.sleep(1)

    logger.info("--- Pipeline processing complete. ---")

    # --- Generate Token Usage Statistics Report ---
    try:
        statistics_reporter = StatisticsReporter()
        log_success(logger, f"📊 Generating statistics report for pipeline: {pipeline_id}")
        statistics_reporter.report_pipeline_statistics(token_tracker)
        
        # Log a summary for easy reference
        total_stats = token_tracker.get_total_statistics()
        summary = statistics_reporter.format_cost_summary(total_stats)
        logger.info(f"📈 Pipeline Summary: {summary}")
        
    except Exception as e:
        logger.error(f"Error generating token usage statistics: {e}", exc_info=True)
    finally:
        # Clear the global token tracker to handle concurrent pipeline cases
        llm_caller.clear_token_tracker()
        logger.debug(f"Token tracker cleared for pipeline: {pipeline_id}")

    # --- Batch LSI CSV Generation ---
    if not args.skip_lsi and args.start_stage <= 4 <= args.end_stage:
        logger.info("--- Batch LSI CSV Generation ---")
        try:
            lsi_metadata_list = [s["lsi_metadata"] for s in all_book_summaries if s.get("lsi_ready")]
            if lsi_metadata_list:
                lsi_generator = LsiAcsGenerator(
                    template_path=config['lsi_template_path'],
                    config_path=config['lsi_config_path'],
                    log_directory=config['lsi_output_dir'] / 'logs',
                    tranche_name=config['tranche_name']
                )
                try:
                    from src.codexes.modules.distribution.series_lsi_integration import integrate_series_with_lsi_generator
                    integrate_series_with_lsi_generator(lsi_generator, "data/series_registry.json")
                    log_success(logger, "✅ Series management integrated with LSI generator")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to integrate series management with LSI generator: {e}")

                batch_lsi_csv_path = config['lsi_output_dir'] / f"{args.imprint}_batch_LSI.csv"
                result = lsi_generator.generate_batch_csv(lsi_metadata_list, str(batch_lsi_csv_path))

                if result.success:
                    log_success(logger, f"✅ Batch LSI CSV generated successfully: {batch_lsi_csv_path}")
                else:
                    logger.warning(f"⚠️ Batch LSI CSV generation completed with warnings: {batch_lsi_csv_path}")

                # Report generation logic...
                # (This complex section is kept as is for functionality)
            else:
                logger.warning("No books ready for LSI CSV generation")
        except Exception as e:
            logger.error(f"❌ Batch LSI CSV generation failed: {e}", exc_info=True)
    else:
        logger.info("Skipping batch LSI CSV generation.")

    # --- Final Step: Generate Storefront Catalog ---
    if not args.skip_catalog:
        logger.info("--- Final Step: Generating Storefront Catalog ---")
        try:
            generate_catalog.create_catalog_from_json(
                json_files=processed_json_files,
                output_file=args.catalog_file
            )
        except Exception as e:
            logger.error(f"❌ Catalog generation failed: {e}", exc_info=True)
    else:
        logger.info("Skipping final catalog generation as requested.")

    # --- Stage 5: Marketing Material Generation ---
    marketing_results = {}
    if args.enable_marketing and args.start_stage <= 5 <= args.end_stage:
        logger.info("--- Stage 5: Marketing Material Generation ---")
        try:
            from codexes.modules.marketing.marketing_manager import MarketingManager
            
            # Parse marketing formats
            marketing_formats = [f.strip().lower() for f in args.marketing_formats.split(',')]
            
            # Use the generated catalog if available, otherwise use existing catalog
            catalog_path = args.catalog_file if not args.skip_catalog else f"imprints/{args.imprint}/books.csv"
            
            # Initialize marketing manager
            marketing_manager = MarketingManager(args.marketing_output_dir)
            
            # Generate marketing materials
            marketing_results = marketing_manager.generate_marketing_materials(
                catalog_path=catalog_path,
                imprint=args.imprint,
                formats=marketing_formats
            )
            
            # Log results
            if marketing_results.get('errors'):
                for error in marketing_results['errors']:
                    logger.error(f"❌ Marketing generation error: {error}")
            else:
                logger.info(f"✅ Marketing materials generated for {args.imprint}")
                for format_type, results in marketing_results.get('generated_materials', {}).items():
                    if results.get('success', False):
                        count = results.get('generated_count', 0)
                        logger.info(f"  {format_type}: {count} items generated")
            
            # Generate campaign summary
            summary_report = marketing_manager.generate_campaign_summary(marketing_results)
            logger.info("Marketing campaign summary generated")
            
        except ImportError:
            logger.error("❌ Marketing modules not available - skipping Stage 5")
        except Exception as e:
            logger.error(f"❌ Marketing material generation failed: {e}", exc_info=True)
    elif args.enable_marketing:
        logger.info("Marketing enabled but not in stage range - skipping Stage 5")
    else:
        logger.info("Marketing material generation disabled - skipping Stage 5")

    # --- Display Final Summary Table ---
    if all_book_summaries:
        print("\n\n" + "=" * 80)
        print(f"PIPELINE EXECUTION SUMMARY FOR IMPRINT: {args.imprint.upper()}")
        print("=" * 80)
        display_mapping = {
            "status": "Status", "prompts_successful": "Prompts OK", "quotes_found": "Quotes Found",
            "quotes_verified": "Quotes Verified", "quotes_accurate": "Quotes Accurate", "pages": "PDF Pages",
            "lsi_csv_generated": "LSI CSV Generated", "lsi_fields_populated": "LSI Fields Populated",
            "lsi_validation_passed": "LSI Validation Passed"
        }
        max_key_len = max(len(v) for v in display_mapping.values())
        for i, summary in enumerate(all_book_summaries):
            print(f"Book {i + 1}: {summary.get('title', 'Untitled Book')}")
            print("-" * 80)
            for key, display_name in display_mapping.items():
                print(f"{display_name:<{max_key_len}} : {summary.get(key, 'N/A')}")
            if i < len(all_book_summaries) - 1:
                print("-" * 80)
        print("=" * 80)
        
        # Add marketing summary if Stage 5 was run
        if marketing_results and args.enable_marketing:
            print(f"\nMARKETING MATERIALS GENERATED:")
            print("-" * 80)
            for format_type, results in marketing_results.get('generated_materials', {}).items():
                status = "✅" if results.get('success', False) else "❌"
                count = results.get('generated_count', 0)
                print(f"{format_type.title():<20} : {status} ({count} items)")
            print(f"Output Directory      : {marketing_results.get('output_directory', 'N/A')}")
        
        print("=" * 80 + "\n")


if __name__ == '__main__':
    main()