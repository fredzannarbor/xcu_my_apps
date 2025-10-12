# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/builders/llm_get_book_data.py
import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from dotenv import load_dotenv

load_dotenv()

from codexes.core.llm_integration import get_responses_from_multiple_models
from codexes.core import prompt_manager
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
    per_model_params: Dict
) -> Optional[Dict[str, Any]]:
    """
    Reprompts with a specific key and returns the updated data.
    """
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')
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

    substitutions = {
        "book_content": book_content,
        "title": title,
        "topic": title,
        "stream": book_data.get("stream", "General"),
        "description": description,
        "quotes_per_book": len(quotes),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", "")
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
        enable_metadata_discovery: bool = False
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
        # Replace gemini_get_basic_info with gemini_get_basic_info_from_public_domain for metadata discovery
        if "gemini_get_basic_info" in prompt_keys:
            prompt_keys = [k if k != "gemini_get_basic_info" else "gemini_get_basic_info_from_public_domain" for k in prompt_keys]
            logger.info("✅ Metadata discovery enabled: using gemini_get_basic_info_from_public_domain prompt")
    else:
        # Ensure we're using the standard prompt that doesn't discover metadata
        if "gemini_get_basic_info_from_public_domain" in prompt_keys:
            prompt_keys = [k if k != "gemini_get_basic_info_from_public_domain" else "gemini_get_basic_info" for k in prompt_keys]
            logger.info("✅ Metadata discovery disabled: using standard gemini_get_basic_info prompt")

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
    
    substitutions = {
        "book_content": book_content,
        "topic": title,
        "stream": stream,
        "description": description,
        "quotes_per_book": book_data.get("quotes_per_book", 90),
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", "")
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