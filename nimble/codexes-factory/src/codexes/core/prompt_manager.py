import json
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_and_prepare_prompts(
        prompt_file_path: str,
        prompt_keys: List[str],
        substitutions: Dict[str, Any],
        base_prompt_files: Optional[List[str]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Loads prompts from JSON files with hierarchical override support, filters by keys, and prepares them for the LLM caller.

    This function handles two prompt formats in the source JSON:
    1. A simple "prompt" key with a string value.
    2. A complex "messages" key with a list of role/content dicts.

    It performs placeholder substitution on the content for both formats.

    Prompts are loaded in priority order: base < publisher < imprint < series
    Later files override prompts from earlier files with the same key.

    Args:
        prompt_file_path: The path to the main prompt configuration file.
        prompt_keys: A list of prompt keys to load and prepare.
        substitutions: A dictionary of placeholder keys and their values.
        base_prompt_files: Optional list of base prompt files to load first (in priority order).
                          If None, will attempt to load from prompts/combined_prompts.json

    Returns:
        A list of prepared prompt configurations ready for the LLM caller, or None on error.
    """
    all_prompts = {}

    # Determine base files to load
    files_to_load = []
    if base_prompt_files:
        files_to_load.extend(base_prompt_files)
    else:
        # Default base file - compute path relative to the imprint file's directory
        if prompt_file_path:
            prompt_dir = os.path.dirname(os.path.abspath(prompt_file_path))
            # Go up from imprints/xxx to project root
            project_root = os.path.dirname(os.path.dirname(prompt_dir))
            base_file = os.path.join(project_root, "prompts", "combined_prompts.json")
        else:
            # Fallback to current working directory
            base_file = "prompts/combined_prompts.json"

        if os.path.exists(base_file):
            files_to_load.append(base_file)
        else:
            logger.info(f"Base prompts file not found at: {base_file}")

    # Add the main prompt file (highest priority)
    if prompt_file_path:
        files_to_load.append(prompt_file_path)

    # Load all files in priority order (earlier = lower priority)
    for file_path in files_to_load:
        if not os.path.exists(file_path):
            logger.info(f"Prompt file not found, skipping: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_prompts = json.load(f)
                # Update (override) with prompts from this file
                all_prompts.update(file_prompts)
            logger.info(f"✅ Successfully loaded prompts from: {file_path}")
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Could not load or parse prompt file {file_path}: {e}", exc_info=True)
            continue

    if not all_prompts:
        logging.error("No prompts were loaded from any file")
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

        # Carry over response_format if specified in the prompt
        if "response_format" in prompt_data:
            prompt_config["response_format"] = prompt_data["response_format"]

        prepared_prompts.append({
            "key": key,
            "prompt_config": prompt_config
        })

    if not prepared_prompts:
        logging.warning("No valid prompts were prepared from the provided keys.")
        return None

    logging.info(f"Prepared {len(prepared_prompts)} prompts for processing.")
    return prepared_prompts
