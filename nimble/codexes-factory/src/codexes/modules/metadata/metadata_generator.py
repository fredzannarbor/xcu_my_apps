# src/codexes/modules/metadata/metadata_generator.py

import os
import sys
import logging
import fitz  # PyMuPDF
from typing import Optional, List

# Adjust path to find core modules
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(project_root_dir, 'src'))

from src.codexes.core import file_handler, prompt_manager
from src.codexes.core.llm_integration import get_responses_from_multiple_models
from src.codexes.modules.metadata.metadata_models import CodexMetadata
from src.codexes.modules.distribution.llm_field_completer import LLMFieldCompleter


def _calculate_list_price(page_count: int) -> float:
    """
    Calculates a suggested list price based on the page count.
    This is a placeholder for a more complex pricing model.
    """
    if not isinstance(page_count, int) or page_count <= 0:
        return 9.99  # Default price

    base_price = 7.99
    price = base_price + (page_count * 0.03)
    return round(price, 2)


def generate_metadata_from_prompts(
        file_path: str,
        model_name: str,
        prompt_file_path: str,
        prompt_keys: List[str]
) -> Optional[CodexMetadata]:
    """
    Generates a complete metadata object for a given document file using a list of prompts.

    This function performs a "one-shot" process:
    1. Extracts deterministic data (e.g., page count) from the file.
    2. Calculates other values (e.g., price).
    3. Calls an LLM with a consolidated list of prompts to get all generative data.
    4. Populates and returns a CodexMetadata object.

    Args:
        file_path: The full path to the input document (PDF, DOCX, etc.).
        model_name: The name of the LLM to use.
        prompt_file_path: Path to the JSON file containing the prompts.
        prompt_keys: A list of keys for the prompts to be executed.

    Returns:
        A populated CodexMetadata object, or None if the process fails.
    """
    logging.info(f"Starting metadata generation for: {os.path.basename(file_path)}")

    metadata = CodexMetadata(filepath=file_path)
    metadata.source_file_basename = os.path.basename(file_path)

    # 1. Deterministic and Calculated Metadata
    try:
        if file_path.lower().endswith('.pdf'):
            with fitz.open(file_path) as doc:
                metadata.page_count = len(doc)
                metadata.text_extractableness = any(page.get_text() for page in doc)

        book_content = file_handler.load_document(file_path)
        if not book_content:
            logging.error("Could not extract text content from the document.")
            return None

        metadata.word_count = len(book_content.split())
        metadata.list_price_usd = _calculate_list_price(metadata.page_count)
        logging.info(f"Determined Page Count: {metadata.page_count}, Word Count: {metadata.word_count}")

    except Exception as e:
        logging.error(f"Error during deterministic metadata extraction: {e}", exc_info=True)
        return None

    # 2. Generative Metadata (LLM Call)
    logging.info(f"Preparing LLM call with model: {model_name} for keys: {prompt_keys}")

    prepared_prompts = prompt_manager.load_and_prepare_prompts(
        prompt_file_path=prompt_file_path,
        prompt_keys=prompt_keys,
        book_content=book_content
    )

    if not prepared_prompts:
        logging.critical("Could not prepare any prompts. Check prompt file and keys.")
        return None

    responses = get_responses_from_multiple_models(
        prompt_configs=prepared_prompts,
        models=[model_name],
        response_format_type="json_object"
    )

    # 3. Populate Metadata Object from LLM Responses
    try:
        model_response_list = responses.get(model_name)
        if not model_response_list:
            logging.error(f"No response received from model {model_name}.")
            return None

        metadata.raw_llm_responses = responses  # Store for debugging

        for response_item in model_response_list:
            content = response_item.get('content', {})
            if 'error' not in content:
                metadata.update_from_dict(content)
            else:
                logging.warning(f"LLM returned an error for prompt '{response_item.get('prompt_key')}': {content}")

        # Post-processing and defaults
        if not metadata.contributor_one:
            metadata.contributor_one = metadata.author

        # 4. Enhanced LSI Field Completion
        logging.info("Starting LSI field completion...")
        try:
            field_completer = LLMFieldCompleter()
            metadata = field_completer.complete_missing_fields(
                metadata=metadata,
                model=model_name,
                book_content=book_content
            )
            logging.info("LSI field completion completed successfully.")
        except Exception as e:
            logging.warning(f"LSI field completion failed, continuing with basic metadata: {e}")

        logging.info("Successfully populated metadata object.")
        return metadata

    except (KeyError, IndexError, TypeError) as e:
        logging.error(f"Failed to parse LLM response: {e}", exc_info=True)
        logging.error(f"Raw response data: {responses}")
        return None