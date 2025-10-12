"""
Configuration loader for batch operations.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BatchConfigLoader:
    """Loads and manages batch configuration files."""

    def __init__(self):
        """Initialize the config loader."""
        self.loaded_configs: Dict[str, Dict[str, Any]] = {}
        self.load_errors: Dict[str, str] = {}

    def load_config(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a single configuration file.

        Args:
            config_path: Path to the config file

        Returns:
            Loaded config dictionary or None if failed
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.loaded_configs[config_path.stem] = config
            logger.info(f"Loaded config: {config_path.stem}")
            return config

        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {e}"
            logger.error(f"Failed to load {config_path}: {error_msg}")
            self.load_errors[config_path.stem] = error_msg
            return None

        except Exception as e:
            error_msg = f"Error loading config: {e}"
            logger.error(f"Failed to load {config_path}: {error_msg}")
            self.load_errors[config_path.stem] = error_msg
            return None

    def load_configs_from_paths(
        self,
        paths: List[Path],
        ignore_errors: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load all configs from the given paths.

        Args:
            paths: List of directory or file paths
            ignore_errors: Whether to continue on errors

        Returns:
            Dictionary mapping config names to their data
        """
        self.loaded_configs.clear()
        self.load_errors.clear()

        config_files = []

        # Collect all config files
        for path in paths:
            if path.is_dir():
                json_files = list(path.glob("*.json"))
                # Exclude template files
                config_files.extend([
                    f for f in json_files
                    if "template" not in f.name.lower()
                ])
            elif path.is_file() and path.suffix == ".json":
                config_files.append(path)

        # Load each config
        for config_file in config_files:
            config = self.load_config(config_file)
            if config is None and not ignore_errors:
                raise ValueError(f"Failed to load {config_file}")

        logger.info(
            f"Loaded {len(self.loaded_configs)} configs, "
            f"{len(self.load_errors)} errors"
        )

        return self.loaded_configs

    def load_config_with_path(
        self,
        config_path: Path
    ) -> Optional[tuple[Dict[str, Any], Path]]:
        """
        Load a config and return it with its path.

        Args:
            config_path: Path to the config file

        Returns:
            Tuple of (config_dict, path) or None if failed
        """
        config = self.load_config(config_path)
        if config:
            return (config, config_path)
        return None

    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get a loaded config by name."""
        return self.loaded_configs.get(config_name)

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded configs."""
        return self.loaded_configs.copy()

    def get_errors(self) -> Dict[str, str]:
        """Get all load errors."""
        return self.load_errors.copy()

    def has_errors(self) -> bool:
        """Check if there were any load errors."""
        return len(self.load_errors) > 0

    def save_config(
        self,
        config_name: str,
        config_data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Save a config to disk.

        Args:
            config_name: Name of the config
            config_data: Config data to save
            output_path: Path to save to

        Returns:
            True if successful
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved config: {config_name} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config {config_name}: {e}")
            return False

    def save_all_configs(
        self,
        output_dir: Path,
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, bool]:
        """
        Save all configs to a directory.

        Args:
            output_dir: Directory to save configs to
            configs: Configs to save (uses loaded_configs if None)

        Returns:
            Dictionary mapping config names to success status
        """
        if configs is None:
            configs = self.loaded_configs

        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        for name, config in configs.items():
            output_path = output_dir / f"{name}.json"
            results[name] = self.save_config(name, config, output_path)

        return results

    def load_template(self, template_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a template configuration.

        Args:
            template_path: Path to the template file

        Returns:
            Template configuration or None
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            logger.info(f"Loaded template: {template_path.name}")
            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return None

    def get_missing_fields(
        self,
        config: Dict[str, Any],
        template: Dict[str, Any],
        path_prefix: str = ""
    ) -> List[str]:
        """
        Find missing fields in a config compared to a template.

        Args:
            config: Config to check
            template: Template to compare against
            path_prefix: Prefix for nested field paths

        Returns:
            List of missing field paths
        """
        missing = []

        for key, value in template.items():
            field_path = f"{path_prefix}.{key}" if path_prefix else key

            if key not in config:
                missing.append(field_path)
            elif isinstance(value, dict) and isinstance(config.get(key), dict):
                # Recurse into nested dictionaries
                nested_missing = self.get_missing_fields(
                    config[key],
                    value,
                    field_path
                )
                missing.extend(nested_missing)

        return missing

    def get_placeholder_fields(
        self,
        config: Dict[str, Any],
        path_prefix: str = ""
    ) -> List[str]:
        """
        Find fields containing placeholder values.

        Args:
            config: Config to check
            path_prefix: Prefix for nested field paths

        Returns:
            List of field paths containing placeholders
        """
        placeholders = []

        for key, value in config.items():
            field_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, str):
                if "[PLACEHOLDER]" in value or value.startswith("[") and value.endswith("]"):
                    placeholders.append(field_path)
            elif isinstance(value, dict):
                # Recurse into nested dictionaries
                nested_placeholders = self.get_placeholder_fields(value, field_path)
                placeholders.extend(nested_placeholders)
            elif isinstance(value, list):
                # Check list items
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        if "[PLACEHOLDER]" in item or (item.startswith("[") and item.endswith("]")):
                            placeholders.append(f"{field_path}[{i}]")
                    elif isinstance(item, dict):
                        nested_placeholders = self.get_placeholder_fields(
                            item,
                            f"{field_path}[{i}]"
                        )
                        placeholders.extend(nested_placeholders)

        return placeholders

    def clear(self):
        """Clear all loaded configs and errors."""
        self.loaded_configs.clear()
        self.load_errors.clear()
