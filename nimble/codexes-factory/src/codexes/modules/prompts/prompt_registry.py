"""
Prompt Registry

Centralized prompt storage, versioning, and management for Codexes Factory.
Supports publisher/imprint prompt inheritance and tournament integration.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptRegistry:
    """Centralized prompt management system."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize prompt registry.

        Args:
            base_path: Base directory for prompts (default: prompts/)
        """
        self.base_path = base_path or Path("prompts")
        self.prompts = {}
        self.load_all_prompts()

    def load_all_prompts(self):
        """Load all prompts from prompt directories."""
        # Load base prompts
        base_prompts = self.base_path / "combined_prompts.json"
        if base_prompts.exists():
            try:
                with open(base_prompts) as f:
                    data = json.load(f)
                    self.prompts.update(data)
                logger.info(f"Loaded {len(data)} base prompts")
            except Exception as e:
                logger.error(f"Failed to load base prompts: {e}")

        # Load publisher-specific prompts
        publisher_prompts_dir = self.base_path / "publishers"
        if publisher_prompts_dir.exists():
            for prompt_file in publisher_prompts_dir.glob("*.json"):
                try:
                    with open(prompt_file) as f:
                        data = json.load(f)
                        publisher_name = prompt_file.stem
                        self.prompts[f"publisher:{publisher_name}"] = data
                    logger.info(f"Loaded prompts for publisher: {publisher_name}")
                except Exception as e:
                    logger.error(f"Failed to load {prompt_file}: {e}")

        # Load imprint-specific prompts
        imprint_prompts_dir = self.base_path / "imprints"
        if imprint_prompts_dir.exists():
            for prompt_file in imprint_prompts_dir.glob("*.json"):
                try:
                    with open(prompt_file) as f:
                        data = json.load(f)
                        imprint_name = prompt_file.stem
                        self.prompts[f"imprint:{imprint_name}"] = data
                    logger.info(f"Loaded prompts for imprint: {imprint_name}")
                except Exception as e:
                    logger.error(f"Failed to load {prompt_file}: {e}")

    def get_prompt(
        self,
        prompt_name: str,
        publisher: Optional[str] = None,
        imprint: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Get a prompt with inheritance and variable substitution.

        Inheritance order:
        1. Imprint-specific prompt (if imprint provided)
        2. Publisher-specific prompt (if publisher provided)
        3. Base prompt

        Args:
            prompt_name: Name of the prompt
            publisher: Publisher name for publisher-specific prompts
            imprint: Imprint name for imprint-specific prompts
            variables: Variables to substitute in prompt template

        Returns:
            Formatted prompt string or None if not found
        """
        # Try imprint-specific first
        if imprint:
            imprint_key = f"imprint:{imprint}"
            if imprint_key in self.prompts:
                if prompt_name in self.prompts[imprint_key]:
                    prompt = self.prompts[imprint_key][prompt_name]
                    return self._format_prompt(prompt, variables)

        # Try publisher-specific
        if publisher:
            publisher_key = f"publisher:{publisher}"
            if publisher_key in self.prompts:
                if prompt_name in self.prompts[publisher_key]:
                    prompt = self.prompts[publisher_key][prompt_name]
                    return self._format_prompt(prompt, variables)

        # Fall back to base prompt
        if prompt_name in self.prompts:
            prompt = self.prompts[prompt_name]
            return self._format_prompt(prompt, variables)

        logger.warning(f"Prompt not found: {prompt_name}")
        return None

    def _format_prompt(self, prompt: Any, variables: Optional[Dict[str, str]] = None) -> str:
        """Format a prompt with variable substitution.

        Args:
            prompt: Prompt string or dict
            variables: Variables to substitute

        Returns:
            Formatted prompt string
        """
        if isinstance(prompt, dict):
            # Handle structured prompt format
            if "template" in prompt:
                prompt_str = prompt["template"]
            elif "messages" in prompt:
                # Handle chat format
                return json.dumps(prompt)
            else:
                return json.dumps(prompt)
        else:
            prompt_str = str(prompt)

        # Substitute variables
        if variables:
            for key, value in variables.items():
                prompt_str = prompt_str.replace(f"{{{key}}}", str(value))

        return prompt_str

    def list_prompts(
        self,
        publisher: Optional[str] = None,
        imprint: Optional[str] = None
    ) -> List[str]:
        """List available prompts.

        Args:
            publisher: Filter by publisher
            imprint: Filter by imprint

        Returns:
            List of prompt names
        """
        if imprint:
            key = f"imprint:{imprint}"
            if key in self.prompts:
                return list(self.prompts[key].keys())

        if publisher:
            key = f"publisher:{publisher}"
            if key in self.prompts:
                return list(self.prompts[key].keys())

        # Base prompts
        return [k for k in self.prompts.keys() if not k.startswith("publisher:") and not k.startswith("imprint:")]

    def register_prompt(
        self,
        prompt_name: str,
        prompt_content: str,
        publisher: Optional[str] = None,
        imprint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a new prompt.

        Args:
            prompt_name: Name of the prompt
            prompt_content: Prompt content/template
            publisher: Publisher (if publisher-specific)
            imprint: Imprint (if imprint-specific)
            metadata: Additional metadata
        """
        prompt_data = {
            "template": prompt_content,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        if imprint:
            key = f"imprint:{imprint}"
            if key not in self.prompts:
                self.prompts[key] = {}
            self.prompts[key][prompt_name] = prompt_data
        elif publisher:
            key = f"publisher:{publisher}"
            if key not in self.prompts:
                self.prompts[key] = {}
            self.prompts[key][prompt_name] = prompt_data
        else:
            self.prompts[prompt_name] = prompt_data

        logger.info(f"Registered prompt: {prompt_name}")

    def save_prompts(self):
        """Save prompts back to files."""
        # Save base prompts
        base_prompts = {k: v for k, v in self.prompts.items() if not k.startswith("publisher:") and not k.startswith("imprint:")}
        if base_prompts:
            base_file = self.base_path / "combined_prompts.json"
            with open(base_file, 'w') as f:
                json.dump(base_prompts, f, indent=2)

        # Save publisher prompts
        publisher_dir = self.base_path / "publishers"
        publisher_dir.mkdir(exist_ok=True)
        for key, value in self.prompts.items():
            if key.startswith("publisher:"):
                publisher_name = key.split(":", 1)[1]
                with open(publisher_dir / f"{publisher_name}.json", 'w') as f:
                    json.dump(value, f, indent=2)

        # Save imprint prompts
        imprint_dir = self.base_path / "imprints"
        imprint_dir.mkdir(exist_ok=True)
        for key, value in self.prompts.items():
            if key.startswith("imprint:"):
                imprint_name = key.split(":", 1)[1]
                with open(imprint_dir / f"{imprint_name}.json", 'w') as f:
                    json.dump(value, f, indent=2)

        logger.info("Prompts saved")


# Global registry instance
_registry = None


def get_prompt_registry() -> PromptRegistry:
    """Get global prompt registry instance."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def get_prompt(
    prompt_name: str,
    publisher: Optional[str] = None,
    imprint: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Convenience function to get a prompt from global registry.

    Args:
        prompt_name: Name of the prompt
        publisher: Publisher name
        imprint: Imprint name
        variables: Variables to substitute

    Returns:
        Formatted prompt or None
    """
    registry = get_prompt_registry()
    return registry.get_prompt(prompt_name, publisher, imprint, variables)


# Example usage
if __name__ == "__main__":
    # Initialize registry
    registry = PromptRegistry()

    # Get a prompt with inheritance
    prompt = registry.get_prompt(
        "book_concept",
        publisher="Big Five Killer LLC",
        imprint="warships_and_navies",
        variables={
            "genre": "Naval History",
            "target_audience": "Academic researchers"
        }
    )

    print(prompt)

    # List available prompts
    print("\nBase prompts:", registry.list_prompts())
    print("\nWarships & Navies prompts:", registry.list_prompts(imprint="warships_and_navies"))
