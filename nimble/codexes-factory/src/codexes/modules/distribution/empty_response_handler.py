"""
Empty Response Handler

This module provides utilities to handle empty LLM responses gracefully.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmptyResponseHandler:
    """Handles empty LLM responses with intelligent fallbacks."""
    
    def __init__(self, config_path: str = "configs/llm_prompt_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for handling empty responses."""
        try:
            import json
            from pathlib import Path
            
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load empty response config: {e}")
        
        # Default configuration
        return {
            "prompt_settings": {
                "use_fallbacks_for_empty_results": True,
                "max_retries_for_empty_results": 2
            }
        }
    
    def handle_empty_response(self, prompt_name: str, metadata: Any, 
                            original_result: str) -> str:
        """
        Handle an empty LLM response with intelligent fallbacks.
        
        Args:
            prompt_name: Name of the prompt that returned empty
            metadata: Book metadata object
            original_result: The empty result from LLM
            
        Returns:
            Fallback result or empty string
        """
        if not self._should_use_fallback(prompt_name):
            return original_result
        
        # Try genre-based fallbacks
        if prompt_name == "generate_illustration_info":
            return self._get_illustration_fallback(metadata)
        elif prompt_name == "suggest_series_info":
            return self._get_series_fallback(metadata)
        elif prompt_name == "determine_age_range":
            return self._get_age_range_fallback(metadata)
        
        return original_result
    
    def _should_use_fallback(self, prompt_name: str) -> bool:
        """Check if we should use fallback for this prompt."""
        return self.config.get("prompt_settings", {}).get(
            "use_fallbacks_for_empty_results", True
        )
    
    def _get_illustration_fallback(self, metadata: Any) -> str:
        """Get fallback for illustration info based on genre/content."""
        try:
            # Try to determine genre from BISAC codes or title
            title = getattr(metadata, 'title', '').lower()
            bisac = getattr(metadata, 'bisac_codes', '').upper()
            
            # Technical/academic indicators
            if any(word in title for word in ['guide', 'manual', 'handbook', 'technical', 'programming']):
                return '{"illustration_count": "5", "illustration_notes": "Technical content likely contains diagrams or charts."}'
            
            # Art/design indicators  
            if any(word in title for word in ['art', 'design', 'visual', 'photography']):
                return '{"illustration_count": "25", "illustration_notes": "Art and design content typically contains visual elements."}'
            
            # Default fallback
            return '{"illustration_count": "0", "illustration_notes": "No illustrations specified in available metadata."}'
            
        except Exception as e:
            logger.warning(f"Error in illustration fallback: {e}")
            return '{"illustration_count": "0", "illustration_notes": "Unable to determine illustration information."}'
    
    def _get_series_fallback(self, metadata: Any) -> str:
        """Get fallback for series info."""
        return '{"series_name": "", "series_number": ""}'
    
    def _get_age_range_fallback(self, metadata: Any) -> str:
        """Get fallback for age range."""
        return '{"min_age": "18", "max_age": "Adult"}'
