"""
Prompt Loader for Social Feed Generator

Loads prompt templates and contexts from JSON files in the prompts directory.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class PromptLoader:
    """Loads and manages prompt templates from JSON files."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt loader.

        Args:
            prompts_dir: Path to prompts directory. If None, uses project_root/prompts
        """
        if prompts_dir is None:
            # Get project root (go up from src/social_server/core to project root)
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.prompts_dir = project_root / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        self.logger = logging.getLogger(__name__)
        self._base_template = None
        self._post_type_contexts = None

    def load_base_template(self) -> Dict[str, Any]:
        """Load the base prompt template."""
        if self._base_template is None:
            template_file = self.prompts_dir / "social_feed_base_template.json"
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    self._base_template = json.load(f)
                self.logger.debug(f"Loaded base template from {template_file}")
            except FileNotFoundError:
                self.logger.error(f"Base template file not found: {template_file}")
                raise
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in base template file: {e}")
                raise

        return self._base_template

    def load_post_type_contexts(self) -> Dict[str, Any]:
        """Load post type contexts."""
        if self._post_type_contexts is None:
            contexts_file = self.prompts_dir / "post_type_contexts.json"
            try:
                with open(contexts_file, 'r', encoding='utf-8') as f:
                    self._post_type_contexts = json.load(f)
                self.logger.debug(f"Loaded post type contexts from {contexts_file}")
            except FileNotFoundError:
                self.logger.error(f"Post type contexts file not found: {contexts_file}")
                raise
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in post type contexts file: {e}")
                raise

        return self._post_type_contexts

    def get_base_prompt_template(self) -> str:
        """Get the base prompt template string."""
        template_data = self.load_base_template()
        return template_data.get("base_prompt_template", "")

    def get_post_type_context(self, post_type: str) -> str:
        """Get context for a specific post type.

        Args:
            post_type: The post type (e.g., "book_recommendation")

        Returns:
            Context string for the post type
        """
        contexts_data = self.load_post_type_contexts()
        contexts = contexts_data.get("post_type_contexts", {})
        default_context = contexts_data.get("default_context", "Create engaging content about your domain of expertise.")

        return contexts.get(post_type, default_context)

    def format_prompt(self, persona, post_type) -> str:
        """Format the complete prompt for a persona and post type.

        Args:
            persona: AIPersona object
            post_type: PostType enum

        Returns:
            Formatted prompt string
        """
        template = self.get_base_prompt_template()
        post_type_context = self.get_post_type_context(post_type.value)

        # Extract model provider
        model_provider = "Unknown"
        if persona.claude_agent_config and 'model' in persona.claude_agent_config:
            model = persona.claude_agent_config['model']
            if '/' in model:
                model_provider = model.split('/')[0].title()
            else:
                model_provider = model

        # Format the template
        formatted_prompt = template.format(
            persona_name=persona.name,
            persona_handle=persona.handle,
            model_provider=model_provider,
            persona_bio=persona.bio,
            persona_specialty=persona.specialty,
            persona_personality=', '.join(persona.personality_traits),
            persona_writing_style=persona.writing_style,
            persona_interests=', '.join(persona.interests),
            post_type=post_type.value,
            post_type_context=post_type_context
        )

        return formatted_prompt

    def reload(self):
        """Reload all templates from files."""
        self._base_template = None
        self._post_type_contexts = None
        self.logger.info("Prompt templates reloaded")