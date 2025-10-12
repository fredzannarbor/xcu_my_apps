import json
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_and_prepare_prompts(
        prompt_file_path: str,
        prompt_keys: List[str],
        substitutions: Dict[str, Any]
) -> Optional[List[Dict[str, Any]]]:
    """
    Loads prompts from JSON files, filters by keys, and prepares them for the LLM caller.

    This function handles two prompt formats in the source JSON:
    1. A simple "prompt" key with a string value.
    2. A complex "messages" key with a list of role/content dicts.

    It performs placeholder substitution on the content for both formats.

    Args:
        prompt_file_path: The path to the main prompt configuration file.
        prompt_keys: A list of prompt keys to load and prepare.
        substitutions: A dictionary of placeholder keys and their values.

    Returns:
        A list of prepared prompt configurations ready for the LLM caller, or None on error.
    """
    if not os.path.exists(prompt_file_path):
        logging.error(f"Prompt file not found: {prompt_file_path}")
        return None

    all_prompts = {}
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            all_prompts.update(json.load(f))
        logger.info(f"✅ Successfully loaded prompts from: {prompt_file_path}")
        # You could add logic here to load from multiple files if needed
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Could not load or parse prompt file {prompt_file_path}: {e}", exc_info=True)
        return None

    prepared_prompts = []
    for key in prompt_keys:
        if key not in all_prompts:
            logging.warning(f"Prompt key '{key}' not found in any loaded prompt files. Skipping.")
            continue

        prompt_data = all_prompts[key].copy()  # Use a copy to avoid modifying the original dict
        prompt_config = {}

        # Handle 'messages' format (preferred)
        if "messages" in prompt_data and isinstance(prompt_data["messages"], list):
            formatted_messages = []
            for message in prompt_data["messages"]:
                content = message.get("content", "")
                try:
                    # Perform substitution
                    formatted_content = content.format(**substitutions)
                    formatted_messages.append({"role": message.get("role", "user"), "content": formatted_content})
                except KeyError as e:
                    logging.warning(f"In prompt '{key}', placeholder {e} was not in substitutions. Using raw content. Available substitutions: {list(substitutions.keys())}")
                    formatted_messages.append({"role": message.get("role", "user"), "content": content})
            prompt_config["messages"] = formatted_messages

        # Handle simple 'prompt' string format
        elif "prompt" in prompt_data:
            content = prompt_data.get("prompt", "")
            try:
                formatted_content = content.format(**substitutions)
            except KeyError as e:
                logging.warning(f"In prompt '{key}', placeholder {e} was not in substitutions. Using raw content.")
                formatted_content = content
            # Wrap the simple prompt in the standard messages structure
            prompt_config["messages"] = [{"role": "user", "content": formatted_content}]

        else:
            logging.warning(f"Prompt key '{key}' has neither 'messages' nor 'prompt' key. Skipping.")
            continue

        # Carry over any other parameters, like 'params' for model-specific settings
        if "params" in prompt_data:
            prompt_config["params"] = prompt_data["params"]

        prepared_prompts.append({
            "key": key,
            "prompt_config": prompt_config
        })

    if not prepared_prompts:
        logging.warning("No valid prompts were prepared from the provided keys.")
        return None

    logging.info(f"Prepared {len(prepared_prompts)} prompts for processing.")
    return prepared_prompts
