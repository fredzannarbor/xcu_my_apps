"""
Validation utilities for batch operations.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from .models import ValidationError, ValidationSeverity

logger = logging.getLogger(__name__)


class BatchValidator:
    """Validates configuration files against schemas."""

    def __init__(self, template_path: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            template_path: Path to template schema file
        """
        self.template_path = template_path
        self.template_schema = None

        if template_path and template_path.exists():
            self.load_template_schema(template_path)

    def load_template_schema(self, template_path: Path) -> bool:
        """
        Load template schema from file.

        Args:
            template_path: Path to template file

        Returns:
            True if loaded successfully
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template_schema = json.load(f)
            logger.info(f"Loaded template schema from {template_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load template schema: {e}")
            return False

    def validate_config(
        self,
        config: Dict[str, Any],
        config_name: str,
        strict: bool = False
    ) -> List[ValidationError]:
        """
        Validate a configuration against the template schema.

        Args:
            config: Configuration to validate
            config_name: Name of the configuration
            strict: Whether to use strict validation

        Returns:
            List of validation errors
        """
        errors = []

        if not self.template_schema:
            errors.append(ValidationError(
                field="schema",
                message="No template schema loaded",
                severity=ValidationSeverity.WARNING,
                config_name=config_name
            ))
            return errors

        # Check for missing required fields
        missing_fields = self._check_missing_fields(config, self.template_schema)
        for field in missing_fields:
            severity = ValidationSeverity.ERROR if strict else ValidationSeverity.WARNING
            errors.append(ValidationError(
                field=field,
                message="Required field is missing",
                severity=severity,
                config_name=config_name,
                suggested_fix=f"Add the '{field}' field to the configuration"
            ))

        # Check for placeholder values
        placeholder_fields = self._check_placeholder_fields(config)
        for field in placeholder_fields:
            severity = ValidationSeverity.WARNING if strict else ValidationSeverity.INFO
            errors.append(ValidationError(
                field=field,
                message="Field contains placeholder value",
                severity=severity,
                config_name=config_name,
                suggested_fix=f"Replace placeholder value in '{field}'"
            ))

        # Check for empty required fields
        empty_fields = self._check_empty_fields(config)
        for field in empty_fields:
            errors.append(ValidationError(
                field=field,
                message="Required field is empty",
                severity=ValidationSeverity.WARNING,
                config_name=config_name,
                suggested_fix=f"Provide a value for '{field}'"
            ))

        # Validate specific field types
        type_errors = self._validate_field_types(config, config_name)
        errors.extend(type_errors)

        return errors

    def _check_missing_fields(
        self,
        config: Dict[str, Any],
        template: Dict[str, Any],
        path_prefix: str = ""
    ) -> List[str]:
        """Check for fields missing in config compared to template."""
        missing = []

        for key, value in template.items():
            field_path = f"{path_prefix}.{key}" if path_prefix else key

            if key not in config:
                # Skip optional fields
                if not key.startswith("_") and key not in ["lsi_specific_settings", "codextypes"]:
                    missing.append(field_path)
            elif isinstance(value, dict) and isinstance(config.get(key), dict):
                nested_missing = self._check_missing_fields(
                    config[key],
                    value,
                    field_path
                )
                missing.extend(nested_missing)

        return missing

    def _check_placeholder_fields(
        self,
        config: Dict[str, Any],
        path_prefix: str = ""
    ) -> List[str]:
        """Check for fields containing placeholder values."""
        placeholders = []

        for key, value in config.items():
            field_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, str):
                # Check for common placeholder patterns
                if any(pattern in value for pattern in [
                    "[PLACEHOLDER]",
                    "[IMPRINT_",
                    "[AI_",
                    "[CONTACT_",
                    "[PRIMARY_",
                    "[SECONDARY_",
                    "[GENRE_",
                    "[TARGET_",
                    "[BISAC_",
                    "[THEMA_",
                    "[LSI_",
                    "[FLEX_",
                ]):
                    placeholders.append(field_path)
            elif isinstance(value, dict):
                nested = self._check_placeholder_fields(value, field_path)
                placeholders.extend(nested)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and "[" in item and "]" in item:
                        placeholders.append(f"{field_path}[{i}]")
                    elif isinstance(item, dict):
                        nested = self._check_placeholder_fields(
                            item,
                            f"{field_path}[{i}]"
                        )
                        placeholders.extend(nested)

        return placeholders

    def _check_empty_fields(
        self,
        config: Dict[str, Any],
        path_prefix: str = ""
    ) -> List[str]:
        """Check for empty required fields."""
        empty = []

        # List of fields that should not be empty
        required_fields = [
            "imprint",
            "publisher",
            "publisher_persona.persona_name",
            "wizard_configuration.name",
            "wizard_configuration.charter"
        ]

        for field in required_fields:
            parts = field.split(".")
            value = config

            # Navigate to nested field
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            # Check if empty
            if value is None or (isinstance(value, str) and not value.strip()):
                empty.append(field)

        return empty

    def _validate_field_types(
        self,
        config: Dict[str, Any],
        config_name: str
    ) -> List[ValidationError]:
        """Validate specific field types."""
        errors = []

        # Validate price point
        if "wizard_configuration" in config:
            wizard_config = config["wizard_configuration"]
            if "price_point" in wizard_config:
                price = wizard_config["price_point"]
                if not isinstance(price, (int, float)):
                    errors.append(ValidationError(
                        field="wizard_configuration.price_point",
                        message=f"Price point must be a number, got {type(price).__name__}",
                        severity=ValidationSeverity.ERROR,
                        config_name=config_name
                    ))
                elif price <= 0:
                    errors.append(ValidationError(
                        field="wizard_configuration.price_point",
                        message="Price point must be positive",
                        severity=ValidationSeverity.ERROR,
                        config_name=config_name
                    ))

        # Validate page count
        if "wizard_configuration" in config:
            wizard_config = config["wizard_configuration"]
            if "page_count" in wizard_config:
                pages = wizard_config["page_count"]
                if not isinstance(pages, int):
                    errors.append(ValidationError(
                        field="wizard_configuration.page_count",
                        message=f"Page count must be an integer, got {type(pages).__name__}",
                        severity=ValidationSeverity.ERROR,
                        config_name=config_name
                    ))
                elif pages <= 0:
                    errors.append(ValidationError(
                        field="wizard_configuration.page_count",
                        message="Page count must be positive",
                        severity=ValidationSeverity.ERROR,
                        config_name=config_name
                    ))

        # Validate genres
        if "wizard_configuration" in config:
            wizard_config = config["wizard_configuration"]
            if "genres" in wizard_config:
                genres = wizard_config["genres"]
                if not isinstance(genres, list):
                    errors.append(ValidationError(
                        field="wizard_configuration.genres",
                        message="Genres must be a list",
                        severity=ValidationSeverity.ERROR,
                        config_name=config_name
                    ))
                elif len(genres) == 0:
                    errors.append(ValidationError(
                        field="wizard_configuration.genres",
                        message="At least one genre should be specified",
                        severity=ValidationSeverity.WARNING,
                        config_name=config_name
                    ))

        return errors

    def validate_batch(
        self,
        configs: Dict[str, Dict[str, Any]],
        strict: bool = False
    ) -> Dict[str, List[ValidationError]]:
        """
        Validate multiple configurations.

        Args:
            configs: Dictionary of config name to config data
            strict: Whether to use strict validation

        Returns:
            Dictionary mapping config names to their validation errors
        """
        results = {}

        for name, config in configs.items():
            errors = self.validate_config(config, name, strict)
            if errors:
                results[name] = errors

        return results

    def get_validation_summary(
        self,
        validation_results: Dict[str, List[ValidationError]]
    ) -> Dict[str, Any]:
        """
        Get summary statistics from validation results.

        Args:
            validation_results: Validation results to summarize

        Returns:
            Dictionary containing summary statistics
        """
        total_configs = len(validation_results)
        total_errors = sum(
            len([e for e in errors if e.severity == ValidationSeverity.ERROR])
            for errors in validation_results.values()
        )
        total_warnings = sum(
            len([e for e in errors if e.severity == ValidationSeverity.WARNING])
            for errors in validation_results.values()
        )
        total_info = sum(
            len([e for e in errors if e.severity == ValidationSeverity.INFO])
            for errors in validation_results.values()
        )

        configs_with_errors = sum(
            1 for errors in validation_results.values()
            if any(e.severity == ValidationSeverity.ERROR for e in errors)
        )

        return {
            "total_configs": total_configs,
            "configs_with_errors": configs_with_errors,
            "configs_with_warnings": sum(
                1 for errors in validation_results.values()
                if any(e.severity == ValidationSeverity.WARNING for e in errors)
            ),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "success_rate": (
                (total_configs - configs_with_errors) / total_configs * 100
                if total_configs > 0 else 0
            )
        }
