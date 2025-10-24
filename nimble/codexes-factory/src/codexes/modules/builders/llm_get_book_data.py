# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/builders/llm_get_book_data.py
import logging
import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from dotenv import load_dotenv

load_dotenv()

from codexes.core.llm_integration import get_responses_from_multiple_models
from codexes.core import prompt_manager
from codexes.core import file_handler
from codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)


def generate_back_cover_text(
    book_data: Dict[str, Any], 
    quotes: List[Dict], 
    prompt_template_file: str,
    model_name: str,
    per_model_params: Dict
) -> str:
    """
    Generate final back cover text using LLM with full book context.
    
    Args:
        book_data: Book metadata dictionary
        quotes: List of generated quotes for context
        prompt_template_file: Path to prompt template file
        model_name: LLM model to use
        per_model_params: Model-specific parameters
        
    Returns:
        Clean, final back cover text ready for cover placement
    """
    title = book_data.get("title", "Untitled")
    author = book_data.get("author", "AI Lab for Book-Lovers")
    stream = book_data.get("stream", "General")
    description = book_data.get('description', 'No description provided')
    imprint = book_data.get("imprint", "xynapse traces")
    quotes_per_book = len(quotes) if quotes else book_data.get("quotes_per_book", 90)
    
    # Build context with quotes for richer generation
    quotes_text = ""
    if quotes:
        quotes_text = "\n\nSample quotations from this book:\n"
        # Include first 3 quotes as examples for context
        for i, quote in enumerate(quotes[:3], 1):
            q_text = quote.get("quote", "")
            q_author = quote.get("author", "Unknown")
            quotes_text += f"{i}. \"{q_text}\" - {q_author}\n"
    
    book_content = f"Title: {title}\nAuthor: {author}\nImprint: {imprint}\nStream: {stream}\n\nDescription: {description}{quotes_text}"
    
    substitutions = {
        "book_content": book_content,
        "title": title,
        "author": author,
        "stream": stream,
        "imprint": imprint,
        "description": description,
        "quotes_per_book": quotes_per_book
    }
    
    try:
        formatted_prompts = prompt_manager.load_and_prepare_prompts(
            prompt_file_path=prompt_template_file,
            prompt_keys=["back_cover_text"],
            substitutions=substitutions
        )
        
        if not formatted_prompts:
            logger.warning(f"Could not load back_cover_text prompt for book '{title}'. Using fallback.")
            return generate_fallback_back_cover_text(book_data, quotes_per_book)
        
        responses = get_responses_from_multiple_models(
            prompt_configs=formatted_prompts,
            models=[model_name],
            response_format_type="json_object",
            per_model_params=per_model_params
        )
        
        # Extract back cover text from response
        for model_name, model_responses in responses.items():
            for response_item in model_responses:
                if response_item.get('prompt_key') == 'back_cover_text':
                    parsed_content = response_item.get('parsed_content')
                    if parsed_content and isinstance(parsed_content, dict):
                        back_cover_text = parsed_content.get('back_cover_text', '')
                        if back_cover_text and len(back_cover_text.strip()) > 0:
                            logger.info(f"✅ Generated back cover text for '{title}' ({len(back_cover_text)} chars)")
                            return back_cover_text.strip()
        
        logger.warning(f"LLM did not return valid back cover text for '{title}'. Using fallback.")
        return generate_fallback_back_cover_text(book_data, quotes_per_book)
        
    except Exception as e:
        logger.error(f"Error generating back cover text for '{title}': {e}")
        return generate_fallback_back_cover_text(book_data, quotes_per_book)


def generate_fallback_back_cover_text(book_data: Dict[str, Any], quotes_per_book: int) -> str:
    """
    Generate fallback back cover text using book metadata when LLM generation fails.
    
    Args:
        book_data: Book metadata dictionary
        quotes_per_book: Number of quotes in the book
        
    Returns:
        Simple fallback back cover text
    """
    title = book_data.get("title", "Untitled")
    stream = book_data.get("stream", "General")
    description = book_data.get('description', 'A collection of thought-provoking content')
    
    # Create simple but professional fallback text
    fallback_text = f"Explore {stream.lower()} through {quotes_per_book} carefully selected quotations. "
    fallback_text += f"{description[:100]}{'...' if len(description) > 100 else ''} "
    fallback_text += f"This collection includes a comprehensive bibliography and verification log for scholarly reference."
    
    logger.info(f"Generated fallback back cover text for '{title}'")
    return fallback_text


