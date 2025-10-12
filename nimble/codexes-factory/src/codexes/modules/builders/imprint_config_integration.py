# imports
import yaml
from pathlib import Path
from typing import List, Dict

from codexes.core.auth import get_allowed_pages

class ImprintConfigIntegration:
    """Integrate generated imprints with the codex-factory config system"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_manager = ConfigManager()

    def register_new_imprint(self, imprint_name: str, codex_types: List[str], artifacts: Dict) -> None:
        """Register new imprint and its codex types in the system"""

        # 1. Update main config.yaml
        self.update_main_config(imprint_name, codex_types)

        # 2. Create imprint-specific config
        self.create_imprint_config(imprint_name, artifacts)

        # 3. Register codex types
        for codex_type in codex_types:
            self.register_codex_type(codex_type, artifacts)

        # 4. Update pipeline configurations
        self.update_pipeline_configs(imprint_name, codex_types)

    def update_main_config(self, imprint_name: str, codex_types: List[str]) -> None:
        """Update the main config.yaml file"""
        config_path = self.project_root / "resources" / "yaml" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Add imprint to available imprints
        if "imprints" not in config:
            config["imprints"] = []
        config["imprints"].append(imprint_name.lower().replace(" ", "_"))

        # Add codex types to available types
        if "codex_types" not in config:
            config["codex_types"] = []
        for codex_type in codex_types:
            if codex_type not in config["codex_types"]:
                config["codex_types"].append(codex_type)

        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, allow_unicode=True)