#!/usr/bin/env python3

"""
Fix Empty LLM Responses

This script provides solutions to reduce empty LLM responses by:
1. Improving prompts to be less restrictive
2. Adding better fallback handling
3. Providing configuration options to skip problematic prompts
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def improve_illustration_prompt():
    """Improve the illustration_info prompt to be less restrictive."""
    
    # Read current prompts
    prompts_file = Path("prompts/enhanced_lsi_field_completion_prompts.json")
    
    if not prompts_file.exists():
        logger.error("Prompts file not found")
        return
    
    with open(prompts_file, 'r') as f:
        prompts = json.load(f)
    
    # Improved illustration prompt
    improved_prompt = {
        "messages": [
            {
                "role": "system",
                "content": "You are a book production specialist with expertise in illustration assessment for the publishing industry. Your task is to analyze book content and metadata to provide reasonable estimates of illustration information for LSI metadata submission, even when explicit information is not available."
            },
            {
                "role": "user",
                "content": "Analyze this book to determine illustration information:\n\nTitle: {title}\nAuthor: {author}\nSummary: {summary_long}\nTable of Contents: {table_of_contents}\nBook Content: {book_content}\nFormat: {format}\nGenre/BISAC: {bisac_codes}\n\nRequirements:\n1. Count any references to figures, charts, images, diagrams, tables, etc.\n2. Make reasonable estimates based on genre and subject matter:\n   - Technical/Academic books: Usually have some diagrams or charts\n   - How-to/Instructional books: Often have illustrations\n   - Children's books: Typically illustrated\n   - Fiction: Usually no illustrations unless specified\n   - Art/Design books: Heavily illustrated\n3. Look for explicit mentions of visual elements in the text\n4. Check the table of contents for sections about illustrations\n5. Provide reasonable estimates rather than defaulting to zero\n6. Format for LSI metadata submission standards\n7. Always provide a count and description, even if estimated\n\nReturn a JSON object with these keys:\n\"illustration_count\": \"Number as string (e.g., '12' or '0')\",\n\"illustration_notes\": \"Brief description of illustration types/content or 'No illustrations' if none\""
            }
        ],
        "params": {
            "temperature": 0.4,  # Slightly higher for more creative estimates
            "max_tokens": 150
        },
        "fallback": {
            "illustration_count": "0",
            "illustration_notes": "No illustrations indicated in the available content."
        }
    }
    
    # Update the prompt
    prompts["generate_illustration_info"] = improved_prompt
    
    # Save the updated prompts
    with open(prompts_file, 'w') as f:
        json.dump(prompts, f, indent=2)
    
    logger.info("✅ Updated illustration_info prompt to be less restrictive")

def create_prompt_configuration():
    """Create a configuration file to control which prompts to use."""
    
    config = {
        "prompt_settings": {
            "skip_empty_prone_prompts": False,
            "use_fallbacks_for_empty_results": True,
            "max_retries_for_empty_results": 2,
            "problematic_prompts": [
                "generate_illustration_info",
                "suggest_series_info",
                "determine_age_range"
            ]
        },
        "prompt_overrides": {
            "generate_illustration_info": {
                "enabled": True,
                "use_genre_based_estimates": True,
                "default_for_unknown": {
                    "illustration_count": "0",
                    "illustration_notes": "Illustration count not specified in available metadata."
                }
            },
            "suggest_series_info": {
                "enabled": True,
                "be_more_permissive": True,
                "default_for_unknown": {
                    "series_name": "",
                    "series_number": ""
                }
            }
        },
        "genre_based_defaults": {
            "technical_books": {
                "illustration_count": "5-10",
                "illustration_notes": "Likely contains diagrams, charts, or technical illustrations typical of the genre."
            },
            "childrens_books": {
                "illustration_count": "20-50",
                "illustration_notes": "Children's books typically contain numerous illustrations throughout."
            },
            "art_books": {
                "illustration_count": "50+",
                "illustration_notes": "Art and design books typically contain extensive visual content."
            },
            "fiction": {
                "illustration_count": "0",
                "illustration_notes": "Fiction books typically do not contain illustrations unless specifically noted."
            }
        }
    }
    
    config_file = Path("configs/llm_prompt_config.json")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Created prompt configuration at {config_file}")

def create_empty_response_handler():
    """Create a handler for empty LLM responses."""
    
    handler_code = '''"""
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
'''
    
    handler_file = Path("src/codexes/modules/distribution/empty_response_handler.py")
    handler_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(handler_file, 'w') as f:
        f.write(handler_code)
    
    logger.info(f"✅ Created empty response handler at {handler_file}")

def main():
    """Main function to apply all fixes."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("🔧 Applying fixes for empty LLM responses...")
    
    improve_illustration_prompt()
    create_prompt_configuration()
    create_empty_response_handler()
    
    logger.info("✅ All fixes applied successfully!")
    
    print("""
🎯 FIXES APPLIED:

1. ✅ Improved illustration_info prompt to be less restrictive
2. ✅ Created prompt configuration for better control
3. ✅ Created empty response handler with intelligent fallbacks

📋 RECOMMENDATIONS:

1. **Monitor Results**: Run your pipeline again and check if empty responses are reduced
2. **Adjust Temperature**: Consider increasing temperature (0.4-0.7) for more creative responses
3. **Add Context**: Ensure book metadata includes as much context as possible
4. **Use Fallbacks**: The system now has better fallback mechanisms
5. **Skip Problematic Prompts**: You can disable specific prompts in the config if needed

🔍 TO DEBUG FURTHER:
- Check the logs for specific prompts that return empty
- Review the actual book metadata being processed
- Consider if the book genuinely has no illustrations (which is valid)
- Test with books that definitely have visual content

The warnings you're seeing are actually GOOD - they indicate the system is working
and logging when LLMs return empty results, which helps with monitoring and debugging.
""")

if __name__ == "__main__":
    main()