def reprompt_and_update(
    book_data: Dict[str, Any],
    prompt_key: str,
    prompt_template_file: str,
    model_name: str,
    per_model_params: Dict,
    imprint_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Reprompts with a specific key and returns the updated data.
    """
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')

    # Check if body_source (PDF file) is provided - extract text from it
    body_source = book_data.get("body_source", "")
    if body_source:
        body_source_path = os.path.expanduser(body_source)
        if os.path.exists(body_source_path):
            logger.info(f"📄 Processing body_source PDF for reprompt: {body_source_path}")
            try:
                pdf_text = file_handler.load_document(body_source_path)

                # Check if PDF is scanned (no extractable text)
                if not pdf_text or len(pdf_text.strip()) < 100:
                    logger.info(f"📸 PDF appears to be scanned - checking for OCR cache...")

                    # Check for cached OCR version
                    ocr_cache_dir = Path("output/ocr_cache")
                    pdf_filename = Path(body_source_path).stem
                    ocr_output = ocr_cache_dir / f"{pdf_filename}_ocr.pdf"

                    if ocr_output.exists():
                        logger.info(f"✅ Using cached OCR'd PDF for reprompt: {ocr_output}")
                        pdf_text = file_handler.load_document(str(ocr_output))
                    else:
                        logger.warning(f"⚠️  No OCR cache found, falling back to description")
                        logger.info(f"💡 Tip: Run full pipeline (stage 1) first to generate OCR cache")
                        book_content = f"Title: {title}\n\nDescription: {description}"
                        pdf_text = None

                # If we have text
                if pdf_text and len(pdf_text.strip()) > 100:
                    # No truncation - modern LLMs have large context windows
                    book_content = f"Title: {title}\n\nDocument Content:\n{pdf_text}"
                    logger.info(f"✅ Using PDF content for reprompt ({len(pdf_text)} chars)")
                elif 'book_content' not in locals():
                    logger.warning(f"⚠️  No text extracted, falling back to description")
                    book_content = f"Title: {title}\n\nDescription: {description}"

            except Exception as e:
                logger.error(f"❌ Failed to process PDF: {e}")
                book_content = f"Title: {title}\n\nDescription: {description}"
        else:
            logger.warning(f"⚠️  body_source file not found: {body_source_path}, using description")
            book_content = f"Title: {title}\n\nDescription: {description}"
    else:
        # Original logic for quote-based books
        quotes = book_data.get("quotes", [])
        quotes_text = ""
        if quotes:
            quotes_text = "\n\nQuotations in this book:\n"
            for i, quote in enumerate(quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"

        book_content = f"Title: {title}\n\nDescription: {description}{quotes_text}"

    # Extract persona data from imprint config
    persona_name = "Unknown Publisher"
    persona_bio_summary = "Publisher"
    persona_location = "Earth"
    imprint_name = "Unknown Imprint"

    if imprint_config:
        persona = imprint_config.get("persona", {})
        if persona:
            persona_name = persona.get("name", "Unknown Publisher")
            # Get bio and create a short summary (first sentence or ~100 chars)
            full_bio = persona.get("bio", "Publisher")
            # Extract first sentence as summary
            bio_parts = full_bio.split('. ')
            persona_bio_summary = bio_parts[0] + '.' if bio_parts else full_bio[:100]
            # Get location from persona config
            persona_location = persona.get("location", "Virtual Editorial Office")
        imprint_name = imprint_config.get("name", "Unknown Imprint")
        logger.info(f"✅ Persona loaded in reprompt: {persona_name} from {imprint_name}")
    else:
        logger.warning(f"⚠️ No imprint_config provided to reprompt_and_update, using defaults")

    substitutions = {
        "book_content": book_content,
        "title": title,
        "topic": title,
        "stream": book_data.get("stream", "General"),
        "description": description,
        "quotes_per_book": len(quotes),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", ""),
        "persona_name": persona_name,
        "persona_bio_summary": persona_bio_summary,
        "persona_location": persona_location,
        "imprint": imprint_name
    }

    formatted_prompts = prompt_manager.load_and_prepare_prompts(
        prompt_file_path=prompt_template_file,
        prompt_keys=[prompt_key],
        substitutions=substitutions
    )

    if not formatted_prompts:
        logger.error(f"Could not load or prepare the prompt for key '{prompt_key}' for book '{title}'.")
        return None

    responses = get_responses_from_multiple_models(
        prompt_configs=formatted_prompts, models=[model_name],
        response_format_type="json_object", per_model_params=per_model_params
    )

    for model_name, model_responses in responses.items():
        for response_item in model_responses:
            if response_item.get('prompt_key') == prompt_key:
                return response_item.get('parsed_content')

    return None


def process_book(
        book_data: Dict[str, Any],
        prompt_template_file: str,
        model_name: str,
        per_model_params: Dict,
        raw_output_dir: Path,
        safe_basename: str,
        prompt_keys: List[str],
        catalog_only: bool = False,
        build_dir: Optional[Path] = None,
        save_responses: bool = False,
        reporting_system: Optional[AccurateReportingSystem] = None,
        enable_metadata_discovery: bool = False,
        imprint_config: Optional[Dict[str, Any]] = None
) -> tuple[Optional[Dict[str, Any]], Dict[str, int]]:
    """
    Processes a single book entry, generates all required data, and returns stats.
    Saves raw LLM responses to the specified directory.
    """
    title = book_data.get("title", f"Title_TBD_{time.time()}")
    stream = book_data.get("stream", "Stream_TBD")
    description = book_data.get('description', 'Expand topic logically into related concepts.')
    logging.info(f"Processing book: '{title}' in stream: '{stream}'")
    
    # Initialize reporting system if not provided
    if reporting_system is None:
        reporting_system = AccurateReportingSystem()
    
    # Track processing start time
    processing_start_time = time.time()

    if catalog_only:
        logger.info("Running in catalog-only mode. Using a reduced set of prompts.")
        prompt_keys = [k for k in prompt_keys if "storefront" in k or "bibliographic" in k or "back_cover" in k]
    
    # Handle metadata discovery setting
    if enable_metadata_discovery:
        # Ensure gemini_get_basic_info_from_public_domain is in the list for metadata discovery
        if "gemini_get_basic_info" in prompt_keys:
            prompt_keys = [k if k != "gemini_get_basic_info" else "gemini_get_basic_info_from_public_domain" for k in prompt_keys]
            logger.info("✅ Metadata discovery enabled: swapped to gemini_get_basic_info_from_public_domain prompt")
        elif "gemini_get_basic_info_from_public_domain" in prompt_keys:
            logger.info("✅ Metadata discovery enabled: using gemini_get_basic_info_from_public_domain prompt")
        else:
            # Neither exists, try to add the metadata discovery version if it exists in the prompt file
            logger.info("✅ Metadata discovery enabled: will attempt to load gemini_get_basic_info_from_public_domain if available")
    else:
        # Ensure we're using the standard prompt that doesn't discover metadata
        if "gemini_get_basic_info_from_public_domain" in prompt_keys:
            prompt_keys = [k if k != "gemini_get_basic_info_from_public_domain" else "gemini_get_basic_info" for k in prompt_keys]
            logger.info("✅ Metadata discovery disabled: swapped to standard gemini_get_basic_info prompt")
        elif "gemini_get_basic_info" in prompt_keys:
            logger.info("✅ Metadata discovery disabled: using standard gemini_get_basic_info prompt")

    # Check if body_source (PDF file) is provided - extract text from it
    body_source = book_data.get("body_source", "")
    if body_source:
        # Expand ~ to home directory
        body_source_path = os.path.expanduser(body_source)
        if os.path.exists(body_source_path):
            logger.info(f"📄 Processing body_source PDF: {body_source_path}")

            # Try to extract text
            try:
                pdf_text = file_handler.load_document(body_source_path)

                # Check if PDF is scanned (no extractable text)
                if not pdf_text or len(pdf_text.strip()) < 100:
                    logger.info(f"📸 PDF appears to be scanned (no extractable text) - running OCR...")

                    # Create OCR cache directory
                    ocr_cache_dir = Path(raw_output_dir) / "ocr_cache" if raw_output_dir else Path("output/ocr_cache")
                    ocr_cache_dir.mkdir(parents=True, exist_ok=True)

                    # Generate OCR output path
                    pdf_filename = Path(body_source_path).stem
                    ocr_output = ocr_cache_dir / f"{pdf_filename}_ocr.pdf"

                    # Check if OCR version already exists
                    if ocr_output.exists():
                        logger.info(f"✅ Using cached OCR'd PDF: {ocr_output}")
                    else:
                        logger.info(f"🔄 Running ocrmypdf (this may take a few minutes)...")
                        try:
                            # Run ocrmypdf with optimizations for speed
                            result = subprocess.run(
                                ['ocrmypdf',
                                 '--skip-text',  # Skip pages that already have text
                                 '--optimize', '0',  # Faster, no compression
                                 '--output-type', 'pdf',
                                 body_source_path,
                                 str(ocr_output)],
                                capture_output=True,
                                text=True,
                                timeout=600  # 10 minute timeout
                            )

                            if result.returncode == 0:
                                logger.info(f"✅ OCR completed successfully: {ocr_output}")
                            else:
                                logger.error(f"❌ OCR failed: {result.stderr}")
                                logger.warning(f"⚠️  Falling back to description due to OCR failure")
                                book_content = f"Title: {title}\n\nDescription: {description}"
                                ocr_output = None
                        except subprocess.TimeoutExpired:
                            logger.error(f"❌ OCR timed out after 10 minutes")
                            book_content = f"Title: {title}\n\nDescription: {description}"
                            ocr_output = None
                        except FileNotFoundError:
                            logger.error(f"❌ ocrmypdf not found. Install with: brew install ocrmypdf (macOS) or pip install ocrmypdf")
                            logger.warning(f"⚠️  Falling back to description")
                            book_content = f"Title: {title}\n\nDescription: {description}"
                            ocr_output = None

                    # Extract text from OCR'd PDF
                    if ocr_output and ocr_output.exists():
                        pdf_text = file_handler.load_document(str(ocr_output))
                        if pdf_text and len(pdf_text.strip()) > 100:
                            logger.info(f"✅ Successfully extracted {len(pdf_text)} chars from OCR'd PDF")
                        else:
                            logger.warning(f"⚠️  OCR'd PDF still has no text, using description")
                            book_content = f"Title: {title}\n\nDescription: {description}"
                            pdf_text = None

                # If we have text (either from original or OCR'd PDF)
                if pdf_text and len(pdf_text.strip()) > 100:
                    # No truncation - modern LLMs have large context windows
                    book_content = f"Title: {title}\n\nDocument Content:\n{pdf_text}"
                    logger.info(f"✅ Using {len(book_content)} chars of PDF content as book_content")
                elif 'book_content' not in locals():
                    logger.warning(f"⚠️  No text extracted, falling back to description")
                    book_content = f"Title: {title}\n\nDescription: {description}"

            except Exception as e:
                logger.error(f"❌ Failed to process PDF: {e}")
                book_content = f"Title: {title}\n\nDescription: {description}"
        else:
            logger.warning(f"⚠️  body_source file not found: {body_source_path}, using description")
            book_content = f"Title: {title}\n\nDescription: {description}"
    else:
        # Original logic for books without body_source (quote-based books)
        quotes = book_data.get("quotes", [])
        quotes_text = ""
        if quotes:
            quotes_text = "\n\nQuotations in this book:\n"
            for i, quote in enumerate(quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"

        book_content = f"Title: {title}\n\nDescription: {description}{quotes_text}"

    # Extract persona data from imprint config
    persona_name = "Unknown Publisher"
    persona_bio_summary = "Publisher"
    persona_location = "Earth"
    imprint_name = "Unknown Imprint"

    if imprint_config:
        persona = imprint_config.get("persona", {})
        if persona:
            persona_name = persona.get("name", "Unknown Publisher")
            # Get bio and create a short summary (first sentence or ~100 chars)
            full_bio = persona.get("bio", "Publisher")
            # Extract first sentence as summary
            bio_parts = full_bio.split('. ')
            persona_bio_summary = bio_parts[0] + '.' if bio_parts else full_bio[:100]
            # Get location from persona config
            persona_location = persona.get("location", "Virtual Editorial Office")
        imprint_name = imprint_config.get("name", "Unknown Imprint")
        logger.info(f"✅ Persona loaded: {persona_name} from {imprint_name}")
    else:
        logger.warning(f"⚠️ No imprint_config provided, using defaults")

    substitutions = {
        "book_content": book_content,
        "topic": title,
        "stream": stream,
        "description": description,
        "quotes_per_book": book_data.get("quotes_per_book", 90),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", ""),
        "persona_name": persona_name,
        "persona_bio_summary": persona_bio_summary,
        "persona_location": persona_location,
        "imprint": imprint_name
    }
    
    formatted_prompts = prompt_manager.load_and_prepare_prompts(
        prompt_file_path=prompt_template_file,
        prompt_keys=prompt_keys,
        substitutions=substitutions
    )

    if not formatted_prompts:
        logging.error(f"Could not load or prepare any prompts for book '{title}'. Skipping.")
        return None, {"prompts_successful": 0, "quotes_found": 0}

    responses = get_responses_from_multiple_models(
        prompt_configs=formatted_prompts, models=[model_name],
        response_format_type="json_object", per_model_params=per_model_params
    )
    
    # Save LLM responses to JSON if requested
    if save_responses and build_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for model_name, model_responses in responses.items():
            for response_item in model_responses:
                prompt_key = response_item.get('prompt_key', 'unknown')
                prompt = response_item.get('prompt', '')
                content = response_item.get('content', {})
                
                # Save response to JSON file
                response_data = {
                    "timestamp": timestamp,
                    "model": model_name,
                    "prompt_key": prompt_key,
                    "prompt": prompt,
                    "response": content
                }
                
                filename = f"{safe_basename}_{prompt_key}_{timestamp}.json"
                response_file = build_dir / filename
                
                with open(response_file, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Saved LLM response for {prompt_key} to {response_file}")

    # Set default values - these will be overridden by LLM if metadata discovery is enabled
    if enable_metadata_discovery:
        # When metadata discovery is enabled, use minimal defaults that can be overridden
        final_book_json = {
            "title": title, "stream": stream, "description": description,
            "schedule_month_year": book_data.get("schedule_month_year", "Unknown"),
            "subtitle": "", "author": "", "publisher": "", "imprint": "", 
            "publication_date": datetime.now().strftime('%Y-%m-%d'),
            "language": "English", "bisac_codes": "", "series_name": "", "series_number": "",
            "keywords": "", "storefront_title_en": title, "storefront_author_en": "",
            "storefront_description_en": description, "storefront_title_ko": "", "storefront_author_ko": "",
            "storefront_description_ko": "", "storefront_publishers_note_en": "", "storefront_publishers_note_ko": "",
            "table_of_contents": "", "quotes": [], "custom_transcription_note": "",
            "mnemonics": "", "mnemonics_tex": "", "bibliography": "", "isbn13": "", "back_cover_text": "", "formatted_prompts": formatted_prompts
        }
        logger.info("✅ Metadata discovery enabled: using minimal defaults that can be overridden by LLM")
    else:
        # When metadata discovery is disabled, use configured values that won't be overridden
        final_book_json = {
            "title": title, "stream": stream, "description": description,
            "schedule_month_year": book_data.get("schedule_month_year", "Unknown"),
            "subtitle": "", "author": "AI Lab for Book-Lovers", "publisher": "Nimble Books LLC",
            "imprint": "xynapse traces", "publication_date": datetime.now().strftime('%Y-%m-%d'),
            "language": "English", "bisac_codes": "", "series_name": "", "series_number": "",
            "keywords": "", "storefront_title_en": title, "storefront_author_en": "AI Lab for Book-Lovers",
            "storefront_description_en": description, "storefront_title_ko": "", "storefront_author_ko": "",
            "storefront_description_ko": "", "storefront_publishers_note_en": "", "storefront_publishers_note_ko": "",
            "table_of_contents": "", "quotes": [], "custom_transcription_note": "",
            "mnemonics": "", "mnemonics_tex": "", "bibliography": "", "isbn13": "", "back_cover_text": "", "formatted_prompts": formatted_prompts
        }
        logger.info("✅ Metadata discovery disabled: using configured publisher/imprint/author values")

    if catalog_only:
        final_book_json['page_count'] = 216
        final_book_json['author'] = "AI Lab for Book-Lovers"
        final_book_json['imprint'] = "xynapse traces"

    successful_prompts = 0
    total_prompts = 0
    final_book_json['responses'] = responses
    
    for model_name, model_responses in responses.items():
        for response_item in model_responses:
            prompt_key = response_item.get('prompt_key', 'unknown_prompt')
            raw_content = response_item.get('raw_content', '')
            parsed_content = response_item.get('parsed_content')
            execution_time = response_item.get('execution_time', 0.0)
            
            total_prompts += 1

            try:
                raw_filename = f"{safe_basename}_{prompt_key}.txt"
                (raw_output_dir / raw_filename).write_text(raw_content, encoding='utf-8')
            except Exception as e:
                logger.error(f"Failed to write raw response for {prompt_key}: {e}")

            # Determine if prompt was successful
            prompt_success = bool(parsed_content and not (isinstance(parsed_content, dict) and 'error' in parsed_content))
            
            # Track prompt execution in reporting system
            reporting_system.track_prompt_execution(
                prompt_name=prompt_key,
                success=prompt_success,
                details={
                    'execution_time': execution_time,
                    'model_name': model_name,
                    'response_length': len(raw_content),
                    'error_message': str(parsed_content.get('error', '')) if isinstance(parsed_content, dict) and 'error' in parsed_content else None
                }
            )

            if not prompt_success:
                logger.warning(f"LLM returned an error or invalid content for prompt '{prompt_key}': {parsed_content}")
                continue

            successful_prompts += 1

            def process_dict(data_dict: Dict):
                if not isinstance(data_dict, dict): return
                for key, value in data_dict.items():
                    if value is not None:
                        # Map document_title to title for metadata discovery
                        if key == 'document_title' and enable_metadata_discovery:
                            final_book_json['title'] = value
                            final_book_json['storefront_title_en'] = value
                            logger.info(f"✅ Updated title from document_title: '{value}'")
                            continue

                        # Protect configured values when metadata discovery is disabled
                        if not enable_metadata_discovery and key in ['author', 'publisher', 'imprint']:
                            logger.debug(f"Metadata discovery disabled: ignoring LLM-provided {key}='{value}'")
                            continue

                        if key in final_book_json and isinstance(final_book_json[key], list) and isinstance(value, list):
                            final_book_json[key].extend(value)
                        elif key in final_book_json:
                            final_book_json[key] = value

            if isinstance(parsed_content, dict):
                process_dict(parsed_content)
            elif isinstance(parsed_content, list):
                for item in parsed_content:
                    process_dict(item)
            else:
                logger.warning(f"Unexpected content type '{type(parsed_content)}' for prompt '{prompt_key}'.")

    # --- Generate Back Cover Text ---
    # Generate clean, final back cover text using LLM with full context
    if not catalog_only or "back_cover" in [k for k in prompt_keys if "back_cover" in k]:
        try:
            generated_back_cover_text = generate_back_cover_text(
                book_data=book_data,
                quotes=final_book_json.get("quotes", []),
                prompt_template_file=prompt_template_file,
                model_name=model_name,
                per_model_params=per_model_params
            )
            final_book_json['back_cover_text'] = generated_back_cover_text
            logger.info(f"✅ Back cover text generated for '{title}'")
        except Exception as e:
            logger.error(f"Failed to generate back cover text for '{title}': {e}")
            final_book_json['back_cover_text'] = generate_fallback_back_cover_text(
                book_data, len(final_book_json.get("quotes", []))
            )

    # --- Final Validation Step ---
    # Validate and correct the publication_date
    try:
        datetime.strptime(str(final_book_json.get('publication_date')), '%Y-%m-%d')
    except (ValueError, TypeError):
        logger.warning(f"Invalid or missing publication_date '{final_book_json.get('publication_date')}'. Replacing with current date.")
        final_book_json['publication_date'] = datetime.now().strftime('%Y-%m-%d')

    # Calculate processing time
    processing_time = time.time() - processing_start_time
    
    # Track quote retrieval statistics
    quotes_retrieved = len(final_book_json.get("quotes", []))
    quotes_requested = book_data.get("quotes_per_book", 90)
    
    reporting_system.track_quote_retrieval(
        book_id=safe_basename,
        quotes_retrieved=quotes_retrieved,
        quotes_requested=quotes_requested,
        retrieval_time=processing_time
    )
    
    # Generate accurate statistics using reporting system
    session_stats = reporting_system.get_session_statistics()
    
    llm_stats = {
        "prompts_successful": successful_prompts,
        "quotes_found": quotes_retrieved,
        "total_prompts": total_prompts,
        "prompt_success_rate": successful_prompts / total_prompts if total_prompts > 0 else 0.0,
        "quote_retrieval_rate": quotes_retrieved / quotes_requested if quotes_requested > 0 else 0.0,
        "processing_time": processing_time,
        "session_stats": session_stats
    }

    return final_book_json, llm_stats