"""
Configuration operations for batch processing.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import time

from .models import (
    BatchOperationResult,
    BatchRevisionResult,
    ConfigDiff,
    ValidationError,
    ValidationSeverity
)
from .config_loader import BatchConfigLoader
from .validation import BatchValidator
from .backup import BackupManager

# Import LLM caller
try:
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt

logger = logging.getLogger(__name__)


def complete_and_validate_configs(
    source_paths: List[Path],
    selected_configs: Optional[List[Path]] = None,
    template_path: Optional[Path] = None,
    llm_model: str = "anthropic/claude-sonnet-4-5-20250929",
    auto_fix: bool = True,
    create_backup: bool = True,
    dry_run: bool = False
) -> BatchOperationResult:
    """
    Complete missing fields and validate imprint configs.

    Process:
    1. Load all configs from selected paths
    2. Identify missing/placeholder fields
    3. Use LLM to generate missing content
    4. Validate against schema
    5. Save updated configs (if not dry_run)

    Args:
        source_paths: List of paths to search for configs
        selected_configs: Specific config files to process (None = all)
        template_path: Path to template schema file
        llm_model: LLM model to use for completion
        auto_fix: Whether to automatically fix issues
        create_backup: Whether to create backups before modifying
        dry_run: If True, don't save changes

    Returns:
        BatchOperationResult with processing details
    """
    start_time = time.time()
    result = BatchOperationResult(operation_type="complete_and_validate")

    # Initialize utilities
    loader = BatchConfigLoader()
    backup_manager = BackupManager()

    # Set template path if not provided
    if template_path is None:
        template_path = Path("configs/imprints/imprint_template.json")

    validator = BatchValidator(template_path)

    try:
        # Load configs
        if selected_configs:
            for config_path in selected_configs:
                loader.load_config(config_path)
        else:
            loader.load_configs_from_paths(source_paths)

        configs = loader.get_all_configs()
        result.configs_processed = len(configs)

        if loader.has_errors():
            for name, error in loader.get_errors().items():
                result.add_error(ValidationError(
                    field="loading",
                    message=error,
                    severity=ValidationSeverity.ERROR,
                    config_name=name
                ))

        # Create backup if requested
        if create_backup and not dry_run:
            config_files = selected_configs if selected_configs else []
            if not config_files:
                # Get all config files from paths
                for path in source_paths:
                    if path.is_dir():
                        config_files.extend([
                            f for f in path.glob("*.json")
                            if "template" not in f.name.lower()
                        ])

            backup_path = backup_manager.create_backup(
                config_files,
                "complete_and_validate"
            )
            result.backup_path = backup_path

        # Process each config
        for config_name, config in configs.items():
            logger.info(f"Processing config: {config_name}")

            try:
                # Validate config
                validation_errors = validator.validate_config(
                    config,
                    config_name,
                    strict=False
                )

                # Add validation errors to result
                for error in validation_errors:
                    result.add_error(error)

                # Complete missing fields if auto_fix is enabled
                if auto_fix:
                    updated_config, was_updated = complete_config_fields(
                        config,
                        config_name,
                        validator.template_schema,
                        llm_model
                    )

                    if was_updated:
                        result.configs_fixed += 1
                        result.updated_configs[config_name] = updated_config

                        # Save updated config if not dry_run
                        if not dry_run:
                            # Find original config path
                            config_path = _find_config_path(config_name, source_paths)
                            if config_path:
                                loader.save_config(
                                    config_name,
                                    updated_config,
                                    config_path
                                )
                                logger.info(f"Saved updated config: {config_name}")
                    else:
                        logger.info(f"No updates needed for: {config_name}")

            except Exception as e:
                logger.error(f"Failed to process config {config_name}: {e}")
                result.configs_failed += 1
                result.add_error(ValidationError(
                    field="processing",
                    message=str(e),
                    severity=ValidationSeverity.ERROR,
                    config_name=config_name
                ))

    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        result.add_error(ValidationError(
            field="operation",
            message=f"Operation failed: {e}",
            severity=ValidationSeverity.ERROR
        ))

    finally:
        result.duration_seconds = time.time() - start_time

    return result


def complete_config_fields(
    config: Dict[str, Any],
    config_name: str,
    template: Optional[Dict[str, Any]],
    llm_model: str
) -> tuple[Dict[str, Any], bool]:
    """
    Complete missing or placeholder fields in a config using LLM.

    Args:
        config: Configuration to complete
        config_name: Name of the configuration
        template: Template schema to use
        llm_model: LLM model to use

    Returns:
        Tuple of (updated_config, was_updated)
    """
    # Find placeholder fields
    loader = BatchConfigLoader()
    placeholder_fields = loader.get_placeholder_fields(config)

    if not placeholder_fields:
        logger.info(f"No placeholder fields found in {config_name}")
        return config, False

    logger.info(f"Found {len(placeholder_fields)} placeholder fields in {config_name}")

    # Create prompt for LLM
    prompt = _create_completion_prompt(config, placeholder_fields, template)

    # Call LLM
    try:
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at completing imprint configuration files. You provide realistic, coherent values that fit the context of the existing configuration."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.7,
                "max_tokens": 4096
            }
        }

        response = call_model_with_prompt(
            model_name=llm_model,
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name=f"complete_config_{config_name}"
        )

        if response and "parsed_content" in response:
            completed_fields = response["parsed_content"]

            if isinstance(completed_fields, dict) and "error" not in completed_fields:
                # Merge completed fields into config
                updated_config = _merge_completed_fields(
                    config.copy(),
                    completed_fields
                )

                logger.info(f"Successfully completed fields for {config_name}")
                return updated_config, True
            else:
                logger.warning(f"LLM returned error for {config_name}: {completed_fields}")
                return config, False
        else:
            logger.warning(f"No valid response from LLM for {config_name}")
            return config, False

    except Exception as e:
        logger.error(f"Failed to complete fields for {config_name}: {e}")
        return config, False


def _create_completion_prompt(
    config: Dict[str, Any],
    placeholder_fields: List[str],
    template: Optional[Dict[str, Any]]
) -> str:
    """Create a prompt for completing config fields."""
    existing_context = {
        "imprint": config.get("imprint", ""),
        "publisher": config.get("publisher", ""),
        "charter": config.get("wizard_configuration", {}).get("charter", ""),
        "genres": config.get("wizard_configuration", {}).get("genres", []),
        "publishing_focus": config.get("publishing_focus", {})
    }

    prompt = f"""Complete the missing fields in this imprint configuration.

