"""
LLM interaction wrapper for Trillions of People.
Uses nimble-llm-caller for provider abstraction.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from nimble_llm_caller import LLMCaller
    from nimble_llm_caller.models import LLMRequest, LLMResponse
except ImportError:
    # Fallback imports for development
    from src.trillions_of_people.core.fallback_llm import LLMCaller, LLMRequest, LLMResponse

from .logging_config import get_logging_manager

logger = get_logging_manager().get_logger(__name__)


@dataclass
class PersonaGenerationRequest:
    """Request structure for generating personas."""
    country: str
    year: int
    count: int = 1
    additional_context: Optional[str] = None


class TrillionsLLMCaller:
    """LLM caller specifically configured for Trillions of People use cases."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

        self.llm_caller = LLMCaller()
        logger.info("TrillionsLLMCaller initialized")

    def generate_personas(self, request: PersonaGenerationRequest) -> List[Dict[str, Any]]:
        """Generate synthetic personas based on the request parameters."""

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_persona_prompt(request)

        llm_request = LLMRequest(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
        )

        try:
            response = self.llm_caller.call(llm_request, api_key=self.api_key)
            logger.info(f"Generated {request.count} personas for {request.country} in {request.year}")
            return self._parse_persona_response(response.content)
        except Exception as e:
            logger.error(f"Error generating personas: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for persona generation."""
        return """You are an expert historical demographer and anthropologist specializing in creating realistic synthetic personas.

Your task is to generate detailed, historically accurate personas for people who might have lived in specific times and places. Each persona should include:

- Basic demographics (name, age, gender, occupation)
- Family and social context
- Historical and cultural background appropriate to the time period
- Personal characteristics and life circumstances
- Economic and social status
- Key life events and challenges

Ensure historical accuracy for the time period and geographic location. For future dates, extrapolate based on current trends and plausible scenarios.

Format your response as structured JSON with clear fields for each persona."""

    def _build_persona_prompt(self, request: PersonaGenerationRequest) -> str:
        """Build the user prompt for specific persona generation request."""
        era_description = self._get_era_description(request.year)

        prompt = f"""Generate {request.count} realistic synthetic persona(s) for people living in {request.country} in the year {request.year} CE.

{era_description}

Please provide detailed personas including:
1. Full name (culturally appropriate for the time/place)
2. Age and gender
3. Occupation and economic status
4. Family situation
5. Living conditions
6. Key personality traits
7. Major life challenges or circumstances
8. Cultural/religious background
9. Education level
10. Notable life events

{f"Additional context: {request.additional_context}" if request.additional_context else ""}

Return as JSON array with each persona as a structured object."""

        return prompt

    def _get_era_description(self, year: int) -> str:
        """Get contextual description for the time period."""
        if year < 0:
            return f"This is {abs(year)} BCE, during ancient times."
        elif year < 500:
            return f"This is {year} CE, during the classical/late antiquity period."
        elif year < 1000:
            return f"This is {year} CE, during the early medieval period."
        elif year < 1500:
            return f"This is {year} CE, during the medieval period."
        elif year < 1800:
            return f"This is {year} CE, during the early modern period."
        elif year < 1900:
            return f"This is {year} CE, during the industrial age."
        elif year < 2000:
            return f"This is {year} CE, during the 20th century."
        elif year <= 2025:
            return f"This is {year} CE, during the early 21st century."
        else:
            return f"This is {year} CE, a projected future date. Consider technological, social, and environmental trends."

    def _parse_persona_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured persona data."""
        try:
            import json

            # Try to parse as JSON first
            if content.strip().startswith('[') or content.strip().startswith('{'):
                return json.loads(content)

            # If not JSON, attempt to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Fallback: create simple structure from text
            logger.warning("Could not parse JSON response, creating fallback structure")
            return [{"description": content, "parsing_failed": True}]

        except Exception as e:
            logger.error(f"Error parsing persona response: {e}")
            return [{"error": str(e), "raw_content": content}]