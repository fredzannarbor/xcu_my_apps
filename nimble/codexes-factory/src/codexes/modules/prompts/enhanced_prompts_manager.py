#!/usr/bin/env python3
"""
Enhanced Prompts Management System for Codexes Factory

This module handles hierarchical prompt selection, virtual prompt file merging,
and organization of prompts into front matter, body, and back matter sections.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PromptSection:
    """Represents a section of prompts (front matter, body, or back matter)."""
    name: str
    prompts: List[str] = field(default_factory=list)
    order: List[str] = field(default_factory=list)  # Order in which prompts should appear

@dataclass
class BookStructure:
    """Represents the complete structure of a book with prompt organization."""
    front_matter: PromptSection = field(default_factory=lambda: PromptSection("front_matter"))
    body_source: Optional[str] = None  # Path to markdown or PDF file
    back_matter: PromptSection = field(default_factory=lambda: PromptSection("back_matter"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "front_matter": {
                "prompts": self.front_matter.prompts,
                "order": self.front_matter.order
            },
            "body_source": self.body_source,
            "back_matter": {
                "prompts": self.back_matter.prompts,
                "order": self.back_matter.order
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookStructure':
        """Create from dictionary."""
        structure = cls()
        if "front_matter" in data:
            structure.front_matter.prompts = data["front_matter"].get("prompts", [])
            structure.front_matter.order = data["front_matter"].get("order", [])
        if "back_matter" in data:
            structure.back_matter.prompts = data["back_matter"].get("prompts", [])
            structure.back_matter.order = data["back_matter"].get("order", [])
        structure.body_source = data.get("body_source")
        return structure

class EnhancedPromptsManager:
    """Enhanced prompts management with hierarchical loading and virtual merging."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the prompts manager."""
        self.project_root = project_root or Path(".")
        self.logger = logging.getLogger(self.__class__.__name__)

    def discover_prompts_files(self) -> Dict[str, List[str]]:
        """Discover available prompts files at publisher and imprint levels."""
        prompts_files = {
            "publisher": [],
            "imprint": []
        }

        # Look for publisher-level prompts files
        publisher_prompts_dir = self.project_root / "prompts"
        if publisher_prompts_dir.exists():
            for prompts_file in publisher_prompts_dir.glob("*.json"):
                if prompts_file.name != "prompts.json":  # Skip global prompts file
                    prompts_files["publisher"].append(prompts_file.stem)

            # Also check global prompts.json as a publisher-level file
            global_prompts = publisher_prompts_dir / "prompts.json"
            if global_prompts.exists():
                prompts_files["publisher"].append("global")

        # Look for imprint-level prompts files
        imprints_dir = self.project_root / "imprints"
        if imprints_dir.exists():
            for imprint_dir in imprints_dir.iterdir():
                if imprint_dir.is_dir():
                    prompts_file = imprint_dir / "prompts.json"
                    if prompts_file.exists():
                        prompts_files["imprint"].append(imprint_dir.name)

        return prompts_files

    def load_prompts_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a single prompts file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load prompts file {file_path}: {e}")
            return {}

    def get_prompts_file_path(self, level: str, name: str) -> Optional[Path]:
        """Get the path to a prompts file by level and name."""
        if level == "publisher":
            if name == "global":
                return self.project_root / "prompts" / "prompts.json"
            else:
                return self.project_root / "prompts" / f"{name}.json"
        elif level == "imprint":
            return self.project_root / "imprints" / name / "prompts.json"
        return None

    def create_virtual_prompts_file(self,
                                  publisher_files: List[str],
                                  imprint_files: List[str]) -> Dict[str, Any]:
        """Create a virtual prompts file by merging publisher and imprint files.

        Imprint prompts take precedence over publisher prompts for identical keys.
        """
        virtual_prompts = {
            "prompt_keys": [],
            "reprompt_keys": [],
            "_metadata": {
                "created_at": datetime.now().isoformat(),
                "source_files": {
                    "publisher": publisher_files,
                    "imprint": imprint_files
                },
                "virtual": True
            }
        }

        # Load all publisher prompts first
        all_prompts = {}
        for publisher_file in publisher_files:
            file_path = self.get_prompts_file_path("publisher", publisher_file)
            if file_path and file_path.exists():
                prompts_data = self.load_prompts_file(file_path)
                # Merge prompt definitions (individual prompts)
                for key, value in prompts_data.items():
                    if key not in ["prompt_keys", "reprompt_keys", "_metadata", "imprint_name", "imprint_intro"]:
                        all_prompts[key] = value

                # Collect prompt keys
                if "prompt_keys" in prompts_data:
                    for key in prompts_data["prompt_keys"]:
                        if key not in virtual_prompts["prompt_keys"]:
                            virtual_prompts["prompt_keys"].append(key)

                if "reprompt_keys" in prompts_data:
                    for key in prompts_data["reprompt_keys"]:
                        if key not in virtual_prompts["reprompt_keys"]:
                            virtual_prompts["reprompt_keys"].append(key)

        # Load imprint prompts (these take precedence)
        for imprint_file in imprint_files:
            file_path = self.get_prompts_file_path("imprint", imprint_file)
            if file_path and file_path.exists():
                prompts_data = self.load_prompts_file(file_path)
                # Merge prompt definitions (imprint overrides publisher)
                for key, value in prompts_data.items():
                    if key not in ["prompt_keys", "reprompt_keys", "_metadata", "imprint_name", "imprint_intro"]:
                        all_prompts[key] = value  # Imprint takes precedence

                # Update metadata from imprint
                if "imprint_name" in prompts_data:
                    virtual_prompts["imprint_name"] = prompts_data["imprint_name"]
                if "imprint_intro" in prompts_data:
                    virtual_prompts["imprint_intro"] = prompts_data["imprint_intro"]

                # Merge prompt keys (imprint additions)
                if "prompt_keys" in prompts_data:
                    for key in prompts_data["prompt_keys"]:
                        if key not in virtual_prompts["prompt_keys"]:
                            virtual_prompts["prompt_keys"].append(key)

                if "reprompt_keys" in prompts_data:
                    for key in prompts_data["reprompt_keys"]:
                        if key not in virtual_prompts["reprompt_keys"]:
                            virtual_prompts["reprompt_keys"].append(key)

        # Add all merged prompts to virtual file
        virtual_prompts.update(all_prompts)

        return virtual_prompts

    def get_available_prompts(self, virtual_prompts: Dict[str, Any]) -> List[str]:
        """Get list of available prompt keys from virtual prompts file."""
        available_prompts = []

        # Get all prompt keys that have actual prompt definitions
        for key in virtual_prompts.get("prompt_keys", []):
            if key in virtual_prompts and isinstance(virtual_prompts[key], dict):
                available_prompts.append(key)

        # Also include any other prompt-like keys
        for key, value in virtual_prompts.items():
            if (key not in ["prompt_keys", "reprompt_keys", "_metadata", "imprint_name", "imprint_intro"]
                and isinstance(value, dict)
                and "messages" in value):
                if key not in available_prompts:
                    available_prompts.append(key)

        return sorted(available_prompts)

    def categorize_prompts(self, available_prompts: List[str]) -> Dict[str, List[str]]:
        """Categorize prompts into suggested front matter, body, and back matter categories."""
        # Define prompt categories based on common naming patterns
        front_matter_patterns = [
            "basic_info", "metadata", "bibliographic", "intro", "preface",
            "foreword", "acknowledgments", "dedication", "abstract", "summary"
        ]

        back_matter_patterns = [
            "bibliography", "back_cover", "bio", "author", "appendix",
            "glossary", "index", "notes", "references", "conclusion",
            "epilogue", "afterword"
        ]

        categorized = {
            "front_matter": [],
            "content": [],  # Main content generation prompts
            "back_matter": []
        }

        for prompt in available_prompts:
            prompt_lower = prompt.lower()

            # Check for front matter patterns
            if any(pattern in prompt_lower for pattern in front_matter_patterns):
                categorized["front_matter"].append(prompt)
            # Check for back matter patterns
            elif any(pattern in prompt_lower for pattern in back_matter_patterns):
                categorized["back_matter"].append(prompt)
            # Everything else is content
            else:
                categorized["content"].append(prompt)

        return categorized

    def validate_book_structure(self, structure: BookStructure, virtual_prompts: Dict[str, Any]) -> List[str]:
        """Validate that the book structure references valid prompts and files."""
        errors = []
        available_prompts = self.get_available_prompts(virtual_prompts)

        # Validate front matter prompts
        for prompt in structure.front_matter.prompts:
            if prompt not in available_prompts:
                errors.append(f"Front matter prompt '{prompt}' not found in virtual prompts file")

        # Validate back matter prompts
        for prompt in structure.back_matter.prompts:
            if prompt not in available_prompts:
                errors.append(f"Back matter prompt '{prompt}' not found in virtual prompts file")

        # Validate body source file
        if structure.body_source:
            body_path = Path(structure.body_source)
            if not body_path.exists():
                errors.append(f"Body source file '{structure.body_source}' does not exist")
            elif not body_path.suffix.lower() in ['.md', '.pdf', '.txt']:
                errors.append(f"Body source file '{structure.body_source}' must be .md, .pdf, or .txt")

        return errors

    def generate_command_line_args(self,
                                 publisher_files: List[str],
                                 imprint_files: List[str],
                                 structure: BookStructure) -> List[str]:
        """Generate command line arguments for the enhanced prompts system."""
        args = []

        # Add publisher prompts files
        if publisher_files:
            args.extend(["--publisher-prompts", ",".join(publisher_files)])

        # Add imprint prompts files
        if imprint_files:
            args.extend(["--imprint-prompts", ",".join(imprint_files)])

        # Add front matter prompts
        if structure.front_matter.prompts:
            front_matter_ordered = structure.front_matter.order if structure.front_matter.order else structure.front_matter.prompts
            args.extend(["--front-matter-prompts", ",".join(front_matter_ordered)])

        # Add body source
        if structure.body_source:
            args.extend(["--body-source", structure.body_source])

        # Add back matter prompts
        if structure.back_matter.prompts:
            back_matter_ordered = structure.back_matter.order if structure.back_matter.order else structure.back_matter.prompts
            args.extend(["--back-matter-prompts", ",".join(back_matter_ordered)])

        return args

    def save_book_structure(self, structure: BookStructure, output_path: Path) -> None:
        """Save book structure configuration to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structure.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"Book structure saved to {output_path}")

    def load_book_structure(self, file_path: Path) -> BookStructure:
        """Load book structure configuration from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return BookStructure.from_dict(data)