Existing Configuration Context:
{json.dumps(existing_context, indent=2)}

Fields needing completion:
{json.dumps(placeholder_fields, indent=2)}

Please provide realistic, coherent values for the placeholder fields. Base your completions on the existing context.

Return ONLY a JSON object with the completed values, using the same structure as the placeholder fields.
For nested fields (e.g., "publisher_persona.persona_name"), include the full nested structure.

Example format:
{{
  "branding": {{
    "tagline": "Your completed tagline here"
  }},
  "publisher_persona": {{
    "persona_name": "Completed name"
  }}
}}
"""

    return prompt


def _merge_completed_fields(
    config: Dict[str, Any],
    completed_fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge completed fields into the original config.

    Args:
        config: Original configuration
        completed_fields: Completed field values

    Returns:
        Updated configuration
    """
    def merge_nested(target: Dict[str, Any], source: Dict[str, Any]):
        """Recursively merge source into target."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                merge_nested(target[key], value)
            else:
                target[key] = value

    updated = config.copy()
    merge_nested(updated, completed_fields)
    return updated


def _find_config_path(config_name: str, source_paths: List[Path]) -> Optional[Path]:
    """Find the file path for a config by name."""
    for path in source_paths:
        if path.is_dir():
            config_file = path / f"{config_name}.json"
            if config_file.exists():
                return config_file
        elif path.is_file() and path.stem == config_name:
            return path

    return None


def revise_configs_batch(
    source_paths: List[Path],
    selected_configs: Optional[List[Path]] = None,
    revision_prompt: str = "",
    llm_model: str = "anthropic/claude-sonnet-4-5-20250929",
    fields_to_modify: Optional[List[str]] = None,
    preview_only: bool = True,
    create_backup: bool = True
) -> BatchRevisionResult:
    """
    Revise imprint configs based on natural language prompt.

    Process:
    1. Load all selected configs
    2. For each config, use LLM to apply revision
    3. Generate diff preview
    4. Apply changes if not preview_only

    Args:
        source_paths: List of paths to search for configs
        selected_configs: Specific config files to process
        revision_prompt: Natural language instruction for revision
        llm_model: LLM model to use
        fields_to_modify: Optional list to limit scope of changes
        preview_only: If True, only show changes without applying
        create_backup: Whether to create backups before modifying

    Returns:
        BatchRevisionResult with revision details
    """
    start_time = time.time()
    result = BatchRevisionResult(revision_prompt=revision_prompt)

    # Initialize utilities
    loader = BatchConfigLoader()
    backup_manager = BackupManager()

    try:
        # Load configs
        if selected_configs:
            for config_path in selected_configs:
                loader.load_config(config_path)
        else:
            loader.load_configs_from_paths(source_paths)

        configs = loader.get_all_configs()

        # Create backup if requested and not preview
        if create_backup and not preview_only:
            config_files = selected_configs if selected_configs else []
            if not config_files:
                for path in source_paths:
                    if path.is_dir():
                        config_files.extend([
                            f for f in path.glob("*.json")
                            if "template" not in f.name.lower()
                        ])

            backup_path = backup_manager.create_backup(
                config_files,
                "batch_revision"
            )
            result.backup_path = backup_path

        # Process each config
        for config_name, config in configs.items():
            logger.info(f"Revising config: {config_name}")

            try:
                # Apply revision using LLM
                revised_config = revise_config_with_llm(
                    config,
                    config_name,
                    revision_prompt,
                    llm_model,
                    fields_to_modify
                )

                if revised_config:
                    # Generate diffs
                    diffs = generate_config_diff(
                        config,
                        revised_config,
                        config_name
                    )

                    for diff in diffs:
                        result.add_change(config_name, diff)

                    # Validate revised config
                    validator = BatchValidator()
                    validation_errors = validator.validate_config(
                        revised_config,
                        config_name,
                        strict=False
                    )

                    result.validation_status[config_name] = len([
                        e for e in validation_errors
                        if e.severity == ValidationSeverity.ERROR
                    ]) == 0

                    # Save if not preview_only
                    if not preview_only:
                        config_path = _find_config_path(config_name, source_paths)
                        if config_path:
                            loader.save_config(
                                config_name,
                                revised_config,
                                config_path
                            )
                            result.configs_modified += 1
                            logger.info(f"Saved revised config: {config_name}")
                else:
                    logger.warning(f"Failed to revise config: {config_name}")
                    result.configs_failed += 1

            except Exception as e:
                logger.error(f"Failed to revise config {config_name}: {e}")
                result.configs_failed += 1

    except Exception as e:
        logger.error(f"Batch revision failed: {e}")

    finally:
        result.duration_seconds = time.time() - start_time

    return result


def revise_config_with_llm(
    config: Dict[str, Any],
    config_name: str,
    revision_prompt: str,
    llm_model: str,
    fields_to_modify: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Revise a config using LLM based on natural language prompt.

    Args:
        config: Configuration to revise
        config_name: Name of the configuration
        revision_prompt: Natural language revision instruction
        llm_model: LLM model to use
        fields_to_modify: Optional list of fields to limit changes to

    Returns:
        Revised configuration or None if failed
    """
    # Create prompt
    prompt = f"""Revise the following imprint configuration based on this instruction:

Instruction: {revision_prompt}

Current Configuration:
{json.dumps(config, indent=2)}

{"Only modify these fields: " + ", ".join(fields_to_modify) if fields_to_modify else ""}

Please return the COMPLETE revised configuration as JSON, with the requested changes applied.
Maintain all existing fields and structure.
"""

    try:
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at revising imprint configurations. You make precise, contextually appropriate changes while preserving the overall structure."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.5,
                "max_tokens": 8192
            }
        }

        response = call_model_with_prompt(
            model_name=llm_model,
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name=f"revise_config_{config_name}"
        )

        if response and "parsed_content" in response:
            revised_config = response["parsed_content"]

            if isinstance(revised_config, dict) and "error" not in revised_config:
                logger.info(f"Successfully revised config: {config_name}")
                return revised_config
            else:
                logger.warning(f"LLM returned error: {revised_config}")
                return None
        else:
            logger.warning(f"No valid response from LLM")
            return None

    except Exception as e:
        logger.error(f"Failed to revise config with LLM: {e}")
        return None


