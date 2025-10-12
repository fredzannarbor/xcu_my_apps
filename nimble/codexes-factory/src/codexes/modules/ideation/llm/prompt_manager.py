"""
Prompt management for ideation LLM operations.
Handles loading and managing prompts specific to ideation workflows.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class IdeationPromptManager:
    """Manages prompts for ideation-specific LLM operations."""
    
    def __init__(self):
        """Initialize the prompt manager."""
        self.prompts = {}
        self._load_default_prompts()
        logger.info("IdeationPromptManager initialized")
    
    def _load_default_prompts(self):
        """Load default prompts for ideation operations."""
        self.prompts = {
            "concept_generation": {
                "system": "You are a creative writing assistant specializing in book concept generation.",
                "user": "Generate a book concept with the following parameters: {parameters}"
            },
            "tournament_evaluation": {
                "system": "You are a literary judge evaluating book concepts for a tournament.",
                "user": "Compare these two book concepts and determine the winner: Concept A: {concept_a} Concept B: {concept_b}"
            },
            "series_generation": {
                "system": "You are a series development specialist creating cohesive book series.",
                "user": "Generate a series entry based on this blueprint: {blueprint}"
            },
            "series_name": {
                "system": "You are a creative naming specialist for book series.",
                "user": "Generate a series name for this concept: {concept}"
            },
            "reader_evaluation": {
                "system": "You are a synthetic reader with specific preferences and demographics.",
                "user": "Evaluate this book concept from your perspective: {concept}"
            },
            "element_extraction": {
                "system": "You are a story analysis expert extracting narrative elements.",
                "user": "Extract story elements from this concept: {concept}"
            },
            "element_recombination": {
                "system": "You are a creative synthesis expert combining story elements.",
                "user": "Create a new concept from these elements: {elements}"
            }
        }
    
    def get_prompt(self, prompt_type: str, **kwargs) -> Dict[str, str]:
        """
        Get a formatted prompt for the specified type.
        
        Args:
            prompt_type: Type of prompt to retrieve
            **kwargs: Parameters to format into the prompt
            
        Returns:
            Dictionary with 'system' and 'user' prompt strings
        """
        if prompt_type not in self.prompts:
            logger.warning(f"Unknown prompt type: {prompt_type}")
            return {
                "system": "You are a helpful AI assistant.",
                "user": str(kwargs)
            }
        
        prompt_template = self.prompts[prompt_type]
        
        try:
            formatted_prompt = {
                "system": prompt_template["system"],
                "user": prompt_template["user"].format(**kwargs)
            }
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Missing parameter for prompt {prompt_type}: {e}")
            return prompt_template
        except Exception as e:
            logger.error(f"Error formatting prompt {prompt_type}: {e}")
            return prompt_template
    
    def add_custom_prompt(self, prompt_type: str, system: str, user: str):
        """Add a custom prompt template."""
        self.prompts[prompt_type] = {
            "system": system,
            "user": user
        }
        logger.info(f"Added custom prompt: {prompt_type}")
    
    def get_idea_generation_prompt(self, context_data: Dict[str, Any], 
                                  prompt_config: Dict[str, Any]) -> str:
        """
        Generate a prompt for idea generation based on context and configuration.
        
        Args:
            context_data: Context information for generation
            prompt_config: Configuration for the prompt
            
        Returns:
            Formatted prompt string
        """
        # Extract parameters from context and config
        genre = context_data.get('genre', 'any genre')
        theme = context_data.get('theme', '')
        imprint = context_data.get('imprint', 'general fiction')
        custom_prompt = context_data.get('custom_prompt', '')
        num_ideas = context_data.get('num_ideas', 1)
        
        # Build the prompt
        if custom_prompt:
            prompt = f"""Generate {num_ideas} compelling book concept(s) based on this specific request: {custom_prompt}

For each concept, provide:
1. Title: A compelling, marketable title
2. Logline: A one-sentence hook that captures the essence
3. Description: A detailed 2-3 paragraph description
4. Genre: The primary genre classification
5. Target Audience: Who would read this book

Format each concept clearly and make them unique, creative, and commercially viable."""
        else:
            theme_text = f" with themes around {theme}" if theme else ""
            prompt = f"""Generate {num_ideas} original, compelling book concept(s) for {imprint}{theme_text}.

Each concept should be:
- Unique and creative
- Commercially viable
- Well-developed with clear conflict and stakes
- Suitable for the target market

For each concept, provide:
1. Title: A compelling, marketable title
2. Logline: A one-sentence hook that captures the essence  
3. Description: A detailed 2-3 paragraph description
4. Genre: The primary genre classification
5. Target Audience: Who would read this book

Make each concept distinct and engaging. Focus on strong premises with clear conflict and emotional stakes."""

        return prompt
    
    def list_available_prompts(self) -> list:
        """Get list of available prompt types."""
        return list(self.prompts.keys())