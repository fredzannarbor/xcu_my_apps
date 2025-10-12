"""
Hierarchical writing style configuration system.
"""

import json
import os
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WritingStyleManager:
    """Hierarchical writing style configuration system"""
    
    def __init__(self):
        self.style_hierarchy = ['tranche', 'imprint', 'publisher']
    
    def load_writing_style(self, tranche: str, imprint: str, publisher: str) -> Dict[str, Any]:
        """Load writing style configuration with proper hierarchy"""
        try:
            style_config = {}
            
            # Load in hierarchy order (publisher -> imprint -> tranche)
            # Later configs override earlier ones
            for level in reversed(self.style_hierarchy):
                if level == 'publisher' and publisher:
                    config = self._load_style_config('publishers', publisher)
                elif level == 'imprint' and imprint:
                    config = self._load_style_config('imprints', imprint)
                elif level == 'tranche' and tranche:
                    config = self._load_style_config('tranches', tranche)
                else:
                    continue
                
                if config:
                    # Merge configurations (tranche overrides imprint overrides publisher)
                    style_config.update(config)
            
            return style_config
            
        except Exception as e:
            logger.error(f"Error loading writing style: {e}")
            return {}
    
    def _load_style_config(self, config_type: str, name: str) -> Dict[str, Any]:
        """Load writing style config from specific directory"""
        try:
            config_path = f"configs/{config_type}/{name}/writing_style.json"
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error loading style config from {config_path}: {e}")
            return {}
    
    def construct_style_prompt(self, style_config: Dict[str, Any]) -> str:
        """Construct single prompt from multiple text values in style config"""
        try:
            if not style_config:
                return ""
            
            prompt_parts = []
            
            # Process different style elements
            style_elements = [
                'tone', 'voice', 'perspective', 'vocabulary', 
                'sentence_structure', 'formatting', 'examples'
            ]
            
            for element in style_elements:
                if element in style_config:
                    value = style_config[element]
                    if isinstance(value, str):
                        prompt_parts.append(f"{element.replace('_', ' ').title()}: {value}")
                    elif isinstance(value, list):
                        prompt_parts.append(f"{element.replace('_', ' ').title()}: {', '.join(value)}")
            
            # Add any custom instructions
            if 'instructions' in style_config:
                instructions = style_config['instructions']
                if isinstance(instructions, list):
                    prompt_parts.extend(instructions)
                elif isinstance(instructions, str):
                    prompt_parts.append(instructions)
            
            return " ".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error constructing style prompt: {e}")
            return ""
    
    def apply_style_to_prompt(self, original_prompt: str, style_prompt: str) -> str:
        """Append style configuration to original prompt"""
        try:
            if not style_prompt:
                return original_prompt
            
            # Add style instructions to the end of the original prompt
            styled_prompt = f"{original_prompt}\n\nWriting Style Guidelines: {style_prompt}"
            
            return styled_prompt
            
        except Exception as e:
            logger.error(f"Error applying style to prompt: {e}")
            return original_prompt
    
    def validate_style_config(self, config_path: str) -> bool:
        """Validate writing_style.json file format and content"""
        try:
            if not os.path.exists(config_path):
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Check if it's a valid dictionary
            if not isinstance(config, dict):
                return False
            
            # Validate known style elements
            valid_elements = [
                'tone', 'voice', 'perspective', 'vocabulary',
                'sentence_structure', 'formatting', 'examples', 'instructions'
            ]
            
            for key in config.keys():
                if key not in valid_elements:
                    logger.warning(f"Unknown style element: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating style config: {e}")
            return False