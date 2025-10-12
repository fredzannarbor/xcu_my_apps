"""
Writing Style Manager - Hierarchical writing style configuration system
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WritingStyleConfig:
    """Writing style configuration data"""
    level: str  # 'tranche', 'imprint', 'publisher'
    name: str
    style_data: Dict[str, Any]
    file_path: str
    is_valid: bool = True
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

class WritingStyleManager:
    """Hierarchical writing style configuration system"""
    
    def __init__(self):
        self.style_hierarchy = ['tranche', 'imprint', 'publisher']
        self.base_paths = {
            'tranche': 'configs/tranches',
            'imprint': 'configs/imprints',
            'publisher': 'configs/publishers'
        }
        self.cache = {}
        self.required_fields = ['text_values', 'style_type']
        self.optional_fields = ['description', 'version', 'created_date', 'updated_date']
    
    def load_writing_style(self, tranche: Optional[str] = None, 
                          imprint: Optional[str] = None, 
                          publisher: Optional[str] = None) -> Dict[str, Any]:
        """Load writing style configuration with proper hierarchy"""
        try:
            # Build cache key
            cache_key = f"{tranche or 'none'}_{imprint or 'none'}_{publisher or 'none'}"
            
            if cache_key in self.cache:
                logger.debug(f"Using cached writing style for {cache_key}")
                return self.cache[cache_key]
            
            # Load configurations in reverse hierarchy order (publisher -> imprint -> tranche)
            configs = []
            
            # Load publisher config (lowest priority)
            if publisher:
                publisher_config = self._load_single_config('publisher', publisher)
                if publisher_config:
                    configs.append(publisher_config)
            
            # Load imprint config (medium priority)
            if imprint:
                imprint_config = self._load_single_config('imprint', imprint)
                if imprint_config:
                    configs.append(imprint_config)
            
            # Load tranche config (highest priority)
            if tranche:
                tranche_config = self._load_single_config('tranche', tranche)
                if tranche_config:
                    configs.append(tranche_config)
            
            # Merge configurations with proper precedence
            merged_style = self._merge_style_configs(configs)
            
            # Cache the result
            self.cache[cache_key] = merged_style
            
            logger.info(f"Loaded writing style with {len(configs)} config levels")
            return merged_style
            
        except Exception as e:
            logger.error(f"Error loading writing style: {e}")
            return self._get_default_style()
    
    def _load_single_config(self, level: str, name: str) -> Optional[WritingStyleConfig]:
        """Load a single writing style configuration file"""
        try:
            base_path = Path(self.base_paths[level])
            
            # Try different file patterns
            possible_files = [
                base_path / f"{name}.json",
                base_path / name / "writing_style.json",
                base_path / f"{name}_writing_style.json"
            ]
            
            for file_path in possible_files:
                if file_path.exists():
                    return self._parse_config_file(level, name, file_path)
            
            logger.debug(f"No writing style config found for {level}: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading {level} config '{name}': {e}")
            return None
    
    def _parse_config_file(self, level: str, name: str, file_path: Path) -> Optional[WritingStyleConfig]:
        """Parse a writing style configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract writing style section if it exists
            if 'writing_style' in data:
                style_data = data['writing_style']
            elif 'style' in data:
                style_data = data['style']
            else:
                # Assume entire file is style config
                style_data = data
            
            # Validate configuration
            config = WritingStyleConfig(
                level=level,
                name=name,
                style_data=style_data,
                file_path=str(file_path)
            )
            
            validation_result = self.validate_style_config_data(style_data)
            config.is_valid = validation_result['is_valid']
            config.validation_errors = validation_result['errors']
            
            if config.is_valid:
                logger.debug(f"Loaded valid {level} writing style: {name}")
            else:
                logger.warning(f"Loaded invalid {level} writing style: {name} - {config.validation_errors}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error parsing config file {file_path}: {e}")
            return None
    
    def _merge_style_configs(self, configs: List[WritingStyleConfig]) -> Dict[str, Any]:
        """Merge multiple style configurations with proper precedence"""
        try:
            if not configs:
                return self._get_default_style()
            
            # Start with empty merged config
            merged = {
                'text_values': [],
                'style_type': 'merged',
                'sources': [],
                'precedence_order': []
            }
            
            # Merge in order (publisher -> imprint -> tranche)
            for config in configs:
                if not config.is_valid:
                    logger.warning(f"Skipping invalid config: {config.name}")
                    continue
                
                style_data = config.style_data
                
                # Merge text values (append all)
                if 'text_values' in style_data:
                    if isinstance(style_data['text_values'], list):
                        merged['text_values'].extend(style_data['text_values'])
                    elif isinstance(style_data['text_values'], str):
                        merged['text_values'].append(style_data['text_values'])
                
                # Override style type with higher precedence
                if 'style_type' in style_data:
                    merged['style_type'] = style_data['style_type']
                
                # Track sources
                merged['sources'].append({
                    'level': config.level,
                    'name': config.name,
                    'file_path': config.file_path
                })
                
                merged['precedence_order'].append(f"{config.level}:{config.name}")
            
            # Remove duplicates from text_values while preserving order
            seen = set()
            unique_text_values = []
            for text_value in merged['text_values']:
                if text_value not in seen:
                    seen.add(text_value)
                    unique_text_values.append(text_value)
            
            merged['text_values'] = unique_text_values
            
            logger.info(f"Merged {len(configs)} style configs into {len(unique_text_values)} text values")
            return merged
            
        except Exception as e:
            logger.error(f"Error merging style configs: {e}")
            return self._get_default_style()
    
    def construct_style_prompt(self, style_config: Dict[str, Any]) -> str:
        """Construct single prompt from multiple text values in style config"""
        try:
            text_values = style_config.get('text_values', [])
            
            if not text_values:
                return ""
            
            # Join text values with appropriate separators
            if len(text_values) == 1:
                return text_values[0]
            
            # For multiple values, create a structured prompt
            prompt_parts = []
            prompt_parts.append("Please follow these writing style guidelines:")
            
            for i, text_value in enumerate(text_values, 1):
                prompt_parts.append(f"{i}. {text_value}")
            
            return '\n'.join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error constructing style prompt: {e}")
            return ""
    
    def apply_style_to_prompt(self, original_prompt: str, style_prompt: str) -> str:
        """Append style configuration to original prompt"""
        try:
            if not style_prompt:
                return original_prompt
            
            # Add style prompt as additional instructions
            enhanced_prompt = f"{original_prompt}\n\nAdditional Style Guidelines:\n{style_prompt}"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error applying style to prompt: {e}")
            return original_prompt
    
    def validate_style_config(self, config_path: str) -> Dict[str, Any]:
        """Validate writing_style.json file format and content"""
        try:
            config_file = Path(config_path)
            
            if not config_file.exists():
                return {
                    'is_valid': False,
                    'errors': [f"Config file does not exist: {config_path}"],
                    'file_path': config_path
                }
            
            # Load and parse file
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self.validate_style_config_data(data)
            
        except json.JSONDecodeError as e:
            return {
                'is_valid': False,
                'errors': [f"Invalid JSON format: {e}"],
                'file_path': config_path
            }
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Error validating config: {e}"],
                'file_path': config_path
            }
    
    def validate_style_config_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate style configuration data"""
        try:
            errors = []
            warnings = []
            
            # Check required fields
            for field in self.required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Validate text_values
            if 'text_values' in data:
                text_values = data['text_values']
                if not isinstance(text_values, (list, str)):
                    errors.append("text_values must be a string or list of strings")
                elif isinstance(text_values, list):
                    for i, value in enumerate(text_values):
                        if not isinstance(value, str):
                            errors.append(f"text_values[{i}] must be a string")
                        elif not value.strip():
                            warnings.append(f"text_values[{i}] is empty")
            
            # Validate style_type
            if 'style_type' in data:
                valid_types = ['formal', 'casual', 'academic', 'creative', 'technical', 'mixed']
                if data['style_type'] not in valid_types:
                    warnings.append(f"Unknown style_type: {data['style_type']}")
            
            # Check for unexpected fields
            all_fields = self.required_fields + self.optional_fields
            for field in data:
                if field not in all_fields:
                    warnings.append(f"Unexpected field: {field}")
            
            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'data': data
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': [],
                'data': data
            }
    
    def create_style_config_template(self, level: str, name: str, 
                                   output_path: Optional[str] = None) -> str:
        """Create a template writing_style.json file"""
        try:
            template = {
                "writing_style": {
                    "text_values": [
                        "Write in a clear, engaging style that is accessible to general readers.",
                        "Use active voice and concrete examples where possible.",
                        "Maintain a professional yet approachable tone throughout."
                    ],
                    "style_type": "mixed",
                    "description": f"Writing style configuration for {level}: {name}",
                    "version": "1.0",
                    "created_date": "2024-01-01",
                    "updated_date": "2024-01-01"
                }
            }
            
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Created style config template: {output_path}")
                return str(output_file)
            else:
                return json.dumps(template, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error creating style config template: {e}")
            return ""
    
    def _get_default_style(self) -> Dict[str, Any]:
        """Get default writing style configuration"""
        return {
            'text_values': [
                "Write in a clear, professional style.",
                "Use accessible language appropriate for the target audience.",
                "Maintain consistency in tone and voice throughout."
            ],
            'style_type': 'default',
            'sources': [],
            'precedence_order': []
        }
    
    def get_style_summary(self, tranche: Optional[str] = None, 
                         imprint: Optional[str] = None, 
                         publisher: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of loaded writing style configuration"""
        try:
            style_config = self.load_writing_style(tranche, imprint, publisher)
            
            return {
                'text_values_count': len(style_config.get('text_values', [])),
                'style_type': style_config.get('style_type', 'unknown'),
                'sources': style_config.get('sources', []),
                'precedence_order': style_config.get('precedence_order', []),
                'constructed_prompt_length': len(self.construct_style_prompt(style_config)),
                'cache_key': f"{tranche or 'none'}_{imprint or 'none'}_{publisher or 'none'}"
            }
            
        except Exception as e:
            logger.error(f"Error getting style summary: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> None:
        """Clear the style configuration cache"""
        self.cache.clear()
        logger.info("Writing style cache cleared")
    
    def list_available_configs(self) -> Dict[str, List[str]]:
        """List all available writing style configurations"""
        try:
            available = {}
            
            for level, base_path in self.base_paths.items():
                configs = []
                path = Path(base_path)
                
                if path.exists():
                    # Look for JSON files
                    for json_file in path.glob("*.json"):
                        if 'writing_style' in json_file.name or json_file.stem not in ['template', 'example']:
                            configs.append(json_file.stem)
                    
                    # Look for directories with writing_style.json
                    for dir_path in path.iterdir():
                        if dir_path.is_dir():
                            style_file = dir_path / "writing_style.json"
                            if style_file.exists():
                                configs.append(dir_path.name)
                
                available[level] = sorted(configs)
            
            return available
            
        except Exception as e:
            logger.error(f"Error listing available configs: {e}")
            return {}