def generate_config_diff(
    old_config: Dict[str, Any],
    new_config: Dict[str, Any],
    config_name: str,
    path_prefix: str = ""
) -> List[ConfigDiff]:
    """
    Generate a list of differences between two configs.

    Args:
        old_config: Original configuration
        new_config: Updated configuration
        config_name: Name of the configuration
        path_prefix: Prefix for nested field paths

    Returns:
        List of ConfigDiff objects
    """
    diffs = []

    # Check for modified and added fields
    for key, new_value in new_config.items():
        field_path = f"{path_prefix}.{key}" if path_prefix else key

        if key not in old_config:
            # Field added
            diffs.append(ConfigDiff(
                field=field_path,
                old_value=None,
                new_value=new_value,
                config_name=config_name,
                change_type="added"
            ))
        elif old_config[key] != new_value:
            if isinstance(new_value, dict) and isinstance(old_config[key], dict):
                # Recurse into nested dicts
                nested_diffs = generate_config_diff(
                    old_config[key],
                    new_value,
                    config_name,
                    field_path
                )
                diffs.extend(nested_diffs)
            else:
                # Field modified
                diffs.append(ConfigDiff(
                    field=field_path,
                    old_value=old_config[key],
                    new_value=new_value,
                    config_name=config_name,
                    change_type="modified"
                ))

    # Check for removed fields
    for key in old_config:
        if key not in new_config:
            field_path = f"{path_prefix}.{key}" if path_prefix else key
            diffs.append(ConfigDiff(
                field=field_path,
                old_value=old_config[key],
                new_value=None,
                config_name=config_name,
                change_type="removed"
            ))

    return diffs
