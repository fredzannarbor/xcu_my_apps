"""LLM service for generating backstories using nimble-llm-caller."""

import logging
from typing import Optional, Dict, Any

from ..core.exceptions import APIError

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating person backstories using LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM service."""
        self.api_key = api_key
        self._client = None
        
        if api_key:
            try:
                # Import nimble-llm-caller dynamically to handle missing dependency gracefully
                from nimble_llm_caller import LLMCaller
                self._client = LLMCaller(api_key=api_key)
                logger.info("LLMService initialized with nimble-llm-caller")
            except ImportError as e:
                logger.warning(f"nimble-llm-caller not available, using fallback: {e}")
                self._client = None
            except Exception as e:
                logger.error(f"Failed to initialize nimble-llm-caller: {e}")
                self._client = None
        else:
            logger.warning("No API key provided for LLM service")
    
    def generate_backstory(self, prompt: str, max_retries: int = 3) -> str:
        """Generate person backstory using nimble-llm-caller package."""
        if not self.api_key:
            raise APIError("API key required for backstory generation")
        
        if not self._client:
            # Fallback to basic implementation if nimble-llm-caller is not available
            logger.warning("Using fallback backstory generation")
            return self._generate_fallback_backstory(prompt)
        
        for attempt in range(max_retries):
            try:
                # Use nimble-llm-caller for backstory generation
                response = self._client.complete(
                    prompt=prompt,
                    model="gpt-3.5-turbo",
                    max_tokens=150,
                    temperature=0.7
                )
                
                if response and response.get('choices'):
                    backstory = response['choices'][0].get('message', {}).get('content', '').strip()
                    if backstory:
                        logger.debug(f"Generated backstory (attempt {attempt + 1})")
                        return backstory
                
                logger.warning(f"Empty response from LLM service (attempt {attempt + 1})")
                
            except Exception as e:
                logger.error(f"LLM service error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise APIError(f"Failed to generate backstory after {max_retries} attempts: {e}")
        
        # Should not reach here, but provide fallback
        return self._generate_fallback_backstory(prompt)
    
    def _generate_fallback_backstory(self, prompt: str) -> str:
        """Generate a simple fallback backstory when LLM service is unavailable."""
        # Extract basic information from prompt for fallback
        if "male" in prompt.lower():
            gender = "male"
        elif "female" in prompt.lower():
            gender = "female"
        else:
            gender = "person"
        
        # Simple template-based backstory
        templates = [
            f"A {gender} with a rich life story and unique experiences.",
            f"An interesting {gender} who has lived through many adventures.",
            f"A thoughtful {gender} with deep connections to their community.",
            f"A creative {gender} who has made meaningful contributions to society."
        ]
        
        import random
        return random.choice(templates)
    
    def is_available(self) -> bool:
        """Check if the LLM service is available and configured."""
        return self._client is not None and self.api_key is not None