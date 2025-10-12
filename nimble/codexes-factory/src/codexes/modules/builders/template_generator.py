# add imports
from pathlib import Path
from typing import Dict


class TemplateGenerator:
    """Generate LaTeX templates customized for specific codex types"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.base_templates = self.load_base_templates()

    def generate_interior_template(self, codex_type: str, requirements: Dict) -> str:
        """Generate customized interior template"""

        base_template = self.base_templates["interior"]

        # Customize based on codex type
        customizations = {
            "pilsa_book": self.get_pilsa_customizations,
            "poetry_collection": self.get_poetry_customizations,
            "technical_manual": self.get_technical_customizations,
            "children_book": self.get_children_customizations
        }

        customizer = customizations.get(codex_type, self.get_default_customizations)
        template_mods = customizer(requirements)

        # Apply customizations
        customized_template = self.apply_template_modifications(base_template, template_mods)

        return customized_template

    def get_pilsa_customizations(self, requirements: Dict) -> Dict:
        """Get customizations specific to pilsa books"""
        return {
            "page_structure": "quotation_and_facing_page",
            "font_requirements": requirements.get("main_font", "Adobe Caslon Pro"),
            "special_formatting": ["quote_boxes", "meditation_spacing"],
            "page_count": 216,  # 90 quotes + 90 facing pages + front/back matter
            "binding_considerations": "lay_flat_binding_preferred"
        }

    def get_poetry_customizations(self, requirements: Dict) -> Dict:
        """Get customizations specific to poetry collections"""
        return {
            "page_structure": "poetry_layout",
            "font_requirements": requirements.get("main_font", "Adobe Caslon Pro"),
            "special_formatting": ["line_spacing_control", "stanza_breaks", "poem_titles"],
            "page_count": "variable",
            "binding_considerations": "standard"
        }