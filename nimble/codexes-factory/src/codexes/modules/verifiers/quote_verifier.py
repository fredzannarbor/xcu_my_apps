import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

from codexes.core import llm_caller, prompt_manager
from codexes.modules.distribution.enhanced_error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

# Initialize enhanced error handler
error_handler = EnhancedErrorHandler(logger)


def verify_quotes_in_file(
        json_path: Path,
        verifier_model: str,
        prompt_template_file: Path,
        per_model_params: Dict[str, Any]
) -> Optional[Dict[str, int]]:
    """
    Verifies quotes in a JSON file and returns a dictionary of verification stats.
    Processes quotes in batches for improved reliability.
    """
    logger.info(f"--- Starting Quote Verification for: {json_path.name} ---")
    logger.info(f"Using verifier model: {verifier_model}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not read or parse JSON file at {json_path}: {e}")
        return None

    original_quotes = data.get("quotes")
    if not original_quotes or not isinstance(original_quotes, list):
        logger.warning(f"No 'quotes' list found in {json_path.name}. Skipping verification.")
        return {"total_verified": 0, "accurate": 0}

    # --- Batch Processing Logic ---
    batch_size = 10  # Process 10 quotes at a time for reliability
    all_verified_quotes = []
    total_quotes = len(original_quotes)
    
    logger.info(f"Starting verification for {total_quotes} quotes in batches of {batch_size}.")

    for i in range(0, total_quotes, batch_size):
        batch_quotes = original_quotes[i:i + batch_size]
        logger.info(f"Processing batch {(i // batch_size) + 1}/{(total_quotes + batch_size - 1) // batch_size}...")

        substitutions = {"quotes_to_verify": json.dumps(batch_quotes, indent=2)}
        
        prepared_prompt = prompt_manager.load_and_prepare_prompts(
            prompt_file_path=str(prompt_template_file),
            prompt_keys=["quote_verification_prompt"],
            substitutions=substitutions
        )

        if not prepared_prompt:
            logger.error("Could not load 'quote_verification_prompt' for batch. Skipping batch.")
            # Add error placeholders for this batch to maintain list integrity
            for quote in batch_quotes:
                all_verified_quotes.append({
                    "is_accurate": False,
                    "verified_quote": quote.get("quote"),
                    "verified_source": quote.get("source"),
                    "verified_author": quote.get("author"),
                    "verification_notes": "Critical error: Failed to prepare verification prompt for this batch."
                })
            continue

        responses = llm_caller.get_responses_from_multiple_models(
            prompt_configs=prepared_prompt, models=[verifier_model],
            response_format_type="json_object", per_model_params=per_model_params
        )
        
        # The response is for a single batch
        verification_result = responses.get(verifier_model, [{}])[0].get('parsed_content', {})
        batch_verified_quotes = verification_result.get('verified_quotes')

        if not batch_verified_quotes or not isinstance(batch_verified_quotes, list) or len(batch_verified_quotes) != len(batch_quotes):
            logger.error(f"Verifier model did not return a valid list for batch. Response: {verification_result}")
            # Add error placeholders for this batch
            for quote in batch_quotes:
                all_verified_quotes.append({
                    "is_accurate": False,
                    "verified_quote": quote.get("quote"),
                    "verified_source": quote.get("source"),
                    "verified_author": quote.get("author"),
                    "verification_notes": "LLM failed to return valid verification data for this batch."
                })
        else:
            all_verified_quotes.extend(batch_verified_quotes)
            logger.info(f"✅ Successfully verified batch. Total verified so far: {len(all_verified_quotes)}")

    # --- Assemble and Process Final Results ---
    verified_quotes = all_verified_quotes

    if not verified_quotes or not isinstance(verified_quotes, list) or len(verified_quotes) != len(original_quotes):
        logger.error(f"Final count of verified quotes ({len(verified_quotes)}) does not match original count ({len(original_quotes)}). Aborting verification.")
        # Use enhanced error handler for recovery
        context = {
            'original_quotes': original_quotes,
            'verifier_model': verifier_model,
            'json_path': str(json_path)
        }
        
        recovered_result = error_handler.handle_quote_verification_error(
            {"error": "Mismatched quote count after batching"}, context
        )
        
        if recovered_result and recovered_result.get('verified_quotes') is not None:
            logger.info(f"✅ Quote verification recovered using enhanced error handler")
            verified_quotes = recovered_result.get('verified_quotes')
        else:
            logger.error(f"❌ Quote verification recovery failed, aborting")
            return None

    accurate_count = 0
    for i, original_quote in enumerate(original_quotes):
        verification_data = verified_quotes[i]
        is_accurate = verification_data.get('is_accurate', False)
        original_quote['verification'] = {
            'status': 'accurate' if is_accurate else 'corrected',
            'notes': verification_data.get('verification_notes', 'N/A')
        }
        if not is_accurate:
            original_quote['quote'] = verification_data.get('verified_quote', original_quote['quote'])
            original_quote['source'] = verification_data.get('verified_source', original_quote['source'])
            original_quote['author'] = verification_data.get('verified_author', original_quote['author'])
        else:
            accurate_count += 1

    # The detailed summary is returned to the caller, so we no longer log it here.
    data['quotes'] = original_quotes

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # The log message now confirms the file write and provides the full path.
        logger.info(f"✅ Verification data written to file: {json_path}")

        # write the verification data to file as a markdown document and add to back matter
        md_path = json_path.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Quote Verification Report\n\n")
            f.write(f"**File:** `{json_path.name}`\n")
            f.write(f"**Total Quotes Verified:** {len(original_quotes)}\n")
            f.write(f"**Accurate Quotes:** {accurate_count}\n\n")
            for i, quote_data in enumerate(original_quotes):
                f.write(f"## Quote {i+1}\n")
                f.write(f"**Status:** {quote_data['verification']['status'].capitalize()}\n")
                f.write(f"**Quote:** {quote_data['quote']}\n")
                f.write(f"**Source:** {quote_data['source']}\n")
                f.write(f"**Author:** {quote_data['author']}\n")
                f.write(f"**Notes:** {quote_data['verification']['notes']}\n\n")

        return {"total_verified": len(original_quotes), "accurate": accurate_count}
    except IOError as e:
        logger.error(f"Failed to write updated JSON to {json_path}: {e}")
        return None
